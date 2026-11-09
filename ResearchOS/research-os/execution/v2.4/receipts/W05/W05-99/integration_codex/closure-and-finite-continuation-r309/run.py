import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
assert len(sys.argv) == 3
review_path = Path(sys.argv[1]).resolve()
assert review_path.is_relative_to(ROOT / 'execution/v2.4/receipts/W05/W05-99/root_registration_r309_readonly_review_codex')
review_raw = review_path.read_bytes()
assert hashlib.sha256(review_raw).hexdigest() == sys.argv[2]
review = json.loads(review_raw)
prepared_raw = (OUT / 'prepared_refs.json').read_bytes()
prepared = json.loads(prepared_raw)
runner = OUT / 'register.py'
assert review['schema'] == 'researchos.root-registration-source-review.v1'
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION'
assert review['requested_changes'] == [] and review['actual_registration_executed'] is False
assert review['expected_before'] == [308, 136, 371] and review['expected_after'] == [309, 137, 379]
for key, path in [('register_sha256', runner), ('wrapper_sha256', Path(__file__)),
                  ('prepared_refs_sha256', OUT / 'prepared_refs.json'), ('audit_sha256', OUT / 'audit.json')]:
    assert review[key] == hashlib.sha256(path.read_bytes()).hexdigest()
assert review['canonical_before'] == prepared['canonical_before']
assert len(review['copied_canonical_before_refs']) == 4
for original, copied in zip(prepared['canonical_before'], review['copied_canonical_before_refs']):
    copied_path = (ROOT / copied['path']).resolve()
    assert copied_path.is_relative_to(review_path.parent)
    copied_raw = copied_path.read_bytes()
    assert copied['sha256'] == original['sha256'] == hashlib.sha256(copied_raw).hexdigest()
    assert copied['bytes'] == original['bytes'] == len(copied_raw)
    assert copied_raw == (ROOT / original['path']).read_bytes()
for item in prepared['canonical_before']:
    raw = (ROOT / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256'] and len(raw) == item['bytes']
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
assert cp['revision'] == 308 and len(cp['failure_counters']) == 371
assert cp['plan_sha256'] == 'a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17'
assert cp['spec_manifest_sha256'] == '4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
for key in ['python', 'git']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
git = lock['git']['path']
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == prepared['head']
assert hashlib.sha256(subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)).hexdigest() == prepared['git_status_sha256']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
argv = [sys.executable, '-I', str(runner)]
env = {key: value for key, value in os.environ.items() if key.upper() not in {'PYTHONOPTIMIZE', 'PYTHONPATH'}}
with (OUT / 'stdout.raw').open('xb') as stdout, (OUT / 'stderr.raw').open('xb') as stderr:
    child = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
record = {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'started_at': started,
    'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_exit': child.returncode,
    'review_ref': {'path': review_path.relative_to(ROOT).as_posix(), 'sha256': sys.argv[2], 'bytes': len(review_raw)},
    'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(), 'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'all_four_reviewed_metadata_pins_checked_before_launch': True,
    'stdout_sha256': hashlib.sha256((OUT / 'stdout.raw').read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256((OUT / 'stderr.raw').read_bytes()).hexdigest(), 'automatic_retry': False, 'counter_reset': False}
with (OUT / 'invocation.json').open('xb') as stream:
    stream.write((json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps({'actual_exit': child.returncode, 'stderr_tail_display_only': (OUT / 'stderr.raw').read_bytes().decode('utf-8', errors='replace')[-1800:],
    'stdout_display': (OUT / 'stdout.raw').read_bytes().decode('utf-8', errors='replace')}, ensure_ascii=True))
sys.exit(child.returncode)
