import pathlib,json,hashlib
P=pathlib.Path;N=P(__file__).resolve().parent
def pin(p):
 p=P(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(P(p).read_bytes())
h=read(N/'HDF.json');m=read(N/'MF.json');refs=read(N/'input-pins.json')
assert pin(N/'MF.json')==h['manifest_ref']
assert all(pin(v['path'])==v for v in m['members'])
assert all(pin(v['path'])==v for v in refs)
o=dict(HDF=pin(N/'HDF.json'),MF=pin(N/'MF.json'),manifest_members=len(m['members']),input_count=len(refs),all_unchanged=True,guard_released=True,formal_acceptance=False)
with (N/'postseal.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(postseal=pin(N/'postseal.json'),**o)))

