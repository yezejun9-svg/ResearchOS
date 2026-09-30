import datetime,hashlib,importlib.util,io,json,pathlib,subprocess,sys
from http.client import HTTPResponse
sys.dont_write_bytecode=True
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[3]
RUN=OUT.name
PACK=ROOT/'execution/receipts/W17'/RUN
PRIOR=ROOT/'execution/verifier/W17/c02-c3991c0'
checks=[]
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p): return [json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,label):
 if not ok: raise AssertionError(label)
 checks.append(label)
def hashed(p,want): check(sha(p)==want.removeprefix('sha256:'),'hash:'+str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p))
def canonical(x):
 def inspect(v):
  if isinstance(v,float): raise ValueError('float not supported')
  if isinstance(v,dict):
   for k,w in v.items():
    if any(ord(c)>65535 for c in k): raise ValueError('non-BMP key')
    inspect(w)
  if isinstance(v,list):
   for w in v: inspect(w)
 inspect(x)
 return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def git_blobs(rev,items):
 items=list(items)
 proc=subprocess.run(['git','cat-file','--batch'],input=''.join(rev+':'+n+'\n' for n,_ in items).encode(),cwd=ROOT,stdout=subprocess.PIPE,check=True)
 stream=io.BytesIO(proc.stdout)
 for name,want in items:
  header=stream.readline().split();check(len(header)==3 and header[1]==b'blob','git-blob:'+name)
  body=stream.read(int(header[2]));check(stream.read(1)==b'\n','git-boundary:'+name)
  check(hashlib.sha256(body).hexdigest()==want.removeprefix('sha256:'),'git-hash:'+name)
receipt=load(PACK/'receipt.json');case=load(PACK/'C02.json');manifest=load(PACK/'artifacts.json')
check(receipt['receipt_hash']=='sha256:'+hashlib.sha256(canonical({k:v for k,v in receipt.items() if k!='receipt_hash'})).hexdigest(),'executor-receipt-JCS')
check(receipt['receipt_hash']=='sha256:e9c3e5c32da5ee2a93e4f69e694c98ca22b0fd8cd7bdbd1525281f0e52586fcc','parent-frozen-receipt')
hashed(PACK/'artifacts.json',receipt['artifact_manifest_hash'])
check(len(manifest['files'])==34,'34-manifest-files')
for row in manifest['files']: hashed(ROOT/row['path'],row['sha256'])
source=case['version_manifest']['source_sha256'];git_blobs(receipt['code_revision'],source.items())
check(set(source)==set(receipt['verified_source_paths']),'source-inventory-exact')
priorindex=load(PRIOR/'evidence-index.json')
for row in priorindex['local_files']: hashed(PRIOR/row['path'],row['sha256'])
reviewroot=ROOT/'.local/worktrees/c02-review'
for row in priorindex['author_evidence']: hashed(reviewroot/row['path'],row['sha256'])
git_blobs(priorindex['review_checkout_revision'],[(r['path'],r['sha256']) for r in priorindex['reviewed_sources']])
for row in priorindex['reviewed_sources']: hashed(ROOT/row['path'],row['sha256'])
prior=load(PRIOR/'review.json');check(prior['verdict']=='PASS_C02_DEVELOPMENT_FIXTURE' and not prior['blocking_findings'],'independent-prior-verdict')
contract=next(c for c in load(ROOT/'spec/v2.0/contracts/acceptance.json')['cases'] if c['id']=='C02')
check(contract['mode']=='FIXTURE' and contract['final_owner_task']=='W17','frozen-case-owner-mode')
check([a['assertion_id'] for a in case['assertion_results']]==[a['id'] for a in contract['assertions']],'frozen-case-complete')
for frozen,actual in zip(contract['assertions'],case['assertion_results']):
 check(frozen['expected']==actual['expected'] and actual['status']=='PASS' and len(actual['actual'])==2,'frozen-assertion:'+frozen['id'])
 for raw in actual['raw_evidence']: hashed(ROOT/raw['path'],raw['sha256'])
