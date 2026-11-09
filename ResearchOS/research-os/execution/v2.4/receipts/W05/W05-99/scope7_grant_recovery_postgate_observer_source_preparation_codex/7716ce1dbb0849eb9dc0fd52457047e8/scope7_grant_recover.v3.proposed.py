"""One-use Scope7 metadata recovery. Never rerun the original grant phase.

SOURCE PROPOSAL ONLY. Root must adopt this exact file after nonauthor review.
This program verifies preexisting facts, calls the pinned read-only grant gate,
then exclusively writes the three missing terminal metadata files.
"""
from __future__ import annotations

import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import types
from ctypes import wintypes

ROOT = Path('D:/作品集/ResearchOS/research-os')
UID = '9eccde97a9fa4815941768cacaf590dc'
REG = ROOT / ('execution/v2.4/receipts/W05/W05-99/integration_codex/'
              'desktop58-finite169-go3-r339-' + UID)
PF = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
             'desktop58_finite_grant_preflight_codex/' + UID)
AUTH = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
               'desktop58_finite_authorization_codex/' + UID)
SOURCE = Path(__file__).absolute()
GATE = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
               'desktop58_cli2_fact_abi_revision_preparation_codex/'
               'ddc11e9721a6490baf1f0032c6bf6d16/'
               'authorization_adapter.v4.cli2_fact.proposed.py')
GATE_PIN = ('2db48d991390dc7706aad553cdc5530d005e90273f6e3eec1231c14dc4c067be', 60679)
PIPELINE = GATE.parent / 'metadata_pipeline.desktop58.bound.v4.proposed.py'
PIPELINE_PIN = ('c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755', 38316)
SCOPE = REG / 'scope_registration.json'
SCOPE_PIN = ('c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859', 25595)
GRANT = AUTH / 'authorization.execute.json'
GRANT_PIN = ('6b0ef299508d98c8f1dca47e3d01116ceae98aca7914d318f3ed6d13bc3f6c10', 33548)
REG_MANIFEST_PIN = ('b76fba76e3134321a19b90ce2a6b50bf31d89dfd106f9b6c0e1704baec01875c', 34164)
GRANT_STARTED_PIN = ('7a31f2fde04692c359d78fc2bfc3945d1159e62d66f8eacd634775439050a51e', 409)
DIAGNOSTIC = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                     'desktop58_grant_resume_diagnostic_codex/' + UID +
                     '/failures658-660-and-current-state.original.json')
DIAGNOSTIC_PIN = ('233cfd48e5ff6aef7cf69b0e6c6633c16ef34b64976486f3fefca1904406ae36', 11192)
BOUNDARY_REVIEW = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                          'desktop58_grant_recovery_independent_review_codex/'
                          '96fdce9d0e3043c0a5d6aa82808749ad/'
                          'boundary-review.json')
BOUNDARY_REVIEW_PIN = ('a54265b97224dda0b4457fe264fc76377862990dbb4b1e652bb7717dd4252dee', 3335)
DISK_ASSESSMENT = BOUNDARY_REVIEW.parent / 'disk-assessment.json'
DISK_ASSESSMENT_PIN = ('82d667aab0593d2a35ceadddacfd0985790ba821425d4834eed36d2883fd3a9f', 178184)
V2_ORIGIN = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
                    'scope7_grant_recovery_root_inputs_codex/' + UID +
                    '-r339-666/failure-origin.667.recovery-once.original.json')
V2_ORIGIN_PIN = ('b74416e6855e77a093757b58900117e7248ec9fbb3352bf73a98775d0e18752a', 4267)
V2_ATTEMPT = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
                     'scope7_grant_recovery_execution_codex/' + UID +
                     '-recovery-v2-once/attempt.started.json')
V2_ATTEMPT_PIN = ('8724a34af64b516f47ca4551bf7f3ce2e519b70dce64f8764527314cf0b3dc21', 880)
V2_SOURCE = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
                    'scope7_grant_recovery_source_preparation_codex/'
                    '8821517157754457be7645afa51c5177/'
                    'scope7_grant_recover.v2.proposed.py')
V2_SOURCE_PIN = ('1004e4d42ac9a32e79e7188e3a91070d7fe7b0fbb3dfdc4481743199310ca7ea', 23698)
POWERSHELL = Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
POWERSHELL_PIN = ('8bb6fa8c283b4d92120b1ef249a9b311b0f804d4cabbe9981159976c8be76a5e', 495616)
OBSERVER_TIMEOUT_SECONDS = 20
OWNED_HELPER = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                       'desktop_go3_os_capture_revision_codex/'
                       '01fc890602df43b89935fdbef4424137/'
                       'windows_debug_owned_process.v2.py')
