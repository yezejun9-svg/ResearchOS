from pathlib import Path
import hashlib

wt = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-policy-binding-20261105')
p = wt / 'adapters/runtime/codex_policy_test.go'
raw = p.read_bytes()
anchor = b'\tfor _, value := range []string{\n'
addition = b'''\tkeys := map[string]int{}
\tfor config, count := range configs {
\t\tkey := strings.SplitN(config, "=", 2)[0]
\t\tkeys[key] += count
\t\tif strings.Contains(key, ".windows.sandbox") || key == "sandbox_mode" || key == "sandbox" {
\t\t\tt.Fatalf("conflicting or profile-scoped sandbox selection %q", config)
\t\t}
\t}
\tif keys["windows.sandbox"] != 1 || configs[`windows.sandbox="mxc"`] != 1 || keys["default_permissions"] != 1 {
\t\tt.Fatalf("global MXC and selected profile must be unique: %v", configs)
\t}
\tfor _, arg := range args {
\t\tif arg == "--sandbox" || arg == "--dangerously-bypass-approvals-and-sandbox" {
\t\t\tt.Fatal("conflicting sandbox command flag", args)
\t\t}
\t}
'''
assert raw.count(anchor) == 1
p.write_bytes(raw.replace(anchor, addition + anchor, 1))
print('policy test', hashlib.sha256(p.read_bytes()).hexdigest())

p = wt / 'adapters/runtime/codex_driver_windows_test.go'
raw = p.read_bytes()
anchor = b'func TestCodexHarnessExecutionSourceContext(t *testing.T) {\n'
addition = b'''func TestCodexReadinessMutationBeforeResume(t *testing.T) {
\texe, err := os.Executable()
\tif err != nil { t.Fatal(err) }
\traw, err := os.ReadFile(exe)
\tif err != nil { t.Fatal(err) }
\thash := Hash(raw)
\tchecks := 0
\tprovider := CodexReadinessFunc(func() CodexReadiness {
\t\tchecks++
\t\tidentity := CodexRequestedPolicyIdentity(hash)
\t\tif checks > 1 { identity.WindowsSandbox = "none" }
\t\treturn CodexReadiness{State: "READY", PolicyIdentity: identity}
\t})
\tdriver, err := NewCodexCLIForTrustedGoTest(CodexCLIOptions{Executable: exe, Descriptor: CodexDescriptor{
\t\tPresent: true, ExecutableHash: hash, AuthState: "LOGGED_IN", ConfigurationControlled: true,
\t}}, provider)
\tif err != nil { t.Fatal(err) }
\td := driver.(*codexCLI)
\td.fixtureArgs = []string{"-test.run=^TestCodexHarnessOwnedChild$"}
\td.fixtureEnv = []string{"RESEARCHOS_CODEX_FAKE_CHILD=1"}
\tcallback := false
\t_, err = d.Start(context.Background(), CodexLaunch{TaskID: "t", RunID: "r-mutate", Epoch: "1",
\t\tWorkspace: t.TempDir(), Prompt: "COMPLETE", Directory: filepath.Join(t.TempDir(), "dispatch"), Timeout: 5*time.Second},
\t\tCodexCallbacks{BeforeResume: func(CodexIdentity) error { callback = true; return nil }, Event: func(CodexEvent) error { callback = true; return nil }})
\tif err == nil || !strings.Contains(err.Error(), "CODEX_POLICY_IDENTITY_MISMATCH") || callback || checks < 2 {
\t\tt.Fatalf("mutated provider passed suspended-child fence: err=%v callback=%v checks=%d", err, callback, checks)
\t}
}

'''
assert raw.count(anchor) == 1
p.write_bytes(raw.replace(anchor, addition + anchor, 1))
print('driver test', hashlib.sha256(p.read_bytes()).hexdigest())
