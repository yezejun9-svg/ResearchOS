from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path(__file__).resolve().parent
repo = Path('D:/作品集/ResearchOS/research-os')
package = Path('C:/nvm4w/nodejs/node_modules/@earendil-works/pi-coding-agent')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert not (root / 'public-inventory.json').exists()
metadata = json.loads((package / 'package.json').read_text(encoding='utf-8'))
assert metadata['name'] == '@earendil-works/pi-coding-agent' and metadata['version'] == '0.99.2'
plan = json.loads((repo / 'execution/product-v1/plan.json').read_text(encoding='utf-8'))
registered = json.loads((repo / 'execution/product-v1/evidence.json').read_text(encoding='utf-8'))
paths = ['package.json','README.md','npm-shrinkwrap.json','docs/cli.md','docs/rpc.md','docs/rpc-commands.md','docs/json.md',
         'dist/bundle/cli.js','dist/bundle/cli-runtime.js','dist/bundle/rpc-entry.js','dist/cli.js','dist/main.js','dist/rpc-entry.js',
         'dist/cli/args.js','dist/cli/auth-command.js','dist/cli/auth-check.js','dist/core/auth-storage.js',
         'dist/core/resolve-config-value.js','dist/core/model-runtime.js','dist/core/agent-session.js',
         'dist/core/settings-manager.js','dist/core/tools/read.js','dist/core/tools/path-utils.js','dist/modes/rpc/rpc-mode.js']
sources = []
registered_by_path = {row['path'].replace('\\','/').lower():row for row in registered['sources']}
for name in paths:
    path = package / name
    digest = sha(path)
    prior = registered_by_path.get(path.as_posix().lower())
    sources.append({'path':str(path),'sha256':digest,'bytes':path.stat().st_size,
                    'registered_source_sha256':prior['sha256'] if prior else None,
                    'registered_pin_matches':digest == prior['sha256'] if prior else None})
for name in ['docs/product-v1/PLAN.md','execution/product-v1/plan.json','execution/product-v1/evidence.json',
             'execution/product-v1/contracts/harness.v1.interface.rev2.json']:
    path = repo / name
    sources.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'role':'public_project_plan_or_contract'})
for path in [Path('C:/nvm4w/nodejs/pi.cmd'), Path('C:/nvm4w/nodejs/pi.ps1'), Path('C:/nvm4w/nodejs/node.exe')]:
    sources.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'role':'public_tool_or_shim'})

# Pin public bundled code, without importing it or copying its dependency tree.
bundle_files = sorted((package / 'dist/bundle').rglob('*.js'))
bundle_bytes = sum(path.stat().st_size for path in bundle_files)
assert bundle_bytes < 128 * 1024 * 1024
bundle = [{'path':path.relative_to(package).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size} for path in bundle_files]
deps = []
for name, requirement in metadata['dependencies'].items():
    path = package / 'node_modules' / name / 'package.json'
    if path.is_file():
        entry = json.loads(path.read_text(encoding='utf-8'))
        deps.append({'name':name,'requirement':requirement,'installed_version':entry.get('version'),'license_declaration':entry.get('license'),'package_sha256':sha(path),'present_at_package_dependency_path':True})
    else:
        deps.append({'name':name,'requirement':requirement,'present_at_package_dependency_path':False,'note':'May be bundled or resolved from an ancestor; no runtime import was attempted.'})

excerpts = {
    'dist/main.js':[(99,166),(442,499),(692,710)],
    'dist/cli/args.js':[(253,325)],
    'dist/cli/auth-check.js':[(1,55)],
    'dist/core/auth-storage.js':[(157,218)],
    'dist/core/agent-session.js':[(2525,2535),(3010,3020)],
    'dist/core/settings-manager.js':[(647,660)],
    'dist/core/tools/read.js':[(9,19),(42,70)],
    'dist/core/tools/path-utils.js':[(37,56)],
    'dist/modes/rpc/rpc-mode.js':[(292,361),(419,435),(579,653)],
}
selected = []
for name, ranges in excerpts.items():
    lines = (package / name).read_text(encoding='utf-8').splitlines()
    selected.append({'source':name,'source_sha256':sha(package/name),'excerpts':[{'first_line':a,'last_line':b,'text':'\n'.join(lines[a-1:b])} for a,b in ranges]})
(root / 'public-source-excerpts.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

ui_root = root.parent / 'product-v1-workbench-author-revision-02'
assert sha(ui_root/'FROZEN.json') == 'ce09b6e7db586688899cab7e3653bfebb93d15e0bb3a0b45078d3f6f882cb817'
ui = json.loads((ui_root/'FROZEN.json').read_text(encoding='utf-8'))
ui_pins = ui['source_sha256'] | ui['test_sha256']
ui_unchanged = all(sha(Path(ui['worktree'])/name) == digest for name,digest in ui_pins.items())
report = {'at':datetime.now(timezone.utc).isoformat(),'method':'PUBLIC_PACKAGE_AND_PROJECT_SOURCE_READS_ONLY',
          'package':{'name':metadata['name'],'version':metadata['version'],'license':metadata['license'],'engines':metadata['engines'],'bin':metadata['bin'],'path':str(package)},
          'sources':sources,'bundle':{'files':bundle,'file_count':len(bundle),'bytes':bundle_bytes,'imported_or_executed':False},
          'direct_dependency_metadata':deps,'root_license_files':[path.name for path in package.iterdir() if path.is_file() and path.name.lower().startswith(('license','notice','copying'))],
          'plan':{'first_harness':plan['first_harness'],'second_harness':plan['second_harness'],'slices':[item for item in plan['slices'] if item['id'] in ['S05','S06','S07','S08']]},
          'ui_freeze02':{'path':str(ui_root/'FROZEN.json'),'sha256':sha(ui_root/'FROZEN.json'),'all_live10_unchanged':ui_unchanged},
          'pi_cli_processes_started':0,'auth_status_commands_run':0,'model_or_api_calls':0,'d_source_writes':0,'user_auth_config_files_read_or_copied':0}
assert ui_unchanged
(root/'public-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'public_sources':len(sources),'bundle_files':len(bundle),'bundle_bytes':bundle_bytes,'registered_pin_mismatches':[row['path'] for row in sources if row.get('registered_pin_matches') is False],'ui_live10_unchanged':ui_unchanged,'root_license_files':report['root_license_files']}))
