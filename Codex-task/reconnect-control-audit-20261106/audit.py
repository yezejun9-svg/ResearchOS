import ctypes
from ctypes import wintypes as w
from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

C = Path(__file__).resolve().parent.parent
O = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
K = ctypes.WinDLL('kernel32', use_last_error=True)
K.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
K.OpenProcess.restype = w.HANDLE
K.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
K.GetProcessTimes.restype = w.BOOL
K.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
K.GetExitCodeProcess.restype = w.BOOL
K.CloseHandle.argtypes = [w.HANDLE]
K.CloseHandle.restype = w.BOOL
seen = {}
def sha(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    seen[str(p)] = h
    return h
def read(p):
    sha(p)
    return json.loads(p.read_bytes())
def inspect(pid, expected):
    v = dict(pid=pid, expected_creation_filetime=str(expected), query_access='PROCESS_QUERY_LIMITED_INFORMATION/0x1000', observed_at=datetime.now(timezone.utc).isoformat())
    h = K.OpenProcess(0x1000, False, pid)
    if not h:
        error = ctypes.get_last_error()
        v.update(open_error=error, identity_state='PID_NOT_PRESENT' if error == 87 else 'QUERY_UNCERTAIN')
        return v
    try:
        created, exited, kernel, user = (w.FILETIME() for _ in range(4))
        code = w.DWORD()
        times_ok = K.GetProcessTimes(h, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user))
        times_error = 0 if times_ok else ctypes.get_last_error()
        exit_ok = K.GetExitCodeProcess(h, ctypes.byref(code))
        exit_error = 0 if exit_ok else ctypes.get_last_error()
        if not times_ok or not exit_ok:
            v.update(identity_state='QUERY_UNCERTAIN', times_error=times_error, exit_error=exit_error)
        else:
            observed = (created.dwHighDateTime << 32) | created.dwLowDateTime
            exit_time = (exited.dwHighDateTime << 32) | exited.dwLowDateTime
            match = observed == int(expected)
            v.update(observed_creation_filetime=str(observed), creation_matches=match, exit_code=code.value, exit_filetime=str(exit_time))
            v['identity_state'] = 'PID_REUSED_NOT_ORIGINAL' if not match else ('ORIGINAL_EXITED' if exit_time != 0 else ('ORIGINAL_STILL_ACTIVE' if code.value == 259 else 'ORIGINAL_EXITED'))
    finally:
        v['query_handle_closed'] = bool(K.CloseHandle(h))
    return v

jobs = []
for name in ['product-v1-native-synthetic-flow-01', 'product-v1-workbench-refinement-tests-03', 'product-v1-workbench-refinement-vite-01', 'product-v1-visual12-purechecks-01']:
    p = C / 'product-v1-owned-verification-20261104/runs' / name / 'RESULT.json'
    j = read(p)
    assert j['job_active_zero'] and j['stop_proved'] and j['root_signaled']
    assert j['close_order'] == ['job', 'thread', 'process'] and not j['errors']
    for raw in j['raw']:
        assert sha(p.parent / raw['file']) == raw['sha256']
    jobs.append(dict(scope_id=name, receipt_sha256=sha(p), historical_status=j['status'], historical_exit_code=j['root_exit_code'], historical_job_total_processes=j['job_total_processes'], historical_job_active_zero=True, historical_stop_proved=True, historical_handles_closed=True, current_root=inspect(j['root_pid'], j['creation_filetime'])))

corepath = C / 'product-v1-native-synthetic-acceptance-中文-run-01/receipts/owned-core.json'
core = read(corepath)['owned_core_identity']
assert int(core['created_ns']) % 100 == 0
core_creation = int(core['created_ns']) // 100 + 116444736000000000
core_observation = inspect(core['pid'], core_creation)
core_observation['receipt_created_ns'] = core['created_ns']
core_observation['conversion'] = 'Unix nanoseconds / 100 + 116444736000000000; exact integer conversion'
core_observation['scope'] = 'Public owned-core receipt only; no DB, image, command line, token or environment read'
cp = read(R / 'execution/v2.4/checkpoint.json')
state = read(R / 'execution/product-v1/state.json')
leases = read(R / 'execution/product-v1/leases.json')
resume = read(R / 'execution/product-v1/receipts/single-harness-20261104/progress-cp693/RESUME.json')
pins = {k:v for row in state['integrated_source'] for k,v in row['source_sha256'].items()}
union = hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert cp['revision'] == 693 and cp['current_Main_HEAD'] == '360c3eefd06ba82255352357c05ece00dae00d3a'
assert len(pins) == 70 and union == '954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2'
for p,h in pins.items():
    assert sha(R / p) == h, p
plan = read(C / 'product-v1-workbench-refinement-integration-plan.json')
for p,h in plan['protected_sha256'].items():
    assert (sha(R / p) if (R / p).is_file() else 'ABSENT_BEFORE') == h, p
assert leases['revision'] == 33 and state['active_scopes'] == leases['source_owners']
assert not [r for r in leases['source_owners'] if r['status'] == 'IMPLEMENTING']
assert len(cp['failure_counters']) == 2648
assert resume['root_running_long_commands'] == [] and resume['active_source_owners'] == []
paths = [R / '.local/worktrees/product-v1-build-14-20261105', R / 'execution/product-v1/receipts/single-harness-20261104/build14-scope', C / 'product-v1-owned-verification-20261104/scopes/product-v1-build-14.json', C / 'product-v1-owned-verification-20261104/runs/product-v1-build-14']
absent = [{'path': str(p), 'absent': not p.exists()} for p in paths]
blockers = [j['scope_id'] for j in jobs if j['current_root']['identity_state'] in ('QUERY_UNCERTAIN', 'ORIGINAL_STILL_ACTIVE')]
if core_observation['identity_state'] in ('QUERY_UNCERTAIN', 'ORIGINAL_STILL_ACTIVE'):
    blockers.append('original-owned-core')
if not all(v['absent'] for v in absent):
    blockers.append('build14-path-present')
result = dict(schema='researchos.reconnect-control-audit/1', at=datetime.now(timezone.utc).isoformat(), decision='READONLY_RECONNECT_CHECKS_CLEAR' if not blockers else 'BLOCKED_OR_UNCERTAIN', blockers=blockers, checkpoint=693, checkpoint_recorded_head=cp['current_Main_HEAD'], live_git='NOT_QUERIED_BY_THIS_REVIEWER_PARENT_CHECKS_SEPARATELY', source_count=70, source_union_sha256=union, protected_count=len(plan['protected_sha256']), lease_revision=33, active_implementing=0, historical_records=2648, jobs=jobs, owned_core=core_observation, build14_paths=absent, pending_or_uncertain_mutation_in_selected_saved_control_scope=False if not blockers else 'NOT_CLEARED', current_job_handles='NONE; historical handle values never opened or reused', limitations=['No whole-machine inventory or current Job membership claimed.', 'Historical stop proof is retained receipt evidence; current ROOT checks use only exact PID plus creation FILETIME.', 'Resource readiness and Git index are independently checked by parent.', 'No product acceptance, build, tests, GUI, native task or model execution in this audit.'], actions=dict(D_writes=0, process_termination=0, OS_setting_changes=0, product_execution=0, model_calls=0, new_C_audit_files_only=True), evidence_sha256=seen)
with (O / 'READBACK.json').open('x', encoding='utf8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k != 'evidence_sha256'}, ensure_ascii=False, indent=2))
