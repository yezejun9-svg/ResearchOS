"""Narrow independent re-review of two identity fixes; original four counterexamples plus fresh data."""
import ast,copy,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_json_identity_revision_codex/90e455115bf34f81bd29e601debf511a")
h=json.loads((B/'handoff.json').read_bytes());report=json.loads((B/'report.json').read_bytes());src=Path(h['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8');tree=ast.parse(src)
wanted={'_same_json','_current_run','_database_row','_public_value','_schema_value','_json_original','_integer','_native_exit','_nonempty','_original','_root_pair','verify_refusal','_jsonl','_event_schema','verify_live_originals'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted];assert len(nodes)==len(wanted)
for n in ast.walk(ast.Module(body=nodes,type_ignores=[])):
 if isinstance(n,(ast.Import,ast.ImportFrom)):assert isinstance(n,ast.Import) and all(x.name in ('math','datetime') for x in n.names)
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):assert n.func.id not in {'open','eval','exec','compile','__import__','input'}
schema=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PUBLIC_SCHEMAS' for x in n.targets))
ns={'json':json,'re':re,'PUBLIC_SCHEMAS':schema,'ASSERTION_LANES':{'A04-01':'success'}}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<independent-selected-pure-functions>','exec'),ns)
previous=json.loads(Path(report['basis_peer_controls_ref']['path']).read_bytes());old={x['id']:x for x in previous['results']}
results=[]
def enc(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def r(name,data):return {'path':name,'sha256':hashlib.sha256(enc(data)).hexdigest()}
def check(label,expected,fn,inputs):
 try:fn();actual='ACCEPTED';error=None
 except Exception as e:actual='REFUSED';error=type(e).__name__+':'+str(e)
 results.append({'id':label,'expected':expected,'actual':actual,'matched':actual==expected,'error':error,'inputs':inputs})
def refusal(inputs):
 originals=inputs['originals']
 def raw(ref):
  data=enc(originals[ref['path']])
  assert hashlib.sha256(data).hexdigest()==ref['sha256'],'independent ref hash mismatch'
  return data
 ns['verify_refusal'](lambda ref:json.loads(raw(ref)),raw,inputs['context'],inputs['row'])
def dbrow(inputs):
 ns['_database_row'](inputs['kind'],inputs['sql_revision'],inputs['sql_content_hash'],enc(inputs['body']),inputs['identity'],inputs['body']['id'])
def composite(inputs):
 objs=inputs['mocked_database_rows'];identity=inputs['row']['product_identity']
 for kind,key in [('Task','Task'),('Run','TaskRun')]:
  v=objs[key];ns['_database_row'](kind,v['revision'],None,enc(v),identity,v['id'])
 for aid,v in objs['Artifacts'].items():ns['_database_row']('Artifact',v['revision'],v['content_hash'],enc(v),identity,aid)
 def raw(ref):
  b=inputs['raw_originals'][ref['path']].encode()
  assert hashlib.sha256(b).hexdigest()==ref['sha256'],'independent ref hash mismatch'
  return b
 ns['_database']=lambda rawbytes,ident:copy.deepcopy(objs)
 ns['verify_live_originals'](lambda ref:json.loads(raw(ref)),raw,inputs['context'],inputs['row'],inputs['invocation'],inputs['scope'])
# Exact old independently created false-acceptance inputs; author controls never executed.
replays=[('TASK_FOREIGN_ACTIVE_RUN_EXPECT_REJECT',dbrow),('NEGATIVE_response_bool_integer_alias',refusal),('NEGATIVE_response_float_integer_alias',refusal),('COMPOSITE_TASK_ACTIVE_RUN_foreign',composite)]
for label,fn in replays:
 inputs=copy.deepcopy(old[label]['inputs']);check('REPLAY_'+label,'REFUSED',lambda fn=fn,inputs=inputs:fn(inputs),inputs)
# Confirm a composite guard itself rejects foreign pointer even when DB is a prevalidated stub,
# matching the prior source guard counterexample rather than stopping only at row validation.
def composite_guard_only(inputs):
 def raw(ref):
  data=inputs['raw_originals'][ref['path']].encode()
  assert hashlib.sha256(data).hexdigest()==ref['sha256']
  return data
 ns['_database']=lambda rawbytes,ident:copy.deepcopy(inputs['mocked_database_rows'])
 ns['verify_live_originals'](lambda ref:json.loads(raw(ref)),raw,inputs['context'],inputs['row'],inputs['invocation'],inputs['scope'])
inputs=copy.deepcopy(old['COMPOSITE_TASK_ACTIVE_RUN_foreign']['inputs'])
check('FOREIGN_POINTER_COMPOSITE_GUARD_ONLY','REFUSED',lambda:composite_guard_only(inputs),inputs)
for name,fn in [('TASK_FULL_NULL',dbrow),('NEGATIVE_valid',refusal),('COMPOSITE_TASK_ACTIVE_RUN_current',composite)]:
 inputs=copy.deepcopy(old[name]['inputs']);check('POSITIVE_'+name,'ACCEPTED',lambda fn=fn,inputs=inputs:fn(inputs),inputs)
# New direct JSON comparison pairs, including nested and reordered objects.
pairs=[
 ('bool_int',True,1,False),('int_float',1,1.0,False),('false_zero',False,0,False),
 ('nested_object_alias',{'outer':{'value':False}},{'outer':{'value':0}},False),
 ('nested_array_alias',[{'values':[1,{'x':True}]}],[{'values':[1,{'x':1}]}],False),
 ('same_nested',{'a':[None,False,0,1.0,'中文']},{'a':[None,False,0,1.0,'中文']},True),
 ('reordered_object',{'a':1,'b':{'x':2,'y':3}},{'b':{'y':3,'x':2},'a':1},True),
 ('array_order',[1,2],[2,1],False),('missing_null',{'a':None},{},False),('same_float',1.25,1.25,True),
 ('different_string','1',1,False),('same_null',None,None,True)]
for label,left,right,expected in pairs:
 actual=ns['_same_json'](left,right)
 results.append({'id':'JSON_'+label,'expected':expected,'actual':actual,'matched':actual is expected,'error':None,'inputs':{'left':left,'right':right}})
# Fresh nested terminal-vs-original response variations, rebuilding every affected exact ref.
def amended_response(original_detail,terminal_detail):
 inp=copy.deepcopy(old['NEGATIVE_valid']['inputs']);objs=inp['originals']
 objs['response.json']['details']=original_detail
 response_ref=r('response.json',objs['response.json'])
 closed=json.loads(objs['pair.json']['initial']['result']['output'])
 closed['actual_refusal_response']=copy.deepcopy(objs['response.json']);closed['actual_refusal_response']['details']=terminal_detail
 objs['pair.json']['initial']['result']['output']=enc(closed).decode();objs['pair.json']['terminal']=copy.deepcopy(objs['pair.json']['initial'])
 objs['invocation.json']['root_tool_pair_ref']=r('pair.json',objs['pair.json'])
 objs['refusal.json']['invocation_ref']=r('invocation.json',objs['invocation.json']);objs['refusal.json']['original_response_ref']=response_ref
 inp['row']['negative_invocation_ref']=r('invocation.json',objs['invocation.json']);inp['row']['refusal_evidence_refs']=[r('refusal.json',objs['refusal.json'])]
 return inp
for label,left,right,expected in [
 ('nested_bool_alias',{'a':[{'b':True}]},{'a':[{'b':1}]},'REFUSED'),
 ('nested_float_alias',{'a':[{'b':1}]},{'a':[{'b':1.0}]},'REFUSED'),
 ('same_nested_types',{'a':[False,None,3,2.5]},{'a':[False,None,3,2.5]},'ACCEPTED'),
 ('same_keys_reordered',{'a':1,'b':2},{'b':2,'a':1},'ACCEPTED'),
 ('array_reordered',{'a':[1,2]},{'a':[2,1]},'REFUSED')]:
 inputs=amended_response(left,right)
 check('TERMINAL_'+label,expected,lambda inputs=inputs:refusal(inputs),inputs)
# Public nullable terminal pointer: row and composite positive; null never skips provenance.
inputs=copy.deepcopy(old['TASK_FULL_NULL']['inputs']);inputs['body']['active_run_id']=None
check('ROW_NULL_TERMINAL_ACTIVE_RUN','ACCEPTED',lambda:dbrow(inputs),inputs)
base_composite=copy.deepcopy(old['COMPOSITE_TASK_ACTIVE_RUN_current']['inputs']);base_composite['mocked_database_rows']['Task']['active_run_id']=None
check('COMPOSITE_NULL_TERMINAL_ACTIVE_RUN','ACCEPTED',lambda:composite(base_composite),base_composite)
for label,key,value in [('wrong_revision','revision',8),('not_settled','status','RUNNING'),('children_alive','children_stopped',False)]:
 inputs=copy.deepcopy(base_composite);inputs['mocked_database_rows']['TaskRun'][key]=value
 check('NULL_POINTER_STILL_REJECTS_'+label,'REFUSED',lambda inputs=inputs:composite(inputs),inputs)
out={'schema':'researchos.a04-json-identity-independent-controls.v1','qualification':'NONE_SYNTHETIC_SOURCE_DATA_ONLY','selected_functions':sorted(wanted),'previous_independent_control_source_ref':report['basis_peer_controls_ref'],'author_controls_reexecuted':False,'new_fresh_cases':len(results)-4,'exact_prior_counterexamples_replayed':4,'candidate_module_imports':0,'candidate_entrypoints':0,'SQL_calls':0,'Go_CLI_model_SDK_native_product_calls':0,'composite_database_stub':True,'results':results,'control_count':len(results),'matched_count':sum(x['matched'] for x in results)}
with (O/'independent-controls.json').open('xb') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2).encode()+b'\n')
print(json.dumps({'control_count':len(results),'matched_count':out['matched_count'],'unmatched':[{k:v for k,v in x.items() if k!='inputs'} for x in results if not x['matched']],'prior_counterexamples_replayed':4,'candidate_imports':0,'SQL_calls':0},ensure_ascii=False))

