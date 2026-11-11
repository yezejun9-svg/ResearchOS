package domain

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"errors"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// The replay encryption key lives only in this handler process. A restart
// preserves consumed fingerprints but cannot reissue earlier credentials.
type remoteHandler struct {
	s       *Service
	cipher  cipher.AEAD
	mu      sync.Mutex
	replays map[string][]byte
}

func (s *Service) newRemoteHandler() *remoteHandler {
	key := make([]byte, 32)
	if _, e := rand.Read(key); e != nil {
		panic(e)
	}
	block, e := aes.NewCipher(key)
	if e != nil {
		panic(e)
	}
	gcm, e := cipher.NewGCM(block)
	if e != nil {
		panic(e)
	}
	return &remoteHandler{s: s, cipher: gcm, replays: map[string][]byte{}}
}
func remoteSecret() (string, error) {
	b := make([]byte, 32)
	_, e := rand.Read(b)
	return hex.EncodeToString(b), e
}
func remoteExpiry(ttl time.Duration) string {
	return time.Now().UTC().Add(ttl).Format(time.RFC3339Nano)
}
func remoteValid(expiry string) bool {
	t, e := time.Parse(time.RFC3339Nano, expiry)
	return e == nil && time.Now().Before(t)
}
func remoteDenied() error {
	return Fail(401, "UNAUTHENTICATED", "credential proof unavailable, expired or consumed")
}

var errRemoteRefreshReuse = errors.New("refresh credential family revoked after reuse")

