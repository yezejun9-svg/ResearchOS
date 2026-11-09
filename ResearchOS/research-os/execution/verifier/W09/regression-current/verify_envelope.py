from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
RUN='887e8883-101f-4c3f-a9f6-85beee26127f';BASE=ROOT/'execution/receipts/W09'/RUN;REV='98468b525d7b88e49d23d434a1d39fcdd403b725'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jcs(v):
 def check(x):
  if isinstance(x,dict):
   assert all(k.isascii() for k in x)
   for y in x.values():check(y)
  elif isinstance(x,list):
   for y in x:check(y)
  else:assert x is None or isinstance(x,(str,bool)) or type(x) is int and abs(x)<2**53
 check(v);return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def committed(path):return subprocess.check_output(['git','show',REV+':'+path],cwd=ROOT)
receipt=load(BASE/'receipt.json');manifest=load(BASE/'artifacts.json');env=load(BASE/'environment-before.json');ac=load(ROOT/'spec/v2.0/contracts/acceptance.json');tasks=load(ROOT/'spec/v2.0/contracts/tasks.json')
assert receipt['code_revision']==env['git_head']==REV and receipt['executor_identity']=='codex:/root' and receipt['status']=='EXECUTION_REPORTED'
assert receipt['verifier_identity'] is None and receipt['owned_acceptance_status']=='PENDING_INDEPENDENT_VERIFIER'
assert receipt['receipt_hash']=='sha256:'+hashlib.sha256(jcs({k:v for k,v in receipt.items() if k!='receipt_hash'})).hexdigest()
assert receipt['artifact_manifest_hash']==sha(BASE/'artifacts.json');assert len(manifest)==129 and len({x['path'] for x in manifest})==129
for a in manifest:assert sha(ROOT/a['path'])==a['sha256'],a['path']
for p,h in env['source_sha256'].items():assert hashlib.sha256(committed(p)).hexdigest()==h,p
assert datetime.fromisoformat(env['sampled_at'])<datetime.fromisoformat(receipt['started_at'])
assert env['tracked_status_porcelain']=='' and env['git_status_porcelain']!=''
assert len(ac['cases'])==42 and all(c['status']=='NOT_RUN' for c in ac['cases'])
package=load(ROOT/'spec/v2.0/PACKAGE_MANIFEST.json')
for a in package['files']:
 p=ROOT/'spec/v2.0'/a['path'];assert sha(p)==a['sha256'] and p.stat().st_size==a['size_bytes'],a['path']
