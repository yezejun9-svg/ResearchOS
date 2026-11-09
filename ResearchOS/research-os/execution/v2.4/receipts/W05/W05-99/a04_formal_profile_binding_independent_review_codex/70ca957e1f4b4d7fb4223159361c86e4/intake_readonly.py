import ast,hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94")
def pin(p):
 r=p.read_bytes(); h=hashlib.sha256(r).hexdigest(); q=O/('original-'+h+'.raw')
 if not q.exists():
  with q.open('xb') as f:f.write(r)
 else: assert q.read_bytes()==r
 return r,{'path':str(p),'sha256':h,'bytes':len(r),'snapshot':str(q)}
seen=[]
for name in ['handoff.json','manifest.json','report.json']:
 raw,row=pin(B/name);seen.append(row)
d=json.loads((B/'handoff.json').read_bytes());m=json.loads((B/'manifest.json').read_bytes());report=json.loads((B/'report.json').read_bytes())
expected={'handoff.json':('3f0717dd603a04c5b6f97adc7f101d1890a1edc8d2eabd01d751b9f135c6bf54',6557),'manifest.json':('f87a2a920d75084de29099aba801e432be394b98d59f9ca4726e8cfb33f8c1ac',9825),'report.json':('6f9bf341f38f3ef2cedc312e89e1866abca50d8375e055c4801a9ff0a8636410',13844)}
for x in seen:
 e=expected[Path(x['path']).name];assert (x['sha256'],x['bytes'])==e
for x in m['members']:
 raw,row=pin(Path(x['path']));assert (row['sha256'],row['bytes'])==(x['sha256'],x['bytes']);seen.append(row)
for x in report['public_source_basis']:
 raw,row=pin(Path(x['path']));assert (row['sha256'],row['bytes'])==(x['sha256'],x['bytes']);seen.append(row)
for key in ['basis_independent_review_ref','basis_handoff_ref','basis_manifest_ref']:
 x=report[key];raw,row=pin(Path(x['path']));assert (row['sha256'],row['bytes'])==(x['sha256'],x['bytes']);seen.append(row)
old=json.loads(Path(report['basis_manifest_ref']['path']).read_bytes())
for x in old.get('members',old.get('files',[])):
 raw,row=pin(Path(x['path']));assert (row['sha256'],row['bytes'])==(x['sha256'],x['bytes']);seen.append(row)
annex=B/'postseal-original-tool-io.json'
if annex.exists():
 raw,row=pin(annex);seen.append(row)
with (O/'inputs.initial.json').open('xb') as f:f.write((json.dumps(seen,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'new_members':len(m['members']),'old_manifest_keys':list(old),'old_members':len(old.get('members',old.get('files',[]))),'public_source_count':len(report['public_source_basis']),'original_snapshots':len(seen)},ensure_ascii=False))
src=Path(d['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8')
tree=ast.parse(src);ls=src.splitlines()
wanted={'_database','_jsonl','verify_refusal','_public_value','_schema_value','_database_row','_event_schema','_root_pair','_grant_original','_original','_json_original'}
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in wanted:
  print('\nFUNCTION '+n.name)
  for j in range(n.lineno,n.end_lineno+1):print(str(j)+':'+ls[j-1])
print('\nBASIS REVIEW')
print(Path(report['basis_independent_review_ref']['path']).read_text(encoding='utf-8'))

