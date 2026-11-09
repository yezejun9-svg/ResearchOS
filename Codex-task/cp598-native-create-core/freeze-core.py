from pathlib import Path
from collections import Counter
import datetime
import hashlib
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
REPO = Path('D:/作品集/ResearchOS/research-os')
ROOT = REPO / '.local/worktrees/w14-native-create-core-20261104'
AUTHOR = REPO / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core/author'
scope_path = AUTHOR.parent / 'scope.json'
scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
names = scope['production_paths'] + scope['test_paths']
assert len(names) == len(set(names)) == 22
assert len(scope['production_paths']) == 17 and len(scope['test_paths']) == 5
attempts = ['compile01', 'focused01', 'focused02', 'focused03', 'regression01', 'compile02']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def stats(path):
    events = []
    for line in path.read_bytes().splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(event, dict) and 'Action' in event:
            events.append(event)
    counts = Counter()
    packages = {}
    tests = []
    failed_output = []
    for e in events:
        name, action, pkg = e.get('Test'), e['Action'], e.get('Package', '')
        if name and action in ('pass', 'fail', 'skip'):
            level = 'subtest' if '/' in name else 'top_level'
            counts[level + '_' + action] += 1
            tests.append({'package': pkg, 'name': name, 'result': action})
        elif not name and action in ('pass', 'fail', 'skip'):
            packages[pkg] = action
        if action == 'output':
            out = e.get('Output', '')
            if any(t in out for t in ('build failed', 'too many arguments', 'undefined:', 'SCHEMA_', 'immutable replay', 'CLIENT_', '--- FAIL:', 'FAIL\t')):
                failed_output.append(out.strip())
    return {'counts': dict(counts), 'packages': packages, 'test_results': tests,
            'test_run_event_count': sum(e['Action'] == 'run' for e in events),
            'failure_evidence_output': failed_output}

