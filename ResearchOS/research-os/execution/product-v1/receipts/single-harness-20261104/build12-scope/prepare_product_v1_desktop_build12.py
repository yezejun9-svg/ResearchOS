import argparse,hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
WT=ROOT/'.local/worktrees/product-v1-build-12-20261105';OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/build12-scope'
CONTROL=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf8')
p=argparse.ArgumentParser();p.add_argument('--web-modules',required=True);p.add_argument('--web-manifest',required=True);p.add_argument('--web-manifest-sha',required=True);a=p.parse_args()
assert not WT.exists() and not OUT.exists();web=Path(a.web_modules).resolve();wm=Path(a.web_manifest)
assert web.is_relative_to(ROOT/'.local/product-v1-build-inputs-20261104') and web.is_dir() and sha(wm)==a.web_manifest_sha
cp=read(ROOT/'execution/v2.4/checkpoint.json');head=git(ROOT,'rev-parse','HEAD').strip();assert cp['current_Main_HEAD']==head and cp['revision']>=681
assert not git(ROOT,'diff','--cached','--name-only').strip()
state=read(ROOT/'execution/product-v1/state.json');integrated=state['integrated_source'];assert len(integrated)>=14
required_scope_ids=('PRODUCT_V1_QUALIFICATION_BUILD_BINDING','PRODUCT_V1_NATIVE_PRELAUNCH_INTENT')
active={row['scope_id']:row for row in state['active_scopes']}
for scope_id in required_scope_ids:
 row=active[scope_id];assert row['status']=='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
scope_refs={scope_id:ROOT/active[scope_id]['scope_ref'] for scope_id in required_scope_ids}
for scope_id,path in scope_refs.items():assert path.is_file(),scope_id
pins={}
for item in integrated:
 for ref,digest in item['source_sha256'].items():pins[ref]=digest
