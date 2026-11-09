"""Independent pure-data controls; no candidate module import, database, SQL or product execution."""
import ast,copy,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94")
h=json.loads((B/'handoff.json').read_bytes());source=Path(h['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8');tree=ast.parse(source)
wanted={'_integer','_native_exit','_nonempty','_json_original','_original','_root_pair','_public_value','_schema_value','_database_row','_event_schema','_jsonl','verify_refusal'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
assert {n.name for n in nodes}==wanted
schemas=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PUBLIC_SCHEMAS' for x in n.targets))
for node in ast.walk(ast.Module(body=nodes,type_ignores=[])):
 if isinstance(node,(ast.Import,ast.ImportFrom)):
  assert isinstance(node,ast.Import) and [x.name for x in node.names]==['datetime']
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in {'open','eval','exec','compile','__import__','input'}
ns={'json':json,'re':re,'PUBLIC_SCHEMAS':schemas}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<independent-pure-AST>','exec'),ns)
N='2026-10-08T00:00:00Z';DIGEST='sha256:'+'a'*64
# Reviewer-created generic required-field constructor from public data; no author control fixtures.
def minimal(s,g):
 if '$ref' in s:
  ng,name=s['$ref'].split(':');return minimal(schemas[ng][name],ng)
 if 'const' in s:return copy.deepcopy(s['const'])
 if 'enum' in s:return copy.deepcopy(s['enum'][0])
 if 'anyOf' in s:
  alt=next((v for v in s['anyOf'] if v.get('type')=='null'),s['anyOf'][0]);return minimal(alt,g)
 kind=s.get('type')
 if kind=='object':return {k:minimal(s['properties'][k],g) for k in s.get('required',[])}
 if kind=='array':return [minimal(s['items'],g) for _ in range(s.get('minItems',0))]
 if kind=='integer':return max(1,s.get('minimum',0))
 if kind=='boolean':return False
 if kind=='null':return None
 if kind=='string':
  if s.get('format')=='date-time':return N
  if 'sha256:' in s.get('pattern',''):return DIGEST
  if s.get('pattern','').startswith('^(0|'):return '0'
  return 'value'
 return {}
identity={'project_id':'project-independent','session_id':'session-independent','goal_id':'goal-independent','task_id':'task-independent','run_id':'run-independent','core_build_id':'build-independent'}
task=minimal(schemas['persistence']['Task'],'persistence');task.update(id=identity['task_id'],project_id=identity['project_id'],goal_id=identity['goal_id'],revision=4,status='EXECUTION_REPORTED',stage='delivery',active_run_id=identity['run_id'],context_bundle_id='context-independent')
run=minimal(schemas['domain']['Run'],'domain');run.update(id=identity['run_id'],project_id=identity['project_id'],task_id=identity['task_id'],revision=7,status='SETTLED',context_bundle_id='context-independent',result_artifact_ids=['artifact-independent'],children_stopped=True,queue_empty=True,runtime_settled_at=N,execution_report='Independent synthetic report',exit_code=0)
artifact=minimal(schemas['domain']['Artifact'],'domain');artifact.update(id='artifact-independent',project_id=identity['project_id'],run_id=identity['run_id'],revision=1,content_hash=DIGEST)
def encode(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
results=[]
def check(name,expected,fn,inputs):
 try:
  fn();actual='ACCEPTED';error=None
 except Exception as e:
  actual='REFUSED';error=type(e).__name__+':'+str(e)
 results.append({'id':name,'expected':expected,'actual':actual,'matched':actual==expected,'error':error,'inputs':inputs})
def row_test(name,kind,obj,digest=None,revision=None,expected='REFUSED'):
 rev=obj['revision'] if revision is None else revision
 check(name,expected,lambda:ns['_database_row'](kind,rev,digest,encode(obj),identity,obj['id']),{'kind':kind,'sql_revision':rev,'sql_content_hash':digest,'body':obj,'identity':identity})
row_test('TASK_FULL_NULL', 'Task',task,expected='ACCEPTED')
row_test('RUN_FULL_NULL','Run',run,expected='ACCEPTED')
row_test('ARTIFACT_FULL_PREFIXED','Artifact',artifact,DIGEST,expected='ACCEPTED')
for kind,obj in [('Task',task),('Run',run)]:
 for label,mut in [('foreign_project',{'project_id':'foreign-project'}),('sql_body_revision',{'revision':9}),('missing_field',{}),('additional_field',{'injected':True})]:
  v=copy.deepcopy(obj);v.update(mut)
  if label=='missing_field':v.pop('created_at')
  row_test(kind+'_'+label,kind,v,revision=obj['revision'])
 row_test(kind+'_invented_hash',kind,obj,'b'*64)
 row_test(kind+'_bool_sql_revision',kind,obj,revision=True)
v=copy.deepcopy(task);v['active_run_id']='foreign-current-run'
row_test('TASK_FOREIGN_ACTIVE_RUN_EXPECT_REJECT', 'Task',v)
v=copy.deepcopy(run);v['task_id']='foreign-task';row_test('RUN_FOREIGN_TASK','Run',v)
for label,hashval in [('null',None),('bare','a'*64),('wrong','sha256:'+'b'*64),('uppercase','sha256:'+'A'*64)]:
 row_test('ARTIFACT_HASH_'+label,'Artifact',artifact,hashval)
v=copy.deepcopy(artifact);v['run_id']='foreign-run';row_test('ARTIFACT_FOREIGN_RUN','Artifact',v,DIGEST)
v=copy.deepcopy(task);v['created_at']='2026-02-30T00:00:00Z';row_test('TASK_IMPOSSIBLE_DATE','Task',v)
def event(kind,payload,seq=1):
 return {'event_id':'event-'+str(seq),'session_id':identity['session_id'],'sequence':seq,'core_build_id':identity['core_build_id'],'protocol_version':'researchos-client/2','run_id':identity['run_id'],'command_id':None,'domain_event_id':None,'kind':kind,'payload':payload}
payload_defs={}
for branch in schemas['client']['SessionEvent']['allOf']:
 kind=branch['if']['properties']['kind']['const'];payload_defs[kind]=branch['then']['properties']['payload']['$ref'].split(':')[1]
valid_events={}
for kind,name in payload_defs.items():
 p=minimal(schemas['client'][name],'client')
 if kind=='MESSAGE':p.update(phase='DELTA',text='中文独立复核',content_offset_utf8_bytes=0,part_index=0)
 if kind=='RUN_STATE':p.update(run_id=identity['run_id'],status='SETTLED',revision=7,children_stopped=True,queue_empty=True,settled_at=N)
 if kind=='GOAL_STATE':p['goal_id']=identity['goal_id']
 e=event(kind,p);valid_events[kind]=e
 check('EVENT_VALID_'+kind,'ACCEPTED',lambda e=e:ns['_event_schema'](e),e)
ev=valid_events['RUN_STATE']
for key in ev:
 e=copy.deepcopy(ev);e.pop(key)
 check('EVENT_MISSING_'+key,'REFUSED',lambda e=e:ns['_event_schema'](e),e)
for name,change in [('unknown_kind',{'kind':'INVENTED'}),('null_payload',{'payload':None}),('array_payload',{'payload':[]}),('bool_sequence',{'sequence':True}),('zero_sequence',{'sequence':0}),('extra_field',{'surprise':1})]:
 e=copy.deepcopy(ev);e.update(change)
 check('EVENT_'+name,'REFUSED',lambda e=e:ns['_event_schema'](e),e)
for kind,field,bad in [('MESSAGE','text',''),('USAGE','money',{'amount':'0','currency':'USD'}),('RUN_STATE','revision',True),('TOOL_RESULT','outcome','MADE_UP')]:
 e=copy.deepcopy(valid_events[kind]);e['payload'][field]=bad
 check('PAYLOAD_'+kind+'_'+field,'REFUSED',lambda e=e:ns['_event_schema'](e),e)
# Stream-level checks use the real selected pure _jsonl and reviewers' complete typed event.
final={**identity,'event_sequence':1,'independent_acceptance':'NOT_EVALUATED','exit_code':0}
def stream(e,tail=None):return b'\n'.join([encode({'type':'session.event','event':e}),encode({'command':'run','execution':tail or final})])+b'\n'
check('STREAM_TYPED_RUN','ACCEPTED',lambda:ns['_jsonl'](stream(ev),identity),{'event':ev,'final':final})
for label,e in [('foreign_run',dict(ev,run_id='other')),('foreign_payload_run',dict(ev,payload=dict(ev['payload'],run_id='other')))]:
 check('STREAM_'+label,'REFUSED',lambda e=e:ns['_jsonl'](stream(e),identity),e)
dup=b'\n'.join([encode({'type':'session.event','event':ev}),encode({'type':'session.event','event':dict(ev,sequence=2)}),encode({'command':'run','execution':dict(final,event_sequence=2)})])
check('STREAM_DUPLICATE_EVENT_ID','REFUSED',lambda:ns['_jsonl'](dup,identity),{'raw':dup.decode()})
# Synthetic content-addressed, complete negative lineage with reviewer-generated data.
def refusal_case(mode):
 blobs={}
 def put(name,obj):
  b=encode(obj);ref={'path':name+'.json','sha256':hashlib.sha256(b).hexdigest()};blobs[ref['path']]=b;return ref
 def getraw(ref):
  b=blobs[ref['path']]
  if hashlib.sha256(b).hexdigest()!=ref['sha256']:raise ValueError('REVIEWER_RAW_REF_HASH')
  return b
 doc=lambda ref:json.loads(getraw(ref))
 rootgrant=put('grant',{'decision':'GRANTED','run_id':'evidence-independent'})
 producer=put('producer',{'synthetic_source_only':True})
 expected={'run_id':'evidence-independent','task_id':identity['task_id'],'lane':'executor_crash','assertion_id':'A04-03','negative_condition':'independent frozen negative condition','product_identity':identity}
 scope={**copy.deepcopy(expected),'schema':'researchos.w05.a04-negative-scope.v3','root_grant_ref':rootgrant,'argv':['synthetic-not-run'],'cwd':'D:/synthetic-review-worktree','env_names':[],'initial_tool_input':{'cmd':'synthetic-not-run','yield_time_ms':1000},'producer_ref':producer}
 if mode=='scope_foreign':scope['lane']='success'
 scoperef=put('scope',scope)
 response={**copy.deepcopy(expected),'schema':'researchos.w05.original-negative-response.v3','scope_ref':scoperef,'status':'REJECTED','details':{'exit_detail':1}}
 if mode=='response_foreign':response['run_id']='foreign-evidence'
 response_ref=put('response',response)
 closed={'actual_launcher_native_exit':-9,'negative_identity':copy.deepcopy(expected),'negative_scope_ref':scoperef,'actual_refusal_response':copy.deepcopy(response)}
 if mode=='terminal_foreign':closed['negative_identity']['product_identity']['run_id']='foreign-run'
 if mode=='response_bool_integer_alias':closed['actual_refusal_response']['details']['exit_detail']=True
 if mode=='response_float_integer_alias':closed['actual_refusal_response']['details']['exit_detail']=1.0
 if mode=='terminal_response_foreign':closed['actual_refusal_response']['negative_condition']='different'
 pair0={'tool':'exec_command','input':copy.deepcopy(scope['initial_tool_input']),'result':{'exit_code':-9,'output':encode(closed).decode()}}
 pair={'schema':'researchos.w05.original-tool-pair.v2','initial':pair0,'terminal':copy.deepcopy(pair0)}
 pairref=put('pair',pair)
 invocation={**copy.deepcopy(expected),'schema':'researchos.w05.negative-invocation.v3','scope_ref':scoperef,'scope':scope,'root_tool_pair_ref':pairref,'native_exit':-9,**{k:scope[k] for k in ('root_grant_ref','argv','cwd','env_names','initial_tool_input','producer_ref')}}
 if mode=='invocation_foreign':invocation['run_id']='foreign-evidence'
 if mode=='zero_exit':invocation['native_exit']=0
 invref=put('invocation',invocation)
 refusal={**copy.deepcopy(expected),'schema':'researchos.w05.actual-refusal.v2','rejected':True,'invocation_ref':invref,'original_response_ref':response_ref}
 refusalref=put('refusal',refusal)
 issuedscope=scoperef if mode!='unissued_scope' else put('unrelated-scope',{'unrelated':True})
 scopes=[issuedscope]
 originalscopes=copy.deepcopy(scopes)
 if mode=='root_stdout_scope_mismatch':originalscopes=[put('foreign-scope',{'foreign':True})]
 issuance={'schema':'researchos.w05.original-root-grant-issuance.v2','actor_id':'codex:/root','run_id':expected['run_id'],'grant_ref':rootgrant,'negative_scope_refs':scopes,'original_input':{'cmd':'synthetic-issuance-not-run'},'original_result':{'exit_code':0,'output':encode({'grant_ref':rootgrant,'negative_scope_refs':originalscopes}).decode()}}
 issuanceref=put('issuance',issuance)
 context={'run_id':expected['run_id'],'root_grant_ref':rootgrant,'root_grant_issuance_ref':issuanceref,'worktree':scope['cwd']}
 row={'id':'A04-03','lane':expected['lane'],'expected':expected['negative_condition'],'product_identity':identity,'refusal_evidence_refs':[refusalref],'negative_invocation_ref':invref}
 return doc,getraw,context,row,{k:json.loads(v) for k,v in blobs.items()}
for mode in ['valid','scope_foreign','response_foreign','terminal_foreign','terminal_response_foreign','invocation_foreign','zero_exit','unissued_scope','root_stdout_scope_mismatch','response_bool_integer_alias','response_float_integer_alias']:
 doc,raw,context,row,inputs=refusal_case(mode)
 check('NEGATIVE_'+mode,'ACCEPTED' if mode=='valid' else 'REFUSED',lambda doc=doc,raw=raw,context=context,row=row:ns['verify_refusal'](doc,raw,context,row),{'context':context,'row':row,'originals':inputs})
out={'schema':'researchos.independent-pure-controls.v1','qualification':'NONE_SYNTHETIC_SOURCE_DATA_ONLY','author_controls_reexecuted':False,'author_fixtures_used':False,'selected_functions':sorted(wanted),'candidate_module_imports':0,'candidate_entrypoints':0,'SQL_calls':0,'Go_CLI_SDK_model_product_native_calls':0,'results':results,'count':len(results),'matched_count':sum(r['matched'] for r in results)}
with (O/'independent-controls.json').open('xb') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2).encode()+b'\n')
print(json.dumps({'count':len(results),'matched':out['matched_count'],'unmatched':[{k:v for k,v in r.items() if k!='inputs'} for r in results if not r['matched']],'selected_functions':len(wanted),'candidate_imports':0,'SQL_calls':0},ensure_ascii=False))

