import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
def pin(p):
 p=pathlib.Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(pathlib.Path(p).read_bytes())
h=read(N/'HDF.json');m=read(N/'MF.json')
assert all(pin(v['path'])==v for v in m['members'])
assert pin(N/'MF.json')==h['manifest_ref']
refs=read(N/'input-pins.json');assert all(pin(v['path'])==v for v in refs)
out=dict(HDF=pin(N/'HDF.json'),MF=pin(N/'MF.json'),manifest_members=len(m['members']),review_inputs=len(refs),all_unchanged=True,source_guard_closed=True,formal_acceptance=False)
with (N/'postseal.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(postseal=pin(N/'postseal.json'),**out)))

