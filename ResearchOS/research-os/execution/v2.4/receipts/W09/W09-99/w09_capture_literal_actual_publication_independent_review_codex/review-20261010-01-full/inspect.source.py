from pathlib import Path
import hashlib,json
R=Path(r'D:\作品集\ResearchOS\research-os')
D=Path(__file__).resolve().parent
C=R/'execution/v2.4/receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01/capture-7d7d176970554ad3b9cdb72bc3b1ce8a'
proposal=json.loads((C/'result.json').read_bytes())
origin=(R/proposal['origin_payload_ref']['path']).read_bytes()
rows=[json.loads(x) for x in origin.splitlines()]
def shape(x):
    if type(x) is dict:
        return {'keys':list(x),'scalars':{k:v for k,v in x.items() if v is None or type(v) in (str,int,bool)},'nested':{k:shape(v) for k,v in x.items() if type(v) in (dict,list)}}
    if type(x) is list:return [shape(v) for v in x]
    return x
facts={'origin_rows':[shape(x) for x in rows], 'live_index_exists':(R/proposal['fixed_path']).is_file(),'new_origin_exists':(R/proposal['origin_fixed_path']).exists(),'new_capture_exists':(R/proposal['capture_fixed_path']).exists()}
with (D/'input-shapes.json').open('xb') as f:f.write((json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode())
for row in facts['origin_rows']:
    row.get('nested',{}).get('payload',{}).get('nested',{}).pop('content',None)
print(json.dumps(facts,ensure_ascii=False))
