import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
request = json.load(sys.stdin)
root = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
out = pathlib.Path(__file__).resolve().parent
label = request['label']
if not label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in label):
    raise ValueError('unsafe receipt label')
if request.get('language') == 'python':
    args = [sys.executable, '-X', 'utf8', '-c', request['script']]
else:
    script = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); " + request['script']
    args = ['powershell', '-NoProfile', '-Command', script]
result = subprocess.run(args, cwd=root, capture_output=True)
for suffix, raw in [('stdout.raw', result.stdout), ('stderr.raw', result.stderr)]:
    with (out / (label + '.' + suffix)).open('xb') as stream:
        stream.write(raw)
recipe = {'schema': 'researchos.readonly-command.v1', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'args': args, 'cwd': str(root), 'native_exit': result.returncode,
          'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
          'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()}
with (out / (label + '.invocation.json')).open('x', encoding='utf-8') as stream:
    json.dump(recipe, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(result.stdout.decode('utf-8', errors='strict'))
print(result.stderr.decode('utf-8', errors='strict'))
print('native_exit=' + str(result.returncode))
