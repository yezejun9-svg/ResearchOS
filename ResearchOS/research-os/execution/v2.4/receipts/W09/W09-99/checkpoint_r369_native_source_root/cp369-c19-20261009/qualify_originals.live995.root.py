"""Preserve actual Root diagnostic qualifications and immutable inputs; no Canon writes."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os
N=Path(__file__).resolve().parent
W=N.parent.parent
B=W.parent.parent/'W05/W05-99'
O=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def read(r):
    assert set(r)=={'path','sha256','bytes'}
    b=Path(r['path']).read_bytes()
    assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
    return b
def pin(p):
    p=p.resolve(strict=True); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def exact(p,h,n):
    r=dict(path=str(p.resolve(strict=True)),sha256=h,bytes=n);read(r);return r
def save(p,obj):
    with p.open('xb') as f:
        f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
resume=json.loads((N/'RESUME.cp369-main-profile-adopted.live993.root.json').read_bytes())
for r in resume['canonical_refs']:read(r)
p=json.loads(read(resume['pending_diagnostics_ref']))
assert [r['ordinal'] for r in p['pending']]==list(range(966,993))
orig993=exact(W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v2/original993.visible-tool-return.md','cedaa83eb67c2517c0176b19b29ca3234559b1bda5fcd7a8e87290d44a9a0d9b',3739)
orig994=exact(B/'genuine_release_resource_inventory_codex/release-resource-20261009-01/original994.original-tool-io.json','c90d731384b295d495166394902d52891fb358bbeb7cfa764a07abb43d481e10',2624)
for ordinal,ref,selector,outer,description,completeness in (
    (993,orig993,'original exec input and exec_command result chunk_id=011ef9',0,'CP370 Source worker treated legacy multi-call MD as JSON; original outer0/Python1; failed chain stopped.','VISIBLE_TRANSCRIPTION_NOT_HOST_RAW'),
    (994,orig994,'$.args / $.result / $.exit_codes',1,'Historical resource inventory used size instead of exactRef bytes; original outer1/Python1; failed chain stopped.','SOURCE_RECORDED_ORIGINAL_TOOL_IO')):
    p['pending'].append(dict(ordinal=ordinal,origin_ref=ref,origin_selector=selector,actual_outer_exit=outer,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,description=description,origin_capture_completeness=completeness))
assert [r['ordinal'] for r in p['pending']]==list(range(966,995))
p['next_original_failure_ordinal']=995
for row in p['pending']:read(row['origin_ref'])
pending_ref=save(N/'pending-diagnostics.live995.root.json',p)
cp=json.loads(read(resume['canonical_refs'][0]))
prior=cp['work_in_progress']['later_diagnostics_observed_after_cutoff']
assert [r['ordinal'] for r in prior]==list(range(966,970))
rows=[]
for v in p['pending']:
    selector=v['origin_selector']
    completeness=v.get('origin_capture_completeness','SOURCE_RECORDED_ORIGINAL_EVIDENCE')
    description=v['description']
    if v['ordinal']<970:
        baseline=prior[v['ordinal']-966]
        assert baseline['origin_ref']==v['origin_ref']
        description=baseline['description']
    rows.append(dict(ordinal=v['ordinal'],origin_ref=v['origin_ref'],origin_selector=selector,description=description,
        actual_outer_exit=v['actual_outer_exit'],actual_python_exit=v['actual_python_exit'],actual_native_exit=v['actual_native_exit'],
        exit_qualification=dict(schema='researchos.root-original-exit-qualification.v1',authority='ROOT_OBSERVED_DIAGNOSTIC_ONLY',
            origin_capture_completeness=completeness,unknown_is_null=True,source_capture_ref=v['origin_ref'],source_capture_selector=selector,
            diagnostic_source_ref=pending_ref,diagnostic_source_selector='pending[ordinal='+str(v['ordinal'])+']')))
unique=[(str(Path(r['origin_ref']['path']).resolve()).casefold(),r['origin_ref']['sha256'],r['origin_selector']) for r in rows]
assert len(unique)==len(set(unique))
O.mkdir(parents=True,exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
q=dict(schema='researchos.root-original-diagnostic-qualifications.v1',issued_by='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',created_utc=now,
    source_pending_ref=pending_ref,before_canonical_refs=resume['canonical_refs'],source_cutoff={'highest_ordinal':965,'next_failure_ordinal':966},
    next_original_failure_ordinal=995,rows=rows,scope='Original diagnostic counting only; no Native, formal, parent, or Source approval authority.',
    formal_acceptance=False,parent_acceptance=False,counter_reset=False)
qr=save(O/'original-diagnostic-qualifications.seed.live995.root.json',q)
resume.update(created_utc=now,next_original_failure_ordinal_live=995,pending_diagnostics_ref=pending_ref,
    C19_dispatcher_caller_source_status='V6_INDEPENDENT_SOURCE_ACCEPTED_CP370_PREPARED_V2_FIXING',
    CP370_status='PREPARED_DEFINITION_REQUEST_CHANGES_F1_TO_F5_SOURCE_V2_FIX_IN_PROGRESS',
    Root_original_qualification_ref=qr)
cr=W/'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
resume['C19_caller_v6_independent_handoff_ref']=exact(cr/'HDF.json','103ec67601f523d545499c8a7d0dc3b16f21d601c8152c232309f916815e0174',3327)
resume['C19_caller_v6_independent_manifest_ref']=exact(cr/'MF.json','0da7ad889c241c41c80ac309b32ea3cfc17e1401ac4a75ca9d32c56050a9a53c',3181)
resume['C19_caller_v6_independent_decision_ref']=exact(cr/'source-decision.json','0586fb5d30533d656fbfd6d4a4d2741bc1e088cdf34bcac1801af88e500fae26',3653)
for r in resume['canonical_refs']:read(r)
rr=save(N/'RESUME.cp369-main-profile-adopted.live995.root.json',resume)
print(json.dumps(dict(resume_ref=rr,pending_ref=pending_ref,qualification_ref=qr,next_original=995,Canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
