import ast,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'integration_codex/cli43-fresh-held2-r325-b2d4f748ec374f248b2a853426d35292'
OLD=P/'integration_codex/cli43-fresh-held2-r325-8e28fdaa3a7244edbbd2fc72e307b689'
O=Path(__file__).parent; reads={};checks=[]
def ck(x,n): checks.append({'check':n,'pass':bool(x)})
def abs_path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=abs_path(p);b=p.read_bytes();k=str(p)
 if k in reads:ck(reads[k]==b,'stable repeated read '+k)
 reads[k]=b;return b
def ref(p):
 p=abs_path(p);b=read(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def vr(r):
 b=read(r['path']);ck(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'inputpin '+r['path']);return b
def doc(p):return json.loads(read(p))
def rd(r):return json.loads(vr(r))
def put(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');old=doc(OLD/'scope_registration.json');ob=doc(OLD/'binding.pre-review.json')
ck(ref(N/'scope_registration.json')['sha256']=='c04fa8a47db6b2430530f326ed50c6e27f89109462a9ecb9ee34aeb9b76c19ed','newscope pin')
ck(ref(N/'bound-scope.manifest.json')['sha256']=='5c8d107b54ee6f881bb0dfa4a2a4ed655088d5729b8a01eaf2a6cefa1194c417','newMF pin')
for name in ['bound-scope.manifest.json','staging.manifest.json']:
 m=doc(N/name);ck(len(m['entries'])==m['count'],'MF count '+name)
 for row in m['entries']:vr(row)
change={k for k in set(s)|set(old) if s.get(k)!=old.get(k)}
ck(change=={'registration_namespace','run_uuid','new_output_root','expected_registration','new_grant_preflight_root','controller_review_path','new_wrapper_root','new_export_root','new_authorization_root'},'exact nine scope-field delta')
ck(s['expected_before_registration']==[324,152,430] and s['expected_registration']==[325,153,440],'frozen transition')
ck(Path(s['controller_review_path'])==O/'review.json' and b['controller_review_ref'] is None,'fixed acyclic review path')
roots=[Path(s[k]) for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
ck(all(not x.exists() for x in roots),'five new leaves absent')
ck(all(x!=y and not x.is_relative_to(y) and not y.is_relative_to(x) for i,x in enumerate(roots) for y in roots[i+1:]),'five new roots disjoint')
for k in ['runtime_resources_ref','compiler_resources_ref','source_inputs_ref','failure_prefix430_ref']:
 nr=rd(b[k]);oraw=rd(ob[k]);ck(nr==oraw,'unchanged descriptor contents '+k)
for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
 ck(s[k]==old[k],'unchanged code ref '+k);vr(s[k])
codes=doc(N/'metadata-code-refs.json')['entries'];oldcodes=doc(OLD/'metadata-code-refs.json')['entries']
ck(codes==b['metadata_code_refs'] and len(codes)==8,'exact8 code refs')
for nr,orr in zip(codes,oldcodes):
 raw=vr(nr);oldraw=vr(orr);ck(raw==oldraw,'code bytes unchanged '+nr['path']);ast.parse(raw,filename=nr['path'])
 pp=abs_path(nr['path']);canonical={'path':pp.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 ck(nr==canonical,'metadata pin() exact root-relative dict '+nr['path'])
can=rd(b['canonical_before_ref']);oldcan=rd(ob['canonical_before_ref']);docs=[]
for nr,orr in zip(can['entries'],oldcan['entries']):
 raw=vr(nr['ref']);ck(raw==vr(orr['ref'])==vr(nr['live_original_ref']),'unchanged live/copies '+nr['canonical_path']);docs.append(json.loads(raw))
ck([docs[0]['revision'],docs[1]['revision'],len(docs[0]['failure_counters'])]==b['before']==[324,152,430],'actual4 canonical before')
cut=rd(b['origin_cut_ref']);oldcut=rd(ob['origin_cut_ref']);ck(cut['origins'][:7]==oldcut['origins'] and len(cut['origins'])==10,'old7 exact plus3 once')
seen=set()
for row in cut['origins']:
 ck(rd(row['evidence_ref'])==row['original_payload'],'raw original payload '+row['evidence_ref']['sha256'])
 sha=row['evidence_ref']['sha256'];ck(sha not in seen and all(x.get('evidence_ref',{}).get('sha256')!=sha for x in docs[0]['failure_counters']),'origin uniqueness '+sha);seen.add(sha)
last=cut['origins'][-1]['original_payload']
for k in ['first_cause_ref','original_native_invocation_ref','original_native_stdout_ref','original_native_stderr_ref']:vr(last[k])
ck(last['original_first_cause']==rd(last['first_cause_ref']) and last['actual_stage_native_exit']==1 and last['actual_outer_tool_exit']==1,'retained metadata native failure one original cause')
for label in ['binding-build','scope-build']:
 inv=doc(N/(label+'.invocation.json'));ck(inv['actual_native_exit']==0,'new actual metadata0 '+label);vr(inv['stdout_ref']);vr(inv['stderr_ref'])
rt=rd(b['runtime_resources_ref']);runner=vr(s['runner_ref']).decode();engine=vr(codes[6]).decode()
ck("allowed=rows+[b[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref')]+b['metadata_code_refs']" in engine,'runtime passes relative metadata refs unchanged')
ck("bypath = {os.path.normcase(x['path']): x for x in allowed}" in runner and "bypath.get(os.path.normcase(p)) == row" in runner,'module lookup has no absolute normalization')
ck("p = getattr(m, key, None)" in runner and "paths.add(str(Path(p).absolute()))" in runner,'sys.modules __main__ absolute path observation')
allowed=rt['files']+[b[k] for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']]+codes
keyset={os.path.normcase(x['path']) for x in allowed}
missing=[]
for row in codes[:6]:
 ap=str(abs_path(row['path']));missing.append({'wrapper_ref':row,'observed_absolute_path':ap,'absolute_path_key_present':os.path.normcase(ap) in keyset})
ck(all(x['absolute_path_key_present'] is False for x in missing),'all six wrapper __main__ absolute paths absent from allowed map')
prior=P/'cli43_current_bound_scope_independent_review_codex/1bcae38e2c3a483d8a1a37602b4e6dcb/review.json';pr=ref(prior)
ck(pr['sha256']=='3ec51876fcc1fe29da2c729350093474cd6f1cc20be22d1aa358acba76e8eebe','prior scope review preserved')
for p,z in list(reads.items()):ck(Path(p).read_bytes()==z,'after stable '+p)
finding={'id':'CLI43-BS-REL-01','priority':'BLOCKER','kind':'STATIC_PREPARATION_RESOURCE_BINDING_MISMATCH_NOT_EXECUTED','source_refs':[codes[6],s['runner_ref']],'locations':['metadata_pipeline.v5.proposed.py:runtime allowed construction lines116-117','current43_runner.v4.proposed.py:151-165 module_observation','metadata_pipeline.v5.proposed.py:prepare line231 git_guard'],'problem':'Root-relative metadata refs fix serialized pin equality but runtime() forwards them unchanged to module_observation. Its lookup keys are only normcase(raw path); observed sys.modules __main__.__file__ is absolute. Each Root wrapper therefore lacks an absolute allowed entry and fails before native Git in next prepare runtime guard.','static_witness':missing,'required_change':'Keep serialized metadata_code_refs root-relative for pin comparison. Build runtime allowlist from the exact verified metadata bytes using canonical absolute paths with unchanged SHA/bytes, no unknown-resource bypass and no unverified second read. Preserve same cached input identity and cross-phase guard. New immutable code/binding/scope and independent review are needed before prepare retry.','required_static_controls':['Every six-wrapper actual absolute __file__ resolves to exactly one allowlist ref with matching verified SHA/bytes.','Relative serialized refs remain exactly metadata pin() output.','An unknown path or altered SHA/bytes still rejects; runner/gate/HTTP/caps/source are unchanged.'],'actual_target_execution':0}
put('audit.json',{'checks':checks,'failed_audit_checks':[x for x in checks if not x['pass']],'static_findings':[finding],'input_refs':[{'path':p,'sha256':hashlib.sha256(z).hexdigest(),'bytes':len(z)} for p,z in reads.items()],'target_executions':0,'all_resource_members_rehashed':False,'current_source_rehashed_again':False,'prior_scope_analysis_reused':pr})
review={'schema':'researchos.cli43-compiler-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','requested_changes':[finding],'scope_sha256':ref(N/'scope_registration.json')['sha256'],'runner_sha256':s['runner_ref']['sha256'],'launcher_sha256':s['launcher_ref']['sha256'],'gate_sha256':s['authorization_gate_ref']['sha256'],'scope_ref':ref(N/'scope_registration.json'),'bound_manifest_ref':ref(N/'bound-scope.manifest.json'),'audit_ref':ref(O/'audit.json'),'prior_review_ref':pr,'expected_before':b['before'],'expected_after':b['after'],'actual_registration_executed':False,'actual_product_execution':False,'review_itself_grants_execution':False,'verified_delta':'Only nine scope identity/tuple fields; eight metadata refs change path spelling, all original code bytes unchanged. Ten exact original failure payloads retain old7 plus3; all4 current canonical bytes match before324/152/430. New scope build reports two metadata native0 only.','limits':'No new resource-current rehash or Go graph/Windows loader qualification. Prior 597-source/selector/runtime reviews reused with descriptor equality. Source/formal acceptance remains false.','new_failure_origins':[],'status':'STOPPED'}
put('review.json',review)
print(json.dumps({'review_ref':ref(O/'review.json'),'checks':len(checks),'failed_audit_checks':sum(not x['pass'] for x in checks),'static_requests':1,'files':len(reads)},ensure_ascii=False))
