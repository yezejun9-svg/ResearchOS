"""Persist exact Root audit pairs, current Canon archives and stopped runtime.

The host tool returned truncated console text; complete caller observations
already exist on disk and are bound separately. No old artifact is changed.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
definitions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('pin','save','outputs')],type_ignores=[])
exec(compile(definitions,'root_capture_common_definitions','exec'),globals())
chunks={'build':'ade816','check':'3829be','activate':'06bdfb','actual':'f2e3c6'}
found={};calls={}
with AUDIT.open('rb') as stream:
    header_raw=stream.readline();assert json.loads(header_raw)['payload']['id']==THREAD
    stream.seek(0,2);size=stream.tell();start=max(len(header_raw),size-24*1024*1024)
    stream.seek(start)
    if start>len(header_raw):stream.readline()
    while True:
        offset=stream.tell();raw=stream.readline()
        if not raw:break
        event=json.loads(raw);payload=event.get('payload',{})
        if event.get('type')!='response_item' or not isinstance(payload,dict):continue
        kind=payload.get('type');callid=payload.get('call_id')
        if kind in ('function_call','custom_tool_call'):calls[callid]=(event,raw,offset)
        elif kind in ('function_call_output','custom_tool_call_output') and callid in calls:
            returned=list(outputs(payload.get('output')))
            for phase,chunk in chunks.items():
                matches=[v for v in returned if v.get('chunk_id')==chunk]
                if matches:
                    assert phase not in found and len(matches)==1
                    found[phase]=(calls[callid],event,raw,offset,matches[0])
assert set(found)==set(chunks)
captures={}
for phase,((call,callraw,callpos),returned,resultraw,resultpos,toolresult) in found.items():
    rawpath=N/('public22.v4.'+phase+'.actual-host.raw.jsonl')
    with rawpath.open('xb') as f:f.write(header_raw+callraw+resultraw);f.flush();os.fsync(f.fileno())
    rawref=pin(rawpath)
    bindingref=save('public22.v4.'+phase+'.actual-host.binding.root.json',dict(
        schema='researchos.root-actual-tool-capture-binding.v1',issued_by='codex:/root',
        original_capture_ref=rawref,original_call_id=call['payload']['call_id'],
        source_audit_path=str(AUDIT),source_prefix_size_observed=size,
        source_line_offsets=[0,callpos,resultpos],source_line_bytes=[len(header_raw),len(callraw),len(resultraw)],
        original_line_sha256=[hashlib.sha256(v).hexdigest() for v in (header_raw,callraw,resultraw)],
        chunk_id=chunks[phase],tool_call_timestamp=call['timestamp'],tool_result_timestamp=returned['timestamp'],
        full_returned_tool_io_preserved=True,console_output_complete=phase!='actual',formal_acceptance=False))
    with AUDIT.open('rb') as f:
        for offset,value in zip((0,callpos,resultpos),(header_raw,callraw,resultraw)):
            f.seek(offset);assert f.read(len(value))==value
    captures[phase]=dict(original_capture_ref=rawref,capture_binding_ref=bindingref,
        actual_outer_exit=toolresult['exit_code'],actual_python_exit=0,
        console_output_complete=phase!='actual')
assert all(c['actual_outer_exit']==0 for c in captures.values())
canonical=[];archives=[]
for name in ('checkpoint','path_ownership','step_state','commands'):
    p=R/'execution/v2.4'/(name+'.json');ref=pin(p);canonical.append(ref)
    with (N/('historical.cp371.'+name+'.json')).open('xb') as f:
        f.write(p.read_bytes());f.flush();os.fsync(f.fileno())
    archive=pin(N/('historical.cp371.'+name+'.json'))
    assert (archive['sha256'],archive['bytes'])==(ref['sha256'],ref['bytes']);archives.append(archive)
cp=json.loads(Path(canonical[0]['path']).read_bytes());ow=json.loads(Path(canonical[1]['path']).read_bytes())
assert cp['revision']==371 and ow['revision']==175 and cp['work_in_progress']['root_next_failure_ordinal_live']==1024
prior=json.loads((N/'RESUME.cp370-public22-v4-activate.live1024.root.json').read_bytes())
assert canonical[2:]==prior['canonical_refs'][2:]
B=R/'execution/v2.4/receipts/W05/W05-99/integration_codex'
case=B/'schema22-public-89c0459006654891bf3c540af6b525aa'
caller=B/'schema22-public-caller-89c0459006654891bf3c540af6b525aa'
caller_ref=pin(caller/'caller-return.root.json');caller_record=json.loads(Path(caller_ref['path']).read_bytes())
state_ref=pin(caller/'runner-returned-state.root.json');state=json.loads(Path(state_ref['path']).read_bytes())
assert state['status']=='STOPPED_AT_FIRST_FAILURE' and state['first_failure']['message']=='PUBLIC_RESTORE_SCHEMA_MISMATCH'
assert state['phase']=='verify22' and caller_record['caller_error'] is None
assert len(state['calls'])==4 and all(c['actual_exit']==0 for c in state['calls'])
assert all(c['observation']['job_cleanup']['job_idle_confirmed'] and
    c['observation']['job_cleanup']['handles_closed'] and c['observation']['job_cleanup']['errors']==[]
    for c in state['calls'])
cleanup=caller_record['source_guard_cleanup']
assert cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[]
failure_ref=save('public22.v4.original1025.assignment.root.json',dict(
    schema='researchos.root-original-failure-assignment.v1',issued_by='codex:/root',ordinal=1025,
    original_capture_ref=captures['actual']['original_capture_ref'],
    capture_binding_ref=captures['actual']['capture_binding_ref'],origin_selector='$',
    caller_record_ref=caller_ref,returned_state_ref=state_ref,first_failure=state['first_failure'],
    actual_outer_exit=0,actual_python_exit=0,actual_native_exit=0,
    actual_dispatcher_exit=None,actual_model_exit=None,actual_SQLite_exit=None,
    successful_native_children=len(state['calls']),Root_assignment_only=True,
    old_artifacts_changed=False,automatic_retry=False,counter_reset=False,formal_acceptance=False))
resume=prior
resume.update(schema='researchos.root-resume.v2',created_utc=datetime.now(timezone.utc).isoformat(),
    prior_resume_ref=pin(N/'RESUME.cp370-public22-v4-activate.live1024.root.json'),
    canonical_refs=canonical,canonical_archive_refs=archives,checkpoint_revision=371,ownership_revision=175,
    registered_failure_count=len(cp['failure_counters']),highest_registered_ordinal=1023,
    next_original_failure_ordinal_live=1026,
    pending_diagnostics_ref=None,pending_diagnostic_originals=[1024,1025],
    prior_pending_diagnostics_registered=True,
    public22_actual_original_refs=captures,
    public22_caller_record_ref=caller_ref,public22_returned_state_ref=state_ref,
    public22_first_failure_assignment_ref=failure_ref,
    public22_closed_receipt_ref=pin(case/'case.closed.json'),
    public22_baseline_manifest_ref=pin(case/'baseline22.manifest.json'),
    W05_public22_root_caller_status='ACTUAL_FOUR_CHILDREN_ZERO_VERIFY22_SCHEMA_MISMATCH_PENDING_INDEPENDENT_REVIEW',
    W05_current_Main23_root_caller_status='SOURCE_CHANGES_REQUIRED_TWO_NONAUTHOR_REVIEW_BLOCKERS_NEW_V2_REPAIR_IN_PROGRESS',
    W09_profile_registry_compat_status='INDEPENDENT_SOURCE_ACCEPTED_V5_CM40_NOT_ADOPTED',
    current_formal_accepted=0,formal_acceptance=False,parent_acceptance=False,counter_reset=False,
    whole_goal_status='ACTIVE',Canon_written=False)
resume_ref=save('RESUME.cp371-public22-stopped.live1026.root.json',resume)
summary_ref=save('public22.v4.actual.closed-summary.root.json',dict(
    issued_by='codex:/root',captures=captures,canonical_refs=canonical,archive_refs=archives,
    resume_ref=resume_ref,original_assignment_ref=failure_ref,caller_record_ref=caller_ref,
    returned_state_ref=state_ref,closed_receipt_ref=pin(case/'case.closed.json'),
    status=state['status'],first_failure=state['first_failure'],actual_native_child_exits=[0,0,0,0],
    native_child_creation_time_100ns_decimal=[str(c['observation']['creation_time_100ns']) for c in state['calls']],
    caller_guard_closed=True,baseline_retained=state['baseline_retained'],formal_acceptance=False))
assert [pin(Path(r['path'])) for r in canonical]==canonical
print(json.dumps(dict(resume_ref=resume_ref,summary_ref=summary_ref,original_assignment_ref=failure_ref,
    actual_host_capture=captures['actual'],canonical_refs=canonical,archive_refs=archives,
    registered_failure_count=len(cp['failure_counters']),pending_originals=[1024,1025],
    next_original=1026,formal_acceptance=False),ensure_ascii=False),flush=True)
