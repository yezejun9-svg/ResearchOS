"""Independent read-only audit of frozen W16 formal package. Never executes product/native tests."""
import base64,datetime,hashlib,io,json,pathlib,subprocess,sys
sys.dont_write_bytecode=True
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[3]
RUN=OUT.name
PACK=ROOT/'execution/receipts/W16'/RUN
PRIOR=ROOT/'execution/verifier/W16/evolution-881e42e'
REV='1768c89ca8a4f2ba4f79240f281c92f3c4683367'
checks=[]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def check(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
def hashed(p,want):check(sha(p)==want.removeprefix('sha256:'),'hash:'+str(p.relative_to(ROOT)))
def canonical(v):
 def inspect(x):
  if isinstance(x,float):raise ValueError('Float requires native JCS')
  if isinstance(x,dict):
   for k,w in x.items():
    if any(ord(c)>65535 for c in k):raise ValueError('Non-BMP key requires native JCS')
    inspect(w)
  elif isinstance(x,list):
   for w in x:inspect(w)
 inspect(v)
 return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def seal(o):return digest(canonical({k:v for k,v in o.items() if k!='receipt_hash'}))
def git_blobs(rev,names):
 names=list(names)
 p=subprocess.run(['git','cat-file','--batch'],input=''.join(rev+':'+n.replace('\\','/')+'\n' for n in names).encode(),cwd=ROOT,stdout=subprocess.PIPE,check=True)
 stream=io.BytesIO(p.stdout);result={}
 for n in names:
  header=stream.readline().split();check(len(header)==3 and header[1]==b'blob','git-blob:'+rev+':'+n)
  result[n]=stream.read(int(header[2]));check(stream.read(1)==b'\n','git-framing:'+n)
 return result
receipt=load(PACK/'receipt.json');manifest=load(PACK/'artifacts.json');env=load(PACK/'environment-before.json')
check(receipt['receipt_hash']==seal(receipt)=='sha256:417fcac1d1ecfc2dace8a2aed34338c11e3f29d2dae9957f0365149d6cf5ff80','frozen-executor-receipt-JCS')
check(receipt['code_revision']==REV and receipt['task_id']=='W16' and receipt['run_id']==RUN,'receipt-identity')
check(receipt['status']=='EXECUTION_REPORTED' and receipt['verifier_identity'] is None,'executor-not-self-approved')
hashed(PACK/'artifacts.json',receipt['artifact_manifest_hash'])
check(len(manifest['files'])==95 and len({r['path'] for r in manifest['files']})==95,'exact-95-artifacts')
for row in manifest['files']:hashed(ROOT/row['path'],row['sha256'])
source=env['source_sha256'];check(len(source)==280 and set(source)==set(receipt['verified_source_paths']),'exact-280-frozen-sources')
check(env['git_head']==REV and env['tracked_source_clean'] and env['tracked_status_porcelain']=='','preflight-clean-source')
blobs=git_blobs(REV,source)
for name,want in source.items():check(hashlib.sha256(blobs[name]).hexdigest()==want,'preflight-git-hash:'+name)
old=load(ROOT/'execution/receipts/W16/f1e68e3d-e065-46f9-a293-fca3ea8c6038/before.json')['version_manifest']['files']
blobs.update(git_blobs(REV,[n.replace('\\','/') for n in old if n.replace('\\','/') not in blobs]))
changed=[]
for name,want in old.items():
 path=name.replace('\\','/');check(path in blobs,'prior-source-listed:'+path)
 if digest(blobs[path])!=want:changed.append(path)
check(changed==['ops/ci/evolution.py'],'prior-reviewed-product-unchanged')
prior_index=load(PRIOR/'evidence-index.json')
for name,want in prior_index['files'].items():hashed(PRIOR/name,want)
hashed(PRIOR/'review.json','f96ebcfe48a93926cca45f36e3af15c339ba05e1a362bd0ffd4ec12d5a250aa5')
prior=load(PRIOR/'review.json');check(prior['gate_verdicts']['W16-G02']=='PASS_IN_FIXTURE_SCOPE','prior-independent-gate-verdict')
# Compile only the pure validator from the frozen runner, without invoking main.
runner_ns={'__name__':'w16_readonly_verifier','__file__':str(ROOT/'ops/ci/evolution.py')}
exec(compile(blobs['ops/ci/evolution.py'],'frozen:ops/ci/evolution.py','exec'),runner_ns)
expected_by_case=runner_ns['CASE_ASSERTIONS']
command_book=json.loads(blobs['execution/commands.json'])
commands=command_book.get('commands',command_book)
evolution_cmd=commands['test.evolution']
check(evolution_cmd['state']=='BOUND' and evolution_cmd['selectors']=={'task_id':['W16'],'check_id':['W16-G02'],'case_id':['C09','C10','C12']},'exact-registered-evolution-selectors')
orchestration=blobs['ops/ci/orchestration.py'].decode()
check("os.getenv('RESEARCHOS_CASE_ID') != 'C10' or os.getenv('RESEARCHOS_CHECK_ID')" in orchestration and "return evolution_main('test.orchestration')" in orchestration,'strict-W16-C10-orchestration-alias')
contracts=json.loads(blobs['spec/v2.0/contracts/acceptance.json']);cases={c['id']:c for c in contracts['cases']}
tasks=json.loads(blobs['spec/v2.0/contracts/tasks.json']);task=next(t for t in tasks['tasks'] if t['task_id']=='W16')
gate=next(g for g in task['task_gate_checks'] if g['check_id']=='W16-G02')
check(gate['mode']=='FIXTURE','G02-frozen-fixture-mode')
allrows={};runs=[];native=[]
case_order=['existing-add','negative-input','instruction-injection','optional-product'];truth=[15,-6,16,21]
def native_verify(v,expected,allow_failure=False):
 r=v['receipt'];check(v['build_hash']==expected and v['raw_hash']==digest(v['raw'].encode()) and base64.b64decode(r['stdout'] or '')==v['raw'].encode(),'native-hash-stdout')
 check(r['pid']>0 and r['appcontainer_sid'] and r['capabilities']==[] and r['children_stopped'],'native-process-sandbox-lifecycle')
 request=v['request'];check(request['phase'] in ('REGRESSION','CANARY','HEALTH'),'native-phase')
 ordered={'phase':request['phase'],'cases':[{k:c[k] for k in ('id','operation','a','b','text')} for c in request['cases']],'protected_paths':request['protected_paths']}
 check(v['input_hash']==digest(json.dumps(ordered,ensure_ascii=False,separators=(',',':')).encode()),'native-frozen-input-hash')
 check([c['id'] for c in request['cases']]==case_order,'native-case-identities')
 bad=bool(v['error']) or r['exit_code']!=0 or r['timed_out']
 if bad:
  check(allow_failure,'native-unexpected-failure')
  return None
 rows=json.loads(v['raw']);check(len(rows)==4 and [r['id'] for r in rows]==case_order,'raw-case-coverage')
 vals=['1' if row['value']==expected else '0' for row,expected in zip(rows,truth)]
 return {'values':vals,'required_passed':all(x=='1' for x in vals[:3]),'correct':vals.count('1'),'rows':rows}
for result in receipt['verification_results']:
 inv=load(ROOT/result['actual_invocation_reference']);key=inv['command_key'];sel=inv['selectors'];label=result['selector_label']
 check(inv['status']==result['status']==result['actual_dispatch_status']=='PASS' and inv['exit_code']==inv['child_exit_code']==result['exit_code']==0,'dispatcher-success:'+label)
 check(inv['code_revision']==REV and sel['task_id']=='W16' and bool(sel['check_id'])!=bool(sel['case_id']),'dispatcher-source-selector:'+label)
 ids=[a for c in expected_by_case.values() for a in c] if sel['check_id'] else expected_by_case[sel['case_id']]
 check(set(ids)==set(inv['assertion_ids']) and len(ids)==len(inv['assertion_ids']) and inv['assertion_ids']==result['assertion_ids'],'dispatcher-assertions:'+label)
 check(inv['registered_command_revision']==source['execution/commands.json'] and inv['toolchain_revision']==source['execution/toolchains/locked.json'] and inv['dispatcher_sha256']==source['execution/command_dispatcher/dispatch.py'],'dispatcher-registered-sources:'+label)
 check(inv['argv'][1:]==commands[key]['argv'],'dispatcher-registered-argv:'+label)
 for version in inv['input_versions']:check(version['sha256']==source[version['path']],'dispatcher-input-version:'+label)
 for kind in ['stdout','stderr']:hashed(ROOT/inv[kind]['path'],inv[kind]['sha256'])
 summary=json.loads((ROOT/inv['stdout']['path']).read_text(encoding='utf-8').splitlines()[-1]);report_path=pathlib.Path(summary['receipt']);directory=report_path.parent
 check(report_path.is_relative_to(ROOT/'execution/receipts/W16'),'child-report-path:'+label)
 report=load(report_path);before=load(directory/'before.json')
 check(summary['assertion_ids']==report['assertion_ids']==inv['assertion_ids'] and summary['assertions']==len(ids),'stdout-child-assertion-chain:'+label)
 check(report['exit_code']==0 and report['status']==report['fixture_assertion_status']=='PASS' and not report['missing'] and not report['unexpected'],'child-exit-and-inventory:'+label)
 check(before['version_manifest']['code_commit']==REV and before['run_receipt']['task_id']=='W16' and (before['run_receipt']['check_id'] or '')==sel['check_id'] and (before['run_receipt']['case_id'] or '')==sel['case_id'],'child-source-selector:'+label)
 check(before['command_receipt']['command_key']==key and before['command_receipt']['resolved_mode']=='fixture','child-exact-command-key:'+label)
 for name,want in before['version_manifest']['files'].items():check(digest(blobs[name.replace('\\','/')])==want,'child-source:'+label+':'+name)
 for name,want in report['hashes'].items():hashed(directory/name,want)
 passed,rows=runner_ns['verify']((directory/'stdout.txt').read_bytes(),0,ids)
 check(passed and rows==report['assertions'],'raw-assertion-parser:'+label)
 for row in rows:allrows[(result['actual_invocation_reference'],row['assertion_id'])]=row
 records=0
 for path in directory.glob('*.json'):
  if not(path.name.endswith('-REGRESSION.json') or path.name.endswith('-CANARY.json')):continue
  doc=load(path);rec=doc['execution'];accept=doc['acceptance']
  check(rec['receipt_hash']==seal(rec) and accept['receipt_hash']==seal(accept) and rec['run_id']==accept['run_id'],'native-record-acceptance-receipts')
  check(rec['scope']=='W16_G02_FIXTURE_ONLY' and rec['state']=='RECORDED','native-record-scope')
  if rec['phase']=='REGRESSION':
   pair=rec['pair'];b=native_verify(pair['baseline'],rec['baseline_hash']);c=native_verify(pair['candidate'],rec['candidate_hash'])
   improved=b['required_passed'] and c['required_passed'] and c['correct']>b['correct']
   check(b==pair['baseline_result'] and c==pair['candidate_result'] and improved==rec['improved']==pair['improved'] and c['required_passed']==rec['required_passed'],'native-independent-regression-outcome')
   check(pair['baseline']['input_hash']==pair['candidate']['input_hash'] and pair['stable_preserved'],'native-same-input-stable-preserved')
  else:
   health=native_verify(rec['stable_health'],rec['baseline_hash']);observed=native_verify(rec['canary'],rec['candidate_hash'],True)
   check(health['required_passed'] and (observed is None or not observed['required_passed'])==rec['observed_regression'],'native-independent-canary-outcome')
   backup=rec['backup_manifest'];restore=rec['restore']
   check(restore['status']=='RESTORED_RECONCILIATION_REQUIRED' and restore['backup_id']==backup['id'] and restore['before']==backup['inventory'],'native-isolated-restore-inventory')
   check(doc['candidate']['status']=='FROZEN','native-terminal-candidate')
  records+=1
 native.append({'selector':label,'execution_records_recomputed':records})
 runs.append({'command_key':key,'invocation_id':inv['invocation_id'],'selector':sel,'assertions':len(ids),'child_report':str(report_path.relative_to(ROOT)).replace('\\','/'),'raw_execution_records_recomputed':records})
check(sorted(r['command_key']+':'+(r['selector']['check_id'] or r['selector']['case_id']) for r in runs)==sorted(['test.evolution:W16-G02','test.evolution:C09','test.evolution:C10','test.orchestration:C10','test.evolution:C12']),'exact-five-formal-commands')
for name in ['C09','C10','C12']:
 c=load(PACK/(name+'.json'));contract=cases[name]
 check(all(c['version_manifest'].get(k)==v for k,v in env.items()) and c['run_receipt']['case_id']==name and c['run_receipt']['environment_mode']=='FIXTURE','case-version-mode:'+name)
 v=c['version_manifest'];hashed(ROOT/v['preflight_reference']['path'],v['preflight_reference']['sha256'])
 extra=v['policy_versions']+v['lock_files']+v['input_snapshots']
 missing=[r['path'] for r in extra if r['path'] not in blobs]
 if missing:blobs.update(git_blobs(REV,missing))
 for row in extra:check(hashlib.sha256(blobs[row['path']]).hexdigest()==row['sha256'],'case-frozen-input:'+row['path'])
 check(hashlib.sha256(blobs['spec/v2.0/contracts/tasks.json']).hexdigest()==v['task_gates_sha256'],'case-task-gate-hash:'+name)
 check([a['assertion_id'] for a in c['assertion_results']]==[a['id'] for a in contract['assertions']],'case-full-assertion-inventory:'+name)
 check(sorted(x['command_key'] for x in c['command_receipt'])==sorted(contract['command_keys']),'case-all-frozen-commands:'+name)
 for command in c['command_receipt']:
  hashed(ROOT/command['reference'],command['sha256'])
  inv=load(ROOT/command['reference'])
  for key in ['command_key','argv','cwd','environment_names','exit_code','stdout','stderr','registered_command_revision','code_revision']:check(command[key]==inv[key],'case-command-'+key+':'+name)
 for frozen,actual in zip(contract['assertions'],c['assertion_results']):
  check(frozen['expected']==actual['expected'] and actual['status']=='PASS' and len(actual['actual'])==len(contract['command_keys']),'case-frozen-expected:'+frozen['id'])
  for row in actual['actual']:
   ref=row['invocation_reference'];without_ref={k:v for k,v in row.items() if k!='invocation_reference'}
   check(without_ref==allrows[(ref,row['assertion_id'])],'case-exact-raw-row:'+frozen['id'])
  for raw in actual['raw_evidence']:hashed(ROOT/raw['path'],raw['sha256'])
 for row in c['supplemental_assertions']:check({k:v for k,v in row.items() if k!='invocation_reference'}==allrows[(row['invocation_reference'],row['assertion_id'])],'case-supplement-raw:'+name)
 hashed(PACK/(name+'.json'),receipt['owned_acceptance_evidence'][name]['sha256'])
summary={'status':'PASS','task_id':'W16','run_id':RUN,'source_revision':REV,'executor_receipt_jcs_hash':receipt['receipt_hash'],'manifest_files':95,'source_hashes_verified':280,'prior_sources_compared':136,'prior_source_changes':changed,'prior_review_hashes_verified':len(prior_index['files']),'prior_native_review_applicable':True,'checks_passed':len(checks),'registered_runs':runs,'native_execution_records_recomputed':sum(r['execution_records_recomputed'] for r in native),'new_native_test_runs':0,'whole_stage_accepted':False,'accepted_task_gate':['W16-G02'],'accepted_cases':['C09','C10','C12'],'C20':'PARTIAL','A16':'PARTIAL_FIXTURE_ONLY','source_comparison_policy':'Git blobs at frozen 1768c89; later W15/main integration excluded.'}
(OUT/'audit-report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
(OUT/'audit-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))


