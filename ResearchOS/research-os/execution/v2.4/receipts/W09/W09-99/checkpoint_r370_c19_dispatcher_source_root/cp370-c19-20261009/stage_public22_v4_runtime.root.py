"""Root-only activation inputs, then actual request after successful activation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
P=R/'execution/v2.4/receipts/W05/W05-99/public22_root_caller_registration_source_codex/p22root-20261009-04'
ROOT='codex:/root'
def pin(path):
    p=Path(path).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(ref):
    assert pin(ref['path'])==ref,'EXACT_INPUT_CHANGED'
    return json.loads(Path(ref['path']).read_bytes())
def save(name,value):
    with (N/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
def now():return datetime.now(timezone.utc).isoformat()
assert len(sys.argv)==5
mode=sys.argv[1];config=read(dict(path=sys.argv[2],sha256=sys.argv[3],bytes=int(sys.argv[4])))
assert config['issued_by']==ROOT
facts_ref=config['facts_ref'];facts=read(facts_ref)
build=read(facts['build_request_ref']);scope=read(facts['scope_ref'])
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
if mode=='activation-inputs':
    assert current==facts['before_canonical_refs']
    checked=read(config['check_result_ref'])
    assert checked['mode']=='check' and checked['transaction'] is None
    assert checked['scope_ref']==facts['scope_ref'] and checked['complete_inverse'] is True
    cleanup=read(pin(P/'source-guard.cleanup.check.root.json'))
    assert cleanup['closed'] is True and cleanup['retained_handles_count']==0 and cleanup['errors']==[]
    pending=read(facts['pending_ref']);old_rows=list(pending['pending'])
    for row in config['later_originals']:
        assert row['ordinal']==pending['next_original_failure_ordinal']
        assert pin(row['origin_ref']['path'])==row['origin_ref']
        if row['capture_binding_ref'] is not None:read(row['capture_binding_ref'])
        pending['pending'].append(row);pending['next_original_failure_ordinal']+=1
    assert pending['pending'][:len(old_rows)]==old_rows
    assert pending['next_original_failure_ordinal']==config['live_next']
    witness_ref=save('public22.v4.activation-witness.root.json',dict(
        schema='researchos.root-public22-activation-witness.v1',issued_by=ROOT,
        source_review_ref=facts['review_decision_ref'],scope_ref=facts['scope_ref'],
        external_hostpair_ref=read(facts['review_hostpair_binding_ref'])['original_capture_ref'],
        actual_build_tool_io_ref=config['build_tool_io_ref'],
        actual_check_tool_io_ref=config['check_tool_io_ref'],
        actual_check_result_ref=config['check_result_ref'],
        created_utc=now(),formal_acceptance=False,parent_acceptance=False))
    read(config['build_tool_io_ref']);read(config['check_tool_io_ref'])
    pending.update(activation_witness_ref=witness_ref,review_decision_ref=facts['review_decision_ref'],
        scope_ref=facts['scope_ref'],created_utc=now())
    pending_ref=save('pending-diagnostics.cp370.activation.live%d.root.json'%config['live_next'],pending)
    resume=read(build['root_resume_ref'])
    resume.update(prior_resume_ref=build['root_resume_ref'],created_utc=now(),
        next_original_failure_ordinal_live=config['live_next'],pending_diagnostics_ref=pending_ref,
        W05_public22_root_caller_status='V4_ROOT_BUILD_AND_CHECK_VERIFIED_PENDING_ATOMIC_ACTIVATION',
        W05_public22_actual_facts_ref=facts_ref,W05_public22_actual_check_ref=config['check_result_ref'])
    resume_ref=save('RESUME.cp370-public22-v4-activate.live%d.root.json'%config['live_next'],resume)
    assert [pin(Path(r['path'])) for r in current]==current
    print(json.dumps(dict(activation_pending_ref=pending_ref,activation_witness_ref=witness_ref,
        root_resume_ref=resume_ref,next_original=config['live_next'],canonical_unchanged=True,
        formal_delta=0),ensure_ascii=False),flush=True)
elif mode=='actual-request':
    result_ref=config['activation_result_ref'];result=read(result_ref)
    assert result_ref==pin(P/'registration.activate.root.json')
    assert result['mode']=='activate' and result['transaction'] is not None
    assert result['complete_inverse'] is True and result['SS_CM_unchanged'] is True
    assert result['proposed_after_refs']==current[:2] and current[2:]==facts['before_canonical_refs'][2:]
    cp=read(current[0]);ow=read(current[1])
    assert cp['revision']==371 and ow['revision']==175
    assert cp['work_in_progress']['public22_root_scope_ref']==facts['scope_ref']
    old_cp=read(pin(N/'historical.cp370.checkpoint.json'))
    assert cp['failure_counters'][:len(old_cp['failure_counters'])]==old_cp['failure_counters']
    assert result['next_original_failure_ordinal']==config['live_next']==cp['work_in_progress']['root_next_failure_ordinal_live']
    assert not Path(scope['output_root']).exists() and not Path(scope['caller_receipt_root']).exists()
    vector_ref=save('public22.v4.current-canonical-vector.actual.root.json',dict(
        issued_by=ROOT,refs=current,checkpoint_revision=371,path_ownership_revision=175,
        commands_revision=39,created_utc=now(),formal_acceptance=False))
    intent_ref=save('public22.v4.host-call-intent.actual.root.json',dict(issued_by=ROOT,
        case_request_ref=scope['case_request_ref'],scope_ref=facts['scope_ref'],
        kind='ACTUAL_HOST_CALL_INTENT',external_hostpair_required=True,created_utc=now()))
    request_ref=save('public22.v4.actual-request.root.json',dict(
        schema='researchos.root-public22-actual-request.v1',issued_by=ROOT,end_version=22,
        scope_ref=facts['scope_ref'],case_request_ref=scope['case_request_ref'],
        owner_ref=facts['owner_ref'],worker_ref=facts['worker_ref'],
        current_canonical_vector_ref=vector_ref,output_root=scope['output_root'],
        source_review_ref=scope['caller_review_ref'],runner_contract_ref=scope['runner_contract_ref'],
        registration_result_ref=result_ref,host_call_intent_ref=intent_ref))
    print(json.dumps(dict(actual_request_ref=request_ref,current_canonical_refs=current,
        scope_ref=facts['scope_ref'],case_request_ref=scope['case_request_ref'],
        output_root=scope['output_root'],caller_receipt_root=scope['caller_receipt_root'],
        next_original=config['live_next'],formal_delta=0),ensure_ascii=False),flush=True)
else:raise ValueError('ROOT_STAGE_MODE')
