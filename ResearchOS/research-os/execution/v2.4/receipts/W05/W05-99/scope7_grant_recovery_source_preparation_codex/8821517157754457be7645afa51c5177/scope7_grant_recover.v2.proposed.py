"""One-use Scope7 metadata recovery. Never rerun the original grant phase.

SOURCE PROPOSAL ONLY. Root must adopt this exact file after nonauthor review.
This program verifies preexisting facts, calls the pinned read-only grant gate,
then exclusively writes the three missing terminal metadata files.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import types

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


def process_empty(value: dict) -> None:
    need(value.get('schema') == 'researchos.root-process-empty-observation.v1' and
         value.get('actor') == 'codex:/root' and
         value.get('run_uuid') == UID and
         value.get('method') == 'Win32_Process' and
         value.get('matching_processes') == [] and
         value.get('native_probe_exit') == 0 and
         value.get('command_filter_contains') == UID,
         'actual current-process observation missing')
    stamp = datetime.datetime.fromisoformat(value['observed_at'].replace('Z', '+00:00'))
    now = datetime.datetime.now(datetime.timezone.utc)
    need(stamp.tzinfo is not None and
         datetime.timedelta(0) <= now - stamp <= datetime.timedelta(seconds=300),
         'process observation stale')


def stamp(value: str) -> datetime.datetime:
    result = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(result.tzinfo is not None, 'unqualified timestamp')
    return result


def validate_existing(review_ref: dict, process_ref: dict) -> tuple[dict, dict, set, set]:
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
    process_empty(strict(reference(process_ref)[1]))
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
    parser.add_argument('--process-ref', required=True, type=json.loads)
    parser.add_argument('--attempt-root', required=True)
    options = parser.parse_args()
    attempt = path(options.attempt_root, False)
    need(attempt.parent == ROOT /
         'execution/v2.4/receipts/W05/W05-99/scope7_grant_recovery_execution_codex'
         and UID in attempt.name and not os.path.lexists(attempt) and
         attempt.parent.is_dir(), 'fresh Root recovery fact namespace required')
    _, _, expected_pf, expected_auth = validate_existing(
        options.review_ref, options.process_ref)
    attempt.mkdir()
    marker = exclusive(attempt / 'attempt.started.json', {
        'schema': 'researchos.desktop58-grant-recovery-attempt.v1',
        'actor': 'codex:/root', 'run_uuid': UID,
        'review_ref': options.review_ref, 'process_ref': options.process_ref,
        'automatic_retry': False, 'counter_reset': False,
        'original_grant_outer_exit': None, 'original_grant_python_exit': None,
        'original_grant_native_exit': None})
    # The pinned gate reads current authority. It must run before any grant
    # completion or manifest write; no caller-supplied source path is used.
    gate_raw = raw_at(GATE, *GATE_PIN)
    gate = types.ModuleType('scope7_exact_pinned_grant_gate')
    gate.__file__ = str(GATE)
    exec(compile(gate_raw, str(GATE), 'exec'), gate.__dict__)
    gate_result = gate.validate_grant(str(SCOPE), SCOPE_PIN[0],
                                      str(GRANT), GRANT_PIN[0])
    need(gate_result['registered_Root_scope_and_grant_verified'] is True and
         gate_result['fresh_current58_CLI2_qualified'] is True,
         'pinned read-only gate rejected actual grant')
    unchanged()
    process_empty(strict(reference(options.process_ref)[1]))
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
        'process_ref': options.process_ref,
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