spec=importlib.util.spec_from_file_location('readonly_c02',ROOT/'tests/security/c02_fixture.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
ids=runner.validate_inventory(load(ROOT/'tests/security/c02_expected.json'))
runs=[]
for result in receipt['verification_results']:
 inv=load(ROOT/result['actual_invocation_reference']);check(inv['status']=='PASS' and inv['exit_code']==inv['child_exit_code']==0,'invocation-pass:'+inv['command_key'])
 check(inv['code_revision']==receipt['code_revision'] and inv['selectors']=={'task_id':'W17','check_id':'','case_id':'C02'},'invocation-binding:'+inv['command_key'])
 check(inv['assertion_ids']==ids and inv['command_key'] in contract['command_keys'],'invocation-inventory:'+inv['command_key'])
 hashed(ROOT/'execution/commands.json',inv['registered_command_revision'])
 for kind in ['stdout','stderr']: hashed(ROOT/inv[kind]['path'],inv[kind]['sha256'])
 stdout=lines(ROOT/inv['stdout']['path'])[-1];directory=pathlib.Path(stdout['receipt']).parent;report=load(directory/'report.json')
 check(stdout['assertion_ids']==ids and report['source_commit']==receipt['code_revision'] and report['mode']=='FIXTURE' and report['exit_code']==0,'report-binding')
 for name,digest in load(directory/'evidence-index.json')['files'].items(): hashed(directory/name,digest)
 sm=load(directory/'source-manifest.json');git_blobs(receipt['code_revision'],sm['files'].items());hashed(pathlib.Path(sm['go']['path']),sm['go']['sha256'])
 events,records=lines(directory/'go.stdout.jsonl'),lines(directory/'audit.jsonl');validated=runner.validate_evidence(events,records,ids)
 check(validated['assertions']==report['assertions'] and validated['scan']==report['scan'],'raw-reported-semantics')
 for filename,key in [('marker-scan.json','scan'),('permission-matrix.json','permission_matrix'),('sqlite-readback.json','sqlite_readback')]:check(load(directory/filename)==validated[key],'derived:'+filename)
 http=[r for r in records if r.get('record_type')=='http'];check(len(http)==135,'135-HTTP')
 for row in http:
  check(row['raw_request'].splitlines()[0]==f"{row['method']} {row['path']} HTTP/1.1",'wire-request')
  class Sock:
   def makefile(self,*args):return io.BytesIO(row['raw_response'].encode())
  response=HTTPResponse(Sock());response.begin();check(response.status==row['status'] and response.read().decode()==row['response_body'],'wire-response')
 materials=[r for r in records if r.get('record_type')=='materialized_file']
 for row in materials:check(row['sha256']=='sha256:'+hashlib.sha256(row['body'].encode()).hexdigest(),'materialized-hash')
 for role in ['READER','PLANNER','EXECUTOR']:
  shared=[json.loads(r['body']) for r in materials if r['role']==role and r['path'].endswith('.content') and 'fixture_explicit_shared_knowledge' in r['body']]
  check(len(shared)==1 and shared[0]['source']=='fixture://explicit-common-knowledge/shared-v1' and shared[0]['source_version']=='1' and shared[0]['shared_knowledge_scope']==['fixture_project_a','fixture_project_b'] and len(set(shared[0]['authorized_project_ids']))==2,'shared-provenance:'+role)
 runs.append({'command_key':inv['command_key'],'invocation_id':inv['invocation_id'],'assertions':22,'HTTP_requests':135,'scan':validated['scan'],'report':str(directory.relative_to(ROOT)/'report.json')})
check(sorted(r['command_key'] for r in runs)==sorted(contract['command_keys']),'both-frozen-commands')
report={'status':'PASS','task_id':'W17','case_id':'C02','run_id':RUN,'source_revision':receipt['code_revision'],'executor_receipt_jcs_hash':receipt['receipt_hash'],'manifest_files':34,'source_hashes_verified':len(source),'prior_independent_review_verified':True,'checks_passed':len(checks),'registered_runs':runs,'new_product_test_runs':0,'new_external_or_protected_access':False,'whole_stage_accepted':False}
(OUT/'audit-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(OUT/'audit-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))

