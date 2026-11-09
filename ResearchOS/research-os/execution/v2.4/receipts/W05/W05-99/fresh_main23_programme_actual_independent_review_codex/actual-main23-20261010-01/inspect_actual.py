"""Read exact actual durable records and publish bounded metadata only."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
C=B/'integration_codex/fresh-main23-caller-3ef8ee61a94e4adca86a00f55a8b7a13'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(path):
 p=Path(path);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(path,digest,size):
 r=pin(path);assert r['sha256']==digest and r['bytes']==size
 return r,json.loads(Path(path).read_bytes())
rr,record=checked(C/'caller-return.root.json','809d7c96852cf6a53a5ffef2ea4b3f6f7186090ce9d71e57b2259c6dcf2f705f',11809063)
sr,state=checked(C/'builder-returned-state.root.json','f627d47e08ab0f0e57a96e1ad3291c92a12b6dbb9cd6074844880331e7ac1361',6510571)
ar,actual=checked(D/'main23.v4.actual-request.root.json','13af70f5c03e23c9fd5b0afdabc48d5844308e9b05a309fe5754f06a3e7b5dca',2965)
vr,vector=checked(D/'main23.v4.activation-after.current4.actual.root.json','f7cb3bd5a29eefb9eafb0e253caa705d5f0de173cf7b080c1df7e3496aecba23',3716)
assert record['builder_returned_state']==state
closed_ref=state['closed_receipt']['ref'];assert pin(closed_ref['path'])==closed_ref
closed=json.loads(Path(closed_ref['path']).read_bytes())
result=dict(status='ACTUAL_METADATA_READ_ONLY_NOT_QUALIFICATION',caller_return_ref=rr,builder_state_ref=sr,actual_request_ref=ar,activation_vector_ref=vr,caller_keys=list(record),builder_keys=list(state),actual_request=actual,activation_vector=vector,caller_error=record['caller_error'],first_failure=state['first_failure'],builder_status=state['status'],Root_failure_assignment_required=record['Root_failure_assignment_required'],durable_state_matches_caller_embedded_state=True,build_closed_ref=closed_ref,build_closed_only_changed_keys=[k for k in set(closed)|set(state) if closed.get(k)!=state.get(k)],candidate=state.get('candidate_for_independent_review'),phase_calls=[dict(phase=x['phase'],actual_exit=x['actual_exit'],owned_child_pid=x['observation']['owned_child_pid'],creation_time_100ns=x['observation']['creation_time_100ns'],PID_type=type(x['observation']['owned_child_pid']).__name__,FILETIME_type=type(x['observation']['creation_time_100ns']).__name__,observation_keys=list(x['observation']),job_cleanup=x['observation'].get('job_cleanup'),before_ref=x['before_ref'],result_ref=x['result_ref'],stdout_ref=x['stdout_ref'],stderr_ref=x['stderr_ref']) for x in state['calls']],builder_guard_summaries={k:{key:g.get(key) for key in ('verification','closed','retained_handles_count','errors')} for k,g in state['guard_cleanup'].items()},caller_guard_summary={key:record['source_guard_cleanup'].get(key) for key in ('verification','closed','retained_handles_count','errors')},Root_outer_API_stdout='TRUNCATED_AS_REPORTED_AWAITING_ORIGINAL_CAPTURE',reconstruction_of_original_stdout=False,formal_acceptance=False,programme_qualification=None)
p=N/'actual-metadata-observation.json'
with p.open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(metadata_ref=pin(p),builder_status=state['status'],caller_error=record['caller_error'],first_failure=state['first_failure'],candidate=state.get('candidate_for_independent_review'),build_closed_ref=closed_ref,build_closed_only_changed_keys=result['build_closed_only_changed_keys'],caller_keys=list(record),builder_keys=list(state),actual_request=actual,phases=[dict(phase=x['phase'],exit=x['actual_exit'],pid=x['owned_child_pid'],filetime=x['creation_time_100ns']) for x in result['phase_calls']],guards=result['builder_guard_summaries'],caller_guard=result['caller_guard_summary'],formal_acceptance=False),ensure_ascii=False),flush=True)
