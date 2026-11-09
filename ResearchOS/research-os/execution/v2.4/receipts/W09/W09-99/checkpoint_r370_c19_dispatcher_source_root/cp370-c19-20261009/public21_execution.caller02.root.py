"""Root prepares current, causal documents for the independently reviewed public caller."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys, uuid
S=Path(__file__).resolve().parent
env={'__name__':'root_public_documents','__file__':str(S/'public21_actual_resources.caller02.host02.root.py')}
exec(compile((S/'public21_actual_resources.caller02.host02.root.py').read_text().split('mode=sys.argv[1]')[0],env['__file__'],'exec'),env)
api=env['api'];base=env['base'];pin=env['pin'];doc=env['doc'];save=env['save'];now=env['now'];O=env['O'];B=env['B'];ROOT=env['ROOT'];THREAD=env['THREAD']
mode=sys.argv[1]
def current():
    refs=[pin(p) for p in base.CANON]
    rev=dict(zip(('checkpoint','path_ownership','step_state','commands'),[api.doc(r).get('revision') for r in refs]))
    api.current_four(refs,rev)
    return refs,rev
def observe_request(op,refs):
    return save(op+'.observation-request.root.json',dict(operation=op,observed_refs=refs,peer_actor=None))
if mode=='current-input':
    refs,rev=current()
    assert rev['checkpoint']==378 and rev['path_ownership']==182
    rr=save('execution-resume.current.root.json',dict(issued_by=ROOT,canonical_refs=refs,expected_revisions=rev,created_utc=now(),live_next_failure_ordinal=1158,pending_diagnostics_preserved=True))
    observe_request('POSTREVIEW_CURRENT_FOUR',refs)
    print({'resume_ref':rr,'current_refs':refs})
elif mode=='request':
    refs,rev=current();resume=pin(O/'execution-resume.current.root.json');assert doc(resume['path'])['canonical_refs']==refs
    live=save('postreview.current.root.json',dict(issued_by=ROOT,canonical_refs=refs,expected_revisions=rev,root_resume_ref=resume,review_decision_ref=env['refs_caller_review']()['decision'],capture_binding_ref=pin(O/'POSTREVIEW_CURRENT_FOUR.actual-root-binding.root.json'),created_utc=now()))
    start=datetime.now(timezone.utc);cid=uuid.uuid4().hex
    case=save('bootstrap.case.root.json',dict(case_id=cid,output_root=str(B/'integration_codex'/('schema21-public-'+cid))))
    cp=api.doc(refs[0]);cutoff=cp['work_in_progress']['root_next_failure_ordinal_live']
    pending=save('execution.pending-preserved.root.json',dict(schema='researchos.root-pending-diagnostics.v1',issued_by=ROOT,counter_reset=False,registered_in_current_canon=False,current_canonical_refs=refs,source_cutoff_original_failure_ordinal=cutoff-1,next_original_failure_ordinal=cutoff,pending=[],later_live_next_failure_ordinal=1158,later_pending_ordinals=list(range(cutoff,1158)),later_pending_preserved=True))
    q=dict(env['common'](),schema='researchos.root-public21-registration-request.v1',issued_by=ROOT,root_thread_id=THREAD,scope_key=api.SCOPE_KEY,formal_acceptance=False,case_request_ref=case,caller_receipt_root=str(B/'integration_codex'/('public21-caller-'+cid)),registration_root=str(B/'integration_codex'/('public21-registration-'+cid)),before_canonical_refs=refs,expected_revisions=rev,runtime_qualification_ref=pin(O/'runtime-qualification.issued.actual.root.json'),root_resume_ref=resume,postreview_live_ref=live,created_utc=start.isoformat(),lease_expires_at=(start+timedelta(seconds=1800)).isoformat(),pending_ref=pending)
    api.request_identity(q,api.doc(case));api.finite_lease(api.doc(api.doc(q['runtime_qualification_ref'])['qualification_scope_ref'])['created_utc'],api.doc(api.doc(q['runtime_qualification_ref'])['qualification_scope_ref'])['lease_expires_at'],180)
    qr=save('execution.registration.request.root.json',q)
    print(__import__('json').dumps(dict(request_ref=qr),ensure_ascii=False))
elif mode=='activation-input':
    q=doc(O/'execution.registration.request.root.json');refs,rev=current();assert refs==q['before_canonical_refs']
    fr=pin(Path(q['registration_root'])/'facts.root.json')
    observe_request('ACTIVATION_FACTS_CURRENT_FOUR',[fr,*refs]);print(__import__('json').dumps(dict(facts_ref=fr),ensure_ascii=False))
elif mode=='activation':
    q=doc(O/'execution.registration.request.root.json');refs,rev=current();assert refs==q['before_canonical_refs']
    value=dict(schema='researchos.root-public21-activation.v1',issued_by=ROOT,root_thread_id=THREAD,scope_key=api.SCOPE_KEY,formal_acceptance=False,facts_ref=pin(Path(q['registration_root'])/'facts.root.json'),before_canonical_refs=refs,created_utc=now(),capture_binding_ref=pin(O/'ACTIVATION_FACTS_CURRENT_FOUR.actual-root-binding.root.json'))
    print(__import__('json').dumps(dict(activation_ref=save('execution.activation.root.json',value)),ensure_ascii=False))
elif mode=='pre-entry-input':
    q=doc(O/'execution.registration.request.root.json');refs,rev=current();assert rev['checkpoint']==q['expected_revisions']['checkpoint']+1
    facts=doc(Path(q['registration_root'])/'facts.root.json');rr=pin(Path(q['registration_root'])/'activate.result.json')
    observe_request('PUBLIC21_BOOTSTRAP_PREREQUISITES',[facts['scope_ref'],pin(Path(q['registration_root'])/'facts.root.json'),rr,q['runtime_qualification_ref'],*q['runner_review_refs'].values(),*refs]);print({'current_refs':refs})
elif mode=='actual-request':
    q=doc(O/'execution.registration.request.root.json');refs,rev=current();facts=doc(Path(q['registration_root'])/'facts.root.json')
    intent=save('bootstrap.host-call-intent.root.json',dict(issued_by=ROOT,kind='ACTUAL_HOST_CALL_INTENT',external_hostpair_required=True,scope_ref=facts['scope_ref'],case_request_ref=q['case_request_ref']))
    value=dict(schema='researchos.root-public21-actual-request.v1',issued_by=ROOT,root_thread_id=THREAD,scope_key=api.SCOPE_KEY,formal_acceptance=False,scope_ref=facts['scope_ref'],facts_ref=pin(Path(q['registration_root'])/'facts.root.json'),case_request_ref=q['case_request_ref'],runtime_qualification_ref=q['runtime_qualification_ref'],current_canonical_refs=refs,registration_result_ref=pin(Path(q['registration_root'])/'activate.result.json'),host_call_intent_ref=intent,pre_entry_host_binding_ref=pin(O/'PUBLIC21_BOOTSTRAP_PREREQUISITES.actual-root-binding.root.json'),created_utc=now())
    print(__import__('json').dumps(dict(actual_request_ref=save('bootstrap.actual.request.root.json',value)),ensure_ascii=False))
else:raise ValueError('ROOT_DOCUMENT_MODE')
