import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
def pin(p):
 p=pathlib.Path(p);r=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(r).hexdigest(),'bytes':len(r)}
def read(n): return json.loads((N/n).read_text(encoding='utf-8'))
h=read('HDF.json');m=read('MF.json'); bad=[]
for ref in m['members']+[h['manifest_ref']]+read('input-pins.json'):
 a=pin(ref['path'])
 if a['sha256']!=ref['sha256'] or a['bytes']!=ref['bytes']: bad.append(a)
obj={'status':'POST_SEAL_VERIFIED' if not bad else 'DRIFT','HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members_verified':len(m['members']),'source_pins_verified':len(read('input-pins.json')),'bad':bad,'seal_original_io':pin(N/'seal.original-tool-io.json'),'guard_released':True,'STOP':True}
with (N/'postseal.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'postseal':pin(N/'postseal.json'),'status':obj['status']},ensure_ascii=False))
raise SystemExit(0 if not bad else 1)

