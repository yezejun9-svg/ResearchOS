package domain

// Proposed test-only helper. The generator's unified diff adds this as
// internal/domain/w09_evidence_export_test.go; this file is not active.
import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "runtime"
    "strings"
    "sync/atomic"
    "testing"
)

var w09ExportSequence atomic.Uint64

func w09Expected(id string) map[string]any {
    expected := map[string]map[string]any{
        "C19-01": {"reposts": 4, "retained_records": 27},
        "C19-02": {"reviewed_independent_roots": 2, "simulated": 20, "experiment_source_kind": "EXPERIMENT"},
        "C19-03": {"unknown": 1, "same_bytes": true, "unsupported_relation_rejected": true},
        "C19-04": {"primary_changed": true, "remaining_independent_roots": 1, "retained_records": 27},
        "C19-05": {"new_relation_rejected": true},
        "A06-01": {"modified_stale": true, "moved_stale": true, "deleted_stale": true, "revoked": true, "new_bundle_excludes_old": true, "old_materialization_rejected": true},
        "A06-02": {"http_path_traversal_rejected": true, "secret_marker_leaks": 0},
        "A06-03": {"indexed_hits": 2, "fallback_hits": 2, "backend": "bounded-scan", "same_named_paths_distinct": true},
        "W09-G02-UNICODE-LOCATOR": {"locator": "line:2"},
        "W09-G02-ROOT-REPLACEMENT": {"capture_denied": true, "search_leaks": 0, "content_denied": true, "invalidated": true},
        "W09-G02-STALE-INPUT-BODY": {"new_context_refused_for_stale_task": true, "old_materialize_denied": true, "get_content_denied": true, "new_task_context_clean": true},
        "W09-G02-LEGACY-ROOT": {"old_root_revoked": true, "identity_unknown": true},
    }
    return expected[id]
}

func w09ExportDir(t *testing.T) string {
    t.Helper()
    base := os.Getenv("RESEARCHOS_W09_EVIDENCE_DIR")
    if base == "" { return "" } // legacy tests keep their existing behavior
    if !filepath.IsAbs(base) { t.Fatal("W09 export directory must be absolute") }
    base = filepath.Clean(base)
    info, err := os.Lstat(base)
    if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
        t.Fatal("W09 export directory unavailable or redirected", err)
    }
    name := strings.NewReplacer("/", "_", "\\", "_", ":", "_").Replace(t.Name())
    dir := filepath.Join(base, name)
    if err := os.Mkdir(dir, 0700); err != nil && !os.IsExist(err) { t.Fatal(err) }
    info, err = os.Lstat(dir)
    if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 { t.Fatal("W09 test export directory redirected",err) }
    return dir
}

func w09ExportRaw(t *testing.T, label string, raw []byte) map[string]any {
    t.Helper()
    dir := w09ExportDir(t)
    if dir == "" { return nil }
    safe := strings.NewReplacer("/", "_", "\\", "_", ":", "_").Replace(label)
    filename := fmt.Sprintf("%08d-%s.raw", w09ExportSequence.Add(1), safe)
    path := filepath.Join(dir, filename)
    f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
    if err != nil { t.Fatal(err) }
    n, writeErr := f.Write(raw)
    closeErr := f.Close()
    if writeErr != nil || closeErr != nil || n != len(raw) {
        t.Fatal("W09 export write failed", writeErr, closeErr, n, len(raw))
    }
    sum := sha256.Sum256(raw)
    return map[string]any{"path": path, "sha256": hex.EncodeToString(sum[:]), "bytes": len(raw)}
}

func w09ExportEvent(t *testing.T, label string, value any) map[string]any {
    t.Helper()
    if os.Getenv("RESEARCHOS_W09_EVIDENCE_DIR") == "" { return nil }
    raw, err := json.Marshal(value)
    if err != nil { t.Fatal(err) }
    return w09ExportRaw(t, label, raw)
}