OWNED_HELPER_PIN = ('b60c8826fb13fc24947965579492b6f4aad76d7d95588fdfe2525daa1941f725', 30109)
CANON = {
    'checkpoint.json': '4ed88a919cecc93d544c3b7a88745f45bcbc5b43156517d3ccccc6aa3cdc258b',
    'path_ownership.json': '8d954eff78630ff678ac9d1abbc5a88cadca60285a4d16a32f857ac2f12d37d3',
    'step_state.json': 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',
    'commands.json': 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',
}
READS: dict[Path, bytes] = {}


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def path(value: str | Path, existing: bool = True) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = ROOT / p
    need(p.is_relative_to(ROOT) and p != ROOT and '..' not in p.parts,
         'outside fixed ResearchOS root')
    need(p.resolve(strict=existing) == p.absolute(), 'alias path')
    for item in (p, *p.parents):
        if os.path.lexists(item):
            need(not item.is_symlink() and
                 not (getattr(item.lstat(), 'st_file_attributes', 0) & 0x400),
                 'reparse path')
        if item == ROOT:
            break
    return p


def raw_at(value: str | Path, sha: str | None = None,
           size: int | None = None) -> bytes:
    p = path(value)
    need(p.is_file(), 'expected regular file absent')
    raw = p.read_bytes()
    need((sha is None or hashlib.sha256(raw).hexdigest() == sha) and
         (size is None or len(raw) == size), 'byte pin mismatch: ' + str(p))
    if p in READS:
        need(READS[p] == raw, 'already read input drift')
    READS[p] = raw
    return raw


def strict(raw: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda value: need(False, 'nonfinite JSON'))


def reference(value: dict) -> tuple[Path, bytes]:
    need(type(value) is dict and set(value) == {'path', 'sha256', 'bytes'} and
         type(value['bytes']) is int and value['bytes'] >= 0 and
         type(value['sha256']) is str and len(value['sha256']) == 64,
         'exact three-key pin required')
    p = path(value['path'])
    return p, raw_at(p, value['sha256'], value['bytes'])