tool_lock = json.loads((REPO / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))
git = tool_lock['tools']['git']
assert sha(Path(git['path'])) == git['sha256']
prefix = [git['path'], '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']
head = subprocess.run(prefix + ['rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, check=True).stdout.decode('ascii').strip()
assert head == scope['base_head']
status = subprocess.run(prefix + ['status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT, capture_output=True, check=True)
changed = []
for entry in status.stdout.split(b'\0'):
    if entry:
        changed.append(entry[3:].decode('utf-8'))
assert set(changed) == set(names), {'unexpected': sorted(set(changed) - set(names)), 'missing': sorted(set(names) - set(changed))}
current = {n: sha(ROOT / n) for n in names}
checks = []
for a in attempts:
    folder = AUTHOR / a
    result_path = folder / 'results.json'
    result = json.loads(result_path.read_text(encoding='utf-8'))
    detail = {'attempt': a, 'result_path': str(result_path), 'result_sha256': sha(result_path),
              'status': result['status'], 'commands': []}
    for row in result['commands']:
        phase = row['phase']
        raw = folder / (phase + '.stdout.raw')
        err = folder / (phase + '.stderr.raw')
        assert sha(raw) == row['stdout_sha256'] and sha(err) == row['stderr_sha256']
        command_path = folder / (phase + '.command.json')
        c = {'phase': phase, 'exit_code': row['exit_code'], 'command_path': str(command_path),
             'command_sha256': sha(command_path), 'stdout_sha256': sha(raw), 'stderr_sha256': sha(err)}
        if phase in ('focused', 'regression', 'compile'):
            c['go_json'] = stats(raw)
            c['execution_class'] = 'COMPILE_ONLY_NO_TESTS_RUN' if c['go_json']['test_run_event_count'] == 0 else 'DEVELOPMENT_FIXTURES_ONLY'
        detail['commands'].append(c)
    checks.append(detail)
for a in ('focused03', 'regression01', 'compile02'):
    check = next(v for v in checks if v['attempt'] == a)
    assert check['status'] == 'DEVELOPMENT_CHECKS_PASS'
    result = json.loads((AUTHOR / a / 'results.json').read_text(encoding='utf-8'))
    assert result['sources'] == current

frozen_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest = {
    'scope_id': scope['scope_id'], 'source_base': head, 'worktree': str(ROOT), 'frozen_utc': frozen_at,
    'construction_frozen': True, 'source_modification_permitted': False,
    'scope_sha256': sha(scope_path), 'production_count': 17, 'new_test_count': 5,
    'source_files': [{'path': n, 'kind': 'production' if n in scope['production_paths'] else 'test',
                      'baseline_sha256': scope['baseline_sha256'][n], 'sha256': current[n], 'bytes': (ROOT/n).stat().st_size}
                     for n in names],
    'unrelated_candidate_changes': [], 'committed': False, 'formal_increment': 0,
    'independent_review_status': 'PENDING',
}
diagnostics = {
    'counter_reset': False, 'existing_counter_not_modified': True,
    'source_failure_record_count': 5, 'distinct_source_failure_origins': 4,
    'note': 'Record counts below identify root causes; package and parent/subtest propagation is not counted again. Root owns global append-only counters.',
    'origins': [
        {'origin': 'CURRENT_AUTHORITY_ROOT_CALL_SIGNATURE', 'failed_attempt_count': 2,
         'attempts': [{'receipt': 'compile01', 'result': 'BUILD_FAILED_TESTS_NOT_RUN', 'cause': 'Used method qualifier for package free function.'},
                      {'receipt': 'focused01', 'result': 'BUILD_FAILED_TESTS_NOT_RUN', 'cause': 'Corrected qualifier but retained extra context argument.'}],
         'directed_evidence': 'Read actual package currentAuthorityRoot(*sql.Tx,string), removed context argument at both new calls.',
         'resolved_by': 'focused02 compiled and executed actual tests; focused03 and compile02 pass.'},
        {'origin': 'NATIVE_FIXTURE_HOST_CONFIGURE_PROJECT_SCOPE', 'failed_attempt_count': 1,
         'attempts': [{'receipt': 'focused02', 'cause': 'New fixture decoded host.configure with non-null project instead of frozen four-null envelope.'}],
         'directed_fix': 'Only new fixture sets project null before decode for host.configure/status.', 'resolved_by': 'focused03'},
        {'origin': 'PRIVATE_PROFILE_PUBLIC_SCHEMA_COMPILER', 'failed_attempt_count': 1,
         'attempts': [{'receipt': 'focused02', 'cause': 'Public domain.LoadSchema requires public method/event maps absent from independently closed private profile.'}],
         'directed_fix': 'Dedicated closed local-only jsonschema compiler for exactly the new request/result definitions; public loader and frozen schema unchanged.',
         'resolved_by': 'focused03'},
        {'origin': 'PREPARED_ADDON_ORIGINAL_IMMUTABLE_HEADER_GUARD', 'failed_attempt_count': 1,
         'attempts': [{'receipt': 'focused02', 'cause': 'Original idempotency_immutable rejects every UPDATE, including exact native origin seal CAS.'}],
         'directed_fix': 'Prepared fresh-only install checks exact sqlite_schema.sql preimage, then atomically replaces only this known guard. All prior UPDATE mutations still rejected except exact v1-to-v2 seal with existing immutable matching origin and NULL-safe preserved columns. Native DELETE/REPLACE protection is new; legacy behavior is not broadened.',
         'legacy_guard_sql_sha256': 'd8602e7b9198f35a6cac8c7f42bf880b083444f5e10ef12e5361973f776211ce',
         'resolved_by': 'focused03'},
    ],
    'transport_and_controller_diagnostics': [
        {'action': 'C apply_patch templates API test + install-final-tests.py', 'old_cell': 'g30:84',
         'status': 'RECONCILED_EXECUTED_NO_REPLAY', 'evidence': 'Parent confirmed files; author read actual contents and hashes before the guarded installer ran once.',
         'template_sha256': '21dab529aee809fd03887f61c1ccce11e3bad69805571a68e0fb65b8801c5dd9',
         'installer_sha256': '3da99a0a5ea1c83a78b9c8793704c9407efd95f497774cf35c71a01c3e7a87cf'},
        {'action': 'Recovery PowerShell read enumeration', 'result': 'PARSER_ERROR_BEFORE_EXECUTION', 'tool_chunk': '44806a',
         'resolution': 'Successful precise read 636dae/9956b5; no source mutation from failed parse.'},
        {'action': 'Resume old focused03 session50136', 'result': 'UNKNOWN_PROCESS_ID_AFTER_COMPLETION',
         'resolution': 'Read actual focused03/results.json and exact raw hashes, confirmed terminal0 at 2026-11-04T16:27:00.010562+00:00; did not rerun.'},
    ],
    'checks': checks, 'formal_increment': 0,
}
summary = {
    'scope_id': scope['scope_id'], 'status': 'DEVELOPMENT_CHECKS_PASS_PENDING_INDEPENDENT_QA',
    'source_base': head, 'construction_frozen': True, 'source_modification_permitted': False,
    'source_manifest_path': str(AUTHOR/'source-manifest.json'),
    'production_count': 17, 'new_test_count': 5, 'formal_increment': 0,
    'implemented': [
        'Private closed Native attestation action from verified current OS peer; legacy bool-only entry cannot issue a witness.',
        'Host service/store/boot-bound immutable witness map, capacity256, TTL60s capped by credential expiry; credential value never retained in witness/origin/result.',
        'HTTP untrusted selector -> exact-transaction/service/principal credential context -> independent actual raw-byte hash and scope verification.',
        'Fresh successful session.create origin insertion and exact private v1-to-v2 response marker seal in same transaction; rejected requests stay v1.',
        'Sealed successful replay uses historical typed origin pair without requiring live map, with normal current Bearer authentication and no new consume/grant/event.',
        'Foreign attach to every origin-bearing session refused before live/expired/null legacy transfer; cold map never downgrades recorded provenance.',
        'Prepared-only immutable addon, strict schema fingerprint and bidirectional marker/origin/identity/raw/typed response validation; ordinary backup/restore unsupported whenever addon exists.',
    ],
    'verified_by': [{'attempt': c['attempt'], 'status': c['status'], 'commands': [
        {'phase': r['phase'], 'exit_code': r['exit_code'], 'execution_class': r.get('execution_class'),
         'counts': r.get('go_json',{}).get('counts', {}), 'packages': r.get('go_json',{}).get('packages', {})}
        for r in c['commands']]} for c in checks],
    'limitations': [
        'Development default-off pilot, not W14 acceptance or formal 22-parent/42-case completion.',
        'All executed tests use fresh fixture stores, injected peers/authority, Recorder or existing local test fixtures. No real Native listener, model, resource scope, old database or production backup was run.',
        'Prepared 0025 asset is not in migrations/sqlite, does not change hard24, does not auto-install on ordinary startup, and is not approved for existing-database adoption.',
        'CLI/Desktop explicit gate behavior is separately owned/integrated/reviewed and not retested or edited by this Core author.',
        'Legacy sessions retain their old behavior; same-writer rebind, goal.start provenance, cross-writer durable ACK/replay/CAS handoff and active-run pausing remain unimplemented.',
        'Cold restart invalidates current in-memory authorization; recorded historical provenance remains verifiable and foreign attach remains refused.',
        'The native producer commits to caller-declared digest; only HTTP consumer proves that digest equals actual received originalRaw bytes.',
        'Historical consistency cannot prove authorization if an attacker deletes every independent trace of addon adoption, marker, origin and schema; no such tamper-resistance claim is made.',
        'No source commit, Main/registry/checkpoint/global counter change or self-signed independent acceptance.',
    ],
    'failure_diagnostics_path': str(AUTHOR/'diagnostics.json'),
}

for target in ('source-manifest.json', 'diagnostics.json', 'author-summary.json', 'construction-freeze.json', 'controller-manifest.json'):
    assert not (AUTHOR/target).exists(), target
snapshot = AUTHOR/'frozen-source'
snapshot.mkdir(exist_ok=False)
for n in names:
    dst = snapshot/n
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/n, dst)
    assert sha(dst) == current[n]
save(AUTHOR/'source-manifest.json', manifest)
save(AUTHOR/'diagnostics.json', diagnostics)
save(AUTHOR/'author-summary.json', summary)
controller_names = sorted(p for p in HERE.rglob('*') if p.is_file() and 'runtime' not in p.relative_to(HERE).parts and '__pycache__' not in p.relative_to(HERE).parts)
save(AUTHOR/'controller-manifest.json', {'files': [{'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in controller_names],
    'note': 'Original generation/test templates are archived provenance only; current frozen-source and exact source-manifest are authoritative after directed refinements.'})
freeze = {'frozen_utc': frozen_at, 'scope_id': scope['scope_id'], 'source_base': head,
          'construction_frozen': True, 'source_modification_permitted': False, 'source_count': 22,
          'manifest_sha256': sha(AUTHOR/'source-manifest.json'),
          'summary_sha256': sha(AUTHOR/'author-summary.json'),
          'diagnostics_sha256': sha(AUTHOR/'diagnostics.json'),
          'controller_manifest_sha256': sha(AUTHOR/'controller-manifest.json'),
          'independent_review': 'PENDING', 'formal_increment': 0, 'no_pending_test_process': True}
save(AUTHOR/'construction-freeze.json', freeze)
assert {n:sha(ROOT/n) for n in names} == current
print(json.dumps({'freeze': freeze, 'construction_freeze_sha256': sha(AUTHOR/'construction-freeze.json'),
                  'result_counts': [{'attempt': c['attempt'], 'counts': [r['go_json']['counts'] for r in c['commands'] if 'go_json' in r]} for c in checks]}, ensure_ascii=False))
