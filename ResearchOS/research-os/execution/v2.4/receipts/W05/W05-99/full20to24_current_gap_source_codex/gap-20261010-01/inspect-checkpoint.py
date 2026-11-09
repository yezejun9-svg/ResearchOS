import json,re,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
d=json.loads((R/'execution/v2.4/checkpoint.json').read_bytes())
out=[]
def walk(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():
   kp=p+'/'+k
   if re.search(r'main24|main23|schema24|history20|historical20|full20|q3',k,re.I):out.append({'key':kp,'value':x})
   elif isinstance(x,(dict,list)) and not re.search(r'fail|diagnostic|mechanical|original',k,re.I):walk(x,kp)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,p+'/'+str(i))
walk(d)
(O/'checkpoint-selected.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for row in out:print(json.dumps(row,ensure_ascii=False)[:3200])

