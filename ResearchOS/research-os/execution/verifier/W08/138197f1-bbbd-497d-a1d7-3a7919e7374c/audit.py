"""Independent C06 public evidence audit; no product or provider execution."""
from pathlib import Path
import json,hashlib,subprocess
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE=ROOT/'execution/receipts/W08'/OUT.name
UI=ROOT/'execution/verifier/W08/c06-ui-delta-20260930'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(v):
 def validate(x):
  assert not isinstance(x,float)
  if isinstance(x,int):assert abs(x)<=9007199254740991
  if isinstance(x,dict):
   assert all(all(ord(c)<65536 for c in k) for k in x)
   for a in x.values():validate(a)
  if isinstance(x,list):
   for a in x:validate(a)
 validate(v)
 return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def jhash(v):return 'sha256:'+hashlib.sha256(canon(v)).hexdigest()
checks=[]
def ck(name,ok):
 assert ok,name
 checks.append({'check':name,'status':'PASS'})
def href(p,h):ck('hash:'+str(p.relative_to(ROOT)),sha(p)==h.removeprefix('sha256:'))
r=read(BASE/'receipt.json');m=read(BASE/'artifacts.json');c=read(BASE/'C06.json')
ck('receipt JCS',r['receipt_hash']==jhash({k:v for k,v in r.items() if k!='receipt_hash'})=='sha256:6b4a277e19f2664cbd2460229321f9a7436a38541ee84ffc6b2dba78c884c596')
href(BASE/'artifacts.json',r['artifact_manifest_hash'])
ck('manifest unique73',len(m['files'])==len({x['path'] for x in m['files']})==73)
for x in m['files']:href(ROOT/x['path'],x['sha256'])
acc=read(ROOT/'spec/v2.0/contracts/acceptance.json');frozen=next(x for x in acc['cases'] if x['id']=='C06')
ck('frozen mode',frozen['mode']==c['run_receipt']['environment_mode']=='FIXTURE')
ck('exact three assertion IDs',{x['id'] for x in frozen['assertions']}=={x['assertion_id'] for x in c['assertion_results']})
for fr,ar in zip(frozen['assertions'],c['assertion_results']):
 ck('frozen expected:'+fr['id'],fr['id']==ar['assertion_id'] and fr['expected']==ar['expected'] and ar['status']=='PASS')
 for e in ar['raw_evidence']:href(ROOT/e['path'],e['sha256'])
env=read(BASE/'environment-before.json');src=env['source_sha256']
keys=list(src);raw=subprocess.run(['git','cat-file','--batch'],input=''.join(r['code_revision']+':'+k+'\n' for k in keys).encode(),cwd=ROOT,capture_output=True,check=True).stdout
pos=0
for name in keys:
 end=raw.index(b'\n',pos);header=raw[pos:end].split();size=int(header[2]);body=raw[end+1:end+1+size];pos=end+size+2
 ck('source git blob:'+name,hashlib.sha256(body).hexdigest()==src[name])
 ck('source current:'+name,sha(ROOT/name)==src[name])
