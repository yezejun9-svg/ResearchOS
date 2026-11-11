package domain

import (
	"bytes"
	"context"
	"database/sql"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func remoteCall(t *testing.T, f *fixture, status int, method, path, token, key, tag string, b any) Object {
	t.Helper()
	var raw []byte
	if b != nil {
		raw = Bytes(b)
	}
	r := httptest.NewRequest(method, path, bytes.NewReader(raw))
	r.Header.Set("Content-Type", "application/json")
	if token != "" {
		r.Header.Set("Authorization", "Bearer "+token)
	}
	if key != "" {
		r.Header.Set("Idempotency-Key", key)
	}
	if tag != "" {
		r.Header.Set("If-Match", tag)
	}
	w := httptest.NewRecorder()
	f.h.ServeHTTP(w, r)
	if w.Code != status {
		t.Fatalf("%s %s status %d wanted %d: %s", method, path, w.Code, status, w.Body.String())
	}
	result, e := Decode(w.Body.Bytes())
	if e != nil {
		t.Fatal(e)
	}
	if w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("secret response may cache")
	}
	return result
}
func remoteAssert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W17_ASSERTION " + string(Bytes(Object{"id": id, "expected": want, "actual": got, "status": status, "mode": "DEVELOPMENT_FIXTURE"})))
	if status != "PASS" {
		t.Fatal(id)
	}
}
func remotePair(t *testing.T, f *fixture, owner, project string) (Object, Object) {
	challenge := remoteCall(t, f, 201, "POST", "/v1/device-pairings", owner, ID(), "", Object{"label": "phone", "project_ids": []any{project}, "expires_in_seconds": 300})
	body := Object{"challenge_id": challenge["challenge_id"], "pairing_token": challenge["pairing_token"], "device_label": "phone"}
	session := remoteCall(t, f, 200, "POST", "/v1/device-pairings/redeem", "", ID(), "", body)
	return challenge, session
}
func TestW17PairingLifecycle(t *testing.T) {
	f := setup(t)
	f.createProject()
	owner, project := f.token, f.project
	f.createProject()
	other := f.project
	f.project = project
	create := Object{"label": "phone", "project_ids": []any{project}, "expires_in_seconds": 300}
	key := ID()
	challenge := remoteCall(t, f, 201, "POST", "/v1/device-pairings", owner, key, "", create)
	replay := remoteCall(t, f, 201, "POST", "/v1/device-pairings", owner, key, "", create)
	remoteAssert(t, "pairing-replay-stable", Hash(challenge), Hash(replay))
	remoteCall(t, f, 409, "POST", "/v1/device-pairings", owner, key, "", Object{"label": "changed", "project_ids": []any{project}, "expires_in_seconds": 300})
	body := Object{"challenge_id": challenge["challenge_id"], "pairing_token": challenge["pairing_token"], "device_label": "phone"}
	redeemKey := ID()
	session := remoteCall(t, f, 200, "POST", "/v1/device-pairings/redeem", "", redeemKey, "", body)
	accessExpiry, err := time.Parse(time.RFC3339Nano, Str(session, "access_expires_at"))
	if err != nil {
		t.Fatal(err)
	}
	remoteAssert(t, "access-default-fifteen-minutes", true, time.Until(accessExpiry) > 14*time.Minute && time.Until(accessExpiry) <= 15*time.Minute)
	again := remoteCall(t, f, 200, "POST", "/v1/device-pairings/redeem", "", redeemKey, "", body)
	remoteAssert(t, "redeem-replay-stable", Hash(session), Hash(again))
	remoteCall(t, f, 401, "POST", "/v1/device-pairings/redeem", "", ID(), "", body)
	remoteCall(t, f, 401, "POST", "/v1/device-pairings", owner, key, "", create)
	device := session["device"].(map[string]any)
	token := Str(session, "access_token")
	remoteAssert(t, "default-readonly-explicit-scope", []any{"READER", []any{project}}, []any{device["role"], device["project_ids"]})
	remoteCall(t, f, 200, "GET", f.path("/state"), token, "", "", nil)
	remoteCall(t, f, 404, "GET", "/v1/projects/"+other+"/state", token, "", "", nil)
	projects := remoteCall(t, f, 200, "GET", "/v1/projects", token, "", "", nil)
	remoteAssert(t, "cross-project-list-filter", 1, len(Arr(projects, "items")))
	remoteCall(t, f, 403, "POST", f.path("/requirements"), token, ID(), "", requirementBody())
	remoteCall(t, f, 403, "POST", "/v1/device-pairings", token, ID(), "", create)
	remoteCall(t, f, 403, "GET", "/v1/devices", token, "", "", nil)
	refresh := Object{"refresh_token": session["refresh_token"]}
	refreshKey := ID()
	renewed := remoteCall(t, f, 200, "POST", "/v1/device-sessions/refresh", "", refreshKey, "", refresh)
	repeated := remoteCall(t, f, 200, "POST", "/v1/device-sessions/refresh", "", refreshKey, "", refresh)
	remoteAssert(t, "refresh-idempotent-rotation", []any{true, true}, []any{Hash(renewed) == Hash(repeated), renewed["access_token"] != session["access_token"]})
	remoteCall(t, f, 401, "GET", f.path("/state"), token, "", "", nil)
	token = Str(renewed, "access_token")
	remoteCall(t, f, 200, "GET", f.path("/state"), token, "", "", nil)
	path := "/v1/devices/" + Str(device, "id")
	granted := remoteCall(t, f, 200, "PUT", path+"/grants", owner, ID(), testTag(device), Object{"role": "OWNER", "project_ids": []any{project}, "reason": "explicit control"})
	remoteCall(t, f, 201, "POST", f.path("/requirements"), token, ID(), f.stateTag(), requirementBody())
	remoteCall(t, f, 403, "POST", "/v1/projects", token, ID(), "", projectBody())
	remoteCall(t, f, 403, "GET", "/v1/policies/run", token, "", "", nil)
	remoteCall(t, f, 403, "POST", "/v1/device-pairings", token, ID(), "", create)
	remoteCall(t, f, 412, "POST", path+"/revoke", owner, ID(), testTag(device), Object{"reason": "lost"})
	revoked := remoteCall(t, f, 200, "POST", path+"/revoke", owner, ID(), testTag(granted), Object{"reason": "lost"})
	remoteAssert(t, "revoke-state", "REVOKED", revoked["status"])
	remoteCall(t, f, 401, "GET", f.path("/state"), token, "", "", nil)
	remoteCall(t, f, 401, "POST", "/v1/device-sessions/refresh", "", ID(), "", Object{"refresh_token": renewed["refresh_token"]})
	remoteCall(t, f, 401, "POST", "/v1/device-sessions/refresh", "", refreshKey, "", refresh)
	remoteCall(t, f, 200, "GET", f.path("/state"), owner, "", "", nil)
	remoteAssert(t, "revocation-next-request-and-refresh", true, true)
	// Public fake credential canaries only. Read our fixture DB's logical tables;
	// challenge, refresh, access and replay JSON are never persistent plaintext.
	for _, table := range []string{"remote_challenges", "remote_refresh", "remote_replays", "remote_audit", "auth_credentials", "domain_objects", "outbox", "idempotency"} {
		rows, e := f.db.Query("SELECT * FROM " + table)
		if e != nil {
			t.Fatal(e)
		}
		cols, _ := rows.Columns()
		var combined strings.Builder
		for rows.Next() {
			values := make([]any, len(cols))
			ptrs := make([]any, len(cols))
			for i := range values {
				ptrs[i] = &values[i]
			}
			if e = rows.Scan(ptrs...); e != nil {
				t.Fatal(e)
			}
			for _, v := range values {
				fmt.Fprint(&combined, v)
			}
		}
		rows.Close()
		for _, secret := range []string{Str(challenge, "pairing_token"), Str(session, "access_token"), Str(session, "refresh_token"), Str(renewed, "access_token"), Str(renewed, "refresh_token")} {
			if strings.Contains(combined.String(), secret) {
				t.Fatalf("plaintext secret in %s", table)
			}
		}
	}
	remoteAssert(t, "no-plaintext-persisted-secret", true, true)
}

