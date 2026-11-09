from pathlib import Path
import json,hashlib,ast,difflib,os
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft';O=Path(__file__).parent;checks=[];refs=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes();v=ref(p);refs.append(v);ck('ref '+str(p),v['sha256']==x['sha256'] and v['bytes']==x['bytes']);return b
def save(n,v):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return ref(p)
pins={'root_finite14_replay.v3.py':'32a3b29c31cad95f3635051fe7301ec7e8bab718e988efb78b86f9d6bb08bb60','root_finite14_scope.v3.json':'55e4c169937d2ecc4bc1aaa98e30538dab8071e9870ffd1c7c3309a636e81eda','authorization_gate.v3.py':'a12d165daf93687531e26a4652dcc338127f61fae63d40821d779128cbb09ba7','launch.v3.py':'63a8092df805a858c943cfb3b01661a541abeea56e876d634364a3cc94aa0be0'};raw={}
for name,h in pins.items():
 b=(N/name).read_bytes();raw[name]=b;refs.append(ref(N/name));ck('exactpin '+name,hashlib.sha256(b).hexdigest()==h);(O/('input.'+name)).write_bytes(b)
 if name.endswith('.py'):ast.parse(b);ck('AST '+name,True)
scope=json.loads(raw['root_finite14_scope.v3.json']);oldscope=json.loads((N/'root_finite14_scope.v2.json').read_bytes())
for k,v in scope.items():
 if isinstance(v,dict) and {'path','sha256','bytes'}<=set(v):verify(v)
for k in ['source_commit','actual_candidate_parent_expected','protected_body_source_base','protected_body_bytes','protected_body_sha256','ordered_cases','source_paths_sha256','actual_source_delta_paths','public_compiler_catalog_ref','individually_approved_public_Go_resources','limits','runtime_resources_ref','input_policy','database_policy','sidecar_rule','immutable_vector_extension','first_unexpected_stop','same_input_automatic_retry','counter_reset','source_acceptance','Main_integration_authorized','formal_increment']:
 ck('preservedscope '+k,scope[k]==oldscope[k])
ck('newfixedtransition',scope['expected_registration']==[319,147,413] and scope['python_flags']==['-I','-S','-X','utf8'])
for k in ['new_output_root','new_export_root','new_authorization_root']:
 ck('freshunique '+k,scope[k]!=oldscope[k] and not os.path.lexists(R/scope[k]) and scope['run_uuid'] in scope[k])
failure=json.loads(verify(scope['v2_actual_prelaunch_failure_ref']));origin=json.loads(verify(scope['v2_original_launcher_failure_ref']));ck('actualprelaunchfailure',failure['actual_outer_exit']==1 and failure['actual_native_exit'] is None and failure['actual_inner_exit'] is None and failure['product_cases_run']==0 and failure['actual_export_or_compile_started'] is False and failure['failure_stage']=='PIN_TOOLCHAIN_AND_RUNTIME');ck('oldauthretained',(R/oldscope['new_authorization_root']).is_dir())
rt=json.loads(verify(scope['runtime_resources_ref']));ck('unchanged1211',len(rt['files'])==1211)
for x in rt['files']:verify(x)
for stem in ['root_finite14_replay','authorization_gate','launch']:
 a=(N/(stem+'.v2.py')).read_bytes();b=raw[stem+'.v3.py'];ta,tb=ast.parse(a),ast.parse(b);(O/(stem+'.diff.txt')).write_text(''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='v2',tofile='v3')),encoding='utf-8');refs.append(ref(N/(stem+'.v2.py')))
 fa={x.name:ast.dump(x,include_attributes=False) for x in ta.body if isinstance(x,ast.FunctionDef)};fb={x.name:ast.dump(x,include_attributes=False) for x in tb.body if isinstance(x,ast.FunctionDef)}
 allowed={'root_finite14_replay':{'main'},'authorization_gate':{'binding','load_scope','validate_authority'},'launch':{'main'}}[stem]
 ck('noaddedremovedfunc '+stem,set(fa)==set(fb))
 for fn in fa:
  if fn not in allowed:ck('unchangedfunction '+stem+'.'+fn,fa[fn]==fb[fn])
 import re
 ck('allold64hexpreserved '+stem,set(re.findall(rb'[0-9a-f]{64}',a))<=set(re.findall(rb'[0-9a-f]{64}',b)))
for n,h in pins.items():ck('afterpin '+n,ref(N/n)['sha256']==h)
save('input_refs.json',refs);au=save('audit.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'candidate_imports':0,'native_product_calls':0,'runtime_DLL_calls':0,'site_package_resources_read_or_approved':False})
review={'schema':'researchos.session-list-root-runner-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_CANONICAL_ROOT_FINITE14_ONCE' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'runner_sha256':pins['root_finite14_replay.v3.py'],'scope_sha256':pins['root_finite14_scope.v3.json'],'launcher_sha256':pins['launch.v3.py'],'gate_sha256':pins['authorization_gate.v3.py'],'audit_ref':au,'source_commit':scope['source_commit'],'source_paths_sha256':scope['source_paths_sha256'],'reviewed_causal_change':'Both launcher and inner require isolated/no_site/UTF8/optimize0; launcher inner argv uses exact scope python_flags which gate validates and grant binding includes. System site startup is disabled rather than adding editable finder to approved resources. Actual loader/runtime success remains NOT_RUN.','registered_transition_required':{'before':[318,146,410],'after':[319,147,413],'failure_rule':'All410 original rows preserved byte-equivalent JSON and exactly3 rows appended; final actual registration separate review must verify identities8957bb/0bbcd5/7783ca.'},'preserved_guards':['Actual sealed registration+independent reviews+four canonical snapshots+unique grant before Git/Go/cases','Fixed14selectors/percase16/total224HTTP/zeroSDKmodelNodeexternalpaid','Exact2source hash/parent/protected14633/35? no new protected claim; original native14 function guards unchanged','Immutable original vector rows, buildinfo-after fullcheck, three per-case input stages','Three Go sidecar facts and proof flag plus Python lstat before/afterclose; no deletion','1211 approved runtime catalog samebytes, strict actualloadedsubset check; no site-packages whitelist','Oldv2 failedauth leaf retained; newUUID three roots unused','Nullable native/inner exit and full ownedJob cleanup/no retry maintained'],'prerequisites':['Root319 actual registration and seal must satisfy gate exact fields and append-three review','Pinned outer Python launch must include -I -S -X utf8','Alias-free authorization parent exists; new three leaves absent','Real fresh export/compile/runtime/cases remain NOT_RUN; firstunexpected stops'], 'limits':['Static analysis and public byte hashing only, no imports/DLL/SQL/Go/Node/HTTP/model','Same-user filesystem TOCTOU and implicitrowid limits retained','No source/Main/formal acceptance; old failure count not reset'],'failure_origins':[],'actual_registration_executed':False,'actual_product_execution':False,'source_acceptance':False,'formal_increment':0}
review['preserved_guards'][2]='Exact source hashes/parent/protected14633 and original14 native assertions unchanged'
r=save('review.json',review);m=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True});h=save('handoff.json',{'review_ref':r,'manifest_ref':m,'decision':review['decision'],'failure_origins':[]});print(json.dumps({'review':r,'manifest':m,'handoff':h,'checks':len(checks),'failed':review['requested_changes']},ensure_ascii=False))
