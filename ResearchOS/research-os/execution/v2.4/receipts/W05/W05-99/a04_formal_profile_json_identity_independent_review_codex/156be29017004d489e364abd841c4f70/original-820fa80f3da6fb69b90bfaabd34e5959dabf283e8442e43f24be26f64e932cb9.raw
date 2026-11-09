from pathlib import Path
import ast, copy, hashlib, json, re
OUT=Path(__file__).parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
PEER=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_binding_independent_review_codex/70ca957e1f4b4d7fb4223159361c86e4/independent-controls.v2.json'
data=json.loads(PEER.read_bytes())
assert hashlib.sha256(PEER.read_bytes()).hexdigest()=='c6d7a23626aea4d968337c2cc4a354d359b74f51bd5450a420ab6d63f87fbcb0'
source=(OUT/'formal_profile_w05.identity.v4.proposed.py').read_text(encoding='utf-8')
tree=ast.parse(source)
names={'_integer','_native_exit','_nonempty','_json_original','_original','_root_pair','_public_value','_schema_value','_database_row','_event_schema','_jsonl','verify_refusal','verify_live_originals','_same_json','_current_run'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('PUBLIC_SCHEMAS','ASSERTION_LANES') for t in n.targets)]
assert len(nodes)==len(names) and len(assignments)==2
env={'json':json,'re':re}
exec(compile(ast.Module(body=assignments+nodes,type_ignores=[]),'<selected-pure-functions>','exec'),env)
assert '_database' not in env
results=[]
def run(label,expected,func,input_record=None,stub=False):
 try:
  func();actual='ACCEPTED';error=None
 except ValueError as exc:
  actual='REFUSED';error=str(exc)
 results.append({'id':label,'expected':expected,'actual':actual,'matched':actual==expected,'error':error,'inputs':input_record,'database_callback_stub':stub,'actual_SQL_calls':0})
def eqcase(label,left,right,expected):
 def test():
  if not env['_same_json'](left,right):raise ValueError('STRICT_JSON_DIFFERENT')
 run(label,expected,test,{'left':left,'right':right})
for a,b in [(1,True),(1,1.0),(True,1.0),(0,False)]:
 eqcase('JSON_TYPE_'+type(a).__name__+'_'+type(b).__name__+'_'+str(a),a,b,'REFUSED')
 eqcase('JSON_RECURSIVE_'+type(a).__name__+'_'+type(b).__name__+'_'+str(a),{'details':[None,{'exit_detail':a}]},{'details':[None,{'exit_detail':b}]},'REFUSED')
eqcase('JSON_EXACT_TYPED_FULL_OBJECT',{'a':[None,True,1,1.0,'中文']},{'a':[None,True,1,1.0,'中文']},'ACCEPTED')
eqcase('JSON_DIFFERENT_OBJECT_ORDER',{'a':1,'b':{'c':2}},{'b':{'c':2},'a':1},'ACCEPTED')
eqcase('JSON_DIFFERENT_ARRAY_ORDER',[1,2],[2,1],'REFUSED')
for value in [float('nan'),float('inf')]:
 # Output retains a textual representation, never nonfinite JSON fixture values.
 def nonfinite(v=value):
  if not env['_same_json'](v,v):raise ValueError('STRICT_JSON_NONFINITE')
 run('JSON_NONFINITE_'+str(value),'REFUSED',nonfinite,{'value_representation':str(value)})
false_rows={r['id']:r for r in data['results'] if not r['matched']}
assert set(false_rows)=={'TASK_FOREIGN_ACTIVE_RUN_EXPECT_REJECT','NEGATIVE_response_bool_integer_alias','NEGATIVE_response_float_integer_alias','COMPOSITE_TASK_ACTIVE_RUN_foreign'}
row_input=copy.deepcopy(false_rows['TASK_FOREIGN_ACTIVE_RUN_EXPECT_REJECT']['inputs'])
def checkrow(d):
 return env['_database_row'](d['kind'],d['sql_revision'],d['sql_content_hash'],json.dumps(d['body']),d['identity'],d['body']['id'])
run('REPLAY_PEER_TASK_FOREIGN_ACTIVE_RUN','REFUSED',lambda:checkrow(row_input),row_input)
for label,pointer in [('CURRENT',row_input['identity']['run_id']),('NULL',None)]:
 d=copy.deepcopy(row_input);d['body']['active_run_id']=pointer
 run('TASK_POINTER_'+label,'ACCEPTED',lambda d=d:checkrow(d),d)
