import base64,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='0e298790cd484ec9ba319a379e7e34ed';O=Path(__file__).parent;N=P/('integration_codex/cli58-fresh-held2-r334-v2-'+U);E=P/'cli58_fresh_compiler_executor_codex'/U;L=P/'cli58_fresh_compiler_launcher_codex'/U
C=[];REF={}
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};REF[str(p)]=r;return r
def doc(p):ref(p);return json.loads(path(p).read_bytes())
def pin(r):
 a=ref(r['path']);ck('pin '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return path(r['path'])
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.json');X=path(s['new_export_root']);g=doc(path(s['new_authorization_root'])/'authorization.execute.json');result=doc(E/'result.json');closure=doc(E/'compiled-closure.json');cat=doc(pin(s['catalog_ref']));plan=doc(pin(s['instrumentation_ref']));inst=doc(E/'instrumentation.actual.json')
ck('MF E supplied',ref(E/'manifest.json')['sha256']=='efb16dfed555d674da8cd498444e66b11689edeb85fcd35ba97386df350e1f6e')
ck('MF L supplied',ref(L/'manifest.json')['sha256']=='c861c74f48704f77a02acc8a1390e1e07e1913abc6c9b1be012310a734634837')
raw=pin(inst['export_test']).read_text(encoding='utf-8');blocks=[]
for i,c in reversed(list(enumerate(plan['changes']))):
 count=raw.count(c['new']);ck('single inverse block '+str(i),count==1);blocks.append({'index':i,'count':count});raw=raw.replace(c['new'],c['old'],1)
ck('whole inverse currentMain originalbytes',raw.encode()==path(plan['original_path']).read_bytes() and hashlib.sha256(raw.encode()).hexdigest()==plan['original_sha256'])
ck('catalog e2 639/559Go',cat['commit']==s['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7' and cat['file_count']==len(cat['files'])==639 and cat['all_platform_Go_count']==559)
for row in cat['files']:
 main=ref(R/row['path']);ck('actualMain '+row['path'],main['sha256']==row['sha256'] and main['bytes']==row['bytes']);export=ref(X/row['path']);expected=inst['export_test'] if row['path']==plan['original_path'] else row
 ck('actual export '+row['path'],export['sha256']==expected['sha256'] and export['bytes']==expected['bytes'])
runner=pin(s['runner_ref']).read_text(encoding='utf-8');ck('instrumentation exact runner scope',"for c in reversed(plan['changes']):" in runner and "plan['exact_scoped_inline_edits']" not in runner)
casefacts=[]
for i,leaf in enumerate(s['ordered_cases']):
 req=doc(E/f'case-{i:02d}.request.json');inv=doc(E/f'case-{i:02d}.invocation.json');d=inv['result']['debug_capture'];gen=d['process_generations'];expected=[closure['test2json'],closure['testexe'],closure['cli']]
 argv=[closure['test2json']['path'],'-t','-p','researchos.local/research-os/apps/cli',closure['testexe']['path'],'-test.v','-test.count=1','-test.timeout=480s','-test.failfast','-test.run','^TestCLIProtocolInteractiveAuthority$/^'+leaf+'$']
 ck('exact leaf argv '+leaf,req['argv']==argv and req['environment']['RESEARCHOS_CLI_PROTOCOL_BINARY']==closure['cli']['path'] and path(req['cwd'])==X/'apps/cli' and req['timeout_seconds']==510 and req['process_cap']==16)
 ck('generation image exact3 '+leaf,len(gen)==3 and all(x['image']['before']=={'sha256':y['sha256'],'bytes':y['bytes']} and x['image']['after']==x['image']['before'] and x['job_membership_observed'] is True for x,y in zip(gen,expected)))
 ck('generation fullint unique and exits '+leaf,all(type(x['pid']) is int and type(x['creation_time_100ns']) is int for x in gen) and len({(x['pid'],x['creation_time_100ns']) for x in gen})==3 and [x['independent_exit'] for x in gen]==([0,0,0] if i==0 else [0,0,3]))
 casefacts.append({'case_id':leaf,'state':'QUALIFIED','native_test_exit':0,'CLI_exit':0 if i==0 else 3,'generations':[{'pid':x['pid'],'creation_time_100ns':x['creation_time_100ns'],'independent_exit':x['independent_exit'],'image':x['image']} for x in gen],'invocation_ref':ref(E/f'case-{i:02d}.invocation.json'),'verified_ref':ref(E/f'case-{i:02d}.verified.json')})
compilerfacts=[]
for name in ['build-cli','build-test','build-test2json']:
 q=doc(E/(name+'.request.json'));ck('fresh compiler flags '+name,'-p=1' in q['argv'] and '-buildvcs=false' in q['argv']);ck('compiler no network '+name,q['environment']['GOPROXY']==q['environment']['GOSUMDB']=='off' and q['environment']['GOTOOLCHAIN']=='local')
 for k in ['GOCACHE','GOTMPDIR','TEMP','TMP']:ck('fresh output cache '+name+k,path(q['environment'][k]).is_relative_to(X))
 compilerfacts.append({'label':name,'request_ref':ref(E/(name+'.request.json')),'argv':q['argv'],'GOCACHE':q['environment']['GOCACHE'],'GOTMPDIR':q['environment']['GOTMPDIR']})
for name in ['buildinfo-cli','buildinfo-test','buildinfo-test2json']:
 q=doc(E/(name+'.request.json'));raw=(E/(name+'.stdout.raw')).read_bytes();ck('new buildinfo actual '+name,len(raw)>0 and q['argv'][-1] in [closure[x]['path'] for x in ['cli','testexe','test2json']]);ref(E/(name+'.stdout.raw'))
Ldone=doc(L/'completed.json');ck('launcher complete no sourceaccept',Ldone['actual_outer_tool_exit'] is None and Ldone['actual_inner_native_exit']==0 and Ldone['program_reported_exit']==0 and Ldone['first_cause'] is None and Ldone['secondary']==[] and Ldone['source_acceptance'] is False and Ldone['formal_increment']==0)
for c in g['canonical_copies']:ck('current canonical equal '+c['canonical_path'],pin(c['ref']).read_bytes()==path(c['canonical_path']).read_bytes())
authority=doc(pin(s['current43_authority_ref']));sourceproof=[]
for k in ['source_commit_closure_ref','forward_head_audit_ref','combined_source_set_ref']:
 r=authority[k];pin(r);sourceproof.append(r)
ck('source58 boundary',authority['unique_combined_source_paths']==58 and authority['source_commit']==s['source_commit'] and authority['source_acceptance'] is False and authority['fresh_compilation_or_cases_accepted'] is False)
source=(X/'internal/domain/client_protocol.go').read_text(encoding='utf-8');ck('journal internal0 producer current', 'hash, 0, string(rb), headers' in source);ref(X/'internal/domain/client_protocol.go')
ck('wire LF producer current','json.NewEncoder(w).Encode(v)' in (X/'internal/api/v2.go').read_text(encoding='utf-8'));ref(X/'internal/api/v2.go')
save('supplement.json',{'checks':C,'failed_checks':[x for x in C if not x['passed']],'input_refs':list(REF.values()),'case_facts':casefacts,'compiler_facts':compilerfacts,'inverse_block_counts':blocks,'source_import_proof_refs':sourceproof,'current_source_files_hashed':639,'current_export_source_files_hashed':639,'qualification':'PENDING_ROOT_CLOSURE','new_failure_origins':[],'candidate_calls':0})
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'ref':ref(O/'supplement.json')},ensure_ascii=False))
