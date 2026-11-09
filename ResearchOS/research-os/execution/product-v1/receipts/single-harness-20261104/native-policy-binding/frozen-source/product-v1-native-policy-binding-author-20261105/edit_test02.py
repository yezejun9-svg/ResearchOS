from pathlib import Path
import hashlib, json

wt = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-policy-binding-20261105')
out = Path(__file__).resolve().parent
prior = json.loads((out / 'test01-source/manifest.json').read_text(encoding='utf-8'))['source_hashes']
changed = {}
def edit(rel, pairs):
    p = wt / rel
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == prior[rel], rel
    text = raw.decode('utf-8')
    for before, after in pairs:
        assert text.count(before) == 1, (rel, before[:90], text.count(before))
        text = text.replace(before, after, 1)
    new = text.encode('utf-8')
    p.write_bytes(new)
    changed[rel] = hashlib.sha256(new).hexdigest()

edit('adapters/runtime/codex_policy_test.go', [
    ('{"unavailable", d, CodexReadiness{State: "UNAVAILABLE", Reason: "PERMISSION_PROFILE_UNAVAILABLE", PolicyIdentity: identity}, "PERMISSION_PROFILE_UNAVAILABLE"},', '''{"unavailable", d, CodexReadiness{State: "UNAVAILABLE", Reason: "PERMISSION_PROFILE_UNAVAILABLE", PolicyIdentity: identity}, "PERMISSION_PROFILE_UNAVAILABLE"},
        {"contradictory_ready", d, CodexReadiness{State: "READY", Reason: "PERMISSION_PROFILE_UNAVAILABLE", PolicyIdentity: identity}, "PERMISSION_PROFILE_UNAVAILABLE"},
        {"descriptor_reason", CodexDescriptor{Present: true, ExecutableHash: hash, AuthState: "LOGGED_IN", ConfigurationControlled: true, UnavailableReason: "UNSUPPORTED_NATIVE_CLI_VERSION"}, ready, "UNSUPPORTED_NATIVE_CLI_VERSION"},'''),
    ('{"identity", d, CodexReadiness{State: "READY", PolicyIdentity: CodexRequestedPolicyIdentity("sha256:" + strings.Repeat("b", 64))}, "CODEX_POLICY_IDENTITY_MISMATCH"},', '''{"identity", d, CodexReadiness{State: "READY", PolicyIdentity: CodexRequestedPolicyIdentity("sha256:" + strings.Repeat("b", 64))}, "CODEX_POLICY_IDENTITY_MISMATCH"},
        {"mode_mutation", d, func() CodexReadiness { x := ready; x.PolicyIdentity.WindowsSandbox = "none"; return x }(), "CODEX_POLICY_IDENTITY_MISMATCH"},
        {"template_mutation", d, func() CodexReadiness { x := ready; x.PolicyIdentity.RequestedConfigSHA256 = "sha256:changed"; return x }(), "CODEX_POLICY_IDENTITY_MISMATCH"},
        {"revision_mutation", d, func() CodexReadiness { x := ready; x.PolicyIdentity.Revision = "old"; return x }(), "CODEX_POLICY_IDENTITY_MISMATCH"},'''),
])

edit('internal/domain/runtime_harness_windows_test.go', [
    ('"QUEUED_CANCEL", "AUTHORITY", "WORKSPACE"', '"QUEUED_CANCEL", "AUTHORITY", "WORKSPACE", "WORKSPACE_REBIND"'),
    ('mode == "QUEUED_CANCEL" || mode == "AUTHORITY" || mode == "WORKSPACE"', 'mode == "QUEUED_CANCEL" || mode == "AUTHORITY" || mode == "WORKSPACE" || mode == "WORKSPACE_REBIND"'),
    ('\t\t\t\tif err = c.Scan(context.Background()); err != nil && mode != "AUTHORITY" {', '''                if mode == "WORKSPACE_REBIND" {
                    sourceTx(t, f.db, func(tx *sql.Tx) error {
                        b.RealPath = t.TempDir()
                        b.Revision++
                        return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
                    })
                }
\t\t\t\tif err = c.Scan(context.Background()); err != nil && mode != "AUTHORITY" {'''),
    ('if mode == "AUTHORITY" || mode == "WORKSPACE" {\n\t\t\t\t\tvar runs int', 'if mode == "AUTHORITY" || mode == "WORKSPACE" || mode == "WORKSPACE_REBIND" {\n\t\t\t\t\tif mode == "WORKSPACE_REBIND" && harnessViewFixture(t, f, c, id)["status"] == "" { t.Fatal("historical Task unreadable") }\n\t\t\t\t\tvar runs int'),
])
(out / 'test02_test_hashes.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
print(json.dumps(changed))
