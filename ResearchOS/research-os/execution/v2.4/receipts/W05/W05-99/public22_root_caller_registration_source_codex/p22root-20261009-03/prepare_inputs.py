"""Append exact review and Root pending inputs to the v3 Source snapshot."""
import hashlib
import json
import ntpath
from pathlib import Path

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
ROOT=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'

def pin(path):
    path=Path(path).resolve(strict=True)
    data=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

p=N/'source-inputs.json'
snapshot=json.loads(p.read_bytes())
refs=snapshot['references']
seen={ntpath.normcase(ntpath.normpath(x['path'])) for x in refs}
def append(path):
    value=pin(path)
    key=ntpath.normcase(ntpath.normpath(value['path']))
    if key not in seen:
        seen.add(key);refs.append(value)

review=B/'public22_root_caller_registration_independent_review_codex/review-v2-01a120dd'
expected={
    'HDF.json':('2eaa87c7ebb3f755b4bd79f7b8aaaf15137599abe480776caa9fbebca285ec5e',3395),
    'MF.json':('fdc064846af6fbbc81591e0c8af7d13405b4a8144e6e04aca07a058446a4fcd5',20848),
    'source-decision.json':('6be1e80b64f11d6ee4c4bf5131c7ccaa89181611d58324ed6db5e383f29cbbeb',13258),
}
for name,(digest,size) in expected.items():
    value=pin(review/name)
    assert (value['sha256'],value['bytes'])==(digest,size),name
    append(review/name)
append(review/'findings.json')
pending=ROOT/'pending-diagnostics.cp370.live1016.root.json'
resume=ROOT/'RESUME.cp370-public22-fixing.live1016.root.json'
assert (pin(pending)['sha256'],pin(pending)['bytes'])==(
    '904233ae7c86c4f59e69f39f9f3dcb6db8355194b57a100ea4d66e3f6b4ceada',11567)
assert (pin(resume)['sha256'],pin(resume)['bytes'])==(
    '43b61539c9ff9d4cb454ae88b3bf15d7cde978d34deeb851bf169fee6c404e84',8314)
append(pending);append(resume)
pending_doc=json.loads(pending.read_bytes())
assert [x['ordinal'] for x in pending_doc['pending']]==list(range(1005,1016))
assert pending_doc['next_original_failure_ordinal']==1016
for row in pending_doc['pending']:
    for key in ('origin_ref','capture_binding_ref'):
        if row.get(key):
            value=pin(row[key]['path'])
            assert value['sha256']==row[key]['sha256'] and value['bytes']==row[key]['bytes']
            append(row[key]['path'])
snapshot['count']=len(refs)
snapshot['pending_original_ordinals']=list(range(1005,1016))
snapshot['pending_first8_preserved']=True
snapshot['root_next_original_failure_ordinal']=1016
snapshot['actual_product_processes']=0
snapshot['actual_database_calls']=0
snapshot['actual_native_calls']=0
p.write_bytes((json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'source_input_count':len(refs),'sha256':pin(p)['sha256'],'bytes':pin(p)['bytes']},ensure_ascii=False))
