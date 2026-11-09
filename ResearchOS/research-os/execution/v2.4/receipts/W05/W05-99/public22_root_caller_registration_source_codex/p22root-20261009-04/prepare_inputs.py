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

review=B/'public22_root_caller_registration_independent_review_codex/review-v3-01a1210b'
expected={
    'HDF.json':('11d1e317758d0c1213b871aba43a0358fb7370fc510eb91443510fc135abb573',3398),
    'MF.json':('1dc20b70eda56e86795bcc615d86b89c9e5c68681df005f19973883c0c8ba9b1',218989),
    'source-decision.json':('e9968c0f8bfd0c9ec056fcac767a7a4eed7be8b39c0d01d37a3564edc737a91a',3615),
}
for name,(digest,size) in expected.items():
    value=pin(review/name)
    assert (value['sha256'],value['bytes'])==(digest,size),name
    append(review/name)
assert (pin(review/'findings.json')['sha256'],pin(review/'findings.json')['bytes'])==(
    '3bc893e1b2b865e485a210031db7f804212948389281955edd01885f105d682e',1522)
append(review/'findings.json')
append(B/'public22_root_caller_registration_source_codex/p22root-20261009-03/HDF.json')
pending=ROOT/'pending-diagnostics.cp370.live1018.root.json'
resume=ROOT/'RESUME.cp370-public22-v4-pending.live1018.root.json'
assert (pin(pending)['sha256'],pin(pending)['bytes'])==(
    'ab22f3b0ee01b4002dfbbc97e219f08e99e371315839248fd4fac4e3e503d3b0',13226)
assert (pin(resume)['sha256'],pin(resume)['bytes'])==(
    '8e08f0fc150de49033ac875e6776951b8ef39169752c97385bf749921a0a3c58',8415)
append(pending);append(resume)
pending_doc=json.loads(pending.read_bytes())
assert [x['ordinal'] for x in pending_doc['pending']]==list(range(1005,1018))
assert pending_doc['next_original_failure_ordinal']==1018
for row in pending_doc['pending']:
    for key in ('origin_ref','capture_binding_ref'):
        if row.get(key):
            value=pin(row[key]['path'])
            assert value['sha256']==row[key]['sha256'] and value['bytes']==row[key]['bytes']
            append(row[key]['path'])
snapshot['count']=len(refs)
snapshot['pending_original_ordinals']=list(range(1005,1018))
snapshot['pending_first8_preserved']=True
snapshot['root_next_original_failure_ordinal']=1018
snapshot['actual_product_processes']=0
snapshot['actual_database_calls']=0
snapshot['actual_native_calls']=0
p.write_bytes((json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'source_input_count':len(refs),'sha256':pin(p)['sha256'],'bytes':pin(p)['bytes']},ensure_ascii=False))
