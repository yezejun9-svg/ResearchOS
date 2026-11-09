"""Own readonly-source metadata review, finite pins/AST only."""
from pathlib import Path
import ast,json,hashlib
OWN=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_terminal_pairing_independent_source_review_codex/5ee0bc895e324d94852e95e383292cfd')
BASE=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_binding_terminal_pairing_preparation_codex/f38b92cdbd4844529ce3da03d08630ad')
def pin(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,v):
 with (OWN/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
h=json.loads((BASE/'handoff.json').read_bytes());mf=json.loads((BASE/'manifest.json').read_bytes())
before=json.loads((BASE/'inputs.before.json').read_bytes())['files'];after=json.loads((BASE/'inputs.after.json').read_bytes())
refs=before+mf['files']+[pin(BASE/'manifest.json'),h['controller_ref_unchanged']]
records={};buffers={}
for ref in refs:
 p=Path(ref['path']);b=p.read_bytes();actual=pin(p,b)
 records[str(p)]={'expected_ref':ref,'actual_ref':actual,'matches':ref['sha256']==actual['sha256'] and ref['bytes']==actual['bytes']}
 buffers[str(p)]=b
save('input-pins.before.json',{'rows':list(records.values()),'input_count':len(before),
 'author_members':len(mf['files']),'author_after_ref_list_exact':after['files']==before,
 'catalog_backing_members_rehashed':False})
checks=[]
for key in ('authority_ref','binding_ref'):
 ref=h[key];p=Path(ref['path'])
 inv=json.loads(next(Path(r['path']) for r in mf['files'] if Path(r['path']).name==p.name+'.inverse.json').read_bytes())
 old=Path(inv['original_ref']['path']).read_bytes();new=p.read_bytes();back=new.decode('utf8');forward=old.decode('utf8')
 rev_counts=[];fwd_counts=[]
 for edit in reversed(inv['edits']):
  rev_counts.append([edit['label'],back.count(edit['new'])])
  if back.count(edit['new'])==1:back=back.replace(edit['new'],edit['old'],1)
 for edit in inv['edits']:
  fwd_counts.append([edit['label'],forward.count(edit['old'])])
  if forward.count(edit['old'])==1:forward=forward.replace(edit['old'],edit['new'],1)
 ot=ast.parse(old.decode('utf8'));nt=ast.parse(new.decode('utf8'))
 of={n.name:n for n in ot.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 nf={n.name:n for n in nt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 checks.append({'source_ref':ref,'old_ref':inv['original_ref'],
 'reverse_counts':rev_counts,'forward_counts':fwd_counts,
 'whole_reverse_equal':back.encode('utf8')==old,'whole_forward_equal':forward.encode('utf8')==new,
 'changed_AST_functions':[k for k in nf if k not in of or ast.dump(nf[k],include_attributes=False)!=ast.dump(of[k],include_attributes=False)],
 'unchanged_AST_functions':[k for k in nf if k in of and ast.dump(nf[k],include_attributes=False)==ast.dump(of[k],include_attributes=False)],
 'candidate_imported_or_executed':False})
save('inverse-and-AST.json',checks)
(OWN/'snapshots').mkdir();copies=[]
for ref in [h['authority_ref'],h['binding_ref'],h['controller_ref_unchanged'],h['contract_ref']]:
 p=Path(ref['path']);dst=OWN/'snapshots'/(p.name+'.txt')
 with dst.open('xb') as f:f.write(p.read_bytes())
 copies.append({'source_ref':ref,'copy_ref':pin(dst)})
save('snapshot-map.json',copies)
final=[{'initial_ref':row['actual_ref'],'final_ref':pin(p),'unchanged':Path(p).read_bytes()==buffers[p]} for p,row in records.items()]
save('input-pins.after.json',{'rows':final,'drift':[x for x in final if not x['unchanged']],
 'mismatches':[x for x in records.values() if not x['matches']]})
save('origins.json',{'new_origins':[],'new_failed_events':0,'old_origins_recounted':False,'canonical_writes':0})
print(json.dumps({'input_count':len(before),'author_members':len(mf['files']),'unique_refs':len(records),
 'drift':sum(not x['unchanged'] for x in final),'mismatch':sum(not x['matches'] for x in records.values()),
 'inverse_and_AST':checks,'candidate_executions':0},ensure_ascii=False))

