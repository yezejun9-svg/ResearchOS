import ast,hashlib,json,copy
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'cli43_root_binding_preparation_revision_codex/9fd9cbeb1343442aa6e34e41f3f2deea'
OLD=P/'cli43_root_binding_preparation_revision_codex/65d40dc010de45a3a06485b0b9a2c37b'
O=Path(__file__).parent;checks=[];reads={}
def ck(ok,label):checks.append({'check':label,'pass':bool(ok)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);raw=p.read_bytes()
 if str(p) in reads:ck(reads[str(p)]==raw,'repeat read unchanged '+str(p))
 reads[str(p)]=raw;return raw
def ref(p):
 p=path(p);raw=read(p);return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def vr(r):
 raw=read(r['path']);ck(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'ref '+r['path']);return raw
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
mf=doc(N/'manifest.complete.json');h=doc(N/'handoff.json');complete=doc(N/'handoff.complete.json')
for name,sha in [('manifest.complete.json','2ef49a19cd9d7f7f711afdb124089e547d56d9eb7775951cf197b5ed31507d15'),('handoff.json','795d8d6ec2a42011cdaa2425d028b2395f3da2f84db60027d625c93895727e2f'),('handoff.complete.json','2a4c955f186a5ebf2010a6d388bc41a822275474af4d9d8010ed1c2f893918ed')]:
 ck(ref(N/name)['sha256']==sha,'pinned '+name)
ck(mf['count']==len(mf['entries'])==23,'actual complete manifest count')
for row in mf['entries']:vr(row)
ck({path(x['path']) for x in mf['entries']}=={x for x in N.iterdir() if x.is_file() and x.name!='manifest.complete.json'},'complete package exact membership excluding self')
for key in ['handoff_ref','manifest_original_ref','actual_preparation_tool_ref']:vr(complete[key])
for row in h['old_manifest_prefixes']:
 m=rd(row['manifest_ref']);ck(len(m['entries'])==row['members'],'old manifest cardinality')
 for r in m['entries']:vr(r)
oldh=rd(h['old_handoff_ref']);newraw=vr(h['metadata_module_ref']);oldraw=vr(oldh['metadata_module_ref'])
ck(h['metadata_module_ref']['sha256']=='095d4f4b86ad0432bd559d2df7221d7f26794eb484f07d313fcc67d3a54f3eed' and len(newraw)==32484,'module fixed pin')
marker=b"    observation['all_observed_inputs_pre_pinned']=True"
lines=newraw.splitlines(keepends=True);selected=[x for x in lines if x.rstrip(b'\r\n')==marker]
ck(len(selected)==1 and b''.join(x for x in lines if x.rstrip(b'\r\n')!=marker)==oldraw,'whole byte inverse single marker line only')
newtree=ast.parse(newraw);oldtree=ast.parse(oldraw)
nf={x.name:x for x in newtree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))};of={x.name:x for x in oldtree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
ck(nf.keys()==of.keys(),'function roster unchanged')
for name in nf:
 if name!='runtime':ck(ast.dump(nf[name])==ast.dump(of[name]),'unchanged function AST '+name)
runtime=nf['runtime'];dumpmarker=ast.dump(ast.parse(marker.decode().strip()).body[0])
indices=[i for i,x in enumerate(runtime.body) if ast.dump(x)==dumpmarker]
ck(len(indices)==1,'runtime marker is direct unconditional-on-success statement')
if len(indices)==1:
 i=indices[0];prev=runtime.body[i-1];nxt=runtime.body[i+1]
 ck(isinstance(prev,ast.Assign) and ast.unparse(prev)=='observation = util.module_observation(allowed, helper)','strict call immediately precedes marker')
 ck(isinstance(nxt,ast.Return) and 'save(' in ast.unparse(nxt),'save immediately follows marker')
 rt=copy.deepcopy(runtime);rt.body.pop(i);ck(ast.dump(rt)==ast.dump(of['runtime']),'runtime AST inverse exact')
 ck(not any(isinstance(x,(ast.Try,ast.TryStar)) for x in ast.walk(runtime)),'no local exception swallowing can reach success marker')
oldwr={Path(r['path']).name:r for r in oldh['wrapper_refs']};ck(len(h['wrapper_refs'])==6,'six wrappers')
for r in h['wrapper_refs']:
 raw=vr(r);tree=ast.parse(raw);prior=vr(oldwr[Path(r['path']).name])
 inv=raw.replace(N.name.encode(),OLD.name.encode()).replace(b'metadata_pipeline.v7.proposed.py',b'metadata_pipeline.v6.proposed.py').replace(h['metadata_module_ref']['sha256'].encode(),oldh['metadata_module_ref']['sha256'].encode())
 ck(inv==prior,'wrapper whole byte inverse '+Path(r['path']).name)
 constants=[x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
 ck(str(path(h['metadata_module_ref']['path'])) in constants and h['metadata_module_ref']['sha256'] in constants,'wrapper literal module path and SHA '+Path(r['path']).name)
for name,r in h['unchanged_refs'].items():
 vr(r);ck(r==oldh['unchanged_refs'][name],'unchanged input exact dictionary '+name)
chain=rd(h['producer_consumer_review_ref'])
for r in chain['peer_refs']:vr(r)
gate=vr(h['unchanged_refs']['gate']).decode();runner=vr(h['unchanged_refs']['runner']).decode();runnerast=ast.parse(runner)
observe=next(x for x in runnerast.body if isinstance(x,ast.FunctionDef) and x.name=='module_observation')
observetext=ast.get_source_segment(runner,observe)
ck("observed['all_observed_inputs_pre_pinned'] is True" in gate,'consumer exact required marker remains')
ck("point_in_time_only" in observetext and "Python_lifecycle_proof" in observetext,'original point-time/non-lifecycle output retained')
ck("for r in b['metadata_code_refs']: verify(r)" in newraw.decode() and "'path':str(safe(r['path']))" in newraw.decode(),'v6 verified ABS runtime allowlist retained')
instructions=rd(h['binding_instructions_ref'])
ck(instructions['future_registration_tuple'] is None and instructions['future_run_uuid'] is None and instructions['future_origin_cut_ref'] is None,'no future binding guessed')
ck(h['candidate_templates_executed']==0 and h['source_acceptance'] is False and h['formal_increment']==0,'reported preparation only')
save('source-extracts.json',{'runtime':ast.get_source_segment(newraw.decode(),runtime),'module_observation':observetext,'gate_marker_lines':[{'line':i+1,'text':x} for i,x in enumerate(gate.splitlines()) if 'all_observed_inputs_pre_pinned' in x],'semantics':'A raising strict observation prevents both marker and save. True derives only successful point-time pre-pin validation, not lifetime closure.'})
for p,raw in list(reads.items()):ck(Path(p).read_bytes()==raw,'after stable '+p)
failed=[x for x in checks if not x['pass']]
save('audit.json',{'checks':checks,'failed_checks':failed,'input_refs':[{'path':p,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for p,raw in reads.items()],'candidate_import_or_execution':False,'new_failure_origins':[]})
review={'schema':'researchos.cli43-root-binding-preparation-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED' if not failed else 'REQUEST_CHANGES','requested_changes':failed,'module_ref':h['metadata_module_ref'],'wrapper_refs':h['wrapper_refs'],'candidate_handoff_ref':ref(N/'handoff.complete.json'),'candidate_manifest_ref':ref(N/'manifest.complete.json'),'audit_ref':ref(O/'audit.json'),'source_extracts_ref':ref(O/'source-extracts.json'),'reused_complete_chain_review_refs':chain['peer_refs'],'finding_closed':'CLI43-BS-OBS-02','basis':['Byte-exact inverse removes only the successful-observation marker assignment.','All other module function ASTs match v6; six wrappers invert with only module filename/path/SHA substitutions.','Strict observation must return successfully before True is derived and saved; no catch can convert an observation error into success.','Unchanged gate still rejects missing marker, unknown paths/hash/bytes; point-time and non-lifecycle facts remain.'],'future_root_conditions':['New actual Root scope/binding and independent review must pin v7 module and all six staged wrappers.','Preserve exact ROOT-relative scope ref through prepare, CP and grant; do not reuse ABS-dictionary input.','Actual runtime catalogue must replace old metadata pins with the new six staged wrappers, v7 module and original binder as eight actual ABS refs; old1250 catalog is not reusable unchanged.','Actual independently reviewed registration/CAS/seal and unique grant are still required before the same two cases.'],'actual_template_execution':False,'actual_registration_executed':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
save('review.json',review)
print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed_checks':failed,'input_files':len(reads),'target_execution':False},ensure_ascii=False))
