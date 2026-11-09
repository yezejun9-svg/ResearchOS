"""Root continuation checkpoint; preserves Canon and captures original tool pairs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys, types

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
B = R / 'execution/v2.4/receipts/W05/W05-99'
W = R / 'execution/v2.4/receipts/W09/W09-99'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')

def pin(path):
    path = path.resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def exact(path, sha, size):
    value = pin(path)
    assert value['sha256'] == sha and value['bytes'] == size, 'EXACT_PIN_MISMATCH'
    return value

def save(name, value):
    with (N / name).open('xb') as file:
        file.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        file.flush(); os.fsync(file.fileno())
    return pin(N / name)

def outputs(value):
    if isinstance(value, list):
        for entry in value: yield from outputs(entry)
    elif isinstance(value, dict):
        if 'chunk_id' in value: yield value
        else:
            for entry in value.values(): yield from outputs(entry)
    elif isinstance(value, str):
        try: yield from outputs(json.loads(value))
        except ValueError: return

def capture(path, number, match, *, root=False):
    calls, found = {}, []
    with path.open('rb') as stream:
        header_raw = stream.readline(); header = json.loads(header_raw)
        if root: assert header['payload']['id'] == THREAD
        else:
            source = header['payload'].get('source', {})
            assert THREAD in json.dumps(source) and '/root/w09_formal_profile_source_impl' in json.dumps(source)
        # Original call and return are recent; a bounded tail avoids reading old trial inputs.
        stream.seek(0, 2); size = stream.tell(); start = max(len(header_raw), size - 24*1024*1024)
        stream.seek(start)
        if start > len(header_raw): stream.readline()
        while True:
            offset = stream.tell(); raw = stream.readline()
            if not raw: break
            event = json.loads(raw); payload = event.get('payload', {})
            if event.get('type') != 'response_item' or not isinstance(payload, dict): continue
            kind, callid = payload.get('type'), payload.get('call_id')
            if kind in ('custom_tool_call', 'function_call'):
                calls[callid] = (event, raw, offset)
            elif kind in ('custom_tool_call_output', 'function_call_output') and callid in calls:
                call = calls[callid]
                if match(call[0], event): found.append((call, event, raw, offset))
    if not found: return None
    assert len(found) == 1, 'UNIQUE_ORIGINAL_HOST_PAIR_REQUIRED'
    (call, call_raw, call_pos), result, result_raw, result_pos = found[0]
    raw_path = N / ('original%d.actual-host.raw.jsonl' % number)
    with raw_path.open('xb') as stream:
        stream.write(header_raw + call_raw + result_raw); stream.flush(); os.fsync(stream.fileno())
    raw_ref = pin(raw_path)
    binding_ref = save('original%d.actual-host.binding.root.json' % number, dict(
        schema='researchos.root-actual-tool-capture-binding.v1', issued_by='codex:/root',
        root_thread_id=THREAD, original_capture_ref=raw_ref, source_audit_path=str(path),
        source_prefix_size_observed=size, source_line_offsets=[0, call_pos, result_pos],
        source_line_bytes=[len(header_raw), len(call_raw), len(result_raw)],
        original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header_raw, call_raw, result_raw)],
        original_call_id=call['payload']['call_id'], tool_call_timestamp=call['timestamp'],
        tool_result_timestamp=result['timestamp'], formal_authority=False, parent_acceptance=False))
    with path.open('rb') as stream:
        for offset, raw in zip((0, call_pos, result_pos), (header_raw, call_raw, result_raw)):
            stream.seek(offset); assert stream.read(len(raw)) == raw
    return raw_ref, binding_ref

def root_chunk(call, result):
    return any(value.get('chunk_id') == '6a17ee' for value in outputs(result['payload'].get('output')))

def failed_collaboration(call, result):
    return ('agent thread limit reached' in json.dumps(result['payload'], ensure_ascii=False)
            and 'public22' in json.dumps(call['payload'], ensure_ascii=False))

root1010 = capture(AUDIT, 1010, root_chunk, root=True)
assert root1010 is not None
root1012 = capture(AUDIT, 1012, failed_collaboration, root=True)

def review_failure(call, result):
    return any(value.get('exit_code') == 1 and "KeyError: 'member_count'" in value.get('output', '')
               for value in outputs(result['payload'].get('output')))

review1019 = []
for day in ('06', '07', '08', '09'):
    folder = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10') / day
    if not folder.exists(): continue
    for path in folder.glob('*.jsonl'):
        with path.open('rb') as stream: header = json.loads(stream.readline())
        source = json.dumps(header.get('payload', {}).get('source', {}))
        if THREAD in source and '/root/w09_formal_profile_source_impl' in source:
            found = capture(path, 1009, review_failure)
            if found is not None: review1019.append(found)
assert len(review1019) <= 1

canonical = [exact(R/'execution/v2.4'/name, sha, size) for name, sha, size in (
    ('checkpoint.json', 'a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994',4489310),
    ('path_ownership.json','a612b51f23a5157aff5b99817caa09fb634a67c70879c56430daa4690d1da0bc',208629),
    ('step_state.json','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
    ('commands.json','28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968))]
identity = exact(R/'execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',420)
ci = W/'c19_two_actual_consumers_independent_review_codex/consumers-01a120dd'
ci_refs = [exact(ci/name,sha,size) for name,sha,size in (
    ('HDF.final.json','37610053cd076381ed7e52cd3a62aa7c1f759f2155bd4fec434a3d0b2130ef41',2614),
    ('MF.final.json','0cfb32b4daa60b9cc5dc601e848bbb5b7a012c1e90b9be7d07740778a47d785e',7255),
    ('actual-decision.final.json','dceefbb5cc2e7e8cb05604f40ef00f759cf326e938fa703569ddc804b701db46',8649))]
pub2 = B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v2'
pr2 = B/'public22_runner_independent_source_review_codex/pub22r-20261009-02'
pr_refs = [exact(pr2/name,sha,size) for name,sha,size in (
    ('HDF.json','e5f5611c4ebae96a3fc640fde86543e44b134812904736cf4021edfe60aadd31',3281),
    ('MF.json','61697145a07ce6bd4c5f69863b4bf94d68923cdcea8e232b34c2f0b4e0fc0d55',5401),
    ('source-decision.json','5c3a287ac4ca8b6f6c5e0b6836b24fa5ab4a544b3a1ff66c4f23294780aba5ce',4141))]
guard_ref=exact(B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py',
    'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
gm=types.ModuleType('root_continuation_source_guard');gm.__file__=guard_ref['path'];sys.modules[gm.__name__]=gm
exec(compile(Path(guard_ref['path']).read_bytes(),guard_ref['path'],'exec'),gm.__dict__)
rows = []
def row(ordinal, origin_ref, description, outer, python, kind, binding=None):
    rows.append(dict(ordinal=ordinal,origin_ref=origin_ref,origin_selector='$',description=description,
        capture_completeness=kind,capture_binding_ref=binding,actual_outer_exit=outer,actual_python_exit=python,
        actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
row(1005,exact(ci/'failure-a7cd3a.actual-host.raw.jsonl','91f01ee37e77834fe6543e4e8d6e74b3fd63d40b75b3a0c59484d1ccaf06088a',38305),
    'Independent component reviewer summary assumed stdout_ref; actual dispatcher uses stdout two-key. No consumer failure or rerun.',1,1,'ACTUAL_HOST_ORIGINAL_PAIR',
    exact(ci/'failure-a7cd3a.actual-host.binding.json','66e1aaf204716503f43e7328a6650c533dcd6896e1f3b64ae53c21c7c903731f',1099))
row(1006,exact(pub2/'original1006.fullhostpair.json','f58e2290fef32928333c3889d16e7585ce50715d8019e39a9e015d9fa96ac669',32506),
    'Source author guessed parent cwd AGENTS path. Successful later reads yielded outer0; no numeric child exit was observed.',0,None,'SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR')
row(1007,exact(pub2/'original-pending-3fb3a3.fullhostpair.json','b4c0433e34fface4ae7b56a881e17ffbed3d3acbff98f26a42e2aded9e997db2',3572),
    'Source archive adapter omitted custom_tool_call; ORIGINAL_HOSTPAIR_NOT_FOUND, repaired adapter for new capture.',1,1,'SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR')
trial = B/'original_provider_trial_reconciliation_readonly_codex/a9e17af6e5cd42fd997f2cb9c6510f32'
row(1008,exact(trial/'failure-origin.1008.json','62b2f89fcaf0a17aadc966dee21aa8dd4b7d2143b8ecb95ef3aa4335aea4a15d',3487),
    'Read-only adapter import reentered discovery; exclusive write rejected existing discovery. Existing file preserved; no paid request.',1,1,'SOURCE_REENCODED_FULL_ORIGINAL_HOST_PAIR')
row(1009,review1019[0][0] if review1019 else pin(pr2/'review-first-run-error.json'),
    'Independent Source reviewer MF assumed absent member_count. Source/product not executed; corrected independent script passed.',1,1,
    'ACTUAL_HOST_ORIGINAL_PAIR' if review1019 else 'SOURCE_RECORDED_PARTIAL_ORIGINAL_TOOL_IO',review1019[0][1] if review1019 else None)
row(1010,root1010[0],'Root guessed Source contract filename. Missing path exit outer1; Python/Native/dispatcher/model not invoked.',1,None,
    'ACTUAL_HOST_ORIGINAL_PAIR',root1010[1])
gap = W/'full_w09_native_gap_source_review_codex'
row(1011,exact(gap/'failure-ec18d2.actual-host.raw.jsonl','cec387cde27d103e414761fe27efefa18d249a248ba8fa7ff8bfe6b91fdd5b46',26617),
    'Independent gap-reader stdin JSON contained invalid escaped regex; rejected before Source guard acquisition. No product run.',1,1,
    'ACTUAL_HOST_ORIGINAL_PAIR',exact(gap/'failure-ec18d2.actual-host.binding.json','5d78e417a8fb069f8c637121556cca426a07d3713d4e5d94206e023c985cd0b0',1068))
if root1012:
    row(1012,root1012[0],'Root subtask dispatch rejected by active agent slot limit; no command process or product invocation.',None,None,
        'ACTUAL_HOST_ORIGINAL_PAIR',root1012[1])
else:
    reported=save('original1012.root-recorded-incomplete.json',dict(schema='researchos.root-recorded-tool-error.v1',
        operation='collaboration.followup_task',target='/root/w09_formal_profile_source_impl',
        description='Source-only public22 Root caller registration task dispatch',
        observed_tool_error='collab tool failed: agent thread limit reached',
        original_full_host_pair_captured=False,actual_outer_exit=None,actual_python_exit=None,
        actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
    row(1012,reported,'Root subtask dispatch rejected by active agent slot limit; incomplete host capture explicitly retained.',None,None,
        'ROOT_RECORDED_PARTIAL_ORIGINAL_TOOL_IO')
refs=[*canonical,identity,*ci_refs,*pr_refs,guard_ref]
for entry in rows:
    refs.append(entry['origin_ref'])
    if entry['capture_binding_ref']:refs.append(entry['capture_binding_ref'])
guard=gm.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=128*1024*1024)
try:
    guard.acquire(refs)
    cp=json.loads(guard.get_buffer(canonical[0]['path']))
    ow=json.loads(guard.get_buffer(canonical[1]['path']))
    decision=json.loads(guard.get_buffer(ci_refs[2]['path']))
    pd=json.loads(guard.get_buffer(pr_refs[2]['path']))
    assert cp['revision']==370 and ow['revision']==174
    assert decision['decision']=='ACTUAL_MAIN_C19_TWO_CONSUMERS_COMPONENT_FIXTURE_VERIFIED'
    assert pd['decision']=='ACCEPTED_SOURCE_ONLY'
    assert [x['ordinal'] for x in rows]==list(range(1005,1013))
finally:
    closed=guard.close()
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
guard_closed=save('continuation-source-guard.live1013.closed.root.json',closed)
pending_ref=save('pending-diagnostics.cp370.live1013.root.json',dict(
    schema='researchos.root-diagnostic-pending.v2',issued_by='codex:/root',
    source_cutoff=dict(highest_ordinal=1004,next_failure_ordinal=1005),
    next_original_failure_ordinal=1013,pending=rows,counter_reset=False,
    registered_in_current_canon=False,unknown_exits_are_null=True))
resume=save('RESUME.cp370-consumers-qualified.live1013.root.json',dict(
    schema='researchos.root-resume.v2',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),
    identity_ref=identity,canonical_refs=canonical,checkpoint_revision=370,ownership_revision=174,commands_revision=39,
    prior_resume_ref=pin(N/'RESUME.cp370-consumers-request-ready.live1005.root.json'),
    registered_failure_count=1002,highest_registered_ordinal=1004,next_original_failure_ordinal_live=1013,
    pending_diagnostics_ref=pending_ref,source_guard_closed_ref=guard_closed,
    active_construction_parents=['W05','W09'],historical_parent_records=6,current_formal_accepted=0,
    required_parents=22,required_formal=42,formal_acceptance=False,parent_acceptance=False,counter_reset=False,
    C19_actual_consumers_status=decision['decision'],C19_actual_independent_review_refs=ci_refs,
    C19_actual_original_tool_io_ref=pin(N/'Main-C19-two-dispatchers.actual.original-tool-io.root.json'),
    C19_actual_output_dir=str(N/'actual-consumers/run-4ec941672d72422ea05c2500a89a9336'),
    C19_successful_Native_and_consumers_must_not_rerun=True,
    W05_public22_runner_status='INDEPENDENT_SOURCE_ACCEPTED_NOT_REGISTERED_NOT_EXECUTED',
    W05_public22_runner_independent_review_refs=pr_refs,
    W05_current_Main23_programme_status='FRESH_CURRENT_MAIN_BUILDER_SOURCE_IN_PROGRESS',
    W05_schema21='OPEN_NO_PROGRAMME_BOUND',W05_full20to24='OPEN',W05_main23to24='BLOCKED_MAIN_NOT_ADOPTED',
    W09_full_G01_G02_A06_Native_and_formal_capture_index='OPEN',
    next_actions=['Prepare and independently review fresh Main23 programme builder and bounded public22 Root caller/registration.',
        'Review full W09 Native routes and formal consumer path compatibility; preserve qualified C19.',
        'Continue original paid trial reconciliation without new paid request while billing/server termination remain unknown.'],
    whole_goal_status='ACTIVE',Canon_written=False))
assert [pin(Path(x['path'])) for x in canonical]==canonical
print(json.dumps(dict(resume_ref=resume,pending_diagnostics_ref=pending_ref,source_guard_closed_ref=guard_closed,
    next_original=1013,rows=len(rows),Root_original1009_full_capture=bool(review1019),
    Root_original1012_full_capture=bool(root1012),Canon_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
