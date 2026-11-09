import ast,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29'
OLD=P/'integration_codex/cli43-fresh-held2-r325-975b85d8c2384852a834cc07d5b3cb90'
V7=P/'cli43_root_binding_preparation_revision_codex/9fd9cbeb1343442aa6e34e41f3f2deea'
reads={};checks=[]
def ck(ok,label):checks.append({'check':label,'pass':bool(ok)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);raw=p.read_bytes()
 if str(p) in reads:ck(reads[str(p)]==raw,'repeat stable '+str(p))
 reads[str(p)]=raw;return raw
def ref(p):
 p=path(p);raw=read(p);return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def vr(r):
 raw=read(r['path']);ck(hashlib.sha256(raw).hexdigest()==r['sha256'] and len(raw)==r['bytes'],'pin '+r['path']);return raw
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
for name,sha in [('scope_registration.json','c942ced8bc4e34668e74997a1950150816ee819298e54a448b588e0e3ea2eb20'),('bound-scope.manifest.json','e6e9ce78c246cca39d0cebeffd4d2ff5e7001fd355d45edc0e7a672dcddc62c0'),('runtime-with-root-metadata.v4.json','ba5dd2044791e16e3cfa0700a7c81b521d7e56a9a2bb4eb4109976a48c7ec59f')]:
 ck(ref(N/name)['sha256']==sha,'actual fixed '+name)
mf=doc(N/'bound-scope.manifest.json');smf=doc(N/'staging.manifest.json')
for row in mf['entries']:vr(row)
for row in smf['entries']:vr(row)
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');old=doc(OLD/'scope_registration.v2.json');oldb=doc(OLD/'binding.pre-review.v2.json');ra=doc(N/'bound-scope-audit.json')
scope_ref=ref(N/'scope_registration.json');scope_relative=dict(scope_ref,path=(N/'scope_registration.json').relative_to(R).as_posix())
ck(ra['scope_invocation_ref']==scope_relative,'actual Root relative scope ref matches Gate Reader serialization')
ck(s['controller_review_path']==str(O/'review.json') and b['controller_review_path']==s['controller_review_path'] and b['controller_review_ref'] is None,'acyclic own fixed review path')
allowed_scope={'run_uuid','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root','registration_namespace','controller_review_path','runtime_resources_ref'}
changed_scope={k for k in set(s)|set(old) if s.get(k)!=old.get(k)}
ck(changed_scope==allowed_scope,'scope exact UUID roots namespace review runtime changes only')
for k in set(s)&set(b):ck(s[k]==b[k],'scope/binding shared field '+k)
ck(b['before']==s['expected_before_registration']==[324,152,430] and b['after']==s['expected_registration']==[325,153,442],'same proposed tuple cut12')
ck(b['registration_namespace']==N.relative_to(R).as_posix(),'actual namespace')
ck(s['ordered_cases']==['real-existing-open-readonly','real-existing-self-send'] and s['limits']==old['limits'],'unchanged exact two cases and caps')
ck(s['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5},'actual timeout bounds')
ck(s['first_unexpected_stop'] and not s['same_input_automatic_retry'] and not s['counter_reset'],'stop no same-input retry no reset')
ck(s['source_acceptance'] is False and s['Main_integration_authorized'] is False and s['formal_increment']==0,'no source/formal grant')
rootkeys=['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root'];roots=[Path(s[k]) for k in rootkeys]
ck(len(set(roots))==5 and all(not x.is_relative_to(y) for x in roots for y in roots if x!=y),'five disjoint roots')
for x in roots:
 ck(s['run_uuid'] in x.name and not os.path.lexists(x),'new UUID leaf absent '+str(x))
 ck(x.parent.is_dir(),'existing parent '+str(x.parent))
ck(not(N/'binding.json').exists() and not(N/'prepare.started.json').exists(),'prepare not yet run')
codes=b['metadata_code_refs'];code_doc=doc(N/'metadata-code-refs.json');ck(codes==code_doc['entries'] and len(codes)==8,'actual metadata8 refs')
vh=doc(V7/'handoff.json');v7wr={Path(r['path']).name:r for r in vh['wrapper_refs']}
for row in codes:
 raw=vr(row);p=path(row['path']);ck(not Path(row['path']).is_absolute(),'metadata serialized ref relative '+row['path'])
 ck({'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}==row,'prepare pin exact dict '+row['path'])
 if p.parent==N:
  ck(raw==vr(v7wr[p.name]),'staged v7 wrapper byte equality '+p.name);ast.parse(raw)
module_ref=next(r for r in codes if r['sha256']==vh['metadata_module_ref']['sha256']);module=vr(module_ref).decode();ast.parse(module)
ck(vh['metadata_module_ref']['sha256']=='095d4f4b86ad0432bd559d2df7221d7f26794eb484f07d313fcc67d3a54f3eed','actual v7 module')
ck("observation=util.module_observation(allowed,helper)\n    observation['all_observed_inputs_pre_pinned']=True\n    return helper,lock,save" in module,'producer successful strict observation marker then save')
ck("for r in b['metadata_code_refs']: verify(r)" in module and "'path':str(safe(r['path']))" in module,'v6 strict verified runtime ABS projection kept')
rt=rd(s['runtime_resources_ref']);ort=doc(OLD/'runtime-with-root-metadata.v4.json')
expected8=[dict(r,path=str(path(r['path']))) for r in codes]
ck(len(rt['files'])==1250 and rt['files'][:1242]==ort['files'][:1242],'runtime old1242 literal prefix unchanged')
ck(rt['files'][1242:]==expected8,'exact8 actual staged metadata ABS tail')
for r in expected8:vr(r)
ck(len({os.path.normcase(r['path']) for r in rt['files']})==1250,'runtime unique paths')
for key in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref','catalog_ref','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref','compiler_resources_ref','current43_authority_ref','toolchain_lock_ref']:
 ck(s[key]==old[key],'unchanged original input '+key);vr(s[key])
gate=vr(s['authorization_gate_ref']).decode();ast.parse(gate)
ck("wip['cli43_fresh_compiler_held2_scope_ref'] == scope_ref" in gate and "grant['scope_ref'] == scope_ref" in gate and "p.relative_to(ROOT).as_posix()" in gate,'gate CP/scope/grant relative exactdict preserved')
ck("observed['all_observed_inputs_pre_pinned'] is True" in gate and "'runtime_observation_refs':observed" in module,'saved marker consumed by original grant gate')
ck("wipvalues=[scope_ref,b['current43_authority_ref'],b['controller_review_ref']]" in module and "'actual_registration_completed':True,'scope_ref':scope_ref" in module,'same supplied scope dict propagated into CP and grant')
source=rd(b['source_inputs_ref']);oldsource=rd(oldb['source_inputs_ref'])
ck(source==oldsource and len(source['files'])==597,'same frozen source597 inventory reused without rehashing its members')
compiler=rd(s['compiler_resources_ref']);ck(len(compiler['files'])==22138,'same selected compiler22138 inventory count only')
can=rd(b['canonical_before_ref']);can_docs=[]
for row in can['entries']:
 raw=vr(row['ref']);ck(raw==vr(row['live_original_ref']),'actual current four canonical equality '+row['canonical_path']);can_docs.append(json.loads(raw))
ck([can_docs[0]['revision'],can_docs[1]['revision'],len(can_docs[0]['failure_counters'])]==b['before'],'current actual324/152/430')
ck(can_docs[0]['head']==s['source_commit']==s['main_git']['head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856','current source/head pin')
prefix=rd(b['failure_prefix430_ref']);ck(prefix['failure_counters']==can_docs[0]['failure_counters'],'full430 prefix exact')
cut=rd(b['origin_cut_ref']);oldcut=rd(oldb['origin_cut_ref'])
ck(cut==oldcut and cut['before']==b['before'] and cut['after']==b['after'] and len(cut['origins'])==12,'same12 original cut not expanded')
ck(cut['counter_reset'] is False and cut['actual_registration_executed'] is False,'cut not registered or reset')
for row in cut['origins']:ck(rd(row['evidence_ref'])==row['original_payload'],'original payload exact '+row['evidence_ref']['path'])
ck(len({r['evidence_ref']['sha256'] for r in cut['origins']})==12,'unique12 evidence refs')
ck(not({r['evidence_ref']['sha256'] for r in cut['origins']} & {r.get('evidence_ref',{}).get('sha256') for r in can_docs[0]['failure_counters']}),'new cut absent from old430')
driver=read(N/'root-metadata-phase.py');prior_driver=read(OLD/'root-metadata-phase.v2.py');ast.parse(driver)
inverse=driver.replace(b'root-inputs.runtime-bound.json',b'root-inputs.runtime-bound.v2.json').replace(b'scope_registration.json',b'scope_registration.v2.json').replace(b'binding.pre-review.json',b'binding.pre-review.v2.json').replace(scope_ref['sha256'].encode(),ref(OLD/'scope_registration.v2.json')['sha256'].encode())
ck(inverse==prior_driver,'outerdriver only three filename versions and scopeSHA delta')
ck("scope_ref['path'] = (OUT / 'scope_registration.json').relative_to(ROOT).as_posix()" in driver.decode(),'outerdriver explicit exact relative ScopeRef before prepare/grant')
for label in ['binding-build','scope-build']:
 inv=doc(N/(label+'.invocation.json'));ck(inv['actual_native_exit']==0 and inv['automatic_retry'] is False and inv['counter_reset'] is False and inv['product_executed'] is False,label+' actual metadata-only native0')
 vr(inv['stdout_ref']);vr(inv['stderr_ref']);doc(N/(label+'.request.json'))
reused=[ref(P/'cli43_root_binding_static_independent_review_codex/c1a6b02b51ac427eb35ea000155db1c7/review.json'),ref(P/'cli43_current_bound_scope_independent_review_codex/46bfd2f723c84ad68e321774d6e08b30/compatibility-matrix.json'),ref(P/'cli43_current_bound_scope_independent_review_codex/46bfd2f723c84ad68e321774d6e08b30/review.json')]
ck([r['sha256'] for r in reused]==['4e3b71bc756207ad72614efe82568f8fa2eecc5fa9b418e4674a4066faaecae6','81d226904a5b40143952c11def14326469c1965b8e41e95e711291d3feb5110b','06f2631a127dab79604a33fee0b5cc4fe5f7bc72dc4170942a3948f3a595aeed'],'prior v7 and full compatibility evidence unchanged')
for p,raw in list(reads.items()):ck(Path(p).read_bytes()==raw,'after stable '+p)
failed=[x for x in checks if not x['pass']]
save('audit.json',{'checks':checks,'failed_checks':failed,'input_refs':[{'path':p,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for p,raw in reads.items()],'reused_review_refs':reused,'actual_target_execution':False,'new_failure_origins':[]})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_CURRENT43_HELD2_ONCE' if not failed else 'REQUEST_CHANGES','requested_changes':failed,'scope_sha256':scope_ref['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],'scope_ref':scope_ref,'scope_invocation_ref':scope_relative,'bound_manifest_ref':ref(N/'bound-scope.manifest.json'),'audit_ref':ref(O/'audit.json'),'reused_review_refs':reused,'metadata_module_ref':module_ref,'expected_before':b['before'],'expected_after':b['after'],'canonical_before':can['entries'],'findings_closed':['ROOT-relative scope dictionary now reaches CP and final grant gate unchanged.','Runtime1250 retains old1242 and byte-verified exact eight metadata ABS identities.','V7 derives the gate success marker only after strict observation returns.'],'execution_conditions':['Independent actual registration-source review then successful CAS and sealed actual registration.','Unique grant validates the full scope SHA, actual copied canonical4, authority refs, final actual Git and runtime observations.','Only the fixed two cases once; every unknown resource, drift, unexpected result or prerequisite failure stops its dependent lane.'],'limits':'Source597/compiler22138/original1242 runtime reviews reused, with JSON inventory identity and only eight metadata members independently rehashed here. No actual fresh Go graph or OS lifecycle/load completeness or time-fit claim. HTTP128 is qualification after full observation, not unknown client outbound hard cap.','actual_registration_executed':False,'actual_product_execution':False,'review_itself_grants_execution':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'}
save('review.json',review);print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed_checks':failed,'input_files':len(reads)},ensure_ascii=False))
