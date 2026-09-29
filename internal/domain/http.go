package domain

import (
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"
)

func (s *Service) Handler() http.Handler {
	mux := http.NewServeMux()
	for _, op := range s.Contracts.Operations {
		mux.HandleFunc(op.Method+" "+op.Path, func(w http.ResponseWriter, r *http.Request) { s.handle(w, r, op) })
	}
	mux.HandleFunc("/v1/", func(w http.ResponseWriter, r *http.Request) {
		s.writeError(w, ID(), Fail(404, "NOT_FOUND", "operation unavailable"))
	})
	return mux
}
func (s *Service) writeError(w http.ResponseWriter, cid string, e error) {
	f, ok := e.(*Fault)
	if !ok {
		f = &Fault{500, "INTERNAL_ERROR", "operation failed", nil}
		if strings.Contains(e.Error(), "constraint failed") {
			f = &Fault{409, "STATE_CONFLICT", "persistent invariant rejected operation", nil}
		}
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Correlation-ID", cid)
	if f.Current != nil {
		w.Header().Set("ETag", fmt.Sprintf("\"r%v\"", f.Current))
	}
	w.WriteHeader(f.Status)
	w.Write(Bytes(Object{"code": f.Code, "message": f.Message, "correlation_id": cid, "retryable": f.Status == 503, "current_revision": f.Current, "details": Empty()}))
}

var etagPattern = regexp.MustCompile(`^"r[1-9][0-9]*"$`)

const BodyReadTimeout = 5 * time.Second

func (s *Service) handle(w http.ResponseWriter, r *http.Request, op Operation) {
	cid := ID()
	auth := r.Header.Get("Authorization")
	if !strings.HasPrefix(auth, "Bearer ") {
		s.writeError(w, cid, Fail(401, "UNAUTHENTICATED", "Bearer credential required"))
		return
	}
	// Read bounded input before acquiring SQLite's single authoritative connection.
	controller := http.NewResponseController(w)
	if e := controller.SetReadDeadline(time.Now().Add(BodyReadTimeout)); e != nil && !errors.Is(e, http.ErrNotSupported) {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "body read unavailable"))
		return
	}
	raw, e := io.ReadAll(io.LimitReader(r.Body, 64*1024*1024+1))
	if e != nil || len(raw) > 64*1024*1024 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "invalid, timed out or oversized body"))
		return
	}
	tx, e := s.DB.BeginTx(r.Context(), nil)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	defer tx.Rollback()
	p, e := authenticate(tx, strings.TrimPrefix(auth, "Bearer "))
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	roleOK := false
	for _, role := range op.Roles {
		if p.HasRole(role) {
			roleOK = true
		}
	}
	if !roleOK {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "role not authorized for operation"))
		return
	}
	project, id := r.PathValue("project_id"), r.PathValue("object_id")
	if project != "" && !p.Allowed(project, "", "", false) {
		if !(op.ID == "getTask" && p.Allowed(project, id, "", false)) {
			s.writeError(w, cid, Fail(404, "NOT_FOUND", "project or object unavailable"))
			return
		}
	}
	if !op.Implemented {
		s.writeError(w, cid, Fail(503, "RESOURCE_UNAVAILABLE", "operation requires "+op.Owner))
		return
	}
	if op.ID == "createProject" && !p.CanCreateProject {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "project creation is not granted"))
		return
	}
	b := Object{}
	if op.Request != "" {
		b, e = Decode(raw)
		if e == nil {
			e = s.Contracts.Validate(op.Request, b)
		}
		if e != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "request violates "+op.Request+" schema"))
			return
		}
	} else if op.Method == "GET" && len(raw) != 0 {
		s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "GET body unsupported"))
		return
	}
	if !s.visible(tx, p, project, b) {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "restricted reference unavailable"))
		return
	}
	write := op.Method != "GET"
	key := r.Header.Get("Idempotency-Key")
	var requestHash string
	if write {
		values, present := r.Header[http.CanonicalHeaderKey("Idempotency-Key")]
		if !present {
			s.writeError(w, cid, Fail(428, "PRECONDITION_REQUIRED", "Idempotency-Key required"))
			return
		}
		if len(values) != 1 || s.Contracts.Validate("Idempotency-Key", key) != nil {
			s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "Idempotency-Key violates header schema"))
			return
		}
		var body any = b
		if op.ID == "uploadContent" {
			body = Digest(raw)
		}
		requestHash = Hash([]any{op.ID, r.URL.EscapedPath(), r.URL.Query().Encode(), r.Header.Get("If-Match"), body})
		var oldHash, headers string
		var status int
		var bodyBytes []byte
		e = tx.QueryRow("SELECT request_hash,status,body,headers FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?", p.ID, project, op.ID, key).Scan(&oldHash, &status, &bodyBytes, &headers)
		if e == nil {
			if oldHash != requestHash {
				s.writeError(w, cid, Fail(409, "IDEMPOTENCY_CONFLICT", "key already used with different request"))
				return
			}
			h, _ := Decode([]byte(headers))
			if !s.replayAllowed(tx, p, op, bodyBytes) {
				s.writeError(w, cid, Fail(403, "FORBIDDEN", "current permission denies replay"))
				return
			}
			for k, v := range h {
				w.Header().Set(k, v.(string))
			}
			w.Header().Set("Idempotency-Replayed", "true")
			w.WriteHeader(status)
			w.Write(bodyBytes)
			return
		}
		if !errors.Is(e, sql.ErrNoRows) {
			s.writeError(w, cid, e)
			return
		}
		if op.Target != "" {
			match := r.Header.Get("If-Match")
			if match == "" {
				s.writeError(w, cid, Fail(428, "PRECONDITION_REQUIRED", "If-Match required"))
				return
			}
			if !etagPattern.MatchString(match) {
				s.writeError(w, cid, Fail(400, "INVALID_REQUEST", "strong revision ETag required"))
				return
			}
			target, e := s.precondition(tx, project, id, op, b)
			if e != nil {
				s.writeError(w, cid, e)
				return
			}
			tag, e := ETag(target)
			if e != nil {
				s.writeError(w, cid, e)
				return
			}
			if match != tag {
				current, e := Num(target, "revision")
				if e != nil {
					s.writeError(w, cid, e)
					return
				}
				s.writeError(w, cid, &Fault{412, "STALE_REVISION", "aggregate changed", current})
				return
			}
		}
	}
	var result Object
	status := 200
	kind := ""
	headers := Object{"Content-Type": "application/json", "Cache-Control": "no-store", "X-Correlation-ID": cid}
	switch op.ID {
	case "createProject":
		result, e = s.createProject(tx, p, b)
		kind = "ProjectProfile"
		status = 201
	case "createRequirement":
		result, e = s.createRequirement(tx, project, b)
		kind = "Requirement"
		status = 201
	case "createEvidence":
		result, e = s.createEvidence(tx, project, b)
		kind = "Evidence"
		status = 201
	case "advanceSourceCursor":
		result, e = s.advanceSourceCursor(tx, project, id, b)
		kind = "SourceCursor"
	case "actOnRequirement":
		result, e = s.actRequirement(tx, project, id, b)
		kind = "Requirement"
	case "createGoal":
		result, e = s.createGoal(tx, project, b)
		kind = "Goal"
		status = 201
	case "createTask":
		result, e = s.createTask(tx, project, b)
		kind = "Task"
		status = 201
	case "actOnTask":
		result, e = s.actTask(tx, project, id, b)
		kind = "Task"
	case "uploadContent":
		result, e = s.upload(tx, p, project, raw)
		status = 201
	case "sealArtifact":
		result, e = s.seal(tx, p, project, b)
		kind = "Artifact"
		status = 201
	case "getArtifactContent":
		s.content(w, r, tx, p, project, id, cid)
		return
	case "getProjectProfile":
		result, e = singleton(tx, project, "ProjectProfile")
	case "getProjectState":
		result, e = singleton(tx, project, "ProjectState")
	case "getGlobalBudgetPolicy", "getGlobalRunPolicy":
		k := strings.TrimPrefix(op.ID, "getGlobal")
		result, e = singleton(tx, "", k)
	case "getBudgetPolicy", "getRunPolicy":
		profile, err := singleton(tx, project, "ProjectProfile")
		e = err
		if e == nil {
			k := strings.TrimPrefix(op.ID, "get")
			field := "budget_policy_id"
			if k == "RunPolicy" {
				field = "run_policy_id"
			}
			result, e = load(tx, project, k, Str(profile, field))
		}
	case "getGoalBudgetPolicy":
		goal, err := load(tx, project, "Goal", id)
		e = err
		if e == nil {
			result, e = load(tx, project, "BudgetPolicy", Str(goal, "budget_policy_id"))
		}
	default:
		if strings.HasPrefix(op.ID, "get") {
			kind = strings.TrimPrefix(op.ID, "get")
			result, e = s.readObject(tx, p, project, kind, id)
		} else if strings.HasPrefix(op.ID, "list") {
			result, e = s.page(tx, p, project, op, r)
		} else if contextOperations[op.ID] {
			result, kind, status, e = s.contextOperation(tx, p, project, id, b, op.ID)
		} else {
			e = Fail(503, "RESOURCE_UNAVAILABLE", "operation unavailable")
		}
	}
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	if !s.visible(tx, p, project, result) {
		s.writeError(w, cid, Fail(403, "FORBIDDEN", "result references restricted content"))
		return
	}
	if write && kind != "" {
		ep := project
		if op.ID == "createProject" {
			ep = Str(result, "project_id")
		}
		eventType := "PROJECT_UPDATED"
		if op.ID == "applyChangeProposal" {
			eventType = "CHANGE_APPLIED"
		}
		if op.ID == "recordAcceptance" {
			eventType = "ACCEPTANCE_RECORDED"
		}
		if op.ID == "recordDecision" {
			eventType = "DECISION_RECORDED"
		}
		if kind == "Task" {
			eventType = "TASK_CHANGED"
		}
		if e = s.event(tx, ep, kind, result, p.ID, cid, eventType); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	if op.Response != "" {
		if e = s.Contracts.Validate(op.Response, result); e != nil {
			s.writeError(w, cid, Fail(500, "INTERNAL_ERROR", "response contract mismatch"))
			return
		}
	}
	if _, ok := result["revision"]; ok {
		tag, e := ETag(result)
		if e != nil {
			s.writeError(w, cid, e)
			return
		}
		headers["ETag"] = tag
	}
	response := Bytes(result)
	if write {
		if _, e = tx.Exec("INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,?,?,?,?)", p.ID, project, op.ID, key, requestHash, status, response, string(Bytes(headers)), Now()); e != nil {
			s.writeError(w, cid, e)
			return
		}
	}
	if e = tx.Commit(); e != nil {
		s.writeError(w, cid, e)
		return
	}
	for k, v := range headers {
		w.Header().Set(k, v.(string))
	}
	w.WriteHeader(status)
	w.Write(response)
}
func (s *Service) precondition(tx *sql.Tx, project, id string, op Operation, b Object) (Object, error) {
	switch op.Target {
	case "subject_ref":
		r := b["subject_ref"].(map[string]any)
		return load(tx, project, Str(r, "entity_type"), Str(r, "id"))
	case "ProjectState":
		return singleton(tx, project, "ProjectState")
	case "Goal":
		if id == "" {
			id = Str(b, "goal_id")
		}
		return load(tx, project, "Goal", id)
	default:
		return load(tx, project, op.Target, id)
	}
}
func (s *Service) replayAllowed(tx *sql.Tx, p Principal, op Operation, raw []byte) bool {
	o, e := Decode(raw)
	if e != nil {
		return false
	}
	if project := Str(o, "project_id"); project != "" && !p.Allowed(project, "", "", false) {
		return false
	}
	return s.visible(tx, p, Str(o, "project_id"), o)
}

