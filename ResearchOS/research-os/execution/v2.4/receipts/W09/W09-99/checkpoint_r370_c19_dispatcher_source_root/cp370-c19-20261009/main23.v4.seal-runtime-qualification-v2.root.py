"""Seal the new one-line Root observer without changing original1066."""
from pathlib import Path
from datetime import datetime, timezone
import ast, json, hashlib, os, types
N = Path(__file__).resolve().parent
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree = ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef)
     and x.name in {'pin','save','exact','outputs','capture'}], type_ignores=[]),
     'sealed_root_capture_helpers_only', 'exec'), globals())
def matched(call, result):
    return any(x.get('chunk_id') == 'ea9e65' for x in outputs(result['payload'].get('output')))
raw_ref, original_binding_ref = capture(AUDIT, 106013, matched, root=True)
binding = json.loads(Path(original_binding_ref['path']).read_bytes())
binding.update(source_audit_path=AUDIT.as_posix(), operation='RUNTIME_QUALIFICATION_ISSUANCE')
binding_ref = save('main23.v4.runtime-issuance-v2.binding.actual.root.json', binding)
payload_ref = exact(N/'main23.v4.runtime-qualification.payload.actual.root.json',
    '332398cbfa1bab18e0748d2bf06b7865e25a871414dea5e52473a2a503e756c3',36130)
payload = json.loads(Path(payload_ref['path']).read_bytes())
now = datetime.now(timezone.utc)
assert datetime.fromisoformat(binding['tool_result_timestamp'].replace('Z','+00:00')) <= now
qualification = {k:v for k,v in payload.items() if k != 'schema'}
qualification.update(schema='researchos.root-main23-qualified-runtime.v2', payload_ref=payload_ref,
    root_issuance_binding_ref=binding_ref, created_utc=now.isoformat())
qualification_ref = save('main23.v4.runtime-qualification-v2.issued.actual.root.json',qualification)
caller_ref = payload['caller_ref']
assert pin(Path(caller_ref['path']))['sha256'] == caller_ref['sha256']
module = types.ModuleType('root_main23_v4_runtime_chain_check')
module.__file__ = caller_ref['path']
exec(compile(Path(caller_ref['path']).read_bytes(),module.__file__,'exec'),module.__dict__)
chain = module.runtime_review_chain(qualification_ref, qualification, module.doc(payload['builder_contract_ref']))
check_ref = save('main23.v4.runtime-qualification-v2.chain-check.actual.root.json',dict(
    schema='researchos.root-main23-runtime-review-chain-check.v1', issued_by='codex:/root', root_thread_id=THREAD,
    qualification_ref=qualification_ref,binding_ref=binding_ref,accepted_reference_count=len(chain),
    runtime_review_chain_validated=True,actual_Go_runs=0,actual_Native_runs=0,Canon_written=False,formal_acceptance=False))
print(json.dumps(dict(qualification_ref=qualification_ref,binding_ref=binding_ref,
    chain_check_ref=check_ref,runtime_review_chain_validated=True),ensure_ascii=False,indent=2))
