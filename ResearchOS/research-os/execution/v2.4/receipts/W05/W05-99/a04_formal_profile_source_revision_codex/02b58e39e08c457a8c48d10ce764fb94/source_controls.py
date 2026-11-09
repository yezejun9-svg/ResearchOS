"""Finite selected-AST source-data controls. No module entrypoint, SQL or product."""
import ast,copy,json,re,hashlib
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94")
OLD=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e")
source=(BASE/"formal_profile_w05.final.proposed.py").read_text(encoding="utf-8")
tree=ast.parse(source);tests=ast.parse((OLD/"precheck_a04.py").read_text(encoding="utf-8"))
names={'_integer','_native_exit','_nonempty','_json_original','_original','_root_pair','_jsonl','verify_refusal','verify_capture_bundle','_witness'}
space={'json':json,'re':re,'IDS':tuple('A04-0'+str(i) for i in range(1,7)),'GATES':('W05-G01','W05-G02','W05-H08','W05-P01','W05-U02'),'SCENARIOS':('success','tool_failed','request_timeout','pending_queue_cancel','executor_crash'),'EXTRA':{'A04-04':'H08','A04-05':'P01','A04-06':'U02'},'ASSERTION_LANES':dict(zip(tuple('A04-0'+str(i) for i in range(1,7)),('success','pending_queue_cancel','executor_crash','H08','P01','U02')))}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<selected-source-data-guards>','exec'),space)
checks=[]
def positive(label,fn):
 value=fn();checks.append({'id':label,'classification':'SYNTHETIC_SOURCE_DATA_ONLY','outcome':'SHAPE_ACCEPT','return_type':type(value).__name__})
def negative(label,fn,expected=None):
 try:fn()
 except (ValueError,KeyError,TypeError) as exc:
  if expected and expected not in str(exc):raise AssertionError(label+':wrong refusal:'+str(exc))
  checks.append({'id':label,'classification':'SYNTHETIC_SOURCE_DATA_ONLY','outcome':'REJECT','error':str(exc)});return
 raise AssertionError(label+':accepted')
positive('typed integer zero',lambda:space['_integer'](0,'count'))
for value in (False,True,0.0,None,-1):
 negative('count rejects '+repr(value),lambda value=value:space['_integer'](value,'count'),'OPEN_TYPED_INTEGER')
positive('signed actual native exit retained',lambda:space['_native_exit'](-1,'actual'))
for value in (False,0.0,None):
 negative('native type rejects '+repr(value),lambda value=value:space['_native_exit'](value,'native'))
initial_input={'cmd':'SYNTHETIC SOURCE DATA; NEVER EXECUTED','workdir':'C:/synthetic'}
scope={'initial_tool_input':initial_input}
pair={'schema':'researchos.w05.original-tool-pair.v2','initial':{'tool':'exec_command','input':initial_input,'result':{'session_id':17}},'terminal':{'tool':'write_stdin','input':{'session_id':17,'chars':''},'result':{'exit_code':0,'output':json.dumps({'actual_launcher_native_exit':3})+'\\nACTUAL_PYTHON_EXIT=0'}}}
# Real wire contains a newline; this is data construction, not command execution.
pair['terminal']['result']['output']=json.dumps({'actual_launcher_native_exit':3})+'\nACTUAL_PYTHON_EXIT=0'
positive('complete original session pair shape',lambda:space['_root_pair'](pair,scope))
for label,edit in [('foreign session',lambda x:x['terminal']['input'].update(session_id=18)),('changed initial command',lambda x:x['initial'].update(input={'cmd':'changed'})),('native bool',lambda x:x['terminal']['result'].update(output=json.dumps({'actual_launcher_native_exit':False}))),('missing native bridge',lambda x:x['terminal']['result'].update(output='ACTUAL_PYTHON_EXIT=0'))]:
 broken=copy.deepcopy(pair);edit(broken)
 negative(label,lambda broken=broken:space['_root_pair'](broken,scope))
identity={k:k+'-synthetic' for k in ('project_id','session_id','goal_id','task_id','run_id','core_build_id')}
event={'type':'session.event','event':{'sequence':1,'session_id':identity['session_id'],'protocol_version':'researchos-client/2','core_build_id':identity['core_build_id'],'run_id':identity['run_id'],'kind':'RUN_STATE','payload':{}}}
final={'execution':{**{k:identity[k] for k in ('project_id','session_id','goal_id','task_id','run_id')},'event_sequence':1,'independent_acceptance':'NOT_EVALUATED','exit_code':3}}
def wire(frames):return ('\n'.join(json.dumps(f) for f in frames)+'\n').encode()
positive('real CLI outer event and terminal field shape',lambda:space['_jsonl'](wire([event,final]),identity))
for label,frames in [('event after final',[event,final,event]),('snapshot unsupported',[{'type':'session.snapshot','snapshot':{}},final]),('missing event stream',[final]),('duplicate terminal',[event,final,final])]:
 negative(label,lambda frames=frames:space['_jsonl'](wire(frames),identity))
