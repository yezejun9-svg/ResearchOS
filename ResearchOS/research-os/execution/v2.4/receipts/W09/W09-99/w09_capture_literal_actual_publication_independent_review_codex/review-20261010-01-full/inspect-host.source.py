from pathlib import Path
import json
R=Path(r'D:\作品集\ResearchOS\research-os')
D=Path(__file__).resolve().parent
P=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.capture-literal-actual-repair01.original.raw.jsonl'
rows=[json.loads(x) for x in P.read_bytes().splitlines()]
facts=[]
for row in rows[1:]:
    p=row['payload'];facts.append({'row_type':row['type'],'timestamp':row['timestamp'],'payload_keys':list(p),'payload_type':p.get('type'),'call_id':p.get('call_id'),'name':p.get('name'),'arguments':p.get('input',p.get('arguments')),'output':p.get('output')})
with (D/'host-shapes.json').open('xb') as f:f.write((json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(facts,ensure_ascii=False))
