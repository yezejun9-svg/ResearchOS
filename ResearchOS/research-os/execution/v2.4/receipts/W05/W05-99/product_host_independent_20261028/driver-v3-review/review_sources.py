"""Independent source-only review; all process and hold-loop effects mocked."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import runpy
import types

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT.parent / 'product_host_native_20261028'
A = NATIVE / 'driver-v3'
B = NATIVE / 'native-init-diagnosis-02' / 'preparation'
OUT_A = ROOT / 'driver-v3-review'
OUT_B = ROOT / 'native-chooser-diagnostic-review'
OUT_B.mkdir(exist_ok=True)

def ref(p):
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

for source, out, names in [(A, OUT_A, ['run-owned.py', 'lifecycle.mjs', 'choose-owned-folder.ps1', 'close-owned-window.ps1', 'PREPARATION.json']), (B, OUT_B, ['diagnose_once.py', 'choose-once.ps1', 'PREPARATION.json'])]:
    snapshots = out / 'input-snapshots'
    snapshots.mkdir(exist_ok=True)
    refs = []
    for name in names:
        p = source / name
        raw = p.read_bytes()
        target = snapshots / name
        if target.exists():
            assert target.read_bytes() == raw
        else:
            target.write_bytes(raw)
        refs.append(ref(p))
    if (out / 'INPUTS.json').exists():
        assert json.loads((out / 'INPUTS.json').read_text(encoding='utf-8')) == refs
    else:
        save(out / 'INPUTS.json', refs)

assert ref(A/'run-owned.py')['sha256'] == '7a24e5fa6af31924058b435a8a6c4b28ad94023a0c97615f9dbf778a6fb3b627'
assert ref(B/'diagnose_once.py')['sha256'] == '7d2a2167b2ebfcf02d4f743785ccc747944b0bcd9fb5f33d9c1f30888e2c343c'
assert ref(B/'choose-once.ps1')['sha256'] == 'f69faab274bfefa1eb53eea480b99e3a5c0d9fc512af8514f9a9a67ee3c92d03'
ga = runpy.run_path(str(A/'run-owned.py'))
gb = runpy.run_path(str(B/'diagnose_once.py'))
ast.parse((A/'run-owned.py').read_text(encoding='utf-8'))
ast.parse((B/'diagnose_once.py').read_text(encoding='utf-8'))

known = [{'pid': 1234, 'image': str(A/'fake-product.exe'), 'created_ns': '100'}]
images = {ga['normpath'](known[0]['image']): known[0]['image']}
reused = {'pid': 1234, 'image': r'C:\Windows\notepad.exe', 'created_ns': '200', 'read_error': None}
visible = ga['blockers']({'status': 'OBSERVED', 'rows': [reused]}, known, images)
filtered = ga['blockers']({'status': 'OBSERVED', 'rows': []}, known, images)
assert 'KNOWN_PID_REUSED_OR_IDENTITY_UNKNOWN:1234' in visible and filtered == []
assert "if ($names -notcontains [string]$item.Name) { continue }" in ga['SCAN_SCRIPT']

class FakeStream:
    def close(self):
        pass

class FakeChild:
    pid = 7654
    def poll(self):
        return None

created = []
fake_subprocess = types.SimpleNamespace(STARTUPINFO=lambda: types.SimpleNamespace(dwFlags=0), STARTF_USESHOWWINDOW=1,
    DEVNULL=-3, Popen=lambda *a, **k: (created.append(FakeChild()) or created[-1]))
launch_globals = gb['launch'].__globals__
launch_globals['open'] = lambda *a, **k: FakeStream()
launch_globals['subprocess'] = fake_subprocess
launch_globals['save'] = lambda *a, **k: (_ for _ in ()).throw(OSError('MOCK_SPAWN_RECEIPT_FAILURE'))
desktop = None
children = []
try:
    desktop = gb['launch'](Path('fake-electron.exe'), [], Path('.'), {}, Path('.'), 'electron')
except OSError as exc:
    launch_error = str(exc)
assert created and desktop is None and children == []

hold_globals = gb['hold'].__globals__
hold_globals['save'] = lambda *a, **k: None
hold_globals['print'] = lambda *a, **k: None
hold_globals['time'] = types.SimpleNamespace(sleep=lambda seconds: (_ for _ in ()).throw(KeyboardInterrupt()))
hold_escaped = False
try:
    gb['hold'](Path('.'), 'mock unresolved', created[0], None, [])
except KeyboardInterrupt:
    hold_escaped = True
assert hold_escaped

common = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewer': 'codex:/root/product_host_independent_20261028',
    'actual_native_runs': 0, 'productCore_runs': 0, 'productElectron_runs': 0, 'formal_increment': 0,
    'methods': ['Exact source hash verification and immutable input copies', 'Python AST parse', 'Exact functions loaded without __main__; process/I/O/sleep mocked for pure probes'],
    'product_acceptance': 'NOT_ASSERTED'}

report_a = dict(common, schema='researchos.independent-native-driver-v3-source-review.v1',
    status='NEEDS_REVISION_BEFORE_SCOPE', driver_source_accepted=False,
    fixed_driver_files=json.loads((OUT_A/'INPUTS.json').read_text(encoding='utf-8')),
    positive_checks=['Scope binds four exact driver files and installed bundle inventory', 'Release binds scope SHA, controller exit SHA, outer/controller PIDs and random nonce', 'Root identity list must match wrapper-derived identities; unknown identity error blocks release', 'Two observations with stable release SHA required; no product terminate/retry operations'],
    findings=[
        {'id':'A1','priority':1,'file':str(A/'run-owned.py'),'lines':'17-18,104-134', 'issue':'Scanner filters by bundled executable names before checking known PIDs. A known PID reused for another executable name is absent from rows, allowing two clean scans despite the stated any-known-PID blocker contract.', 'required':'Include known PIDs regardless of executable name in read-only scan; unknown/reused identity must remain a blocker.', 'proof':{'known_pid':1234, 'unfiltered_blockers':visible, 'name_filtered_blockers':filtered}},
        {'id':'A2','priority':1,'file':str(A/'run-owned.py'),'lines':'181-203,290-304', 'issue':'After controller spawn, exit/spawn/waiting receipt writes and print are outside a fail-preserving guard. An I/O or broken-output exception can terminate the wrapper before reconciliation, contradicting its main purpose.', 'required':'Establish a post-spawn catch/hold boundary that cannot exit on diagnostic I/O failure; retain original controller result and require reconciled release even when reporting fails.'}
    ], limitations=['No actual process inventory, native GUI, Win32 pipe or external host/job lifetime exercised. Existing v2 lifecycle/helpers are byte-identical and inherited from prior source review only.'])
save(OUT_A/'REVIEW.json', report_a)

report_b = dict(common, schema='researchos.independent-native-chooser-diagnostic-source-review.v1',
    status='NEEDS_REVISION_BEFORE_NATIVE_DIAGNOSIS', diagnostic_source_accepted=False,
    fixed_files=json.loads((OUT_B/'INPUTS.json').read_text(encoding='utf-8')),
    positive_checks=['Fresh isolated profile/workspace and exact candidate/bundle hashes checked before launch', 'One NativeWorkspaceChoose request frame; raw request and full raw reply retained including error.message', 'Named pipe server PID checked before request and after reply; core image/creation/hash and witness continuity checked', 'Helper timeout reaches hold without retry or forced product termination; close uses existing identity-bound WM_CLOSE helper'],
    findings=[
        {'id':'B1','priority':1,'file':str(B/'diagnose_once.py'),'lines':'87-101,170-171,191-200', 'issue':'Popen is followed by spawn receipt I/O before returning the handle; caller only then assigns desktop or appends children. A receipt exception leaves a live child missing from the holding registry.', 'required':'Register the child handle/identity in a shared registry immediately after successful spawn, before any fallible receipt operations; failure path uses that registry.', 'proof':{'spawn_count':len(created), 'error':launch_error, 'desktop_registered':desktop is not None, 'children_registered':len(children)}},
        {'id':'B2','priority':1,'file':str(B/'diagnose_once.py'),'lines':'60-75,236-238', 'issue':'hold has no validated Root release or independently observed absence exit path. Its own save/print or sleep interruption can escape, so it both lacks safe reconciliation and fails its stay-alive contract.', 'required':'Use the corrected shared Root-release contract with bundle and known-PID observations, repeated clean scans and resilient diagnostics; never exit on unresolved or reporting failures.', 'proof':{'mock_keyboard_interrupt_escaped_hold':hold_escaped}},
        {'id':'B3','priority':2,'file':str(B/'diagnose_once.py'),'lines':'226-235', 'issue':'RESULT proves only pair absence after WM_CLOSE, without desktop returncode or witness retirement. It must not be promoted to clean product shutdown.', 'required':'Explicitly label only pair absence, or additionally prove zero desktop exit and retired witness before claiming clean shutdown.'}
    ], limitations=['PowerShell synchronous pipe read has no internal timeout; Python observes 60 seconds then retains client and product processes in hold. This is intentional unresolved behavior, not a completed exchange.', 'No native action authorized by this review; no live pipe, chooser, WM_CLOSE or real process observed.'])
save(OUT_B/'REVIEW.json', report_b)
print(json.dumps({'A':ref(OUT_A/'REVIEW.json'), 'B':ref(OUT_B/'REVIEW.json'), 'native_runs':0}, ensure_ascii=False))
