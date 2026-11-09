import ast,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'integration_codex/cli43-fresh-held2-r325-975b85d8c2384852a834cc07d5b3cb90';OLD=P/'integration_codex/cli43-fresh-held2-r325-b2d4f748ec374f248b2a853426d35292';O=Path(__file__).parent
reads={};checks=[]
def ck(x,n):checks.append({'check':n,'pass':bool(x)})
def ap(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=ap(p);b=p.read_bytes();k=str(p)
 if k in reads:ck(reads[k]==b,'stable reread '+k)
 reads[k]=b;return b
def ref(p):
 p=ap(p);z=read(p);return {'path':str(p),'sha256':hashlib.sha256(z).hexdigest(),'bytes':len(z)}
def vr(r):
 z=read(r['path']);ck(len(z)==r['bytes'] and hashlib.sha256(z).hexdigest()==r['sha256'],'pin '+r['path']);return z
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def put(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');old=doc(OLD/'scope_registration.json');ob=doc(OLD/'binding.pre-review.json')
ck(ref(N/'scope_registration.json')['sha256']=='3c70764ec5eec52475ede71e196557a354b4aecef4d50c84b7df6433d7d150dc','actual scope pin')
ck(ref(N/'bound-scope.manifest.json')['sha256']=='ad2856c01f0b14da0a1b9f2a986bafcc1c09655c78db9e31e1d82153d3027255','bound MF pin')
for name,size in [('bound-scope.manifest.json',34),('staging.manifest.json',20)]:
 m=doc(N/name);ck(len(m['entries'])==size and m['self_excluded'] is True,'actual manifest shape '+name)
 for row in m['entries']:vr(row)
partial=doc(N/'partial-staging-closure.json')
for row in partial['initial_staged_refs']:vr(row)
ck(len(partial['initial_staged_refs'])==15 and partial['actual_original_binding_or_template_calls']==0 and partial['original_program_not_rerun'] is True,'partial staged14 plusfailure exact15 closure preserved')
failure=rd(partial['original_failure_ref']);vr(failure['original_program_ref'])
ck(failure['actual_outer_exit']==failure['actual_root_python_exit']==1 and failure['actual_binding_template_helper_Git_CAS_product_calls']==0,'original a7 failure not product/nativeGit')
delta={k for k in set(s)|set(old) if s.get(k)!=old.get(k)}
ck(delta=={'registration_namespace','run_uuid','new_output_root','expected_registration','new_grant_preflight_root','controller_review_path','new_wrapper_root','new_export_root','new_authorization_root'},'scope exact identity/tuple delta only')
ck(s['expected_before_registration']==b['before']==[324,152,430] and s['expected_registration']==b['after']==[325,153,442],'actual before and proposed after')
ck(Path(s['controller_review_path'])==O/'review.json' and b['controller_review_ref'] is None,'acyclic review path exact')
for k,v in s.items():
 if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:vr(v)
for k,v in b.items():
 if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:vr(v)
roots=[Path(s[k]) for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
ck(all(not x.exists() for x in roots),'five execution leaves absent')
ck(all(x!=y and not x.is_relative_to(y) and not y.is_relative_to(x) for i,x in enumerate(roots) for y in roots[i+1:]),'five execution roots disjoint')
codesdoc=doc(N/'metadata-code-refs.json');codes=codesdoc['entries'];h=rd(codesdoc['source_handoff_ref']);v6review=rd(codesdoc['independent_preparation_review_ref'])
ck(v6review['decision']=='PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED' and v6review['requested_changes']==[],'v6 independent narrow review reused')
ck(len(codes)==8 and codes==b['metadata_code_refs'],'eight actual metadata refs')
projections=[]
for row in codes:
 raw=vr(row);ast.parse(raw,filename=row['path']);pp=ap(row['path']);rr={'path':pp.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 ck(rr==row,'prepare pin exact relative serialized '+row['path'])
 projections.append({'path':str(pp),'sha256':row['sha256'],'bytes':row['bytes']})
for row in h['wrapper_refs']:
 name=Path(row['path']).name;ck(read(N/name)==vr(row),'actual staged wrapper equals v6 '+name)
 actual=ref(N/name);matches=[x for x in projections if os.path.normcase(x['path'])==os.path.normcase(str(N/name))]
 ck(matches==[actual],'actual Root wrapper absolute module identity pinned '+name)
ck(codes[6]['sha256']=='10f179c906ed5a0ed3b551fac06252e54fe2a21579c27b11c8f7c1499ce4f950' and codes[7]['sha256']=='179de3dc1763cdf956b08327cb8727e231a3a227b9067ee84c4fc8158c88ad5a','actual v6 module and unchanged builder pinned')
module=vr(codes[6]).decode();runner=vr(s['runner_ref']).decode();gate=vr(s['authorization_gate_ref']).decode()
ck("for r in b['metadata_code_refs']: verify(r)" in module and "[{'path':str(safe(r['path'])),'sha256':r['sha256'],'bytes':r['bytes']} for r in b['metadata_code_refs']]" in module,'v6 exact verified ABS projection used')
ck("pin(output/name)==known[output/name]" in module and "bypath.get(os.path.normcase(p)) == row" in runner,'exact serialized and unknown runtime guards both preserved')
ck("grant['actual_registration_completed'] is True" in gate and "review['decision'] == 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE'" in gate,'actual sealed grant remains mandatory')
can=rd(b['canonical_before_ref']);oldcan=rd(ob['canonical_before_ref']);docs=[]
for x,y in zip(can['entries'],oldcan['entries']):
 raw=vr(x['ref']);ck(raw==vr(y['ref'])==vr(x['live_original_ref']),'current/copy/original canonical byte equality '+x['canonical_path']);docs.append(json.loads(raw))
ck([docs[0]['revision'],docs[1]['revision'],len(docs[0]['failure_counters'])]==[324,152,430] and docs[0]['head']==s['source_commit'],'actual current tuple/head unchanged')
cut=rd(b['origin_cut_ref']);oldcut=rd(ob['origin_cut_ref']);ck(len(cut['origins'])==12 and cut['origins'][:10]==oldcut['origins'] and cut['after']==[325,153,442],'exact original10 plus2')
seen=set()
for row in cut['origins']:
 ck(rd(row['evidence_ref'])==row['original_payload'],'exact original cut payload '+row['evidence_ref']['sha256'])
 sha=row['evidence_ref']['sha256'];ck(sha not in seen and all(x.get('evidence_ref',{}).get('sha256')!=sha for x in docs[0]['failure_counters']),'unique new origin '+sha);seen.add(sha)
for k in ['source_inputs_ref','runtime_resources_ref','compiler_resources_ref','failure_prefix430_ref','current43_authority_ref']:
 ck(rd(b[k])==rd(ob[k]),'unchanged descriptor/authority/prefix '+k)
authority=rd(s['current43_authority_ref'])
for row in authority['sealed_integration_refs']:vr(row)
ck(authority['current_canonical_refs']==[x['live_original_ref'] for x in can['entries']],'source authority exact actual four')
for label in ['binding-build','scope-build']:
 inv=doc(N/(label+'.invocation.json'));ck(inv['actual_native_exit']==0,'reported new metadata native0 '+label);vr(inv['stdout_ref']);vr(inv['stderr_ref'])
for name in ['root-metadata-phase.py','complete-stage-v2.py']:ast.parse(read(N/name),filename=name)
previous_review=ref(P/'cli43_current_bound_scope_independent_review_codex/1bcae38e2c3a483d8a1a37602b4e6dcb/review.json');request=ref(P/'cli43_current_bound_scope_independent_review_codex/6270469239494b17b9fd3d239243238b/review.json')
ck(previous_review['sha256']=='3ec51876fcc1fe29da2c729350093474cd6f1cc20be22d1aa358acba76e8eebe' and request['sha256']=='213d5c888e689fa910cbbaaa42220083322466d790875407962a7ac3be42623b','prior reviews immutable')
ck(s['limits']==old['limits'] and s['launch_limits']==old['launch_limits'] and s['ordered_cases']==['real-existing-open-readonly','real-existing-self-send'],'exact2 cases/caps/time unchanged')
ck(s['first_unexpected_stop'] and not s['same_input_automatic_retry'] and not s['source_acceptance'] and not s['Main_integration_authorized'] and s['formal_increment']==0,'stop and acceptance restrictions preserved')
for p,z in list(reads.items()):ck(Path(p).read_bytes()==z,'after-read stable '+p)
failed=[x for x in checks if not x['pass']]
put('audit.json',{'checks':checks,'failed':failed,'input_refs':[{'path':p,'sha256':hashlib.sha256(z).hexdigest(),'bytes':len(z)} for p,z in reads.items()],'actual_staged_module_projections':projections,'target_execution':0,'resource_members_independently_rehashed':False,'source597_rehashed_again':False})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES' if failed else 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE','requested_changes':failed,'scope_sha256':ref(N/'scope_registration.json')['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],'scope_ref':ref(N/'scope_registration.json'),'bound_manifest_ref':ref(N/'bound-scope.manifest.json'),'binding_ref':ref(N/'binding.pre-review.json'),'audit_ref':ref(O/'audit.json'),'v6_independent_review_ref':codesdoc['independent_preparation_review_ref'],'prior_scope_review_ref':previous_review,'preserved_prior_request_ref':request,'expected_before':b['before'],'expected_after':b['after'],'canonical_before':[x['live_original_ref'] for x in can['entries']],'actual_registration_executed':False,'actual_product_execution':False,'review_itself_grants_execution':False,'verified_facts':['Actual Root six staged wrappers equal reviewed v6 bytes; eight serialized relative metadata refs exactly equal pin() while their verified absolute projections match actual wrapper module keys.','Four current canonical originals match sealed copies at324/152/430; original430 prefix preserved, proposed12 new origin payloads unique and byte-bound. Original partial staging/failure retained; new continuation reports two metadata native0.','Scope identity/tuple fields changed with reviewed v6 metadata binding; runner/gate/launcher/business cases/caps unchanged. Original597-source and1242/22138 descriptor evidence reused, not independently rehashed again.'],'conditions':['Only new independently reviewed emitted registration metadata, actual Root CAS+seal and one exclusive actual grant authorize this exact two-case execution; standalone execution_authorized=true and this review alone do not.','Future full fresh Go graph/generated/importcfg/archive/exe and actual hFile resources must match declared approved inputs before cases; unknownresource/firstunexpected stops without automatic widening/retry.','Partial PE catalogue does not establish actual loaded completeness;3300/3600 bounds are not a demonstrated timing fit. HTTP32 upstream and32 proxy ingress percase/128 observed qualification remains separate from unobserved outbound hardcapNULL.','All source/Main/product/formal acceptance and old47/SDKNodeModelpaid/private calls remain outside this scope.'],'new_failure_origins':[],'status':'STOPPED'}
put('review.json',review)
print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed':len(failed),'read_files':len(reads)},ensure_ascii=False))
