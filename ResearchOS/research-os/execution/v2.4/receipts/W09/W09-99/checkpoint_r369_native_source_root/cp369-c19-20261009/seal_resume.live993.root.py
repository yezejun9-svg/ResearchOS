"""Root append-only durability: original observations through 992, nonformal Main adoption."""
from datetime import datetime, timezone
import hashlib, json, os
from pathlib import Path
N=Path(__file__).resolve().parent
W=N.parent.parent
def pin(p):
    p=p.resolve(strict=True); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(r):
    assert set(r)=={'path','sha256','bytes'}
    b=Path(r['path']).read_bytes()
    assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
    return b
def exact(p,sha,size):
    r={'path':str(p.resolve(strict=True)),'sha256':sha,'bytes':size}; read(r); return r
def save(name,obj):
    with (N/name).open('xb') as f:
        f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
    return pin(N/name)
old=json.loads((N/'RESUME.cp369-native-qualified.live986.root.json').read_bytes())
for r in old['canonical_refs']: read(r)
p=json.loads(read(old['pending_diagnostics_ref']))
assert [v['ordinal'] for v in p['pending']]==list(range(966,986))
def append(ordinal,path,sha,size,selector,outer,python,description,**extra):
    p['pending'].append(dict(ordinal=ordinal,origin_ref=exact(path,sha,size),origin_selector=selector,actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,description=description,**extra))
