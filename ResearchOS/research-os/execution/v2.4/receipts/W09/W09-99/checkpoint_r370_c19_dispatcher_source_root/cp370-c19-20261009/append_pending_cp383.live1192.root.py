"""Append the preserved evidence-marker error1191, retaining six prior rows."""
from pathlib import Path
import copy,hashlib,json,os
S=Path(__file__).resolve().parent;W=S.parent.parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
old=S/'pending-diagnostics.cp383.live1191.root.json';oldref=pin(old)
assert oldref['sha256']=='e50fa831cd9a2cfa535265a4a61b47bb792182e236bb9bc701fd1a4eb862b35f' and oldref['bytes']==13681
before=json.loads(old.read_bytes());prefix=copy.deepcopy(before['pending'])
p=W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-06-attach/original-1191.binding.json';br=pin(p)
assert br['sha256']=='08af275ac7e282f466427654571ab51f3cfa2af7fa1360bf7a6ba03f34f7e452' and br['bytes']==2128
b=json.loads(p.read_bytes());assert b['original_ordinal']==1191 and b['actual_outer_exit']==1 and b['actual_python_exit']==1
rr=b['original_raw_ref'];assert pin(rr['path'])==rr
lines=Path(rr['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3
assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256'] and [len(x) for x in lines]==b['original_line_bytes']
ev=[json.loads(x) for x in lines];assert ev[0]['payload']['id']==b['actor_thread_id']
assert ev[1]['payload']['call_id']==ev[2]['payload']['call_id']==b['actual_call_id']
host=b['host_event_ref'];assert pin(host['path'])==host
with Path(b['source_audit_path']).open('rb') as f:
    for offset,line in zip(b['source_line_offsets'],lines):
        assert offset+len(line)<=b['source_prefix_size_observed'];f.seek(offset);assert f.readline()==line
    raw=Path(host['path']).read_bytes();f.seek(b['host_event_offset']);assert f.readline()==raw
    assert json.loads(raw)['ordinal']==b['host_event_ordinal']
row=dict(ordinal=1191,origin_ref=rr,origin_selector='$',capture_binding_ref=br,description='BR6 independent Source reviewer required uppercase PYTHON_EXIT=0 although actual successful Source host used Python_exit=0; evidence assertion failed after24 passed controls. Failed25 retained and only tail corrected.',capture_completeness='ACTUAL_ORIGINAL_3LF_WITH_SEPARATE_SAVED_HOST_EVENT',source_fact_refs=[br,rr,host],actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
after=copy.deepcopy(before);after['pending'].append(row);after['next_original_failure_ordinal']=1192
assert after['pending'][:-1]==prefix and [x['ordinal'] for x in after['pending']]==list(range(1185,1192))
pr=save(S/'pending-diagnostics.cp383.live1192.root.json',after)
vr=save(S/'pending-diagnostics.cp383.live1192.verified.root.json',dict(schema='researchos.root-original-diagnostic-suffix-verification.v1',issued_by='codex:/root',pending_ref=pr,verified_successful_prefix_ref=oldref,verified_successful_prefix_receipt_ref=pin(S/'pending-diagnostics.cp383.live1191.verified.root.json'),old_six_rows_unchanged=True,old_original_verification_replayed=False,new_original1191_3LF_and_host_event_verified=True,new_source_fact_refs=[br,rr,host],registered=False,Canon_written=False,product_calls=0))
print(json.dumps(dict(pending_ref=pr,verification_ref=vr,next_original_failure_ordinal=1192,Canon_written=False),ensure_ascii=False))
