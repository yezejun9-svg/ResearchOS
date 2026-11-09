from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parent
directory = root / sys.argv[1]
directory.mkdir(exist_ok=False)
wt = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-workbench-20261104')
scope = json.loads(Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/workbench/scope.json').read_text(encoding='utf-8-sig'))
git = Path('C:/Program Files/Git/cmd/git.exe')
assert hashlib.sha256(git.read_bytes()).hexdigest() == 'da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f'
results = []
for index, args in enumerate([['diff', '--check'], ['status', '--short', '--untracked-files=all', '-z'], ['diff', '--stat']], 1):
    argv = [str(git), '-C', str(wt), *args]
    (directory / f'{index:02}.command.json').write_text(json.dumps(argv, ensure_ascii=False) + '\n', encoding='utf-8')
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    (directory / f'{index:02}.stdout').write_bytes(result.stdout)
    (directory / f'{index:02}.stderr').write_bytes(result.stderr)
    results.append({'command': index, 'exit_code': result.returncode})
    if index == 2:
        changed = sorted(record[3:].decode('utf-8') for record in result.stdout.split(b'\0') if record)
expected = sorted(scope['production_paths'] + scope['test_paths'])
report = {'commands': results, 'changed': changed, 'expected': expected, 'exact_scope': changed == expected}
(directory / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
raise SystemExit(0 if all(row['exit_code'] == 0 for row in results) and changed == expected else 1)