def pinned(p: Path) -> dict:
    raw = raw_at(p)
    return {'path': p.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def files_in(directory: Path) -> dict[str, Path]:
    need(path(directory) == directory and directory.is_dir(), 'missing fixed root')
    rows = {}
    for item in directory.iterdir():
        item = path(item)
        need(item.is_file() and item.name not in rows, 'unexpected directory or alias')
        rows[item.name] = item
    return rows


def encoded(value) -> bytes:
    # Byte-for-byte serializer of the pinned pipeline's save() contract.
    return (json.dumps(value, ensure_ascii=False, indent=2,
                       allow_nan=False) + '\n').encode('utf-8')


def exclusive(p: Path, value) -> dict:
    need(path(p, False) == p and not os.path.lexists(p), 'target occupied')
    raw = encoded(value)
    with p.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    need(p.read_bytes() == raw, 'new output incomplete')
    return pinned(p)


def exclusive_raw(p: Path, raw: bytes) -> dict:
    need(path(p, False) == p and not os.path.lexists(p), 'raw target occupied')
    with p.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    need(p.read_bytes() == raw, 'raw output incomplete')
    return pinned(p)


def pinned_powershell() -> None:
    need(POWERSHELL.is_file() and not POWERSHELL.is_symlink() and
         POWERSHELL.resolve(strict=True) == POWERSHELL.absolute() and
         not (getattr(POWERSHELL.lstat(), 'st_file_attributes', 0) & 0x400),
         'pinned native observer absent or aliased')
    raw = POWERSHELL.read_bytes()
    need((hashlib.sha256(raw).hexdigest(), len(raw)) == POWERSHELL_PIN,
         'native observer binary pin mismatch')


def unchanged() -> None:
    for p, raw in READS.items():
        need(p.read_bytes() == raw, 'input drift before terminal write: ' + str(p))


def git_three(records, label: str) -> None:
    need(type(records) is list and len(records) == 3 and
         [item.get('kind') for item in records] == ['head', 'status', 'index'],
         label + ' Git triple')
    for item in records:
        result = item['result']
        cleanup = result['job_cleanup']
        need(result['actual_exit'] == 0 and result['error'] is None and
             result['timed_out'] is False and result['resumed'] is True and
             type(result['owned_child_pid']) is int and
             result['owned_child_pid'] > 0 and
             type(result['creation_time_100ns']) is int and
             result['creation_time_100ns'] > 0 and
             cleanup['errors'] == [] and
             cleanup['active_processes_last_observed'] == 0 and
             all(cleanup.get(key) is True for key in
                 ('unnamed_exclusive_job', 'kill_on_job_close_configured',
                  'assigned_before_resume', 'primary_exit_confirmed',
                  'job_idle_confirmed', 'handles_closed')),
             label + ' Git Job lifecycle')
        need(reference(item['stdout_ref'])[0].parent == PF and
             reference(item['stderr_ref'])[0].parent == PF,
             label + ' Git original raw location')


def current_process_creation_100ns() -> int:
    class FILETIME(ctypes.Structure):
        _fields_ = [('low', wintypes.DWORD), ('high', wintypes.DWORD)]
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetCurrentProcess.argtypes, api.GetCurrentProcess.restype = [], wintypes.HANDLE
    api.GetProcessTimes.argtypes = ([wintypes.HANDLE] +
                                   [ctypes.POINTER(FILETIME)] * 4)
    api.GetProcessTimes.restype = wintypes.BOOL
    values = [FILETIME() for _ in range(4)]
    need(bool(api.GetProcessTimes(api.GetCurrentProcess(),
                                  *(ctypes.byref(item) for item in values))),
         'current Python creation identity unavailable')
    return (int(values[0].high) << 32) | int(values[0].low)


def observe(attempt: Path, phase: str) -> dict:
    """Use the pinned owned Job runner and capture an actual CIM snapshot."""
    need(phase in ('pre-gate', 'post-gate'), 'invalid observation phase')
    pinned_powershell()
    helper_raw = raw_at(OWNED_HELPER, *OWNED_HELPER_PIN)
    helper = types.ModuleType('scope7_exact_pinned_owned_runner')
    helper.__file__ = str(OWNED_HELPER)
    exec(compile(helper_raw, str(OWNED_HELPER), 'exec'), helper.__dict__)
    # Every UID-bearing row is emitted. Python checks exact PID, creation,
    # parent chain and expected command lines before excluding its own tree.
    script = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);"
        "$OutputEncoding=[Console]::OutputEncoding;"
        "$rows=@(Get-CimInstance Win32_Process | ForEach-Object {"
        "$birth=$null;if($null -ne $_.CreationDate){$birth=[int64]$_.CreationDate.ToUniversalTime().ToFileTimeUtc()};"
        "[pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;"
        "CreationTime100ns=$birth;CommandLine=[string]$_.CommandLine}});"
        "$selfRow=@($rows | Where-Object {$_.ProcessId -eq $PID})[0];"
        "if($null -eq $selfRow){throw 'CIM observer absent'};"
        "$parentRow=@($rows | Where-Object {$_.ProcessId -eq $selfRow.ParentProcessId})[0];"
        "if($null -eq $parentRow){throw 'CIM Python parent absent'};"
        "$grandRow=@($rows | Where-Object {$_.ProcessId -eq $parentRow.ParentProcessId})[0];"
        "if($null -eq $grandRow){throw 'CIM Root wrapper absent'};"
        "$uidRows=@($rows | Where-Object {([string]$_.CommandLine).Contains('" + UID + "')});"
        "$out=[ordered]@{schema='researchos.scope7-win32-process-observation.v3';"
        "run_uuid='" + UID + "';method='Win32_Process';"
        "observed_at=[DateTime]::UtcNow.ToString('o');"
        "observer=$selfRow;python_parent=$parentRow;root_wrapper=$grandRow;"
        "all_uid_processes=$uidRows};"
        "$out | ConvertTo-Json -Depth 8 -Compress")
    argv = [str(POWERSHELL), '-NoLogo', '-NoProfile', '-NonInteractive',
            '-ExecutionPolicy', 'Bypass', '-Command', script]
    env = {'SystemRoot': 'C:/Windows', 'WINDIR': 'C:/Windows',
           'PATH': 'C:/Windows/System32;C:/Windows',
           'PSModulePath': 'C:/Windows/System32/WindowsPowerShell/v1.0/Modules',
           'TEMP': str(attempt), 'TMP': str(attempt)}
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    python_pid, wrapper_pid = os.getpid(), os.getppid()
    python_birth = current_process_creation_100ns()
    stdout_path, stderr_path = (attempt / (phase + '.stdout.raw'),
                                attempt / (phase + '.stderr.raw'))
    need(not os.path.lexists(stdout_path) and not os.path.lexists(stderr_path),
         'observer raw target occupied')
    result = None
    with stdout_path.open('xb') as stdout_file, stderr_path.open('xb') as stderr_file:
        try:
            result = helper.run_owned(argv, str(ROOT), env, stdout_file,
                                      stderr_file, OBSERVER_TIMEOUT_SECONDS,
                                      {'sha256': POWERSHELL_PIN[0],
                                       'bytes': POWERSHELL_PIN[1]})
        except BaseException as exc:
            result = {'actual_exit': None, 'timed_out': None,
                      'error': 'owned helper raised: ' + repr(exc),
                      'owned_child_pid': None, 'creation_time_100ns': None,
                      'job_cleanup': None}
        stdout_file.flush(); os.fsync(stdout_file.fileno())
        stderr_file.flush(); os.fsync(stderr_file.fileno())
    stdout_ref, stderr_ref = pinned(stdout_path), pinned(stderr_path)
    invocation = exclusive(attempt / (phase + '.invocation.json'), {
        'schema': 'researchos.scope7-win32-process-invocation.v3',
        'phase': phase, 'argv': argv, 'cwd': str(ROOT), 'public_env': env,
        'timeout_seconds': OBSERVER_TIMEOUT_SECONDS,
        'started_at': started,
        'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'python_pid': python_pid, 'python_creation_time_100ns': python_birth,
        'root_wrapper_pid': wrapper_pid,
        'owned_result': result,
        'stdout_ref': stdout_ref, 'stderr_ref': stderr_ref})
    cleanup = result.get('job_cleanup') if type(result) is dict else None
    need(result.get('actual_exit') == 0 and result.get('error') is None and
         result.get('timed_out') is False and result.get('resumed') is True and
         type(result.get('owned_child_pid')) is int and
         type(result.get('creation_time_100ns')) is int and
         type(cleanup) is dict and cleanup.get('errors') == [] and
         cleanup.get('active_processes_last_observed') == 0 and
         all(cleanup.get(key) is True for key in
             ('unnamed_exclusive_job', 'kill_on_job_close_configured',
              'assigned_before_resume', 'primary_exit_confirmed',
              'job_idle_confirmed', 'handles_closed')) and
         not stderr_path.read_bytes(),
         phase + ' owned Win32_Process observer failed')
    value = strict(stdout_path.read_bytes())
    need(type(value) is dict and value.get('schema') ==
         'researchos.scope7-win32-process-observation.v3' and
         value.get('run_uuid') == UID and value.get('method') == 'Win32_Process' and
         type(value.get('all_uid_processes')) is list,
         phase + ' native CIM result malformed')
    own, parent, wrapper = (value.get('observer'), value.get('python_parent'),
                            value.get('root_wrapper'))
    need(all(type(row) is dict for row in (own, parent, wrapper)) and
         own.get('ProcessId') == result['owned_child_pid'] and
         own.get('CreationTime100ns') == result['creation_time_100ns'] and
         own.get('ParentProcessId') == python_pid and
         parent.get('ProcessId') == python_pid and
         parent.get('CreationTime100ns') == python_birth and
         parent.get('ParentProcessId') == wrapper_pid and
         wrapper.get('ProcessId') == wrapper_pid and
         type(wrapper.get('CreationTime100ns')) is int and
         0 < wrapper['CreationTime100ns'] <= python_birth <
         result['creation_time_100ns'] and
         SOURCE.name in str(parent.get('CommandLine')) and
         SOURCE.name in str(wrapper.get('CommandLine')) and
         'Get-CimInstance Win32_Process' in str(own.get('CommandLine')),
         phase + ' owned CIM PID/creation/parent chain mismatch')
    excluded = [own, parent, wrapper]
    excluded_identities = {(row['ProcessId'], row['CreationTime100ns'])
                           for row in excluded}
    uid_rows = value['all_uid_processes']
    need(all(type(row) is dict and type(row.get('ProcessId')) is int and
             type(row.get('CreationTime100ns')) is int and
             UID in str(row.get('CommandLine')) for row in uid_rows) and
         len({(row['ProcessId'], row['CreationTime100ns'])
              for row in uid_rows}) == len(uid_rows),
         phase + ' UID process row malformed or duplicated')
    matching = [row for row in uid_rows if
                (row['ProcessId'], row['CreationTime100ns']) not in excluded_identities]
    classification = exclusive(attempt / (phase + '.classification.json'), {
        'schema': 'researchos.scope7-win32-process-classification.v3',
        'raw_stdout_ref': stdout_ref, 'invocation_ref': invocation,
        'exclusion_rule': 'exact PID plus 100ns creation; owned child, current Python, verified Root wrapper',
        'excluded_processes': [row for row in uid_rows if
                               (row['ProcessId'], row['CreationTime100ns']) in excluded_identities],
        'matching_processes': matching})
    observed = stamp(value['observed_at'])
    age = datetime.datetime.now(datetime.timezone.utc) - observed
    need(datetime.timedelta(0) <= age <= datetime.timedelta(seconds=300) and
         matching == [],
         phase + ' observation stale or original grant/another UID process live')
    return {'invocation_ref': invocation, 'stdout_ref': stdout_ref,
            'stderr_ref': stderr_ref, 'classification_ref': classification,
            'observed_at': value['observed_at'],
            'native_probe_exit': result['actual_exit'],
            'matching_processes': matching}


