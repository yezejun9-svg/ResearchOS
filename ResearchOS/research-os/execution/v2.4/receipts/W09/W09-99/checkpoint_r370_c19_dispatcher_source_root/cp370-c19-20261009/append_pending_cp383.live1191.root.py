"""Append original1190 to the verified immutable five-row prefix."""
from pathlib import Path
import copy,hashlib,json,os
S=Path(__file__).resolve().parent
W=S.parent.parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
old=S/'pending-diagnostics.cp383.live1190.root.json';oldref=pin(old)
assert oldref['sha256']=='149fd9cd7e661a6992b9b4f6add20323e30a919df2f7fbd95e3f3dde4bf1129b' and oldref['bytes']==11806
before=json.loads(old.read_bytes());prefix=copy.deepcopy(before['pending'])
p=W/'w09_formal_root_bridge_source_codex/bridge-20261010-06/original-1190.binding.json';br=pin(p)
assert br['sha256']=='a0bc23695fa514729231272778d4be74d3c3b826d41f1d4d61765556b438240b' and br['bytes']==1449
b=json.loads(p.read_bytes());assert b['original_ordinal']==1190 and b['actual_outer_exit']==0 and b['actual_python_exit'] is None
rr=b['original_raw_ref'];assert pin(rr['path'])==rr
lines=Path(rr['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3
assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256'] and [len(x) for x in lines]==b['original_line_bytes']
events=[json.loads(x) for x in lines];assert events[0]['payload']['id']==b['actor_thread_id']
assert events[1]['payload']['call_id']==events[2]['payload']['call_id']==b['actual_call_id']
with Path(b['source_audit_path']).open('rb') as f:
    for offset,line in zip(b['source_line_offsets'],lines):
        assert offset+len(line)<=b['source_prefix_size_observed'];f.seek(offset);assert f.readline()==line
row=dict(ordinal=1190,origin_ref=rr,origin_selector='$',capture_binding_ref=br,description='Full BR6 Source-only reader guessed decision.json instead of published review-decision.json; Get-Content error retained with actual compound host exit0. No product process.',capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',source_fact_refs=[br,rr],actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
after=copy.deepcopy(before);after['pending'].append(row);after['next_original_failure_ordinal']=1191
assert after['pending'][:-1]==prefix and [x['ordinal'] for x in after['pending']]==list(range(1185,1191))
pr=save(S/'pending-diagnostics.cp383.live1191.root.json',after)
vr=save(S/'pending-diagnostics.cp383.live1191.verified.root.json',dict(schema='researchos.root-original-diagnostic-suffix-verification.v1',issued_by='codex:/root',pending_ref=pr,verified_successful_prefix_ref=oldref,verified_successful_prefix_receipt_ref=pin(S/'pending-diagnostics.cp383.live1190.verified.root.json'),old_five_rows_unchanged=True,old_original_verification_replayed=False,new_original1190_3LF_verified=True,new_source_fact_refs=[br,rr],registered=False,Canon_written=False,product_calls=0))
print(json.dumps(dict(pending_ref=pr,verification_ref=vr,next_original_failure_ordinal=1191,Canon_written=False),ensure_ascii=False))