func TestW17RefreshReuseRevokesFamily(t *testing.T) {
	f := setup(t)
	f.createProject()
	_, session := remotePair(t, f, f.token, f.project)
	_, other := remotePair(t, f, f.token, f.project)
	body := Object{"refresh_token": session["refresh_token"]}
	key := ID()
	rotated := remoteCall(t, f, 200, "POST", "/v1/device-sessions/refresh", "", key, "", body)
	again := remoteCall(t, f, 200, "POST", "/v1/device-sessions/refresh", "", key, "", body)
	remoteAssert(t, "same-key-refresh-replay-keeps-family", Hash(rotated), Hash(again))
	remoteCall(t, f, 200, "GET", f.path("/state"), Str(rotated, "access_token"), "", "", nil)
	remoteCall(t, f, 401, "POST", "/v1/device-sessions/refresh", "", ID(), "", body)
	// Reconstruct the handler to prove revocation was committed, not cached.
	f.h = f.s.Handler()
	remoteCall(t, f, 401, "GET", f.path("/state"), Str(rotated, "access_token"), "", "", nil)
	remoteCall(t, f, 401, "POST", "/v1/device-sessions/refresh", "", ID(), "", Object{"refresh_token": rotated["refresh_token"]})
	remoteCall(t, f, 200, "GET", f.path("/state"), Str(other, "access_token"), "", "", nil)
	remoteCall(t, f, 200, "GET", f.path("/state"), f.token, "", "", nil)
	remoteAssert(t, "different-key-refresh-reuse-revokes-only-family", true, true)
}

