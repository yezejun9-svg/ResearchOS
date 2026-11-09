from pathlib import Path
import json
O=Path(__file__).parent;d=json.loads((O/'inspection.json').read_bytes());c=json.loads(Path(d['completion_ref']['path']).read_bytes());q=json.loads(Path(c['closure_request_ref']['path']).read_bytes())
out={'completion_direct_refs':{k:v for k,v in c.items() if k.endswith('_ref') or k=='authorization_canonical_copy_refs'},'request_path':c['closure_request_ref'],'request':q,'member_refs':json.loads(Path(d['manifest_ref']['path']).read_bytes())['members']}
with (O/'contract.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'completion_direct_refs':out['completion_direct_refs'],'request':q},ensure_ascii=False))
