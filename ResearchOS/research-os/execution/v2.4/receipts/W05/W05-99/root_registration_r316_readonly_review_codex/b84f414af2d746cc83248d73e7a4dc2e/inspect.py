from pathlib import Path
import ast,json,hashlib,datetime,subprocess
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-harness-v4-r316'
reads={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':sha(b),'bytes':len(b)}
def read(p):
 p=Path(p);b=p.read_bytes();reads[p]=b;return b
def check(name,value):checks.append({'check':name,'ok':bool(value)})
def verify(x,base=R):
 p=Path(x['path']);p=p if p.is_absolute() else base/p;b=read(p)
 check('hash '+str(p),sha(b)==x['sha256'])
 if 'bytes' in x:check('bytes '+str(p),len(b)==x['bytes'])
 return b
def save(name,x):
 b=x if isinstance(x,bytes) else (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 with (O/name).open('xb') as f:f.write(b)
 return ref(O/name,b)
pins={'register.py':'dbc2f4cee5720cd2008a57f5ecfc931dcc04e9775534d4332614a5e4b85006a9','run.py':'8844cd9f5f40c814159cc4335d01970873ba373ebf777799ce00d1ac8d35e58e','prepared_refs.json':'f8663262c4983a6c0f6ccccc26f49d438a70c8fc175e95c4f411a0066d682f75','audit.json':'5baf798b184623272bce050e7ce6d051e14abcbb1278ebd039a22d30c4d77560','scope_registration.json':'e1213dd4e0d26a2010bd209cbbafee1425a497071c6c0964f47ce4a57c0804b0','seal.py':'2fa37609c5e4d7a3f80eef3609469bd42f9e5033ba5725f5b561061871c56ea9'}
for name,h in pins.items():
 b=verify({'path':str(N/name),'sha256':h});save('input-'+name,b)
 if name.endswith('.py'):ast.parse(b)
p=json.loads(read(N/'prepared_refs.json'))
for x in p['verified_refs']:verify(x)
canon=[];copied=[]
for i,x in enumerate(p['canonical_before']):
 b=verify(x);canon.append(json.loads(b));copied.append(save('canonical-before-'+str(i+1)+'-'+Path(x['path']).name,b))
cp,ow=canon[:2]
check('canonical order',[x['path'] for x in p['canonical_before']]==['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/step_state.json','execution/v2.4/commands.json'])
check('before revisions',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[315,143,393])
check('source writers preserved',ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']['current_source_writer']=='codex:/root/command_queue_impl' and ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer']=='codex:/root/sources_parent_impl')
check('new chain absent','W05-99/r315-utf8-and-review-Desktop-finite-origins' not in cp['failure_chains'])
origins=p['origins'];keys=[x['origin_key'] for x in origins]
check('13 unique new origins',len(keys)==len(set(keys))==13 and not set(keys)&{x.get('origin_key') for x in cp['failure_counters']})
check('kind counts',sum(x['event_kind']=='ACTUAL_NONZERO_EXECUTION' for x in origins)==11 and sum(x['event_kind']=='QUALIFICATION_DEVIATION' for x in origins)==2)
desktop=R/'.local/worktrees/codex-w1303-desktop-http-r311';mapping=[]
for i,x in enumerate(origins):
 raw=verify(x['evidence_ref']);q=json.loads(raw);save('origin-%02d.json'%i,raw)
 fact={'origin_key':x['origin_key'],'event_kind':x['event_kind'],'registered_outer':x['actual_outer_exit'],'registered_native':x['actual_native_exit'],'original_evidence_ref':x['evidence_ref'],'raw_top_level_keys':list(q)}
 if x['event_kind']=='QUALIFICATION_DEVIATION':
  check('zero qualification '+x['origin_key'],x['actual_outer_exit']==x['actual_native_exit']==x['native_failure_count']==0 and x['qualification_failure_count']==1)
 else:check('nonzero '+x['origin_key'],x['actual_outer_exit']==1 or x['actual_native_exit']==1)
 if x['actor']=='codex:/root/sources_parent_impl':
  native=q['native_exit'] if 'native_exit' in q else q['native_node_exit']
  check('desktop raw exit mapping '+x['origin_key'],native==x['actual_native_exit'] and q['wrapper_outer_exit']==x['actual_outer_exit'])
  filemap={}
  for rr in q['refs']:
   rb=verify(rr,desktop);path=desktop/rr['path'];filemap[Path(rr['path']).name]=(path,rb)
  inv=json.loads(filemap['invocation.json'][1]);check('actual invocation exit '+x['origin_key'],inv['exit']==native)
  for stream in ('stdout','stderr'):
   if stream in filemap:check('actual raw '+x['origin_key']+stream,sha(filemap[stream][1])==inv[stream+'_sha256'])
  fact.update(actual_invocation=inv,original_cause=q.get('cause',q.get('actual_cause_boundary')),nested_exit=q.get('nested_electron_exit',q.get('actual_nested_node_test_exit')),raw_validator_children=q.get('direct_validator_children',q.get('actual_direct_validator_children',q.get('observed_children'))))
  if 'ce8887' in x['origin_key']:check('ce8887 original children7',q['direct_validator_children']==7 and inv['child_count']==7)
 elif x['actor']=='codex:/root/command_queue_impl':
  report=json.loads(verify(x['stopped_report_ref']))
  check('cmd schema mapping',q['actual_driver_exit']==x['actual_native_exit']==1 and report['actual_outer_exit']==1 and report['actual_cases']==0 and len(report['NOT_RUN'])==14)
  check('cmd original report retained',x['original_stopped_report']==report)
  for inv in q['invocations']:
   z=json.loads(verify(inv['ref']));check('cmd child '+inv['name'],z['actual_exit']==inv['actual_exit']==0)
  fact.update(actual_product_exit_original=q['actual_product_exit'],registered_product_exit=x['actual_product_exit'],compile_exit=report['actual_compile_exit'],cases=report['actual_cases'],retained_original_invocation_count=len(q['invocations']))
 else:
  check('tool raw exit mapping '+x['origin_key'],q['actual_outer_exit']==x['actual_outer_exit'] and q['actual_native_exit']==x['actual_native_exit'])
  fact.update(raw_limitation=q.get('raw_limitation'),raw_file=q.get('raw_file'),original_tool_ref=q.get('original_tool_ref'))
 mapping.append(fact)
scope=json.loads(read(N/'scope_registration.json'))
check('exact1 scope',scope['source_exact_paths']==['internal/api/v2_sessions_test.go'] and scope['registration_checkpoint']==316)
check('fixed14cap',[scope['cases'],scope['per_case_HTTP_maximum'],scope['total_HTTP_maximum']]==[14,16,224] and scope['previous_same_chain_actual_failures']==3)
check('source not accepted',not scope['source_acceptance'] and not scope['Main_integration_authorized'] and scope['formal_increment']==0)
check('v4 not started',not (R/p['pins']['v4_driver']['path']).with_name('started.json').exists())
lock=json.loads(read(R/'execution/toolchains/locked.json'))['tools']
for key in ('python','git'):verify(lock[key])
git=lock['git']['path'];g2=R/'.local/worktrees/codex-w0599-provider-g2-finite-r307';gitfacts=[]
for label,cwd,args in [('main-head',R,['rev-parse','HEAD']),('main-status',R,['status','--porcelain=v1','--untracked-files=no']),('main-index',R,['diff','--cached','--name-only']),('g2-head',g2,['rev-parse','HEAD']),('g2-status',g2,['status','--porcelain=v1'])]:
 argv=[git,*args];z=subprocess.run(argv,cwd=cwd,capture_output=True);so=save(label+'.stdout.raw',z.stdout);se=save(label+'.stderr.raw',z.stderr)
 gitfacts.append({'argv':argv,'cwd':str(cwd),'actual_exit':z.returncode,'stdout_ref':so,'stderr_ref':se});check(label+' actual exit',z.returncode==0)
 if label=='main-head':check('main head',z.stdout.decode().strip()==p['head'])
 if label=='main-status':check('main status',sha(z.stdout)==p['git_status_sha256'] and len(z.stdout.splitlines())==13 and sum(t[:2]==b' D' for t in z.stdout.splitlines())==11)
 if label in ('main-index','g2-status'):check(label+' empty',z.stdout==b'')
 if label=='g2-head':check('g2 head',z.stdout.decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9')
for name,h in [('runtime_coordinator_windows_test.go','a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'),('runtime_provider_binding_windows_test.go','df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4')]:verify({'path':str(g2/'internal/domain'/name),'sha256':h})
check('all read beforeafter unchanged',all(path.read_bytes()==b for path,b in reads.items()))
failed=[x for x in checks if not x['ok']]
decision='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if not failed else 'REQUEST_CHANGES'
audit=save('audit.json',{'actual_registration_executed':False,'checks':checks,'prepared_refs_count':len(p['verified_refs']),'input_refs':[ref(path,b) for path,b in reads.items()],'origin_mapping':mapping,'readonly_git_invocations':gitfacts,'static_findings':['Exact CP/OW/ST/CM original bytes guarded at wrapper launch and before each replace; HEAD/status/old393 prefix preserved.','Persistent original/desired/temp/intent/done/verified sequence, expected_live and READS refreshed after own writes; no automatic rollback/retry.','13 origins include11 actual nonzero and2 zero-exit QUALIFICATION_DEVIATION; actual exits and nested child counts retained.','Only original312 exact1 harness4 grant changes; Desktop15/G2 grants not expanded; source/Main/formal false.','Seal verifies invocation, reviewed scripts, previous315 metadata chain, actual desired bytes, done hashes and all prepared refs; Root must seal before explicitv4 followup.'],'limitations':['Registration and seal not executed; known same-user file CAS/path TOCTOU remains.','Wrapper launch exception can precede invocation JSON; Root outer raw must preserve actual error.','Source causal descriptions are historical reports, not independent product qualification.'],'new_failure_origins':[]})
review=save('review.json',{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':decision,'requested_changes':failed,'actual_registration_executed':False,'expected_before':[315,143,393],'expected_after':[316,144,406],'register_sha256':pins['register.py'],'wrapper_sha256':pins['run.py'],'prepared_refs_sha256':pins['prepared_refs.json'],'audit_sha256':pins['audit.json'],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copied,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_ref':ref(N/'scope_registration.json'),'registration_sealer_ref':ref(N/'seal.py'),'independent_audit_ref':audit,'conditions':['Root only executes exact reviewed wrapper against unchanged4canonical/HEAD/status.','Only actual316 plus registration seal and precise Root followup authorize one v4 new-input execution.','Keep2 zero-exit qualification deviations distinct from11 actual nonzero origins.','Source latest f02bcf outside this fixed13cut remains pending; no source acceptance.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]})
manifest=save('manifest.json',{'entries':[ref(x) for x in sorted(O.iterdir()) if x.is_file()],'self_excluded':True})
handoff=save('handoff.json',{'decision':decision,'review_ref':review,'manifest_ref':manifest,'actual_registration_executed':False,'new_failure_origins':[],'formal_increment':0})
print(json.dumps({'review':review,'manifest':manifest,'handoff':handoff,'failed_checks':failed},ensure_ascii=True))
