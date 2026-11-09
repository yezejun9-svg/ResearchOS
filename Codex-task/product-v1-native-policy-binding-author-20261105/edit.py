from pathlib import Path
import hashlib
import json

root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-policy-binding-20261105'
out = Path(__file__).resolve().parent
scope = json.loads((root / 'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json').read_text(encoding='utf-8'))
changed = {}

def edit(rel, replacements):
    p = wt / rel
    raw = p.read_bytes()
    expected = scope['baseline_sha256'][rel]
    assert hashlib.sha256(raw).hexdigest() == expected, (rel, 'baseline changed')
    text = raw.decode('utf-8')
    for before, after in replacements:
        assert text.count(before) == 1, (rel, 'anchor count', text.count(before), before[:100])
        text = text.replace(before, after, 1)
    new = text.encode('utf-8')
    p.write_bytes(new)
    changed[rel] = {'before': expected, 'after': hashlib.sha256(new).hexdigest(), 'bytes': len(new)}

policy = (out / 'codex_policy.go').read_bytes()
policy_path = wt / 'adapters/runtime/codex_policy.go'
assert not policy_path.exists()
policy_path.write_bytes(policy)
changed['adapters/runtime/codex_policy.go'] = {'before': 'ABSENT_BEFORE', 'after': hashlib.sha256(policy).hexdigest(), 'bytes': len(policy)}

edit('adapters/runtime/codex.go', [
    ('type CodexDriver interface {\n\tDescriptor() CodexDescriptor\n', 'type CodexDriver interface {\n\tDescriptor() CodexDescriptor\n\tReadinessSnapshot() CodexReadiness\n')
])

edit('adapters/runtime/codex_driver_windows.go', [
    ('\tfixtureEnv  []string\n', '\tfixtureEnv  []string\n\treadiness CodexReadinessProvider\n'),
    ('\toptions.PermissionOverrides = append([]string(nil), options.PermissionOverrides...)\n', '\tif len(options.PermissionOverrides) != 0 {\n\t\treturn nil, errors.New("CODEX_POLICY_OVERRIDE_FORBIDDEN")\n\t}\n'),
    ('func (d *codexCLI) Descriptor() CodexDescriptor { return d.options.Descriptor }\n', '''func (d *codexCLI) Descriptor() CodexDescriptor { return d.options.Descriptor }
// Only trusted Go composition can inject a fixture provider. NewCodexCLI and
// the actual Host composition always remain UNVERIFIED in Slice A.
func NewCodexCLIForTrustedGoTest(options CodexCLIOptions, provider CodexReadinessProvider) (CodexDriver, error) {
    if provider == nil { return nil, errors.New("CODEX_TEST_PROVIDER_REQUIRED") }
    driver, err := NewCodexCLI(options)
    if err != nil { return nil, err }
    driver.(*codexCLI).readiness = provider
    return driver, nil
}
func (d *codexCLI) ReadinessSnapshot() CodexReadiness {
    if d.readiness != nil { return d.readiness.Snapshot() }
    return CodexReadiness{State: "UNVERIFIED", Reason: "PERMISSION_PROFILE_UNVERIFIED", PolicyIdentity: CodexRequestedPolicyIdentity(d.options.Descriptor.ExecutableHash)}
}
func (d *codexCLI) evaluatedReadiness() CodexReadiness {
    return EvaluateCodexReadiness(d.Descriptor(), d.ReadinessSnapshot(), CodexRequestedPolicyIdentity(d.options.Descriptor.ExecutableHash))
}
'''),
    ('func (d *codexCLI) arguments(cwd, source string) []string {\n', 'func (d *codexCLI) arguments(cwd, source string) []string {\n'),
    ('\t// Fixed requested profile; managed platform policy is authoritative. TOML\n\t// strings use JSON-compatible escaping; no shell interpolation is involved.\n\tq := strconv.Quote\n\treturn []string{"exec", "--json", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check", "-C", cwd,\n\t\t"-c", `default_permissions="researchos-readonly"`,\n\t\t"-c", `permissions.researchos-readonly.filesystem={":root"="deny",":minimal"="read",":workspace_roots"={"."="read"}}`,\n\t\t"-c", "permissions.researchos-readonly.workspace_roots={" + q(source) + "=true}",\n\t\t"-c", "permissions.researchos-readonly.network.enabled=false",\n\t\t"-c", `project_root_markers=[".researchos-codex-root"]`, "-c", `approval_policy="never"`,\n\t\t"-c", "features.hooks=false", "-c", "features.plugins=false", "-c", "features.remote_plugin=false",\n\t\t"-c", "features.skill_mcp_dependency_install=false", "-c", "features.apps=false",\n\t\t"-c", "notify=[]", "-c", `web_search="disabled"`, "-"}\n', '\treturn codexRequestedArguments(cwd, source)\n'),
    ('func (d *codexCLI) Start(ctx context.Context, in CodexLaunch, cb CodexCallbacks) (CodexHandle, error) {\n', 'func (d *codexCLI) Start(ctx context.Context, in CodexLaunch, cb CodexCallbacks) (CodexHandle, error) {\n\tif gate := d.evaluatedReadiness(); gate.State != "READY" { return nil, errors.New(gate.Reason) }\n'),
    ('\t\tfunc(p *process) error {\n\t\t\treturn cb.BeforeResume', '\t\tfunc(p *process) error {\n\t\t\tif gate := d.evaluatedReadiness(); gate.State != "READY" { return errors.New(gate.Reason) }\n\t\t\treturn cb.BeforeResume'),
])

