"""Prepare a finite, immutable CP369 Source registration without executing Native."""
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import types
N=Path(__file__).resolve().parent
w=N/'register_cp369.source.py';m=types.ModuleType('cp369_source');m.__file__=str(w);sys.modules[m.__name__]=m
exec(compile(w.read_bytes(),str(w),'exec'),m.__dict__)
def fixed(p,sha,size):
    ref=dict(path=str(Path(p).resolve(strict=True)),sha256=sha,bytes=size);m.read(ref);return ref
def main():
    P=m.W/'w09_c19_main_root_producer_v2_source_codex/mainc19p2-1a11fe4'
    V=m.W/'main_c19_root_producer_v2_independent_review_codex/review-1a11fff'
    A=m.W/'main_c19_adoption_decision_supplement_codex/adoptsupp-01a11fea'
    DA=m.B/'restored21_runtime_v3_actual_independent_review_codex/actualreview-1a11fff'
    ph=fixed(P/'HDF.json','8d3fe469f3797d0b7e72342e230696b99109359ed310a46cc191ce213a67d4ec',15498);p=m.load(ph)
    vh=fixed(V/'HDF.json','e7a931426882ae5217a4143e9ff821106b68454585e316ba543503bcc8f56ff9',2793);v=m.load(vh)
    ah=fixed(A/'HDF.json','c9a2924d4c6fb8656b1beebbfa8b1de03e12af9310c4cd8e718656dbf13c81a8',4288);a=m.load(ah)
    dh=fixed(DA/'HDF.json','b923aff86455114fa850a37e6934948e238ac6fdb07070422146b5ab552f6673',3418);dev=m.load(dh)
    contract_ref=fixed(P/'root-calling-contract.json','5fbae9c15d6e4dd4b6df6bffbe98cd78bd731ce809b017eef4648a16fbd88e9e',19919);contract=m.load(contract_ref)
    choice=m.load(contract['bound_source_refs']['choice_ref']);ad=m.load(a['actual_decision_ref'])
    scope=dict(schema=contract['root_scope_schema'],status=contract['root_scope_status'],issued_by=m.ACTOR,executor=m.ACTOR,source_handoff_ref=ph,source_manifest_ref=p['manifest_ref'],source_review_handoff_ref=vh,source_review_manifest_ref=v['manifest_ref'],source_review_decision_ref=v['source_decision_ref'],adoption_outcome_ref=ad['adoption_outcome_ref'],adoption_review_handoff_ref=ah,adoption_review_manifest_ref=a['manifest_ref'],adoption_review_decision_ref=a['actual_decision_ref'])
    scope.update(contract['bound_source_refs'])
    for k in ('source_root','run_id','receipt_root','scratch_root','output_root','selected_tests','expected_native_ids','source21','main_seven_after_refs'):scope[k]=choice[k]
    scope.update(list_timeout_seconds=240,producer_timeout_seconds=420,inner_Go_timeout_seconds=180,maximum_go_test_runs=1,maximum_go_list_runs=1)
    for k in ('formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry'):scope[k]=False
    for k in ('formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes'):scope[k]=0
    m.require(set(scope)==set(contract['scope_required_fields']),'EXACT45_SCOPE_FIELDS')
    sr=m.save('scope-registration.root.json',scope)
    origins=[
        (953,m.B/'checkpoint_r368_w05_independent_review_codex/cp368r-01a11fea/failure953.original-tool-io.json','5526df6a460b1541612533ba44dca285bb756180568d1cc5766efb13d11f0015',1375,1,None,'c3b898','Source reviewer guessed missing registration-facts.json.'),
        (954,V/'failure954.original-tool-io.json','447ef857ee89b6094b798f7905cb3870fc3a72fbd4f7c0c4b3c4487bdd200e15',3469,1,None,'36b716','Source reviewer guessed missing HANDOFF.md.'),
        (955,m.W/'w09_formal_profile_gap_map_readonly_codex/query955-20261009/original-tool-io.json','ab7867e2863e929edadada46d5bd51695b9157bbb170f5927bf5827aab1f9fb6',9614,0,None,'8cf996','Read-only rg child exit2; final child succeeded, original outer0. Preserve both distinct observations.'),
        (956,m.W/'w09_formal_profile_gap_map_readonly_codex/query2794b6-20261009/original-tool-io.json','702adcecc7f3b28baf84d2026df306a164b0b65a19325053095e1ebe4d93d346',11961,1,None,'2794b6','One read-only query used two nonexistent paths. Child exits unobserved NULL; returned output truncated as originally reported.'),
        (957,m.B/'checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009/failure957.original-tool-io.root.json','4270b24b1c7f09d8297c88acc279cd16db20ca8dac0afb167c33900c5ac446d5',3631,1,1,'aeafbc','Root canonical registration forward-slash context argv rejected before SourceGuard/transaction; later reconciled fresh-input invocation succeeded.'),
        (958,m.W/'w09_formal_profile_source_codex/prof-20261009a/failure-origin-958.txt','80c9ea69f2bb3eae62df91cefb977935850a3946ff0e402f90f60bf48ca99e45',1065,None,None,'functions.exec JS SyntaxError','Missing JS right-parenthesis; no shell or Python dispatch, every numeric exit NULL.'),
        (959,m.B/'checkpoint_r368_actual_independent_review_codex/actual368r-01a11fea/failure959.original-tool-io.json','2dff4842eb24adb46e19df211a09b3f80da1edc98f5b3e47616c1cec8f645565',1122,1,None,'6cfa1a','Independent actual-review stale store generated undefined path.'),
        (960,m.B/'checkpoint_r368_actual_independent_review_codex/actual368r-01a11fea/failure960.original-tool-io.json','9636c5d0880ca0ab25e4676b0aa94ee5c14213aa53d32c1f29314471160de704',1158,1,None,'ccf906','Independent actual-review stale store generated undefined path.'),
        (961,m.B/'checkpoint_r368_actual_independent_review_codex/actual368r-01a11fea/failure961.original-tool-io.json','cf290a0130bc03467ad36a5fc4ae78164b3dd6e6a2db68efa31e85448f49024b',1152,1,None,'ffbd3a','Independent actual-review stale store generated undefined path.'),
        (962,m.B/'checkpoint_r368_actual_independent_review_codex/actual368r-01a11fea/failure962.original-tool-io.json','f988d455739e3d22fb15f76beab4ed69905ff8e92f625ac169ba75904a9e06e5',1139,1,None,'2c3a6e','Independent actual-review stale store generated undefined path.'),
        (963,m.B/'checkpoint_r368_actual_independent_review_codex/actual368r-01a11fea/failure963.original-tool-io.json','ad936afb8cd641a7a0e9ed25a313b308c9c4142eeb13d4647ec7a15cb42d3e00',1080,1,None,'c74e98','Independent actual-review stale store generated undefined path.'),
        (964,m.W/'w09_formal_profile_source_codex/prof-20261009a/failure-origin-unassigned-native-report-read.txt','d4b6707f468ca83b47e8afb27b97fe35718e45afc43c99ced391f7d34807bbfa',1330,1,1,'profile historical report read','Source author guessed nonexistent current-Main historical report path; no Native/model invoked.'),
        (965,DA/'failure-read-summary.original-tool-io.json','f08baaa63d738e3e64a44794c6b639781c544b5719a15f1b1bb93bb4cb28a678',13112,1,1,'9a8635','W05 actual reviewer summarized list as dict.items; Rootassigned965 preserved initial requested964. No Actual rerun.')]
    diagnostics=[dict(ordinal=ordinal,origin_ref=fixed(path,sha,size),actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=None,description=description,origin_selector=selector,exit_qualification='Exact originally observed exits only; unobserved Python/Native/model or child exits remain NULL. Source findings/negative controls and later successful input do not reset this count.') for ordinal,path,sha,size,outer,python,selector,description in origins]
    cr=[dict(path=str(path.resolve(strict=True)),sha256=sha,bytes=size) for path,(sha,size) in zip(m.CANON,m.BEFORE)]
    for ref in cr:m.read(ref)
    closed=fixed(m.B/'integration_codex/restored21-v3-target-root-20261009-01/validation.closed.json','3b5109fc204e73f0dd455e85ec8a369c40c8777d1368ef3ae0aed67bbffe0ab8',12474)
    owner=dict(owner=m.ACTOR,current_source_writer=None,state=m.STATE,scope_ref=sr,source_handoff_ref=ph,source_manifest_ref=p['manifest_ref'],source_review_handoff_ref=vh,source_review_manifest_ref=v['manifest_ref'],adoption_outcome_ref=scope['adoption_outcome_ref'],adoption_review_handoff_ref=ah,source_root=scope['source_root'],run_id=scope['run_id'],receipt_root=scope['receipt_root'],scratch_root=scope['scratch_root'],output_root=scope['output_root'],formal_case_accepted_delta=0,parent_acceptance=False)
    worker=dict(step_id='W09-99',slice_id=m.SLICE,owner=m.ACTOR,state=m.STATE,scope_ref=sr,source_handoff_ref=ph,source_review_handoff_ref=vh,adoption_outcome_ref=scope['adoption_outcome_ref'],run_id=scope['run_id'])
    facts=dict(schema='researchos.root-cp369-native-registration-facts.v1',issued_by=m.ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=cr,scope_ref=sr,calling_contract_ref=contract_ref,owner=owner,worker=worker,diagnostics=diagnostics,W05_actual_closed_ref=closed,W05_actual_review_handoff_ref=dh,W05_actual_review_manifest_ref=dev['manifest_ref'],pairs=[dict(handoff_ref=h,manifest_ref=o['manifest_ref']) for h,o in ((ph,p),(vh,v),(ah,a),(dh,dev))],input_refs=[*contract['bound_source_refs'].values(),scope['adoption_outcome_ref'],scope['source_review_decision_ref'],scope['adoption_review_decision_ref'],*scope['source21'],*scope['main_seven_after_refs']],formal_acceptance=False,checkpoint_note='CP369: retain independently reviewed W05 dev13 PARTIAL NativeOPEN; append original953..965 exactly once without resetting NULL/zero evidence; register Root single Main C19 producer v2 owner after Source/adoption independent qualification. No new Native, real dispatcher, formal or parent acceptance in registration.')
    fr=m.save('checkpoint.execution.facts.json',facts)
    live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by=m.ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=dict(highest_ordinal=965,next_failure_ordinal=966),next_original_failure_ordinal=966,pending=[])
    lr=m.save('live-context.source-check.root.json',live)
    proof=m.execute('check',fr,lr)
    old_c,old_o=[m.load(ref) for ref in cr[:2]]
    controls=[]
    for label,mutate in [('reject live reset',lambda x:x.update(next_original_failure_ordinal=965)),('reject boolean live',lambda x:x.update(next_original_failure_ordinal=True)),('reject omitted pending',lambda x:x.update(next_original_failure_ordinal=967))]:
        bad=copy.deepcopy(live);mutate(bad)
        try:m.validate_live(bad)
        except ValueError:controls.append(dict(label=label,rejected=True))
        else:raise AssertionError(label)
    for label,mutate in [('preserve two parents',lambda c,o:c['work_in_progress'].update(construction_active_parents=['W05','W09','W10'])),('reject duplicate worker',lambda c,o:c['workers'].append(copy.deepcopy(worker))),('preserve active Root',lambda c,o:o['active_integrator'].update(id='someone_else'))]:
        c,o=copy.deepcopy(old_c),copy.deepcopy(old_o);mutate(c,o)
        try:m.transform(c,o,facts,fr,c,o,live)
        except ValueError:controls.append(dict(label=label,rejected=True))
        else:raise AssertionError(label)
    control=m.save('source-controls.json',dict(controls=controls,synthetic_control_authority=False,Native_executed=False,formal_case_accepted_delta=0))
    files=['register_cp369.source.py','build_source.root.py','scope-registration.root.json','checkpoint.execution.facts.json','live-context.source-check.root.json','source_guard.cleanup.check.json','canonical_pair.check.json','source-controls.json']
    mf=m.save('MF.json',dict(schema='researchos.root-cp369-source-manifest.v1',members=[m.pin(N/name) for name in files]))
    hf=m.save('HDF.json',dict(schema='researchos.root-cp369-source-handoff.v1',actor_id=m.ACTOR,status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW_NO_CANON_WRITE',manifest_ref=mf,writer_ref=m.pin(w),facts_ref=fr,scope_ref=sr,proof_ref=proof,controls_ref=control,source_cutoff=dict(highest_ordinal=965,next_failure_ordinal=966),formal_case_accepted_delta=0,actual_executed=False,all_handles_closed=True))
    print(json.dumps(dict(handoff_ref=hf,manifest_ref=mf,facts_ref=fr,scope_ref=sr,proof_ref=proof,actual_executed=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
