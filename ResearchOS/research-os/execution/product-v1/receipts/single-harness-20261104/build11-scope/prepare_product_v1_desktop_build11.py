import argparse,hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
WT=ROOT/'.local/worktrees/product-v1-build-11-20261105';OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/build11-scope'
CONTROL=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf8')
p=argparse.ArgumentParser();p.add_argument('--web-modules',required=True);p.add_argument('--web-manifest',required=True);p.add_argument('--web-manifest-sha',required=True);a=p.parse_args()
assert not WT.exists() and not OUT.exists();web=Path(a.web_modules).resolve();wm=Path(a.web_manifest)
assert web.is_relative_to(ROOT/'.local/product-v1-build-inputs-20261104') and web.is_dir() and sha(wm)==a.web_manifest_sha
cp=read(ROOT/'execution/v2.4/checkpoint.json');head=git(ROOT,'rev-parse','HEAD').strip();assert cp['current_Main_HEAD']==head and cp['revision']>=667
assert not git(ROOT,'diff','--cached','--name-only').strip()
state=read(ROOT/'execution/product-v1/state.json');integrated=state['integrated_source'];assert len(integrated)>=14
pins={}
for item in integrated:
 for ref,digest in item['source_sha256'].items():pins[ref]=digest
assert len(pins)>=48
for ref,digest in pins.items():assert sha(ROOT/ref)==digest
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert sha(HERE/'product-v1-owned-supervisor-root-review.json')=='5eda7e5c0200b14650fc893a5cfd2b0ad7b20c7251261d78d01a0827932cd296'
OUT.mkdir();put(OUT/'journal.json',dict(status='PRECHECKED_AWAITING_CLEAN_WORKTREE',main_head=head,source_sha256=pins))
git(ROOT,'worktree','add','--no-checkout','-b','codex/product-v1-build-11-20261105',str(WT),head)
patterns=['/.gitignore','/AGENTS.md','/go.mod','/go.sum','/go.work','/go.work.sum','/apps/','/internal/','/adapters/','/migrations/sqlite/','/spec/v2.0/contracts/','/spec/v2.0/ui/','/ops/','/tests/ui/','/tests/runtime/','/docs/installation/','/execution/toolchains/']
git(WT,'sparse-checkout','set','--no-cone',*patterns);git(WT,'checkout','HEAD')
dependencies=git(WT,'ls-tree','-r','--name-only','HEAD','--','evaluation/holdout/jev','evaluation/evolution','evaluation/skills').splitlines()
code=['/'+v for v in dependencies if v.endswith('.go') and not v.endswith('_test.go')]
if code:git(WT,'sparse-checkout','add',*code)
assert not git(WT,'status','--porcelain=v1').strip()
for ref,digest in pins.items():assert sha(WT/ref)==digest,ref
for ref in ['.gitignore','spec/v2.0/ui/design-tokens.json','execution/toolchains/locked.json','apps/desktop/build-development.py','apps/desktop/build-validator.py','apps/desktop/launch-development.mjs','docs/installation/desktop-development.md']:assert (WT/ref).is_file(),ref
bundle=WT/'.local/desktop-v1-build-11';producer=OUT/'producer-11';assert not bundle.exists() and not producer.exists()
python=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe');node=Path('C:/nvm4w/nodejs/node.exe');go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe';electron=ROOT/'apps/desktop/node_modules/electron/dist';mods=ROOT/'.local/tools/gopath/pkg/mod'
argv=['-B','-X','utf8',str(WT/'apps/desktop/build-development.py'),'--go',str(go),'--node',str(node),'--electron-dist',str(electron),'--module-cache',str(mods),'--web-modules',str(web),'--mu-common',str(ROOT),'--output',str(bundle),'--receipts',str(producer)]
inputs=[dict(path=str(WT/ref),sha256=digest) for ref,digest in pins.items()]
for f in [WT/'apps/desktop/build-development.py',WT/'apps/desktop/build-validator.py',WT/'apps/desktop/launch-development.mjs',WT/'go.mod',WT/'go.sum',go,node,electron/'electron.exe',wm]:inputs.append(dict(path=str(f),sha256=sha(f)))
scope=dict(schema='researchos.owned-windows-run/1',scope_id='product-v1-build-11',purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(python),executable_sha256=sha(python),argv=argv,cwd=str(WT),inputs=inputs,timeout_seconds=1200,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=48,memory_mib=6144,max_raw_bytes=67108864,env=dict(GOENV='off',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOWORK='off'))
scopepath=CONTROL/'scopes/product-v1-build-11.json';assert not scopepath.exists();put(scopepath,scope)
registration=dict(status='REGISTERED_NOT_EXECUTED',at=datetime.now(timezone.utc).isoformat(),main_head=head,main_checkpoint=cp['revision'],clean_worktree=str(WT),source_sha256=pins,scope_path=str(scopepath),scope_sha256=sha(scopepath),bundle=str(bundle),producer_receipts=str(producer),web_manifest=str(wm),web_manifest_sha256=sha(wm),public_module_cache=dict(path=str(mods),mode='EXPLICIT_OFFLINE_SHARED_PUBLIC_MODULE_INPUT; fresh Go build/temp caches are owned output siblings; never delete or rewrite existing modules'),model_gui_started=False,formal_increment=0,product_acceptance_increment=0)
put(OUT/'registration.json',registration);put(OUT/'journal.json',dict(status='CLEAN_SOURCE_SCOPE_REGISTERED_NOT_EXECUTED',scope_sha256=sha(scopepath)))
(OUT/'prepare_product_v1_desktop_build11.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(registration))
