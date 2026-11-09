from pathlib import Path
import json,hashlib,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009';Q=S/'public21-current-resource-root-20261010-02';M=B/'integration_codex/public21-runtime-3260013e7e24465cbce754a9c534262d'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def documents(v):
 if type(v) is dict:
  yield v
  for x in v.values():yield from documents(x)
 elif type(v) is list:
  for x in v:yield from documents(x)
 elif type(v) is str:
  try:yield from documents(json.loads(v))
  except (ValueError,TypeError):pass
def shape(v):
 if type(v) is dict:return {'keys':list(v),'scalars':{k:x for k,x in v.items() if x is None or type(x) in (str,int,bool,float)}}
 if type(v) is list:return {'length':len(v),'first':shape(v[0]) if v else None}
 return v
out={}
for name,file in [('scope','qualification-scope.root.json'),('request','runtime-prepare.request.root.json')]:out[name]=read(Q/file)
for name,file in [('scope_audit','w09.public21-caller02-runtime-scope-issued.actual-audit.root.json'),('prepare_audit','w09.public21-caller02-runtime-prepare-completed.actual-audit.root.json')]:
 a=read(S/file);rows=[json.loads(x) for x in Path(a['original_capture_ref']['path']).read_bytes().splitlines()];out[name]=a
 out[name+'_rows']=[shape(x) for x in rows]
 out[name+'_call']=rows[1]['payload']
 out[name+'_hosts']=[x for x in documents(rows[2]['payload']['output']) if 'chunk_id' in x]
manifest=read(M/'runtime-manifest.root.json');guard=read(M/'prepare.guard.closed.json')
out['manifest_metadata']={k:v for k,v in manifest.items() if k!='resource_refs'};out['manifest_ref']=pin(M/'runtime-manifest.root.json');out['resource_count']=len(manifest['resource_refs']);out['prepare_guard_ref']=pin(M/'prepare.guard.closed.json');out['guard_shape']=shape(guard);out['guard_entry_shape']=shape(guard.get('entries',[]))
leaf=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-02';out['leaf_hdf']=read(leaf/'HDF.json');out['leaf_contract_shape']=shape(read(leaf/'contract.json'));out['programme']=read(S/'old21.programme.qualification.bound.actual.root.json')
for name in ('SOURCE_REVIEW_WITNESS.witness.root.json','RUNNER_SOURCE_REVIEW_WITNESS.witness.root.json','RUNTIME_MANIFEST_PREREQUISITES.actual-root-binding.root.json'):out[name]=read(Q/name)
print(json.dumps(out,ensure_ascii=False,allow_nan=False))
