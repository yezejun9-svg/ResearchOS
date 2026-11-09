"""Issue Root qualification only after the actual completed runtime observer."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,types,sys
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
def match(call,result):return any(x.get('chunk_id')=='763940' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,106032,match,root=True);assert pair
binding=json.loads(Path(pair[1]['path']).read_bytes())
binding.update(source_audit_path=AUDIT.as_posix(),operation='RUNTIME_QUALIFICATION_ISSUANCE')
binding_ref=save('old21.v3.runtime-issuance.binding.actual.root.json',binding)
prepared=json.loads((N/'old21.v3.prepared-runtime-binding.root.json').read_bytes())['runtime']
payload=json.loads(Path(prepared['payload_ref']['path']).read_bytes())
wrapper=dict(payload,schema='researchos.root-old21-qualified-runtime.v2',payload_ref=prepared['payload_ref'],
    root_issuance_binding_ref=binding_ref,created_utc=datetime.now(timezone.utc).isoformat())
qualification_ref=save('old21.v3.runtime-qualification.issued.actual.root.json',wrapper)
p=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py'
exact(p,'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06',65191)
caller=types.ModuleType('root_old21_runtime_chain_verifier');caller.__file__=str(p);sys.modules[caller.__name__]=caller
exec(compile(p.read_bytes(),str(p),'exec'),caller.__dict__)
contract=json.loads(Path(wrapper['builder_contract_ref']['path']).read_bytes())
refs=caller.runtime_review_chain(qualification_ref,wrapper,contract)
print(json.dumps(dict(qualification_ref=qualification_ref,root_issuance_binding_ref=binding_ref,
    complete_original_pair_refs=pair,runtime_review_chain_verified=True,chain_ref_count=len(refs),
    formal_programme_qualification=False,formal_acceptance=False,Canon_written=False),ensure_ascii=False,indent=2))