assert len(pins)>=60
for ref,digest in pins.items():assert sha(ROOT/ref)==digest
QUALIFICATION_ROOT=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-qualification-中文-root-01')
QUALIFICATION_HELPER=QUALIFICATION_ROOT/'S/qualification-helper.exe'
QUALIFICATION_HELPER_SHA='4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef'
HELPER_RECEIPTS=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-helper-build01'
FIXTURE_RECEIPTS=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-fixture-preparation01'
QUALIFICATION_PROOFS=[
 (QUALIFICATION_HELPER,QUALIFICATION_HELPER_SHA),
 (FIXTURE_RECEIPTS/'product-v1-first-native-fixture-canaries-preparation.json','1a8affeaefb21738acd929e1ae709e149a4020856ad611a5c368b02842dbb2aa'),
 (FIXTURE_RECEIPTS/'product-v1-first-native-fixture-preparation.json','e2c78d439d6b7dd69a224350d0f6cc560c98ed8594f163310dce0785c84ae7dc'),
 (HELPER_RECEIPTS/'scope.json','c1aff0bca3d4b7b63edbae04dc2c2538260d4aba64b4c4b1b11e9ad114c85350'),
 (HELPER_RECEIPTS/'RESULT.json','1244420e5b354a6fdbbcab2e3320d94df6ac425b3f52c990292b794d9d3a56d6'),
 (HELPER_RECEIPTS/'POSTCHECK.json','b62f09d6f766c4878e04609909087f871089e02cc31c6c3cb916952e6556a5cd'),
 (HELPER_RECEIPTS/'MANIFEST.json','f232b86b8871df92a7fdfe621e6934324603d280daa744249e4756318e54b7bd'),
]
for f,digest in QUALIFICATION_PROOFS:assert sha(f)==digest,f
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert sha(HERE/'product-v1-owned-supervisor-root-review.json')=='5eda7e5c0200b14650fc893a5cfd2b0ad7b20c7251261d78d01a0827932cd296'
OUT.mkdir();put(OUT/'journal.json',dict(status='PRECHECKED_AWAITING_CLEAN_WORKTREE',main_head=head,source_sha256=pins))
git(ROOT,'worktree','add','--no-checkout','-b','codex/product-v1-build-12-20261105',str(WT),head)
patterns=['/.gitignore','/AGENTS.md','/go.mod','/go.sum','/go.work','/go.work.sum','/apps/','/cmd/','/tests/desktop/','/internal/','/adapters/','/migrations/sqlite/','/spec/v2.0/contracts/','/spec/v2.0/ui/','/ops/','/tests/ui/','/tests/runtime/','/docs/installation/','/execution/toolchains/']
git(WT,'sparse-checkout','set','--no-cone',*patterns);git(WT,'checkout','HEAD')
dependencies=git(WT,'ls-tree','-r','--name-only','HEAD','--','evaluation/holdout/jev','evaluation/evolution','evaluation/skills').splitlines()
code=['/'+v for v in dependencies if v.endswith('.go') and not v.endswith('_test.go')]
if code:git(WT,'sparse-checkout','add',*code)
assert not git(WT,'status','--porcelain=v1').strip()
for ref,digest in pins.items():assert sha(WT/ref)==digest,ref
for ref in ['.gitignore','spec/v2.0/ui/design-tokens.json','execution/toolchains/locked.json','apps/desktop/build-development.py','apps/desktop/build-validator.py','apps/desktop/launch-development.mjs','docs/installation/desktop-development.md']:assert (WT/ref).is_file(),ref
bundle=WT/'.local/desktop-v1-build-12';producer=OUT/'producer-12';assert not bundle.exists() and not producer.exists()
python=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe');node=Path('C:/nvm4w/nodejs/node.exe');go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe';electron=ROOT/'apps/desktop/node_modules/electron/dist';mods=ROOT/'.local/tools/gopath/pkg/mod'
argv=['-B','-X','utf8',str(HERE/'build_desktop_serial12.py'),str(WT/'apps/desktop/build-development.py'),'--go',str(go),'--node',str(node),'--electron-dist',str(electron),'--module-cache',str(mods),'--web-modules',str(web),'--mu-common',str(ROOT),'--output',str(bundle),'--receipts',str(producer),'--qualification-root',str(QUALIFICATION_ROOT),'--qualification-helper',str(QUALIFICATION_HELPER),'--qualification-helper-sha256',QUALIFICATION_HELPER_SHA]
inputs=[dict(path=str(WT/ref),sha256=digest) for ref,digest in pins.items()]
inputs.append(dict(path=str(HERE/'build_desktop_serial12.py'),sha256=sha(HERE/'build_desktop_serial12.py')))
inputs.append(dict(path=str(HERE/'prepare_product_v1_desktop_build12.py'),sha256=sha(HERE/'prepare_product_v1_desktop_build12.py')))
for scope_id,path in scope_refs.items():inputs.append(dict(path=str(path),sha256=sha(path)))
for f,digest in QUALIFICATION_PROOFS:inputs.append(dict(path=str(f),sha256=digest))
for f in [WT/'apps/desktop/build-development.py',WT/'apps/desktop/build-validator.py',WT/'apps/desktop/launch-development.mjs',WT/'go.mod',WT/'go.sum',go,node,electron/'electron.exe',wm]:inputs.append(dict(path=str(f),sha256=sha(f)))
scope=dict(schema='researchos.owned-windows-run/1',scope_id='product-v1-build-12',purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(python),executable_sha256=sha(python),argv=argv,cwd=str(WT),inputs=inputs,timeout_seconds=1200,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=48,memory_mib=6144,max_raw_bytes=67108864,env=dict(GOENV='off',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOWORK='off'))
scopepath=CONTROL/'scopes/product-v1-build-12.json';assert not scopepath.exists();put(scopepath,scope)
registration=dict(serial_execution=dict(wrapper=str(HERE/'build_desktop_serial12.py'),wrapper_sha256=sha(HERE/'build_desktop_serial12.py'),gomaxprocs=1),bound_scope_ids={scope_id:dict(status=active[scope_id]['status'],scope_ref=str(scope_refs[scope_id]),scope_sha256=sha(scope_refs[scope_id])) for scope_id in required_scope_ids},qualification_helper=dict(root=str(QUALIFICATION_ROOT),path=str(QUALIFICATION_HELPER),sha256=QUALIFICATION_HELPER_SHA,source='PINNED_BUILT_NOT_EXECUTED_HELPER'),status='REGISTERED_NOT_EXECUTED',at=datetime.now(timezone.utc).isoformat(),main_head=head,main_checkpoint=cp['revision'],clean_worktree=str(WT),source_sha256=pins,scope_path=str(scopepath),scope_sha256=sha(scopepath),bundle=str(bundle),producer_receipts=str(producer),web_manifest=str(wm),web_manifest_sha256=sha(wm),public_module_cache=dict(path=str(mods),mode='EXPLICIT_OFFLINE_SHARED_PUBLIC_MODULE_INPUT; fresh Go build/temp caches are owned output siblings; never delete or rewrite existing modules'),model_gui_started=False,formal_increment=0,product_acceptance_increment=0)
put(OUT/'registration.json',registration);put(OUT/'journal.json',dict(status='CLEAN_SOURCE_SCOPE_REGISTERED_NOT_EXECUTED',scope_sha256=sha(scopepath)))
(OUT/'prepare_product_v1_desktop_build12.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(registration))