edit('internal/domain/runtime_dispatch.go', [
    ('profile["sandbox"] != "codex-permissions-workspace-read-v1" || Str(profile, "build_hash") == "" || Str(profile, "harness_owner") == ""', 'profile["sandbox"] != "codex-mxc-permissions-workspace-read-v2" || profile["command_id"] != "codex-mxc-readonly-v2" || profile["native_policy_revision"] != "researchos-codex-mxc-readonly-v1" || profile["windows_sandbox"] != "mxc" || profile["permission_profile"] != "researchos-readonly" || Str(profile, "requested_config_sha256") == "" || Str(profile, "build_hash") == "" || Str(profile, "harness_owner") == ""'),
])

edit('internal/domain/harness_v1.go', [
    ('profile["sandbox"] != "codex-permissions-workspace-read-v1" || profile["credential_revision"] != "CLI_OWNED"', 'profile["sandbox"] != "codex-mxc-permissions-workspace-read-v2" || profile["command_id"] != "codex-mxc-readonly-v2" || profile["native_policy_revision"] != "researchos-codex-mxc-readonly-v1" || profile["windows_sandbox"] != "mxc" || profile["permission_profile"] != "researchos-readonly" || Str(profile, "requested_config_sha256") == "" || profile["credential_revision"] != "CLI_OWNED"'),
])

