"""Seal one actual Root observation and its post-return artifact."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, sys, types
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)
    and x.name in {'pin','exact','save','outputs','capture'}],type_ignores=[]),'Root_capture_functions_only','exec'),globals())
chunk,number,label,request_path=sys.argv[1:]
number=int(number)
assert label.startswith('main23.v4.') and '/' not in label and '\\' not in label
request=json.loads(Path(request_path).read_bytes())
def matched(call,result):
    return any(x.get('chunk_id')==chunk for x in outputs(result['payload'].get('output')))
raw_ref,original_binding_ref=capture(AUDIT,number,matched,root=True)
binding=json.loads(Path(original_binding_ref['path']).read_bytes())
binding.update(source_audit_path=AUDIT.as_posix(),operation=request['operation'])
if request.get('peer_delivery_binding_ref') is not None:
    binding['peer_delivery_binding_ref']=request['peer_delivery_binding_ref']
binding_ref=save(label+'.capture.binding.root.json',binding)
caller_path=Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\fresh_main23_root_caller_registration_source_codex\main23root-20261010-04\main23_root.source.py')
exact(caller_path,'85ec3da49ab65741d1f1a8a94996c55f22d3b2394959e641bb3f0bd4b694f75e',56626)
module=types.ModuleType('root_main23_v4_observer_validator');module.__file__=str(caller_path)
exec(compile(caller_path.read_bytes(),module.__file__,'exec'),module.__dict__)
module.validate_root_capture(binding,module.checked(raw_ref),request['observed_refs'],request['operation'],request['peer_actor'])
created=datetime.now(timezone.utc).isoformat()
if request['operation']=='SOURCE_REVIEW_WITNESS':
    hdf,mf,decision=request['observed_refs']
    artifact=dict(schema='researchos.root-main23-external-review-witness.v1',issued_by='codex:/root',
        review_hdf_ref=hdf,review_mf_ref=mf,review_decision_ref=decision,capture_binding_ref=binding_ref,created_utc=created)
elif request['operation']=='POSTREVIEW_CURRENT_FOUR':
    artifact=dict(schema='researchos.root-main23-postreview-live.v1',issued_by='codex:/root',
        canonical_refs=request['observed_refs'],expected_revisions=request['expected_revisions'],
        root_resume_ref=request['root_resume_ref'],review_decision_ref=request['review_decision_ref'],
        capture_binding_ref=binding_ref,created_utc=created)
elif request['operation']=='ACTIVATION_FACTS_CURRENT_FOUR':
    artifact=dict(schema='researchos.root-main23-activation-envelope.v1',issued_by='codex:/root',
        facts_ref=request['observed_refs'][0],before_canonical_refs=request['observed_refs'][1:],
        capture_binding_ref=binding_ref,created_utc=created)
else:raise AssertionError('NO_ARTIFACT_KIND_FOR_OPERATION')
artifact_ref=save(label+'.artifact.actual.root.json',artifact)
print(json.dumps(dict(binding_ref=binding_ref,artifact_ref=artifact_ref,actual_capture_validated=True),ensure_ascii=False,indent=2))