def stamp(value: str) -> datetime.datetime:
    result = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(result.tzinfo is not None, 'unqualified timestamp')
    return result


def validate_existing(review_ref: dict) -> tuple[dict, dict, set, set]:
    need(not any(os.path.lexists(p) for p in
                 (AUTH / 'grant.completed.json', PF / 'manifest.json',
                  AUTH / 'manifest.json')), 'terminal recovery already started')
    scope = strict(raw_at(SCOPE, *SCOPE_PIN))
    grant = strict(raw_at(GRANT, *GRANT_PIN))
    diagnostic = strict(raw_at(DIAGNOSTIC, *DIAGNOSTIC_PIN))
    boundary = strict(raw_at(BOUNDARY_REVIEW, *BOUNDARY_REVIEW_PIN))
    need(boundary['reviewer'] == 'codex:/root/w05_merge_review' and
         boundary['decision'] == 'RECOVERY_BOUNDARY_SUPPORTED_PENDING_NEW_SOURCE_REVIEW' and
         boundary['checks'] == 272 and boundary['failed_checks'] == [] and
         boundary['actual_gate_executions'] == 0 and
         boundary['grant_tail_writes'] == 0,
         'independent boundary input mismatch')
    disk = strict(raw_at(DISK_ASSESSMENT, *DISK_ASSESSMENT_PIN))
    need(boundary['disk_assessment']['sha256'] == DISK_ASSESSMENT_PIN[0] and
         boundary['disk_assessment']['bytes'] == DISK_ASSESSMENT_PIN[1] and
         path(boundary['disk_assessment']['path']) == DISK_ASSESSMENT and
         disk['check_count'] == 272 and disk['failed'] == [] and
         type(disk['pins']) is list and len(disk['pins']) == 219,
         'fixed independent physical inventory absent')
    frozen_pf, frozen_auth = {}, {}
    for item in disk['pins']:
        candidate = Path(item['path'])
        if candidate.parent not in (PF, AUTH):
            continue
        pinned_path, _ = reference(item)
        if pinned_path.parent == PF:
            bucket = frozen_pf
        elif pinned_path.parent == AUTH:
            bucket = frozen_auth
        else:
            continue
        if pinned_path.name in bucket:
            need(bucket[pinned_path.name] == item,
                 'independent duplicate pin conflict')
        bucket[pinned_path.name] = item
    need(len(frozen_pf) == 32 and len(frozen_auth) == 34 and
         set(frozen_pf) == set(files_in(PF)) and
         set(frozen_auth) == set(files_in(AUTH)),
         'frozen independent PF32/AUTH34 not exact')
    need(diagnostic['schema'] ==
         'researchos.desktop58-grant-resume-current-state-diagnostic.v1' and
         diagnostic['actor'] == 'codex:/root' and
         diagnostic['fixed_scope_origin_cut'] == 645 and
         diagnostic['current_canonical_tuple'] == [339, 167, 645] and
         all(diagnostic[key] is None for key in
             ('original_grant_terminal_outer_exit',
              'original_grant_terminal_python_exit',
              'original_grant_terminal_native_exit')) and
         diagnostic['original_grant_restarted'] is False and
         diagnostic['candidate_execution_started'] is False and
         diagnostic['authorization_execute_existing'] is True and
         diagnostic['authorization_manifests_missing'] is True and
         diagnostic['canonical_writes'] == 0 and
         diagnostic['automatic_retry'] is False and
         diagnostic['counter_reset'] is False,
         'Root original unknown-result diagnostic changed')
    registration_manifest = strict(raw_at(REG / 'manifest.json', *REG_MANIFEST_PIN))
    grant_started = strict(raw_at(REG / 'grant.started.json', *GRANT_STARTED_PIN))
    need(grant_started.get('mode') == 'grant' and
         grant_started.get('automatic_retry') is False and
         registration_manifest['count'] == len(registration_manifest['entries']) and
         registration_manifest['excluded_only_self'] is True,
         'registration/grant start chain')
    reg_members = set()
    for item in registration_manifest['entries']:
        original, _ = reference(item)
        need(original.parent == REG and original.name not in reg_members,
             'registration member outside exact namespace')
        reg_members.add(original.name)
    need(set(files_in(REG)) == reg_members |
         {'manifest.json', 'grant.started.json'}, 'registration after-seal delta')
    need(scope['run_uuid'] == UID and
         scope['registration_namespace'] == REG.relative_to(ROOT).as_posix() and
         scope['new_authorization_root'] == str(AUTH) and
         scope['new_grant_preflight_root'] == str(PF) and
         grant['scope_ref'] == pinned(SCOPE) and
         grant['automatic_retry'] is False and grant['counter_reset'] is False,
         'fixed scope/grant mismatch')
    for key, expected in (('output_root', 'executor'), ('outer_output_root', 'launcher'),
                          ('export_root', 'export')):
        target = path(scope[key], False)
        need(not os.path.lexists(target) and UID in target.name,
             'new execution root occupied: ' + expected)
    raw_at(GATE, *GATE_PIN)
    raw_at(PIPELINE, *PIPELINE_PIN)
    review = strict(reference(review_ref)[1])
    need(review.get('schema') == 'researchos.desktop58-grant-recovery-independent-review.v1' and
         review.get('decision') == 'READY_SOURCE_ONLY' and
         review.get('reviewer_id') not in (None, '', 'codex:/root') and
         review.get('scope_ref') == pinned(SCOPE) and
         review.get('grant_ref') == pinned(GRANT) and
         review.get('diagnostic_ref') == pinned(DIAGNOSTIC) and
         review.get('boundary_review_ref') == pinned(BOUNDARY_REVIEW) and
         review.get('disk_assessment_ref') == pinned(DISK_ASSESSMENT) and
         review.get('grant_started_ref') == pinned(REG / 'grant.started.json') and
         review.get('source_path') == SOURCE.relative_to(ROOT).as_posix() and
         review.get('source_sha256') == hashlib.sha256(raw_at(SOURCE)).hexdigest() and
         review.get('requests') == [],
         'independent source review absent or changed')
    v2_origin = strict(raw_at(V2_ORIGIN, *V2_ORIGIN_PIN))
    v2_attempt = strict(raw_at(V2_ATTEMPT, *V2_ATTEMPT_PIN))
    raw_at(V2_SOURCE, *V2_SOURCE_PIN)
    need(v2_origin['count'] == 667 and
         v2_origin['first_cause'] == "RuntimeError('process observation stale')" and
         v2_origin['new_gate_result_not_separately_saved'] is True and
         v2_origin['original_grant_terminal'] ==
         {'outer': None, 'python': None, 'native': None} and
         v2_attempt['schema'] == 'researchos.desktop58-grant-recovery-attempt.v1' and
         v2_attempt['run_uuid'] == UID and
         v2_attempt['original_grant_outer_exit'] is None and
         v2_attempt['original_grant_python_exit'] is None and
         v2_attempt['original_grant_native_exit'] is None and
         set(files_in(V2_ATTEMPT.parent)) == {'attempt.started.json'},
         'prior v2 failed attempt chain changed')
    for name, sha in CANON.items():
        raw_at(ROOT / 'execution/v2.4' / name, sha)
    copies = grant['canonical_copies']
    need(len(copies) == 4 and
         {item['canonical_path'] for item in copies} ==
         {'execution/v2.4/' + name for name in CANON}, 'canonical copy set')
    for item in copies:
        copied_path, copied_raw = reference(item['ref'])
        need(copied_path.parent == AUTH and
             copied_raw == raw_at(ROOT / item['canonical_path']) and
             item['ref']['sha256'] == CANON[Path(item['canonical_path']).name],
             'canonical copy bytes differ from current')
    copy_map = strict(raw_at(AUTH / 'preflight-copy-map.json'))
    need(copy_map['preflight_root'] == str(PF) and
         copy_map['directory_or_copy_is_not_authority'] is True and
         type(copy_map['entries']) is list and len(copy_map['entries']) == 32,
         'original 32-copy map changed')
    seen_pf, seen_auth = set(), set()
    for pair in copy_map['entries']:
        need(set(pair) == {'original_ref', 'copy_ref'}, 'copy map pair shape')
        original, before = reference(pair['original_ref'])
        copied, after = reference(pair['copy_ref'])
        need(original.parent == PF and copied.parent == AUTH and
             original.name == copied.name and before == after and
             pair['original_ref']['sha256'] == pair['copy_ref']['sha256'] and
             pair['original_ref']['bytes'] == pair['copy_ref']['bytes'] and
             original.name not in seen_pf and copied.name not in seen_auth,
             'copy map byte/namespace conflict')
        seen_pf.add(original.name)
        seen_auth.add(copied.name)
    need(set(files_in(PF)) == seen_pf and
         set(files_in(AUTH)) == seen_auth |
         {'preflight-copy-map.json', 'authorization.execute.json'},
         'unexpected old fact or terminal file')
    admission = strict(raw_at(PF / 'admission.verified.json'))
    prelaunch = strict(reference(grant['prelaunch_evidence_ref'])[1])
    started = strict(raw_at(PF / 'preflight.started.json'))
    admission_window = strict(raw_at(PF / 'admission.time-window.json'))
    created = strict(raw_at(PF / 'authorization-leaf.created.json'))
    final_window = strict(raw_at(PF / 'grant-final.time-window.json'))
    need(started['authorization_leaf_created'] is False and
         created['admission_ref'] == pinned(PF / 'admission.verified.json') and
         created['directory_is_not_grant'] is True and
         stamp(started['at']) <= stamp(admission_window['started_at']) <=
         stamp(admission_window['ended_at']) <= stamp(admission['at']) <=
         stamp(created['at']) <= stamp(final_window['started_at']) <=
         stamp(final_window['ended_at']) and
         prelaunch['time_window_ref'] == pinned(PF / 'grant-final.time-window.json'),
         'admission before auth creation before grant-final')
    need(admission['scope_ref'] == pinned(SCOPE) and
         admission['authorization_leaf_created'] is False and
         prelaunch['admission_ref'] == pinned(PF / 'admission.verified.json') and
         prelaunch['runtime_observation_refs'] == grant['runtime_observation_refs'],
         'admission/prelaunch chain')
    git_three(admission['actual_Git_records'], 'admission')
    git_three(prelaunch['git'], 'grant-final')
    obs = grant['runtime_observation_refs']
    need(len(obs) == 3 and
         [row['path'] for row in obs] == scope['expected_runtime_observation_paths'],
         'three ordered complete runtime observations')
    for row in obs:
        observed_path, observed_raw = reference(row)
        value = strict(observed_raw)
        need(observed_path.parent == AUTH and
             value['all_observed_inputs_pre_pinned'] is True and value['files'],
             'runtime observation incomplete')
    return scope, grant, seen_pf, seen_auth


