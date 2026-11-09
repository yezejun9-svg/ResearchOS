import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
CONTROL=HERE/'product-v1-owned-verification-20261104'
ID='product-v1-workbench-refinement-tests-02'
LEASE=ROOT/'execution/product-v1/receipts/single-harness-20261104/workbench-assistant-refinement/scope.json'
FREEZE=HERE/'product-v1-workbench-assistant-refinement-20261105-freeze-02/manifest.json'
NODE=Path('C:/nvm4w/nodejs/node.exe')
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
s=read(LEASE);m=read(FREEZE);wt=Path(s['worktree']);assert m['scope_id']==s['scope_id'] and m['candidate_root']==str(wt)
assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert not (CONTROL/'runs'/ID).exists()
for entry in m['files']:assert sha(wt/entry['repo_relative'])==entry['candidate_sha256']
for ref,digest in s['contract_pins'].items():assert sha(ROOT/ref)==digest
tests=['tests/ui/desktop/harness-workbench.test.mjs','tests/ui/harness-progress.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/assistant-startup.test.mjs']
files=[LEASE,FREEZE,Path(__file__),wt/'apps/web/package.json',wt/'apps/desktop/package.json']+[ROOT/p for p in s['contract_pins']]+[wt/p for p in tests]
for base,patterns in [(wt/'apps/web/src',['*.js','*.jsx','*.css']),(wt/'apps/desktop/main',['*.js'])]:
 for pattern in patterns:files+=sorted(base.rglob(pattern))
files=list({str(p.resolve()).lower():p for p in files}.values())
scope=dict(schema='researchos.owned-windows-run/1',scope_id=ID,purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(NODE),executable_sha256=sha(NODE),argv=['--test',*tests],cwd=str(wt),timeout_seconds=120,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=24,memory_mib=3072,max_raw_bytes=4*1024*1024,env={},inputs=[dict(path=str(p),sha256=sha(p)) for p in files])
out=HERE/(ID+'-registration');assert not out.exists();out.mkdir();sp=CONTROL/'scopes'/(ID+'.json');put(sp,scope)
reg=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),source_scope_sha256=sha(LEASE),freeze_sha256=sha(FREEZE),input_count=len(files),model_tasks=0,native_invocations=0,fixture_only=True,automatic_retry=0,formal_increment=0,product_increment=0)
put(out/'REGISTRATION.json',reg);print(json.dumps(reg))
