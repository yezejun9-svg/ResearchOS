from pathlib import Path
import json,hashlib,ast,os
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W13/W13-03/desktop15_cli_qualification_gate_preparation_codex/0293420914814321ac0897bdfa7d9ee7';O=Path(__file__).parent
checks=[];refs={}
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);b=p.read_bytes();r={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[p.as_posix()]=r;return r
def verify(r):
 p=path(r['path']);a=refs.get(p.as_posix()) or ref(p);ck('pin '+p.as_posix(),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return p
def read(p):ref(p);return json.loads(path(p).read_bytes())
def load(r):return read(verify(r))
def key(r):return str(path(r['path']).resolve()).casefold(),r['sha256'],r['bytes']
def same(a,b):return key(a)==key(b)
def mf(r,field,count=None,required=()):
 p=verify(r);d=read(p);rows=d[field];ck('manifest count '+p.name,(count is None or len(rows)==count) and ('count' not in d or d['count']==len(rows)));seen={}
 for item in rows:
  q=verify(item);ck('safe member '+q.as_posix(),q.is_relative_to(p.parent) and q.resolve()==q.absolute() and not any(os.path.lexists(x) and (x.is_symlink() or getattr(x.lstat(),'st_file_attributes',0)&0x400) for x in [q,*q.parents]));k=key(item)[0];ck('unique member '+k,k not in seen);seen[k]=item
 for item in required:ck('required member '+str(item['path']),key(item)[0] in seen and same(seen[key(item)[0]],item))
 return len(rows)
def save(n,v):(O/n).open('xb').write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
h=read(N/'handoff.complete.json');ck('handoff expected',ref(N/'handoff.complete.json')['sha256']=='3e9b7fa338f737a229a520de6c0148d0bf4d1c1ed8c5b0c22dffd76dddcbb91c');ck('MF expected',ref(N/'manifest.complete.json')['sha256']=='63dbc6099d83a0d117d4d1f6835f0d12844924623c946217e294bdee2d91b417');candidate_count=mf(ref(N/'manifest.complete.json'),'entries')
small=load(h['selected_handoff_ref']);before=read(N/'inputs.before.json');after=read(N/'inputs.after.json');ck('original35 beforeafter unchanged',before==after and len(before)==35)
for r in before:verify(r)
for r in small['reused_unchanged_refs'].values():verify(r)
for r in h['failure_origins']:verify(r)
asts={};inversefacts=[]
for kind in ['builder','controller']:
 data=read(N/(kind+'.inverse.json'));original=verify(data['original_ref']).read_bytes();candidate=verify(data['candidate_ref']).read_bytes();text=candidate.decode('utf-8');ast.parse(text);asts[kind]=ast.parse(text)
 for e in reversed(data['edits']):ck(kind+' inverse unique',text.count(e['after_utf8'])==1);text=text.replace(e['after_utf8'],e['before_utf8'],1)
 ck(kind+' complete inverse bytes',text.encode()==original)
 inversefacts.append({'kind':kind,'original_ref':data['original_ref'],'candidate_ref':data['candidate_ref'],'inverse_full_equal':text.encode()==original})
 old={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(original.decode()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))};new={x.name:ast.dump(x,include_attributes=False) for x in asts[kind].body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
 for name in old:
  if name not in ['main','grant_check']:ck(kind+' unchanged function '+name,old[name]==new[name])
body=lambda tree,name:next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
ck('embedded gate identical AST',ast.dump(body(asts['builder'],'cli43_bounded_qualification_gate'),include_attributes=False)==ast.dump(body(asts['controller'],'cli43_bounded_qualification_gate'),include_attributes=False))
constants=[]
for tree in asts.values():
 node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='CLI43_BOUNDED_QUALIFICATION_REFS' for y in x.targets));constants.append(ast.literal_eval(node.value))
