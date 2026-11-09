import pathlib,json,ast,re,difflib,hashlib
N=pathlib.Path(__file__).parent
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
old=(pathlib.Path(data['att3'])/'candidate-root/internal/domain/client_protocol_attach_contract_windows_test.go').read_text(encoding='utf-8')
current=(pathlib.Path(data['t9'])/'internal/domain/client_protocol_attach_contract_windows_test.go').read_text(encoding='utf-8')
tree=ast.parse((N/'construct-source.py').read_text(encoding='utf-8'))
nodes=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'raw_string','pattern'} for t in node.targets):nodes.append(node)
 if isinstance(node,ast.FunctionDef) and node.name=='tokens':nodes.append(node)
scope={'re':re}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'lexical-only','exec'),scope)
a,b=scope['tokens'](old),scope['tokens'](current)
diff=[]
for tag,a1,a2,b1,b2 in difflib.SequenceMatcher(a=a,b=b).get_opcodes():
 if tag!='equal':diff.append({'tag':tag,'old':a[a1:a2],'current':b[b1:b2],'old_context':a[max(0,a1-5):a2+5],'current_context':b[max(0,b1-5):b2+5]})
result={'old_tokens':len(a),'current_tokens':len(b),'diff':diff,'without_explicit_semicolons_equal':[x for x in a if x!=';']==[x for x in b if x!=';'],'Go_AST_executed':False}
with (N/'lexical-format-difference.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result))