def main() -> int:
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,
         'pinned Python -I -S -X utf8 required')
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument('--review-ref', required=True, type=json.loads)
    parser.add_argument('--attempt-root', required=True)
    options = parser.parse_args()
    attempt = path(options.attempt_root, False)
    need(attempt.parent == ROOT /
         'execution/v2.4/receipts/W05/W05-99/scope7_grant_recovery_execution_codex'
         and UID in attempt.name and not os.path.lexists(attempt) and
         attempt.parent.is_dir(), 'fresh Root recovery fact namespace required')
    _, _, expected_pf, expected_auth = validate_existing(options.review_ref)
    attempt.mkdir()
    marker = exclusive(attempt / 'attempt.started.json', {
        'schema': 'researchos.desktop58-grant-recovery-attempt.v3',
        'actor': 'codex:/root', 'run_uuid': UID,
        'review_ref': options.review_ref,
        'prior_failure_ref': pinned(V2_ORIGIN),
        'prior_attempt_ref': pinned(V2_ATTEMPT),
        'prior_source_ref': pinned(V2_SOURCE),
        'automatic_retry': False, 'counter_reset': False,
        'original_grant_outer_exit': None, 'original_grant_python_exit': None,
        'original_grant_native_exit': None})
    pre_observation = observe(attempt, 'pre-gate')
    # The pinned gate reads current authority. It must run before any grant
    # completion or manifest write; no caller-supplied source path is used.
    gate_raw = raw_at(GATE, *GATE_PIN)
    gate = types.ModuleType('scope7_exact_pinned_grant_gate')
    gate.__file__ = str(GATE)
    exec(compile(gate_raw, str(GATE), 'exec'), gate.__dict__)
    gate_result = gate.validate_grant(str(SCOPE), SCOPE_PIN[0],
                                      str(GRANT), GRANT_PIN[0])
    gate_result_ref = exclusive(attempt / 'gate.result.json', gate_result)
    need(gate_result['registered_Root_scope_and_grant_verified'] is True and
         gate_result['fresh_current58_CLI2_qualified'] is True,
         'pinned read-only gate rejected actual grant')
    unchanged()
    post_observation = observe(attempt, 'post-gate')
    need(set(files_in(PF)) == expected_pf and
         set(files_in(AUTH)) == expected_auth |
         {'preflight-copy-map.json', 'authorization.execute.json'},
         'old input membership changed during gate')
    need(all(not os.path.lexists(path(gate_result['scope'][key], False))
             for key in ('output_root', 'outer_output_root', 'export_root')),
         'execution leaf appeared during read-only gate')
    need(not any(os.path.lexists(p) for p in
                 (AUTH / 'grant.completed.json', PF / 'manifest.json',
                  AUTH / 'manifest.json')), 'terminal appeared during gate')
    unchanged()
    post_age = datetime.datetime.now(datetime.timezone.utc) - stamp(
        post_observation['observed_at'])
    need(datetime.timedelta(0) <= post_age <= datetime.timedelta(seconds=300),
         'post-gate process observation stale before terminal write')
    completed = exclusive(AUTH / 'grant.completed.json', {
        'grant_ref': pinned(GRANT), 'source_acceptance': False,
        'formal_increment': 0, 'launcher_executions': 0,
        'preflight_root': str(PF), 'point_in_time_not_lifecycle': True})
    unchanged()
    need(set(files_in(PF)) == expected_pf, 'preflight membership changed')
    pf_rows = [pinned(p) for p in sorted(files_in(PF).values())]
    pf_manifest = exclusive(PF / 'manifest.json', {
        'entries': pf_rows, 'count': len(pf_rows), 'excluded_only_self': True})
    unchanged()
    need(set(files_in(AUTH)) == expected_auth |
         {'preflight-copy-map.json', 'authorization.execute.json',
          'grant.completed.json'}, 'authorization membership changed')
    auth_rows = [pinned(p) for p in sorted(files_in(AUTH).values())]
    auth_manifest = exclusive(AUTH / 'manifest.json', {
        'entries': auth_rows, 'count': len(auth_rows), 'excluded_only_self': True})
    fact = exclusive(attempt / 'recovery.completed.json', {
        'schema': 'researchos.desktop58-grant-recovery-fact.v1',
        'actor': 'codex:/root', 'run_uuid': UID,
        'attempt_ref': marker, 'review_ref': options.review_ref,
        'pre_gate_process_observation': pre_observation,
        'post_gate_process_observation': post_observation,
        'gate_result_ref': gate_result_ref,
        'grant_ref': pinned(GRANT), 'grant_completed_ref': completed,
        'preflight_manifest_ref': pf_manifest,
        'authorization_manifest_ref': auth_manifest,
        'gate_authority_input_count': len(gate_result['authorization_input_refs']),
        'original_grant_outer_exit': None, 'original_grant_python_exit': None,
        'original_grant_native_exit': None, 'automatic_retry': False,
        'counter_reset': False, 'source_acceptance': False, 'formal_increment': 0})
    print(json.dumps({'status': 'RECOVERED_METADATA_ONLY',
                      'recovery_fact_ref': fact, 'grant_completed_ref': completed,
                      'preflight_manifest_ref': pf_manifest,
                      'authorization_manifest_ref': auth_manifest,
                      'original_grant_outer_exit': None,
                      'source_acceptance': False, 'formal_increment': 0},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        actual_code = main()
    except BaseException as exc:
        # No rollback, no retry. Root seals stdout/stderr and inspects
        # exclusive partial files before choosing a new recovery procedure.
        print(json.dumps({'status': 'RECOVERY_INCOMPLETE', 'first_cause': repr(exc),
                          'original_grant_outer_exit': None,
                          'original_grant_python_exit': None,
                          'original_grant_native_exit': None,
                          'automatic_retry': False, 'counter_reset': False},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(actual_code)
