from pathlib import Path
import json,hashlib,subprocess,datetime
root=Path(__file__).resolve().parents[4];out=Path(__file__).parent
base=root/'execution/receipts/W06/8af0b592-7e0d-4ced-83d3-32db7670007d';live=root/'execution/receipts/W06/continuation-live/65ebbc11-20bd-4136-aa39-faa2fa3c4849'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
enc=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
digest=lambda x:'sha256:'+hashlib.sha256(x).hexdigest()
receipt=read(base/'receipt.json');manifest=read(base/'artifacts.json');case=read(base/'C01.json');pre=read(base/'environment-before.json');checked={}
def ref(v):
 p=v.get('path',v.get('reference'));h=v['sha256'].removeprefix('sha256:');assert sha(root/p)==h,p;checked[p]=h
def walk(v):
 if isinstance(v,dict):
  if 'sha256' in v and ('path' in v or 'reference' in v):ref(v)
  for child in v.values():walk(child)
 elif isinstance(v,list):
  for child in v:walk(child)
walk(manifest);walk(case);walk(receipt)
assert receipt['artifact_manifest_hash']==sha(base/'artifacts.json')
b=dict(receipt);want=b.pop('receipt_hash');assert digest(enc(b))==want
assert receipt['input_manifest_hash']==sha(root/'spec/v2.0/PACKAGE_MANIFEST.json') and receipt['route_revision']==sha(root/'execution/route.json')
vm=case['version_manifest'];rev=receipt['code_revision'];assert rev==vm['git_head']==pre['git_head']=='7d57b244feaf0cc15974e5ec11d517a10caa5b07'
assert vm['source_sha256']==pre['source_sha256'];assert vm['sampled_at']<case['run_receipt']['started_at']
for path,h in vm['source_sha256'].items():
 actual=subprocess.run(['git','show',rev+':'+path],cwd=root,capture_output=True,check=True).stdout
 assert hashlib.sha256(actual).hexdigest()==h,path
