"""Seal completed actual Root source observations after non-author delivery."""
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
p=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py'
exact(p,'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06',65191)
caller=types.ModuleType('root_old21_source_witness_verifier');caller.__file__=str(p);sys.modules[caller.__name__]=caller
exec(compile(p.read_bytes(),str(p),'exec'),caller.__dict__)
prepared=json.loads((N/'old21.v3.prepared-review-bindings.root.json').read_bytes())
sealed={}
for key,chunk,number,operation,actor in (
    ('caller','09137b',106030,'SOURCE_REVIEW_WITNESS','codex:/root/attach_fixture_source_review'),
    ('builder','c23d01',106031,'BUILDER_SOURCE_REVIEW_WITNESS','codex:/root/full_w09_source_review')):
    def match(call,result):return any(x.get('chunk_id')==chunk for x in outputs(result['payload'].get('output')))
    pair=capture(AUDIT,number,match,root=True);assert pair
    binding=json.loads(Path(pair[1]['path']).read_bytes())
    binding.update(source_audit_path=AUDIT.as_posix(),operation=operation,
        peer_delivery_binding_ref=prepared[key]['peer_binding_ref'])
    binding_ref=save('old21.v3.'+key+'.root-observation.binding.json',binding)
    refs=prepared[key]['review_refs']
    caller.validate_root_capture(binding,Path(pair[0]['path']).read_bytes(),refs,operation,actor)
    now=datetime.now(timezone.utc).isoformat()
    if key=='caller':
        witness=dict(schema='researchos.root-old21-external-review-witness.v1',issued_by='codex:/root',root_thread_id=THREAD,
            review_hdf_ref=refs[0],review_mf_ref=refs[1],review_decision_ref=refs[2],capture_binding_ref=binding_ref,
            created_utc=now,formal_acceptance=False,execution_grant=False)
    else:
        witness=dict(schema='researchos.root-old21-builder-review-witness.v1',issued_by='codex:/root',root_thread_id=THREAD,
            review_author=actor,review_refs=dict(zip(('hdf','mf','decision'),refs)),capture_binding_ref=binding_ref,
            created_utc=now,formal_acceptance=False,execution_grant=False)
    witness_ref=save('old21.v3.'+key+'.source-review-witness.actual.root.json',witness)
    sealed[key]=dict(witness_ref=witness_ref,root_binding_ref=binding_ref,original_pair_refs=pair)
source=p.parent
caller.own_review(dict(source_hdf_ref=pin(source/'HDF.json'),source_mf_ref=pin(source/'MF.json'),
    review_hdf_ref=prepared['caller']['review_refs'][0],review_mf_ref=prepared['caller']['review_refs'][1],
    review_decision_ref=prepared['caller']['review_refs'][2],review_hostpair_witness_ref=sealed['caller']['witness_ref']))
caller.builder_chain(dict(zip(('hdf','mf','decision'),prepared['builder']['review_refs'])),sealed['builder']['witness_ref'])
result=save('old21.v3.source-witnesses.sealed.actual.root.json',dict(sealed=sealed,
    full_actual_Root_witness_gates_passed=True,formal_acceptance=False,execution_grant=False,Canon_written=False))
print(json.dumps(dict(seal_ref=result,sealed=sealed),ensure_ascii=False,indent=2))