func (h *remoteHandler) handle(w http.ResponseWriter, r *http.Request, op Operation) {
	s := h.s
	cid := ID()
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Pragma", "no-cache")
	if origin := r.Header.Get("Origin"); origin != "" {
		u, err := url.Parse(origin)
		if err != nil || u.User != nil || u.Host != r.Host || (u.Scheme != "http" && u.Scheme != "https") || u.Path != "" || u.RawQuery != "" || u.Fragment != "" {
			s.writeError(w, cid, Fail(403, "FORBIDDEN", "same-origin request required"))
			return
		}
	}
	if r.Header.Get("Sec-Fetch-Site") == "cross-site" {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "cross-site request rejected"))
		return
	}
	// Credential proofs are JSON only. No query or form secrets; no cookies are
	// authentication here, so cross-site credentialed requests cannot act as user.
	if len(r.URL.Query()) != 0 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "device endpoints do not accept query parameters"))
		return
	}
	if op.Method != "GET" && !strings.HasPrefix(strings.ToLower(r.Header.Get("Content-Type")), "application/json") {
		s.writeError(w, cid, Fail(415, "INVALID_REQUEST", "JSON content type required"))
		return
	}
	controller := http.NewResponseController(w)
	_ = controller.SetReadDeadline(time.Now().Add(BodyReadTimeout))
	raw, e := io.ReadAll(io.LimitReader(r.Body, 16385))
	if e != nil || len(raw) > 16384 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "invalid or oversized request"))
		return
	}
	b := Object{}
	if op.Request != "" {
		b, e = Decode(raw)
		if e == nil {
			e = s.Contracts.Validate(op.Request, b)
		}
		if e != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "invalid device request"))
			return
		}
	} else if len(raw) != 0 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "unexpected body"))
		return
	}
	key := r.Header.Get("Idempotency-Key")
	if op.Method != "GET" {
		if key == "" {
			s.writeError(w, cid, Fail(428, "PRECONDITION_REQUIRED", "Idempotency-Key required"))
			return
		}
		if len(r.Header.Values("Idempotency-Key")) != 1 || s.Contracts.Validate("Idempotency-Key", key) != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "invalid Idempotency-Key"))
			return
		}
	}
	tx, e := s.DB.BeginTx(r.Context(), nil)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	defer tx.Rollback()
	// A write lock precedes all checks/consumption, also across independent service processes.
	if op.Method != "GET" {
		if _, e = tx.Exec("UPDATE remote_challenges SET consumed=consumed WHERE 0"); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	actor, target := "", r.PathValue("device_id")
	var p Principal
	if op.ID == "redeemDevicePairing" {
		actor = Digest([]byte(Str(b, "pairing_token")))
		target = Str(b, "challenge_id")
	} else if op.ID == "refreshDeviceSession" {
		actor = Digest([]byte(Str(b, "refresh_token")))
	} else {
		auth := r.Header.Get("Authorization")
		if !strings.HasPrefix(auth, "Bearer ") {
			s.writeError(w, cid, remoteDenied())
			return
		}
		p, e = authenticate(tx, strings.TrimPrefix(auth, "Bearer "))
		if e != nil {
			s.writeError(w, cid, e)
			return
		}
		if !p.HasRole("OWNER") || p.DeviceID != "" {
			s.writeError(w, cid, Fail(403, "FORBIDDEN", "local owner required"))
			return
		}
		actor = p.ID
	}
	hash := Hash([]any{op.ID, r.URL.EscapedPath(), r.Header.Get("If-Match"), b})
	cacheID := Hash([]any{actor, op.ID, key})
	if op.Method != "GET" {
		var oldHash, oldTarget, expiry string
		var stored []byte
		e = tx.QueryRow("SELECT request_hash,target,expires_at,response FROM remote_replays WHERE actor=? AND operation=? AND key=?", actor, op.ID, key).Scan(&oldHash, &oldTarget, &expiry, &stored)
		if e == nil {
			h.mu.Lock()
			ciphertext := h.replays[cacheID]
			h.mu.Unlock()
			if hash != oldHash {
				s.writeError(w, cid, Fail(409, "IDEMPOTENCY_CONFLICT", "key already used with a different request"))
				return
			}
			if !remoteValid(expiry) || (stored == nil && len(ciphertext) < h.cipher.NonceSize()) {
				s.writeError(w, cid, Fail(409, "STATE_CONFLICT", "secret response replay expired; do not repeat credential issuance"))
				return
			}
			plain, err := stored, error(nil)
			if stored == nil {
				plain, err = h.cipher.Open(nil, ciphertext[:h.cipher.NonceSize()], ciphertext[h.cipher.NonceSize():], []byte(actor+op.ID+key))
			}
			if err != nil {
				s.writeError(w, cid, Fail(409, "STATE_CONFLICT", "secret response unavailable after service restart"))
				return
			}
			result, err := Decode(plain)
			if err != nil {
				s.writeError(w, cid, err)
				return
			}
			if err = h.replayAllowed(tx, p, op, oldTarget, result); err != nil {
				s.writeError(w, cid, err)
				return
			}
			if e = tx.Commit(); e != nil {
				s.writeError(w, cid, e)
				return
			}
			w.Header().Set("Idempotency-Replayed", "true")
			h.respond(w, cid, op, result)
			return
		}
		if !errors.Is(e, sql.ErrNoRows) {
			s.writeError(w, cid, e)
			return
		}
	}
	var result Object
	switch op.ID {
	case "createDevicePairing":
		result, e = h.create(tx, p, b)
		if e == nil {
			target = Str(result, "challenge_id")
		}
	case "redeemDevicePairing":
		result, e = h.redeem(tx, b)
		if e == nil {
			target = Str(result["device"].(map[string]any), "id")
		}
	case "refreshDeviceSession":
		result, e = h.refresh(tx, b)
		if e == nil {
			target = Str(result["device"].(map[string]any), "id")
		}
	case "listDevices":
		result, e = h.list(tx, p)
	case "updateDeviceGrants", "revokeDevice":
		result, e = h.change(tx, p, target, b, op, r.Header.Get("If-Match"))
	}
	if e != nil {
		if errors.Is(e, errRemoteRefreshReuse) {
			// Reuse is rejected, but revocation must survive the error response.
			if e = tx.Commit(); e == nil {
				e = remoteDenied()
			}
		}
		s.writeError(w, cid, e)
		return
	}
	if e = s.Contracts.Validate(op.Response, result); e != nil {
		s.writeError(w, cid, Fail(500, "INTERNAL_ERROR", "device response contract mismatch"))
		return
	}
	var encrypted []byte
	if op.Method != "GET" {
		var stored []byte
		expiry := remoteExpiry(5 * time.Minute)
		if op.ID == "updateDeviceGrants" || op.ID == "revokeDevice" {
			stored = Bytes(result)
			expiry = remoteExpiry(7 * 24 * time.Hour)
		} else {
			nonce := make([]byte, h.cipher.NonceSize())
			if _, e = rand.Read(nonce); e != nil {
				s.writeError(w, cid, e)
				return
			}
			encrypted = h.cipher.Seal(nonce, nonce, Bytes(result), []byte(actor+op.ID+key))
		}
		if _, e = tx.Exec("INSERT INTO remote_replays(actor,operation,key,request_hash,target,response,expires_at,created_at) VALUES(?,?,?,?,?,?,?,?)", actor, op.ID, key, hash, target, stored, expiry, Now()); e != nil {
			s.writeError(w, cid, e)
			return
		}
		// Audit identifiers only: labels, reason text and all credentials excluded.
		if _, e = tx.Exec("INSERT INTO remote_audit(id,actor,operation,target,created_at) VALUES(?,?,?,?,?)", ID(), actor, op.ID, target, Now()); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	if e = tx.Commit(); e != nil {
		s.writeError(w, cid, e)
		return
	}
	if encrypted != nil {
		h.mu.Lock()
		h.replays[cacheID] = encrypted
		h.mu.Unlock()
		time.AfterFunc(5*time.Minute, func() { h.mu.Lock(); delete(h.replays, cacheID); h.mu.Unlock() })
	}
	h.respond(w, cid, op, result)
}
func (h *remoteHandler) respond(w http.ResponseWriter, cid string, op Operation, result Object) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Correlation-ID", cid)
	if _, ok := result["revision"]; ok {
		tag, _ := ETag(result)
		w.Header().Set("ETag", tag)
	}
	status := 200
	if op.ID == "createDevicePairing" {
		status = 201
	}
	w.WriteHeader(status)
	_, _ = w.Write(Bytes(result))
}

