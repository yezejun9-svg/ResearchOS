import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';ID='product-v1-native-policy-tests-02';OUT=HERE/'product-v1-native-policy-test-registration02';WT=ROOT/'.local/worktrees/product-v1-native-policy-binding-20261105'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not OUT.exists() and not (CONTROL/'runs'/ID).exists();cp=read(ROOT/'execution/v2.4/checkpoint.json');assert cp['revision']>=664
lease=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json';s=read(lease);assert Path(s['worktree'])==WT and s['owner']=='codex:/root/mobile_viewport_impl'
go=ROOT/'.local/tools/go1.27.1/go/bin/go.exe';assert sha(go)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490';assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
files=[WT/ref for ref in s['production_paths']+s['test_paths']]+[WT/'go.mod',WT/'go.sum',lease,ROOT/s['contract_ref'],Path(__file__)]
OUT.mkdir();cache=OUT/'gocache';tmp=OUT/'gotmp';cache.mkdir();tmp.mkdir()
pattern='TestCodex(RequestedPolicyIdentityAndArguments|ReadinessFailClosed|ReadinessMutationBeforeResume|HarnessFixedArguments|HarnessNativeLifecycle)$|TestHarnessCoordinatorFakeChain$|TestHarnessSourceRebindBeforeResume$|TestHarnessHostPrincipalActualBinding$'
scope=dict(schema='researchos.owned-windows-run/1',scope_id=ID,purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(go),executable_sha256=sha(go),argv=['test','-v','-count=1','-run',pattern,'./adapters/runtime','./internal/domain','./internal/host'],cwd=str(WT),timeout_seconds=600,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=48,memory_mib=6144,max_raw_bytes=8*1024*1024,env=dict(GOENV='off',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOWORK='off',CGO_ENABLED='0',GOMODCACHE=str(ROOT/'.local/tools/gopath/pkg/mod'),GOCACHE=str(cache),GOTMPDIR=str(tmp)),inputs=[dict(path=str(p),sha256=sha(p)) for p in files])
sp=CONTROL/'scopes'/f'{ID}.json';put(sp,scope);registration=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),unit='SOURCE_FAKE_CHILD_FIXTURE_NOT_NATIVE_MODEL_PERMISSION_QUALIFICATION',actual_native_invocations=0,actual_model_tasks=0,task_submissions=0,selected_test_pattern=pattern,source_sha256={str(p):sha(p) for p in files},formal_increment=0,product_increment=0,automatic_retry=0);put(OUT/'REGISTRATION.json',registration)
target=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/development-test02';assert not target.exists();target.mkdir()
for name,p in [('scope.json',sp),('REGISTRATION.json',OUT/'REGISTRATION.json'),(Path(__file__).name,Path(__file__))]:(target/name).write_bytes(p.read_bytes())
print(json.dumps(dict(scope_path=str(sp),scope_sha256=sha(sp),selected_pattern=pattern,source_files=len(files),native_invocations=0,model_tasks=0)))
