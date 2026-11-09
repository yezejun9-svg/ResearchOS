import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
ID='product-v1-native-preparation-drain-tests-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
lease=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-preparation-desktop-drain/scope.effective-v1.json'
assert sha(lease)=='071178b1f0298b3403e0d428fb83bc121d836b644088276e5dc2cd1956baf2ea'
source=read(lease);wt=Path(source['worktree']);archive=HERE/'native-preparation-desktop-drain-candidate-rev3-20261105';manifest=archive/'manifest.json';assert sha(manifest)=='02fbe59e7188bd71b5a0f886b6cb120ebf2c9beee570d14d627c01ed512b784c'
for ref,digest in read(manifest)['candidate_sha256'].items():assert sha(wt/ref)==digest
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe';assert sha(go)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
python=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe');assert sha(python)=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
wrapper=HERE/'run_preparation_drain_go_serial03.py';pattern=read(archive/'diagnostics.json')['root_suggested_test_regex'];assert len(pattern)<2048
out=HERE/(ID+'-registration');sp=CONTROL/'scopes'/(ID+'.json');assert not out.exists() and not sp.exists() and not (CONTROL/'runs'/ID).exists()
files=[wt/ref for ref in source['production_paths']+source['test_paths']]+[wt/'go.mod',wt/'go.sum',go,wrapper,Path(__file__),manifest,archive/'diagnostics.json',lease,CONTROL/'owned_run.py',ROOT/source['original_lease_ref'],ROOT/source['amendment_ref']]
for ref,digest in source['contract_pins'].items():assert sha(ROOT/ref)==digest;files.append(ROOT/ref)
out.mkdir();cache=out/'gocache';tmp=out/'gotmp';cache.mkdir();tmp.mkdir()
scope=dict(schema='researchos.owned-windows-run/1',scope_id=ID,purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(python),executable_sha256=sha(python),argv=['-B','-X','utf8',str(wrapper),str(go),'test','-p=1','-v','-count=1','-run',pattern,'./internal/domain'],cwd=str(wt),timeout_seconds=600,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=48,memory_mib=6144,max_raw_bytes=8388608,env=dict(GOENV='off',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOWORK='off',CGO_ENABLED='0',GOMODCACHE=str(ROOT/'.local/tools/gopath/pkg/mod'),GOCACHE=str(cache),GOTMPDIR=str(tmp)),inputs=[dict(path=str(p),sha256=sha(p)) for p in files])
sp.write_bytes((json.dumps(scope,indent=2)+'\n').encode('utf8'))
r=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),source_scope_sha256=sha(lease),source_manifest_sha256=sha(manifest),new_app_native_model_budget=0,resource_wrapper='GOMAXPROCS1_SAME_ORIGINAL_F13_JOB_LIMITS',formal_increment=0)
(out/'REGISTRATION.json').write_bytes((json.dumps(r,indent=2)+'\n').encode('utf8'));print(json.dumps(r))