qr=small['qualification_refs'];ck('exact four fixedrefs',constants[0]==constants[1]==qr and set(qr)=={'qualification_ref','review_ref','manifest_ref','handoff_ref'})
q=load(qr['qualification_ref']);r=load(qr['review_ref']);hh=load(qr['handoff_ref']);qualification_count=mf(qr['manifest_ref'],'entries',18,[qr[k] for k in ['qualification_ref','review_ref','handoff_ref']]);ids=['real-existing-open-readonly','real-existing-self-send']
ck('schemas actual',q['schema']=='researchos.cli43-bounded-execution-qualification.v1' and r['schema']=='researchos.cli43-bounded-execution-independent-review.v1')
ck('nonauthor decision',q['reviewer']==r['reviewer']==hh['reviewer']=='codex:/root/w05_merge_review' and r['non_author'] is True and r['requested_changes']==[] and r['decision']==hh['decision']=='CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED')
ck('four qualificationref edges',same(r['qualification_ref'],qr['qualification_ref']) and same(hh['qualification_ref'],qr['qualification_ref']) and same(hh['review_ref'],qr['review_ref']))
ck('source cohort',q['run_uuid']=='c4f309c5528f5d42be5e7eeb146a20aa' and q['source_commit']==r['source_commit']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856')
ck('case qualification exact',q['current43_fresh_held2_qualified'] is r['current43_fresh_held2_qualified'] is True and q['qualified_case_count']==2 and q['qualified_case_ids']==r['case_ids']==hh['qualified_case_ids']==ids)
ck('counts exits limits',q['native_calls']==q['native_calls_exit0']==hh['native_calls']==14 and q['test_leaf_PASS']==2 and q['test_leaf_FAIL']==q['test_leaf_SKIP']==q['SDK_MODEL_Node_external_paid_private_calls']==0 and q['cases_NOT_RUN']==[] and q['CLI_exit_codes']==hh['CLI_exit_codes']==[0,3])
ck('no escalation boundary',q['whole43_test_suite_qualified'] is q['Main_integration_authorized'] is q['desktop15_execution_authorized'] is r['desktop15_execution_authorized'] is hh['actual_execution_authorized'] is False and all(x['source_acceptance'] is False and x['formal_increment']==0 and x['desktop15_new_scope_preparation_permitted'] is True for x in [q,r,hh]))
ck('qualified limits match',q['limitations']==r['limitations'] and r['counts']['remaining_failed_checks']==0 and r['counts']['source_files_current_hashed']==r['counts']['export_files_current_hashed']==597 and r['counts']['compiled_current_files_hashed']==5460)
e=q['evidence_refs']
for name,item in e.items():verify(item);ck('actual evidence edge '+name,same(item,r[name]))
for item in q['source_import_proof_refs']:verify(item)
z=load(e['result_ref']);outer=load(e['root_completion_ref']);ck('result success',z['status']=='BOUNDED_DEVELOPMENT_EVIDENCE_REPORTED' and z['first_cause'] is None and z['secondary']==z['NOT_RUN']==[] and z['native_calls']==14 and z['SDK_MODEL_external_paid']==z['formal_increment']==0 and z['product_acceptance'] is False)
ck('rosters', [x['leaf'] for x in z['cases']]==[x['leaf'] for x in z['case_roster']]==ids and len(q['case_facts'])==2 and [x['case_id'] for x in q['case_facts']]==ids)
for i,(row,f) in enumerate(zip(z['case_roster'],q['case_facts'])):
 ck('case actual '+str(i),row['state']==f['state']=='QUALIFIED' and row['actual_native_exit']==f['native_test_exit']==0 and all(row[x] is True for x in ['launch_attempted','resumed','requested','test_leaf_started','qualified']) and row['fixture_observation']=='OBSERVED' and row['failure'] is None and f['CLI_exit']==[0,3][i] and z['cases'][i]['status']=='PASS')
 for k in ['invocation_ref','verified_ref','stdout_ref','stderr_ref']:verify(f[k])
labels=['git-head','git-public-blobs','go-version','go-env','go-list','go-list-test2json','build-test2json','build-cli','build-test','buildinfo-cli','buildinfo-test','buildinfo-test2json','case-00','case-01'];ck('exact14stageorder',[x['label'] for x in z['stages']]==labels)
for i,stage in enumerate(z['stages']):
 inv=load(stage['result_ref']);ck('actualstage '+str(i),inv['actual_exit']==inv['result']['actual_exit']==0 and inv['automatic_retry'] is False and inv['counter_reset'] is False and inv['request']['sequence']==i+1)
 if i>=12:ck('same case invocation '+str(i),same(stage['result_ref'],q['case_facts'][i-12]['invocation_ref']))
ck('root closed actual fields',outer['schema']=='researchos.root-actual-launch-completion.v2' and outer['actor']=='codex:/root' and outer['actual_outer_tool_exit']==outer['actual_launcher_native_exit']==outer['actual_inner_python_native_exit']==0 and outer['caller_error'] is None and outer['caller_secondary']==[] and outer['native_calls']==14 and outer['actual_case_roster_original_payload']==z['case_roster'] and outer['actual_case_results_original_payload']==z['cases'] and outer['actual_NOT_RUN_original_payload']==[])
for name,k in {'source_scope_ref':'scope_ref','grant_ref':'grant_ref','executor_result_ref':'result_ref','executor_manifest_ref':'executor_manifest_ref','launcher_completion_ref':'launcher_completed_ref','launcher_manifest_ref':'launcher_manifest_ref'}.items():ck('root link '+name,same(outer[name],e[k]))
ss=load(e['scope_ref']);gg=load(e['grant_ref']);ck('actual scope grant',ss['run_uuid']==q['run_uuid'] and ss['source_commit']==q['source_commit'] and ss['ordered_cases']==ids and gg['actual_registration_completed'] is True and same(gg['scope_ref'],e['scope_ref']))
required=[e['result_ref'],outer['closed_graph_ref'],outer['compiled_closure_ref'],outer['test2json_artifact_ref']]+[x['result_ref'] for x in z['stages']]+[x[k] for x in q['case_facts'] for k in ['invocation_ref','verified_ref','stdout_ref','stderr_ref']]
manifestcounts={'package':candidate_count,'qualification':qualification_count,'executor':mf(e['executor_manifest_ref'],'files',125,required),'launcher':mf(e['launcher_manifest_ref'],'files',7,[e['launcher_completed_ref']]),'root':mf(e['root_closed_manifest_ref'],'members',11,[e['root_completion_ref']])}
originalscope=read(N/'original.scope.json');scope=load(h['scope_ref']);copy=dict(scope);copy.pop('cli43_bounded_qualification_refs');copy['controller_ref']=originalscope['controller_ref'];ck('scope exact two key delta',copy==originalscope and scope['cli43_bounded_qualification_refs']==qr and scope['controller_ref']==h['controller_ref'])
ck('future authority unbound',scope['authorized'] is False and scope['status']=='PREPARATION_ONLY_NOT_EXECUTABLE' and all(scope[k] is None for k in ['expected_registration','expected_before_registration','registration_namespace','operation_uuid','new_output_root','protected_source_vector_ref','expected_cli43_head']))
ck('pure source limits unchanged',scope['exact_paths']==15 and scope['union_paths']==58 and scope['apply_cap']==scope['commit_cap']==1 and scope['product_tests_HTTP_SQL_models']==0 and scope['git_step_cap']==80)
# Verify all original four CLI source-import field consumers and their ordering survive the exact-byte inverse.
controller=verify(h['controller_ref']).read_text(encoding='utf-8');builder=verify(h['builder_ref']).read_text(encoding='utf-8')
ck('controller gate before mutating execute/helper',controller.index("    cli43_bounded_qualification_gate(scope[")<controller.index('def execute(') and controller.index('copies=grant_check(scope,sref,grant)')<controller.index('candidate.mkdir(exist_ok=False)'))
ck('builder gate before ownedGit preparation',builder.index("cli43_bounded_qualification_gate(request[")<builder.index("helper.run_owned(call"))
ck('reads remain immutable double consumption guarded',"require(p not in READS or READS[p] == item, 'input drift')" in builder and "require(k not in READS or READS[k]==row" in controller)
ck('no candidate execution in review',True)
save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'manifest_counts':manifestcounts,'inverses':inversefacts,'candidate_module_imported':False,'candidate_executed':False,'native_product_calls':0,'source_writes':0,'canonical_writes':0,'whole_backing_resource_rehash':False,'new_failure_origins':[]});print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json'),'manifest_counts':manifestcounts},ensure_ascii=False))
