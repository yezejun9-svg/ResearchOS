import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli58-fresh-held2-r334-56b244cd06264dc7b95d381fc3297d61';O=Path(__file__).parent
def load(p):return json.loads(Path(p).read_bytes())
def get(r):return load(Path(r['path']) if Path(r['path']).is_absolute() else R/r['path'])
s=load(N/'scope_registration.json');b=load(N/'binding.pre-review.json');rt=get(s['runtime_resources_ref']);old=get(get(s['draft_history']['old_scope_ref'])['runtime_resources_ref'])
def brief(v):
    if isinstance(v,dict):return {'type':'dict','keys':list(v),'containers':{k:len(x) for k,x in v.items() if isinstance(x,(list,dict))}}
    return {'type':type(v).__name__,'length':len(v)}
result={'runtime':brief(rt),'oldruntime':brief(old),'compiler':brief(get(s['compiler_resources_ref'])),'catalog':brief(get(s['catalog_ref'])),'authority':get(s['current43_authority_ref']),'cut':brief(get(b['origin_cut_ref'])),'source_inputs':brief(get(b['source_inputs_ref'])),'instrumentation':brief(get(s['instrumentation_ref']))}
if 'files' in rt and 'files' in old:
    newmap={x['path']:x for x in rt['files']};oldmap={x['path']:x for x in old['files']}
    result['removed_runtime_rows']=[x for p,x in oldmap.items() if p not in newmap]
    result['new_runtime_rows']=[x for p,x in newmap.items() if p not in oldmap]
    result['same_path_changed']=[p for p,x in newmap.items() if p in oldmap and x!=oldmap[p]]
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(result,ensure_ascii=False))
