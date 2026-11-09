"""Source prepared for a fresh Root host observation after facts review; not auto-run."""
from datetime import datetime, timezone
from pathlib import Path
import copy, hashlib, json, os

N=Path(__file__).resolve().parent
W=N.parent.parent
S=W/'checkpoint_r369_native_source_root/cp369-c19-20261009'
V4=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
EXITS=('actual_outer_exit','actual_python_exit','actual_native_exit','actual_dispatcher_exit','actual_model_exit')

def pin(path):
    path=path.resolve(strict=True);raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(Path(ref['path']))==ref
    return Path(ref['path']).read_bytes()

def exact(path,sha,size):
    ref=dict(path=str(path.resolve(strict=True)),sha256=sha,bytes=size);read(ref);return ref

def save(path,value):
    with path.open('xb') as file:
        file.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());file.flush();os.fsync(file.fileno())
    return pin(path)

review_input=json.loads((N/'postseal-registrar-review.root.json').read_bytes())
reviews=review_input['registrar_review_refs']
assert len(reviews)==3
rh,rm,decision=[json.loads(read(ref)) for ref in reviews]
assert decision['schema']=='researchos.w09-cp370-registrar-independent-source-decision.v1'
assert decision['decision']=='ACCEPTED_SOURCE_ONLY' and decision['actor_id']=='codex:/root/attach_fixture_source_review' and decision['actor_role']=='INDEPENDENT_NON_AUTHOR'
assert all(decision[key] is False for key in ('actual_registration','formal_acceptance','parent_acceptance'))
assert rh['manifest_ref']==reviews[1] and rh['source_decision_ref']==reviews[2] and reviews[2] in rm['members']
assert decision['registrar_ref']==exact(V4/'register_cp370.source.py','d3a824904bc171bea8db5d9d2dcf64bd0577ecb0a8c2cf53471cd31cf325f95c',59180)
assert decision['source_hdf_ref']==exact(V4/'HDF.json','36b3f37527ccba3c64c4e55d723e34735c4a93214342210d498c7dee64ed824e',2760)
assert decision['source_mf_ref']==exact(V4/'MF.json','f0ca65b9f3ed8510d156cefbfc0a65ff89c755395bc681cb679ca52c11edf570',7286)
read(review_input['source_facts_ref']);read(review_input['source_seed_live_ref'])
facts=json.loads(read(review_input['source_facts_ref']))
assert facts['live_ref']==review_input['source_seed_live_ref']
assert review_input['source_facts_ref']['path']==str((V4/'registration-facts.root.json').resolve(strict=True))
assert decision['root_facts_ref']==review_input['source_facts_ref']
assert decision['root_seed_live_ref']==review_input['source_seed_live_ref']
now=datetime.now(timezone.utc)
assert now>datetime.fromisoformat(decision['reviewed_at'].replace('Z','+00:00'))
resume=json.loads((S/'RESUME.cp369-main-profile-adopted.live1005.root.json').read_bytes())
for ref in resume['canonical_refs']:read(ref)
assert facts['before_canonical_refs']==resume['canonical_refs']
pending_ref=exact(S/'pending-diagnostics.live1005.root.json','3c53c0613a91c65d4d892d56c79d5ad3c134ee6b215063d7b7eac941dc9b7f90',33252)
pending=json.loads(read(pending_ref))['pending']
assert [row['ordinal'] for row in pending]==list(range(966,1005))
seed_ref=exact(N/'original-diagnostic-qualifications.seed.live1004.root.json','c4de0877dadf3aba8d8c9f227590dd4a0fc094769b5f21ad8456f8cf4e5a0b7f',70982)
seed=json.loads(read(seed_ref));rows=copy.deepcopy(seed['rows'])
assert len(rows)==38
for row,source in zip(rows,pending[:38]):
    assert all(row[key]==source[key] for key in ('ordinal','origin_ref','description'))
    read(row['origin_ref']);row['exit_qualification']['diagnostic_source_ref']=pending_ref
source=pending[38];assert source['ordinal']==1004
read(source['origin_ref']);read(source['capture_binding_ref']);read(source['original_tool_io_ref'])
row={key:source[key] for key in ('ordinal','origin_ref','origin_selector','description',*EXITS)}
row['capture_completeness']=source['origin_capture_completeness']
row['exit_qualification']=dict(schema='researchos.root-original-exit-qualification.v1',authority='ROOT_OBSERVED_DIAGNOSTIC_ONLY',unknown_is_null=True,
    source_capture_ref=source['origin_ref'],source_capture_selector=source['origin_selector'],diagnostic_source_ref=pending_ref,diagnostic_source_selector='pending[ordinal=1004]')
assert all(row[key] is None or type(row[key]) is int for key in EXITS)
rows.append(row)
identities=[(row['origin_ref']['sha256'],row['origin_selector']) for row in rows]
assert len(identities)==len(set(identities))==39
qualification=dict(schema='researchos.root-cp370-original-invocation-qualification.v1',issued_by='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',created_utc=now.isoformat(),
    source_pending_ref=pending_ref,before_canonical_refs=resume['canonical_refs'],source_cutoff={'highest_ordinal':965,'next_failure_ordinal':966},
    next_original_failure_ordinal=1005,rows=rows,formal_acceptance=False,parent_acceptance=False,counter_reset=False)
qualification_ref=save(N/'original-diagnostic-qualifications.postseal.live1005.root.json',qualification)
resume.update(created_utc=now.isoformat(),Root_original_qualification_ref=qualification_ref,CP370_status='REGISTRAR_V4_ROOT_FACTS_SOURCE_ACCEPTED_POSTSEAL_ACTUAL_OBSERVED',
    registrar_facts_independent_review_refs=reviews,source_facts_ref=review_input['source_facts_ref'])
for ref in resume['canonical_refs']:read(ref)
resume_ref=save(S/'RESUME.cp369-main-profile-adopted.postseal.live1005.root.json',resume)
print(json.dumps(dict(resume_ref=resume_ref,pending_ref=pending_ref,qualification_ref=qualification_ref,next_original=1005,
                     Canonical_unchanged=True,formal_delta=0,registrar_review_refs=reviews,canonical_refs=resume['canonical_refs']),ensure_ascii=False),flush=True)
