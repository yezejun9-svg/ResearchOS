from pathlib import Path
import hashlib, json

wt = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-rpc-runtime-20261105')
out = Path(__file__).resolve().parent / 'shared-api-v1'
assert not out.exists()
paths = ['adapters/runtime/codex.go', 'adapters/runtime/codex_policy.go']
pins = {}
for rel in paths:
    raw = (wt / rel).read_bytes()
    dest = out / 'source' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    pins[rel] = hashlib.sha256(raw).hexdigest()
notes = {
  'status': 'shared Go API v1 for B2; source copies/pins frozen, B1 implementation continues',
  'source_pins': pins,
  'dto': {
    'CodexDescriptor.NativeTransport': 'constructor-sealed; exec-ephemeral-v1 or app-server-stdio-first-local-turn-v1',
    'CodexPolicyIdentity': 'Revision, WindowsSandbox, PermissionProfile, RequestedConfigSHA256, BinarySHA256, Transport, HelperContract',
    'CodexLaunch.SourceBindingHash': 'Host-supplied Hash(source_binding snapshot), must match BeforeModelTurn evidence',
    'CodexTurnEvidence': 'PolicyIdentity, RenderedConfigSHA256, SourceBindingHash, ProfileNonce, ThreadID, TaskID, RunID, Epoch, Process CodexIdentity, CaptureBytes',
    'CodexCallbacks.BeforeModelTurn': 'func(CodexTurnEvidence) error; required by RPC; runs after startup barrier before single prompt write'
  },
  'functions': {
    'CodexExpectedPolicyIdentity': 'func(CodexDescriptor) CodexPolicyIdentity; transport-specific canonical template',
    'CodexAllowsPreparation': 'func(CodexReadiness) bool; PREPARATION_READY or trusted fixture READY',
    'EvaluateCodexReadiness': 'existing signature; takes fresh snapshot and expected identity',
    'CodexRPCPolicyIdentity': 'func(binarySHA256 string) CodexPolicyIdentity',
    'NewCodexRPC': 'func(CodexRPCOptions) (CodexDriver, error); options {Executable, Descriptor, NormalHome}; production has no qualifier',
    'NewCodexRPCForTrustedGoTest': 'func(CodexRPCOptions, CodexQualificationProvider) (CodexDriver, error); Go-only fixture composition'
  },
  'qualification': 'Production NewCodexRPC has nil qualifier and must fail QUALIFICATION_REQUIRED before user prompt. B3 producer is separately leased.',
  'public_wire': 'harness.v1 rev2 unchanged; preparation may set can_submit=true and reason_codes includes PER_RUN_PERMISSION_CHECK_REQUIRED while verification stays UNVERIFIED/enforcement false'
}
(out / 'API.json').write_text(json.dumps(notes, indent=2) + '\n', encoding='utf-8')
print(json.dumps(pins))
