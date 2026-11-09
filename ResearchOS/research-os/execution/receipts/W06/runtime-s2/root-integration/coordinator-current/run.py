import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parents[6]
out = Path(__file__).resolve().parent
go = root / '.local/tools/go1.27.1/go/bin/go.exe'
binary = root / '.local/runtime-s2-root-control.exe'
assert not binary.exists()
env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RUNTIME_CONTROL_BINARY=str(binary),
           W10_EVIDENCE_DIR=str(out / 'W10'), W16_EVIDENCE_DIR=str(out / 'W16'),
           RESEARCHOS_C22_EVIDENCE=str(out / 'C22'))
for name in ('W10', 'W16', 'C22'):
    (out / name).mkdir(exist_ok=False)
source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
pattern = '^(TestRuntimeCoordinator(NativeQualification|ReadyToIndependentAcceptance|TypedBroker|CheckpointResume|FailedExitReleasesExecutor|SkipsUnrelatedReady|ConcurrentSealConflict|ControlStartup|CrashRecovery)|TestW17C22ProtectedIsolation|TestW10NativePair|TestW16C20|TestRuntimeSandbox(StartCancellationCleanup|IdentityJSONExact))$'
commands = [
    ('build', [str(go), 'build', '-o', str(binary), './apps/control']),
    ('test', [str(go), 'test', '-json', '-count=1', '-timeout=120s', '-run', pattern,
              './internal/domain', './ops/experiment_sandbox']),
]
report = {'source_revision': source, 'scope': 'Root main integration, normal lifecycle and previously accepted fixture consumers only',
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'commands': [],
          'blocked_adversarial_review_retried': False, 'LIVE_qualified': False, 'formal_case_count_changed': False}
try:
    for name, command in commands:
        started = time.monotonic()
        p = subprocess.run(command, cwd=root, env=env, capture_output=True)
        (out / (name + '.stdout.log')).write_bytes(p.stdout)
        (out / (name + '.stderr.log')).write_bytes(p.stderr)
        report['commands'].append({'name': name, 'argv': command, 'exit_code': p.returncode, 'seconds': time.monotonic() - started})
        if name == 'build' and p.returncode == 0:
            report['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        if name == 'test':
            events = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
            for action in ('run', 'pass', 'skip', 'fail'):
                report[action] = [x['Test'] for x in events if x.get('Test') and x.get('Action') == action]
        if p.returncode:
            break
finally:
    if binary.exists():
        binary.unlink()
    report['temporary_binary_removed'] = not binary.exists()
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
assert all(x['exit_code'] == 0 for x in report['commands']) and report.get('pass') and not report.get('fail') and not report.get('skip')
