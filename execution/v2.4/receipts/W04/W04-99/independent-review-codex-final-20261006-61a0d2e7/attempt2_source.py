import pathlib,json,hashlib,math,collections,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W04/W04-99'
E=B/'executor_codex'
RUN=E/'runs/20261005T225411Z-9b77d17e0eb1'
checked={}
def parse(raw):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d: raise ValueError('duplicate '+k)
   d[k]=v
  return d
 def number(x):
  v=float(x)
  if not math.isfinite(v): raise ValueError('nonfinite')
  return v
 return json.loads(raw,object_pairs_hook=pairs,parse_float=number,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def rd(path):
 p=path if isinstance(path,pathlib.Path) else R/path
 raw=p.read_bytes(); checked[str(p)]=hashlib.sha256(raw).hexdigest()
 return parse(raw)
def ref(v):
 assert isinstance(v,dict) and type(v['path']) is str and type(v['sha256']) is str
 rel=pathlib.PurePosixPath(v['path'])
 assert not rel.is_absolute() and not pathlib.PureWindowsPath(v['path']).drive and '\\' not in v['path'] and not {'..','.'}&set(v['path'].split('/'))
 p=(R/v['path']).resolve(strict=True); assert p.is_relative_to(R.resolve()) and p.is_file()
 raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest(); assert actual==v['sha256'],(v['path'],actual,v['sha256'])
 checked[str(p)]=actual
 return p
def doc(v):return rd(ref(v))
def rawloc(v):
 p=ref(v); loc=v['locator']; raw=p.read_bytes()
 if 'json_pointer' in loc:
  out=parse(raw)
  for token in loc['json_pointer'].split('/')[1:]:
   token=token.replace('~1','/').replace('~0','~')
   out=out[int(token)] if isinstance(out,list) else out[token]
  assert out is not None and out!=''
  return out
 lines=raw.decode('utf8').splitlines()
 assert type(loc['line_start']) is int and type(loc['line_end']) is int and 1<=loc['line_start']<=loc['line_end']<=len(lines)
 return '\n'.join(lines[loc['line_start']-1:loc['line_end']])
ctx=rd(B/'integration_codex/current_context_codex.json'); index=doc(ctx['execution_index'])
proof=doc(rd(E/'current_proof.json')['proof_ref'])
vec=doc(proof['version_vector_ref'])
assert ctx['version_vector']==vec
go=doc(proof['go_invocation_ref']); package=doc(proof['package_invocation_ref'])
go_path=ref(go['stdout']); ref(go['stderr']); ref(package['stdout']); ref(package['stderr'])
events=[parse(l) for l in go_path.read_bytes().splitlines()]
runs={(e['Package'],e['Test']) for e in events if e['Action']=='run'}
passes={(e['Package'],e['Test']) for e in events if e['Action']=='pass' and e.get('Test')}
assert runs==passes
assert not [e for e in events if e['Action'] in ['skip','fail']]
pending=collections.defaultdict(str);records={};locations={};starts={}
for n,event in enumerate(events,1):
 if event.get('Action')!='output' or not event.get('Test'):continue
 key=(event['Package'],event['Test']); starts.setdefault(key,n); pending[key]+=event['Output']
 while '\n' in pending[key]:
  line,pending[key]=pending[key].split('\n',1)
  if line.startswith('W04_ASSERTION '):
   row=parse(line[len('W04_ASSERTION '):]); name=(event['Package'],event['Test'],row['assertion_id']);assert name not in records
   records[name]=row;locations[name]=(starts[key],n)
  starts[key]=n
 if not pending[key]:starts[key]=n+1
def rec(id,test=None):
 xs=[(k,v) for k,v in records.items() if k[2]==id and (k[1]==test if test else k[1].startswith('TestW04Current'))]
 assert len(xs)==1,(id,len(xs))
 k,v=xs[0]; assert v['status']=='PASS' and v['expected']==v['actual'],(id,v['expected'],v['actual'])
 return v
def done(data):
 for s,h in checked.items(): assert hashlib.sha256(pathlib.Path(s).read_bytes()).hexdigest()==h,('changed',s)
 print(json.dumps(data,ensure_ascii=False,indent=2))


import fnmatch,ast,types,sys,copy,re
checks=[]
def ck(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
def sha(p):
 p=pathlib.Path(p);raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();checked[str(p.resolve())]=h;return h
def cref(p):return {'path':pathlib.Path(p).relative_to(R).as_posix(),'sha256':sha(p)}
def canonical(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for group in ('spec_files','source_files','input_files','lock_files','tool_files'):
 for row in vec[group]:ref(row)
ck('vector_complete_groups', [len(vec[k]) for k in ('spec_files','source_files','input_files','lock_files','tool_files')]==[5,417,182,3,1])
tools=doc(vec['tool_files'][0]);lock=doc(tools['locked_ref'])
for tool in tools['tools']:ck('locked_tool_'+tool['name'],sha(tool['path'])==tool['sha256'])
coverage=ctx['source_coverage'];discovered=set(coverage['exact_files'])
for root in coverage['roots']:
 for p in (R/root['path']).rglob('*'):
  if p.is_file() and any(fnmatch.fnmatch(p.name,pattern) for pattern in root['patterns']):discovered.add(p.relative_to(R).as_posix())
ck('independent_complete_source_inventory',discovered=={v['path'] for v in vec['source_files']})
ck('source_inventory_digest',canonical(sorted(discovered))==coverage['paths_sha256'])
ck('root_vector_digest',canonical(vec)==ctx['execution_source_snapshot']['version_vector_sha256'])
ck('actual_execution_commit_dirty',ctx['execution_source_snapshot']['code_revision']==proof['code_revision'] and ctx['execution_source_snapshot']['dirty'] is True)
expected=rd(E/'expected.json')
exact={(p,t) for p,tests in expected['go_package_rosters'].items() for t in tests}
ck('29_exact_package_tests',exact==runs==passes and len(runs)==29)
for pkg in expected['go_package_rosters']:
 ck('unique_package_lifecycle_'+pkg,sum(e['Action']=='start' and e['Package']==pkg for e in events)==1 and sum(e['Action']=='pass' and not e.get('Test') and e['Package']==pkg for e in events)==1)
for inv in (go,package):
 ck('actual_exit_'+pathlib.Path(inv['actual_argv'][0]).name,type(inv['exit_code']) is int and inv['exit_code']==0 and inv['status']=='PASS' and inv['mode']=='FIXTURE')
 ck('actual_invocation_time',datetime.datetime.fromisoformat(inv['started_at'])<=datetime.datetime.fromisoformat(inv['ended_at']))
 ck('actual_executable_sha',sha(inv['actual_argv'][0])==inv['executable_sha256'])
 ck('actual_invocation_vector',inv['version_vector_ref']==proof['version_vector_ref'])
ck('go_exact_packages_in_argv',all(p.replace('researchos.local/research-os/','./') in go['actual_argv'] for p in expected['go_package_rosters']))
accept=doc(vec['spec_files'][0]);tasks=doc(vec['spec_files'][1]);plan=doc(vec['spec_files'][2])
formal={c['id']:c for c in accept['cases'] if c['final_owner_task']=='W04'}
ck('frozen_exact_owner_cases',set(formal)=={'C03','C04','A01'})
raw_for_case={}
for cid,parts in index['cases'].items():
 docs={k:doc(v) for k,v in parts.items()}
 run=docs['run_receipt'];version=docs['version_manifest'];results=docs['assertion_results']
 ck('case_identity_'+cid,run['executor_id']=='codex:/root/w1102_impl' and run['verifier_id']=='codex:/root/w1702_review' and run['environment_mode']=='FIXTURE')
 ck('case_actual_snapshot_'+cid,version['code_revision']==proof['code_revision'] and version['dirty'] is True and version['version_vector_ref']==proof['version_vector_ref'])
 ars={a['id']:a for a in results['assertions']};fars={a['id']:a for a in formal[cid]['assertions']}
 ck('case_assertion_roster_'+cid,len(ars)==len(results['assertions']) and set(ars)==set(fars))
 raw_for_case[cid]=[]
 for aid,a in ars.items():
  ck('frozen_expected_'+aid,a['expected']==fars[aid]['expected'] and a['status']=='PASS')
  for r in a['raw_evidence_refs']:
   rawloc(r);raw_for_case[cid].append(r)
  for r in a.get('refusal_evidence_refs',[]):rawloc(r)
  if aid!='A01-03':rec(aid)
 ck('two_formal_commands_'+cid,len(docs['command_receipt']['commands'])==2)
 for command in docs['command_receipt']['commands']:
  ck('direct_command_'+command['command_key']+cid,command['invocation_kind']=='DIRECT_DRIVER' and type(command['exit_code']) is int and command['exit_code']==0)
  out=doc(command['stdout']);ref(command['stderr'])
  ck('direct_complete_ids_'+command['command_key']+cid,set(out['assertion_ids'])==set(ars) and out['mode']=='FIXTURE' and out['status']=='PASS')
  ck('source_pair_'+command['command_key']+cid,{r['sha256'] for r in command['source_invocation_refs']}=={proof['go_invocation_ref']['sha256'],proof['package_invocation_ref']['sha256']})
 for r in results['scenario']['raw_evidence_refs']:rawloc(r)
# Independent business interpretation of original observed records.
c31,c32,c33=[rec('C03-0'+str(i)) for i in (1,2,3)]
e31,e32,e33=[x['evidence'] for x in (c31,c32,c33)]
imp=e31['proposal']['impacted_refs']
ck('C03_only_Artifact_and_dependent_Task',len(imp)==2 and {r['entity_type'] for r in imp}=={'Artifact','Task'} and e31['proposal']['status']=='APPLIED')
ck('C03_D1_D2_immutable_lineage',e31['D1']['id']!=e31['D2']['id'] and e31['D1']['revision']==e31['D2']['revision']==1 and e31['logical_generation']==2)
ck('C03_unrelated_task_excluded_and_continues',e32['bundle']['task_id']==e32['message_receipt']['task_id'] and e32['bundle']['task_id'] not in {r['id'] for r in imp} and e32['message_receipt']['created_at']>e31['proposal']['updated_at'])
ck('C03_unrelated_version_vector_excludes_D1',e31['D1'] not in e32['bundle']['version_vector'])
ck('C03_late_output_is_historical_only',e33['historical_output']['validity']=='STALE' and e31['D1'] in e33['historical_output']['input_refs'])
ck('C03_actual_revision_and_state_refusals',e33['stale_rejection']['code']=='STALE_REVISION' and e33['conflict_rejection']['code']=='STATE_CONFLICT')
c41,c42,c43=[rec('C04-0'+str(i)) for i in (1,2,3)]
e41,e42=c41['evidence'],c42['evidence']
ck('C04_single_integration_current_result',c41['actual']==[201,412,1,'RESOLVED'] and e41['integration_task']['task_type']=='integration' and e41['integration_task']['binding']['route']=='MU_FORK' and len(e41['current_decision'])==1 and e41['applied']['status']=='APPLIED')
ck('C04_wait_for_predecessor',e42['wait']=={'applied_count':0,'sequence':0,'status':'WAITING_FOR_PREDECESSOR'})
ck('C04_deduplicated_ordered_events',len(e42['events'])==len({e['id'] for e in e42['events']})==e42['applied_once']==22 and [e['sequence'] for e in e42['events']]==list(range(1,23)))
ck('C04_same_key_replay_and_different_body',c43['actual']==[201,c43['evidence']['id'],'true',409])
a1=rec('A01-01')['evidence'];impdoc=a1['import'];fixed=a1['fixed_rule'];rh='sha256:b81a28161c9115f3290a9e61e0460d22a516e168071965efd9692a0d45dc2497'
ck('A01_full_pinned_import_scope',impdoc['scope']=='SPECIFICATION_IMPORT_ONLY' and impdoc['product_tests']=='NOT_RUN' and impdoc['goal']['status']=='DRAFT' and impdoc['goal']['acceptance_id'] is None)
ck('A01_four_explicit_fact_bases',len({x['basis'] for x in impdoc['profile']['facts']})==4)
rules=[x for x in impdoc['inventory'] if x['path']=='15_NEW_PROJECT_WORKFLOW.md']
ck('A01_reuses_one_exact_rule',len(rules)==1 and rules[0]['artifact_ref']['id']==fixed['id'] and fixed['content_hash']==rh and fixed['byte_size']==12952)
ck('A01_import_scope_grants_project_only',all(x['resource_id']==impdoc['project_id'] and x['resource_type']=='PROJECT' for x in impdoc['profile']['scope_grants']))
e=rec('A01-02')['evidence']
ck('A01_six_hard_refusals_rollback',set(e['refusals'])=={'tampered-file','traversal','unknown-manifest-field','historical-authority','unlisted-file','wrong-manifest-pin'} and e['before']==e['after'] and all(e['refusals'].values()))
pk=doc(package['stdout'])
ck('A01_package_validation_never_product_acceptance',pk['status']=='PASS' and pk['scope']=='SPECIFICATION_PACKAGE_ONLY' and pk['product_tests']=='NOT_RUN' and pk['errors']==[] and 'manifest_bytes_and_hashes' in pk['checks'])
a4=rec('A01-04')['evidence'];projects=a4['projects']
ck('A01_two_distinct_projects_rules_and_scope_refs',len(projects)==2 and len({p['project_id'] for p in projects})==2 and len({p['rule_ref']['id'] for p in projects})==2 and len({p['workspace_registration']['authorized_workspace_ref'] for p in projects})==2)
for i,p in enumerate(projects):
 ck('A01_project_policy_'+str(i),p['profile']['project_id']==p['state']['project_id']==p['rule_artifact']['project_id']==p['project_id'] and p['state']['binding']['route']=='MU_FORK' and p['rule_ref'] in p['profile']['source_document_refs'] and p['rule_ref'] in p['continued_profile']['source_document_refs'] and p['rule_bytes_sha256']==rh and p['rule_byte_size']==12952 and p['rules_version']=='1.1')
 ck('A01_project_replay_and_continuation_'+str(i),p['bootstrap']==p['replay'] and p['replay_snapshot']==p['replay_snapshot_after'] and p['continued']['project_id']==p['alias_continued']['project_id']==p['project_id'])
 ck('A01_local_first_and_later_not_started_'+str(i),p['stages']['LOCAL_INVENTORY']['status']=='COMPLETED' and all(v['status']=='NOT_STARTED' for k,v in p['stages'].items() if k!='LOCAL_INVENTORY'))
 statuses={x['status'] for x in p['inventory_payload']['entries']}|{x['Status'] for x in p['separate_complete_scanner_result']['Entries']}|{x['Status'] for x in p['unavailable_scanner_result']['Entries']}
 ck('A01_actual_four_scanner_statuses_'+str(i),statuses=={'FOUND','NOT_FOUND','NOT_CHECKED','NOT_ACCESSIBLE'} and bool(p['unavailable_scanner_result']['Failures']))
 for name,v in p['existing_project_documents'].items():ck('A01_preserved_original_'+str(i)+name,v['before_sha256']==v['after_sha256']=='sha256:'+hashlib.sha256(v['original_text'].encode()).hexdigest())
ck('A01_late_failure_rollback_and_scope_refusal',a4['rollback']['before']==a4['rollback']['after'] and a4['rollback']['code']=='CONTENT_HASH_MISMATCH' and a4['unauthorized_scope_refusal'].startswith('PATH_OUT_OF_SCOPE') and a4['later_business_object_count']==0)
for variant in ('absent','different'):
 e=rec('W04-IMPORT-RULES-'+variant)['evidence'];refs=e['profile']['source_document_refs'];rows=[x for x in e['inventory'] if x['path']=='15_NEW_PROJECT_WORKFLOW.md']
 ck('A01_rule_variant_'+variant,e['installed_rules'] in refs and e['installed_rules']['content_hash']==rh and (not rows if variant=='absent' else len(rows)==1 and rows[0]['artifact_ref'] in refs and rows[0]['artifact_ref']!=e['installed_rules']))
workers=rec('W04-G03-EMPTY-WORKERS')['evidence']['workers']
ck('G03_two_empty_worker_materializations',len(workers)==2 and workers[0]==workers[1] and all(w['readonly'] is True and w['rule_size']==12952 and w['rule_sha256']==rh and w['task_acceptance_contract']['require_independent_verifier'] is True for w in workers))
ck('G03_profile_mutation_invalidates',rec('W04-G03-PROFILE')['evidence']['changed_task']['status']=='NEEDS_REVALIDATION')
ck('G03_old_bundle_preserved_new_bundle_distinct',rec('W04-G03-REBUILT')['evidence']['old']!=rec('W04-G03-REBUILT')['evidence']['new'])
ck('G03_revoked_auth_refused',rec('W04-G03-REVOKED')['actual']=='UNAUTHENTICATED')
ck('G03_restricted_data_ordinary_denied',rec('W04-G03-RESTRICTED')['evidence']['ordinary_construction']=='403 rolled back' and rec('W04-G03-RESTRICTED')['evidence']['ordinary_read']=='404' and rec('W04-G03-RESTRICTED')['actual'][-1]==503)
negative_projects=[]
for suffix,status,code in [('required-contract',404,'NOT_FOUND'),('rules-original',422,'CONTENT_HASH_MISMATCH'),('rules-original-missing',None,None),('authorization',401,'UNAUTHENTICATED')]:
 e=rec('W04-H01-'+suffix)['evidence'];negative_projects.append(e['positive_manifest']['project_id'])
 ck('H01_positive_then_rollback_'+suffix,e['positive_original_hash']==rh and e['destination_absent'] is True and e['before']==e['after'] and e['positive_manifest']['bundle_ref']==e['bundle'])
 if status:ck('H01_refusal_'+suffix,e['refusal']['status']==status and e['refusal']['code']==code)
 else:ck('H01_actual_missing_original',e['before']['uploaded_content']==0 and e['error_kind']=='SQL_NO_ROWS_NOT_HTTP_STATUS' and e['refusal']=='sql: no rows in result set')
ck('H01_four_isolated_projects',len(set(negative_projects))==4)
optional=rec('W04-H01-OPTIONAL-RECALL')['evidence']
ck('H01_optional_failure_does_not_block_required_context',len(optional['before']['hits'])==1 and optional['after']['hits']==[] and len(optional['after']['warnings'])>=1 and optional['worker_manifest']['input_manifest'][0]['content_hash']==rh)
# Actual dispatcher records, not normalized summaries.
registry=doc(ctx['registry_ref']);ck('root_registry_snapshot_exact',doc(ctx['registry_snapshot_ref'])==registry)
bindings=[b for b in tasks['verification_command_selection']['formal_case_bindings']+tasks['verification_command_selection']['parent_check_bindings'] if b['task_id']=='W04']
wanted={(b['key'],b.get('case_id') or b.get('check_id')) for b in bindings}
seen=set()
for row in ctx['registered_dispatches']:
 d=doc(row['receipt_ref']);out=doc(d['stdout']);ref(d['stderr'])
 sid=row.get('case_id') or row.get('check_id');key=(row['command_key'],sid);seen.add(key)
 ck('native_selector_'+str(key),key in wanted and d['selectors']['task_id']=='W04' and (d['selectors']['case_id'] or d['selectors']['check_id'])==sid and d['command_key']==key[0])
 ck('native_integer_exit_'+sid+key[0],type(d['exit_code']) is int and type(d['child_exit_code']) is int and d['exit_code']==d['child_exit_code']==0 and d['status']=='PASS')
 ck('native_registered_revision_'+sid+key[0],d['registered_command_revision']==ctx['registry_ref']['sha256'] and d['toolchain_revision']==tools['locked_ref']['sha256'] and d['dispatcher_sha256']==sha(R/'bootstrap/dispatch.py'))
 ck('native_argv_'+sid+key[0],d['argv'][1:]==registry['commands'][key[0]]['argv'] and pathlib.Path(d['cwd']).resolve()==R.resolve())
 ck('native_proof_link_'+sid+key[0],out['execution_index_ref']==ctx['execution_index'] and out['mode']=='FIXTURE' and out['status']=='PASS' and out['proof_ref']==rd(E/'current_proof.json')['proof_ref'])
 required=set(expected['cases'][sid] if sid in expected['cases'] else [sid])
 ck('native_exact_ids_'+sid+key[0],set(d['assertion_ids'])==set(out['assertion_ids'])==required and len(out['assertion_ids'])==len(required))
 for r in d['input_versions']:ref(r)
ck('all_11_actual_native_bindings',seen==wanted and len(ctx['registered_dispatches'])==11)
# Historical failing source remains byte-verifiable and does not count as PASS.
old=E/'runs/20261005T224949Z-418d17844405';oldmanifest=rd(old/'source_snapshot_manifest.json');oldgo=rd(old/'go.json');oldvec=rd(old/'version_vector.json')
ck('failed_original_snapshot_vector',oldmanifest['source_vector_sha256']==sha(old/'version_vector.json') and oldmanifest['unavailable_originals']==[] and len(oldmanifest['snapshots'])==598)
for row in oldmanifest['snapshots']:
 ck('old_snapshot_'+row['original_ref']['path'],row['original_ref']['sha256']==row['snapshot_ref']['sha256']);ref(row['snapshot_ref'])
oldraw=[parse(l) for l in ref(oldgo['stdout']).read_bytes().splitlines()]
failed=[e['Test'] for e in oldraw if e['Action']=='fail' and e.get('Test')]
ck('five_historical_failures_retained',type(oldgo['exit_code']) is int and oldgo['exit_code']!=0 and len(failed)==5)
# Verify already run validator controls, do not repeat suites.
control_receipts=[]
for relative,count in [('formal_validator_codex/synthetic-runs/controls-9714cb682e004c188edf523961283188/receipt.json',65),('formal_validator_codex/generic-controls/runs/controls-ad01f33f58554c5ba2ebb601db3966c7/receipt.json',30)]:
 p=B/relative;d=rd(p);err=p.parent/'stderr.txt';out=p.parent/'stdout.txt'
 ck('control_raw_hashes_'+str(count),sha(err)==d['stderr_sha256'] and sha(out)==d['stdout_sha256'])
 ck('control_actual_pass_'+str(count),type(d['exit_code']) is int and d['exit_code']==0 and d['source_unchanged_during_run'] is True and re.search(r'Ran '+str(count)+r' tests in ',err.read_text('utf8')) is not None and err.read_text('utf8').rstrip().endswith('OK'))
 for name,h in d['source_hashes'].items():ck('control_source_'+str(count)+name,sha(p.parent/'source'/name)==h)
 control_receipts.append(cref(p))
public={'execution/v2.4/formal_case_index.py':'101241f1f06c2e0b8c472ced25fbaebe046e87e62dd58620fd08e46865af77b1','execution/v2.4/parent_gate_ledger.py':'5cb708317a24eebac00173f6ae52c3e4cda41ce08d8a0d9f60a53dcd22b176a8','bootstrap/v24_checkpoint.py':'3b648383c64091821c8274cb08323ca41da47deb5ab1ed69cb032e2112292ee8'}
for name,h in public.items():ck('public_frozen_'+name,sha(R/name)==h)
# Call only a reviewed read-only source function; no dispatcher or product commands.
mod=types.ModuleType('independent_public_formal');mod.__file__=str(R/'execution/v2.4/formal_case_index.py')
exec(compile(pathlib.Path(mod.__file__).read_bytes(),mod.__file__,'exec'),mod.__dict__)
derive=mod.derive_formal_cases(R,R/'execution/v2.4/step_state.json',E/'frozen_inputs/package/contracts/execution.plan.json')
ck('actual_formal_count_still_zero',derive['integrity']=='PASS' and derive['formal_cases_accepted']==0 and len(derive['cases'])==42 and len(derive['owners'])==22)
ck('actual_formal_recheck',mod.recheck_inputs(derive['dependency_snapshot'])['status']=='PASS')
for p,h in derive['input_hashes'].items():ck('derived_read_dependency_'+p,sha(p)==h)
# AST source audit: primitives shared unchanged except isolated registry refresh profile.
original=ast.parse((B/'formal_validator_codex/validate.py').read_text('utf8'))
public_ast=ast.parse(pathlib.Path(mod.__file__).read_text('utf8'))
oldnodes={n.name:n for n in original.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newnodes={n.name:n for n in public_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name in sorted(oldnodes.keys()&newnodes.keys()-{'main'}):ck('shared_primitive_AST_'+name,ast.dump(oldnodes[name],include_attributes=False)==ast.dump(newnodes[name],include_attributes=False))
# Pure memory adversarial controls against fixed parser; no child process and no filesystem mutation.
ev=types.ModuleType('evidence_module');ev.__file__=str(E/'evidence_module.py');exec(compile(pathlib.Path(ev.__file__).read_bytes(),ev.__file__,'exec'),ev.__dict__)
ev.reference=lambda *args,**kwargs:{'synthetic':True,**kwargs}
sys.modules['evidence_module']=ev
pd=types.ModuleType('independent_parent_driver');pd.__file__=str(E/'parent_driver.py');exec(compile(pathlib.Path(pd.__file__).read_bytes(),pd.__file__,'exec'),pd.__dict__)
class Raw:
 def __init__(self,events):self.events=events
 def read_text(self,encoding):return '\n'.join(json.dumps(e) for e in self.events)
pkg='expected/pkg';test='TestExpected';base=[{'Action':'start','Package':pkg},{'Action':'run','Package':pkg,'Test':test},{'Action':'output','Package':pkg,'Test':test,'Output':'W04_ASSERTION '+json.dumps({'assertion_id':'X','expected':True,'actual':True,'status':'PASS','evidence':{'observed':True}})+'\n'},{'Action':'pass','Package':pkg,'Test':test},{'Action':'pass','Package':pkg}]
synthetics=[]
def control(name,fn,accept=False):
 try:fn();outcome=True
 except (ValueError,TypeError,KeyError):outcome=False
 ck('synthetic_'+name,outcome==accept);synthetics.append({'name':name,'expected':'ACCEPT' if accept else 'REJECT','actual':'ACCEPT' if outcome else 'REJECT','scope':'SYNTHETIC_PARSER_CONTROL_NOT_PRODUCT_EVIDENCE'})
control('positive_exact_stream',lambda:ev.assertion_records(None,Raw(base),{pkg:[test]}),True)
for name,stream in [('wrong_package',[{**e,'Package':'other'} for e in base]),('missing_package_completion',base[:-1]),('missing_test_run',base[:1]+base[2:]),('duplicate_package_pass',base+[base[-1]]),('duplicate_test_pass',base[:4]+[base[3]]+base[4:]),('failed_test',base[:3]+[{**base[3],'Action':'fail'}]+base[4:]),('skipped_test',base[:3]+[{**base[3],'Action':'skip'}]+base[4:])]:
 control(name,lambda stream=stream:ev.assertion_records(None,Raw(stream),{pkg:[test]}))
for value in [False,True,None,'0',0.0,1,-1]:control('exit_'+repr(value),lambda value=value:pd.require_invocation_pass({'status':'PASS','mode':'FIXTURE','exit_code':value}))
control('positive_integer_zero',lambda:pd.require_invocation_pass({'status':'PASS','mode':'FIXTURE','exit_code':0}),True)
for raw in ['{"a":1,"a":2}','{"x":NaN}','{"x":Infinity}','{"x":1e999}']:control('strict_json_'+raw,lambda raw=raw:ev.strict_json(raw))
for p,h in checked.items():assert hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h,('input_changed',p)
result={'schema':'researchos.w04.independent-audit-detail.v1','scope':'READ_ONLY_INDEPENDENT_REVIEW_NOT_PRODUCT_REEXECUTION','verifier_id':'codex:/root/w1702_review','issued_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','checks':checks,'check_count':len(checks),'input_hashes':checked,'registered_dispatch_count':len(seen),'product_commands_executed':0,'synthetic_parser_controls':synthetics,'control_receipts':control_receipts,'historical_failed_tests':failed,'current_formal_count_before_registration':derive['formal_cases_accepted'],'raw_evidence_refs_by_case':raw_for_case,'public_source_hashes':public}
out=pathlib.Path(__file__).parent/'audit_result.json'
with out.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks),'input_files':len(checked),'result':str(out),'sha256':sha(out),'synthetic_controls':len(synthetics)},ensure_ascii=False))

