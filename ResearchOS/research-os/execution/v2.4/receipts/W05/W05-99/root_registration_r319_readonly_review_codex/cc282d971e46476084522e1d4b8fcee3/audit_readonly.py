from pathlib import Path
import json,hashlib,ast,subprocess,os
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-r319';O=Path(__file__).parent;checks=[];inputs=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
def ref(p):
 p=Path(p);raw=p.read_bytes();return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute() else R/p;v=ref(p);inputs.append(v);ck('pin '+str(p),v['sha256']==x['sha256'] and v['bytes']==x['bytes']);return p.read_bytes()
def doc(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 (O/n).write_bytes((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode());return ref(O/n)
pins={'register.py':'305be8576b1819e0d9083a10d9a78ff9d7b8a482db9da1e709a54d0b97bcbae3','run.py':'62269db0db826deaa81bf04f98fc9fa3e1108de35ba922f9712c13a7f1609355','prepared_refs.json':'a8386408439e9139310a997944bc73058c406cef925c75faf5ed8796cfd1a426','audit.json':'dec49916b900afac4d4e4a28d9d50d5ce4030d1280c8dd623c8da32f1f097d86','scope_registration.json':'f146af477ba408c54b9664f16785ac78ed255617fa47bfaf728304e136d7bf77','seal.py':'c4e94a4df05d367cdffb054d30d4f2bfb3b4fa6d49ff7eb3f646373aa0abf1a3'}
for name,sha in pins.items():
 b=(N/name).read_bytes();ck('draft '+name,hashlib.sha256(b).hexdigest()==sha);inputs.append(ref(N/name));(O/('input.'+name)).write_bytes(b)
 if name.endswith('.py'):ast.parse(b);ck('AST '+name,True)
p=doc(N/'prepared_refs.json');a=doc(N/'audit.json');s=doc(N/'scope_registration.json');copies=[];before=[]
for i,item in enumerate(p['canonical_before']):
 raw=verify(item);target=O/('before.'+Path(item['path']).name);target.write_bytes(raw);copies.append(ref(target));before.append(json.loads(raw));ck('copy bytes '+str(i),target.read_bytes()==raw)
ck('canonical order',[x['path'] for x in p['canonical_before']]==['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']]);ck('actualbefore',[before[0]['revision'],before[1]['revision'],len(before[0]['failure_counters'])]==[318,146,410])
for x in p['verified_refs']:verify(x)
orig=p['origins'];ck('three unique origins',len(orig)==3 and len({x['origin_key'] for x in orig})==3)
ck('audit origins exact',a['new_origins']==orig and a['expected_before']==[318,146,410] and a['expected_after']==[319,147,413])
oldkeys={x.get('origin_key') for x in before[0]['failure_counters']}
for x in orig:
 raw=verify(x['evidence_ref']);original=json.loads(raw)
 ck('original payload exact '+x['origin_key'],original==x['original_payload'])
 ck('origin new '+x['origin_key'],x['origin_key'] not in oldkeys and x['count_once'] is True and x['counter_reset'] is False)
ck('typed nullable exit mapping',[(x['actual_outer_exit'],x['actual_native_exit']) for x in orig]==[(1,None),(0,1),(1,None)])
ck('case counts actual',[x['product_cases_run'] for x in orig]==[0,1,0])
ck('source Node mapping',orig[1]['actual_native_exit']==orig[1]['original_payload']['actual_Node_exit'] and orig[1]['actual_HTTP_observed']==4)
# Resolve nested Source receipts using the evidence's actual worktree prefix; do not assume Main-relative originals.
wt=R/'.local/worktrees/codex-w1303-desktop-http-r311'
for key in ['result','stdout','stderr','source_snapshot']:
 x=orig[1]['original_payload'][key];q=wt/x['path'];v=ref(q);inputs.append(v);ck('Source nested '+key,v['sha256']==x['sha256'] and v['bytes']==x['bytes'])
result=doc(wt/orig[1]['original_payload']['result']['path']);save('source_failure_result_shape.json',{'keys':list(result),'raw_ref':ref(wt/orig[1]['original_payload']['result']['path'])})
ck('formal no increment',a['formal_increment']==0 and a['Main_source_integration'] is False)
rs=json.loads(verify(p['pins']['root_scope']));rr=json.loads(verify(p['pins']['runner_review']));sr=json.loads(verify(p['pins']['author14_review_ref']))
ck('runner grant review',rr['decision']=='READY_FOR_CANONICAL_ROOT_FINITE14_ONCE' and rr['requested_changes']==[] and rr['scope_sha256']==p['pins']['root_scope']['sha256']);ck('source nonauthor review',sr['actor']=='codex:/root/sources_parent_impl' and sr['status']=='READY_FOR_ROOT_INDEPENDENT_FINITE14' and sr['failed_checks']==[] and sr['source_acceptance'] is False)
ck('exact14 scope',s['case_count']==14 and s['ordered_cases']==rs['ordered_cases'] and s['limits']==rs['limits'] and s['source_only_commit']==rs['source_commit'] and s['source_acceptance'] is False and s['Main_integration_authorized'] is False and s['formal_increment']==0)
for k in ['new_output_root','new_export_root','new_authorization_root']:ck('root absent '+k,not os.path.lexists(R/rs[k]))
lock=doc(R/'execution/toolchains/locked.json')['tools'];env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul');git=lock['git']['path'];inv=[]
for k in ['python','git']:ck('lockedtool '+k,ref(lock[k]['path'])['sha256']==lock[k]['sha256'])
queries=[('main-head',R,['rev-parse','HEAD']),('main-status',R,['status','--porcelain=v1','--untracked-files=no']),('main-index',R,['diff','--cached','--name-only']),('g2-head',R/'.local/worktrees/codex-w0599-provider-g2-finite-r307',['rev-parse','HEAD']),('g2-status',R/'.local/worktrees/codex-w0599-provider-g2-finite-r307',['status','--porcelain=v1'])];outs={}
for n,cwd,args in queries:
 argv=[git,*args];z=subprocess.run(argv,cwd=cwd,env=env,capture_output=True);(O/(n+'.stdout.raw')).write_bytes(z.stdout);(O/(n+'.stderr.raw')).write_bytes(z.stderr);inv.append({'argv':argv,'cwd':str(cwd),'actual_exit':z.returncode});outs[n]=z.stdout;ck('git exit '+n,z.returncode==0)
ck('MainHEAD',outs['main-head'].decode().strip()==p['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079');ck('statuspin',hashlib.sha256(outs['main-status']).hexdigest()==p['git_status_sha256']);ck('13rows11D',len(outs['main-status'].splitlines())==13 and sum(x[:2]==b' D' for x in outs['main-status'].splitlines())==11);ck('indexempty',outs['main-index']==b'');ck('g2frozen',outs['g2-head'].decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9' and outs['g2-status']==b'')
for name,sha in [('runtime_coordinator_windows_test.go','a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'),('runtime_provider_binding_windows_test.go','df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4')]:ck('g2source '+name,ref(R/'.local/worktrees/codex-w0599-provider-g2-finite-r307/internal/domain'/name)['sha256']==sha)
for item in p['canonical_before']:verify(item)
for name,sha in pins.items():ck('draft unchanged '+name,ref(N/name)['sha256']==sha)
save('git_invocations.json',inv);save('input_refs.json',inputs);au=save('readonly-audit.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'actual_registration_executed':False,'product_calls':0})
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'actual_registration_executed':False,'expected_before':[318,146,410],'expected_after':[319,147,413],'register_sha256':pins['register.py'],'wrapper_sha256':pins['run.py'],'prepared_refs_sha256':pins['prepared_refs.json'],'audit_sha256':pins['audit.json'],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'readonly_audit_ref':au,'scope_review':['Only finite14 Root execution registration; no production source lease or source acceptance','Old410 exact prefix retained, three distinct actual origins appended once to413. Postcut7ae982 and536e3d remain pending; not imported here','Desktop06b1 writer released with author169 reported and Go3 OS limitation; no new execution or source acceptance. G2 bounded29 independent review registered without whole9/Main/formal acceptance','Four canonical pins before wrapper and every replace; HEAD/status guards, original+desired+intent before writes; expected_live and READS updated after own replacement','ST/CM bytes unchanged; original11deletions/indexempty/currentformal unchanged'],'future_gate_shape_mapping':{'registration-audit.json':'seal emits exact actor/status/before/after/actualexit/review/invocation/intent/verified fields required by gate','invocation.json':'wrapper emits actor/actual_exit/review_ref/register+wrapperSHA/stdout+stderrSHA and retry/reset false','canonical-write.intent.json':'register emits ordered CP/OW metadata original_ref+desired_ref; ST/CM unchanged ordered SHA; actor/head/exacttransition','canonical-write.verified.json':'register emits319/147/413 and actual intent_ref; two done files contain exactdesiredSHA','manifest.json':'seal hashes every ownNS file excluding manifest; requiredscripts/raw/intent/done/verified/audit listed with exactpath/hash/bytes','canonical snapshots':'future launcher compares current319 to actualdesired; copies4raw to exclusiveauthorizationroot; inner validates snapshotchain; laterliveprogress doesnotrebase'},'not_executed':['register','wrapper','seal','launcher','gate','product/tests/SQL/HTTP/Go/Node'],'postcut_pending_not_imported':['Source7ae982','Root536e3d'],'failure_origins':[],'source_acceptance':False,'formal_increment':0}
r=save('review.json',review);m=save('manifest.json',{'entries':[ref(x) for x in sorted(O.iterdir()) if x.is_file()],'self_excluded':True});h=save('handoff.json',{'review_ref':r,'manifest_ref':m,'decision':review['decision'],'failure_origins':[]});print(json.dumps({'review':r,'manifest':m,'handoff':h,'checks':len(checks),'failed':review['requested_changes']},ensure_ascii=False))
