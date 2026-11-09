from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os'); B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e'
V=B/'official_test2json_resource_independent_review_codex/fd737b147f004cb4be2e57a0f85d9c4e'
V.mkdir(parents=True,exist_ok=False)
def pin(p):
 b=p.read_bytes(); return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def key(p): return str(Path(p).resolve()).casefold()
def load(name): return json.loads((Q/name).read_text(encoding='utf-8'))
refs={}; mismatches=[]
def verify(ref):
 p=Path(ref['path']); k=key(p)
 if k in refs:
  actual=refs[k]
 else:
  if not p.is_file(): mismatches.append({'missing':ref}); return
  actual=pin(p); refs[k]=actual
 if actual['sha256']!=ref['sha256'] or actual['bytes']!=ref['bytes']:mismatches.append({'expected':ref,'actual':actual})
def walk(obj):
 if isinstance(obj,dict):
  if all(k in obj for k in ['path','sha256','bytes']):verify(obj)
  else:
   for value in obj.values():walk(value)
 elif isinstance(obj,list):
  for value in obj:walk(value)
closed=load('resource-build.closed.json'); inventory=load('selected-official-compiler-inputs.json')
verify({'path':str(Q/'resource-build.closed.json'),'sha256':'bf9a9df9448be2df121455460378d895441a244684ca053bbf288f92276dbf01','bytes':24186})
for p in Q.iterdir():
 if p.is_file():
  refs[key(p)]=pin(p)
  if p.suffix=='.json':walk(json.loads(p.read_text(encoding='utf-8')))
raw=(Q/'official-stdlib-tool-selected-inputs.stdout.raw').read_text(encoding='utf-8'); decoder=json.JSONDecoder(); pos=0; packages=[]
while pos<len(raw):
 while pos<len(raw) and raw[pos].isspace():pos+=1
 if pos==len(raw):break
 p,pos=decoder.raw_decode(raw,pos);packages.append(p)
selected={}; embeds={}; nonstandard=[]
for pkg in packages:
 if not pkg.get('Standard') or not pkg.get('Goroot'):nonstandard.append(pkg['ImportPath'])
 for field in inventory['selected_file_fields']:
  for name in pkg.get(field,[]):
   p=Path(name)
   if not p.is_absolute():p=Path(pkg['Dir'])/p
   selected[key(p)]=pin(p)
   if field=='EmbedFiles':embeds[key(p)]=pin(p)
invpaths={key(ref['path']):ref for ref in inventory['build_inputs']}
inventory_same=set(selected)==set(invpaths) and all(selected[k]['sha256']==invpaths[k]['sha256'] and selected[k]['bytes']==invpaths[k]['bytes'] for k in selected)
guards={}
for stem,expected in [('base',closed['base_input_refs']),('selected',inventory['build_inputs']+[closed['compiler_inventory_ref']]),('binary',[closed['binary_ref']])]:
 g=load(stem+'-source-guard.cleanup.actual.json');entries=g['entries']
 guards[stem]={'entry_count':len(entries),'expected_count':len(expected),'exact_ref_set':{(key(r['path']),r['sha256'],r['bytes']) for r in entries}=={(key(r['path']),r['sha256'],r['bytes']) for r in expected},'every_entry_verified_closed':all(e.get('verified') and e.get('final_path_match') and e.get('closed') for e in entries),'verification':g['verification'],'closed':g['closed'],'retained_handles_count':g['retained_handles_count'],'errors':g['errors'],'failure':g['failure'],'share_mode':g['share_mode']}
jobs=[]
for label in ['official-stdlib-tool-selected-inputs','official-test2json-build']:
 inv=load(label+'.invocation.json'); res=inv['result'];j=res['job_cleanup']
 jobs.append({'label':label,'argv':inv['argv'],'cwd':inv['cwd'],'environment':inv['public_environment'],'actual_native_exit':inv['actual_native_exit'],'result_exit':res['actual_exit'],'timed_out':res['timed_out'],'error':res['error'],'resumed':res['resumed'],'owned_child_pid':res['owned_child_pid'],'creation_time_100ns':res['creation_time_100ns'],'job_cleanup':j,'stdout_bytes':inv['stdout_ref']['bytes'],'stderr_bytes':inv['stderr_ref']['bytes']})
io=load('original-tool-io.json')
out={'scope':'TOOL_COMPILATION_COMPONENT','input_ref_count':len(refs),'hash_mismatches':mismatches,'package_count':len(packages),'reported_package_count':inventory['package_count'],'packages_exact':inventory['packages']==[p['ImportPath'] for p in packages],'nonstandard_or_non_goroot_packages':nonstandard,'package_errors':[p['ImportPath'] for p in packages if p.get('Error') or p.get('DepsErrors')],'selected_input_count':len(selected),'inventory_exact_raw_selection':inventory_same,'actual_embed_count':len(embeds),'guards':guards,'jobs':jobs,'original_outer_exit':io['result']['exit_code'],'original_marked_python_exit0':'ROOT_PYTHON_EXIT=0' in io['result']['output'],'binary':pin(Path(closed['binary_ref']['path'])),'target_binary_executions':closed['tool_executions'],'provider_requests':closed['provider_requests'],'private_key_reads':closed['private_key_reads'],'original_trial_DB_writes':closed['original_trial_DB_writes'],'limitations':['Review reads existing actual build receipts; does not execute Go or test2json.','Shared GOCACHE may reuse compiled artifacts; this is successful official package build, not proof every dependency was freshly recompiled.','SourceReadGuard was closed after build; future use requires fresh exact binary hash verification/guard.','No product fixture or child test JSONL yet.'],'formal_acceptance':False}
for name,obj in [('checks.json',out),('input-refs.json',list(refs.values()))]:
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
