from pathlib import Path
import json,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820'
d=json.loads((N/'literal-staging.actual.json').read_bytes());q=json.loads(Path(d['request_ref']['path']).read_bytes());old=json.loads(Path(d['old_request_ref']['path']).read_bytes())
oldid='1c4ea6999d4d4437a0202c4e81ce581b';newid='dc00ad52f46c49acacc8058a58500820'
norm=json.loads(json.dumps(q,ensure_ascii=False).replace(newid,oldid))
diff=[]
def walk(a,b,p):
 if type(a)!=type(b):diff.append({'path':p,'old':a,'new':b});return
 if isinstance(a,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:diff.append({'path':p+'/'+k,'old':a.get(k),'new':b.get(k)})
   else:walk(a[k],b[k],p+'/'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):diff.append({'path':p,'old_length':len(a),'new_length':len(b)})
  for i,(v,w) in enumerate(zip(a,b)):walk(v,w,p+'/'+str(i))
 elif a!=b:diff.append({'path':p,'old':a,'new':b})
walk(old,norm,'')
summary={k:({'length':len(v),'first':v[:1]} if isinstance(v,list) and len(v)>5 else v) for k,v in q.items() if k!='pending_origin_refs'}
out={'schema':'researchos.literal-inputs-delta-inspection.v1','request_keys':list(q),'normalized_uuid_diffs':diff,'request_without_full_origin_list':summary,'staging':d}
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(out,ensure_ascii=False))