func TestW17ExpiredRestartAndParentScope(t *testing.T) {
	f := setup(t)
	f.createProject()
	owner, project := f.token, f.project
	challenge := remoteCall(t, f, 201, "POST", "/v1/device-pairings", owner, ID(), "", Object{"label": "phone", "project_ids": []any{project}, "expires_in_seconds": 30})
	if _, e := f.db.Exec("UPDATE remote_challenges SET expires_at=? WHERE id=?", remoteExpiry(-time.Minute), challenge["challenge_id"]); e != nil {
		t.Fatal(e)
	}
	remoteCall(t, f, 401, "POST", "/v1/device-pairings/redeem", "", ID(), "", Object{"challenge_id": challenge["challenge_id"], "pairing_token": challenge["pairing_token"], "device_label": "expired"})
	_, session := remotePair(t, f, owner, project)
	token := Str(session, "access_token")
	var e error
	f.s, e = New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	f.h = f.s.Handler() // Real migration/service reconstruction; persistent auth remains.
	remoteCall(t, f, 200, "GET", f.path("/state"), token, "", "", nil)
	if _, e := f.db.Exec("DELETE FROM auth_grants WHERE principal=? AND project=?", f.owner, project); e != nil {
		t.Fatal(e)
	}
	remoteCall(t, f, 404, "GET", f.path("/state"), token, "", "", nil)
	remoteCall(t, f, 401, "POST", "/v1/device-sessions/refresh", "", ID(), "", Object{"refresh_token": session["refresh_token"]})
	remoteAssert(t, "grant-parent-intersection-after-restart", true, true)
	if e := f.s.RevokePrincipal(context.Background(), f.owner); e != nil {
		t.Fatal(e)
	}
	remoteCall(t, f, 401, "GET", f.path("/state"), token, "", "", nil)
	remoteAssert(t, "parent-revocation-cascades", true, true)
}

