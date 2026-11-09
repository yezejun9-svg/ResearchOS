from pathlib import Path
import hashlib, json

root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-policy-binding-20261105'
out = Path(__file__).resolve().parent
prior = json.loads((out / 'test01-source/manifest.json').read_text(encoding='utf-8'))['source_hashes']
changed = {}
def edit(rel, pairs):
    p = wt / rel
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == prior[rel], (rel, 'test01 source moved')
    text = raw.decode('utf-8')
    for before, after in pairs:
        assert text.count(before) == 1, (rel, before[:90], text.count(before))
        text = text.replace(before, after, 1)
    new = text.encode('utf-8')
    p.write_bytes(new)
    changed[rel] = {'before': prior[rel], 'after': hashlib.sha256(new).hexdigest()}

edit('internal/domain/harness_v1.go', [
    ('func harnessLabel(s string, max int) bool {', '''// The input artifact is Host-sealed; this snapshot never comes from the
// renderer. It binds the selected source to the task across admission and resume.
func harnessSourceBinding(b *WorkspaceBinding) Object {
    return Object{"binding_ref": b.AuthorizedRef, "principal_id": b.PrincipalID,
        "project_id": *b.ProjectID, "access": "READ_ONLY", "binding_access": b.Access,
        "revision": strconv.FormatInt(b.Revision, 10), "canonical_path_sha256": Digest([]byte(b.RealPath))}
}
func harnessSourceBindingMatches(record Object, b *WorkspaceBinding) bool {
    if b == nil || b.ProjectID == nil { return false }
    snapshot, ok := record["source_binding"].(map[string]any)
    return ok && Hash(snapshot) == Hash(harnessSourceBinding(b))
}
func harnessLabel(s string, max int) bool {'''),
    ('\tif err != nil || binding.PrincipalID != principal || binding.ProjectID == nil || *binding.ProjectID != project || binding.Status != WorkspaceActive {\n\t\treturn nil, Fail(403, "FORBIDDEN", "native workspace revoked")\n\t}\n', '\tif err != nil || binding.PrincipalID != principal || binding.ProjectID == nil || *binding.ProjectID != project || binding.Status != WorkspaceActive {\n\t\treturn nil, Fail(403, "FORBIDDEN", "native workspace revoked")\n\t}\n\tif !harnessSourceBindingMatches(record, binding) {\n\t\treturn nil, Fail(412, "STALE_INPUT", "native source binding changed or missing")\n\t}\n'),
])

edit('internal/domain/runtime_harness_windows.go', [
    ('\tif _, err = h.workspace(ctx, tx, p, in.ProjectID, in.WorkspaceRef); err != nil {\n\t\treturn nil, err\n\t}\n\trecord := Object{"schema": "researchos.harness-submit.v1", "request": in, "principal_id": p.ID, "runtime_id": route.runtimeID, "profile_ref": route.profileRef}', '\tbinding, err := h.workspace(ctx, tx, p, in.ProjectID, in.WorkspaceRef)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\trecord := Object{"schema": "researchos.harness-submit.v1", "request": in, "principal_id": p.ID, "runtime_id": route.runtimeID, "profile_ref": route.profileRef, "source_binding": harnessSourceBinding(binding)}'),
    ('\t\t_, err = port.workspace(ctx, tx, p, item.project, Str(record["request"].(map[string]any), "workspace_ref"))\n\t\ttx.Rollback()\n\t\tif err != nil {', '\t\tbinding, err := port.workspace(ctx, tx, p, item.project, Str(record["request"].(map[string]any), "workspace_ref"))\n\t\tvalidSource := err == nil && harnessSourceBindingMatches(record, binding)\n\t\ttx.Rollback()\n\t\tif !validSource {'),
    ('\tif _, err = (&harnessV1{c: c}).workspace(ctx, tx, principal, project, Str(record["request"].(map[string]any), "workspace_ref")); err != nil {\n\t\treturn fail(err)\n\t}\n\treturn tx, run, dispatch, nil', '\tbinding, err := (&harnessV1{c: c}).workspace(ctx, tx, principal, project, Str(record["request"].(map[string]any), "workspace_ref"))\n\tif err != nil {\n\t\treturn fail(err)\n\t}\n\tif !harnessSourceBindingMatches(record, binding) {\n\t\treturn fail(Fail(412, "STALE_INPUT", "native source binding changed or missing"))\n\t}\n\treturn tx, run, dispatch, nil'),
    ('\tbinding, err := (&harnessV1{c: c}).workspace(ctx, tx, principal, project, Str(request, "workspace_ref"))\n\tif err != nil {\n\t\ttx.Rollback()\n\t\treturn err\n\t}\n\tprofile :=', '\tbinding, err := (&harnessV1{c: c}).workspace(ctx, tx, principal, project, Str(request, "workspace_ref"))\n\tif err != nil {\n\t\ttx.Rollback()\n\t\treturn err\n\t}\n\tif !harnessSourceBindingMatches(record, binding) {\n\t\ttx.Rollback()\n\t\treturn c.harnessUnknown(ctx, project, runID, epoch, "native source binding changed")\n\t}\n\tprofile :='),
    ('\t\t\tdefer tx.Rollback()\n\t\t\tif fresh["state"] != "STARTED"', '\t\t\tdefer tx.Rollback()\n\t\t\tfreshBinding, bindErr := (&harnessV1{c: c}).workspace(child, tx, principal, project, Str(request, "workspace_ref"))\n\t\t\tif bindErr != nil || !harnessSourceBindingMatches(record, freshBinding) || freshBinding.RealPath != binding.RealPath || freshBinding.Revision != binding.Revision {\n\t\t\t\treturn Fail(412, "STALE_INPUT", "native source changed before resume")\n\t\t\t}\n\t\t\tif fresh["state"] != "STARTED"'),
])

edit('adapters/runtime/codex_policy.go', [
    ('\tif snapshot.State == "UNAVAILABLE" && snapshot.Reason != "" {\n\t\treturn blocked(snapshot.Reason)\n\t}\n', '\tif snapshot.Reason != "" {\n\t\treturn blocked(snapshot.Reason)\n\t}\n'),
])

(out / 'test02_edits.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
print(json.dumps(changed))
