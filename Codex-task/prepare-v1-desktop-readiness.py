"""Readonly public resource discovery; writes only C reports, never builds/runs."""
from datetime import datetime,timezone
import hashlib,json,shutil
from pathlib import Path
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp605-desktop-resource-readiness')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(value,dict):json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
        else:f.write(value)
assert not OUT.exists(),'Existing result: read back, do not replay'
OUT.mkdir()
tools=[]
for name,version,path in [
    ('Python','3.14.3','C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'),
    ('Node','24.9.0','C:/nvm4w/nodejs/node.exe'),
    ('npm CLI','11.6.0','C:/nvm4w/nodejs/node_modules/npm/bin/npm-cli.js'),
    ('Go','1.27.1',str(MAIN/'.local/tools/go1.27.1/go/bin/go.exe')),
    ('Electron','37.10.3',str(MAIN/'apps/desktop/node_modules/electron/dist/electron.exe'))]:
    p=Path(path);tools.append({'name':name,'version':version,'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),
                              'executed_this_readiness_turn':False})
packages=[]
package_paths=[MAIN/'apps/desktop/node_modules/electron/package.json',MAIN/'apps/web/node_modules/vite/package.json',
    MAIN/'apps/web/node_modules/react/package.json',MAIN/'apps/web/node_modules/react-dom/package.json',
    MAIN/'apps/web/node_modules/@rolldown/binding-win32-x64-msvc/package.json',
    MAIN/'third_party/mu/node_modules/esbuild/package.json']
for cache in ['705bc6b22212b352','e41f203b7505f1fb','31e32ef8478fbf80','423231821c231c73','9833c18b2d85bc59']:
    for name in ['playwright','playwright-core']:
        package_paths.append(Path('C:/Users/yqyyds/AppData/Local/npm-cache/_npx')/cache/'node_modules'/name/'package.json')
for p in package_paths:
    if p.is_file():
        j=json.loads(p.read_bytes());packages.append({'path':str(p),'name':j['name'],'version':j['version'],'sha256':sha(p)})
sources=[]
for relative in ['apps/desktop/build-development.py','apps/desktop/build-validator.py','apps/desktop/launch-development.mjs',
    'docs/installation/desktop-development.md','apps/desktop/package.json','apps/web/package.json',
    'execution/toolchains/locked.json','apps/desktop/main/main.js']:
    src=MAIN/relative;dst=OUT/'source'/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    sources.append({'path':relative,'sha256':sha(src),'bytes':src.stat().st_size})
pw=Path('C:/Users/yqyyds/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright-core/index.mjs')
put('RESOURCES.json',{'status':'PUBLIC_METADATA_DISCOVERED_NOT_BUILD_OR_RUNTIME_QUALIFIED','tools':tools,'packages':packages,
    'module_locations':{'Go_public_cache':str(MAIN/'.local/tools/gopath/pkg/mod'),'web_public_cache':str(MAIN/'apps/web/node_modules'),
       'Electron_dist':str(MAIN/'apps/desktop/node_modules/electron/dist'),'Mu_common':str(MAIN),
       'Mu_esbuild_exe':str(MAIN/'third_party/mu/node_modules/@esbuild/win32-x64/esbuild.exe'),
       'Playwright_stable_candidate':'C:/Users/yqyyds/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright-core'},
    'Playwright_electron_export':{'file':str(pw),'sha256':sha(pw),'static_export_found':'export const _electron = playwright._electron' in pw.read_text(encoding='utf-8'),
       'import_launch_compatibility_tested':False},
    'Chromium_public_cache_observed':['chromium-1208','chromium-1223','chromium-1234','chromium-1237'],
    'Chromium_cache_note':'Browser executable metadata found; Electron automation uses explicit Electron binary, not an assumed cached Chrome replacement.',
    'disk_snapshot':{'C_free_bytes':10777583616,'D_free_bytes':36330205184,'observed_chunk':'e91b58','not_capacity_guarantee':True},
    'full_dependency_closure_verified':False,'full_Electron_distribution_inventory_verified':False,
    'source_pins':sources,'builds':0,'GUI_launches':0,'model_calls':0,'installs':0,'old_DB_or_credentials_read':0})
