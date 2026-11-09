from pathlib import Path
import json,hashlib,ast
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
P=R/'execution/v2.4/receipts/W05/W05-99';P13=R/'execution/v2.4/receipts/W13/W13-03'
QDIR=P/'cli58_successful_execution_independent_review_codex/83c89c410a1744b8b77d121fd44e5c5e'
REG=P/'integration_codex/desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820'
GATE=P13/'desktop58_cli_root_closure_adapter_revision_preparation_codex/156343f1960f409cbfb1b13af160735f/authorization_adapter.v3.cli_root.proposed.py'
C=[];READS={};HASHED={};MATRIX=[]
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};READS[str(p)]=r;return r
def ck(name,ok,detail=None):C.append({'check':name,'passed':bool(ok),'detail':detail})
def verify(r):
 p=path(r['path']);key=str(p)
 if key not in HASHED:HASHED[key]=pin(p)
 a=HASHED[key];ck('pin '+key,a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return p
def read(r):
 if isinstance(r,dict):p=verify(r)
 else:p=path(r);pin(p)
 return json.loads(p.read_bytes())
def same(a,b):return path(a['path'])==path(b['path']) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def fields(label,obj,keys):
 absent=[k for k in keys if k not in obj];MATRIX.append({'object':label,'required_keys':list(keys),'actual_keys':list(obj),'missing':absent});ck('keys '+label,not absent);return not absent
def mf(ref,field,count,selfkey=None,owned=True):
 m=read(ref);rows=m[field];ck('MF count '+field+str(count),type(rows)is list and len(rows)==count)
 if selfkey:ck('MF self/count '+ref['path'],m[selfkey]is True and m['count']==len(rows))
 out={};base=path(ref['path']).parent
 for r in rows:
  p=verify(r);ck('unique MF member '+str(p),str(p)not in out and p!=path(ref['path']) and (not owned or p.is_relative_to(base)));out[str(p)]=r
 return m,out
q=read(QDIR/'qualification.json');review=read(QDIR/'review.json');scope=read(REG/'scope_registration.json');failure=read(REG/'failure.prepare.json');e=q['evidence_refs']
qm,qmembers=mf(scope['current58_CLI2_manifest_ref'],'entries',18,'self_excluded')
em,ex=mf(e['executor_manifest_ref'],'files',125,'excluded_only_self');lm,la=mf(e['launcher_manifest_ref'],'files',7,'excluded_only_self');rm,rt=mf(e['root_closed_manifest_ref'],'members',169,owned=False)
result=read(e['result_ref']);completed=read(e['launcher_completed_ref']);root=read(e['root_completion_ref']);req=read(root['closure_request_ref']);cs=read(e['scope_ref']);grant=read(e['grant_ref']);caller=read(req['caller_invocation_ref']);intent=read(req['caller_intent_ref']);tools=read(req['tool_observation_ref']);terminal=read(req['terminal_tool_result_ref']);action=read(req['terminal_action_input_ref'])
CASES=['real-existing-open-readonly','real-existing-self-send'];SOURCE='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
fields('qualification',q,['schema','source_commit','reviewer','current43_fresh_held2_qualified','qualified_case_count','qualified_case_ids','native_calls','native_calls_exit0','test_leaf_PASS','test_leaf_FAIL','test_leaf_SKIP','CLI_exit_codes','cases_NOT_RUN','SDK_MODEL_Node_external_paid_private_calls','underlying_product_failure_count_this_cohort','source_acceptance','formal_increment','desktop15_execution_authorized','whole43_test_suite_qualified','Main_integration_authorized','evidence_refs','run_uuid','current_canonical_tuple','case_facts'])
fields('review',review,['schema','source_commit','reviewer','decision','requested_changes','non_author','actual_readonly_evidence_audit','qualification_ref','current43_fresh_held2_qualified','case_ids','source_acceptance','formal_increment','desktop15_execution_authorized'])
ck('qualification/review wire and identity',q['schema']=='researchos.cli43-bounded-execution-qualification.v1' and review['schema']=='researchos.cli43-bounded-execution-independent-review.v1' and q['source_commit']==review['source_commit']==SOURCE and q['reviewer']==review['reviewer']=='codex:/root/w05_merge_review' and review['decision']=='CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED' and review['requested_changes']==[] and review['non_author']is True and review['actual_readonly_evidence_audit']is True)
ck('qualification sealed member and exact review ref',same(review['qualification_ref'],scope['current58_CLI2_qualification_ref']) and str(path(scope['current58_CLI2_qualification_ref']['path']))in qmembers and same(qmembers[str(path(scope['current58_CLI2_qualification_ref']['path']))],scope['current58_CLI2_qualification_ref']))
ck('qualified counts ordered exact',q['current43_fresh_held2_qualified']is True and review['current43_fresh_held2_qualified']is True and q['qualified_case_count']==2 and q['qualified_case_ids']==review['case_ids']==CASES and q['native_calls']==q['native_calls_exit0']==14 and q['test_leaf_PASS']==2 and q['test_leaf_FAIL']==q['test_leaf_SKIP']==0 and q['CLI_exit_codes']==[0,3] and q['cases_NOT_RUN']==[] and q['SDK_MODEL_Node_external_paid_private_calls']==q['underlying_product_failure_count_this_cohort']==0)
ck('no expanded acceptance',all(d['source_acceptance']is False and d['formal_increment']==0 and d['desktop15_execution_authorized']is False for d in [q,review]) and q['whole43_test_suite_qualified']is False and q['Main_integration_authorized']is False)
e_keys=['scope_ref','grant_ref','result_ref','executor_manifest_ref','launcher_completed_ref','launcher_manifest_ref','root_completion_ref','root_closed_manifest_ref','audit_ref','supplement_ref','final_corrections_ref']
fields('evidence_refs',e,e_keys);fields('review evidence refs',review,e_keys)
for k in e_keys:verify(e[k]);ck('Q/review exact evidence '+k,same(e[k],review[k]))
fields('CLI scope',cs,['source_commit','ordered_cases','run_uuid','catalog_ref','new_output_root','new_wrapper_root']);fields('CLI grant',grant,['scope_ref','actual_registration_completed','binding','status','canonical_copies']);fields('CLI grant.binding',grant['binding'],['source_commit','run_uuid'])
ck('scope/catalog/grant exact',cs['source_commit']==SOURCE and cs['ordered_cases']==CASES and cs['run_uuid']==q['run_uuid']==grant['binding']['run_uuid'] and same(cs['catalog_ref'],scope['source_catalog_ref']) and same(grant['scope_ref'],e['scope_ref']) and grant['actual_registration_completed']is True and grant['binding']['source_commit']==SOURCE and grant['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED')
ck('qualification tuple not future',type(q['current_canonical_tuple'])is list and len(q['current_canonical_tuple'])==3 and all(type(x)is int for x in q['current_canonical_tuple']) and all(a<=b for a,b in zip(q['current_canonical_tuple'],scope['expected_registration'])))
fields('result',result,['status','first_cause','secondary','NOT_RUN','native_calls','stages','case_roster','cases']);fields('launcher completed',completed,['program_reported_exit','actual_inner_native_exit','first_cause','secondary'])
ck('result and launcher closed',completed['program_reported_exit']==completed['actual_inner_native_exit']==0 and completed['first_cause']is None and completed['secondary']==[] and result['status']=='BOUNDED_DEVELOPMENT_EVIDENCE_REPORTED' and result['first_cause']is None and result['secondary']==result['NOT_RUN']==[] and result['native_calls']==len(result['stages'])==14 and len(result['case_roster'])==len(result['cases'])==2)
labels=['git-head','git-public-blobs','go-version','go-env','go-list','go-list-test2json','build-test2json','build-cli','build-test','buildinfo-cli','buildinfo-test','buildinfo-test2json','case-00','case-01'];ck('stage exact roster',[s['label']for s in result['stages']]==labels)
stagefacts=[]
for st in result['stages']:
 fields('stage '+st['label'],st,['label','result_ref']);ck('stage is E member '+st['label'],same(ex[str(path(st['result_ref']['path']))],st['result_ref']));inv=read(st['result_ref']);rr=inv['result'];j=rr['job_cleanup']
 ck('native closed0 '+st['label'],inv['actual_exit']==rr['actual_exit']==0 and rr['error']is None and rr['timed_out']is False and rr['resumed']is True and j['job_idle_confirmed']is True and j['primary_exit_confirmed']is True and j['handles_closed']is True and j['errors']==[])
 stagefacts.append({'label':st['label'],'invocation_ref':st['result_ref'],'actual_exit':rr['actual_exit'],'creation_time_100ns':rr['creation_time_100ns'],'owned_child_pid':rr['owned_child_pid'],'job_cleanup':j,'debug_capture_present':'debug_capture'in rr})
facts=[];expected_absences=[]
ck('fact order',[x['case_id']for x in q['case_facts']]==CASES)
for i,leaf in enumerate(CASES):
 f=q['case_facts'][i];state=result['case_roster'][i];c=result['cases'][i];label=labels[12+i]
 fields('casefact '+leaf,f,['case_id','state','native_test_exit','CLI_exit','generations','invocation_ref','verified_ref'])
 expected_absences.append({'case':leaf,'missing_consumer_only_keys':[k for k in ['stdout_ref','stderr_ref']if k not in f]})
 fields('case state '+leaf,state,['state','leaf','launch_attempted','resumed','actual_native_exit','test_leaf_started','fixture_observation','qualified','failure']);fields('case result '+leaf,c,['leaf','status','proof_ref'])
 ck('fact/state/result values '+leaf,f['state']==state['state']=='QUALIFIED' and f['native_test_exit']==0 and f['CLI_exit']==[0,3][i] and state['leaf']==c['leaf']==leaf and state['launch_attempted']is True and state['resumed']is True and state['actual_native_exit']==0 and state['test_leaf_started']is True and state['fixture_observation']=='OBSERVED' and state['qualified']is True and state['failure']is None and c['status']=='PASS')
 for k in ['invocation_ref','verified_ref']:ck('existing fact sealed '+leaf+k,same(ex[str(path(f[k]['path']))],f[k]));verify(f[k])
 inv=read(f['invocation_ref']);v=read(f['verified_ref']);ck('stage/fact invocation same '+leaf,same(result['stages'][12+i]['result_ref'],f['invocation_ref']));ck('verified/result same '+leaf,v==c)
 base=path(e['executor_manifest_ref']['path']).parent;rawrefs={}
 for suffix in ['stdout.raw','stderr.raw']:
  key=str(base/(label+'.'+suffix));ck('producer-derived raw unique membership '+key,key in ex);r=ex[key];verify(r);rawrefs[suffix]=r
 events=[json.loads(line)for line in path(rawrefs['stdout.raw']['path']).read_bytes().splitlines()if line.strip()];expected={'TestCLIProtocolInteractiveAuthority','TestCLIProtocolInteractiveAuthority/'+leaf}
 ck('native raw exact RUN/PASS '+leaf,{x.get('Test')for x in events if x['Action']=='run'}==expected and {x.get('Test')for x in events if x['Action']=='pass'and x.get('Test')}==expected and not any(x['Action']in ['fail','skip']for x in events));ck('stderr actually empty '+leaf,rawrefs['stderr.raw']['bytes']==0)
 gens=inv['result']['debug_capture']['process_generations'];ck('native vs expected CLI3 '+leaf,[g['independent_exit']for g in gens]==([0,0,0]if i==0 else[0,0,3]) and len(gens)==3 and all(type(g['pid'])is int and type(g['creation_time_100ns'])is int for g in gens))
 ck('Q generation projection exact '+leaf,f['generations']==[{k:g[k]for k in ['pid','creation_time_100ns','independent_exit','image']}for g in gens]);ck('debug strict unchanged '+leaf,inv['result']['debug_capture']['complete']is True and inv['result']['debug_capture']['rejected_load_facts']==[])
 verify(c['proof_ref']);ck('proof external export not E '+leaf,path(c['proof_ref']['path']).is_relative_to(path(cs['new_export_root'])) and not path(c['proof_ref']['path']).is_relative_to(base))
 facts.append({'case_id':leaf,'label':label,'actual_fact_keys':list(f),'actual_invocation_keys':list(inv),'raw_refs_from_sealed_E':rawrefs,'verified_ref':f['verified_ref'],'proof_ref':c['proof_ref'],'native_test_exit':0,'expected_CLI_exit':[0,3][i],'observed_generation_exits':[g['independent_exit']for g in gens]})
# Dedicated aggregate schema and all remaining object dereferences, using independent data checks only.
fields('root completion',root,['schema','actor','run_uuid','source_commit','closure_kind','source_acceptance','formal_increment','fresh_compile_qualification','complete_current58_source_validation','case_qualification','caller_OS_lifecycle_qualification','completion_live_canonical_observed','independent_qualification','executor_manifest_all_members_verified','launcher_manifest_all_members_verified','closure_request_ref','source_scope_ref','grant_ref','executor_manifest_ref','launcher_manifest_ref','caller_ref','caller_invocation_ref','tool_observation_ref','terminal_action_input_ref','terminal_tool_result_ref'])
ck('root record semantics',root['schema']=='researchos.root-actual-launch-completion.v2'and root['actor']=='codex:/root'and root['run_uuid']==q['run_uuid']and root['source_commit']==SOURCE and root['closure_kind']=='TERMINAL_EVIDENCE_RECORDED_NOT_QUALIFICATION'and root['source_acceptance']is False and root['formal_increment']==0 and all(root[k]is False for k in ['fresh_compile_qualification','complete_current58_source_validation','case_qualification','caller_OS_lifecycle_qualification','completion_live_canonical_observed'])and root['independent_qualification']=='PENDING'and root['executor_manifest_all_members_verified']is True and root['launcher_manifest_all_members_verified']is True)
direct=['scope_ref','grant_ref','caller_ref','caller_intent_ref','caller_invocation_ref','tool_observation_ref','terminal_action_input_ref','terminal_tool_result_ref','executor_manifest_ref','launcher_manifest_ref']
fields('root request',req,['schema','run_uuid','source_commit','new_closure_output_root','caller_output_root','additional_sealed_refs']+direct)
ck('root request identity',req['schema']=='researchos.current58-root-terminal-closure-request.v1'and req['run_uuid']==q['run_uuid']and req['source_commit']==SOURCE and path(req['new_closure_output_root'])==path(e['root_closed_manifest_ref']['path']).parent)
for k in ['scope_ref','grant_ref','executor_manifest_ref','launcher_manifest_ref']:ck('request/evidence '+k,same(req[k],e[k]))
for k in ['caller_ref','caller_invocation_ref','tool_observation_ref','terminal_action_input_ref','terminal_tool_result_ref']:ck('request/completion '+k,same(req[k],root[k]))
for k in ['grant_ref','executor_manifest_ref','launcher_manifest_ref']:ck('completion/evidence '+k,same(root[k],e[k]))
ck('completion source scope',same(root['source_scope_ref'],e['scope_ref']))
fields('caller',caller,['scope_ref','grant_ref','caller_OS_lifecycle_qualification','automatic_retry','counter_reset','stdout_ref','stderr_ref','actual_launcher_native_exit','actual_outer_tool_exit','caller_error','secondary']);fields('intent',intent,['scope_ref','grant_ref','caller_OS_lifecycle_qualification','automatic_retry','counter_reset'])
ck('caller/intent original exact serialized dicts',caller['scope_ref']==intent['scope_ref']==req['scope_ref']and caller['grant_ref']==intent['grant_ref']==req['grant_ref'])
ck('roots exact',path(req['caller_invocation_ref']['path']).parent==path(req['caller_intent_ref']['path']).parent==path(req['caller_output_root'])and path(e['executor_manifest_ref']['path']).parent==path(cs['new_output_root'])and path(e['launcher_manifest_ref']['path']).parent==path(cs['new_wrapper_root']))
ck('outer NULL vs actual bridge0 preserved',caller['actual_outer_tool_exit']is None and caller['actual_launcher_native_exit']==0 and caller['caller_error']is None and caller['secondary']==[] and root['actual_outer_tool_exit']==root['actual_python_caller_exit']==root['actual_launcher_native_exit']==root['actual_inner_python_native_exit']==0 and root['separately_captured_outer_native_raw']is False)
ck('caller not OS qualified/no retry',all(d['caller_OS_lifecycle_qualification']is False and d['automatic_retry']is False and d['counter_reset']is False for d in [caller,intent]))
ck('aggregate exact header',set(rm)=={'schema','actor','members','original_registration_manifests_unchanged','source_acceptance','formal_increment'}and rm['schema']=='researchos.root-launch-closure-manifest.v2'and rm['actor']=='codex:/root'and rm['original_registration_manifests_unchanged']is True and rm['source_acceptance']is False and rm['formal_increment']==0)
expected={}
def add(r):
 p=verify(r);old=expected.get(str(p));ck('aggregate repeated pin consistent '+str(p),old is None or same(old,r));expected[str(p)]=r
add(root['closure_request_ref']);add(e['root_completion_ref'])
gate_raw=GATE.read_bytes();pin(GATE);tree=ast.parse(gate_raw);producer=None
for n in tree.body:
 if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='CLI_ROOT_CLOSURE_PRODUCER'for t in n.targets):producer=ast.literal_eval(n.value)
add(producer)
for k in direct:add(req[k])
ck('added exact19',len(req['additional_sealed_refs'])==19)
for r in req['additional_sealed_refs']:add(r)
for r in list(ex.values())+list(la.values()):add(r)
ck('grant4',len(grant['canonical_copies'])==4)
for row in grant['canonical_copies']:add(row['ref'])
for k in ['stdout_ref','stderr_ref']:
 if caller[k]is not None:add(caller[k])
ck('READS union exact169',len(expected)==169 and set(expected)==set(rt)and all(same(expected[k],rt[k])for k in rt))
ck('aggregate sorted refs',list(rt)==sorted(rt))
for r in [cs['runner_ref'],cs['launcher_ref']]:verify(r)
for p in [QDIR/'seal.py',QDIR/'supplement.py',QDIR/'audit.py']:pin(p)
ck('actual blocker only expected missing pair',all(a['missing_consumer_only_keys']==['stdout_ref','stderr_ref']for a in expected_absences))
ast_rows=json.loads((O/'inspection.json').read_bytes())['gate_dereferences']
out={'schema':'researchos.cli2-producer-consumer-abi-diagnostic.v1','candidate_executed':False,'candidate_imported':False,'checks':C,'failed_checks':[x for x in C if not x['passed']],'actual_gate_missing_fields':expected_absences,'object_field_matrix':MATRIX,'all_gate_data_subscripts':ast_rows,'stage_facts':stagefacts,'case_binding_matrix':facts,'root_request_ref':root['closure_request_ref'],'root_producer_ref':producer,'root_tool_shape':{'observation_keys':list(tools),'terminal_keys':list(terminal),'action_keys':list(action)},'input_refs':list(READS.values()),'failure_original_payload':failure,'new_failure_origins':[],'scope':'Current sealed CLI2 producer/fact ABI only; no candidate calls, no 24k resource-tree rehash, no refreshed source/formal acceptance.'}
save('abi-audit.json',out)
print(json.dumps({'checks':len(C),'failed':out['failed_checks'],'missing_fields':expected_absences,'refs':len(READS),'case_raw_refs':[x['raw_refs_from_sealed_E']for x in facts],'audit_ref':pin(O/'abi-audit.json')},ensure_ascii=False))
