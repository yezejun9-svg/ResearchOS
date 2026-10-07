"""Run the three exact current selectors and retain every dispatcher byte."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CARD = HERE.parent

def load(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

binding = load(HERE / 'binding_codex.json')
registry = ROOT / 'execution/v2.4/commands.json'
assert sha(registry) == binding['registry_sha256']
assert load(registry)['revision'] == 35
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
out = HERE / ('registered-root-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:12])
out.mkdir(exist_ok=False)
rows = []
for selector in ('W02-G01', 'W02-G02', 'W02-G03'):
    argv = [sys.executable, '-B', '-X', 'utf8',
        str(ROOT / 'execution/command_dispatcher/dispatch.py'), 'build.check',
        '--task-id', 'W02', '--check-id', selector, '--spec', 'v2.4']
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=650)
    (out / (selector + '.stdout.txt')).write_bytes(result.stdout)
    (out / (selector + '.stderr.txt')).write_bytes(result.stderr)
    launch = {'selector': selector, 'argv': argv, 'exit_code': result.returncode}
    save(out / (selector + '.launch.json'), launch)
    assert result.returncode == 0, selector + ': original output retained'
    emitted = json.loads(result.stdout)
    original = Path(emitted['receipt'])
    receipt = load(original)
    assert receipt['code_revision'] == head
    assert receipt['selectors'] == {'task_id': 'W02', 'check_id': selector, 'case_id': ''}
    assert receipt['registered_command_revision'] == sha(registry)
    assert receipt['status'] == 'PASS' and receipt['child_exit_code'] == 0
    child_stdout = ROOT / receipt['stdout']['path']
    child_stderr = ROOT / receipt['stderr']['path']
    assert sha(child_stdout) == receipt['stdout']['sha256']
    assert sha(child_stderr) == receipt['stderr']['sha256']
    report = load(child_stdout)
    child = Path(report['receipt'])
    child_report = load(child)
    assert child_report['check_id'] == selector and child_report['status'] == 'PASS'
    assert report['assertion_ids'] == receipt['assertion_ids']
    ids = receipt['assertion_ids']
    assert ids and len(ids) == len(set(ids))
    assert all(x == selector or x.startswith(selector + '-') for x in ids)
    assert child_report['owned_acceptance_ids'] == child_report['formal_cases_accepted'] == []
    mirror = CARD / 'registered-dispatch' / receipt['invocation_id']
    mirror.mkdir(parents=True, exist_ok=False)
    for source, name in ((original, 'receipt.json'), (child_stdout, 'stdout.txt'), (child_stderr, 'stderr.txt')):
        shutil.copyfile(source, mirror / name)
        assert source.read_bytes() == (mirror / name).read_bytes()
    rows.append({**launch, 'dispatcher': emitted, 'dispatcher_receipt_sha256': sha(original),
        'mirror_path': mirror.relative_to(ROOT).as_posix(),
        'child_exit_code': receipt['child_exit_code'], 'assertion_ids': ids,
        'child_receipt': str(child), 'child_receipt_sha256': sha(child),
        'child_manifest_sha256': sha(child.parent / 'manifest.json')})
    print(json.dumps({'selector': selector, 'status': 'PASS', 'invocation_id': receipt['invocation_id'],
                      'dispatch_assertions': len(ids)}), flush=True)
save(HERE / 'exact_dispatch_results.json', {
    'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'actor': 'codex:/root',
    'source_head': head, 'registry_revision': 35, 'registry_sha256': sha(registry),
    'raw_root_launch_dir': out.relative_to(ROOT).as_posix(), 'actual_registered_selectors': rows,
    'interpretation': 'G01/G03 strictly revalidate unchanged inputs and archived actual results; '
        'G02 observes current registration and mapping. Aggregation assertions do not add product tests. '
        'No formal-case/whole-card acceptance before independent review.',
    'new_provider_calls': 0, 'new_service_operations': 0, 'new_gui_operations': 0,
})