func (s *Service) visible(tx *sql.Tx, p Principal, project string, value any) bool {
	return s.visibleGraph(tx, p, project, value, map[string]bool{})
}
func (s *Service) visibleGraph(tx *sql.Tx, p Principal, project string, value any, seen map[string]bool) bool {
	switch o := value.(type) {
	case map[string]any:
		if o["access_class"] == "VERIFIER_ONLY" && (!p.Allowed(project, "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
			return false
		}
		if o["entity_type"] == "Artifact" {
			var access string
			if e := tx.QueryRow("SELECT json_extract(body,'$.access_class') FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", project, o["id"]).Scan(&access); e == nil && access == "VERIFIER_ONLY" && (!p.Allowed(project, "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
				return false
			}
		}
		if kind := Str(o, "entity_type"); kind != "" {
			key := Hash([]any{project, o})
			if !seen[key] {
				seen[key] = true
				obj, e := version(tx, project, o)
				if e == nil && !s.visibleGraph(tx, p, project, obj, seen) {
					return false
				}
			}
		}
		for _, v := range o {
			if !s.visibleGraph(tx, p, project, v, seen) {
				return false
			}
		}
	case []any:
		for _, v := range o {
			if !s.visibleGraph(tx, p, project, v, seen) {
				return false
			}
		}
	}
	return true
}
func (s *Service) readObject(tx *sql.Tx, p Principal, project, kind, id string) (Object, error) {
	if kind == "Artifact" {
		var access string
		e := tx.QueryRow("SELECT json_extract(body,'$.access_class') FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", project, id).Scan(&access)
		if e != nil || access == "VERIFIER_ONLY" && (!p.Allowed(project, "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
			return nil, Fail(404, "NOT_FOUND", "artifact unavailable")
		}
	}
	o, e := load(tx, project, kind, id)
	if e == nil && !s.visible(tx, p, project, o) {
		return nil, Fail(404, "NOT_FOUND", "object unavailable")
	}
	return o, e
}
func (s *Service) content(w http.ResponseWriter, r *http.Request, tx *sql.Tx, p Principal, project, id, cid string) {
	o, e := s.readObject(tx, p, project, "Artifact", id)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	if o["access_class"] == "VERIFIER_ONLY" {
		s.writeError(w, cid, Fail(503, "RESOURCE_UNAVAILABLE", "protected content store requires W17 qualification"))
		return
	}
	var b []byte
	e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, o["storage_key"]).Scan(&b)
	size, numberErr := Num(o, "byte_size")
	if e != nil || numberErr != nil || Digest(b) != o["content_hash"] || int64(len(b)) != size {
		s.writeError(w, cid, Fail(422, "CONTENT_HASH_MISMATCH", "sealed content verification failed"))
		return
	}
	hash, _ := hex.DecodeString(strings.TrimPrefix(Str(o, "content_hash"), "sha256:"))
	w.Header().Set("Content-Type", Str(o, "media_type"))
	w.Header().Set("Digest", "sha-256="+base64.StdEncoding.EncodeToString(hash))
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Content-Security-Policy", "sandbox; default-src 'none'")
	w.Header().Set("Content-Disposition", "attachment")
	w.Header().Set("Cache-Control", "no-store")
	tag, e := ETag(o)
	if e != nil {
		s.writeError(w, cid, e)
		return
	}
	w.Header().Set("ETag", tag)
	w.Write(b)
}
func (s *Service) page(tx *sql.Tx, p Principal, project string, op Operation, r *http.Request) (Object, error) {
	for key, values := range r.URL.Query() {
		if len(values) != 1 || (key != "limit" && key != "cursor" && !(op.ID == "listEvents" && key == "after_sequence")) {
			return nil, Fail(400, "INVALID_REQUEST", "unsupported or repeated query parameter")
		}
	}
	limit := 50
	if q := r.URL.Query().Get("limit"); q != "" {
		v, e := strconv.Atoi(q)
		if e != nil || v < 1 || v > 100 {
			return nil, Fail(400, "INVALID_REQUEST", "limit must be 1..100")
		}
		limit = v
	}
	grantHash := Hash([]any{p.Grants, p.Roles})
	after := int64(0)
	if q := r.URL.Query().Get("after_sequence"); q != "" {
		n, e := strconv.ParseInt(q, 10, 64)
		if e != nil || n < 0 {
			return nil, Fail(400, "INVALID_REQUEST", "invalid event sequence")
		}
		after = n
	}
	operationKey := op.ID + ":" + Hash(Object{"limit": limit, "after_sequence": after})
	var items []any
	var seq int64
	cursor := r.URL.Query().Get("cursor")
	if cursor != "" {
		var raw, expires string
		e := tx.QueryRow("SELECT body,expires_at FROM page_cursors WHERE id=? AND principal=? AND project=? AND operation=? AND grant_hash=?", cursor, p.ID, project, operationKey, grantHash).Scan(&raw, &expires)
		if e != nil {
			return nil, Fail(400, "INVALID_REQUEST", "cursor is not valid for this scope")
		}
		expiry, e := time.Parse(time.RFC3339Nano, expires)
		if e != nil || time.Now().After(expiry) {
			return nil, Fail(410, "CURSOR_EXPIRED", "cursor expired")
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		items = Arr(o, "items")
		seq, e = Num(o, "snapshot_event_sequence")
		if e != nil {
			return nil, e
		}
	} else {
		kind := strings.TrimPrefix(op.ID, "list")
		if op.ID == "listProjects" {
			kind = "ProjectProfile"
		}
		if op.ID == "listEvents" {
			kind = "EventEnvelope"
		}
		if project != "" {
			state, e := singleton(tx, project, "ProjectState")
			if e != nil {
				return nil, e
			}
			seq, e = Num(state, "event_sequence")
			if e != nil {
				return nil, e
			}
		}
		query := "SELECT body FROM domain_objects WHERE kind=?"
		args := []any{kind}
		if project != "" {
			query += " AND project=?"
			args = append(args, project)
		}
		if kind == "EventEnvelope" {
			query += " AND json_extract(body,'$.sequence')>? ORDER BY json_extract(body,'$.sequence')"
			args = append(args, after)
		} else {
			query += " ORDER BY json_extract(body,'$.created_at'),id"
		}
		rows, e := tx.Query(query, args...)
		if e != nil {
			return nil, e
		}
		items = Empty()
		for rows.Next() {
			var raw string
			if e = rows.Scan(&raw); e != nil {
				rows.Close()
				return nil, e
			}
			o, e := Decode([]byte(raw))
			if e != nil {
				rows.Close()
				return nil, e
			}
			if !p.Allowed(Str(o, "project_id"), "", "", false) {
				continue
			}
			if o["access_class"] == "VERIFIER_ONLY" && (!p.Allowed(Str(o, "project_id"), "", "", true) || !(p.HasRole("OWNER") || p.HasRole("VERIFIER"))) {
				continue
			}
			items = append(items, o)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return nil, e
		}
		// Resolve event/reference permissions after closing rows on the single connection.
		visible := Empty()
		for _, v := range items {
			if s.visible(tx, p, Str(v.(map[string]any), "project_id"), v) {
				visible = append(visible, v)
			}
		}
		items = visible
	}
	var next any
	if len(items) > limit {
		next = ID()
		tail := Object{"items": items[limit:], "snapshot_event_sequence": seq}
		_, e := tx.Exec("INSERT INTO page_cursors(id,principal,project,operation,grant_hash,body,expires_at) VALUES(?,?,?,?,?,?,?)", next, p.ID, project, operationKey, grantHash, string(Bytes(tail)), time.Now().UTC().Add(15*time.Minute).Format(time.RFC3339Nano))
		if e != nil {
			return nil, e
		}
		items = items[:limit]
	}
	// ponytail: snapshots materialize matching rows; indexed snapshot pagination replaces this when projects exceed local scale.
	return Object{"items": items, "next_cursor": next, "snapshot_event_sequence": seq}, nil
}
