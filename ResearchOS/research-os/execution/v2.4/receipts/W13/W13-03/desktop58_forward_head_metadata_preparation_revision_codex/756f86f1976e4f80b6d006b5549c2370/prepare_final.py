"""Pure IO/AST: add the independently identified exact MODE-line repair."""
from pathlib import Path
import ast,difflib,hashlib,json
P=Path(__file__).parent
OLD=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_codex/503ef47ea65144029c73a4d7bf19409a')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,b):
 with (P/n).open('xb') as f:f.write(b)
 return pin(P/n)
def obj(n,x):return put(n,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
old=(P/'forward_head_engine.v2.proposed.py').read_bytes()
assert hashlib.sha256(old).hexdigest()=='da7589b15de7c81d02642a14f02a33d827cc165b2920d8a413cb5ba0d56f8b1c'
original=(OLD/'forward_head_engine.selected.proposed.py').read_bytes()
assert hashlib.sha256(original).hexdigest()=='b9318a1f361b9ed4aa42e1e21e41bb4eefd5909310a73f396820e1680286ef47'
replace_old=b'''source.replace(b"MODE = 'register'", ("MODE = '" + mode + "'").encode(), 1)'''
replace_new=b'''source.replace(b"\nMODE = 'register'\n", ("\nMODE = '" + mode + "'\n").encode(), 1)'''.replace(b'\n',b'\\n')
# Build source bytes explicitly: the candidate literal contains backslash-n,
# while the future value is the actual whole newline-delimited assignment.
replace_new=b'source.replace(b"\\nMODE = \'register\'\\n", ("\\nMODE = \'" + mode + "\'\\n").encode(), 1)'
count_old=b'''source.count(b"MODE = 'register'")==1'''
count_old=b'''source.count(b"MODE = 'register'") == 1'''
count_new=b'''source.count(b"\nMODE = 'register'\n") == 1'''.replace(b'\n',b'\\n')
assert old.count(replace_old)==2 and old.count(count_old)==1
new=old.replace(replace_old,replace_new).replace(count_old,count_new)
assert new.replace(replace_new,replace_old).replace(count_new,count_old)==old
ast.parse(new)
anchor=b"\nMODE = 'register'\n"
assert old.count(b"MODE = 'register'")==4
assert new.count(anchor)==1
derived=[]
for mode in ['register','run','seal']:
 actual=new.replace(anchor,("\nMODE = '"+mode+"'\n").encode(),1)
 tree=ast.parse(actual)
 assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODE' for t in n.targets)]
 assert len(assignments)==1 and isinstance(assignments[0].value,ast.Constant) and assignments[0].value.value==mode
 reverse=actual.replace(("\nMODE = '"+mode+"'\n").encode(),anchor,1)
 assert reverse==new
 derived.append({'mode':mode,'byte_length':len(actual),'sha256':hashlib.sha256(actual).hexdigest(),'exact_assignment_once':True,'inverse':True,'executed':False})
er=put('forward_head_engine.final.proposed.py',new)
ob=(P/'build_forward_draft.v2.proposed.py').read_bytes()
changes=[(repr(str(P/'forward_head_engine.v2.proposed.py')).encode(),repr(er['path']).encode()),(hashlib.sha256(old).hexdigest().encode(),er['sha256'].encode()),(f'len(raw) != {len(old)}'.encode(),f'len(raw) != {len(new)}'.encode())]
nb=ob
for a,b in changes:
 assert nb.count(a)==1;nb=nb.replace(a,b,1)
ast.parse(nb)
rev=nb
for a,b in reversed(changes):rev=rev.replace(b,a,1)
assert rev==ob
br=put('build_forward_draft.final.proposed.py',nb)
ol=original.splitlines(keepends=True);nl=new.splitlines(keepends=True)
ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,ol,nl,autojunk=False).get_opcodes():
 if tag!='equal':ops.append({'old_line_start':a,'old_line_end':b,'new_line_start':c,'new_line_end':d,'old_hex':b''.join(ol[a:b]).hex(),'new_hex':b''.join(nl[c:d]).hex()})
inverse=list(nl)
for op in reversed(ops):
 assert b''.join(inverse[op['new_line_start']:op['new_line_end']]).hex()==op['new_hex']
 inverse[op['new_line_start']:op['new_line_end']]=bytes.fromhex(op['old_hex']).splitlines(keepends=True)
assert b''.join(inverse)==original
obj('whole-inverse.final.json',{'base_ref':pin(OLD/'forward_head_engine.selected.proposed.py'),'candidate_ref':er,'hunks':ops,'restored_exact':True,'builder_previous_ref':pin(P/'build_forward_draft.v2.proposed.py'),'builder_final_ref':br,'builder_replacements':[{'old_hex':a.hex(),'new_hex':b.hex()} for a,b in changes],'builder_restored_exact':True})
put('engine.final.diff',''.join(difflib.unified_diff(original.decode().splitlines(True),new.decode().splitlines(True),fromfile='b9318a1-selected',tofile='final-proposed')).encode())
of={n.name:n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)}
nf={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
assert set(of)==set(nf)
changed=[k for k in of if ast.dump(of[k],include_attributes=False)!=ast.dump(nf[k],include_attributes=False)]
assert changed==['setup','closure','prepare_request']
unchanged=[]
for k in of:
 if k in changed:continue
 a,b=of[k],nf[k];assert b''.join(ol[a.lineno-1:a.end_lineno])==b''.join(nl[b.lineno-1:b.end_lineno]);unchanged.append(k)
obj('static-audit.final.json',{'candidate_imported_or_executed':False,'AST_candidate_files':2,'original_bare_substring_count':4,'final_whole_line_count':1,'mode_derivations_pure_IO_AST':derived,'runtime_guard':'same(scope.runtime_resources_ref,q.runtime_resources_ref); existing path/SHA/bytes predicate unchanged','changed_functions':changed,'unchanged_AST_and_byte_functions':unchanged,'whole_byte_inverse':True,'future_runtime_negatives':'NOT_RUN','Root_params_actualdraft_canonical_product_writes':0,'mode_repair_did_not_run_candidate':True})
obj('code-refs.final.json',{'engine':er,'builder':br})
print(json.dumps({'engine':er,'builder':br,'changed':changed,'unchanged':len(unchanged),'inverse_hunks':len(ops),'new_origins':0},ensure_ascii=False))
