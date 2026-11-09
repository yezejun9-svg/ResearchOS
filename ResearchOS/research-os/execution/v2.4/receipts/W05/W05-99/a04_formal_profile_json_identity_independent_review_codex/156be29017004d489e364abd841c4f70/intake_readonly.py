import ast,difflib,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_json_identity_revision_codex/90e455115bf34f81bd29e601debf511a")
seen=[]
def save(p,expected=None):
 b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};q=O/('original-'+r['sha256']+'.raw')
 if expected is not None:assert (r['sha256'],r['bytes'])==(expected['sha256'],expected['bytes'])
 if not q.exists():
  with q.open('xb') as f:f.write(b)
 else:assert q.read_bytes()==b
 seen.append(dict(r,snapshot=str(q)));return b
hand=json.loads(save(B/'handoff.json',{'sha256':'f548dac3821e9a2966e5667ba1d3c990ff4a603f144769af20fc65ac0a2a6234','bytes':7998}))
mf=json.loads(save(B/'manifest.json',hand['manifest_ref']))
for r in mf['members']:save(Path(r['path']),r)
report=json.loads(Path(hand['report_ref']['path']).read_bytes())
for key in ['basis_independent_review_ref','basis_review_handoff_ref','basis_source_handoff_ref','basis_source_manifest_ref']:
 r=hand[key];save(Path(r['path']),r)
oldhand=json.loads(Path(hand['basis_source_handoff_ref']['path']).read_bytes())
for r in oldhand['source_pins'].values():save(Path(r['path']),r)
r=report['basis_peer_controls_ref'];save(Path(r['path']),r)
for x in report['request_dispositions']:
 if 'public_producer_ref' in x:save(Path(x['public_producer_ref']['path']),x['public_producer_ref'])
if (B/'postseal-original-tool-io.json').exists():save(B/'postseal-original-tool-io.json')
with (O/'inputs.initial.json').open('xb') as f:f.write(json.dumps(seen,ensure_ascii=False,indent=2).encode()+b'\n')
src=Path(hand['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8');old=Path(oldhand['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8')
tree=ast.parse(src);ls=src.splitlines()
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['_same_json','_current_run','verify_refusal','_database_row']:
  print('\nFUNCTION '+node.name)
  for i in range(node.lineno,node.end_lineno+1):print(str(i)+':'+ls[i-1])
on={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};nn={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for name in ['verify_live_originals','verify_refusal','_database_row']:
 print('\nDIFF '+name)
 print('\n'.join(difflib.unified_diff(ast.get_source_segment(old,on[name]).splitlines(),ast.get_source_segment(src,nn[name]).splitlines())))
print('\nFAILURE ORIGINAL')
print((B/'failure-origin.9691d9.json').read_text(encoding='utf-8'))
print('\nCOUNTS '+json.dumps({'new_members':len(mf['members']),'read_entries':len(seen),'unique_paths':len({x['path'] for x in seen})}))