func (h *remoteHandler) scope(tx *sql.Tx, p Principal, projects []any) error {
	if len(projects) == 0 || len(projects) > 100 {
		return Fail(400, "INVALID_REQUEST", "one to 100 explicit projects required")
	}
	seen := map[string]bool{}
	for _, v := range projects {
		id, ok := v.(string)
		if !ok || seen[id] || !p.Allowed(id, "", "", false) {
			return Fail(403, "FORBIDDEN", "project scope unavailable")
		}
		seen[id] = true
		if _, e := singleton(tx, id, "ProjectProfile"); e != nil {
			return Fail(403, "FORBIDDEN", "project scope unavailable")
		}
	}
	return nil
}
func (h *remoteHandler) owner(tx *sql.Tx, id string) (Principal, error) {
	var p Principal
	var roles string
	var revoked int
	if e := tx.QueryRow("SELECT id,roles,revoked FROM auth_principals WHERE id=?", id).Scan(&p.ID, &roles, &revoked); e != nil {
		return p, remoteDenied()
	}
	o, e := Decode([]byte(`{"roles":` + roles + `}`))
	if e != nil {
		return p, e
	}
	for _, r := range Arr(o, "roles") {
		p.Roles = append(p.Roles, r.(string))
	}
	if revoked != 0 || !p.HasRole("OWNER") {
		return p, remoteDenied()
	}
	rows, e := tx.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", id)
	if e != nil {
		return p, e
	}
	defer rows.Close()
	for rows.Next() {
		var g Grant
		if e = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); e != nil {
			return p, e
		}
		p.Grants = append(p.Grants, g)
	}
	return p, rows.Err()
}
func (h *remoteHandler) create(tx *sql.Tx, p Principal, b Object) (Object, error) {
	if len(Str(b, "label")) > 200 {
		return nil, Fail(400, "INVALID_REQUEST", "label too long")
	}
	if e := h.scope(tx, p, Arr(b, "project_ids")); e != nil {
		return nil, e
	}
	secret, e := remoteSecret()
	if e != nil {
		return nil, e
	}
	ttl, _ := Num(b, "expires_in_seconds")
	id, expiry := ID(), remoteExpiry(time.Duration(ttl)*time.Second)
	_, e = tx.Exec("INSERT INTO remote_challenges(id,owner,token_hash,projects,expires_at) VALUES(?,?,?,?,?)", id, p.ID, Digest([]byte(secret)), string(Bytes(b["project_ids"])), expiry)
	return Object{"challenge_id": id, "pairing_token": secret, "expires_at": expiry}, e
}
func (h *remoteHandler) device(tx *sql.Tx, id string) (Object, string, error) {
	var body, owner string
	if e := tx.QueryRow("SELECT body,owner FROM remote_devices WHERE id=?", id).Scan(&body, &owner); e != nil {
		return nil, "", Fail(404, "NOT_FOUND", "device unavailable")
	}
	o, e := Decode([]byte(body))
	return o, owner, e
}
func (h *remoteHandler) active(tx *sql.Tx, id string) (Object, error) {
	d, owner, e := h.device(tx, id)
	if e != nil {
		return nil, remoteDenied()
	}
	if Str(d, "status") != "ACTIVE" {
		return nil, remoteDenied()
	}
	var revoked int
	if e = tx.QueryRow("SELECT revoked FROM auth_principals WHERE id=?", id).Scan(&revoked); e != nil || revoked != 0 {
		return nil, remoteDenied()
	}
	p, e := h.owner(tx, owner)
	if e != nil {
		return nil, e
	}
	if e = h.scope(tx, p, Arr(d, "project_ids")); e != nil {
		return nil, remoteDenied()
	}
	return d, nil
}
func (h *remoteHandler) session(tx *sql.Tx, d Object) (Object, error) {
	access, e := remoteSecret()
	if e != nil {
		return nil, e
	}
	refresh, e := remoteSecret()
	if e != nil {
		return nil, e
	}
	aexp, rexp := remoteExpiry(15*time.Minute), remoteExpiry(24*time.Hour)
	if _, e = tx.Exec("INSERT INTO auth_credentials(token_hash,principal,expires_at) VALUES(?,?,?)", Digest([]byte(access)), d["id"], aexp); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("INSERT INTO remote_refresh(token_hash,device,expires_at) VALUES(?,?,?)", Digest([]byte(refresh)), d["id"], rexp); e != nil {
		return nil, e
	}
	d["last_seen_at"] = Now()
	if _, e = tx.Exec("UPDATE remote_devices SET body=? WHERE id=?", string(Bytes(d)), d["id"]); e != nil {
		return nil, e
	}
	return Object{"device": d, "access_token": access, "access_expires_at": aexp, "refresh_token": refresh, "refresh_expires_at": rexp}, nil
}
func (h *remoteHandler) redeem(tx *sql.Tx, b Object) (Object, error) {
	var owner, projects, expiry string
	var consumed int
	e := tx.QueryRow("SELECT owner,projects,expires_at,consumed FROM remote_challenges WHERE id=? AND token_hash=?", b["challenge_id"], Digest([]byte(Str(b, "pairing_token")))).Scan(&owner, &projects, &expiry, &consumed)
	if e != nil || consumed != 0 || !remoteValid(expiry) {
		return nil, remoteDenied()
	}
	if len(Str(b, "device_label")) > 200 {
		return nil, Fail(400, "INVALID_REQUEST", "label too long")
	}
	p, e := h.owner(tx, owner)
	if e != nil {
		return nil, e
	}
	o, e := Decode([]byte(`{"projects":` + projects + `}`))
	if e != nil {
		return nil, e
	}
	ids := Arr(o, "projects")
	if e = h.scope(tx, p, ids); e != nil {
		return nil, e
	}
	id := ID()
	d := Object{"id": id, "revision": 1, "created_at": Now(), "label": b["device_label"], "project_ids": ids, "role": "READER", "status": "ACTIVE", "last_seen_at": nil, "revoked_at": nil}
	if _, e = tx.Exec("INSERT INTO auth_principals(id,roles) VALUES(?,?)", id, `["READER"]`); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("INSERT INTO remote_devices(id,owner,body) VALUES(?,?,?)", id, owner, string(Bytes(d))); e != nil {
		return nil, e
	}
	for _, project := range ids {
		if _, e = tx.Exec("INSERT INTO auth_grants(principal,project) VALUES(?,?)", id, project); e != nil {
			return nil, e
		}
	}
	if _, e = tx.Exec("UPDATE remote_challenges SET consumed=1 WHERE id=?", b["challenge_id"]); e != nil {
		return nil, e
	}
	return h.session(tx, d)
}
func (h *remoteHandler) refresh(tx *sql.Tx, b Object) (Object, error) {
	hash := Digest([]byte(Str(b, "refresh_token")))
	var id, expiry string
	var consumed int
	if e := tx.QueryRow("SELECT device,expires_at,consumed FROM remote_refresh WHERE token_hash=?", hash).Scan(&id, &expiry, &consumed); e != nil {
		return nil, remoteDenied()
	}
	if consumed != 0 {
		// Exact idempotent retries have already returned from the replay path.
		// Each pairing creates a device principal and its own refresh family.
		d, _, e := h.device(tx, id)
		if e != nil {
			return nil, e
		}
		if d["status"] == "REVOKED" {
			return nil, remoteDenied()
		}
		d["status"], d["revoked_at"] = "REVOKED", Now()
		revision, _ := Num(d, "revision")
		d["revision"] = revision + 1
		for _, statement := range []string{"UPDATE auth_principals SET revoked=1 WHERE id=?", "UPDATE auth_credentials SET revoked=1 WHERE principal=?", "UPDATE remote_refresh SET consumed=1 WHERE device=?"} {
			if _, e = tx.Exec(statement, id); e != nil {
				return nil, e
			}
		}
		if _, e = tx.Exec("UPDATE remote_devices SET body=? WHERE id=?", string(Bytes(d)), id); e != nil {
			return nil, e
		}
		if _, e = tx.Exec("INSERT INTO remote_audit(id,actor,operation,target,created_at) VALUES(?,?,?,?,?)", ID(), hash, "refreshReuseRevocation", id, Now()); e != nil {
			return nil, e
		}
		return nil, errRemoteRefreshReuse
	}
	if !remoteValid(expiry) {
		return nil, remoteDenied()
	}
	d, e := h.active(tx, id)
	if e != nil {
		return nil, e
	}
	if _, e = tx.Exec("UPDATE remote_refresh SET consumed=1 WHERE token_hash=?", hash); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("UPDATE auth_credentials SET revoked=1 WHERE principal=?", id); e != nil {
		return nil, e
	}
	return h.session(tx, d)
}
func (h *remoteHandler) list(tx *sql.Tx, p Principal) (Object, error) {
	rows, e := tx.Query("SELECT body FROM remote_devices WHERE owner=? ORDER BY id", p.ID)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	items := Empty()
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			return nil, e
		}
		d, err := Decode([]byte(raw))
		if err != nil {
			return nil, err
		}
		items = append(items, d)
	}
	return Object{"items": items, "next_cursor": nil}, rows.Err()
}
func (h *remoteHandler) change(tx *sql.Tx, p Principal, id string, b Object, op Operation, tag string) (Object, error) {
	d, owner, e := h.device(tx, id)
	if e != nil {
		return nil, e
	}
	if owner != p.ID {
		return nil, Fail(404, "NOT_FOUND", "device unavailable")
	}
	if tag == "" {
		return nil, Fail(428, "PRECONDITION_REQUIRED", "If-Match required")
	}
	want, _ := ETag(d)
	if tag != want {
		return nil, &Fault{412, "STALE_REVISION", "device changed", d["revision"]}
	}
	if Str(d, "status") == "REVOKED" {
		return nil, Fail(409, "STATE_CONFLICT", "device revoked")
	}
	if op.ID == "revokeDevice" {
		d["status"] = "REVOKED"
		d["revoked_at"] = Now()
		if _, e = tx.Exec("UPDATE auth_principals SET revoked=1 WHERE id=?", id); e != nil {
			return nil, e
		}
		if _, e = tx.Exec("UPDATE auth_credentials SET revoked=1 WHERE principal=?", id); e != nil {
			return nil, e
		}
		if _, e = tx.Exec("UPDATE remote_refresh SET consumed=1 WHERE device=?", id); e != nil {
			return nil, e
		}
	} else {
		if e = h.scope(tx, p, Arr(b, "project_ids")); e != nil {
			return nil, e
		}
		d["role"] = b["role"]
		d["project_ids"] = b["project_ids"]
		if _, e = tx.Exec("UPDATE auth_principals SET roles=? WHERE id=?", string(Bytes([]any{b["role"]})), id); e != nil {
			return nil, e
		}
		if _, e = tx.Exec("DELETE FROM auth_grants WHERE principal=?", id); e != nil {
			return nil, e
		}
		for _, project := range Arr(b, "project_ids") {
			if _, e = tx.Exec("INSERT INTO auth_grants(principal,project) VALUES(?,?)", id, project); e != nil {
				return nil, e
			}
		}
	}
	revision, _ := Num(d, "revision")
	d["revision"] = revision + 1
	if _, e = tx.Exec("UPDATE remote_devices SET body=? WHERE id=?", string(Bytes(d)), id); e != nil {
		return nil, e
	}
	return d, nil
}
func (h *remoteHandler) replayAllowed(tx *sql.Tx, p Principal, op Operation, target string, result Object) error {
	if op.ID == "createDevicePairing" {
		var owner, projects, expiry string
		var consumed int
		if e := tx.QueryRow("SELECT owner,projects,expires_at,consumed FROM remote_challenges WHERE id=?", target).Scan(&owner, &projects, &expiry, &consumed); e != nil || owner != p.ID || consumed != 0 || !remoteValid(expiry) {
			return remoteDenied()
		}
		o, e := Decode([]byte(`{"projects":` + projects + `}`))
		if e != nil {
			return e
		}
		return h.scope(tx, p, Arr(o, "projects"))
	}
	if op.ID == "redeemDevicePairing" || op.ID == "refreshDeviceSession" {
		if _, e := h.active(tx, target); e != nil {
			return e
		}
		var valid int
		if e := tx.QueryRow("SELECT count(*) FROM auth_credentials WHERE token_hash=? AND principal=? AND revoked=0 AND expires_at>?", Digest([]byte(Str(result, "access_token"))), target, Now()).Scan(&valid); e != nil || valid != 1 {
			return remoteDenied()
		}
		return nil
	}
	d, owner, e := h.device(tx, target)
	if e != nil || owner != p.ID {
		return Fail(404, "NOT_FOUND", "device unavailable")
	}
	if Hash(d) != Hash(result) {
		return Fail(409, "STATE_CONFLICT", "device changed since original operation")
	}
	return nil
}
