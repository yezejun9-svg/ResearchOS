from pathlib import Path
import json,hashlib
O=Path(__file__).parent
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
r=read(O/'review.json');m=read(O/'resource-map.json');rt=read(m['runtime_base_ref']['path']);known={Path(x['path']):x for x in rt['files']};rows={}
for x in r['old_module_observations']['observation_refs']:
 for row in read(x['path'])['files']:rows[Path(row['path'])]=row
missing=[x for p,x in rows.items() if p not in known];osmissing=[x for x in missing if x['path'].lower().replace('\\','/').startswith('c:/windows/')];common=[{'old':x,'base':known[p]} for p,x in rows.items() if p in known]
revision={'schema':'researchos.resource-inventory-static-correction.v1','supersedes_interpretation_ref':ref(O/'review.json'),'reason':'Use Windows Path identity when comparing old sampled module spelling to runtime base; exact serialized source refs remain preserved. Web inventory contains native .node addons, not an esbuild.exe; do not invent or require an absent esbuild binary.','canonical_path_module_union':len(rows),'actual_missing_base_count':len(missing),'missing_Windows_count':len(osmissing),'missing_Windows_refs':osmissing,'all_missing_refs':missing,'common_refs':common,'web_native_addons':r['old_web_native_images'],'image_instruction':'Actual selected web tree has rolldown and lightningcss .node native libraries. Put these in files; no esbuild executable was observed in356-member tree. Derive images only from actual reachable .exe files and fixed commands, including cmd.exe for the existing mklink operation.','tool_nonzero':False,'new_failure_origins':[]}
save('correction.json',revision)
save('handoff.corrected.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':'RESOURCE_MAPPING_CLOSED_FOR_ROOT_NEW_CAPTURE_PREPARATION','review_ref':ref(O/'review.json'),'mandatory_correction_ref':ref(O/'correction.json'),'manifest_path':(O/'manifest.corrected.json').as_posix(),'new_failure_origins':[],'actual_execution_authorized':False,'status':'STOPPED'})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.corrected.json'];save('manifest.corrected.json',{'schema':'researchos.public-review-manifest.v1','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({'union':len(rows),'missingWindows':len(osmissing),'refs':{n:ref(O/n) for n in ['correction.json','handoff.corrected.json','manifest.corrected.json']}},ensure_ascii=False))
