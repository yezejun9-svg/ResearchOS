import argparse, datetime, hashlib, json, pathlib, subprocess, sys

BASE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path('D:/作品集/ResearchOS/research-os')
p = argparse.ArgumentParser()
p.add_argument('--id', required=True)
p.add_argument('--recipe', required=True)
a = p.parse_args()
recipe = (BASE / a.recipe).resolve()
if not recipe.is_relative_to(BASE):
    raise SystemExit('recipe outside ownE')
command = recipe.read_text(encoding='utf-8')
record = {'id': a.id, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'recipe': str(recipe), 'recipe_sha256': hashlib.sha256(recipe.read_bytes()).hexdigest(), 'command': command, 'cwd': str(REPO), 'status': 'PREWRITTEN'}
pre = BASE / (a.id + '-command.json')
with pre.open('x', encoding='utf-8') as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
with (BASE / 'command-index.jsonl').open('a', encoding='utf-8') as f:
    f.write(json.dumps(record, ensure_ascii=False) + '\n')
try:
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=55)
    stdout, stderr, code = result.stdout, result.stderr, result.returncode
    state = 'SUCCESS' if code == 0 else 'FAILED'
except subprocess.TimeoutExpired as e:
    stdout, stderr, code, state = e.stdout or b'', e.stderr or b'', None, 'TIMEOUT'
out = BASE / (a.id + '-stdout.txt')
err = BASE / (a.id + '-stderr.txt')
out.write_bytes(stdout)
err.write_bytes(stderr)
entry = {'id': a.id, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': state, 'exit_code': code, 'stdout_sha256': hashlib.sha256(stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr).hexdigest()}
with (BASE / 'ledger.jsonl').open('a', encoding='utf-8') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
sys.stdout.write(stdout.decode('utf-8', errors='backslashreplace'))
sys.stderr.write(stderr.decode('utf-8', errors='backslashreplace'))
print(json.dumps(entry))
raise SystemExit(0 if code == 0 else 1)
