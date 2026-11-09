"""Review frozen diagnostic revision with pure mocks; never runs native main."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent.parent / 'product_host_native_20261028' / 'native-init-diagnosis-02' / 'preparation' / 'revision01'
OUT = ROOT / 'revision01-4bfabee8'
OUT.mkdir(exist_ok=False)
SNAP = OUT / 'input-snapshots'
SNAP.mkdir()

def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(name, value):
    with (OUT/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

inputs = []
for name in ('diagnose_once.py', 'choose-once.ps1', 'test_mock.py', 'PREPARATION.json'):
    raw = (SOURCE/name).read_bytes()
    (SNAP/name).write_bytes(raw)
    inputs.append(ref(SOURCE/name))
assert inputs[0]['sha256'] == '4bfabee8223c0737233ea20b55b2d53bcc055a549531b74659c0a8e65e0783b9'
assert inputs[1]['sha256'] == 'f69faab274bfefa1eb53eea480b99e3a5c0d9fc512af8514f9a9a67ee3c92d03'
assert inputs[3]['sha256'] == 'a2ac45c0e646762b1a4b3d3b52feb423b41f21960496ee700a4f1b8424fec9f2'
save('INPUTS.json', inputs)
source = (SNAP/'diagnose_once.py').read_text(encoding='utf-8')
ast.parse(source)
argv = [sys.executable, str(SNAP/'test_mock.py'), '-v']
result = subprocess.run(argv, capture_output=True, check=False)
(OUT/'author-mock.stdout.raw').write_bytes(result.stdout)
(OUT/'author-mock.stderr.raw').write_bytes(result.stderr)
save('AUTHOR-MOCK-COMMAND.json', {'argv':argv, 'exit':result.returncode, 'real_product_processes':0,
    'stdout':ref(OUT/'author-mock.stdout.raw'), 'stderr':ref(OUT/'author-mock.stderr.raw')})
assert result.returncode == 0, result.stderr

g = runpy.run_path(str(SNAP/'diagnose_once.py'))
fn = g['scan_once']
captured = {}
def fake_run(*args, **kwargs):
    captured.update(kwargs)
    return type('Result', (), {'returncode':0, 'stdout':'[]', 'stderr':''})()
known = [{'pid':1234, 'image':g['normpath']('C:/bundle/electron.exe'), 'created_ns':'100', 'role':'electron'}]
images = [known[0]['image']]
with mock.patch.object(fn.__globals__['subprocess'], 'run', side_effect=fake_run):
    observation = fn(Path('C:/fake/pwsh.exe'), Path('C:/bundle'), images, known)
assert observation == {'status':'OBSERVED', 'rows':[]}
assert json.loads(captured['env']['ROS_SCAN_KNOWN_PIDS_JSON']) == [1234]
assert '-and $known -notcontains [int]$item.ProcessId' in g['SCAN_SCRIPT']
assert g['scan_blockers']({'status':'UNKNOWN'}, images, known) == ['SCAN_UNKNOWN']
reused = {'pid':1234, 'image':'C:/Windows/notepad.exe', 'created_ns':'200', 'read_error':None}
assert 'KNOWN_PID_REUSED_OR_UNKNOWN:1234' in g['scan_blockers']({'status':'OBSERVED','rows':[reused]}, images, known)

waiting = {'scope_sha256':'scope', 'controller_pid':77, 'release_nonce':'nonce', 'known_identities':known,
           'at':'2026-10-28T00:00:00+00:00'}
value = {'schema':'researchos.native-chooser-root-release.v1','actor':'codex:/root',
         'scope_sha256':'scope','controller_pid':77,'release_nonce':'nonce','known_identities':known,
         'root_confirmed_identity_absence':True,'confirmed_absent_at':'2026-10-28T00:00:01+00:00'}
cases = []
for label, key, invalid in [('wrong_actor','actor','other'), ('wrong_scope','scope_sha256','wrong'),
                            ('wrong_pid','controller_pid',78), ('empty_known_list','known_identities',[]),
                            ('premature_time','confirmed_absent_at','2026-10-27T00:00:00+00:00')]:
    candidate = dict(value)
    candidate[key] = invalid
    path = OUT/(label+'.fixture.json')
    path.write_text(json.dumps(candidate), encoding='utf-8')
    try:
        g['validate_root_release'](path, waiting)
    except RuntimeError as error:
        cases.append({'case':label, 'rejected':True, 'error':str(error)})
    else:
        raise AssertionError('Accepted invalid release '+label)
save('INDEPENDENT-PROBES.json', {'status':'PURE_PROBES_PASS','author_pure_mock_cases':5,
    'known_pid_passed_to_scanner':True,'known_pid_reuse_blocks_release':True,'unknown_scan_blocks_release':True,
    'negative_release_cases':cases,'real_product_processes':0,'native_runs':0})

report = {'schema':'researchos.independent-native-chooser-diagnostic-source-review.v2',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'SOURCE_ACCEPTED_FOR_ONE_NEW_EXACT_BOUND_DIAGNOSTIC_SCOPE',
    'diagnostic_source_accepted':True,'actual_native_runs':0,'formal_increment':0,
    'fixed_files':inputs, 'findings':[],
    'resolved_findings':[
        'B1: argv and image resolved before Popen; next statement registers process handle globally before stream-close or receipt I/O; original exception paths reproduced with pure mocks.',
        'B2: hold catches reporting/scan/interrupt errors; Root release binds scope/PID/nonce/exact known list and time; exact bundle paths plus all known PIDs independently scanned twice; missing log blocks count; wrong scope/actor/PID/known list/time rejected.',
        'B3: normal-close result now requires WM_CLOSE receipt, pair absence, desktop exit0 and retired witness; pair absence without these enters hold and is not clean close.'
    ],
    'request_boundary':'At most one NamedPipe NativeWorkspaceChoose frame; no model call, retry, credential access, kill or product relaunch. Raw reply retains error.message. Existing pipe PID/image/creation/hash/witness guards unchanged.',
    'scope_requirements':[
        'Root issues a fresh exact scope binding these final revision01 hashes, unchanged driver-v2 chooser/close helpers and accepted build05 marker; fresh isolated state and receipt roots.',
        'Run plain Python without -O or inherited PYTHONOPTIMIZE because input guards use assert; record interpreter and scope hash.',
        'A completed clean close is separate from successful diagnostic exchange; inspect raw reply and helper exits even when controller exits0.',
        'If hold occurs, Root uses researchos.native-chooser-root-release.v1 from this source; it is intentionally distinct from the outer lifecycle-wrapper schema.',
        'This review authorizes no actual native action itself; parent must separately scope the single diagnostic, not full lifecycle.'
    ],
    'limitations':[
        'No real product, pipe, GUI, WM_CLOSE or CIM scan was executed; source/fixture acceptance only.',
        'Pipe read is synchronous and may remain blocked; controller reaches hold at60seconds without terminating it. Root reconciliation must independently resolve all known children.',
        'Inaccessible process identities or corrupt identity evidence prevent release; external host/job termination remains outside this script proof.',
        'Author changed revision01 during initial inspection; only final4bfabee8 source is accepted and copied into immutable reviewer snapshots.'
    ],
    'evidence_refs':[ref(OUT/'INPUTS.json'),ref(OUT/'AUTHOR-MOCK-COMMAND.json'),ref(OUT/'INDEPENDENT-PROBES.json')]
}
save('REVIEW.json',report)
print(json.dumps(ref(OUT/'REVIEW.json'),ensure_ascii=False))
