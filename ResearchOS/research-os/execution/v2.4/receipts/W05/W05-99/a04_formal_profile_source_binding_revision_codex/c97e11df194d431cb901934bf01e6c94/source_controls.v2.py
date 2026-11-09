from pathlib import Path
import ast, copy, hashlib, json, re

OUT=Path(__file__).parent
text=(OUT/'formal_profile_w05.binding.v3.proposed.py').read_text(encoding='utf-8')
tree=ast.parse(text)
names={'_integer','_native_exit','_nonempty','_json_original','_original','_root_pair',
       '_public_value','_schema_value','_database_row','_event_schema','_jsonl','verify_refusal'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert {n.name for n in nodes}==names
constants=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PUBLIC_SCHEMAS' for t in n.targets)]
assert len(constants)==1
env={'re':re,'json':json}
exec(compile(ast.Module(body=constants+nodes,type_ignores=[]),'<selected-pure-AST-only>','exec'),env)
# SQL _database and full candidate module are deliberately absent.
assert '_database' not in env
projection=json.loads((OUT/'public-schema-projection.actual.json').read_bytes())['projection']
assert env['PUBLIC_SCHEMAS']==projection
results=[]
def run(label,expected,fn):
    try:
        value=fn();outcome='ACCEPTED';error=None
    except ValueError as exc:
        value=None;outcome='REFUSED';error=str(exc)
    results.append({'id':label,'expected':expected,'actual':outcome,'matched':outcome==expected,'error':error})
def rejected(label,fn):run(label,'REFUSED',fn)
def accepted(label,fn):run(label,'ACCEPTED',fn)
identity={'project_id':'project','session_id':'session','goal_id':'goal','task_id':'task','run_id':'run','core_build_id':'build'}
stamp='2026-10-08T00:00:00Z';digest='sha256:'+'a'*64
task={'id':'task','project_id':'project','revision':1,'created_at':stamp,'updated_at':stamp,'goal_id':'goal','title':'test','task_type':'IMPLEMENTATION','stage':'delivery','status':'EXECUTION_REPORTED','dependency_task_ids':[],'requirement_refs':[],'input_refs':[],'context_bundle_id':None,
'acceptance_contract':{'contract_hash':digest,'contract_revision':1,'checks':[{'check_id':'check','kind':'DETERMINISTIC','required':True,'expected':'raw','command_key':'test.runtime','rubric_ref':None,'qualification_id':None,'not_applicable_reason':None}],'require_independent_verifier':True,'version_policy':'EXACT','frozen_at':stamp},
'assigned_principal_id':None,'active_run_id':'run','output_artifact_ids':['artifact'],'acceptance_id':None,'blocking_conflict_ids':[],'no_progress_record_id':'progress','stop_policy':{'wall_time_seconds':300,'max_attempts':1,'max_parallel_runs':1,'stop_conditions':['cancel']},'binding':{'route':'MU_FORK','upstream_project_id':None,'upstream_goal_id':None,'upstream_task_id':None}}
run_object={'id':'run','project_id':'project','revision':1,'created_at':stamp,'updated_at':stamp,'task_id':'task','runtime_id':'runtime','executor_principal_id':'executor','attempt':1,'status':'SETTLED','input_refs':[],'context_bundle_id':'context','external_run_id':None,'workspace_snapshot_id':'snapshot','lease_token_hash':digest,'lease_expires_at':stamp,'heartbeat_at':None,'checkpoint_artifact_id':None,'result_artifact_ids':['artifact'],'execution_report':'actual report','exit_code':0,'runtime_settled_at':stamp,'cancel_requested_at':None,'cancel_confirmed_at':None,'children_stopped':True,'queue_empty':True,'started_at':stamp,'ended_at':stamp,'lease_epoch':1}
defs=projection['domain']
artifact={'id':'artifact','project_id':'project','revision':1,'created_at':stamp,'updated_at':stamp,'run_id':'run','kind':'REPORT','evidence_kind':defs['EvidenceKind']['enum'][0],'validity':defs['Validity']['enum'][0],'measurement_mode':defs['MeasurementMode']['enum'][0],'content_hash':digest,'storage_key':'sha256/'+('a'*64),'media_type':'application/json','byte_size':1,'input_refs':[],'source_refs':[],'produced_by':'executor','sealed_at':stamp,'access_class':'PROJECT'}
def row(kind,value,hash_value=None,rev=1):
    return env['_database_row'](kind,rev,hash_value,json.dumps(value),identity,value['id'])
accepted('DB_TASK_NULL_HASH_PUBLIC_FULL_BODY',lambda:row('Task',task))
accepted('DB_RUN_NULL_HASH_PUBLIC_FULL_BODY',lambda:row('Run',run_object))
accepted('DB_ARTIFACT_PUBLIC_FULL_BODY_STRICT_HASH',lambda:row('Artifact',artifact,digest))
for kind,value in [('Task',task),('Run',run_object)]:
    for label,bad in [('BOOL_REVISION',True),('FLOAT_REVISION',1.0),('ZERO_REVISION',0)]:
        rejected('DB_'+kind+'_'+label,lambda k=kind,v=value,b=bad:row(k,v,None,b))
    rejected('DB_'+kind+'_INVENTED_HASH',lambda k=kind,v=value:row(k,v,digest))
    for key,replacement in [('project_id','foreign'),('revision',True)]:
        bad=copy.deepcopy(value);bad[key]=replacement
        rejected('DB_'+kind+'_BODY_'+key,lambda k=kind,v=bad:row(k,v))
    bad=copy.deepcopy(value);bad.pop('created_at')
    rejected('DB_'+kind+'_MISSING_PUBLIC_FIELD',lambda k=kind,v=bad:row(k,v))
for label,bad in [('NULL',None),('BARE','a'*64),('WRONG','sha256:'+'b'*64),('BOOL',True)]:
    rejected('DB_ARTIFACT_'+label+'_HASH',lambda b=bad:row('Artifact',artifact,b))
bad=copy.deepcopy(artifact);bad['run_id']='foreign'
rejected('DB_ARTIFACT_FOREIGN_RUN',lambda:row('Artifact',bad,digest))
bad=copy.deepcopy(task);bad['goal_id']='foreign'
rejected('DB_TASK_FOREIGN_GOAL',lambda:row('Task',bad))
bad_run=copy.deepcopy(run_object);bad_run['task_id']='foreign'
rejected('DB_RUN_FOREIGN_TASK',lambda:row('Run',bad_run))
bad=copy.deepcopy(task);bad['updated_at']='2026-02-30T00:00:00Z'
rejected('DB_INVALID_CALENDAR_DATE',lambda:row('Task',bad))

event={'event_id':'event-1','session_id':'session','sequence':1,'core_build_id':'build','protocol_version':'researchos-client/2','run_id':'run','command_id':None,'domain_event_id':None,'kind':'RUN_STATE',
'payload':{'run_id':'run','status':'SETTLED','revision':1,'cancel_requested_at':None,'cancel_confirmed_at':None,'settled_at':stamp,'children_stopped':True,'queue_empty':True}}
final={'execution':{**{k:v for k,v in identity.items() if k!='core_build_id'},'event_sequence':1,'independent_acceptance':'NOT_EVALUATED','exit_code':0}}
def stream(events,tail=None):
    frames=[{'type':'session.event','event':item} for item in events]+[final if tail is None else tail]
    return env['_jsonl'](('\n'.join(json.dumps(x) for x in frames)+'\n').encode(),identity)
accepted('SESSION_EVENT_TEN_FIELDS_TYPED_RUN_PAYLOAD',lambda:stream([event]))
for key in event:
    bad=copy.deepcopy(event);bad.pop(key)
    rejected('SESSION_EVENT_MISSING_'+key,lambda e=bad:stream([e]))
for key,bad_value in [('kind','INVENTED'),('sequence',True),('sequence',1.0),('sequence',0),('event_id',''),('command_id',False),('domain_event_id',''),('protocol_version','old'),('payload',[]),('run_id','foreign')]:
    bad=copy.deepcopy(event);bad[key]=bad_value
    rejected('SESSION_EVENT_BAD_'+key+'_'+str(bad_value),lambda e=bad:stream([e]))
for key,bad_value in [('revision',True),('run_id','foreign'),('status','INVENTED')]:
    bad=copy.deepcopy(event);bad['payload'][key]=bad_value
    rejected('RUN_PAYLOAD_BAD_'+key,lambda e=bad:stream([e]))
bad=copy.deepcopy(event);bad['extra']=1
rejected('SESSION_EVENT_EXTRA',lambda:stream([bad]))
bad=copy.deepcopy(event);bad['payload']['secret']='not-a-secret-test-value'
rejected('SESSION_EVENT_SENSITIVE_KEY',lambda:stream([bad]))
second=copy.deepcopy(event);second['sequence']=2
tail=copy.deepcopy(final);tail['execution']['event_sequence']=2
rejected('SESSION_EVENT_DUPLICATE_ID',lambda:stream([event,second],tail))
tail=copy.deepcopy(final);tail['execution']['event_sequence']=True
rejected('FINAL_CURSOR_BOOL',lambda:stream([event],tail))
message=copy.deepcopy(event);message['kind']='MESSAGE';message['payload']={'message_id':'message','role':'ASSISTANT','phase':'DELTA','part_index':0,'content_offset_utf8_bytes':0,'text':'中文'}
accepted('MESSAGE_TYPED_DELTA',lambda:stream([message]))
message_bad=copy.deepcopy(message);message_bad['payload']['text']=''
rejected('MESSAGE_EMPTY_DELTA',lambda:stream([message_bad]))
message_bad=copy.deepcopy(message);message_bad['payload']['phase']='START'
rejected('MESSAGE_START_NONEMPTY',lambda:stream([message_bad]))
artifact_event=copy.deepcopy(event);artifact_event['kind']='ARTIFACT';artifact_event['payload']={'artifact_ref':{'entity_type':'Artifact','id':'artifact','revision':1,'content_hash':digest},'availability':'AVAILABLE'}
accepted('ARTIFACT_TYPED_AVAILABLE',lambda:stream([artifact_event]))
artifact_event_bad=copy.deepcopy(artifact_event);artifact_event_bad['payload']['artifact_ref']['content_hash']=None
rejected('ARTIFACT_EVENT_NULL_HASH',lambda:stream([artifact_event_bad]))

objects={}
def put(name,obj):
    payload=json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()
    ref={'path':'execution/v2.4/receipts/W05/W05-99/source-data/'+name,'sha256':hashlib.sha256(payload).hexdigest()}
    objects[ref['path']]=(obj,payload)
    return ref
def doc(ref):
    value,payload=objects[ref['path']]
    if hashlib.sha256(payload).hexdigest()!=ref['sha256']:raise ValueError('raw-hash')
    return copy.deepcopy(value)
def raw(ref):doc(ref);return objects[ref['path']][1]
grant_ref=put('grant.json',{'actor_id':'codex:/root','run_id':'evidence-run'})
expected={'run_id':'evidence-run','task_id':'task','lane':'success','assertion_id':'A04-01','negative_condition':'frozen rejection','product_identity':identity}
scope={**expected,'schema':'researchos.w05.a04-negative-scope.v3','root_grant_ref':grant_ref,'argv':['researchos','status'],'cwd':'D:/Source-worktree','env_names':['PATH'],'initial_tool_input':{'cmd':'Root-fixed-original-command','workdir':'D:/Source-worktree'},'producer_ref':{'path':'producer.py','sha256':'b'*64}}
scope_ref=put('scope.json',scope)
response={**expected,'schema':'researchos.w05.original-negative-response.v3','scope_ref':scope_ref,'status':'REJECTED'}
response_ref=put('response.json',response)
closed={'actual_launcher_native_exit':3,'negative_identity':expected,'negative_scope_ref':scope_ref,'actual_refusal_response':response}
initial={'tool':'exec_command','input':scope['initial_tool_input'],'result':{'exit_code':3,'output':json.dumps(closed)}}
pair_ref=put('pair.json',{'schema':'researchos.w05.original-tool-pair.v2','initial':initial,'terminal':initial})
inv={**expected,'schema':'researchos.w05.negative-invocation.v3','root_grant_ref':grant_ref,'scope_ref':scope_ref,'scope':scope,**{k:scope[k] for k in ('argv','cwd','env_names','initial_tool_input','producer_ref')},'native_exit':3,'root_tool_pair_ref':pair_ref}
inv_ref=put('negative.json',inv)
refusal={**{k:expected[k] for k in ('run_id','task_id','lane','assertion_id','negative_condition')},'schema':'researchos.w05.actual-refusal.v2','rejected':True,'invocation_ref':inv_ref,'original_response_ref':response_ref}
refusal_ref=put('refusal.json',refusal)
issuance={'schema':'researchos.w05.original-root-grant-issuance.v2','actor_id':'codex:/root','run_id':'evidence-run','grant_ref':grant_ref,'negative_scope_refs':[scope_ref],'original_result':{'exit_code':0,'output':json.dumps({'grant_ref':grant_ref,'negative_scope_refs':[scope_ref]})}}
issuance_ref=put('issuance.json',issuance)
ctx={'run_id':'evidence-run','root_grant_ref':grant_ref,'root_grant_issuance_ref':issuance_ref,'worktree':'D:/Source-worktree'}
assertion={'id':'A04-01','lane':'success','expected':'frozen rejection','product_identity':identity,'negative_invocation_ref':inv_ref,'refusal_evidence_refs':[refusal_ref]}
def verify(c=ctx,a=assertion):return env['verify_refusal'](doc,raw,c,a)
accepted('NEGATIVE_ACTUAL_IDENTITY_SCOPE_RESPONSE_CHAIN',verify)
# Rehash changed objects and their referring wrappers: no test relies on hash mismatch.
for object_kind in ('invocation','response','scope'):
    for key,value in [('run_id','foreign'),('task_id','foreign'),('lane','H08'),('negative_condition','other-condition'),('product_identity',{**identity,'goal_id':'foreign'})]:
        new_inv=copy.deepcopy(inv);new_response=copy.deepcopy(response);new_scope=copy.deepcopy(scope);new_refusal=copy.deepcopy(refusal);new_issuance=copy.deepcopy(issuance);a=copy.deepcopy(assertion);c=copy.deepcopy(ctx)
        if object_kind=='invocation':new_inv[key]=value
        elif object_kind=='response':new_response[key]=value
        else:
            new_scope[key]=value
            sr=put('bad-scope-'+key+'.json',new_scope)
            new_inv['scope']=new_scope;new_inv['scope_ref']=sr
            new_issuance['negative_scope_refs']=[sr]
            new_issuance['original_result']['output']=json.dumps({'grant_ref':grant_ref,'negative_scope_refs':[sr]})
            c['root_grant_issuance_ref']=put('bad-issuance-'+key+'.json',new_issuance)
        new_refusal['original_response_ref']=put('bad-response-'+object_kind+key+'.json',new_response)
        new_refusal['invocation_ref']=put('bad-inv-'+object_kind+key+'.json',new_inv)
        a['negative_invocation_ref']=new_refusal['invocation_ref'];a['refusal_evidence_refs']=[put('bad-refusal-'+object_kind+key+'.json',new_refusal)]
        rejected('NEGATIVE_'+object_kind+'_'+key,lambda c=c,a=a:verify(c,a))
bad_response=copy.deepcopy(response);bad_response['status']='BLOCKED'
bad_response_ref=put('relabeled-response.json',bad_response)
bad_refusal=copy.deepcopy(refusal);bad_refusal['original_response_ref']=bad_response_ref
a=copy.deepcopy(assertion);a['refusal_evidence_refs']=[put('relabeled-refusal.json',bad_refusal)]
rejected('NEGATIVE_RESPONSE_NOT_ACTUAL_TERMINAL',lambda:verify(ctx,a))
for label,refs in [('EMPTY',[]),('DUPLICATE',[scope_ref,scope_ref]),('FOREIGN',[put('foreign-scope.json',scope)])]:
    b=copy.deepcopy(issuance);b['negative_scope_refs']=refs;b['original_result']['output']=json.dumps({'grant_ref':grant_ref,'negative_scope_refs':refs})
    c=copy.deepcopy(ctx);c['root_grant_issuance_ref']=put(label+'-issuance.json',b)
    rejected('NEGATIVE_ROOT_SCOPE_'+label,lambda c=c:verify(c))
b=copy.deepcopy(issuance);b['negative_scope_refs']=[put('relabel-scope.json',scope)]
c=copy.deepcopy(ctx);c['root_grant_issuance_ref']=put('unobserved-issuance.json',b)
rejected('NEGATIVE_ROOT_LIST_NOT_ORIGINAL_STDOUT',lambda:verify(c))
for key in ['verify_capture_bundle','verify_live_originals','_witness','_invocations','verify_owner']:
    old=(OUT.parent.parent/'a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94/formal_profile_w05.final.proposed.py').read_text(encoding='utf-8')
    old_nodes={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
    new_nodes={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert ast.get_source_segment(old,old_nodes[key])==ast.get_source_segment(text,new_nodes[key])
# No assertions of LIVE success: all current public dispatch selectors keep OPEN.
fixtures={'identity':identity,'Task':task,'Run':run_object,'Artifact':artifact,'SessionEvent':event,'final':final,'negative_expected':expected,'objects':{path:obj for path,(obj,b) in objects.items()},'synthetic_only':True,'actual_live_evidence':False}
with (OUT/'source-data-controls.fixtures.v2.json').open('xb') as f:f.write(json.dumps(fixtures,ensure_ascii=False,indent=2).encode()+b'\n')
report={'schema':'researchos.a04-binding-source-controls.v1','qualification':'NONE_SYNTHETIC_PUBLIC_SCHEMA_SOURCE_DATA_ONLY','selected_function_count':len(nodes),'results':results,'control_count':len(results),'matched_count':sum(x['matched'] for x in results),'candidate_entrypoints':0,'SQL_calls':0,'Go_CLI_SDK_model_native_calls':0,'unchanged_always_open_dispatch':True}
with (OUT/'source-controls.actual.v2.json').open('xb') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2).encode()+b'\n')
print(json.dumps({'controls':len(results),'matched':report['matched_count'],'unmatched':[x for x in results if not x['matched']],'candidate_SQL_product_calls':0}))