changed=copy.deepcopy(final);changed['execution']['task_id']='foreign'
negative('final cross task',lambda:space['_jsonl'](wire([event,changed]),identity))
changed=copy.deepcopy(event);changed['event']['sequence']=True
negative('boolean event sequence',lambda:space['_jsonl'](wire([changed,final]),identity))
# Existing fixture values supply only scalar field controls; the full original
# gate is explicitly stubbed and no LIVE/SQL/OS qualification is inferred.
vals={'re':re,'copy':copy}
for node in tests.body:
 if isinstance(node,ast.ClassDef) and node.name=='API' or isinstance(node,ast.FunctionDef) and node.name=='row' or isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('LANES','INV','facts','context','raw_values'):
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<scalar-source-control-values>','exec'),vals)
proofs={}
for cid,facts in vals['facts'].items():
 lane=vals['LANES'][cid];proofs[cid]={'schema':'researchos.w05.a04-raw-observation.v1','assertion_id':cid,'run_id':vals['context']['run_id'],'lane':lane,'invocation_ref':next(x['invocation_ref'] for x in vals['INV'] if x['lane']==lane),'facts':facts,'actual':'observed-'+cid,'fact_source_refs':{k:{'path':'raw-'+cid,'sha256':'d'*64,'locator':{'json_pointer':'/facts/'+k}} for k in facts}}
def raw(_a,_r,reference):
 if reference['path'].startswith('obs-'):return proofs[reference['path'][4:]]
 if reference['path'].startswith('raw-'):return vals['raw_values'][reference['path'][4:]][reference['locator']['json_pointer'][7:]]
 raise ValueError('unknown source-data ref')
space['_raw']=raw;space['_live_gate']=lambda *_:None;space['_doc']=lambda *_:{'selected_runtime':'mu'}
negative_ref={'path':'negative','sha256':'a'*64}
response_ref={'path':'response','sha256':'a'*64};pair_ref={'path':'pair','sha256':'a'*64};refusal_ref={'path':'refusal','sha256':'a'*64}
def enriched(cid):
 row=vals['row'](cid);row.update(product_identity=identity,original_witness_ref={'path':'unsupported','sha256':'a'*64},negative_invocation_ref=negative_ref,refusal_evidence_refs=[refusal_ref]);return row
docs={'negative':{'native_exit':3,'root_tool_pair_ref':pair_ref,'scope':scope},'pair':pair,'response':{'status':'REJECTED','task_id':identity['task_id']}}
row=enriched('A04-02');docs['refusal']={'schema':'researchos.w05.actual-refusal.v2','assertion_id':'A04-02','run_id':vals['context']['run_id'],'lane':'pending_queue_cancel','task_id':identity['task_id'],'rejected':True,'negative_condition':row['expected'],'invocation_ref':negative_ref,'original_response_ref':response_ref}
doc=lambda ref:docs[ref['path']];whole=lambda ref:b'synthetic source-data bytes only'
space['_profile_io']=lambda *_:(doc,whole)
positive('refusal full identity and original native result shape',lambda:space['verify_refusal'](doc,whole,vals['context'],row))
for key,value in (('rejected',False),('task_id','foreign'),('run_id','foreign'),('lane','success'),('negative_condition','arbitrary')):
 old=docs['refusal'][key];docs['refusal'][key]=value
 negative('refusal '+key,lambda:space['verify_refusal'](doc,whole,vals['context'],row))
 docs['refusal'][key]=old
old=docs['negative']['native_exit'];docs['negative']['native_exit']=0
negative('refusal zero actual native outcome',lambda:space['verify_refusal'](doc,whole,vals['context'],row))
docs['negative']['native_exit']=old
invocations={lane:{} for lane in vals['LANES'].values()}
positive('scalar cancel field guard only, original gate stubbed',lambda:space['_witness'](vals['API'],None,row,vals['context'],invocations))
for key in ('owned_tool_processes_after','pending_requests_after','late_launches'):
 old=vals['facts']['A04-02'][key];vals['facts']['A04-02'][key]=False;vals['raw_values']['A04-02'][key]=False
 negative('cancel bool '+key,lambda:space['_witness'](vals['API'],None,row,vals['context'],invocations),'A04_CANCEL')
 vals['facts']['A04-02'][key]=old;vals['raw_values']['A04-02'][key]=old
wrong=copy.deepcopy(row);wrong['lane']='success';proofs['A04-02']['lane']='success';proofs['A04-02']['invocation_ref']=vals['INV'][0]['invocation_ref']
negative('consistent cancellation relabeled success',lambda:space['_witness'](vals['API'],None,wrong,vals['context'],invocations),'ASSERTION_LANE')
# Compile/inspect remaining original readers but never execute database or
# whole module/controller entrypoints.
source_files=list(BASE.glob('*.proposed.py'))
for file in source_files:ast.parse(file.read_bytes())
if "b'SQLite format 3\\\\x00'" in source:raise AssertionError('literal SQLite header escape wrong')
out={'schema':'researchos.a04-source-revision-pure-ast-controls.v1','checks':checks,'count':len(checks),'source_asts_parsed':len(source_files),'full_candidate_entrypoints':0,'sqlite_calls':0,'native_os_calls':0,'model_calls':0,'canonical_writes':0,'formal_acceptance_increment':0,'full_original_gate_stubbed_only_for_scalar_leaf_controls':True,'qualification':'NONE_SYNTHETIC_SOURCE_DATA_ONLY'}
rawout=(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode()
with (BASE/'controls.actual.json').open('xb') as f:f.write(rawout)
print(json.dumps({'controls_ref':{'path':str(BASE/'controls.actual.json').replace('\\','/'),'sha256':hashlib.sha256(rawout).hexdigest(),'bytes':len(rawout)},'count':len(checks),'source_asts_parsed':len(source_files),'sqlite_native_model_calls':0},ensure_ascii=False))