func w09ExportHTTP(t *testing.T, method, path, key, etag string, request []byte,
    status int, response []byte, responseETag, responseType string) {
    t.Helper()
    if os.Getenv("RESEARCHOS_W09_EVIDENCE_DIR") == "" { return }
    requestPin := w09ExportRaw(t, "http-request", request)
    responsePin := w09ExportRaw(t, "http-response", response)
    w09ExportEvent(t, "http-exchange", map[string]any{
        "method": method, "path": path, "idempotency_key": key, "if_match": etag,
        "request": requestPin, "status": status, "response": responsePin,
        "response_etag": responseETag, "response_content_type": responseType,
        "delivery": "IN_PROCESS_HTTptest_RECORDER", "authorization_header_exported": false,
    })
}

func w09ExportFile(t *testing.T, label, path, rootID string) map[string]any {
    t.Helper()
    if os.Getenv("RESEARCHOS_W09_EVIDENCE_DIR") == "" { return nil }
    info, err := os.Lstat(path)
    if os.IsNotExist(err) {
        return w09ExportEvent(t, "file-"+label, map[string]any{
            "path": filepath.Clean(path), "root_id": rootID, "exists": false,
            "observation": "OS_LSTAT_NOT_EXIST", "goos": runtime.GOOS, "goarch": runtime.GOARCH,
        })
    }
    if err != nil { t.Fatal(err) }
    if !info.Mode().IsRegular() {
        return w09ExportEvent(t, "file-"+label, map[string]any{
            "path": filepath.Clean(path), "root_id": rootID, "exists": true,
            "type": info.Mode().Type().String(), "mode": info.Mode().String(),
            "size": info.Size(), "mod_time": info.ModTime().UTC().Format("2006-01-02T15:04:05.999999999Z07:00"),
        })
    }
    raw, err := os.ReadFile(path)
    if err != nil { t.Fatal(err) }
    if int64(len(raw)) != info.Size() { t.Fatal("W09 source changed during input capture") }
    bytesPin := w09ExportRaw(t, "file-body-"+label, raw)
    return w09ExportEvent(t, "file-"+label, map[string]any{
        "path": filepath.Clean(path), "root_id": rootID, "exists": true,
        "type": "regular", "mode": info.Mode().String(), "size": info.Size(),
        "mod_time": info.ModTime().UTC().Format("2006-01-02T15:04:05.999999999Z07:00"),
        "body": bytesPin, "goos": runtime.GOOS, "goarch": runtime.GOARCH,
    })
}

