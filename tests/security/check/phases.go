package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

func base64Decode(s string) ([]byte, error) { return base64.StdEncoding.DecodeString(s) }
func bytesEqual(a, b []byte) bool           { return bytes.Equal(a, b) }

const sentinelSecret = "sk-SENTINEL-DO-NOT-ECHO-0123456789"

// notVerified records the checks this machine could not exercise, so the report can never read as
// a stronger claim than the evidence supports.
var notVerified []string

func skip(label, reason string) {
	notVerified = append(notVerified, label+": "+reason)
}

// ----------------------------------------------------------------------------- bootstrap phase
func bootstrapPhase(ctx context.Context, h *harness) {
	res, err := h.host.BootstrapOwner(ctx)
	ok("BOOT-CREATES-OWNER", err == nil && res != nil && res.CreatedOwner && !res.BoundExisting, err, res)
	ok("BOOT-EXACTLY-ONE-PRINCIPAL", h.count(ctx, `SELECT count(*) FROM auth_principals`) == 1,
		h.count(ctx, `SELECT count(*) FROM auth_principals`))
	ok("BOOT-OWNER-ROLE", h.count(ctx, `SELECT count(*) FROM auth_principals WHERE roles LIKE '%OWNER%' AND revoked=0`) == 1)
	ok("BOOT-SESSION-ISSUED", err == nil && res.Session.Token != "" && res.Session.ExpiresAt.After(res.Session.IssuedAt), err)
	ok("BOOT-TTL-WITHIN-CEILING", err == nil && !res.Session.ExpiresAt.After(res.Session.IssuedAt.Add(15*time.Minute)))
	if serr := fileGrantsOnlyCurrentUser(h.host.SessionFile()); serr != "" {
		ok("BOOT-SESSION-FILE-CURRENT-USER-ONLY", false, serr)
	} else {
		ok("BOOT-SESSION-FILE-CURRENT-USER-ONLY", true)
	}
	if derr := dirGrantsOnlyCurrentUser(h.dir); derr != "" {
		ok("BOOT-HOST-DIR-CURRENT-USER-ONLY", false, derr)
	} else {
		ok("BOOT-HOST-DIR-CURRENT-USER-ONLY", true)
	}
	sess, ferr := h.host.ReadSessionFile()
	ok("BOOT-SESSION-FILE-HANDS-TOKEN-TO-LOCAL-CLIENT", ferr == nil && sess.Token != "", ferr)
	h.token = sess.Token
	census := h.censusHash(ctx)

	res2, err2 := h.host.BootstrapOwner(ctx)
	ok("BOOT-SECOND-RUN-BINDS-EXISTING", err2 == nil && res2 != nil && res2.BoundExisting && !res2.CreatedOwner, err2, res2)
	ok("BOOT-SECOND-RUN-NO-NEW-PRINCIPAL", h.count(ctx, `SELECT count(*) FROM auth_principals`) == 1)
	stable := true
	for i := 0; i < 4; i++ {
		if _, e := h.host.BootstrapOwner(ctx); e != nil {
			stable = false
		}
	}
	ok("BOOT-REPEATED-STABLE", stable && h.count(ctx, `SELECT count(*) FROM auth_principals`) == 1 &&
		h.censusHash(ctx) == census, h.censusHash(ctx), census)

	var ownerID string
	h.db.QueryRowContext(ctx, `SELECT id FROM auth_principals LIMIT 1`).Scan(&ownerID)
	h.db.ExecContext(ctx, `INSERT INTO auth_principals(id,roles,can_create_project,revoked) VALUES('second-owner','["OWNER"]',0,0)`)
	_, dupErr := h.host.BootstrapOwner(ctx)
	ok("BOOT-MULTI-OWNER-REFUSED", errors.Is(dupErr, host.ErrMultipleOwners), dupErr)
	ok("BOOT-MULTI-OWNER-REPAIRS-NOTHING", h.count(ctx, `SELECT count(*) FROM auth_principals`) == 2,
		h.count(ctx, `SELECT count(*) FROM auth_principals`))
	h.db.ExecContext(ctx, `DELETE FROM auth_principals WHERE id='second-owner'`)

	// principals without an OWNER must not be promoted by the bootstrap path
	h.db.ExecContext(ctx, `INSERT INTO auth_principals(id,roles,can_create_project,revoked) VALUES('plain-worker','["READER"]',0,0)`)
	h.db.ExecContext(ctx, `UPDATE auth_principals SET revoked=1 WHERE id=?`, ownerID)
	fresh, ferr := host.New(host.Config{DB: h.db, Dir: filepath.Join(h.root, "host2"),
		ContractsDir:  filepath.Join(repoRoot(), "spec", "v2.0", "contracts"),
		MigrationFile: filepath.Join(repoRoot(), "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir:     filepath.Join(repoRoot(), "tests", "contracts", "fixtures"), Now: h.clock.Now})
	if ferr != nil {
		ok("BOOT-NO-PROMOTION-OF-EXISTING", false, ferr)
	} else {
		_, noOwner := fresh.BootstrapOwner(ctx)
		ok("BOOT-NO-PROMOTION-OF-EXISTING", errors.Is(noOwner, host.ErrNoOwner) || errors.Is(noOwner, host.ErrPrincipalRevoked), noOwner)
	}
	ok("BOOT-NO-PROMOTION-KEeps-COUNT", h.count(ctx, `SELECT count(*) FROM auth_principals`) == 2)
	h.db.ExecContext(ctx, `UPDATE auth_principals SET revoked=0 WHERE id=?`, ownerID)
	h.db.ExecContext(ctx, `DELETE FROM auth_principals WHERE id='plain-worker'`)

	// Each successful bootstrap above re-issued a credential, so only the newest one is live: the
	// session file the local client reads must name the token that works, and the token it
	// supersedes must stop working instead of lingering until its TTL.
	staleToken := h.token
	latest, lerr := h.host.ReadSessionFile()
	ok("BOOT-SESSION-FILE-HOLDS-THE-LIVE-CREDENTIAL", lerr == nil && latest.Token != "" &&
		latest.Token != staleToken, lerr)
	stStale, _ := h.post(statusCmd("w17-stale"), staleToken)
	ok("BOOT-SUPERSEDED-CREDENTIAL-REFUSED", stStale == 401, stStale)
	stLive, _ := h.post(statusCmd("w17-live"), latest.Token)
	ok("BOOT-LIVE-CREDENTIAL-ACCEPTED", stLive == 200, stLive)
	h.token = latest.Token

	before := h.censusHash(ctx)
	st, body := h.post(`{"protocol_version":"researchos-client/2","command_id":"w17-noauth","client_id":"cli-a","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`, "")
	ok("BOOT-NO-PUBLIC-OWNER-ROUTE", st == 401 && strings.Contains(string(body), "UNAUTHENTICATED"), st, string(body))
	cfg := `{"protocol_version":"researchos-client/2","command_id":"w17-cfg","client_id":"cli-a","project_id":"p1","session_id":null,"expected_revision":1,"writer_epoch":1,"method":"host.configure","payload":{"config_revision":1,"provider_id":"deepseek","base_url":"https://api.deepseek.com","model_id":"deepseek-chat","credential_ref":null}}`
	st2, body2 := h.post(cfg, h.token)
	ok("BOOT-OWNER-WITHOUT-GRANT-REFUSED", st2 == 403 && strings.Contains(string(body2), "FORBIDDEN"), st2, string(body2))
	h.db.ExecContext(ctx, `INSERT OR IGNORE INTO auth_grants(principal,project,task,run,restricted) SELECT id,'p1','','',0 FROM auth_principals WHERE roles LIKE '%OWNER%'`)
	st2b, body2b := h.post(strings.Replace(cfg, "w17-cfg", "w17-cfg-2", 1), h.token)
	ok("BOOT-HOST-CONFIGURE-NEVER-ECHOES-SECRET", st2b == 200 && !strings.Contains(string(body2b), "credential_value"), st2b, string(body2b))
	ok("BOOT-HOST-CONFIGURE-REFUSED-UNTIL-HANDLER-CARD", strings.Contains(string(body2b), "NOT_IMPLEMENTED"), string(body2b))
	ok("BOOT-REFUSED-WRITES-ARE-STATELESS", h.censusHash(ctx) == before, h.censusHash(ctx), before)
}

// ------------------------------------------------------------------------------- renewal phase
func renewPhase(ctx context.Context, h *harness) {
	first, err := h.host.ReadSessionFile()
	ok("RENEW-STARTS-FROM-BOOTSTRAP", err == nil && first.Token != "", err)
	sess, rerr := h.host.RenewSession(ctx)
	ok("RENEW-ISSUES-NEW-CREDENTIAL", rerr == nil && sess.Token != "" && sess.Token != first.Token, rerr)
	stSup, _ := h.post(statusCmd("w17-renew-superseded"), first.Token)
	ok("RENEW-SUPERSEDED-TOKEN-REFUSED", stSup == 401, stSup)
	stNew, _ := h.post(statusCmd("w17-renew-live"), sess.Token)
	ok("RENEW-NEW-TOKEN-ACCEPTED", stNew == 200, stNew)
	census := h.censusHash(ctx)
	second, serr := h.host.RenewSession(ctx)
	ok("RENEW-PRESERVES-BUSINESS-STATE", serr == nil && h.censusHash(ctx) == census, serr, h.censusHash(ctx), census)
	ok("RENEW-ROTATES-TOKEN", serr == nil && second.Token != sess.Token)
	h.token = second.Token

	fresh, ferr := host.New(host.Config{DB: h.db, Dir: filepath.Join(h.root, "host3"),
		ContractsDir:  filepath.Join(repoRoot(), "spec", "v2.0", "contracts"),
		MigrationFile: filepath.Join(repoRoot(), "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir:     filepath.Join(repoRoot(), "tests", "contracts", "fixtures"), Now: h.clock.Now})
	if ferr != nil {
		ok("RENEW-UNBOUND-HOST-REFUSED", false, ferr)
	} else {
		_, e := fresh.RenewSession(ctx)
		ok("RENEW-UNBOUND-HOST-REFUSED", errors.Is(e, host.ErrNotBound), e)
	}

	var ownerID string
	h.db.QueryRowContext(ctx, `SELECT id FROM auth_principals WHERE roles LIKE '%OWNER%' LIMIT 1`).Scan(&ownerID)
	h.db.ExecContext(ctx, `UPDATE auth_principals SET revoked=1 WHERE id=?`, ownerID)
	_, revErr := h.host.RenewSession(ctx)
	ok("RENEW-REVOKED-PRINCIPAL-REFUSED", errors.Is(revErr, host.ErrPrincipalRevoked), revErr)
	st, body := h.post(`{"protocol_version":"researchos-client/2","command_id":"w17-revoked","client_id":"cli-a","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`, h.token)
	ok("REVOKE-KILLS-LIVE-SESSION", st == 401 && strings.Contains(string(body), "UNAUTHENTICATED"), st, string(body))
	h.db.ExecContext(ctx, `UPDATE auth_principals SET revoked=0 WHERE id=?`, ownerID)

	h.db.ExecContext(ctx, `UPDATE auth_credentials SET expires_at=? WHERE principal=?`,
		time.Now().UTC().Add(-time.Hour).Format(time.RFC3339Nano), ownerID)
	before := h.censusHash(ctx)
	st2, _ := h.post(`{"protocol_version":"researchos-client/2","command_id":"w17-expired","client_id":"cli-a","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`, h.token)
	ok("EXPIRED-CREDENTIAL-REFUSED", st2 == 401, st2)
	ok("EXPIRY-PRESERVES-PROJECTS-AND-SESSIONS", h.censusHash(ctx) == before, h.censusHash(ctx), before)
	renewed, e := h.host.RenewSession(ctx)
	ok("EXPIRY-THEN-RENEW-RESTORES-ACCESS", e == nil && renewed.Token != "", e)
	h.token = renewed.Token
	st3, _ := h.post(`{"protocol_version":"researchos-client/2","command_id":"w17-after-renew","client_id":"cli-a","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`, h.token)
	ok("RENEWED-CREDENTIAL-WORKS", st3 == 200, st3)
	// Rows are history: the host revokes what it supersedes rather than deleting credentials, so
	// the honest bound is on the total number ever issued by this qualification run.
	ok("RENEW-CREDENTIAL-ROWS-BOUNDED", h.count(ctx, `SELECT count(*) FROM auth_credentials`) <= 24,
		h.count(ctx, `SELECT count(*) FROM auth_credentials`))
	// Renewal rotates rather than accumulates: exactly one credential for the bound principal is
	// still live, so a stolen old token cannot simply wait out the TTL.
	live := h.count1(ctx, `SELECT count(*) FROM auth_credentials WHERE revoked=0 AND expires_at>?
		AND principal=(SELECT id FROM auth_principals WHERE roles LIKE '%OWNER%' LIMIT 1)`,
		time.Now().UTC().Add(-time.Second).Format(time.RFC3339Nano))
	ok("RENEW-LEAVES-ONE-LIVE-CREDENTIAL", live == 1, live)
}

// --------------------------------------------------------------------------- credential phase
func credentialPhase(ctx context.Context, h *harness) {
	req := frame(host.KindCredentialImportRequest, "cli-desktop", map[string]any{
		"provider_id": "deepseek", "credential_kind": "API_KEY",
		"credential_value": sentinelSecret, "replace_credential_ref": nil})
	reply, err := h.host.HandleNative(req, true, nil)
	ok("CRED-IMPORT-ACCEPTED", err == nil, err)
	kind, payload, _ := decodeReply(reply)
	ref, _ := payload["credential_ref"].(string)
	status, _ := payload["status"].(string)
	ok("CRED-IMPORT-REF-AND-AVAILABLE", err == nil && kind == host.KindCredentialImportResult &&
		strings.HasPrefix(ref, "cred-") && status == "AVAILABLE", kind, ref, status)
	ok("CRED-IMPORT-REPLY-HAS-NO-SECRET", !strings.Contains(string(reply), sentinelSecret), string(reply))
	ok("CRED-STATUS-AVAILABLE", h.host.CredentialStatus(ref) == "AVAILABLE", h.host.CredentialStatus(ref))
	ok("CRED-USABLE-ONLY-INSIDE-HOST", h.host.CredentialUsable(ref), ref)

	// argv must never be a carrier: put the sentinel in the process arguments and prove nothing
	// absorbs it, then re-import through the real frame path.
	argsBefore := os.Args
	os.Args = []string{"researchos", "--credential", sentinelSecret}
	_, err2 := h.host.HandleNative(req, true, nil)
	os.Args = argsBefore
	ok("CRED-IMPORT-STILL-WORKS-WITH-SECRET-IN-ARGV", err2 == nil, err2)
	srcLeaks := sourceReferences([]string{"internal/host", "internal/auth"}, []string{"os.Args", "os.Environ"})
	ok("CRED-HOST-NEVER-READS-ARGV-OR-ENV", srcLeaks == 0, srcLeaks)

	leaks := diskLeaks(h.dir, sentinelSecret)
	ok("CRED-NO-PLAINTEXT-ON-DISK", len(leaks) == 0, leaks)

	// Protection is graded, not asserted: a unique material is imported, the stored blob is
	// compared against the material in every reversible encoding, and one flipped byte inside the
	// blob must make it unusable. An identity transform (or any reversible encoding) fails the
	// first, and a blob without integrity fails the second.
	uniq := randomToken()
	uniqReply, uerr := h.host.HandleNative(frame(host.KindCredentialImportRequest, "cli-desktop",
		map[string]any{"provider_id": "deepseek", "credential_kind": "API_KEY",
			"credential_value": uniq, "replace_credential_ref": nil}), true, nil)
	uniqRef := ""
	if uerr == nil {
		_, up, _ := decodeReply(uniqReply)
		uniqRef, _ = up["credential_ref"].(string)
	}
	ok("CRED-UNIQUE-IMPORT-ACCEPTED", uerr == nil && uniqRef != "", uerr)
	ok("CRED-UNIQUE-NO-PLAINTEXT-ON-DISK", len(diskLeaks(h.dir, uniq)) == 0, diskLeaks(h.dir, uniq))
	rec, rerr := vaultRecord(h.dir, uniqRef)
	wrappedLen, materialLen := 0, len(uniq)
	if rerr == nil {
		if buf, derr := base64Decode(fmt.Sprint(rec["wrapped"])); derr == nil {
			wrappedLen = len(buf)
			ok("CRED-WRAPPED-DIFFERS-FROM-MATERIAL", !bytesEqual(buf, []byte(uniq)), len(buf))
		} else {
			ok("CRED-WRAPPED-DIFFERS-FROM-MATERIAL", false, derr)
		}
	} else {
		ok("CRED-WRAPPED-DIFFERS-FROM-MATERIAL", false, rerr)
	}
	ok("CRED-WRAPPED-LARGER-THAN-MATERIAL", wrappedLen > materialLen, wrappedLen, materialLen)
	ok("CRED-USABLE-BEFORE-TAMPER", h.host.CredentialUsable(uniqRef), uniqRef)
	terr := tamperVaultRecord(h.dir, uniqRef)
	ok("CRED-TAMPER-APPLIED", terr == nil, terr)
	ok("CRED-WRAPPED-TAMPER-MAKES-UNUSABLE", !h.host.CredentialUsable(uniqRef), uniqRef)
	logLine, _ := json.Marshal(map[string]any{"event": "credential.import", "reply": json.RawMessage(reply)})
	ok("CRED-NO-PLAINTEXT-IN-LOG-LINE", !strings.Contains(string(logLine), sentinelSecret), string(logLine))
	envelopeLeak := fmt.Sprintf(`{"protocol_version":"researchos-client/2","command_id":"x","client_id":"c","project_id":"p1","session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.configure","payload":{"config_revision":1,"provider_id":"deepseek","base_url":"https://api.deepseek.com","model_id":"m","credential_ref":null,"credential_value":"%s"}}`, sentinelSecret)
	_, envErr := decodeEnvelopeStrict(envelopeLeak)
	ok("CRED-ENVELOPE-REFUSES-SECRET-FIELD", envErr != nil, envErr)
	ok("CRED-ENVELOPE-LEAK-NOT-PERSISTED", len(diskLeaks(h.dir, sentinelSecret)) == 0)

	bad := []struct {
		label   string
		payload map[string]any
	}{
		{"CRED-REJECT-MISSING-FIELD", map[string]any{"credential_kind": "API_KEY", "credential_value": "x", "replace_credential_ref": nil}},
		{"CRED-REJECT-BAD-KIND", map[string]any{"provider_id": "p", "credential_kind": "NOT_A_KIND", "credential_value": "x", "replace_credential_ref": nil}},
		{"CRED-REJECT-EMPTY-VALUE", map[string]any{"provider_id": "p", "credential_kind": "API_KEY", "credential_value": "", "replace_credential_ref": nil}},
		{"CRED-REJECT-HUGE-VALUE", map[string]any{"provider_id": "p", "credential_kind": "API_KEY", "credential_value": strings.Repeat("a", 70000), "replace_credential_ref": nil}},
		{"CRED-REJECT-EXTRA-FIELD", map[string]any{"provider_id": "p", "credential_kind": "API_KEY", "credential_value": "x", "replace_credential_ref": nil, "extra": 1}},
	}
	for _, b := range bad {
		_, e := h.host.HandleNative(frame(host.KindCredentialImportRequest, "cli-desktop", b.payload), true, nil)
		ok(b.label, e != nil, e)
	}

	replace := frame(host.KindCredentialImportRequest, "cli-desktop", map[string]any{
		"provider_id": "deepseek", "credential_kind": "API_KEY",
		"credential_value": sentinelSecret + "-rotated", "replace_credential_ref": ref})
	reply2, e := h.host.HandleNative(replace, true, nil)
	newRef := ""
	if e == nil {
		_, p2, _ := decodeReply(reply2)
		newRef, _ = p2["credential_ref"].(string)
	}
	ok("CRED-REPLACE-ISSUES-NEW-REF", e == nil && newRef != "" && newRef != ref, e, newRef)
	ok("CRED-REPLACE-REVOKES-OLD", h.host.CredentialStatus(ref) == "REVOKED" && !h.host.CredentialUsable(ref),
		h.host.CredentialStatus(ref))
	ok("CRED-NEW-REF-USABLE", h.host.CredentialStatus(newRef) == "AVAILABLE" && h.host.CredentialUsable(newRef))
	ok("CRED-UNKNOWN-STATUS-MISSING", h.host.CredentialStatus("cred-nope") == "MISSING")
	clean, badNames := vaultHasNoReadAPI()
	ok("CRED-NO-PLAINTEXT-READ-API", clean, badNames)
	refs, _ := h.host.VaultRefs()
	ok("CRED-REFS-LIST-REFERENCES-ONLY", len(refs) >= 1 && !strings.Contains(strings.Join(refs, ","), sentinelSecret), refs)
}

// ---------------------------------------------------------------------------- workspace phase
func workspacePhase(ctx context.Context, h *harness) {
	base := filepath.Join(h.root, "ws")
	mustMkTree(base)
	outside := filepath.Join(h.root, "outside")
	os.MkdirAll(outside, 0o755)
	os.WriteFile(filepath.Join(outside, "c.md"), []byte("escape"), 0o600)
	hook := func(string) (string, error) { return base, nil }

	reply, err := h.host.HandleNative(frame(host.KindWorkspaceChooseRequest, "cli-desktop",
		map[string]any{"requested_path": nil, "requested_access": "READ_WRITE"}), true, hook)
	ok("WS-CHOOSE-ACCEPTED", err == nil, err)
	_, payload, _ := decodeReply(reply)
	selRef, _ := payload["selection_ref"].(string)
	expiry, _ := payload["expires_at"].(string)
	ok("WS-SELECTION-ISSUED", strings.HasPrefix(selRef, "sel-") && expiry != "", selRef)
	exp, perr := time.Parse(time.RFC3339Nano, expiry)
	ok("WS-SELECTION-TTL-FIVE-MINUTES", perr == nil && exp.Sub(h.clock.Now()) > 4*time.Minute &&
		exp.Sub(h.clock.Now()) <= 5*time.Minute+time.Second, perr, exp.Sub(h.clock.Now()))

	rec, cerr := h.host.ConsumeSelection(selRef, "cli-desktop")
	ok("WS-SELECTION-CONSUMED-ONCE", cerr == nil && rec != nil && rec.Access == host.AccessReadWrite, cerr)
	_, again := h.host.ConsumeSelection(selRef, "cli-desktop")
	ok("WS-SELECTION-SINGLE-USE", errors.Is(again, host.ErrSelectionUsed), again)

	// expiry is enforced even for a reference that was never used
	reply2, err2 := h.host.HandleNative(frame(host.KindWorkspaceChooseRequest, "cli-cli",
		map[string]any{"requested_path": nil, "requested_access": "READ_ONLY"}), true, hook)
	ok("WS-SECOND-CHOOSE-OK", err2 == nil, err2)
	_, payload2, _ := decodeReply(reply2)
	sel2, _ := payload2["selection_ref"].(string)
	h.clock.Add(6 * time.Minute)
	_, expiredErr := h.host.ConsumeSelection(sel2, "cli-cli")
	ok("WS-SELECTION-EXPIRED", errors.Is(expiredErr, host.ErrSelectionExpired), expiredErr)
	h.clock.Add(-6 * time.Minute)

	// a foreign client cannot redeem someone else's selection
	reply3, err3 := h.host.HandleNative(frame(host.KindWorkspaceChooseRequest, "cli-cli",
		map[string]any{"requested_path": nil, "requested_access": "READ_ONLY"}), true, hook)
	ok("WS-THIRD-CHOOSE-OK", err3 == nil, err3)
	_, payload3, _ := decodeReply(reply3)
	sel3, _ := payload3["selection_ref"].(string)
	_, foreignErr := h.host.ConsumeSelection(sel3, "cli-other")
	ok("WS-SELECTION-FOREIGN-CLIENT-REFUSED", errors.Is(foreignErr, host.ErrSelectionForeign), foreignErr)

	h.db.ExecContext(ctx, `INSERT OR IGNORE INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p1','Project','p1',1,'{}',0)`)
	h.db.ExecContext(ctx, `INSERT OR IGNORE INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p1','Run','run-w17',1,'{"status":"RUNNING"}',0)`)
	roots := h.host.Roots()
	ok("WS-ROOT-REGISTERED", len(roots) >= 3, len(roots))
	rootRef := ""
	for _, r := range roots {
		if !r.Revoked && r.Access == host.AccessReadWrite {
			rootRef = r.Ref
		}
	}
	var pinned bool
	for _, r := range roots {
		if r.Ref == rootRef {
			pinned = r.VolumeID != "" && r.FileID != 0 && r.FinalPath != ""
		}
	}
	ok("WS-ROOT-PINNED-VOLUME-AND-INDEX", rootRef != "" && pinned, rootRef)

	abs, rerr := h.host.ResolveWorkspace(rootRef, "notes/a.md", host.AccessReadOnly)
	ok("WS-RESOLVE-ALLOWED", rerr == nil && strings.HasSuffix(abs, filepath.Join("notes", "a.md")), rerr, abs)

	// A link planted *inside* the root is the escape the pinned root identity cannot see: the root
	// itself is untouched, so only the per-access reparse walk can stop it.
	roRef := roots[len(roots)-1].Ref
	inside := filepath.Join(base, "notes", "jlink")
	if made, reason := makeJunction(inside, outside); made {
		_, je := h.host.ResolveWorkspace(rootRef, "notes/jlink/c.md", host.AccessReadOnly)
		ok("WS-LINK-INSIDE-ROOT-REJECTED", errors.Is(je, host.ErrPathReparsePoint), je)
		_, jeRO := h.host.ResolveWorkspace(roRef, "notes/jlink/c.md", host.AccessReadOnly)
		ok("WS-LINK-INSIDE-READONLY-ROOT-REJECTED", errors.Is(jeRO, host.ErrPathReparsePoint), jeRO)
		removeJunction(inside)
		_, afterErr := h.host.ResolveWorkspace(rootRef, "notes/a.md", host.AccessReadOnly)
		ok("WS-RESOLVE-ALLOWED-AFTER-LINK-REMOVED", afterErr == nil, afterErr)
	} else {
		skip("WS-LINK-INSIDE-ROOT-REJECTED", reason)
		skip("WS-LINK-INSIDE-READONLY-ROOT-REJECTED", reason)
	}

	cases := []struct{ label, path string }{
		{"WS-REJECT-TRAVERSAL", "../outside/c.md"},
		{"WS-REJECT-DEEP-TRAVERSAL", "notes/../../outside/c.md"},
		{"WS-REJECT-ABSOLUTE", "/etc/passwd"},
		{"WS-REJECT-WINDOWS-ABSOLUTE", `\Windows\win.ini`},
		{"WS-REJECT-DRIVE", "C:/Windows/win.ini"},
		{"WS-REJECT-UNC", `\\server\share\file`},
		{"WS-REJECT-ADS", "notes/a.md:hidden"},
		{"WS-REJECT-NUL", "notes/a\x00.md"},
		{"WS-REJECT-EMPTY", ""},
		{"WS-REJECT-DOTDOT-ONLY", ".."},
	}
	for _, c := range cases {
		_, e := h.host.ResolveWorkspace(rootRef, c.path, host.AccessReadOnly)
		ok(c.label, e != nil, c.path, e)
	}

	// A read-only binding refuses a write request, and the same call against a read-write binding
	// must succeed: without the second half the first assertion would also pass on a host that
	// denies everything.
	_, denied := h.host.ResolveWorkspace(roRef, "notes/a.md", host.AccessReadWrite)
	ok("WS-READ-ONLY-ROOT-DENIES-WRITE", errors.Is(denied, host.ErrRootDenied), denied)
	_, allowed := h.host.ResolveWorkspace(rootRef, "notes/a.md", host.AccessReadWrite)
	ok("WS-READ-WRITE-ROOT-ALLOWS-WRITE", allowed == nil, allowed)

	// A client that names its own directory with no user chooser behind it is refused, and the
	// refusal must not leave a binding or a spendable selection reference behind.
	rootsBefore := len(h.host.Roots())
	selBefore := h.host.OutstandingSelections()
	_, namedErr := h.host.HandleNative(frame(host.KindWorkspaceChooseRequest, "cli-evil",
		map[string]any{"requested_path": outside, "requested_access": "READ_WRITE"}), true, nil)
	ok("WS-CLIENT-NAMED-PATH-REFUSED-WITHOUT-CHOOSER", errors.Is(namedErr, host.ErrUntrustedPathChoice), namedErr)
	ok("WS-REFUSED-CHOICE-REGISTERS-NOTHING", len(h.host.Roots()) == rootsBefore &&
		h.host.OutstandingSelections() == selBefore, len(h.host.Roots()), rootsBefore,
		h.host.OutstandingSelections(), selBefore)
	// the same request with a real chooser is accepted, so the refusal above is not blanket
	replyNamed, namedOK := h.host.HandleNative(frame(host.KindWorkspaceChooseRequest, "cli-desktop",
		map[string]any{"requested_path": outside, "requested_access": "READ_ONLY"}), true,
		func(string) (string, error) { return base, nil })
	ok("WS-CHOOSER-CONFIRMED-PATH-ACCEPTED", namedOK == nil && replyNamed != nil, namedOK)
	// What the chooser returned is what gets bound. The client hinted at a different directory on
	// purpose, so a host that trusted the hint instead of the choice is visible here.
	_, hintPayload, _ := decodeReply(replyNamed)
	hintDisplay, _ := hintPayload["display_path"].(string)
	ok("WS-CHOOSER-RETURN-WINS-OVER-CLIENT-HINT", hintDisplay != "" &&
		strings.EqualFold(filepath.Clean(hintDisplay), filepath.Clean(base)) &&
		!strings.EqualFold(filepath.Clean(hintDisplay), filepath.Clean(outside)), hintDisplay, base, outside)
	bound := false
	for _, r := range h.host.Roots() {
		if strings.EqualFold(filepath.Clean(r.RealPath), filepath.Clean(base)) &&
			!strings.EqualFold(filepath.Clean(r.RealPath), filepath.Clean(outside)) {
			bound = true
		}
	}
	ok("WS-BOUND-ROOT-IS-CHOSEN-DIRECTORY", bound, h.host.Roots())

	// the same path pointing at a different directory must be detected by the pinned identity
	os.Rename(base, base+"-orig")
	os.MkdirAll(filepath.Join(base, "notes"), 0o755)
	os.WriteFile(filepath.Join(base, "notes", "a.md"), []byte("swapped"), 0o600)
	_, swapErr := h.host.ResolveWorkspace(rootRef, "notes/a.md", host.AccessReadOnly)
	ok("WS-DIRECTORY-REPLACEMENT-DETECTED", swapErr != nil, swapErr)
	os.RemoveAll(base)
	os.Rename(base+"-orig", base)

	// a junction or symlink swap is the same attack with OS link semantics
	if made, reason := makeJunction(base, outside); made {
		_, jerr := h.host.ResolveWorkspace(rootRef, "notes/a.md", host.AccessReadOnly)
		ok("WS-JUNCTION-SWAP-DETECTED", jerr != nil, jerr)
		removeJunction(base)
		mustMkTree(base)
	} else {
		skip("WS-JUNCTION-SWAP-DETECTED", reason)
	}

	if e := h.host.RevokeWorkspace(rootRef); e != nil {
		ok("WS-REVOKE-REFUSES-WRITES", false, e)
	} else {
		_, after := h.host.ResolveWorkspace(rootRef, "notes/a.md", host.AccessReadOnly)
		ok("WS-REVOKE-REFUSES-WRITES", errors.Is(after, host.ErrRootRevoked), after)
		ok("WS-REVOKED-REPORTED-NOT-EMPTY", h.host.WorkspaceStatus(rootRef) == "REVOKED", h.host.WorkspaceStatus(rootRef))
		found := false
		for _, r := range h.host.Roots() {
			if r.Ref == rootRef && r.Revoked {
				found = true
			}
		}
		ok("WS-REVOKED-ROOT-STILL-LISTED", found, h.host.Roots())
	}
	_, unknown := h.host.ResolveWorkspace("ws-nope", "notes/a.md", host.AccessReadOnly)
	ok("WS-UNKNOWN-ROOT-NOT-FOUND", errors.Is(unknown, host.ErrRootUnknown), unknown)
}

// --------------------------------------------------------------------------- transport phase
func transportPhase(ctx context.Context, h *harness) {
	id, err := auth.Current()
	ok("OS-IDENTITY-AVAILABLE", err == nil && id.Ref != "" && id.Kind == "WINDOWS_SID", err, id)
	self, perr := auth.ProcessIdentity(uint32(os.Getpid()))
	ok("OS-IDENTITY-SAME-USER-MATCHES", perr == nil && id.SameUser(self), perr, self)
	if peer, verr := auth.VerifyProcess(uint32(os.Getpid()), id); verr != nil || !id.SameUser(peer) {
		ok("OS-IDENTITY-VERIFY-SELF", false, verr, peer)
	} else {
		ok("OS-IDENTITY-VERIFY-SELF", true)
	}
	// deterministic negative: a foreign SID string is never the same principal, and a frame from
	// an unverified peer is refused regardless of what the pipe ACL claims
	foreign := auth.Identity{Kind: "WINDOWS_SID", VID: "S-1-5-21-1111111111-2222222222-3333333333-1000", Ref: "windows_sid:other"}
	ok("OS-IDENTITY-FOREIGN-SID-NOT-SAME", !id.SameUser(foreign), foreign)
	pid, pidErr := foreignAccountPID()
	if pidErr != nil {
		skip("OS-IDENTITY-OTHER-ACCOUNT-REFUSED", pidErr.Error())
	} else {
		peer, verr := auth.VerifyProcess(pid, id)
		ok("OS-IDENTITY-OTHER-ACCOUNT-REFUSED", verr != nil && !id.SameUser(peer), verr, peer)
	}
	_, zeroErr := auth.VerifyProcess(0, id)
	ok("OS-IDENTITY-PID-ZERO-REFUSED", zeroErr != nil, zeroErr)
	// The peer answer must come from the OS rather than from a constant: an id that is not a live
	// process may not resolve to anyone, and the system process may never be reported as this user.
	_, highErr := auth.ProcessIdentity(0x7FFFFFC0)
	ok("OS-IDENTITY-NONEXISTENT-PID-UNRESOLVED", highErr != nil, highErr)
	sysPeer, sysErr := auth.ProcessIdentity(4)
	ok("OS-IDENTITY-SYSTEM-PID-NOT-SELF", sysErr != nil || !id.SameUser(sysPeer), sysErr, sysPeer)

	census := h.censusHash(ctx)
	_, untrusted := h.host.HandleNative(frame(host.KindUserBootstrapRequest, "cli-x", map[string]any{}), false, nil)
	ok("IPC-UNVERIFIED-SENDER-REFUSED", errors.Is(untrusted, host.ErrFrameUntrusted), untrusted)
	ok("IPC-REFUSAL-WRITES-NOTHING", h.censusHash(ctx) == census)

	oversized := make([]byte, host.MaxNativeFrameBytes+1)
	for i := range oversized {
		oversized[i] = 'a'
	}
	_, bigErr := h.host.HandleNative(oversized, true, nil)
	ok("IPC-OVERSIZED-FRAME-REFUSED", errors.Is(bigErr, host.ErrFrameTooLarge), bigErr)
	_, junk := h.host.HandleNative([]byte("not json"), true, nil)
	ok("IPC-MALFORMED-FRAME-REFUSED", errors.Is(junk, host.ErrFrameShape), junk)
	_, noClient := h.host.HandleNative([]byte(`{"kind":"NATIVE_USER_BOOTSTRAP_REQUEST","payload":{}}`), true, nil)
	ok("IPC-MISSING-CLIENT-REFUSED", errors.Is(noClient, host.ErrFrameShape), noClient)
	_, extra := h.host.HandleNative([]byte(`{"kind":"NATIVE_USER_BOOTSTRAP_REQUEST","client_id":"c","payload":{},"extra":1}`), true, nil)
	ok("IPC-FRAME-EXTRA-FIELD-REFUSED", errors.Is(extra, host.ErrFrameShape), extra)
	_, unknownKind := h.host.HandleNative(frame("NATIVE_SHELL_EXEC_REQUEST", "c", map[string]any{"cmd": "dir"}), true, nil)
	ok("IPC-UNKNOWN-KIND-REFUSED", unknownKind != nil && !strings.Contains(fmt.Sprint(unknownKind), "dir"), unknownKind)
	_, emptyPayload := h.host.HandleNative([]byte(`{"kind":"NATIVE_CREDENTIAL_IMPORT_REQUEST","client_id":"c","payload":{}}`), true, nil)
	ok("IPC-PAYLOAD-GRADED-BY-CONTRACT", errors.Is(emptyPayload, host.ErrFrameShape), emptyPayload)

	pipeName := host.PipeName(h.host.InstanceID())
	preToken := h.token
	ownersBefore := h.count(ctx, `SELECT count(*) FROM auth_principals`)
	sctx, cancel := context.WithCancel(ctx)
	go h.host.ServeNative(sctx, pipeName)
	boot, derr := host.DialNative(pipeName, frame(host.KindUserBootstrapRequest, "cli-desktop", map[string]any{}))
	ok("IPC-PIPE-ROUNDTRIP", derr == nil && len(boot) > 0, derr, string(boot))
	if derr == nil {
		kind, payload, errObj := decodeReply(boot)
		ok("IPC-PIPE-RESULT-SHAPE", errObj == nil && kind == host.KindUserBootstrapResult &&
			payload["credential_exposed_to_renderer"] == false &&
			strings.HasPrefix(fmt.Sprint(payload["host_instance_id"]), "host-") &&
			payload["protocol_version"] == "researchos-client/2" &&
			fmt.Sprint(payload["client_id"]) == "cli-desktop", kind, payload, errObj)
		ok("IPC-PIPE-NO-CREDENTIAL-IN-FRAME", !strings.Contains(string(boot), `"token"`) &&
			!strings.Contains(string(boot), "credential_value"), string(boot))
	}
	_, berr := host.DialNative(host.PipeName("absent-host"), frame(host.KindUserBootstrapRequest, "cli-x", map[string]any{}))
	ok("IPC-PIPE-ABSENT-HOST-REFUSED", berr != nil, berr)

	// The bridge's own bootstrap supersedes the credential it replaced, over the real transport.
	stPipeSup, _ := h.post(statusCmd("w17-pipe-superseded"), preToken)
	ok("IPC-PIPE-BOOTSTRAP-SUPERSEDES-OLD-TOKEN", stPipeSup == 401, stPipeSup)

	// The serve path decides from the resolved peer, so a connection the OS reports as another
	// account is refused before any frame is handled. This is the case the pipe DACL alone cannot
	// show, and it is what makes the identity comparison load-bearing rather than decorative.
	foreignPeer := auth.Identity{Kind: "WINDOWS_SID", VID: "S-1-5-21-1111111111-2222222222-3333333333-1000",
		Ref: "windows_sid:foreign"}
	fh, ferr := h.newHost(filepath.Join(h.root, "host-peer"), func(c *host.Config) {
		c.PeerIdentityResolver = func(uint32) (auth.Identity, error) { return foreignPeer, nil }
	})
	if ferr != nil {
		ok("IPC-SERVE-FOREIGN-PEER-REFUSED", false, ferr)
	} else {
		fctx, fcancel := context.WithCancel(ctx)
		go fh.ServeNative(fctx, host.PipeName(fh.InstanceID()))
		fboot, fderr := host.DialNative(host.PipeName(fh.InstanceID()),
			frame(host.KindUserBootstrapRequest, "cli-desktop", map[string]any{}))
		_, _, fobj := decodeReply(fboot)
		ok("IPC-SERVE-FOREIGN-PEER-REFUSED", fderr == nil && strings.Contains(string(fboot), "NATIVE_ERROR") &&
			strings.Contains(string(fboot), "UNAUTHENTICATED") && fobj != nil &&
			!strings.Contains(string(fboot), host.KindUserBootstrapResult), fderr, string(fboot))
		_, serr := os.Stat(fh.SessionFile())
		ok("IPC-SERVE-FOREIGN-PEER-WROTE-NOTHING", os.IsNotExist(serr) &&
			h.count(ctx, `SELECT count(*) FROM auth_principals`) == ownersBefore, serr)
		// A transport-level refusal must not echo what it refused. A unique material is offered to
		// a host that will turn it away, and the error frame plus the whole host directory are
		// then searched: the material may not appear in the reply, on disk, or in any record.
		pipeMaterial := randomToken()
		pframe, perr := host.DialNative(host.PipeName(fh.InstanceID()),
			frame(host.KindCredentialImportRequest, "cli-desktop", map[string]any{
				"provider_id": "deepseek", "credential_kind": "API_KEY",
				"credential_value": pipeMaterial, "replace_credential_ref": nil}))
		ok("IPC-PIPE-REFUSAL-NEVER-ECHOES-MATERIAL", perr == nil &&
			strings.Contains(string(pframe), "NATIVE_ERROR") &&
			!strings.Contains(string(pframe), pipeMaterial) &&
			!strings.Contains(string(pframe), "credential_value"), perr, len(pframe))
		ok("IPC-PIPE-REFUSAL-STORES-NOTHING", len(diskLeaks(filepath.Join(h.root, "host-peer"), pipeMaterial)) == 0,
			diskLeaks(filepath.Join(h.root, "host-peer"), pipeMaterial))
		fcancel()
	}
	bh, berr2 := h.newHost(filepath.Join(h.root, "host-unknown-peer"), func(c *host.Config) {
		c.PeerIdentityResolver = func(uint32) (auth.Identity, error) {
			return auth.Identity{}, errors.New("peer identity unavailable")
		}
	})
	if berr2 != nil {
		ok("IPC-SERVE-UNRESOLVED-PEER-REFUSED", false, berr2)
	} else {
		bctx, bcancel := context.WithCancel(ctx)
		go bh.ServeNative(bctx, host.PipeName(bh.InstanceID()))
		bframe, bderr := host.DialNative(host.PipeName(bh.InstanceID()),
			frame(host.KindCredentialImportRequest, "cli-desktop", map[string]any{
				"provider_id": "deepseek", "credential_kind": "API_KEY",
				"credential_value": randomToken(), "replace_credential_ref": nil}))
		ok("IPC-SERVE-UNRESOLVED-PEER-REFUSED", bderr == nil && strings.Contains(string(bframe), "NATIVE_ERROR"),
			bderr, string(bframe))
		_, bserr := os.Stat(bh.SessionFile())
		ok("IPC-SERVE-UNRESOLVED-PEER-WROTE-NOTHING", os.IsNotExist(bserr), bserr)
		bcancel()
	}
	cancel()
}

// --------------------------------------------------------------------------- grading phase
// Reply-side contract grading has to be load-bearing, so it is tested by outcome instead of by
// trust: a host built for an unsupported protocol version has its reply refused AND its staged
// local state withdrawn, while the same call on a host with the pinned version succeeds. Without
// the second half, "nothing ever works" would look identical to "nothing leaks".
func gradingPhase(ctx context.Context, h *harness) {
	revoked := func() int64 {
		return h.count(ctx, `SELECT count(*) FROM auth_credentials WHERE revoked=1`)
	}
	bad, err := h.newHost(filepath.Join(h.root, "host-bad-version"), func(c *host.Config) {
		c.ProtocolVersion = "researchos-client/1"
	})
	if err != nil {
		ok("NATIVE-REPLY-GRADING-HOST-BUILT", false, err)
		return
	}
	ok("NATIVE-REPLY-GRADING-HOST-BUILT", true)
	revBefore := revoked()
	_, gerr := bad.HandleNative(frame(host.KindUserBootstrapRequest, "cli-desktop", map[string]any{}), true, nil)
	ok("NATIVE-REPLY-GRADING-REFUSES-UNSUPPORTED-VERSION", errors.Is(gerr, host.ErrFrameShape), gerr)
	if _, serr := os.Stat(bad.SessionFile()); os.IsNotExist(serr) {
		ok("NATIVE-REPLY-GRADING-WITHDRAWS-SESSION-FILE", true)
	} else {
		ok("NATIVE-REPLY-GRADING-WITHDRAWS-SESSION-FILE", false, serr)
	}
	// The withdrawal is a revoke, not a delete: exactly one more row is marked revoked and none of
	// the earlier history disappears.
	ok("NATIVE-REPLY-GRADING-WITHDRAWS-CREDENTIAL", revoked() == revBefore+1, revoked(), revBefore)

	good, gerr2 := h.newHost(filepath.Join(h.root, "host-pinned-version"), nil)
	if gerr2 != nil {
		ok("NATIVE-REPLY-GRADING-ALLOWS-PINNED-VERSION", false, gerr2)
		return
	}
	_, oerr := good.HandleNative(frame(host.KindUserBootstrapRequest, "cli-desktop", map[string]any{}), true, nil)
	ok("NATIVE-REPLY-GRADING-ALLOWS-PINNED-VERSION", oerr == nil, oerr)
	if _, serr := os.Stat(good.SessionFile()); serr == nil {
		ok("NATIVE-REPLY-GRADING-KEEPS-ACCEPTED-SESSION", true)
	} else {
		ok("NATIVE-REPLY-GRADING-KEEPS-ACCEPTED-SESSION", false, serr)
	}
	sessGood, rerr := good.ReadSessionFile()
	st, _ := h.post(statusCmd("w17-graded-live"), sessGood.Token)
	ok("NATIVE-REPLY-GRADING-ACCEPTED-CREDENTIAL-WORKS", rerr == nil && st == 200, rerr, st)
}

// ------------------------------------------------------------------- HTTP chain on the bridges token
func httpChainPhase(ctx context.Context, h *harness) {
	// The bridge hands the local client its live credential through the private file; every later
	// HTTP call is made with that one, which is the point of "no manual token copying".
	cur, cerr := h.host.ReadSessionFile()
	ok("HTTP-SESSION-FILE-IS-THE-CLIENT-HANDOFF", cerr == nil && cur.Token != "", cerr)
	h.token = cur.Token
	st, body := h.post(`{"protocol_version":"researchos-client/2","command_id":"w17-http-1","client_id":"cli-desktop","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`, h.token)
	ok("HTTP-BRIDGE-CREDENTIAL-WORKS", st == 200, st, string(body))
	var wire map[string]any
	json.Unmarshal(body, &wire)
	res, _ := wire["result"].(map[string]any)
	ok("HTTP-PRINCIPAL-COMES-FROM-CREDENTIAL", res != nil &&
		strings.HasPrefix(fmt.Sprint(res["authenticated_principal_ref"]), "principal:"), res)
	ok("HTTP-BRIDGE-NEVER-EXPOSES-RENDERER-CREDENTIAL", res != nil && res["credentials"] != nil, res["credentials"])

	other := "w17-reader-b"
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: other, Roles: []string{"READER"},
		Grants: []domain.Grant{{ProjectID: "p2"}}}); e != nil {
		ok("HTTP-FOREIGN-PRINCIPAL-PROVISIONED", false, e)
		return
	}
	tok, e := h.svc.IssueCredential(ctx, other, time.Minute)
	ok("HTTP-FOREIGN-PRINCIPAL-PROVISIONED", e == nil && tok != "", e)
	if e := seedSession(ctx, h, "s-w17"); e != nil {
		ok("HTTP-SESSION-SEEDED", false, e)
		return
	}
	ok("HTTP-SESSION-SEEDED", true)
	cancelCmd := `{"protocol_version":"researchos-client/2","command_id":"w17-cancel-foreign","client_id":"cli-b","project_id":"p1","session_id":"s-w17","expected_revision":1,"writer_epoch":1,"method":"session.control","payload":{"action":"CANCEL","target_id":"run-w17","reason":"x"}}`
	before := h.censusHash(ctx)
	st2, body2 := h.post(cancelCmd, tok)
	ok("HTTP-WRONG-PROJECT-REFUSED", st2 == 403 && strings.Contains(string(body2), "FORBIDDEN"), st2, string(body2))
	ok("HTTP-WRONG-PROJECT-NO-STATE", h.censusHash(ctx) == before, h.censusHash(ctx), before)

	h.db.ExecContext(ctx, `UPDATE auth_principals SET revoked=1 WHERE id=?`, other)
	st3, _ := h.post(cancelCmd, tok)
	ok("HTTP-REVOKED-PRINCIPAL-REFUSED", st3 == 401, st3)
	after := h.censusHash(ctx)
	ok("HTTP-REFUSALS-NEVER-REACH-HANDLER", after == before, after, before)
}
