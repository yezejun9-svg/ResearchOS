"""Root qualifications from observed legacy formats; preserve partial failed writer output."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os
N=Path(__file__).resolve().parent
W=N.parent.parent
O=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def read(r):
    assert set(r)=={'path','sha256','bytes'}
    b=Path(r['path']).read_bytes()
    assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
    return b
def pin(p):
    p=p.resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def exact(p,h,n):
    r=dict(path=str(p.resolve(strict=True)),sha256=h,bytes=n);read(r);return r
def save(p,obj):
    with p.open('xb') as f:
        f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
resume=json.loads((N/'RESUME.cp369-main-profile-adopted.live993.root.json').read_bytes())
for r in resume['canonical_refs']:read(r)
partial_ref=pin(N/'pending-diagnostics.live995.root.json')
p=json.loads(read(partial_ref))
assert [r['ordinal'] for r in p['pending']]==list(range(966,995))
fr=pin(N/'failure995.original-tool-io.root.json');fv=json.loads(read(fr))
assert fv['ordinal']==995 and fv['actual_outer_exit']==1 and fv['actual_python_exit']==1 and fv['actual_native_exit'] is None
p['pending'].append(dict(ordinal=995,origin_ref=fr,origin_selector='args/result chunk_id=6a22ad',actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
    description='Root qualification builder assumed legacy pending rows already had origin_selector; original outer/Python1 after writing only immutable pending live995. No qualification/resume/Canon writes occurred.',origin_capture_completeness='ROOT_RECORDED_ORIGINAL_TOOL_IO'))
p['next_original_failure_ordinal']=996
assert [r['ordinal'] for r in p['pending']]==list(range(966,996))
for v in p['pending']:read(v['origin_ref'])
pending_ref=save(N/'pending-diagnostics.live996.root.json',p)
cp=json.loads(read(resume['canonical_refs'][0]));prior=cp['work_in_progress']['later_diagnostics_observed_after_cutoff']
assert [r['ordinal'] for r in prior]==list(range(966,970))
legacy={966:('2acc95',0,None,None),967:('43ad9b',1,None,None),968:('f3d65d',1,None,None),969:('e84755',1,1,None)}
failed_children={966:2,968:2,981:2,987:1,991:1}
rows=[]
for v in p['pending']:
    n=v['ordinal']
    if n in legacy:
        selector,outer,python,native=legacy[n]
        baseline=prior[n-966]
        assert baseline['origin_ref']==v['origin_ref'] and baseline['description']==v['description']
    else:
        selector=v['origin_selector'];outer=v['actual_outer_exit'];python=v['actual_python_exit'];native=v['actual_native_exit']
    completeness=v.get('origin_capture_completeness','SOURCE_RECORDED_ORIGINAL_EVIDENCE')
    q=dict(schema='researchos.root-original-exit-qualification.v1',authority='ROOT_OBSERVED_DIAGNOSTIC_ONLY',unknown_is_null=True,
        source_capture_ref=v['origin_ref'],source_capture_selector=selector,diagnostic_source_ref=pending_ref,diagnostic_source_selector='pending[ordinal='+str(n)+']')
    if n in failed_children:q['observed_failed_child_exit']=failed_children[n]
    row=dict(ordinal=n,origin_ref=v['origin_ref'],origin_selector=selector,description=v['description'],capture_completeness=completeness,exit_qualification=q,
        actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=native,actual_dispatcher_exit=v.get('actual_dispatcher_exit'),actual_model_exit=v.get('actual_model_exit'))
    assert all(x is None or type(x) is int for x in (outer,python,native,row['actual_dispatcher_exit'],row['actual_model_exit']))
    rows.append(row)
unique=[(str(Path(r['origin_ref']['path']).resolve()).casefold(),r['origin_ref']['sha256'],r['origin_selector']) for r in rows]
assert len(unique)==len(set(unique))
O.mkdir(parents=True,exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
q=dict(schema='researchos.root-cp370-original-invocation-qualification.v1',issued_by='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',created_utc=now,
    source_pending_ref=pending_ref,before_canonical_refs=resume['canonical_refs'],source_cutoff={'highest_ordinal':965,'next_failure_ordinal':966},next_original_failure_ordinal=996,rows=rows,
    formal_acceptance=False,parent_acceptance=False,counter_reset=False)
qr=save(O/'original-diagnostic-qualifications.seed.live996.root.json',q)
resume.update(created_utc=now,next_original_failure_ordinal_live=996,pending_diagnostics_ref=pending_ref,
    C19_dispatcher_caller_source_status='V6_INDEPENDENT_SOURCE_ACCEPTED_CP370_PREPARED_V2_FIXING',CP370_status='PREPARED_DEFINITION_REQUEST_CHANGES_F1_TO_F5_SOURCE_V2_FIX_IN_PROGRESS',Root_original_qualification_ref=qr)
cr=W/'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
resume['C19_caller_v6_independent_handoff_ref']=exact(cr/'HDF.json','103ec67601f523d545499c8a7d0dc3b16f21d601c8152c232309f916815e0174',3327)
resume['C19_caller_v6_independent_manifest_ref']=exact(cr/'MF.json','0da7ad889c241c41c80ac309b32ea3cfc17e1401ac4a75ca9d32c56050a9a53c',3181)
resume['C19_caller_v6_independent_decision_ref']=exact(cr/'source-decision.json','0586fb5d30533d656fbfd6d4a4d2741bc1e088cdf34bcac1801af88e500fae26',3653)
for r in resume['canonical_refs']:read(r)
rr=save(N/'RESUME.cp369-main-profile-adopted.live996.root.json',resume)
print(json.dumps(dict(resume_ref=rr,pending_ref=pending_ref,qualification_ref=qr,next_original=996,Canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
