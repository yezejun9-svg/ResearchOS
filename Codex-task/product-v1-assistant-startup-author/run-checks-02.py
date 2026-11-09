import hashlib, json, subprocess
from pathlib import Path
ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-assistant-home-20261104')
BASE = Path(__file__).resolve().parent
directory = BASE / 'checks-02-public-spec'
directory.mkdir(exist_ok=False)
argv = ['C:/nvm4w/nodejs/node.exe', '--require', str(BASE/'resolve-public-spec.cjs'), '--test', '--test-reporter=tap', '--test-name-pattern=^first use consumes native choice', 'tests/ui/desktop/w13-react.test.js']
spec = Path('D:/作品集/ResearchOS/research-os/spec/v2.0/contracts/openapi.json')
(directory/'command.json').write_text(json.dumps({'argv':argv,'cwd':str(ROOT),'public_spec':str(spec),'public_spec_sha256':hashlib.sha256(spec.read_bytes()).hexdigest(),'source_modified':False,'note':'Same selected existing pure first-use fixture, only missing sparse-tree static public spec dependency resolved from Main.'},ensure_ascii=True,indent=2),encoding='utf-8')
r = subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60)
(directory/'stdout.raw').write_bytes(r.stdout)
(directory/'stderr.raw').write_bytes(r.stderr)
(directory/'result.json').write_text(json.dumps({'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()},indent=2),encoding='utf-8')
print(json.dumps({'exit_code':r.returncode,'stdout':r.stdout.decode('utf-8',errors='replace')}))
raise SystemExit(r.returncode)
