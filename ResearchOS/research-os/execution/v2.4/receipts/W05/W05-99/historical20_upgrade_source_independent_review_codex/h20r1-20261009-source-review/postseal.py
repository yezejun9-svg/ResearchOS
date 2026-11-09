import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
def pin(p):
 p=pathlib.Path(p);r=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(r).hexdigest(),'bytes':len(r)}
def read(n):return json.loads((N/n).read_text(encoding='utf-8'))
h=read('HDF.json');m=read('MF.json');inputs=read('input-pins.json')
refs=m['members']+[h['manifest_ref']]+inputs
bad=[r['path'] for r in refs if pin(r['path'])!=r]
obj={'status':'POST_SEAL_VERIFIED' if not bad else 'DRIFT','HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members_verified':len(m['members']),'inputs_verified':len(inputs),'bad':bad,'seal_original_io':pin(N/'seal.original-tool-io.json'),'guard_released':True,'STOP':True}
with (N/'postseal.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'postseal':pin(N/'postseal.json'),'status':obj['status']},ensure_ascii=False))
raise SystemExit(0 if not bad else 1)