before=read(live/'before.json');assert before['head']==rev
assert before['code_tree']==subprocess.run(['git','rev-parse',rev+'^{tree}'],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
for path,h in before['versions'].items():
 normalized=path.replace(chr(92),'/');actual=subprocess.run(['git','show',rev+':'+normalized],cwd=root,capture_output=True,check=True).stdout;assert digest(actual)==h,path
for path,h in vm['lock_files'].items():ref({'path':path,'sha256':h})
assert vm['rubric']['acceptance_sha256']==sha(root/'spec/v2.0/contracts/acceptance.json')
assert vm['task_gates_sha256']==sha(root/'spec/v2.0/contracts/tasks.json')
cmd=case['command_receipt'];inv=read(root/cmd['reference'])
for key in ['command_key','argv','cwd','environment_names','exit_code','stdout','stderr','registered_command_revision']:assert cmd[key]==inv[key],key
assert cmd['registered_command_revision']==sha(root/'execution/commands.json')
report=read(live/'report.json');assert report['status']=='PASS' and report['exit']==0 and not report['missing'] and not report['unexpected']
for path,h in report['hashes'].items():ref({'path':str((live/path).relative_to(root)),'sha256':h})
frozen=next(x for x in read(root/'spec/v2.0/contracts/acceptance.json')['cases'] if x['id']=='C01')
assert case['run_receipt']['environment_mode']==frozen['mode'];assert case['run_receipt']['executor_identity']!=case['run_receipt']['independent_verifier_identity']=='codex:/root/orchestration_verifier'
assert len(case['assertion_results'])==len(frozen['assertions'])==3
for r,f in zip(case['assertion_results'],frozen['assertions']):
 assert r['assertion_id']==f['id'] and r['expected']==f['expected'] and r['status']=='PASS';assert r['actual'] in report['assertions']
for r in case['supplemental_assertions']:assert r in report['assertions']
raw=(live/'stdout.txt').read_text(encoding='utf-8').splitlines()
for r in report['assertions']:
 line=raw[r['raw']['line']-1];observed=json.loads(line[line.index('{'):]);assert {k:v for k,v in r.items() if k!='raw'}==observed
inp=read(live/'C01-input.json');command=read(live/'C01-command.json');journal=read(live/'C01-journal.json');result=read(live/'C01-result.json');sealed=read(live/'C01-sealed-artifacts.json')
assert command['input_hash']==digest((live/'C01-input.json').read_bytes()) and command['prompt_hash']==digest((live/'C01-prompt.txt').read_bytes())
assert (live/'C01-prompt.txt').read_text(encoding='utf-8').split('INPUT:\n',1)[1]==(live/'C01-input.json').read_text(encoding='utf-8')
assert command['bundle_hash']==digest(enc(inp['bundle']))
assert command['stdout_hash']==digest((live/'C01-000.stdout').read_bytes())
assert journal['streams'][0]['stderr_hash']==digest((live/'C01-000.stderr').read_bytes())
assert journal['streams'][0]['stdout_hash']==command['stdout_hash'];assert journal['state']=='SETTLED' and journal['queue_empty'] and journal['children_stopped'] and journal['launched']==1 and journal['exit_code']==0
assert result==journal['protocol']['result']==command['protocol']['result']==sealed['model_output'];assert command['protocol']['tools_completed']==0 and not command['tool_attempt_observed']
assert command['provider_model_revision'] is None and command['cost'] is None
for opt in ['--ephemeral','--ignore-user-config','--ignore-rules']:assert opt in command['argv']
assert command['no_prior_session'];assert digest(Path(command['argv'][0]).read_bytes())==command['binary_hash']
assert len(inp['materialized_inputs'])==len(inp['manifest']['input_manifest'])==4
for m in inp['materialized_inputs']:
 assert m['manifest_entry'] in inp['manifest']['input_manifest'];assert digest(m['content'].encode())==m['manifest_entry']['content_hash']
for r in inp['records']:
 assert r['record']['id']==r['ref']['id'] and r['record']['revision']==r['ref']['revision']
 if r['ref']['content_hash'] is not None:assert r['ref']['content_hash']==r['record'].get('content_hash',r['record'].get('receipt_hash'))
for r in inp['bundle']['version_vector']:assert any(x['ref']==r for x in inp['records'])
continuation=json.loads(inp['bundle']['summary'].split('Continuation: ',1)[1]);latest=continuation['current_decision_refs'][0];historical=continuation['historical_decision_refs'][0]
lookup={x['ref']['id']:x['record'] for x in inp['records']}
assert lookup[latest['id']]['selected']=='B' and lookup[historical['id']]['selected']=='A' and lookup[latest['id']]['supersedes_id']==historical['id']
assert result['current_decision_id']==latest['id'] and result['current_decision_revision']==latest['revision'] and result['historical_decision_id']==historical['id']
assert result['goal_id']==continuation['goal_id'] and result['goal_intent']==continuation['goal_intent'] and result['next_task_id']==continuation['next_task_id']
source=next(x for x in inp['materialized_inputs'] if x['manifest_entry']['ref']['id']==result['source_id']);content=json.loads(source['content'])
assert result['source_hash']==source['manifest_entry']['content_hash'];assert result['operands']==content['operands']==[17,25]
assert result['operation']==content['operations'][lookup[latest['id']]['selected']]=='MULTIPLY' and result['total']==17*25==425
questions=read(live/'C01-question-events.json');assert result['questions']==questions['model_requests']==questions['events']==[] and questions['after']==questions['before']==0
log={'model_output':result,'command':command,'source_ref':source['manifest_entry']['ref'],'decision_ref':latest,'bundle_ref':inp['manifest']['bundle_ref'],'host_computation_passed':True}
# Go preserves Protocol struct field order inside command; reuse exact archived command bytes.
log_bytes=b'{'+b','.join(enc(k)+b':'+((live/'C01-command.json').read_bytes() if k=='command' else enc(log[k])) for k in sorted(log))+b'}'
assert digest(log_bytes)==sealed['computation_log']['content_hash'] and len(log_bytes)==sealed['computation_log']['byte_size']
assert digest(enc(result['candidate']))==sealed['result']['content_hash']
a=sealed['acceptance'];assert a['verdict']=='PASS' and a['independence_basis']=='DETERMINISTIC_SERVICE' and a['measurement_mode']=='FIXTURE'
assert a['verifier_principal_id'] not in a['executor_principal_ids'];assert a['run_id']==journal['spec']['run_id'] and a['subject_ref']['id']==result['next_task_id']
assert sealed['computation_log']['run_id']==a['run_id'] and sealed['computation_log']['sealed_at']
assert a['artifact_refs'][0]['id']==sealed['result']['id'] and a['artifact_refs'][0]['content_hash']==sealed['result']['content_hash']
assert latest in a['input_refs'] and source['manifest_entry']['ref'] in a['input_refs']
summary={'status':'PASS','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executor_receipt_sha256':sha(base/'receipt.json'),'executor_receipt_jcs_hash':want,'artifact_manifest_sha256':sha(base/'artifacts.json'),'artifact_count':len(manifest),'distinct_references_checked':len(checked),'live_code_revision':rev,'source_files_git_verified':len(vm['source_sha256']),'before_git_tree_verified':before['code_tree'],'C01_frozen_ids':[x['id'] for x in frozen['assertions']],'formal_assertions':report['assertion_ids'],'materialized_artifact_hashes_verified':4,'record_bindings_verified':len(inp['records']),'context_vector_records_verified':len(inp['bundle']['version_vector']),'calculation':{'effective_option':'B','operation':'MULTIPLY','operands':[17,25],'total':425,'superseded_option':'A','superseded_total':42},'questions_observed':0,'tool_attempts_observed':0,'sealed_full_computation_log_bytes_and_hash_verified':True,'independent_service_acceptance':'PASS_FIXTURE','model_provider_revision':None,'cost':None,'checked_references':checked}
(out/'envelope-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='checked_references'},ensure_ascii=True,indent=2))
