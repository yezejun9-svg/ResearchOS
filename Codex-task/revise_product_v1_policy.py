import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
old=ROOT/'execution/product-v1/contracts/harness.v1.interface.json'
assert hashlib.sha256(old.read_bytes()).hexdigest()=='90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66'
d=json.loads(old.read_bytes());d['contract_revision']=2;d['status']='ROOT_FROZEN_IMPLEMENTATION_INTERFACE_NOT_RUNTIME_QUALIFICATION'
scope=d['$defs']['Capabilities']['properties']['security_scope']['properties']
scope['hooks']['const']='PLATFORM_POLICY';scope['mcp']['const']='PLATFORM_POLICY'
d['identity_and_authority']=[x.replace('No arbitrary caller command, inherited hooks/MCP configuration or dangerous bypass.','No arbitrary caller command or dangerous bypass. Host-controlled working directory excludes project-local configuration; mandatory native platform policy remains authoritative.') for x in d['identity_and_authority']]
d['capabilities_rules'].append('security_scope.hooks/mcp=PLATFORM_POLICY declares native platform ownership, not proof that extensions are disabled. Fixed flags request optional hooks/plugins disabled; mandatory platform policies are never bypassed. UI must keep verification states separate.')
d['evidence_notes'].append('D03 revision2: reuse the native Harness under its existing trusted machine/account policy. Actual Windows readonly boundary/events/cancel remain separately unverified; known policy incompatibility or uncontrolled project inheritance blocks only that Run.')
new=ROOT/'execution/product-v1/contracts/harness.v1.interface.rev2.json';local=HERE/'product-v1-host-interface.rev2.json'
assert not new.exists() and not local.exists()
raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf8');local.write_bytes(raw);new.write_bytes(raw)
digest=hashlib.sha256(raw).hexdigest()
decision=ROOT/'execution/product-v1/receipts/single-harness-20261104/interface-root-decision.rev2.json'
assert not decision.exists()
record=dict(decision='D03_NATIVE_PLATFORM_POLICY',contract_revision=2,interface_ref=str(new.relative_to(ROOT)),sha256=digest,
 supersedes_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),source_acceptance_increment=0,
 rationale='Product delegates to installed Harness rather than duplicating its model/tool engine. Respect existing trusted machine/account requirements; do not falsely claim all managed extensions disabled.',
 constraints=[
 'No weakening or bypass of native sandbox, approvals, managed hooks or organization requirements.',
 'Fixed CLI argv requests optional hooks/plugins disabled, notify empty, user config ignored, requested workspace readonly profile; no dangerous bypass and no combination with legacy --sandbox.',
 'Host-owned run working directory and verified project-root marker contain no copied user .codex/AGENTS/config; source project is separately authorized readonly. Do not treat working-directory isolation as OS isolation.',
 'No manual credential/config extraction, account cloning or CODEX_HOME rewrite. Native CLI owns auth. No raw private config/server names are rendered or retained as public evidence.',
 'Source can expose policy intent, declared capabilities and independently observed verification separately. Missing enforced readonly/termination evidence cannot satisfy REAL journey acceptance.',
 'Actual Host policy producer checks current installation/version/profile/workspace/permissions. Known incompatible native policy or uncontrolled project inheritance yields blocked reason, never fallback to full access.',
 'First phase has no write,pause,resume,per-tool approval bridge; all remain false.',
 'Old revision1 and all diagnostic outcomes remain immutable; user authorizes continued V1 implementation.'])
decision.write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
doc=ROOT/'docs/product-v1/D03-native-platform-policy.md';assert not doc.exists()
doc.write_bytes(('''# D03: Native platform policy in the first Harness adapter

ResearchOS owns outer tasks, dispatch, process supervision, event persistence and result presentation. The installed Harness owns model authentication and its native inner tool policies. V1 respects trusted machine/account requirements and never bypasses them.

The earlier `DISABLED` intent could imply that every managed hook/MCP source had been eliminated. That is not established by `--ignore-user-config` or an ordinary MCP-list probe. Revision 2 therefore reports `PLATFORM_POLICY`, independently of execution, filesystem and cancellation verification.

The driver uses fixed safe arguments, a Host-owned per-Run working directory and project-root marker, with the authorized source root separately readonly. It requests optional extensions disabled and does not copy user configuration or credentials. Known policy incompatibility or uncontrolled project inheritance blocks that Run. It does not silently request full access.

This is an architecture decision, not a runtime qualification. Real readonly-boundary, event, cancellation and Windows UI evidence remain required by the V1 acceptance records. Source/unit/build success cannot mark those journeys accepted.
''').encode('utf8'))
print(json.dumps(dict(revision=2,interface=str(new),sha256=digest,decision_sha256=hashlib.sha256(decision.read_bytes()).hexdigest())))
