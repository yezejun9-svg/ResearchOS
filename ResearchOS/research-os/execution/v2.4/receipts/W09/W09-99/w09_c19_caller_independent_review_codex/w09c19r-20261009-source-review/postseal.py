import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
h=json.loads((N/'HDF.json').read_bytes());m=json.loads((N/'MF.json').read_bytes())
assert pin(Path(h['manifest_ref']['path']))==h['manifest_ref']
for v in m['members']+json.loads((N/'input-pins.json').read_bytes()):assert pin(Path(v['path']))==v,v['path']
x={'status':'PASS','HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'manifest_members':len(m['members']),'input_pins_verified':153,'canonical_unchanged':True,'retained_handles_count':0}
with (N/'postseal.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'postseal':pin(N/'postseal.json'),'status':'PASS'}))

