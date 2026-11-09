from pathlib import Path
import hashlib, json

root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-policy-binding-20261105'
out = Path(__file__).resolve().parent
scope = json.loads((root / 'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json').read_text(encoding='utf-8'))
changed = {}
def edit(rel, pairs):
    p = wt / rel
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == scope['baseline_sha256'][rel], rel
    text = raw.decode('utf-8')
    for before, after in pairs:
        assert text.count(before) == 1, (rel, before[:90], text.count(before))
        text = text.replace(before, after, 1)
    new = text.encode('utf-8')
    p.write_bytes(new)
    changed[rel] = {'before': scope['baseline_sha256'][rel], 'after': hashlib.sha256(new).hexdigest()}

edit('adapters/runtime/codex_driver_windows_test.go', [
    ('driver, err := NewCodexCLI(CodexCLIOptions{Executable: exe, Descriptor: CodexDescriptor{Present: true, ExecutableHash: Hash(raw), AuthState: "LOGGED_IN", ConfigurationControlled: true}})', 'driver, err := NewCodexCLIForTrustedGoTest(CodexCLIOptions{Executable: exe, Descriptor: CodexDescriptor{Present: true, ExecutableHash: Hash(raw), AuthState: "LOGGED_IN", ConfigurationControlled: true}}, CodexReadinessFunc(func() CodexReadiness { return CodexReadiness{State: "READY", PolicyIdentity: CodexRequestedPolicyIdentity(Hash(raw))} }))'),
])
edit('internal/domain/runtime_harness_windows_test.go', [
    ('driver, err := rt.NewCodexCLI(rt.CodexCLIOptions{Executable: exe, Descriptor: rt.CodexDescriptor{Present: true, ExecutableHash: Digest(raw), AuthState: "LOGGED_IN", AuthKind: "other", ConfigurationControlled: true}})', 'driver, err := rt.NewCodexCLIForTrustedGoTest(rt.CodexCLIOptions{Executable: exe, Descriptor: rt.CodexDescriptor{Present: true, ExecutableHash: Digest(raw), AuthState: "LOGGED_IN", AuthKind: "other", ConfigurationControlled: true}}, rt.CodexReadinessFunc(func() rt.CodexReadiness { return rt.CodexReadiness{State: "READY", PolicyIdentity: rt.CodexRequestedPolicyIdentity(Digest(raw))} }))'),
    ('import("os";"io";"fmt";"time";"encoding/json")', 'import("os";"io";"fmt";"time";"encoding/json";"strings")'),
    ('func main(){raw,_:=io.ReadAll(os.Stdin);', 'func main(){args:=strings.Join(os.Args[1:],"|");if strings.Count(args,"permissions.researchos-readonly.windows.sandbox=\\\"mxc\\\"")!=1||!strings.Contains(args,"--ignore-user-config")||!strings.Contains(args,"approval_policy=\\\"never\\\""){os.Exit(74)};raw,_:=io.ReadAll(os.Stdin);'),
])

policy_test = (out / 'codex_policy_test.go').read_bytes()
p = wt / 'adapters/runtime/codex_policy_test.go'
assert not p.exists()
p.write_bytes(policy_test)
changed['adapters/runtime/codex_policy_test.go'] = {'before': 'ABSENT_BEFORE', 'after': hashlib.sha256(policy_test).hexdigest()}
(out / 'test_hashes.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
print(json.dumps(changed))