edit('internal/domain/runtime_harness_windows.go', [
    ('func harnessNull(s string) any {', '''func harnessReadiness(driver rt.CodexDriver) (rt.CodexDescriptor, rt.CodexReadiness) {
    descriptor := rt.CodexDescriptor{}
    snapshot := rt.CodexReadiness{}
    if driver != nil { descriptor, snapshot = driver.Descriptor(), driver.ReadinessSnapshot() }
    return descriptor, rt.EvaluateCodexReadiness(descriptor, snapshot, rt.CodexRequestedPolicyIdentity(descriptor.ExecutableHash))
}
func harnessPolicyMatches(profile map[string]any, identity rt.CodexPolicyIdentity) bool {
    return profile["sandbox"] == rt.CodexNativeSandboxID && profile["command_id"] == rt.CodexNativeCommandID &&
        profile["native_policy_revision"] == identity.Revision && profile["windows_sandbox"] == identity.WindowsSandbox &&
        profile["permission_profile"] == identity.PermissionProfile && profile["requested_config_sha256"] == identity.RequestedConfigSHA256 &&
        profile["build_hash"] == identity.BinarySHA256
}
func harnessNull(s string) any {'''),
    ('\tdescriptor := rt.CodexDescriptor{}\n\tif h.c.config.HarnessDriver != nil {\n\t\tdescriptor = h.c.config.HarnessDriver.Descriptor()\n\t}\n\tready := descriptor.Present && descriptor.ConfigurationControlled && descriptor.AuthState == "LOGGED_IN"\n\treasons := Empty()\n\tif !descriptor.Present {\n\t\treasons = append(reasons, "NOT_INSTALLED")\n\t}\n\tif !descriptor.ConfigurationControlled {\n\t\treasons = append(reasons, "CONFIG_INHERITANCE_UNVERIFIED")\n\t}\n\tif descriptor.AuthState != "LOGGED_IN" {\n\t\treasons = append(reasons, "AUTH_METADATA_REQUIRED")\n\t}\n\tif descriptor.UnavailableReason != "" {\n\t\treasons = append(reasons, descriptor.UnavailableReason)\n\t}\n', '\tdescriptor, readiness := harnessReadiness(h.c.config.HarnessDriver)\n\tready := readiness.State == "READY"\n\treasons := Empty()\n\tif !ready { reasons = append(reasons, readiness.Reason) }\n'),
    ('"workspace_read_scope": "UNVERIFIED", "cancellation": "UNVERIFIED"', '"workspace_read_scope": readiness.State, "cancellation": "UNVERIFIED"'),
    ('"enforcement_verified": false}', '"enforcement_verified": ready}'),
    ('\tdescriptor := h.c.config.HarnessDriver.Descriptor()\n\ttx, err :=', '\tdescriptor := h.c.config.HarnessDriver.Descriptor()\n\tidentity := rt.CodexRequestedPolicyIdentity(descriptor.ExecutableHash)\n\ttx, err :='),
    ('name := "Codex readonly Host V1 " + p.ID', 'name := "Codex readonly Host MXC V2 " + p.ID'),
    ('if profile["build_hash"] != descriptor.ExecutableHash || profile["backend"] != harnessBackend {', 'if profile["backend"] != harnessBackend || !harnessPolicyMatches(profile, identity) {'),
    ('"sandbox": "codex-permissions-workspace-read-v1", "credential_revision": "CLI_OWNED"', '"sandbox": rt.CodexNativeSandboxID, "native_policy_revision": identity.Revision, "requested_config_sha256": identity.RequestedConfigSHA256, "windows_sandbox": identity.WindowsSandbox, "permission_profile": identity.PermissionProfile, "credential_revision": "CLI_OWNED"'),
    ('"command_id": "codex-readonly-v1"', '"command_id": rt.CodexNativeCommandID'),
    ('\td := c.config.HarnessDriver.Descriptor()\n\tif !d.Present || !d.ConfigurationControlled || d.AuthState != "LOGGED_IN" {', '\t_, readiness := harnessReadiness(c.config.HarnessDriver)\n\tif readiness.State != "READY" {'),
    ('\tif admission["admission_kind"] != "HOST_HARNESS_V1" {\n', '\tif admission["admission_kind"] != "HOST_HARNESS_V1" {\n'),
    ('\t\treturn fail(Fail(403, "FORBIDDEN", "native admission required"))\n\t}\n\trecord, err := harnessTaskInput', '''\t\treturn fail(Fail(403, "FORBIDDEN", "native admission required"))
    }
    descriptor, readiness := harnessReadiness(c.config.HarnessDriver)
    profile := admission["profile"].(map[string]any)
    if readiness.State != "READY" || !harnessPolicyMatches(profile, rt.CodexRequestedPolicyIdentity(descriptor.ExecutableHash)) {
        return fail(Fail(503, "HARNESS_UNAVAILABLE", "native policy readiness changed"))
    }
\trecord, err := harnessTaskInput'''),
    ('\tprofile := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)["profile"].(map[string]any)\n\tdescriptor := c.config.HarnessDriver.Descriptor()\n\tif !descriptor.ConfigurationControlled || descriptor.ExecutableHash != profile["build_hash"] {', '\tprofile := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)["profile"].(map[string]any)\n\tdescriptor, readiness := harnessReadiness(c.config.HarnessDriver)\n\tif readiness.State != "READY" || !harnessPolicyMatches(profile, rt.CodexRequestedPolicyIdentity(descriptor.ExecutableHash)) {'),
])

edit('internal/host/harness_windows.go', [
    ('return rt.NewCodexCLI(rt.CodexCLIOptions{Executable: executable, Descriptor: descriptor})', 'return rt.NewCodexCLI(rt.CodexCLIOptions{Executable: executable, Descriptor: descriptor})'),
])

(out / 'source_hashes.json').write_text(json.dumps(changed, indent=2) + '\n', encoding='utf-8')
print(json.dumps(changed))
