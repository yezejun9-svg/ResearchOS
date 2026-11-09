import ast, hashlib, json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'integration_codex/cli43-fresh-held2-r325-8e28fdaa3a7244edbbd2fc72e307b689'
O=Path(__file__).parent
reads={}; checks=[]
def ck(ok,label):
 checks.append({'check':label,'pass':bool(ok)})
def path(s):
 p=Path(s); return p if p.is_absolute() else R/p
def read(p):
 p=path(p); b=p.read_bytes(); k=str(p)
 if k in reads: ck(reads[k]==b,'stable repeated read '+k)
 reads[k]=b; return b
def ref(p):
 p=path(p);b=read(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def vr(r):
 b=read(r['path']);ck(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'ref '+r['path']);return b
def doc(p): return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def put(name,d):
 with (O/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json')
ck(ref(N/'scope_registration.json')['sha256']=='4e93937bed5ad9ab68c0b89f9db378b8b70e2da32437ebd01f6e93c7408c94a4','Root scope pin')
ck(ref(N/'bound-scope.manifest.json')['sha256']=='1909a7d97c47e1fb108bb6eedfdde82a3487655876aae0ed52aa793ddb93e8fc','Root manifest pin')
for name,count in [('bound-scope.manifest.json',34),('staging.manifest.json',19)]:
 m=doc(N/name);ck(m['count']==len(m['entries'])==count,name+' actual cardinality')
 for x in m['entries']:vr(x)
for x in s.values():
 if isinstance(x,dict) and set(x)=={'path','sha256','bytes'}:vr(x)
for x in b.values():
 if isinstance(x,dict) and set(x)=={'path','sha256','bytes'}:vr(x)
codes=doc(N/'metadata-code-refs.json')['entries']
ck(codes==b['metadata_code_refs'] and len(codes)==8,'eight actual code refs (six wrappers plus pipeline/builder)')
for x in codes:ast.parse(vr(x),filename=x['path'])
v5=P/'cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
for name in ['scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py']:
 ck(read(N/name)==read(v5/name),name+' exact reviewed template bytes')
original=doc(v5/'scope.v5.proposed.json');expect=dict(original)
for k in ('run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root','registration_namespace','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','controller_review_path','main_git','public_environment','authorization_gate_ref','runner_ref','launcher_ref'):expect[k]=b[k]
expect.update(preparation_only=False,execution_authorized=True,expected_before_registration=b['before'],expected_registration=b['after'],registration_metadata_paths=['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json'])
ck(s==expect,'entire actual scope equals v5 producer substitutions; no silent business change')
ck(b['before']==[324,152,430] and b['after']==[325,153,437],'explicit finite registration tuples')
ck(b['controller_review_ref'] is None and Path(s['controller_review_path'])==O/'review.json','acyclic future review path')
ck(s['source_commit']==s['main_git']['head']==b['main_git']['head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856','current43 source identity')
ck(s['main_git']['status_bytes']==894 and s['main_git']['status_rows']==13 and s['main_git']['deleted_rows']==11 and s['main_git']['index_empty'] is True,'declared immutable Git status bounds; no new Git invocation')
roots=[Path(s[k]) for k in ('new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root')]
ck(all(not p.exists() for p in roots),'all five operation roots absent')
ck(all(x!=y and not x.is_relative_to(y) and not y.is_relative_to(x) for i,x in enumerate(roots) for y in roots[i+1:]),'all operation roots disjoint')
before=rd(b['canonical_before_ref']); raws=[]
for x in before['entries']:
 z=vr(x['ref']);ck(z==vr(x['live_original_ref']),'copied/live canonical equality '+x['canonical_path']);raws.append(z)
cp,ow=map(json.loads,raws[:2]);ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'],'actual current tuple')
ck(cp['head']==s['source_commit'],'canonical current head')
prefix=rd(b['failure_prefix430_ref'])['failure_counters'];ck(prefix==cp['failure_counters'] and len(prefix)==430,'entire430 prefix')
cut=rd(b['origin_cut_ref']);ck(cut['before']==b['before'] and cut['after']==b['after'] and len(cut['origins'])==7,'seven frozen origins')
seen=set()
for row in cut['origins']:
 actual=rd(row['evidence_ref']);ck(actual==row['original_payload'],'original payload retained '+row['evidence_ref']['sha256'])
 sha=row['evidence_ref']['sha256'];ck(sha not in seen and all(old.get('evidence_ref',{}).get('sha256')!=sha for old in prefix),'origin new and unique '+sha);seen.add(sha)
authority=rd(s['current43_authority_ref'])
for x in authority['sealed_integration_refs']:vr(x)
ck(authority['current_canonical_refs']==[x['live_original_ref'] for x in before['entries']],'authority exact current four refs')
ck(authority['source_commit']==s['source_commit'] and authority['execution_authorized'] is False and authority['formal_increment']==0,'source identity is not execution grant')
catalog=rd(s['catalog_ref']);sources=rd(b['source_inputs_ref'])
ck(catalog['file_count']==len(catalog['files'])==len(sources['files'])==597,'597 current public source rows')
for a,c in zip(sources['files'],catalog['files']):
 ck(path(a['path'])==R/c['path'] and a['sha256']==c['sha256'] and a['bytes']==c['bytes'],'source catalogue join '+c['path']);vr(a)
rt=rd(s['runtime_resources_ref']); compiler=rd(s['compiler_resources_ref'])
ck(len(rt['files'])==1242 and len(compiler['files'])==22138,'actual descriptor resource counts; no current resource rehash claim')
roster=rd(s['roster_ref']);ck([x['test'].split('/')[-1] for x in roster['cases']]==s['ordered_cases']==['real-existing-open-readonly','real-existing-self-send'],'exact two existing-session cases')
ck(all(x['status']=='NOT_RUN' for x in roster['cases']),'no case executed')
ck(s['limits']=={'cases':2,'upstream_dispatch_per_case':32,'proxy_admission_per_case':32,'qualifying_observed_HTTP_legs':128,'unobserved_client_outbound_hard_cap':None,'SDK_MODEL_Node_external_paid_private_calls':0},'HTTP boundary and zero restricted calls')
ck(s['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5},'finite time limits not fit guarantee')
ck(s['first_unexpected_stop'] and not s['same_input_automatic_retry'] and not s['counter_reset'] and not s['source_acceptance'] and not s['Main_integration_authorized'] and s['formal_increment']==0,'stop/no authority widening')
for label in ['binding-build','scope-build']:
 inv=doc(N/(label+'.invocation.json'));ck(inv['actual_native_exit']==0 and inv['product_executed'] is False,label+' reported metadata native0');vr(inv['stdout_ref']);vr(inv['stderr_ref'])
reuse=[]
for rel,sha in [
 ('cli43_root_binding_static_independent_review_codex/24e45e3f33844e759faa662405e3d665/review.json','bafabafe29e493b5113c0d9fbeecc1f608517bb36965238f66959ffe3ed7fda9'),
 ('cli43_resource_selection_static_independent_review_codex/c171229249cc4a91a4b82dec5150c7d3/review.json','b4aaa816057f2a8b9906331d54d77d145a552835dc0ec06d7ef19937da29c43c'),
 ('cli43_recursive_runtime_static_independent_review_codex/777543835c244c2e948b49ea3933b58f/review.json','4b521f87453c0f74fa0f33e2cbbbee13cd400e8bd971ad1236bd476e57e7d81f')]:
 rr=ref(P/rel);ck(rr['sha256']==sha,'reused prior review pin '+rel);reuse.append(rr)
for k in ['runner_ref','launcher_ref','authorization_gate_ref']:ast.parse(vr(s[k]),filename=s[k]['path'])
gate=vr(s['authorization_gate_ref']).decode('utf-8'); engine=vr(codes[6]).decode('utf-8')
ck("grant['actual_registration_completed'] is True" in gate and "wip['cli43_fresh_compiler_controller_review_ref']" in gate and "review['decision'] == 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE'" in gate,'actual sealed future grant/review gate remains')
ck("desiredcp['work_in_progress'].update(dict(zip(WIP_KEYS,wipvalues)))" in engine and "rawdesired=[encoded(desiredcp),encoded(desiredow),*before[2:]]" in engine,'future three WIP refs/two changed metadata/STCM untouched')
ck("original[2:]==desired[2:]" in engine,'actual metadata invariant STCM')
for k,v in list(reads.items()):ck(Path(k).read_bytes()==v,'after-read stable '+k)
failed=[x for x in checks if not x['pass']]
put('audit.json',{'schema':'researchos.bound-scope-readonly-audit.v1','checks':checks,'failed':failed,'input_refs':[{'path':k,'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for k,v in reads.items()],'target_executions':0,'source_current_files_rehashed':597,'compiler_runtime_members_independently_rehashed_this_review':False,'actual_resource_pin_basis':'Root scope-mode producer code and actual0 metadata invocations plus exact descriptors; prior independent selector and partial PE reviews reused'})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES' if failed else 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE','requested_changes':failed,'scope_sha256':ref(N/'scope_registration.json')['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],'scope_ref':ref(N/'scope_registration.json'),'root_bound_manifest_ref':ref(N/'bound-scope.manifest.json'),'binding_ref':ref(N/'binding.pre-review.json'),'audit_ref':ref(O/'audit.json'),'reused_review_refs':reuse,'actual_registration_executed':False,'actual_product_execution':False,'review_itself_grants_execution':False,'expected_before':b['before'],'expected_after':b['after'],'actual_current_canonical_refs':[x['live_original_ref'] for x in before['entries']],'conditions':['Only after separately reviewed emitted registration metadata, actual CAS+seal and one exclusive Root grant may this exact two-case scope execute once. Standalone execution_authorized=true is configuration, not grant.','Future fresh Go graph, generated testmain/importcfg/archives/executables and actual observed OS hFiles must be fully matched/frozen; an unknown resource or first unexpected result stops without automatic widening or retry.','1242 runtime candidates include only54 statically inspected PE files; APIs/forwarders/74 unread nodes remain unresolved. Compiler22138 is a directory-selection candidate, not proof of actual fresh graph completeness or3300-second feasibility.','HTTP128 is an observed qualification boundary; unknown client outbound hard cap remainsNULL. Case exit, fixture validity and qualification remain separate.','This is preparation review only: no source/Main/formal acceptance, no old47 replay, no models/SDK/Node/external/private calls.'],'scope_inventory_corrections':{'metadata_code_refs':8,'staging_members':19,'bound_scope_members':34},'new_failure_origin_refs':[ref(O/'failure-origin.59b1a9.json')],'failure_cut_note':'New59b1a9 is outside fixed seven-origin325 proposal cut; retain pending, do not rewrite430→437.','status':'STOPPED'}
put('review.json',review)
print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed':len(failed),'read_files':len(reads)},ensure_ascii=False))
