from pathlib import Path
import hashlib
import json
ROOT=Path('D:/作品集/ResearchOS/research-os')
REG=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-dc4fe023ed714e74b8d3692b504cf55d'
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_current_bound_scope_supporting_audit_codex/3896a25682e14422a41c9cfd2dac61e1")
def read(path):
    raw=path.read_bytes()
    return json.loads(raw),{'path':path.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def shape(value, depth=0):
    if isinstance(value,dict):
        return {'type':'dict','len':len(value),'keys':list(value),'children':{k:shape(v,depth+1) for k,v in value.items()} if depth<1 else None}
    if isinstance(value,list):
        return {'type':'list','len':len(value),'sample_type':type(value[0]).__name__ if value else None,'sample_keys':list(value[0]) if value and isinstance(value[0],dict) else None}
    return {'type':type(value).__name__,'value':value}
s,sr=read(REG/'scope_registration.json')
b,br=read(REG/'binding.pre-review.json')
q,qr=read(REG/'root-inputs.desktop58.pre-review.json')
cat,cr=read(Path(s['resource_catalog_ref']['path']))
compiler,cpr=read(Path(s['compiler_resources_ref']['path']))
runtime,rr=read(Path(s['runtime_resources_ref']['path']))
source,sour=read(Path(s['source_catalog_ref']['path']))
membership,mr=read(Path(cat['root_membership_ref']['path']))
aliases,ar=read(Path(s['alias_roster_ref']['path']))
edits,er=read(Path(s['alias_edits_ref']['path']))
qual,quar=read(Path(s['current58_CLI2_qualification_ref']['path']))
data={
    'scope_ref':sr,'binding_ref':br,'root_inputs_ref':qr,
    'scope':s,'binding':b,'root_inputs':q,
    'catalog_ref':cr,'compiler_ref':cpr,'runtime_ref':rr,'source_ref':sour,'membership_ref':mr,
    'catalog_keys':list(cat),'compiler_keys':list(compiler),'runtime_keys':list(runtime),
    'compiler_roots':[{'path':item['path'],'file_count':len(item['files']),'keys':list(item)} for item in compiler['complete_public_roots']],
    'compiler_explicit_metadata_count':len(compiler['explicit_metadata_files']),
    'runtime_overlay_shapes':shape(runtime['desktop58_overlay']),
    'root_membership_shapes':shape(membership),
    'aliases':aliases,'alias_edits':edits,'qualification':qual,
    'catalog_tools':cat['tools'],'catalog_images':cat['images'],
    'runtime_added_static_candidates':runtime['added_static_candidate_files'],
    'runtime_candidate_evidence_ref':runtime['candidate_evidence_ref'],
}
for name in ['root-allocation.actual.json','literal-inputs.original.json','root-construction.parameters.desktop58.json','root-construction.audit.json','tool-observations.fifth-construction.closed.original.json','RESUME.fifth-construction.closed.scope-review-pending.json']:
    value,pin=read(REG/name)
    data[name]={'ref':pin,'shape':shape(value)}
p=BASE/'inspection.json'
with p.open('xb') as stream:stream.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
raw=p.read_bytes()
print(json.dumps({
    'inspection_ref':{'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},
    'compiler_roots':data['compiler_roots'],
    'runtime_overlay_keys':list(runtime['desktop58_overlay']),
    'membership_children':data['root_membership_shapes']['children']['membership'],
    'alias_roster_shape':shape(aliases),
    'alias_edits_shape':shape(edits),
    'qualification_keys':list(qual),
},ensure_ascii=False))
