import ast, copy, hashlib, json, math
from pathlib import Path
O=Path(__file__).resolve().parent
source=(O/'compose_main24.source.py').read_bytes()
tree=ast.parse(source)
names={'Refusal','need','sha','decode','apply_edits'}
body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
assert len(body)==5
env={'hashlib':hashlib,'json':json,'math':math}
exec(compile(ast.Module(body=body,type_ignores=[]),'<isolated-pure-helper-functions>','exec'),env)
checks=[]
def ok(name, value):
    assert value, name
    checks.append({'id':name,'passed':True})
def reject(name, fn, expected):
    try:fn()
    except env['Refusal'] as exc:ok(name,str(exc)==expected)
    else:raise AssertionError(name+': did not refuse')
sha=env['sha']; apply=env['apply_edits']
original='首A中BC尾'.encode()
pieces=[(len('首'.encode()),len('首A'.encode()),'甲'),(len('首A中'.encode()),len('首A中'.encode()),'新'),(len('首A中B'.encode()),len('首A中BC'.encode()),'')]
edits=[]
for start,end,new in pieces:
    old=original[start:end];n=new.encode()
    edits.append(dict(old_start_byte=start,old_end_byte=end,old_utf8=old.decode(),replacement_utf8=new,old_bytes=len(old),old_sha256=sha(old),new_bytes=len(n),new_sha256=sha(n)))
desired='首甲中新B尾'.encode()
edit=dict(required_current_ref=dict(sha256=sha(original),bytes=len(original)),expected_result_ref=dict(sha256=sha(desired),bytes=len(desired)),edits=edits)
actual,inverse=apply(original,edit)
ok('unicode-replace-insert-delete-exact-desired',actual==desired)
restored=actual
for a in reversed(inverse):restored=restored[:a['start']]+a['replacement_utf8'].encode()+restored[a['end']:]
ok('complete-byte-inverse-exact-original',restored==original)
reject('base-drift-refuses',lambda:apply(original+b'x',edit),'EDIT_BASE')
bad=copy.deepcopy(edit);bad['edits'][0]['old_sha256']='0'*64
reject('old-slice-drift-refuses',lambda:apply(original,bad),'OLD_SLICE_PIN')
bad=copy.deepcopy(edit);bad['edits'][0]['new_sha256']='0'*64
reject('new-slice-drift-refuses',lambda:apply(original,bad),'NEW_SLICE_PIN')
bad=copy.deepcopy(edit);bad['edits'][1]['old_start_byte']=0
reject('overlap-refuses',lambda:apply(original,bad),'EDIT_RANGES')
bad=copy.deepcopy(edit);bad['expected_result_ref']['sha256']='0'*64
reject('final-result-drift-refuses',lambda:apply(original,bad),'EDIT_RESULT_PIN')
reject('duplicate-json-key-refuses',lambda:env['decode']('{"x":1,"x":2}'),'DUPLICATE_JSON_KEY')
reject('nonfinite-json-refuses',lambda:env['decode']('{"x":NaN}'),'NONFINITE_JSON')
reject('overflow-json-number-refuses',lambda:env['decode']('{"x":1e999}'),'NONFINITE_JSON')
constants={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        try:constants[node.targets[0].id]=ast.literal_eval(node.value)
        except (ValueError,TypeError):pass
mapping_path=O.parent.parent/'public23_to24_main_merge_preparation_codex/prepare-20261010-01/file-merge-map.json'
mapping_raw=mapping_path.read_bytes();mapping=json.loads(mapping_raw)
ok('fixed-merge-map-pin',sha(mapping_raw)==constants['MERGE_SHA'])
ok('exact-ordered-40-map-targets',tuple(x['repo_relative_path'] for x in mapping['files'])==constants['PATHS'] and len(set(constants['PATHS']))==40)
ok('ten-existing-thirty-absent-contract',sum(x['current_ref'] is not None for x in mapping['files'])==10)
ok('native-root-selected-v2',constants['NATIVE']==mapping['selected_native_revision']=='b1599aaf259c435db5a0a5313ab0ea65')
result={'schema':'researchos.main24-helper-new-pure-controls.v1','status':'PASS','source_ref':{'path':str(O/'compose_main24.source.py'),'sha256':sha(source),'bytes':len(source)},'checks':checks,'checks_count':len(checks),'helper_module_imported':False,'prepare_or_apply_executed':False,'filesystem_functions_extracted_or_called':False,'Main_Canon_writes':0,'Go_SQL_Native_product_calls':0,'prior_successful_Source_controls_replayed':0,'limits':'Synthetic pure-function checks and new helper contract checks only; no Windows handle, source guard, prepare/apply, runtime or production acceptance.'}
with (O/'new-pure-controls.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=True))

