import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
source=HERE/'product-v1-host-interface.json'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
assert digest=='90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66'
dto=json.loads(source.read_bytes());assert len(dto['routes'])==6 and len(dto['$defs'])==22
target=ROOT/'execution/product-v1/contracts/harness.v1.interface.json'
decision=ROOT/'execution/product-v1/receipts/single-harness-20261104/interface-root-decision.json'
assert not target.exists() and not decision.exists(), 'Reconcile prior interface freeze; never overwrite'
target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
value=dict(status='ROOT_FROZEN_IMPLEMENTATION_INTERFACE_REV1_NOT_RUNTIME_QUALIFICATION',interface_ref=str(target.relative_to(ROOT)),sha256=digest,
 routes=6,definitions=22,root_review_chunks=['4be7d1','1a9fde'],backend_clarification='a0098d',
 rules=[
  'workspace_ref is existing WorkspaceBinding.AuthorizedRef / authorized_workspace_ref, never path or VersionRef. Server validates actual principal/project/ACTIVE binding and ConfirmPath.',
  'Use existing workspace.register/project.bootstrap for real owner first use; they do not require provider model configuration. Codex UI must not retain Mu model/session guards.',
  'security_scope hooks/MCP DISABLED describes Host requested configuration intent, never observed enforcement. Unknown inherited configuration means can_submit=false with reason; no synthetic LIVE_OBSERVED.',
  'Prompt must contain non-whitespace UTF8 and at most65536 bytes; reject empty task before state creation.',
  'Same Coordinator and canonical Task/Run/outbox/idempotency only; initial QUEUED/run=null, exact CAS cancellation, no automatic ambiguous retry.',
  'Numeric identity fields remain canonical decimal strings. Preserve HTTP query cursor in narrow Main transport; no renderer bearer/exec access.',
  'Independent code review and separately scoped real CLI/Electron evidence required before any journey acceptance.'
 ],product_acceptance_increment=0)
decision.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(interface=str(target),sha256=digest,decision_sha256=hashlib.sha256(decision.read_bytes()).hexdigest())))
