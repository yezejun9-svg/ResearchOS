from pathlib import Path
import json,re,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-'+O.name)
ob=json.loads((N/'tool-observations.sixth-construction.closed.original.json').read_bytes());rows=[]
for rec in ob['records']:
 if rec['kind'] not in ('capture-poll3','scope-poll3','scope-precall-failed'):continue
 def walk(x):
  if isinstance(x,dict):
   if 'chunk_id' in x and 'output' in x:rows.append({'kind':rec['kind'],'chunk_id':x['chunk_id'],'exit_code':x.get('exit_code'),'markers':re.findall('ACTUAL_[A-Z_]*EXIT[=:] *(-?[0-9]+)',x['output']),'tail':x['output'][-600:]})
   for z in x.values():walk(z)
  elif isinstance(x,list):
   for z in x:walk(z)
 walk(rec['result'])
with (O/'tool-markers.supplement.json').open('xb') as f:f.write((json.dumps({'rows':rows,'reason':'Correct literal regex for printed ACTUAL exit markers; original raw and prior summary preserved.'},ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(rows,ensure_ascii=False))

