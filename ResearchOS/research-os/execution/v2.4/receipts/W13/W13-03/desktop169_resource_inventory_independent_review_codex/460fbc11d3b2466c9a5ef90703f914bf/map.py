from pathlib import Path
import json,hashlib,collections,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W13/W13-03';I=json.loads((O/'inspection.json').read_bytes());REF=[]
def ref(p):
 b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};REF.append(r);return r
def doc(p):ref(p);return json.loads(p.read_bytes())
old=doc(Path(I['full_inputs_ref']['ref']['path']));build=doc(Path(I['build_ref']['ref']['path']));desc=doc(Path(build['descriptor']));compiler=doc(Path(I['compiler_resources_ref']['ref']['path']));runtime=doc(R/'execution/v2.4/receipts/W05/W05-99/cli43_windows_recursive_resource_catalog_codex/ca31885a78a74dff8ac108e20542331e/runtime-v3.json');modules=doc(Path(I['module_ref']['ref']['path']))
def under(row,root):return Path(row['path']).is_relative_to(root)
roots={'electron_dist':R/'apps/desktop/node_modules/electron/dist','web_modules':R/'apps/web/node_modules','Go_root':Path(compiler['GOROOT']),'GOMODCACHE':Path(compiler['GOMODCACHE'])}
tools={x['name']:x for x in desc['tools']};node=Path(tools['node']['path']);roots['Node_directory']=node.parent
summaries={}
for name,root in roots.items():
 rows=[x for x in old if under(x,root)];current=[];aliases=[]
 for base,dirs,files in os.walk(root,followlinks=False):
  for n in list(dirs):
   p=Path(base)/n;st=os.lstat(p)
   if p.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:aliases.append(str(p));dirs.remove(n)
  current.extend(str(Path(base)/n) for n in files)
 oldpaths={str(Path(x['path'])) for x in rows};now=set(current)
 summaries[name]={'root':str(root),'resolved_root':str(root.resolve()),'exists':root.is_dir(),'old_sealed_member_count':len(rows),'old_sealed_bytes':sum(x['bytes'] for x in rows),'current_inventory_regular_filename_count':len(current),'current_membership_only_not_content_rehashed':True,'current_added_vs_old_count':len(now-oldpaths),'current_missing_vs_old_count':len(oldpaths-now),'added_first10':sorted(now-oldpaths)[:10],'missing_first10':sorted(oldpaths-now)[:10],'reparse_subdirectories':aliases,'old_member_refs':rows}
toolrows=[]
for name,row in tools.items():
 p=Path(row['path']);toolrows.append({'name':name,'old_descriptor_row':row,'current_actual_ref':ref(p),'matches_old_sha':ref(p)['sha256']==row['sha256'],'resolved_path':str(p.resolve())})
rtgroups=collections.Counter();rtpaths={str(Path(x['path'])) for x in runtime['files']};cpaths={str(Path(x['path'])) for x in compiler['files']}
for x in runtime['files']:
 p=x['path'].lower();rtgroups['Python' if '/python/' in p.replace('\\','/') or 'pythoncore-' in p else 'Windows' if p.startswith('c:\\windows') or p.startswith('c:/windows') else 'other']+=1
out={'runtime_base_ref':REF[4] if False else ref(R/'execution/v2.4/receipts/W05/W05-99/cli43_windows_recursive_resource_catalog_codex/ca31885a78a74dff8ac108e20542331e/runtime-v3.json'),'runtime_schema':runtime['schema'],'runtime_count':len(runtime['files']),'runtime_group_counts':dict(rtgroups),'runtime_non_python_non_windows':[x for x in runtime['files'] if not ('pythoncore-' in x['path'].lower() or x['path'].lower().replace('\\','/').startswith('c:/windows'))],'compiler_roots':compiler['complete_public_roots'],'compiler_images':compiler['compiler_images'],'compiler_explicit_metadata_files':compiler['explicit_metadata_files'],'tools':toolrows,'resource_roots':summaries,'tool_catalog_membership':{k:{'in_runtime':str(Path(v['path'])) in rtpaths,'in_compiler':str(Path(v['path'])) in cpaths} for k,v in tools.items()},'module_observation_shape':{'keys':list(modules),'observations_type':type(modules['observations']).__name__,'observations_count':len(modules['observations']),'first':modules['observations'][:1] if isinstance(modules['observations'],list) else list(modules['observations'])[:2]},'input_refs':REF}
with (O/'resource-map.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in out.items() if k not in ['resource_roots','input_refs','compiler_explicit_metadata_files','module_observation_shape']},ensure_ascii=False))
print(json.dumps({'roots':{k:{x:y for x,y in v.items() if x!='old_member_refs'} for k,v in summaries.items()},'module_observation_shape':out['module_observation_shape']},ensure_ascii=False))
