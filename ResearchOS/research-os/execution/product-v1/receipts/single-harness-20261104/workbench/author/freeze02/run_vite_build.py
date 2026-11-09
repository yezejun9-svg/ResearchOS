from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parent
wt = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-workbench-20261104')
repo = Path('D:/作品集/ResearchOS/research-os')
node = Path('C:/nvm4w/nodejs/node.exe')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(node) == '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
directory = root / sys.argv[1]
directory.mkdir(exist_ok=False)
tree = directory / 'source'
inputs = [wt / 'apps/web/package.json', wt / 'apps/web/index.html', wt / 'apps/desktop/main/lib/wire-values.mjs']
tokens = wt / 'spec/v2.0/ui/design-tokens.json'
inputs.append(tokens if tokens.exists() else repo / 'spec/v2.0/ui/design-tokens.json')
inputs += [p for p in (wt / 'apps/web/src').rglob('*') if p.is_file()]
inventory = []
for source in inputs:
    relative = source.relative_to(wt) if source.is_relative_to(wt) else source.relative_to(repo)
    target = tree / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    inventory.append({'path': relative.as_posix(), 'source_path': str(source), 'sha256': sha(source), 'copied_sha256': sha(target)})
modules = repo / 'apps/web/node_modules'
aliases = [
    {'find': 'react-dom/client', 'replacement': (modules / 'react-dom/client.js').as_posix()},
    {'find': 'react/jsx-runtime', 'replacement': (modules / 'react/jsx-runtime.js').as_posix()},
    {'find': 'react', 'replacement': (modules / 'react/index.js').as_posix()},
]
config = directory / 'vite.config.mjs'
config.write_text('export default ' + json.dumps({'resolve': {'alias': aliases}}, ensure_ascii=False) + '\n', encoding='utf-8')
vite = modules / 'vite/bin/vite.js'
argv = [str(node), str(vite), 'build', str(tree / 'apps/web'), '--config', str(config), '--outDir', str(directory / 'dist')]
(directory / 'command.json').write_text(json.dumps({'argv': argv, 'cwd': str(root), 'inputs': inventory, 'vite_bin_sha256': sha(vite), 'note': 'Exact production source copies; pinned existing local modules, no install/download/app/model. Only resolver aliases differ to bind cache without creating links in the source WT.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (directory / 'stdout').open('wb') as stdout, (directory / 'stderr').open('wb') as stderr:
    result = subprocess.run(argv, cwd=root, stdout=stdout, stderr=stderr, timeout=120)
after = [{'path': item['path'], 'matched': sha(Path(item['source_path'])) == item['sha256']} for item in inventory]
outputs = [{'path': p.relative_to(directory).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in (directory / 'dist').rglob('*') if p.is_file()]
report = {'exit_code': result.returncode, 'all_source_unchanged': all(item['matched'] for item in after), 'source_readback': after, 'outputs': outputs, 'real_app_or_model_run': False}
(directory / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'exit_code': result.returncode, 'all_source_unchanged': report['all_source_unchanged'], 'output_files': len(outputs)}))
raise SystemExit(result.returncode if report['all_source_unchanged'] else 2)