for label,pointer in [('BOOL',True),('EMPTY',''),('FOREIGN','other-run')]:
 d=copy.deepcopy(row_input);d['body']['active_run_id']=pointer
 run('TASK_POINTER_'+label,'REFUSED',lambda d=d:checkrow(d),d)

def readers(originals):
 # Only closed, captured synthetic control documents. We isolate the guard
 # semantics; formal _profile_io path/hash/membership checks are not executed.
 docs={Path(key).name:value for key,value in originals.items()}
 def doc(ref):
  name=Path(ref['path']).name
  value=docs[name]
  return copy.deepcopy(value) if type(value) is dict else env['_json_original'](value)
 def raw(ref):
  value=docs[Path(ref['path']).name]
  return json.dumps(value,ensure_ascii=False).encode() if type(value) is dict else value.encode()
 return doc,raw
for label in ('NEGATIVE_response_bool_integer_alias','NEGATIVE_response_float_integer_alias'):
 d=copy.deepcopy(false_rows[label]['inputs']);doc,raw=readers(d['originals'])
 run('REPLAY_PEER_'+label,'REFUSED',lambda d=d,doc=doc,raw=raw:env['verify_refusal'](doc,raw,d['context'],d['row']),d)
 # Bring the Root-observed response back into exact typed equality while
 # preserving the original scope and invocation/refusal reference labels.
 fixed=copy.deepcopy(d)
 pair=fixed['originals']['pair.json']
 terminal_result=pair['terminal']['result']
 lines=terminal_result['output'].splitlines()
 for i,line in enumerate(lines):
  if line.startswith('{'):
   obj=json.loads(line)
   if 'actual_launcher_native_exit' in obj:
    obj['actual_refusal_response']=copy.deepcopy(fixed['originals']['response.json'])
    lines[i]=json.dumps(obj,ensure_ascii=False)
 terminal_result['output']='\n'.join(lines)
 if pair['initial']==d['originals']['pair.json']['terminal']:
  pair['initial']=copy.deepcopy(pair['terminal'])
 doc,raw=readers(fixed['originals'])
 run('NEGATIVE_EXACT_TYPED_POSITIVE_'+label,'ACCEPTED',lambda d=fixed,doc=doc,raw=raw:env['verify_refusal'](doc,raw,d['context'],d['row']),fixed)

composite=copy.deepcopy(false_rows['COMPOSITE_TASK_ACTIVE_RUN_foreign']['inputs'])
def composite_call(d):
 originals=d['raw_originals']
 # Saved composite raw files are keyed by stem, not hypothetical disk paths.
 def lookup(ref):
  key=Path(ref['path']).stem
  return originals[key]
 def doc(ref):return env['_json_original'](lookup(ref))
 def raw(ref):return lookup(ref).encode()
 env['_database']=lambda raw_value,identity:copy.deepcopy(d['mocked_database_rows'])
 try:
  return env['verify_live_originals'](doc,raw,d['context'],d['row'],d['invocation'],d['scope'])
 finally:
  env.pop('_database',None)
run('REPLAY_PEER_COMPOSITE_FOREIGN_ACTIVE_RUN','REFUSED',lambda:composite_call(composite),composite,True)
for label,pointer in [('CURRENT',composite['row']['product_identity']['run_id']),('NULL',None)]:
 d=copy.deepcopy(composite);d['mocked_database_rows']['Task']['active_run_id']=pointer
 run('COMPOSITE_TERMINAL_POINTER_'+label,'ACCEPTED',lambda d=d:composite_call(d),d,True)
report={'schema':'researchos.a04-json-identity-source-controls.v1','qualification':'NONE_SYNTHETIC_SELECTED_AST_ONLY','basis_peer_controls_ref':{'path':PEER.as_posix(),'sha256':hashlib.sha256(PEER.read_bytes()).hexdigest(),'bytes':len(PEER.read_bytes())},'peer_original_74_70_record_unchanged':True,'replayed_peer_counterexamples':4,'selected_definitions':sorted(names),'no_full_module_import':True,'formal_path_hash_reader_exercised':False,'complete_original_bytes_authority_proven':False,'composite_SQL_stub_explicit':True,'SQL_Go_CLI_SDK_model_native_calls':0,'results':results,'count':len(results),'matched_count':sum(r['matched'] for r in results)}
with (OUT/'source-controls.actual.json').open('xb') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2).encode()+b'\n')
print(json.dumps({'count':len(results),'matched':report['matched_count'],'unmatched':[{'id':r['id'],'error':r['error']} for r in results if not r['matched']],'replayed_peer4':True,'SQL_calls':0,'full_module_imports':0}))

