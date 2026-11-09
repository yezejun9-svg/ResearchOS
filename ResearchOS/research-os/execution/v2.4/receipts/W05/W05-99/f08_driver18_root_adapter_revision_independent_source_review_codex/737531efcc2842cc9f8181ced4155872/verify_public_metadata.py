"""Own finite metadata IO/AST only. Never imports candidate sources."""
from pathlib import Path
import json,hashlib,ast
OWN=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_adapter_revision_independent_source_review_codex/737531efcc2842cc9f8181ced4155872')
BASE=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_binding_revision_preparation_codex/ae14ede5d4d34ea493f9945886997cb2')
def pin(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,obj):
 with (OWN/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
h=json.loads((BASE/'handoff.json').read_bytes())
mf=json.loads((BASE/'manifest.json').read_bytes())
inputs=json.loads((BASE/'inputs.final.before.json').read_bytes())['files']
after=json.loads((BASE/'inputs.after.json').read_bytes())
scope=json.loads(Path(h['scope_template_ref']['path']).read_bytes())
fixedref=scope['fixed_inputs_ref'];fixed=json.loads(Path(fixedref['path']).read_bytes())
extra=[fixedref]+[fixed[k] for k in ('test_source_ref','producer_ref','probe_ref','original_regression_ref')]
refs=mf['files']+inputs+extra+[pin(BASE/'manifest.json')]
records={};buffers={}
for ref in refs:
 p=Path(ref['path']);b=p.read_bytes();key=str(p);actual=pin(p,b)
 records[key]={'expected_ref':ref,'actual_ref':actual,'matches':actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']}
 buffers[key]=b
save('input-pins.before.json',{'rows':list(records.values()),'original_inputs':len(inputs),
 'author_members':len(mf['files']),'author_after_exact':after['files']==inputs,'catalog_backing_members_rehashed':False})
inverse=[];inventories=[]
for key,ref in h['selected_source_refs'].items():
 invref=next(r for r in mf['files'] if Path(r['path']).name==Path(ref['path']).name+'.inverse.json')
 inv=json.loads(Path(invref['path']).read_bytes());old=Path(inv['original_ref']['path']).read_bytes();new=Path(ref['path']).read_bytes()
 text=new.decode('utf-8');steps=[]
 for edit in reversed(inv['edits']):
  count=text.count(edit['new']);steps.append({'label':edit['label'],'matched_new_count':count})
  if count==1:text=text.replace(edit['new'],edit['old'],1)
 restored=text.encode('utf-8')
 forward=old.decode('utf-8');forward_steps=[]
 for edit in inv['edits']:
  count=forward.count(edit['old']);forward_steps.append({'label':edit['label'],'matched_old_count':count})
  if count==1:forward=forward.replace(edit['old'],edit['new'],1)
 ot=ast.parse(old.decode('utf-8'));nt=ast.parse(new.decode('utf-8'))
 of={n.name:n for n in ot.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 nf={n.name:n for n in nt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changed=[n for n in nf if n not in of or ast.dump(nf[n],include_attributes=False)!=ast.dump(of[n],include_attributes=False)]
 unchanged=[n for n in nf if n in of and ast.dump(nf[n],include_attributes=False)==ast.dump(of[n],include_attributes=False)]
 inverse.append({'key':key,'old_ref':inv['original_ref'],'new_ref':ref,'reverse_steps':steps,'forward_steps':forward_steps,
 'whole_reverse_bytes_equal':restored==old,'whole_forward_bytes_equal':forward.encode('utf-8')==new,
 'restored_whole_AST_equal':ast.dump(ast.parse(restored.decode('utf-8')),include_attributes=False)==ast.dump(ot,include_attributes=False),
 'changed_AST_functions':changed,'unchanged_AST_functions':unchanged,'removed_functions':list(set(of)-set(nf))})
 inventories.append({'key':key,'functions':[(n.name,n.lineno,n.end_lineno) for n in nf.values()],
 'imports':[ast.dump(n,include_attributes=False) for n in nt.body if isinstance(n,(ast.Import,ast.ImportFrom))]})
save('byte-inverse-and-AST.json',inverse);save('source-inventory.json',inventories)
(OWN/'snapshots').mkdir()
copies=[]
for ref in list(h['selected_source_refs'].values())+extra:
 p=Path(ref['path']);dst=OWN/'snapshots'/(p.name+'.txt')
 with dst.open('xb') as f:f.write(p.read_bytes())
 copies.append({'source_ref':ref,'copy_ref':pin(dst)})
save('snapshot-map.json',copies)
final=[{'initial_ref':row['actual_ref'],'final_ref':pin(p),'same_bytes':Path(p).read_bytes()==buffers[p]} for p,row in records.items()]
save('input-pins.after.json',{'rows':final,'drift':[x for x in final if not x['same_bytes']],
 'mismatches':[x for x in records.values() if not x['matches']]})
save('origins.json',{'new_origins':[],'new_failed_events':0,'old_origins_recounted':False,'canonical_writes':0})
print(json.dumps({'refs':len(records),'author_members':len(mf['files']),'original_inputs':len(inputs),
 'mismatch':sum(not x['matches'] for x in records.values()),'drift':sum(not x['same_bytes'] for x in final),
 'inverse':inverse,'snapshot_count':len(copies),'targets':0},ensure_ascii=False))