func TestW17ReplayExpiryOriginAndRestricted(t *testing.T) {
	f := setup(t)
	f.createProject()
	owner := f.token
	project := f.project
	body := Object{"label": "phone", "project_ids": []any{project}, "expires_in_seconds": 300}
	key := ID()
	challenge := remoteCall(t, f, 201, "POST", "/v1/device-pairings", owner, key, "", body)
	if _, e := f.db.Exec("UPDATE remote_replays SET expires_at=? WHERE operation='createDevicePairing' AND key=?", remoteExpiry(-time.Second), key); e != nil {
		t.Fatal(e)
	}
	remoteCall(t, f, 409, "POST", "/v1/device-pairings", owner, key, "", body)
	remoteCall(t, f, 428, "POST", "/v1/device-pairings", owner, "", "", body)
	remoteCall(t, f, 401, "POST", "/v1/device-pairings", "", ID(), "", body)
	remoteCall(t, f, 403, "POST", "/v1/device-pairings", owner, ID(), "", Object{"label": "none", "project_ids": []any{"ungranted"}, "expires_in_seconds": 300})
	remoteCall(t, f, 400, "POST", "/v1/device-pairings", owner, ID(), "", Object{"label": "none", "project_ids": Empty(), "expires_in_seconds": 300})
	for _, origin := range []string{"https://evil.invalid", "null", "http://example.com/", "http://example.com?token=bad"} {
		req := httptest.NewRequest("POST", "/v1/device-pairings/redeem", bytes.NewReader(Bytes(Object{"challenge_id": challenge["challenge_id"], "pairing_token": challenge["pairing_token"], "device_label": "phone"})))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Origin", origin)
		req.Header.Set("Idempotency-Key", ID())
		res := httptest.NewRecorder()
		f.h.ServeHTTP(res, req)
		if res.Code != 403 {
			t.Fatalf("bad origin status %d", res.Code)
		}
	}
	remoteAssert(t, "expired-replay-csrf-and-ungranted-scope", true, true)
	_, session := remotePair(t, f, owner, project)
	d := session["device"].(map[string]any)
	token := Str(session, "access_token")
	remoteCall(t, f, 200, "PUT", "/v1/devices/"+Str(d, "id")+"/grants", owner, ID(), testTag(d), Object{"role": "OWNER", "project_ids": []any{project}, "reason": "explicit fixture"})
	// Public fake metadata only, never a formal holdout read or registration.
	canary := "PUBLIC_FAKE_W17_RESTRICTED_CANARY"
	a := Merge(Base(project), Object{"run_id": nil, "kind": "TEST_RESULT", "evidence_kind": "SIMULATED", "validity": "CURRENT", "measurement_mode": "FIXTURE", "content_hash": Digest(nil), "storage_key": canary, "media_type": "application/json", "byte_size": 0, "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "sealed_at": Now(), "access_class": "VERIFIER_ONLY"})
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if e := f.s.put(tx, "Artifact", a); e != nil {
			return e
		}
		return f.s.event(tx, project, "Artifact", a, f.owner, ID(), "PROJECT_UPDATED")
	})
	for _, suffix := range []string{"", "/content"} {
		remoteCall(t, f, 404, "GET", f.path("/artifacts/"+Str(a, "id")+suffix), token, "", "", nil)
	}
	for _, suffix := range []string{"/artifacts", "/events"} {
		result := remoteCall(t, f, 200, "GET", f.path(suffix), token, "", "", nil)
		if strings.Contains(string(Bytes(result)), canary) || strings.Contains(string(Bytes(result)), Str(a, "id")) {
			t.Fatal("restricted canary/reference escaped")
		}
	}
	// Browser transport marker is authority-reducing: local Owner credentials
	// cannot be pasted into the remotely exposed gateway.
	req := httptest.NewRequest("GET", f.path("/state"), nil)
	req.Header.Set("Authorization", "Bearer "+owner)
	req.Header.Set("X-ResearchOS-Remote-Access", "device")
	res := httptest.NewRecorder()
	f.h.ServeHTTP(res, req)
	remoteAssert(t, "gateway-requires-device-credential", 403, res.Code)
	remoteAssert(t, "device-owner-cannot-read-restricted-artifacts-events", true, true)
}

func TestW17SSERevocation(t *testing.T) {
	f := setup(t)
	f.createProject()
	owner := f.token
	_, session := remotePair(t, f, owner, f.project)
	server, _ := fixtureHTTPServer(t, f.h)
	defer server.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, "GET", server.URL+f.path("/events/stream"), nil)
	req.Header.Set("Authorization", "Bearer "+Str(session, "access_token"))
	response, e := server.Client().Do(req)
	if e != nil {
		t.Fatal(e)
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		t.Fatalf("SSE %d", response.StatusCode)
	}
	buffer := make([]byte, len(": connected\n\n"))
	if _, e = io.ReadFull(response.Body, buffer); e != nil {
		t.Fatal(e)
	}
	device := session["device"].(map[string]any)
	start := time.Now()
	remoteCall(t, f, 200, "POST", "/v1/devices/"+Str(device, "id")+"/revoke", owner, ID(), testTag(device), Object{"reason": "lost"})
	_, e = io.ReadAll(response.Body)
	elapsed := time.Since(start)
	remoteAssert(t, "SSE-revoked-under-30seconds", []any{true, true}, []any{e == nil, elapsed < 30*time.Second})
	fmt.Println("W17_SSE_REVOCATION_MS", elapsed.Milliseconds())
}
