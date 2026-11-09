import ast,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';N=P/'cli43_root_binding_preparation_revision_codex/65d40dc010de45a3a06485b0b9a2c37b';O=Path(__file__).parent
reads={};checks=[]
def ck(x,n): checks.append({'check':n,'pass':bool(x)})
def ap(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=ap(p);b=p.read_bytes();k=str(p)
 if k in reads:ck(reads[k]==b,'stable read '+k)
 reads[k]=b;return b
def ref(p):
 p=ap(p);b=read(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def vr(r):
 b=read(r['path']);ck(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'pin '+r['path']);return b
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def put(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
h=doc(N/'handoff.json');mf=doc(N/'manifest.json')
ck(ref(N/'handoff.json')['sha256']=='31a99abd1fdce62aa33f46e4658727ea5e0398b597aeb7a436749f63b6f71085','handoff pin')
ck(ref(N/'manifest.json')['sha256']=='cb98e08960285b0fafaecff858e8e0b44c96d4150313ef2a67a3b1cbb0828357','MF pin')
for x in mf['entries']:vr(x)
oldh=rd(h['old_handoff_ref']);oldmf=rd(h['old_manifest_ref'])
for x in oldmf['entries']:vr(x)
new=vr(h['metadata_module_ref']);oldpath=ap(h['old_handoff_ref']['path']).parent/'metadata_pipeline.v5.proposed.py';old=read(oldpath)
oldline=next(x for x in old.splitlines(keepends=True) if b'    allowed=rows+' in x)
newlines=new.splitlines(keepends=True)
ni=next(i for i,x in enumerate(newlines) if b"    for r in b['metadata_code_refs']: verify(r)" in x)
ck(b'    allowed=rows+' in newlines[ni+1],'only runtime adjacent projection')
inverse=b''.join(newlines[:ni])+oldline+b''.join(newlines[ni+2:])
ck(inverse==old,'whole module exact bytes inverse')
nt=ast.parse(new);ot=ast.parse(old)
nf={x.name:ast.dump(x,include_attributes=False) for x in nt.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))};of={x.name:ast.dump(x,include_attributes=False) for x in ot.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
ck(set(nf)==set(of),'all function names preserved')
for name in of:
 if name!='runtime':ck(nf[name]==of[name],'unchanged full function AST '+name)
oldsha=hashlib.sha256(old).hexdigest();newsha=h['metadata_module_ref']['sha256'];six=[]
for row in h['wrapper_refs']:
 raw=vr(row);ast.parse(raw);p=ap(row['path']);oldraw=read(oldpath.parent/p.name)
 inv=raw.replace(N.name.encode(),oldpath.parent.name.encode()).replace(b'metadata_pipeline.v6.proposed.py',b'metadata_pipeline.v5.proposed.py').replace(newsha.encode(),oldsha.encode())
 ck(inv==oldraw,'wrapper exact path/hash-only inverse '+p.name)
 tree=ast.parse(raw);const=[x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
 ck(str(ap(h['metadata_module_ref']['path'])) in const and newsha in const,'wrapper actual module path/hash pinned '+p.name)
 rr={'path':p.relative_to(R).as_posix(),'sha256':row['sha256'],'bytes':row['bytes']}
 absrow={'path':str(R/rr['path']),'sha256':rr['sha256'],'bytes':rr['bytes']}
 ck(absrow==ref(p),'relative serialized pin and absolute runtime projection both exact '+p.name)
 ck(p.resolve()==p.absolute() and all(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400) for q in [p,*list(p.parents)[:len(p.parts)-len(R.parts)]]),'actual static noalias/reparse '+p.name)
 six.append({'serialized_metadata_ref':rr,'projected_runtime_ref':absrow,'absolute_observer_key':os.path.normcase(str(p)),'matching_key':os.path.normcase(absrow['path'])})
for x in h['unchanged_refs'].values():vr(x)
runner=vr(h['unchanged_refs']['runner']).decode();gate=vr(h['unchanged_refs']['gate']).decode();text=new.decode()
ck("bypath = {os.path.normcase(x['path']): x for x in allowed}" in runner and "bypath.get(os.path.normcase(p)) == row" in runner,'unchanged unknown path/hash reject')
ck("[{'path':str(safe(r['path'])),'sha256':r['sha256'],'bytes':r['bytes']} for r in b['metadata_code_refs']]" in text,'only canonical absolute path projection retains digest/length')
ck("if str(p) in READS: need(raw==READS[str(p)],'read drift')" in text,'reverification reads compared to same cached raw; no unchecked second consume')
ck("pin(output/name)==known[output/name]" in text,'relative pin exact equality retained')
ck(all(x['matching_key']==x['absolute_observer_key'] for x in six),'all six actual module keys match transformed allowlist')
ck(h['future_registration_tuple'] is None and h['future_resources_ref'] is None and h['candidate_templates_executed']==0,'future binding missing cannot be execution permission')
prior=ref(P/'cli43_root_binding_static_independent_review_codex/24e45e3f33844e759faa662405e3d665/review.json')
req=ref(P/'cli43_current_bound_scope_independent_review_codex/6270469239494b17b9fd3d239243238b/review.json')
ck(prior['sha256']=='bafabafe29e493b5113c0d9fbeecc1f608517bb36965238f66959ffe3ed7fda9','original v5 review immutable')
ck(req['sha256']=='213d5c888e689fa910cbbaaa42220083322466d790875407962a7ac3be42623b','original b2 REQUEST immutable')
for p,raw in list(reads.items()):ck(Path(p).read_bytes()==raw,'after stable '+p)
failed=[x for x in checks if not x['pass']]
put('audit.json',{'checks':checks,'failed':failed,'six_wrapper_projection':six,'input_refs':[{'path':p,'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for p,v in reads.items()],'AST_only':True,'target_executions':0})
review={'schema':'researchos.cli43-root-binding-preparation-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES' if failed else 'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED','requested_changes':failed,'handoff_ref':ref(N/'handoff.json'),'candidate_manifest_ref':ref(N/'manifest.json'),'metadata_module_ref':h['metadata_module_ref'],'wrapper_refs':h['wrapper_refs'],'unchanged_refs':h['unchanged_refs'],'audit_ref':ref(O/'audit.json'),'prior_v5_review_ref':prior,'closed_request_ref':req,'verified_scope':['Whole module byte inverse removes only runtime verify-loop and absolute ref projection; all other function ASTs unchanged.','Six wrappers change only module path/hash; relative serialization equals pin() while projected absolute runtime refs match each actual wrapper __file__ key.','verify() rejects raw drift against its existing cache; projection consumes verified ref identity without a new unchecked byte read. Unknown path/hash rejection is unchanged.','Original prepare/run/seal/grant functions, immediate four-canonical CAS and preflight/identity sequence are byte-preserved through inverse.'],'conditions':['Root must stage six wrappers byte-identically in a fresh actual registration namespace, bind new metadata module+all staged wrapper refs with exact relative serialization, and bind actual runtime/compiler/source resources. Recheck those new absolute module identities in future boundscope review.','Actual Root tuple/cut/resources/scope review and emitted registration review remain required; only actual CAS+seal+exclusive grant may authorize the exact two-case execution.','No Go/compiler graph, Windows loader lifecycle, timing fit, cases, source/Main or formal acceptance follows from static AST/byte evidence.'],'actual_registration_executed':False,'actual_target_execution':False,'execution_authorized':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
put('review.json',review)
print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed':len(failed),'files':len(reads),'new_members':len(mf['entries']),'old_members':len(oldmf['entries'])},ensure_ascii=False))
