from pathlib import Path
import json,hashlib
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+O.name)
def read(p):return json.loads(Path(p).read_bytes())
q=read(N/'root-construction.parameters.desktop58.json');s=read(N/'scope_registration.json');rt=read(s['runtime_resources_ref']['path']);comp=read(s['compiler_resources_ref']['path']);old=read(q['compiler_base_ref']['path']);base=read(q['runtime_base_ref']['path'])['files'];corr=read(q['mandatory_correction_ref']['path'])['missing_Windows_refs']
def canon(r):return {'path':str(Path(r['path']).resolve()),'sha256':r['sha256'],'bytes':r['bytes']}
ck=[]
def test(n,v):ck.append({'check':n,'passed':bool(v)})
rm={r['path']:r for r in rt['files']};changed=[]
for r in base+corr:
 c=canon(r);test('canonical original runtime '+r['path'],rm.get(c['path'])==c)
 if c!=r:changed.append({'original':r,'canonical':c})
keys=['controller_ref','launcher_ref','authorization_verifier_ref','owned_helper_ref','debug_helper_ref','utility_ref']
wanted={canon(x)['path']:canon(x) for x in base+corr+q['metadata_code_refs']+[s[k] for k in keys]}
test('exact canonical runtime union',rm==wanted)
oldm={canon(x)['path']:canon(x) for x in old['files']};newm={x['path']:x for x in comp['files']};test('exact canonical compiler rows',oldm==newm)
cd=[{'original':x,'canonical':canon(x)} for x in old['files'] if x!=canon(x)]
out={'checks':ck,'failed_checks':[x for x in ck if not x['passed']],'runtime_path_only_changes':changed,'compiler_path_only_changes':cd,'compiler_count':len(oldm),'runtime_count':len(wanted),'normalization':'Canonical Path.resolve() projection, preserving exact SHA256 and byte count. No module loading or candidate execution.'}
with (O/'path-projection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'checks':len(ck),'failed':out['failed_checks'],'runtime_changes':len(changed),'compiler_changes':len(cd),'samples':changed[:2]+cd[:2]},ensure_ascii=False))
