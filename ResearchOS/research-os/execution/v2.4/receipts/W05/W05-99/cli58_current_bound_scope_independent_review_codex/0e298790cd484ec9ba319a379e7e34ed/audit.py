import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).parent; P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed'
OLD=P/'integration_codex/cli58-fresh-held2-r334-56b244cd06264dc7b95d381fc3297d61'
Q=P/'cli58_current_bound_scope_independent_review_codex/56b244cd06264dc7b95d381fc3297d61'
C=[]; REFS={}
def ck(n,v): C.append({'check':n,'passed':bool(v)})
def path(p):
 p=Path(p); return p if p.is_absolute() else R/p
def ref(p):
 p=path(p); b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):
 p=path(p); REFS[str(p)]=ref(p); return json.loads(p.read_bytes())
def pin(r):
 p=path(r['path']); a=ref(p); REFS[str(p)]=a; ck('pin '+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']); return p.read_bytes()
def rd(r): return json.loads(pin(r))
def refs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys(): yield v
  else:
   for x in v.values(): yield from refs(x)
 elif isinstance(v,list):
  for x in v: yield from refs(x)
def save(n,v):
 with (O/n).open('xb') as f: f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
mf=load(N/'bound-scope.pre-review.manifest.json')
ck('new MF expected',ref(N/'bound-scope.pre-review.manifest.json')['sha256']=='058ef95f32e84a663f4216f9fe271f700bbf9c626d6843a91861c6f272bf2877')
ck('23 members self excluded',mf['count']==len(mf['entries'])==23 and mf['self_excluded'] is True)
for r in mf['entries']: pin(r)
oldmf=load(Q/'manifest.json')
for r in oldmf['entries']: pin(r)
oldreview=load(Q/'review.json'); oldaudit=load(Q/'audit.json')
s=load(N/'scope_registration.json'); b=load(N/'binding.pre-review.json'); old=load(OLD/'scope_registration.json'); ob=load(OLD/'binding.pre-review.json'); params=load(N/'root-construction.parameters.json')
ck('scope exact SHA',ref(N/'scope_registration.json')['sha256']=='459f00078d742e754631294d17210329280c2e1fec0cf7925b94fb4333c3bc84')
for v in [s,b,params]:
 for r in refs(v): pin(r)
allowed={'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root','registration_namespace','controller_review_path','runtime_resources_ref'}
delta={k:{'old':old.get(k),'new':s.get(k)} for k in set(old)|set(s) if old.get(k)!=s.get(k)}
ck('scope only exact resource/namespace changes',set(delta)==allowed and set(old)==set(s))
ck('all unchanged source/caps/authority code fields',all(old[k]==s[k] for k in old if k not in allowed))
for name in ['construct_root_inputs.py','canonical-before.json','failure-origins.cut.json','source-inputs.json','scope.template.current58.actual-catalog.json','scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py']:
 ck('unchanged bytes '+name,(N/name).read_bytes()==(OLD/name).read_bytes())
ck('before/after',s['expected_before_registration']==b['before']==[333,161,524] and s['expected_registration']==b['after']==[334,162,532])
ck('review exact path unbound ref',path(s['controller_review_path'])==O/'review.json' and b['controller_review_ref'] is None)
for k in allowed-{'runtime_resources_ref'}:
 ck('binding scope '+k,b[k]==s[k])
ck('binding runtime',b['runtime_resources_ref']==s['runtime_resources_ref'])
for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']:
 ck('fresh absent '+k,not path(s[k]).exists() and path(s[k]).name.endswith(s['run_uuid']))
for name in ['binding.json','prepare.started.json','prepared_refs.json']: ck('not prepared '+name,not (N/name).exists())
cb=rd(b['canonical_before_ref']); docs=[]
for row in cb['entries']:
 raw=pin(row['ref']); ck('live4 '+row['canonical_path'],path(row['canonical_path']).read_bytes()==raw); docs.append(json.loads(raw))
cp,ow=docs[:2]; ck('current tuple/head',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'] and cp['head']==s['source_commit'])
cut=rd(b['origin_cut_ref']); ck('cut8 unchanged',cut==load(OLD/'failure-origins.cut.json') and len(cut['origins'])==8)
seen=set(); oldkeys={x.get('evidence_ref',{}).get('sha256') for x in cp['failure_counters']}
for x in cut['origins']:
 r=x['evidence_ref']; ck('full opaque origin '+r['sha256'],rd(r)==x['original_payload'] and x['counter_reset'] is False); ck('unique origin '+r['sha256'],r['sha256'] not in seen|oldkeys); seen.add(r['sha256'])
base=rd(params['runtime_base_ref']); rt=rd(s['runtime_resources_ref']); compiler=rd(s['compiler_resources_ref'])
ck('original1242 pinned base',params['runtime_base_ref']['sha256']=='98b5efb1e3bfa8ab5c64a7ed3280b62ca6c856cc562e1d5ea59f89caca28d6cf' and len(base['files'])==1242)
norm=lambda p:str(path(p)).casefold()
rows={norm(r['path']):r for r in rt['files']}; br={norm(r['path']):r for r in base['files']}
ck('1250 unique',len(rows)==len(rt['files'])==1250)
ck('base rows verbatim preserved',all(rows.get(k)==v for k,v in br.items()))
meta=[]
for i,r in enumerate(b['metadata_code_refs']):
 raw=pin(r); ast.parse(raw); projected={**r,'path':str(path(r['path']))};meta.append(projected)
 ck('relative prepare serialized pin '+str(i),r['path']==path(r['path']).relative_to(R).as_posix())
 ck('metadata ABS actual module row '+str(i),rows.get(norm(r['path']))==projected)
 ck('metadata unchanged SHA bytes '+str(i),(r['sha256'],r['bytes'])==(ob['metadata_code_refs'][i]['sha256'],ob['metadata_code_refs'][i]['bytes']))
 if i<6: ck('six wrapper actual new NS '+str(i),path(r['path']).parent==N)
ck('exact eight overlay only',len(meta)==8 and set(rows)-set(br)=={norm(r['path']) for r in meta} and not(set(br)&{norm(r['path']) for r in meta}))
module=path(b['metadata_code_refs'][-1]['path']); raw=module.read_bytes()
ck('module expected',hashlib.sha256(raw).hexdigest()=='4a5913346f0fa83f65824861077a05087de9244530be2754f138063821f7aeb4')
for r in b['metadata_code_refs'][:6]: ck('wrapper module pin '+r['path'],repr(str(module)).encode() in path(r['path']).read_bytes() and b['metadata_code_refs'][-1]['sha256'].encode() in path(r['path']).read_bytes())
obs=load(Q/'observed-resource-comparison.json'); missingrefs={x['omitted_ref']['path']:x['omitted_ref'] for x in obs['missing_observed_records']}
for p,r in missingrefs.items(): pin(r); ck('previously observed DLL exact approved '+p,rows.get(norm(p))==r)
ck('three observed omissions resolved',len(missingrefs)==3)
ck('compiler preserved',s['compiler_resources_ref']==old['compiler_resources_ref'] and len(compiler['files'])==22138 and len(compiler['compiler_images'])==9)
head=(R/'.git/HEAD').read_text().strip(); current=(R/'.git'/head[5:]).read_text().strip() if head.startswith('ref: ') else head
ck('Main direct head',current==s['source_commit'])
ck('source/static limits unchanged',s['source_acceptance'] is False and s['formal_increment']==0 and s['actual_cases'] is None and s['same_input_automatic_retry'] is False)
tools=load(N/'scope-generation.tool-observations.closed.json')
result={'checks':C,'failed':[x for x in C if not x['passed']],'scope_delta':delta,'binding_changed_keys':[k for k in set(b)|set(ob) if b.get(k)!=ob.get(k)],'input_refs':list(REFS.values()),'prior_review_ref':ref(Q/'review.json'),'prior_audit_ref':ref(Q/'audit.json'),'prior_check_count':len(oldaudit['checks']),'resolved_DLL_refs':list(missingrefs.values()),'current_head':current,'candidate_calls':0,'canonical_writes':0,'native_Git_calls':0,'full_resource_tree_rehashed':False,'source639_rehashed_this_audit':False,'runtime_leaf_rehash_scope':'8 metadata sources and 3 prior observed DLLs only; descriptor bytes verified','future_actual_graph_and_loader_qualification':'OPEN'}
save('audit.json',result)
print(json.dumps({'check_count':len(C),'failed':result['failed'],'binding_changed_keys':result['binding_changed_keys'],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