append(986,W/'w09_formal_profile_v4_independent_review_codex/profv4r-01a12c10/failure-153bb2.original-tool-io.json','32880e47da87e070709b806f6d44177339a2190f168fdd6e5c9e818f7c893838',5410,'153bb2',1,1,'Independent Source review mkdir omitted parent creation; no Main or Canon writes.')
obs=W/'w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v5/source-original-observations.json'
osh='ee01ed345c56dff55146c1c682b598cacd50d8276ce28fedd7c3604eea5c1ae5'
append(987,obs,osh,3250,'observations[root_ordinal=987]',None,None,'One original batched query had a missing frozen plan path and excessive output; later Ctrl-C terminates that same query, counted once. Full truncated origin unavailable; preserve observed results only.',origin_capture_completeness='OBSERVED_TRUNCATED_NOT_FULL',observed_missing_child_exit=1,observed_cancelled_child_exit=1)
b=W.parent.parent/'W05/W05-99/remaining_boundary_independent_review_codex/boundary-20261009-01'
append(988,b/'original-error-1b770f.json','261886c9bace4dd48b70fa5449ef5ba353910e011892fd287103f6d1ab5969b2',28024,'1b770f',1,1,'W05 narrow review indexed a dict roster as a list; no Actual rerun or Canon changes.')
append(989,b/'original-error-cdd1a7.json','056ce64644b866190346160e334fc6a1d60e6659b21ae4a21f96c6fdeaea7f44',581,'cdd1a7',1,None,'W05 narrow reviewer guessed a nonexistent workspace top AGENTS.md; repository AGENTS.md remains the real project instruction.')
append(990,W/'formal_profile_v4_adoption_independent_source_review_codex/adoptr-01a12072/failure-85cd9f.original-tool-io.json','24ea6898ae3e532d81341b687d8b200707a9da58bffded6c27339555d680407b',4525,'85cd9f',1,None,'Root adopter Source independent review read omitted research-os path; exact original IO preserved.')
append(991,obs,osh,3250,'observations[root_ordinal=991]',None,None,'Caller Source worker guessed decision.json; exact HDF names source-decision.json. Preserve observed failed child output; no invented full functions result.',origin_capture_completeness='OBSERVED_NOT_FULL',observed_failed_child_exit=1)
ap=W/'formal_profile_v4_actual_adoption_independent_review_codex/actualr-01a12072'
append(992,ap/'failure-aa52e1.original-tool-io.json','35019e0a44227a63071f00db50edcc92a75edcbc1494565c49fbe1e075e7427a',4581,'aa52e1',1,None,'Actual profile independent reviewer guessed adoption-decision.json; exact Main7 HDF supplies actual-decision.json. Read only; no Source/Main/Canon writes.')
assert [v['ordinal'] for v in p['pending']]==list(range(966,993))
for v in p['pending']: read(v['origin_ref'])
p['next_original_failure_ordinal']=993
pending=save('pending-diagnostics.live993.root.json',p)
old.update(created_utc=datetime.now(timezone.utc).isoformat(),next_original_failure_ordinal_live=993,pending_diagnostics_ref=pending,W09_formal_profile_source_status='MAIN_PROFILE_V4_SOURCE_ADOPTION_ACTUAL_VERIFIED_NONFORMAL',C19_dispatcher_caller_source_status='V5_REQUEST_CHANGES_STATIC_SOURCE_CONTINUITY_V6_SOURCE_FIX_IN_PROGRESS')
old['W09_profile_actual_independent_handoff_ref']=exact(ap/'HDF.json','340062540dc455bee4b38279ea6f8e8d913081c4c98b31274e32dc6d50d03a6e',3607)
old['W09_profile_actual_independent_manifest_ref']=exact(ap/'MF.json','51879507ff2d858aed167ac7956be74e7330092861d2e81e27050f2b5db79e85',2606)
old['W09_profile_actual_independent_decision_ref']=exact(ap/'actual-decision.json','986cdb9fd870df86579ecf72b7fe5c2ca1ae2c68cbf2625f91185af5a0dbe953',3032)
ad=json.loads(read(old['W09_profile_actual_independent_decision_ref']))
assert ad['decision']=='SOURCE_ADOPTION_ACTUAL_VERIFIED_NONFORMAL' and ad['formal_case_accepted_delta']==0 and ad['parent_acceptance'] is False
old['W09_profile_Main_after_refs']=ad['Main_after_refs']
for r in old['W09_profile_Main_after_refs']: read(r)
old['W09_profile_Actual_outcome_ref']=ad['actual_outcome_ref']; read(ad['actual_outcome_ref'])
old['W09_profile_Actual_original_IO_ref']=ad['original_actual_tool_io_ref']; read(ad['original_actual_tool_io_ref'])
cr=W/'main_c19_dispatcher_caller_independent_review_codex/c19v5-review-20261009'
old['C19_caller_v5_independent_handoff_ref']=exact(cr/'HDF.json','2f1ec8ff8791b0e59c6e810143ba45818f851a4fd78f813744f904f91052e4f5',3245)
old['C19_caller_v5_independent_manifest_ref']=exact(cr/'MF.json','8ba80ebe677ec166db7621644fdfdd0e043b8ccdc3e526a3073f5f0131648962',3198)
old['C19_caller_v5_independent_decision_ref']=exact(cr/'source-decision.json','0a8c24001e6abeb7424143d240bc2bcec96acb459d5688ad016b8ec95da45d8b',3314)
cp=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009'
old['CP370_registrar_prepared_manifest_ref']=exact(cp/'source-prepared-manifest.json','ff49d4a724cf3c51dac9971f781113f8db5797c9b04895a948e103075a3bb7bb',2124)
old['CP370_status']='SOURCE_PREPARED_DEFINITION_ONLY_NO_SCOPE_NO_FACTS_NO_CANON_WRITE'
wr=b/'review.json'
old['W05_remaining_boundary_independent_review_ref']=exact(wr,'2024bc6ff72eebf295bb008b1ddc08abfd41ec2a7657edc0934b1c1469e798cb',75925)
old['next_action']='Fix frozen static input continuity in Caller v6; obtain independent Source acceptance; Root build CP370 facts and cycle-free bounded scope with all original ordinals through live cutoff, then independent review and fresh Root post-seal context before actual Canon registration and exactly two qualified C19 consumer jobs. Preserve successful Native and W05 dev13 evidence. Full W05/W09 and 22 parents/42 Current cases remain open.'
assert old['current_formal_accepted']==0 and old['checkpoint_revision']==369 and old['ownership_revision']==173
for r in old['canonical_refs']: read(r)
resume=save('RESUME.cp369-main-profile-adopted.live993.root.json',old)
print(json.dumps(dict(resume_ref=resume,pending_diagnostics_ref=pending,live_next=993,canonical_unchanged=True,Main_profile_adoption_independently_verified=True,current_formal=0,formal_delta=0),ensure_ascii=False),flush=True)
