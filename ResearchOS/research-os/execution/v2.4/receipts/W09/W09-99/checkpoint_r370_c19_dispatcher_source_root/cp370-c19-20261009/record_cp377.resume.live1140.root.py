"""Durable Root continuation with truthful registered and later diagnostic cutoffs."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, re

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def pin(p):
    p=Path(p);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value,raw=False):
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    return pin(N/name)
source=N/'seal_native_original_root_hosts.cp376.root.py'
tree=ast.parse(source.read_bytes());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='documents')
namespace={'json':json};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
documents=namespace['documents']
calls={};found=[]
with AUDIT.open('rb') as f:
    header=f.readline();assert json.loads(header)['payload']['id']==THREAD
    f.seek(0,2);prefix=f.tell();f.seek(max(len(header),prefix-32*1024*1024))
    if f.tell()>len(header):f.readline()
    while f.tell()<prefix:
        off=f.tell();raw=f.readline();event=json.loads(raw);p=event.get('payload',{})
        if event.get('type')!='response_item' or not isinstance(p,dict):continue
        if p.get('type') in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(off,raw)
        elif p.get('type') in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls:
            hits=[x for x in documents(p.get('output')) if x.get('chunk_id')=='cd338a']
            if hits:
                assert len(hits)==1;found.append((calls[p['call_id']],(off,raw),hits[0]))
assert len(found)==1
(co,call),(ro,ret),obs=found[0];lines=[header,call,ret];offsets=[0,co,ro]
assert obs['exit_code']==2 and re.findall(r'(?m)^ROOT_SOURCE_PYTHON_EXIT=(-?\d+)\s*$',obs['output'])==['2']
with AUDIT.open('rb') as f:
    for offset,line in zip(offsets,lines):f.seek(offset);assert f.readline()==line
raw_ref=save('original1136.actual-host.raw.jsonl',b''.join(lines),True)
binding_ref=save('original1136.actual-host.binding.json',dict(
    schema='researchos.root-native-original-host-binding.v1',actor_id='codex:/root',
    Root_thread_id=THREAD,original_failure_ordinal=1136,original_chunk_id='cd338a',
    source_audit_path=str(AUDIT),source_prefix_size_observed=prefix,source_line_offsets=offsets,
    original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],original_capture_ref=raw_ref,
    actual_outer_exit=2,actual_python_exit=2,actual_native_exit=None,actual_Go_exit=None,
    actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
    automatic_retry=False,counter_reset=False,
    diagnosis='Root guessed repository tools/task_packet.py. Actual tool is in the requested implementation package; interpreter exit2 preserved.'))
prior_ref=pin(N/'RESUME.cp376-w09-all-closed.live1134.root.json')
prior=json.loads(Path(prior_ref['path']).read_bytes())
current=[pin(R/'execution/v2.4'/x) for x in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
assert current[0]['sha256']=='03f7fec737ca5e740762f934a9c74b3b80e987fde6c8b82e16c92bba30f74090'
assert current[1]['sha256']=='c55ae46b147b89bed48718dbc60c646c68a6198aac7596460bfe1d440d015698'
cp=json.loads(Path(current[0]['path']).read_bytes());ow=json.loads(Path(current[1]['path']).read_bytes())
assert cp['revision']==377 and ow['revision']==181
assert cp['work_in_progress']['root_next_failure_ordinal_live']==1134
assert len(cp['failure_counters'])==1131 and cp['failure_counters'][-1]['original_payload']['observed_ordinal']==1133
closure_ref=pin(N/'cp377-native-closure-live1135/canonical-closure.committed.json')
resume_ref=save('RESUME.cp377-current-source-required.live1140.root.json',dict(prior,
    created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=prior_ref,
    canonical_refs=current,canonical_checkpoint_revision=377,canonical_ownership_revision=181,
    registered_through_original_ordinal=1133,next_registered_original_ordinal=1134,
    next_original_failure_ordinal=1140,pending_original_ordinals=list(range(1134,1140)),
    pending_capture_delivery_required=[1134,1137,1138,1139],
    Root_original1136_ref=raw_ref,Root_original1136_binding_ref=binding_ref,
    canonical_closure_ref=closure_ref,
    actual_closure_original_capture_ref=pin(N/'w09.cp377-native-closure.actual-audit.root.json'),
    W09='MAIN_FIXTURE_ADOPTED_OLD_NATIVE_CLOSED_CURRENT_SOURCE4_NATIVE_AND6_CONSUMERS_REQUIRED',
    Main_fixture_adopted=True,Main_fixture_adoption_ref=pin(N/'legacy-fixture-Main-adoption-20261010-01/adoption.closed.json'),
    Main_fixture_actual_ref=pin(R/'internal/domain/retrieval_test.go'),
    three_old_native_registrations_closed=True,Source21_after_adoption_requires_new_evidence=True,
    old_C19_consumers_are_historical_after_source_change=True,
    Source_bridge02_handoff_ref=pin(W/'w09_formal_root_bridge_source_codex/bridge-20261010-02/HDF.json'),
    Source_bridge02_status='TASK95_SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_NOT_EXECUTABLE',
    Source_NF4_and_new_generation_scope_caller='TASK97_SOURCE_ONLY_IN_PROGRESS',
    public21_caller_status='TASK91_58_SOURCE_CONTROLS_PASSED_SEAL_IN_PROGRESS',
    required_current_Native_selectors=['W09-G01','W09-G02','C19','A06'],
    fresh_CM40_consumer_route_count=6,
    task_packet_actual=dict(chunk='4614af',actual_outer_exit=0,actual_python_exit=0,
       package_tool_path=r'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\tools\task_packet.py',
       plan_path=r'D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\contracts\execution.plan.json',
       card='W09-99',eligible=True,state_source='VALIDATED_FILE',product_acceptance='NOT_ASSERTED'),
    next_actions=['Finish independent qualification of new current Native Source and new-generation Scope Caller.',
      'Run each newly scoped Native once with fresh C scratch; do not replay consumed historical scopes.',
      'Independently review Source bridge02 and then execute six real CM40 consumers under an actual Root formal assembly scope.',
      'Qualify the public21 Source caller and execute only a new PUBLIC21_BOOTSTRAP_ONLY component scope.',
      'Capture true formal reviewer delivery, use real Main verify_owner and current state derive before accepting cases.']))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes()
save('historical.HANDOFF.before-cp377.live1140.root.md',old,True)
prefix=('# Current Root continuation: CP377 / OW181 / CM40 / live next1140\n\n'
 'Main legacy fixture correction adopted with independent Source review and exclusive byte verification. Three historical Native registrations closed. Diagnostics1117..1133 registered once;1134..1139 pending. Current Source requires four new Native selectors and six CM40 consumer receipts. Formal0/42; Goal ACTIVE; no reset. W05 public21 Caller Source58 controls passed; seal/qualification pending.\n\n'
 'Current resume: '+resume_ref['path']+'\nSHA256 '+resume_ref['sha256']+' bytes '+str(resume_ref['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old) and all(pin(x['path'])==x for x in current)
print(json.dumps(dict(resume_ref=resume_ref,original1136_raw_ref=raw_ref,
    original1136_binding_ref=binding_ref,canonical_unchanged=True,
    registered_through=1133,live_next=1140,formal_acceptance=False),ensure_ascii=False))
