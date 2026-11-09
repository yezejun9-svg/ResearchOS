"""Pure metadata controls. Parse selected helpers, never import/run recovery."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
UID = '9eccde97a9fa4815941768cacaf590dc'
HERE = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
               'scope7_grant_recovery_source_preparation_codex/'
               '8821517157754457be7645afa51c5177')
AUTH = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
               'desktop58_finite_authorization_codex/' + UID)
PF = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
             'desktop58_finite_grant_preflight_codex/' + UID)
REG = ROOT / ('execution/v2.4/receipts/W05/W05-99/integration_codex/'
              'desktop58-finite169-go3-r339-' + UID)
source = HERE / 'scope7_grant_recover.v2.proposed.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in ('need', 'git_three', 'process_empty')]
assert [node.name for node in selected] == ['need', 'git_three', 'process_empty']


def reference(value):
    assert type(value) is dict and set(value) == {'path', 'sha256', 'bytes'}
    p = Path(value['path'])
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    assert len(raw) == value['bytes']
    assert hashlib.sha256(raw).hexdigest() == value['sha256']
    return p, raw


space = {'PF': PF, 'UID': UID, 'datetime': datetime, 'reference': reference}
exec(compile(ast.Module(body=selected, type_ignores=[]),
             '<scope7-selected-pure-helpers>', 'exec'), space)
git_three, process_empty = space['git_three'], space['process_empty']
grant = json.loads((AUTH / 'authorization.execute.json').read_text(encoding='utf-8'))
admission = json.loads((PF / 'admission.verified.json').read_text(encoding='utf-8'))
prelaunch = json.loads((AUTH / 'prelaunch.json').read_text(encoding='utf-8'))
scope = json.loads((REG / 'scope_registration.json').read_text(encoding='utf-8'))
copy_map = json.loads((AUTH / 'preflight-copy-map.json').read_text(encoding='utf-8'))
registration_manifest = json.loads((REG / 'manifest.json').read_text(encoding='utf-8'))
grant_started = json.loads((REG / 'grant.started.json').read_text(encoding='utf-8'))
diagnostic_path = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                          'desktop58_grant_resume_diagnostic_codex/' + UID +
                          '/failures658-660-and-current-state.original.json')
diagnostic = json.loads(diagnostic_path.read_text(encoding='utf-8'))
boundary_path = ROOT / ('execution/v2.4/receipts/W13/W13-03/'
                        'desktop58_grant_recovery_independent_review_codex/'
                        '96fdce9d0e3043c0a5d6aa82808749ad/boundary-review.json')
boundary = json.loads(boundary_path.read_text(encoding='utf-8'))
disk_path = boundary_path.parent / 'disk-assessment.json'
disk = json.loads(disk_path.read_text(encoding='utf-8'))
checks = []


def passed(name, condition):
    assert condition, name
    checks.append({'id': name, 'result': 'PASS'})


def refused(name, action):
    try:
        action()
    except (RuntimeError, AssertionError, KeyError, TypeError, ValueError):
        checks.append({'id': name, 'result': 'REJECT'})
        return
    raise AssertionError('not rejected: ' + name)


passed('fixed grant bytes',
       hashlib.sha256((AUTH / 'authorization.execute.json').read_bytes()).hexdigest()
       == '6b0ef299508d98c8f1dca47e3d01116ceae98aca7914d318f3ed6d13bc3f6c10')
passed('fixed scope bytes',
       hashlib.sha256((REG / 'scope_registration.json').read_bytes()).hexdigest()
       == 'c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859')
passed('registration one-file after-seal delta',
       {item.name for item in REG.iterdir()} -
       {Path(row['path']).name for row in registration_manifest['entries']} ==
       {'manifest.json', 'grant.started.json'} and
       grant_started['mode'] == 'grant' and
       grant_started['automatic_retry'] is False)
passed('Root unknown-original-result diagnostic',
       hashlib.sha256(diagnostic_path.read_bytes()).hexdigest() ==
       '233cfd48e5ff6aef7cf69b0e6c6633c16ef34b64976486f3fefca1904406ae36' and
       diagnostic['current_canonical_tuple'] == [339, 167, 645] and
       diagnostic['original_grant_terminal_outer_exit'] is None and
       diagnostic['original_grant_terminal_python_exit'] is None and
       diagnostic['original_grant_terminal_native_exit'] is None)
passed('independent boundary input',
       hashlib.sha256(boundary_path.read_bytes()).hexdigest() ==
       'a54265b97224dda0b4457fe264fc76377862990dbb4b1e652bb7717dd4252dee' and
       boundary['checks'] == 272 and boundary['failed_checks'] == [] and
       boundary['decision'] == 'RECOVERY_BOUNDARY_SUPPORTED_PENDING_NEW_SOURCE_REVIEW')
passed('independent disk snapshot exact ref',
       disk_path.stat().st_size == boundary['disk_assessment']['bytes'] and
       hashlib.sha256(disk_path.read_bytes()).hexdigest() ==
       boundary['disk_assessment']['sha256'] ==
       '82d667aab0593d2a35ceadddacfd0985790ba821425d4834eed36d2883fd3a9f')
for label, root, expected in (('PF', PF, 32), ('AUTH', AUTH, 34)):
    selected = [item for item in disk['pins']
                if Path(item['path']).parent == root]
    unique = {}
    for item in selected:
        old = unique.setdefault(Path(item['path']).name, item)
        assert old == item, label + ' conflicting independent pin'
        reference(item)
    passed(label + ' every old physical file has an independent pin',
           len(unique) == expected and
           set(unique) == {item.name for item in root.iterdir()})
    altered = copy.deepcopy(selected[0])
    altered['sha256'] = '0' * 64
    refused(label + ' paired old-byte mutation',
            lambda item=altered: reference(item))
timeline = [json.loads((PF / name).read_text(encoding='utf-8'))
            for name in ('preflight.started.json', 'admission.time-window.json',
                         'admission.verified.json', 'authorization-leaf.created.json',
                         'grant-final.time-window.json')]
times = [timeline[0]['at'], timeline[1]['started_at'], timeline[1]['ended_at'],
         timeline[2]['at'], timeline[3]['at'],
         timeline[4]['started_at'], timeline[4]['ended_at']]
passed('admission before auth mkdir before final Git',
       times == sorted(times) and timeline[0]['authorization_leaf_created'] is False and
       timeline[2]['authorization_leaf_created'] is False and
       timeline[3]['directory_is_not_grant'] is True)
passed('terminal trio absent',
       not any(p.exists() for p in (AUTH / 'grant.completed.json',
                                    PF / 'manifest.json', AUTH / 'manifest.json')))
passed('three future execution roots absent',
       not any(Path(scope[key]).exists() for key in
               ('output_root', 'outer_output_root', 'export_root')))
passed('32 exact original-copy pairs',
       len(copy_map['entries']) == 32 and
       {p.name for p in PF.iterdir()} ==
       {Path(row['original_ref']['path']).name for row in copy_map['entries']} and
       {p.name for p in AUTH.iterdir()} ==
       {Path(row['copy_ref']['path']).name for row in copy_map['entries']} |
       {'preflight-copy-map.json', 'authorization.execute.json'} and
       all(reference(row['original_ref'])[1] == reference(row['copy_ref'])[1]
           for row in copy_map['entries']))
passed('three ordered runtime observations',
       len(grant['runtime_observation_refs']) == 3 and
       [row['path'] for row in grant['runtime_observation_refs']] ==
       scope['expected_runtime_observation_paths'] and
       all(reference(row)[0].parent == AUTH for row in grant['runtime_observation_refs']))
for phase, records in (('admission', admission['actual_Git_records']),
                       ('grant-final', prelaunch['git'])):
    git_three(records, phase)
    checks.append({'id': phase + ' three Git Job receipts', 'result': 'PASS'})
    altered = copy.deepcopy(records)
    altered[0]['result']['resumed'] = False
    refused(phase + ' unresumed child', lambda rows=altered: git_three(rows, phase))
    altered = copy.deepcopy(records)
    altered[1]['result']['creation_time_100ns'] = 0
    refused(phase + ' missing PID creation', lambda rows=altered: git_three(rows, phase))
    altered = copy.deepcopy(records)
    altered[2]['result']['job_cleanup']['job_idle_confirmed'] = False
    refused(phase + ' unclosed Job', lambda rows=altered: git_three(rows, phase))
    altered = copy.deepcopy(records)
    altered[0]['stdout_ref']['sha256'] = '0' * 64
    refused(phase + ' altered Git raw pin', lambda rows=altered: git_three(rows, phase))

observation = {'schema': 'researchos.root-process-empty-observation.v1',
               'actor': 'codex:/root', 'run_uuid': UID,
               'method': 'Win32_Process', 'matching_processes': [],
               'native_probe_exit': 0, 'command_filter_contains': UID,
               'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
process_empty(observation)
checks.append({'id': 'typed fresh process-empty envelope', 'result': 'PASS_SYNTHETIC'})
for name, change in (('foreign UID', {'run_uuid': 'foreign'}),
                     ('nonzero probe', {'native_probe_exit': 1}),
                     ('matching PID', {'matching_processes': [39468]}),
                     ('stale observation', {'observed_at': '2000-01-01T00:00:00+00:00'})):
    altered = dict(observation, **change)
    refused(name, lambda value=altered: process_empty(value))
entry = next(item for item in tree.body if isinstance(item, ast.If) and
             isinstance(item.test, ast.Compare) and
             isinstance(item.test.left, ast.Name) and
             item.test.left.id == '__name__')
assert (isinstance(entry.body[0], ast.Try) and
        isinstance(entry.body[0].body[0], ast.Assign) and
        isinstance(entry.body[-1], ast.Raise))
passed('success SystemExit outside BaseException handler',
       ast.unparse(entry.body[-1]) == 'raise SystemExit(actual_code)')
body = source.read_text(encoding='utf-8')
passed('postgate process and E/L/export refusal precedes first terminal write',
       body.index('gate_result = gate.validate_grant') <
       body.index('process_empty(strict(reference(options.process_ref)[1]))',
                  body.index('gate_result = gate.validate_grant')) <
       body.index("need(all(not os.path.lexists(path(gate_result['scope'][key], False))") <
       body.index("completed = exclusive(AUTH / 'grant.completed.json'"))
out = {'schema': 'researchos.scope7-recovery-pure-io-controls.v1',
       'checks': checks, 'count': len(checks),
       'gate_executions': 0, 'recovery_executions': 0,
       'Go_executions': 0, 'model_calls': 0, 'Main_writes': 0}
with (HERE / 'precheck.scope7.v5.json').open('xb') as target:
    target.write((json.dumps(out, ensure_ascii=False, sort_keys=True,
                             indent=2) + '\n').encode('utf-8'))
print('SCOPE7_SOURCE_PURE_IO=' + str(len(checks)) + ' FAIL=0')
