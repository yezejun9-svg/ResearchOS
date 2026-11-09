from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parent
wt = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-workbench-20261104')
node = Path('C:/nvm4w/nodejs/node.exe')
assert hashlib.sha256(node.read_bytes()).hexdigest() == '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
directory = root / sys.argv[1]
directory.mkdir(exist_ok=False)
scope = json.loads(Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/workbench/scope.json').read_text(encoding='utf-8-sig'))
source_names = scope['production_paths'] + scope['test_paths'] + ['tests/ui/desktop/activity-projection.test.mjs', 'apps/desktop/main/lib/http-wire.js']
pins = {name: hashlib.sha256((wt / name).read_bytes()).hexdigest() for name in source_names}
(directory / 'source-pins.json').write_text(json.dumps(pins, indent=2) + '\n', encoding='utf-8')
commands = [
    ['--check', 'apps/desktop/main/main.js'],
    ['--check', 'apps/desktop/main/lib/ipc.js'],
    ['--check', 'apps/desktop/main/lib/harness-wire.js'],
    ['--check', 'apps/desktop/preload/preload.js'],
    ['--test', '--test-concurrency=1', 'tests/ui/desktop/harness-workbench.test.mjs', 'tests/ui/harness-bridge-fixture.cjs', 'tests/ui/desktop/activity-projection.test.mjs'],
]
results = []
for index, arguments in enumerate(commands, 1):
    argv = [str(node), *arguments]
    (directory / f'{index:02}.command.json').write_text(json.dumps({'argv': argv, 'cwd': str(wt)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (directory / f'{index:02}.stdout').open('wb') as stdout, (directory / f'{index:02}.stderr').open('wb') as stderr:
        result = subprocess.run(argv, cwd=wt, stdout=stdout, stderr=stderr, timeout=90)
    results.append({'command': index, 'exit_code': result.returncode})
    (directory / 'results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results))
readback = {name: hashlib.sha256((wt / name).read_bytes()).hexdigest() == digest for name, digest in pins.items()}
(directory / 'source-readback.json').write_text(json.dumps(readback, indent=2) + '\n', encoding='utf-8')
raise SystemExit(0 if all(item['exit_code'] == 0 for item in results) and all(readback.values()) else 1)