// Record the exact project/root/cache state available to the current fixture.
// The status row is a projection of actual SQLite rows, never a claimed cache hit.
func w09ExportState(t *testing.T, f *fixture, label, rootID string) map[string]any {
    t.Helper()
    if os.Getenv("RESEARCHOS_W09_EVIDENCE_DIR") == "" { return nil }
    var path, identity string
    var revision, revoked int
    if rootID != "" {
        if err := f.db.QueryRow("SELECT path,root_identity,revision,revoked FROM retrieval_roots WHERE project=? AND id=?", f.project, rootID).Scan(&path, &identity, &revision, &revoked); err != nil { t.Fatal(err) }
    }
    var current, stale, rejected, indexRows, maxIndexRev, origins, dedupe, grants, principalRevoked int
    var roles string
    for _, item := range []struct { q string; dst *int; args []any }{
        {"SELECT count(*) FROM retrieval_snapshots WHERE project=? AND status='CURRENT'", &current, []any{f.project}},
        {"SELECT count(*) FROM retrieval_snapshots WHERE project=? AND status='STALE'", &stale, []any{f.project}},
        {"SELECT count(*) FROM retrieval_snapshots WHERE project=? AND status='REVOKED'", &rejected, []any{f.project}},
        {"SELECT count(*) FROM retrieval_index WHERE project=?", &indexRows, []any{f.project}},
        {"SELECT coalesce(max(index_revision),0) FROM retrieval_index WHERE project=?", &maxIndexRev, []any{f.project}},
        {"SELECT count(*) FROM evidence_origins WHERE project=?", &origins, []any{f.project}},
        {"SELECT count(*) FROM retrieval_dedupe WHERE project=? AND principal=?", &dedupe, []any{f.project,f.owner}},
        {"SELECT count(*) FROM auth_grants WHERE project=? AND principal=?", &grants, []any{f.project,f.owner}},
        {"SELECT revoked FROM auth_principals WHERE id=?", &principalRevoked, []any{f.owner}},
    } {
        if err := f.db.QueryRow(item.q,item.args...).Scan(item.dst); err != nil { t.Fatal(err) }
    }
    if err := f.db.QueryRow("SELECT roles FROM auth_principals WHERE id=?",f.owner).Scan(&roles); err != nil { t.Fatal(err) }
    grantRows, err := f.db.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=? AND project=? ORDER BY task,run",f.owner,f.project)
    if err != nil { t.Fatal(err) }
    actualGrants := []map[string]any{}
    for grantRows.Next() {
        var project, task, run string
        var restricted int
        if err := grantRows.Scan(&project,&task,&run,&restricted); err != nil { grantRows.Close();t.Fatal(err) }
        actualGrants=append(actualGrants,map[string]any{"project":project,"task":task,"run":run,"restricted":restricted})
    }
    if err := grantRows.Err(); err != nil { grantRows.Close();t.Fatal(err) }
    grantRows.Close()
    index, err := f.db.Query("SELECT artifact_id,index_revision,content_hash FROM retrieval_index WHERE project=? ORDER BY artifact_id",f.project)
    if err != nil { t.Fatal(err) }
    actualIndex := []map[string]any{}
    for index.Next() {
        var artifact, hash string
        var revision int
        if err := index.Scan(&artifact,&revision,&hash); err != nil { index.Close();t.Fatal(err) }
        actualIndex=append(actualIndex,map[string]any{"artifact_id":artifact,"index_revision":revision,"content_hash":hash})
    }
    if err := index.Err(); err != nil { index.Close();t.Fatal(err) }
    index.Close()
    return w09ExportEvent(t, "state-"+label, map[string]any{
        "project": f.project, "principal": f.owner, "root_id": rootID,
        "root_path": path, "root_identity": identity, "root_revision": revision,
        "root_revoked": revoked, "principal_revoked": principalRevoked,
        "grant_count": grants, "current_snapshots": current, "stale_snapshots": stale,
        "roles_json": roles, "actual_grants": actualGrants, "actual_index": actualIndex,
        "revoked_snapshots": rejected, "index_rows": indexRows,
        "max_index_revision": maxIndexRev, "origin_rows": origins,
        "dedupe_rows": dedupe, "project_state": f.state(),
        "cache_identity_claim": nil,
    })
}

func w09ExportOriginRows(t *testing.T, f *fixture, label string) map[string]any {
    t.Helper()
    if os.Getenv("RESEARCHOS_W09_EVIDENCE_DIR") == "" { return nil }
    rows, err := f.db.Query("SELECT evidence_id,origin_id,relation,basis_artifact_id,basis_root_id,basis_relative_path,recorded_by,recorded_at FROM evidence_origins WHERE project=? ORDER BY evidence_id", f.project)
    if err != nil { t.Fatal(err) }
    defer rows.Close()
    result := []map[string]any{}
    for rows.Next() {
        var evidence, origin, relation, artifact, root, relative, actor, at string
        if err := rows.Scan(&evidence,&origin,&relation,&artifact,&root,&relative,&actor,&at); err != nil { t.Fatal(err) }
        result = append(result,map[string]any{"evidence_id":evidence,"origin_id":origin,
            "relation":relation,"basis_artifact_id":artifact,"basis_root_id":root,
            "basis_relative_path":relative,"recorded_by":actor,"recorded_at":at})
    }
    if err := rows.Err(); err != nil { t.Fatal(err) }
    return w09ExportEvent(t,"origins-"+label,result)
}
