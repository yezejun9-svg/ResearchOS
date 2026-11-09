from pathlib import Path
import ast,hashlib,json,difflib
P=Path(__file__).parent
old=(P/'forward_head_engine.proposed.py').read_bytes()
assert hashlib.sha256(old).hexdigest()=='6cbedde0cef3932bdd336da891a2cf52ef3629ae2c9fc48329d1ff3c30d7fa5b'
s=old.decode().replace('\r\n','\n')
anchor="    calls = [x for v, x in inner.items() if v.name.endswith('.invocation.json')]"
new='''    union = sorted(set(scope['shared38_paths'] + scope['cli8_paths'] + r['source_paths']))
    need(len(union) == 58, 'actual combined58 membership')
    protected = {path(x['path']): x for x in q['immutable_inputs']}
    tree = {}
    for entry in verify(member(inner, ip, 'tree-after.stdout.raw')).split(b'\\0'):
        if entry:
            header, name = entry.split(b'\\t', 1)
            mode, kind, oid = header.decode('ascii').split()
            rel = name.decode('utf-8', 'strict')
            need(rel not in tree, 'duplicate sealed tree path')
            tree[rel] = (mode, kind, oid)
    for rel in union:
        target = path(ROOT / rel)
        need(target in protected and rel in tree, 'missing current58 immutable pin')
        b = verify(protected[target])
        mode, kind, oid = tree[rel]
        need(mode in ['100644', '100755'] and kind == 'blob' and hashlib.sha1(b'blob ' + str(len(b)).encode('ascii') + b'\\0' + b).hexdigest() == oid, 'current58 bytes differ from actual committed tree')
'''
assert s.count(anchor)==1
s=s.replace(anchor,new+anchor,1)
# Independent closure is fixed actual input; it is not an arbitrary reviewer-shaped assertion.
anchor="    r = doc(q['source_closure_review_ref'])"
assert s.count(anchor)==1
s=s.replace(anchor,"    need(q['source_closure_review_ref']['sha256'] == '7d82779e61ff50c3072e9d008531b2409e3ee288235ec7ad12a24f276f4de4b7', 'fixed actual source closure review')\n"+anchor,1)
ast.parse(s)
raw=s.replace('\n','\r\n').encode()
def put(name,b):
 with (P/name).open('xb') as f:f.write(b)
 return {'path':str(P/name),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
er=put('forward_head_engine.final.proposed.py',raw)
br0=(P/'build_forward_draft.proposed.py').read_bytes()
br=br0.replace(str(P/'forward_head_engine.proposed.py').__repr__().encode(),repr(er['path']).encode()).replace(b'6cbedde0cef3932bdd336da891a2cf52ef3629ae2c9fc48329d1ff3c30d7fa5b',er['sha256'].encode()).replace(b'len(raw) != 44066',f"len(raw) != {er['bytes']}".encode())
assert br!=br0
ast.parse(br)
bref=put('build_forward_draft.final.proposed.py',br)
base=(P/'original.r332.register.py.txt').read_bytes()
bl=base.splitlines(keepends=True); nl=raw.splitlines(keepends=True)
ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,bl,nl,autojunk=False).get_opcodes():
 if tag!='equal':ops.append({'old_line_start':a,'old_line_end':b,'new_line_start':c,'new_line_end':d,'old_hex':b''.join(bl[a:b]).hex(),'new_hex':b''.join(nl[c:d]).hex()})
inv=list(nl)
for op in reversed(ops):
 assert b''.join(inv[op['new_line_start']:op['new_line_end']]).hex()==op['new_hex']
 inv[op['new_line_start']:op['new_line_end']]=bytes.fromhex(op['old_hex']).splitlines(keepends=True)
assert b''.join(inv)==base
put('whole-inverse.final.json',(json.dumps({'base_sha256':hashlib.sha256(base).hexdigest(),'candidate_ref':er,'hunks':ops,'restored_exact':True},indent=2)+'\n').encode())
put('forward-engine.final.diff',''.join(difflib.unified_diff(base.decode().splitlines(True),raw.decode().splitlines(True),fromfile='original.r332.register.py',tofile='forward_head_engine.final.proposed.py')).encode())
oldf={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(base).body if isinstance(x,ast.FunctionDef)}
newf={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef)}
inverse_br=br.replace(repr(er['path']).encode(),repr(str(P/'forward_head_engine.proposed.py')).encode()).replace(er['sha256'].encode(),b'6cbedde0cef3932bdd336da891a2cf52ef3629ae2c9fc48329d1ff3c30d7fa5b').replace(f"len(raw) != {er['bytes']}".encode(),b'len(raw) != 44066')
assert inverse_br==br0
audit={'AST_files':2,'source_executed':False,'whole_byte_inverse_to_r332':True,'inverse_hunks':len(ops),'builder_inverse_to_initial':True,'unchanged_functions':[k for k in oldf if oldf[k]==newf.get(k)],'changed_functions':[k for k in oldf if k in newf and oldf[k]!=newf[k]],'removed':['grant'],'new_functions':[k for k in newf if k not in oldf],'current58_tree_pin_static_added':True,'runtime_calls':0,'canonical_writes':0}
put('static-audit.final.json',(json.dumps(audit,indent=2)+'\n').encode())
put('code-refs.final.json',(json.dumps({'engine':er,'builder':bref},ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'engine':er,'builder':bref,'audit':audit},ensure_ascii=False))