assert receipt['input_manifest_hash']==sha(ROOT/'spec/v2.0/PACKAGE_MANIFEST.json')
assert receipt['route_revision']==sha(ROOT/'execution/route.json')
assert sorted(receipt['changed_paths'])==sorted(subprocess.check_output(['git','diff','--name-only',receipt['base_revision'],REV],cwd=ROOT,text=True).splitlines())
command_results=[];raw_rows={}
for item in receipt['verification_results']:
 ip=ROOT/item['actual_invocation_reference'];r=load(ip);assert r['status']==item['status']=='PASS' and r['exit_code']==r['child_exit_code']==0 and r['code_revision']==REV
 assert r['argv'] and Path(r['cwd'])==ROOT and r['assertion_ids']==item['assertion_ids']
 assert r['registered_command_revision']==sha(ROOT/'execution/commands.json') and r['toolchain_revision']==sha(ROOT/'execution/toolchains/locked.json')
 for stream in ['stdout','stderr']:assert sha(ROOT/r[stream]['path'])==r[stream]['sha256']
 for p in item['raw_evidence_references']:assert any(x['path']==p for x in manifest),p
 outer=load(ROOT/r['stdout']['path'])
 if r['command_key']=='build.check':assert outer['status']=='PASS' and len(outer['assertion_ids'])==9 and all(c['exit_code']==0 and c['argv'] and c['cwd'] for c in outer['commands'])
 if 'report_reference' in outer:
  child=load(ROOT/outer['report_reference']);assert child['exit_code']==0 and child['status']=='PASS';assert child['version_manifest']['git_head']==REV
  events=[json.loads(l) for l in (ROOT/child['raw_evidence_references'][0]).read_text(encoding='utf-8').splitlines()]
  passed={e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')};assert set(child['selected_tests'])<=passed
  records=[]
  for e in events:
   line=e.get('Output','').strip()
   if line.startswith('W09_ASSERTION '):records.append(json.loads(line.removeprefix('W09_ASSERTION ')))
  assert sorted(x['assertion_id'] for x in records)==sorted(r['assertion_ids'])==sorted(child['expected_assertion_ids'])
  assert all(x['status']=='PASS' for x in records);raw_rows[r['invocation_id']]=records
 command_results.append({'reference':item['actual_invocation_reference'],'sha256':sha(ip),'command_key':r['command_key'],'selectors':r['selectors'],'assertion_count':len(r['assertion_ids']),'status':'PASS'})
case_results=[]
for case_id in ['A06','C19']:
 g=load(BASE/(case_id+'.json'));case=next(c for c in ac['cases'] if c['id']==case_id);run=g['run_receipt'];vm=g['version_manifest']
 assert g['global_evidence_id']=='GLOBAL_EVIDENCE_V1' and run['case_id']==case_id and run['environment_mode']==case['mode']=='FIXTURE'
 assert run['executor_identity']!=run['independent_verifier_identity']=='codex:/root/retrieval_verifier'
 assert vm['git_head']==REV and vm['tracked_source_clean'] is True and vm['working_tree_clean'] is False
 assert vm['source_sha256']==env['source_sha256'] and vm['rubric']['acceptance_sha256']==sha(ROOT/'spec/v2.0/contracts/acceptance.json')
 assert vm['task_gates_sha256']==sha(ROOT/'spec/v2.0/contracts/tasks.json')
 for p,h in vm['lock_files'].items():assert sha(ROOT/p)==h
 for row in vm['policy_versions']+[vm['preflight_reference']]:assert sha(ROOT/row['path'])==row['sha256']
 assert vm['model_runtime']['status']=='NOT_APPLICABLE' and vm['model_runtime']['reason'] and vm['input_snapshots']
 assert {a['assertion_id'] for a in g['assertion_results']}=={a['id'] for a in case['assertions']}
 for actual in g['assertion_results']:
  expected=next(a for a in case['assertions'] if a['id']==actual['assertion_id']);assert actual['expected']==expected['expected'] and actual['status']=='PASS' and actual['actual']
  for row in actual['raw_evidence']:assert sha(ROOT/row['path'])==row['sha256']
  for row in actual['actual']:
   cleaned={k:v for k,v in row.items() if k!='raw_evidence_reference'};assert cleaned in raw_rows[run['run_id']]
 for cr in g['command_receipt']:
  assert sha(ROOT/cr['reference'])==cr['sha256'];r=load(ROOT/cr['reference'])
  for k in ['argv','cwd','environment_names','exit_code','stdout','stderr','command_key']:assert cr[k]==r[k]
 assert g['acceptance_receipt']['reference']=='execution/verifier/W09/'+RUN+'.json'
 case_results.append({'case_id':case_id,'frozen_mode':case['mode'],'actual_runtime_scope':run['actual_runtime_scope'],'frozen_assertion_ids':[a['id'] for a in case['assertions']],'global_evidence_reference':str((BASE/(case_id+'.json')).relative_to(ROOT)).replace('\\','/'),'global_evidence_sha256':sha(BASE/(case_id+'.json')),'status':'PASS'})
task=next(t for t in tasks['tasks'] if t['task_id']=='W09');assert task['depends_on']==['W03','W07'] and set(task['owned_acceptance_ids'])=={'C19','A06'}
predecessors=['execution/verifier/W03/3de29703-976f-4fed-870b-62123619053b.json','execution/verifier/W07/d0c0e908-9e50-4202-88e4-fcbc6a7b9990.json']
assert all(load(ROOT/p)['status']=='CONSTRUCTION_ACCEPTED' for p in predecessors)
report={'status':'PASS','verifier_identity':'codex:/root/retrieval_verifier','checked_at':datetime.now(timezone.utc).isoformat(),'candidate_revision':REV,'executor_receipt_reference':str((BASE/'receipt.json').relative_to(ROOT)).replace('\\','/'),'executor_receipt_sha256':sha(BASE/'receipt.json'),'executor_receipt_jcs_hash':receipt['receipt_hash'],'manifest_reference':str((BASE/'artifacts.json').relative_to(ROOT)).replace('\\','/'),'manifest_sha256':sha(BASE/'artifacts.json'),'verified_artifact_count':len(manifest),'verified_preflight_source_count':len(env['source_sha256']),'verified_spec_file_count':len(package['files']),'frozen_not_run_case_count':len(ac['cases']),'commands':command_results,'cases':case_results,'predecessors':[{'reference':p,'sha256':sha(ROOT/p)} for p in predecessors],'evidence_limit':'Build report retains child output tails and exit codes; full W09 selected-test JSONL and independent probe raw are separately retained. Deterministic fixture inputs are fixed in hash-bound source; this is not external source/model evaluation.'}
(OUT/'envelope-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':'PASS','artifacts':len(manifest),'sources':len(env['source_sha256']),'cases':case_results},ensure_ascii=True))
