from pathlib import Path
import hashlib, json

root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-rpc-runtime-20261105'
out = Path(__file__).resolve().parent
scope = json.loads((root / 'execution/product-v1/receipts/single-harness-20261104/native-rpc-runtime/scope.json').read_text(encoding='utf-8'))
changed = {}
def edit(rel, pairs):
    p = wt / rel
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == scope['baseline_sha256'][rel], rel
    text = raw.decode('utf-8')
    for before, after in pairs:
        assert text.count(before) == 1, (rel, before[:80], text.count(before))
        text = text.replace(before, after, 1)
    new = text.encode('utf-8')
    p.write_bytes(new)
    changed[rel] = hashlib.sha256(new).hexdigest()

edit('adapters/runtime/codex.go', [
    ('\tUnavailableReason                                           string\n}', '\tUnavailableReason                                           string\n\tNativeTransport                                            string\n}'),
    ('TaskID, RunID, Epoch, Workspace, Prompt, Directory string', 'TaskID, RunID, Epoch, Workspace, Prompt, Directory, SourceBindingHash string'),
    ('type CodexEvent struct{ Kind, Text, ToolID, ToolName, ToolPhase, NativeID string }', '''// CodexTurnEvidence is a value-only projection of the live RPC barrier.
// A serialized copy cannot recreate the driver's private one-use permit.
type CodexTurnEvidence struct {
    PolicyIdentity CodexPolicyIdentity
    RenderedConfigSHA256, SourceBindingHash, ProfileNonce, ThreadID string
    TaskID, RunID, Epoch string
    Process CodexIdentity
    CaptureBytes int64
}
type CodexEvent struct{ Kind, Text, ToolID, ToolName, ToolPhase, NativeID string }'''),
    ('\tBeforeResume func(CodexIdentity) error\n', '\tBeforeResume func(CodexIdentity) error\n\tBeforeModelTurn func(CodexTurnEvidence) error\n'),
])

edit('adapters/runtime/codex_policy.go', [
    ('\tCodexPermissionProfile    = "researchos-readonly"\n', '''\tCodexPermissionProfile    = "researchos-readonly"
    CodexExecTransport = "exec-ephemeral-v1"
    CodexRPCTransport = "app-server-stdio-first-local-turn-v1"
    CodexRPCPolicyRevision = "researchos-codex-mxc-rpc-readonly-v1"
    CodexRPCSandboxID = "codex-mxc-rpc-permissions-workspace-read-v3"
    CodexRPCCommandID = "codex-mxc-rpc-readonly-v3"
    CodexRPCHelperContract = "native-0166-windows-fresh-arg0-read-v1"
'''),
    ('Revision, WindowsSandbox, PermissionProfile, RequestedConfigSHA256, BinarySHA256 string', 'Revision, WindowsSandbox, PermissionProfile, RequestedConfigSHA256, BinarySHA256, Transport, HelperContract string'),
    ('"sha256:" + hex.EncodeToString(sum[:]), binarySHA256}', '"sha256:" + hex.EncodeToString(sum[:]), binarySHA256, CodexExecTransport, ""}'),
    ('// Every caller uses this predicate.', '''func codexTransport(d CodexDescriptor) string {
    if d.NativeTransport == "" { return CodexExecTransport }
    return d.NativeTransport
}

// CodexExpectedPolicyIdentity selects only the constructor-sealed transport.
func CodexExpectedPolicyIdentity(d CodexDescriptor) CodexPolicyIdentity {
    if d.NativeTransport == CodexRPCTransport { return CodexRPCPolicyIdentity(d.ExecutableHash) }
    return CodexRequestedPolicyIdentity(d.ExecutableHash)
}

func CodexAllowsPreparation(r CodexReadiness) bool {
    return r.State == "PREPARATION_READY" || r.State == "READY"
}

// Every caller uses this predicate.'''),
    ('\tif expected.BinarySHA256 == "" || expected.BinarySHA256 != d.ExecutableHash ||', '\tif expected.BinarySHA256 == "" || expected.BinarySHA256 != d.ExecutableHash ||'),
    ('expected.Revision != CodexNativePolicyRevision || expected.WindowsSandbox != CodexWindowsSandbox ||', '((codexTransport(d) == CodexRPCTransport && expected.Revision != CodexRPCPolicyRevision) || (codexTransport(d) != CodexRPCTransport && expected.Revision != CodexNativePolicyRevision)) || expected.Transport != codexTransport(d) || expected.WindowsSandbox != CodexWindowsSandbox ||'),
    ('\tif snapshot.State != "READY" {\n\t\treturn blocked("PERMISSION_PROFILE_UNVERIFIED")\n\t}\n\treturn CodexReadiness{State: "READY", PolicyIdentity: expected}', '''\tif d.NativeTransport == CodexRPCTransport && snapshot.State == "PREPARATION_READY" {
        return CodexReadiness{State: "PREPARATION_READY", PolicyIdentity: expected}
    }
    if snapshot.State != "READY" {
        return blocked("PERMISSION_PROFILE_UNVERIFIED")
    }
    return CodexReadiness{State: "READY", PolicyIdentity: expected}'''),
])
(out / 'shared_api_hashes.json').write_text(json.dumps(changed, indent=2)+'\n',encoding='utf-8')
print(json.dumps(changed))