put('COMMANDS-NOT-EXECUTED.txt','''PROPOSED ONLY. Replace <W>, <owned-public-web-cache>, <new-receipts> and fresh names only in a new Root scope.

First integrate reviewed UI10 and Backend18 into one exact V1 commit, then create a clean registered source worktree <W>. Source branches currently are not integrated; do not build old Main and call it this V1. Use a small explicit OS/Python/Git/Node environment without tokens, proxies, NODE_OPTIONS or Electron flags; builders currently start from os.environ.copy().

& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -B -X utf8 '<W>/apps/desktop/build-development.py' `
  --go 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe' `
  --node 'C:/nvm4w/nodejs/node.exe' `
  --electron-dist 'D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist' `
  --module-cache '<new-owned-module-cache-or-explicitly-approved-public-cache>' `
  --web-modules '<owned-public-web-cache>' `
  --mu-common 'D:/作品集/ResearchOS/research-os' `
  --output '<W>/.local/desktop-v1-<fresh-scope>' `
  --receipts '<new-receipts>/build-01'

Builder success, if actually observed, is only BUILT_NOT_NATIVE_TESTED. It internally compiles Core/verifier/client-wire/negative fixture/Mu and runs Vite; it does not install a product or launch Electron. It creates a web-module junction in its fresh intermediate client tree. Any cache copy/junction must be explicit in the new build scope; do not modify shared caches or choose old receipt/output names.

After an actual successful source-bound build, separate dry-run (still not executed here):
& 'C:/nvm4w/nodejs/node.exe' '<W>/.local/desktop-v1-<fresh-scope>/launch-development.mjs' `
  --bundle '<W>/.local/desktop-v1-<fresh-scope>' `
  --state '<W>/.local/gui-state-v1-<new-run>' --dry-run

Actual GUI/Host startup is a later separate qualification, not authorized by this file:
& 'C:/nvm4w/nodejs/node.exe' '<W>/.local/desktop-v1-<fresh-scope>/launch-development.mjs' `
  --bundle '<W>/.local/desktop-v1-<fresh-scope>' `
  --state '<W>/.local/gui-state-v1-<new-run>' --launch --smoke

The GUI command is only a minimal readiness smoke. V1 user-flow and screenshots require an explicitly reviewed new GUI harness/scope, not simply this command or prior pure tests. Never reuse previous state/model/Native/UNKNOWN scopes or run old probes.
''')
put('READINESS.md','''# Windows Desktop V1 resources — readonly preparation

Observed public resources: locked Python3.14.3, Node24.9.0, npm11.6.0, Go1.27.1 and Electron37.10.3 executables match the recorded locked hashes. Local web packages are Vite8.3.1, React/react-dom19.3.0 and rolldown Windows binding1.2.11. Public Mu/esbuild0.28.2 inputs and dist files exist. Playwright/playwright-core stable1.61.1 and1.62.1 plus three alpha caches exist under npm-cache/_npx; the1.62.1 core entry statically exports _electron. None was imported, built, installed or launched during this preparation, and full dependency/runtime closure is not established by these metadata facts.

Root's CP605 status says UI10 has40pure checks and5Vite builds frozen for independent QA; Backend18 has not had its first compile. Neither is integrated into Main. Those are reported source checks, not this turn's desktop build or GUI observation. The exact integrated V1 source commit is therefore a necessary input before build qualification.

Existing build-development.py and docs provide a reusable source-bound development-tree recipe. A clean registered source worktree is required: the script rejects all changed/untracked paths outside its old seven-file allowlist. Once UI/backend are reviewed and integrated, their tracked files enter the normal source closure; do not weaken the guard to build a dirty branch. The output must be new under that worktree's .local; receipt and six sibling scratch paths must also be new. The script rechecks source, Go/tool closure,5083Mu vendored files, compiled Mu inputs and public package inputs, and seals per-file output hashes. It compiles the real verifier and control, all cwd contracts/migrations, React assets, client-wire validator and complete Electron tree. Absolute verifier/bundle bindings prohibit moving an old built tree or reusing its manifest.

Cache plan: use explicit absolute Node/Python/Go paths, not npm/npx downloads. Electron distribution is a public read-only input which the builder copies and rehashes. Mu common must remain the real Git common Main selected by build.mjs. Web node_modules can be copied physically into a new owned cache after rejecting reparse points and recording hashes, then passed via --web-modules; the existing client builder still creates an intermediate junction to that new cache. This avoids Vite temporary writes reaching the shared old cache. Go -mod=readonly protects go.mod, not every cache write; either scope the existing public module cache deliberately or copy the required locked module closure to a new owned cache. Fresh GOCACHE/GOTMPDIR/temp/Mu/client staging are built under output siblings. C had about10.8GB and D36.3GB free at discovery; do not blindly copy large caches onto C or treat those values as an adequate-capacity proof. Recheck the new worktree/build/scratch/cache space before allocation.

Minimal actual sequence after new scope: (1) build exact integrated source and pin final manifest, raw stdout/stderr, invocation exits and before/after closures; (2) dry-run a never-existing sibling state path; (3) one owned real Electron/Host smoke with a new state path. Launcher derives data/, discovery.json, electron-user-data/, profile/ and tmp/ from that fresh state, disables shared-host locator and filters ambient RESEARCHOS/ROS_DESKTOP/NODE_OPTIONS/ELECTRON values. Never copy an old user DB, credentials, profile or desktop context. The original paused sandbox candidate and old model/qualification approvals remain unrelated and unavailable for reuse.

Runtime evidence must come from actual events: ready_to_show with mounted React root/navigation/title, management READY, native host.status success for the owned Core identity, then shutdown_confirmed with matching PID/creation-time/image SHA/Host ID and process_exit_confirmed. Capture screenshot, renderer console errors, ordered action/event results and artifact references from the same owned run; persist their hashes and exact source/build/run binding. A successful renderer screenshot alone is not Host/business acceptance, and this readiness smoke is not V1 project/batch/trace/summary persistence verification. Backend completion and fresh user-flow fixtures remain separate conditions.

Screenshot gap: Main already supports ROS_DESKTOP_CAPTURE_PATH and capturePage, but buildChildEnv does not forward that variable; the existing launcher therefore does not automatically enable it. Do not assume setting ambient env produces a screenshot. A new reviewed harness can use cached Playwright _electron with the explicitly pinned bundled Electron and the same validated fresh launch recipe, or Root can separately scope a narrowly bound capture option. The actual ElectronApplication process/Window must be owned by this run; a cached Chromium/browser profile is not an Electron substitute. Playwright import/launch compatibility and all screenshot interaction remain unverified.

Stop ownership gap: existing launcher awaits child close without an outer total deadline; build subcommands also use an unbounded parent wait. Future build/GUI qualification must assign one owner to the exact launcher/Electron/owned Core identities, use graceful management shutdown first, and provide a separately reviewed bounded original-handle/tree fail-safe. Never kill by process name, scan/reopen an old PID, or reuse the old model supervisor scope/exe as GUI authorization. If shutdown is uncertain, retain new state/receipts and report UNKNOWN; do not rerun with reused state. Old SDK/Native/model resource failures and counters remain unchanged.

No resource absence currently proves that installation is needed. The concrete unresolved items are the reviewed integrated V1 source, an actual complete source-bound build, the fresh GUI ownership/capture scope and harness, runtime compatibility, verified shutdown, and actual V1 user-flow evidence. This report neither requests installation nor claims build/install/runtime PASS.
''')
put('DIAGNOSTICS.json',{'readonly_chunks':['1412c1','7abc6f','8c6e40','0c20f2','8beefd','deeeb8','66b6d8','79ba27','e91b58','cc6f88'],
    'optional_lookup_exit1':'deeeb8 ended with absent optional roaming npm directory; public package findings above succeeded; no build/test/runtime attempt',
    'builds':0,'tests_run':0,'GUI_launches':0,'Electron_version_launches':0,'model_calls':0,'Native_qualification_calls':0,'installs':0,
    'D_writes':0,'user_credentials_or_DB_read':0,'old_probe_replays':0,'failure_counter_reset':False,
    'old_sandbox_candidate':'Paused and untouched; no Go/Native tests or new source edits',
    'readonly_child':'Build/docs analysis completed and finalized; no files written or runtime started'})
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
put('MANIFEST.json',{'schema':'researchos.v1-desktop-resource-readiness.v1','status':'READONLY_RESOURCES_DISCOVERED_NO_BUILD_NO_GUI',
    'at':datetime.now(timezone.utc).isoformat(),'owner':'codex:/root/runtime_readiness','parent_baseline':'CP605/Main29f923 (parent-reported; V1 UI10/Backend18 unintegrated)',
    'construction':False,'source_modification_permitted':False,'GUI_or_model_execution_authorized':False,
    'builds':0,'GUI_launches':0,'installs':0,'model_calls':0,'D_writes':0,'formal_increment':0,'failure_counter_reset':False,
    'files':files})
print(json.dumps({'status':'READONLY_RESOURCES_DISCOVERED_NO_BUILD_NO_GUI','path':str(OUT),'manifest_sha256':sha(OUT/'MANIFEST.json'),'files':len(files),
    'builds':0,'GUI_launches':0,'installs':0,'model_calls':0,'D_writes':0}))