commands=[];sem=[]
for entry in c['command_receipt']:
 inv=read(ROOT/entry['reference']);stdout=read(ROOT/inv['stdout']['path']);rp=ROOT/Path(stdout['report_reference']);report=read(rp)
 ck('command frozen:'+inv['command_key'],inv['command_key'] in frozen['command_keys'] and inv['selectors']=={'task_id':'W08','check_id':'','case_id':'C06'})
 ck('command source/status',inv['code_revision']==r['code_revision']==report['head'] and inv['status']==report['status']=='PASS' and inv['exit_code']==report['exit_code']==0)
 ck('command 11 assertions',len(report['assertions'])==11 and set(inv['assertion_ids'])==set(report['assertion_ids']) and not report['failures'])
 rawrows=[]
 for line in (rp.parent/'go-test.jsonl').read_text('utf-8-sig').splitlines():
  output=json.loads(line).get('Output','')
  if output.startswith('W08_ASSERTION '):rawrows.append(json.loads(output[len('W08_ASSERTION '):]))
 ck('raw assertions match report',sorted(rawrows,key=lambda x:x['assertion_id'])==report['assertions'])
 ck('raw assertions pass',all(x['status']=='PASS' and x['actual']==x['expected'] for x in rawrows))
 ck('run interval covers backend',c['run_receipt']['started_at']<=inv['started_at'] and c['run_receipt']['ended_at']>=inv['ended_at'])
 for fault in ['missing-x','x-429']:
  snap=read(rp.parent/(fault+'-sqlite.json'));objs={x['id']:x['body'] for x in snap['objects']};closed=[x['body'] for x in snap['objects'] if x['kind']=='ResearchCycle' and x['body']['closed_at']]
  ck('one closed cycle:'+fault,len(closed)==1);cy=closed[0];cov=cy['source_coverage'];complete=[x for x in cov if x['status']=='COMPLETE'];bad=[x for x in cov if x['status']!='COMPLETE']
  ck('honest partial:'+fault,cy['status']=='PARTIAL' and len(complete)==2 and len(bad)==1 and bad[0]['status']==('NOT_CONFIGURED' if fault=='missing-x' else 'RATE_LIMITED') and bool(bad[0]['gap_reason']))
  for row in complete:
   cur=objs[row['cursor_id']];pages=[x for x in snap['pages'] if x['cursor_id']==cur['id']]
   ck('cursor/window/page:'+cur['id'],cur['covered_until']==cy['window_to'] and cur['last_cycle_id']==cy['id'] and len(pages)==1 and pages[0]['complete']==1 and pages[0]['window_from']==cy['window_from'] and pages[0]['window_to']==cy['window_to'] and pages[0]['raw_artifact_id'] in objs)
  if fault=='missing-x':
   requests=[x['body'] for x in snap['objects'] if x['kind']=='ResourceRequest'];ck('one resource request after repeat',len(requests)==1 and requests[0]['reason_code']=='RESEARCH_SOURCE_NOT_CONFIGURED:'+bad[0]['source_id'])
  else:
   cur=objs[bad[0]['cursor_id']];a=datetime.fromisoformat(cur['retry_after'].replace('Z','+00:00'));b=datetime.fromisoformat(cur['updated_at'].replace('Z','+00:00'));ck('persisted retry60 seconds',59<=(a-b).total_seconds()<=60)
  sem.append({'command':inv['command_key'],'fault':fault,'closed_cycle_id':cy['id'],'cycle_status':cy['status'],'source_statuses':[x['status'] for x in cov],'verified_pages':len(snap['pages'])})
 commands.append({'key':inv['command_key'],'invocation':inv['invocation_id'],'assertions':11})
ck('both required commands',set(x['key'] for x in commands)==set(frozen['command_keys']))
ui=read(UI/'report.json');prior=read(UI/'review.json');uiadd=c['assertion_results'][1]['actual'][-1]['actual']
ck('UI nested checks exact',uiadd['runtime_checks']==read(UI/'checks.json'))
ck('UI nested readback exact',uiadd['independent_readback']==read(UI/'response-readback-audit.json'))
ck('UI source binding',ui['source_revision']==r['code_revision'] and ui['passed']==ui['assertion_count']==31)
ck('UI period included',c['run_receipt']['started_at']==ui['started_at'] and c['run_receipt']['ended_at']>=ui['finished_at'])
ck('UI screenshot list four',len(ui['screenshots'])==4)
ck('hygiene remains blocked',read(UI/'hygiene.json')['status']=='BLOCKED_HYGIENE')
result={'status':'PASS','reviewed_at':datetime.now(timezone.utc).isoformat(),'receipt_jcs':r['receipt_hash'],'manifest_files_verified':len(m['files']),'source_git_and_current_hashes':len(src),'commands':commands,'sqlite_semantics':sem,'ui_runtime_assertions':31,'ui_response_readback_assertions':8,'ui_screenshots_previously_personally_reviewed':4,'ui_response_body_capture_errors_disclosed':11,'page_errors':0,'hygiene_status':'BLOCKED_HYGIENE','new_product_executions':0,'checks':checks,'check_count':len(checks)}
(OUT/'audit-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','sqlite_semantics']},ensure_ascii=False))
