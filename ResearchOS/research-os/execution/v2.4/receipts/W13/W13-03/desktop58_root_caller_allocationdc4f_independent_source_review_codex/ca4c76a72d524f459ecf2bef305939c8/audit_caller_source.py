import ast,json,hashlib
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationdc4f_source_preparation_codex/dc4fe023ed714e74b8d3692b504cf55d'
A=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-dc4fe023ed714e74b8d3692b504cf55d/root-allocation.actual.json'
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(r):
 b=Path(r['path']).read_bytes();ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def j(p):return json.loads(p.read_bytes())
def save(n,d):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
h=j(S/'handoff.json');mf=json.loads(verify(h['manifest_ref']))
ck('handoffpin',pin(S/'handoff.json')['sha256']=='3cd9fc35f0d68e19c4b0bd51cff95b7102402d868c9a3d3efa3d5e833ef733f7')
ck('MF8',len(mf['members'])==mf['member_count']==8)
for r in mf['members']:verify(r)
inv=json.loads(verify(h['inverse_ref']));old=verify(h['seed_ref']);new=verify(h['selected_ref'])
oldtext=old.decode();newtext=new.decode();back=newtext
ck('4logicaledits',len(inv['edits'])==4)
for e in reversed(inv['edits']):
 ck('exactanchor '+str(inv['edits'].index(e)),back.count(e['after'])==e['count']==1)
 back=back.replace(e['after'],e['before'],1)
ck('wholebytesinverse',back.encode()==old)
ot,nt=ast.parse(old),ast.parse(new);compile(new,'static-only','exec')
defs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
ck('3helperASTunchanged',defs(ot)==defs(nt) and set(defs(nt))=={'need','pin','save'})
anchor=inv['unchanged_tail_starts_at']
ck('tailwholebyteunchanged',oldtext[oldtext.index(anchor):]==newtext[newtext.index(anchor):])
alloc=j(A);ar=pin(A)
ck('actualallocationpin',ar['sha256']=='205a02409bece1af372d276bc9191328a115c1e8cd1826022b64524b8c40f1a0' and ar['bytes']==1487)
a=alloc['allocation']
ck('allocatedUID',a['run_uuid']==h['run_uuid']=='dc4fe023ed714e74b8d3692b504cf55d')
ck('allocatedregistration',Path(a['registration_namespace'])==Path(h['registration_namespace']))
ck('allocatedOUT',Path(alloc['caller_output'])==Path(h['root_allocated_future_caller_output']))
ck('beforeafter',alloc['before']==[335,163,580] and alloc['after']==[336,164,603])
ck('allocationnotgrant',alloc['execution_authorized'] is False)
ck('ROOTconstant',"ROOT = Path('D:/作品集/ResearchOS/research-os')" in newtext)
ck('REGconstant',a['registration_namespace'].replace('\\','/').split('/research-os/')[1] in newtext)
ck('AUTHconstant',a['new_authorization_root'].replace('\\','/').split('/W13-03/')[1] in newtext)
guard="need(OUT == DESKTOP_RECEIPTS / 'desktop58_root_terminal_closure_codex/baaf93516e9d42e2b583972e5a30df91', 'Fixed Root allocated caller output')"
ck('newexactOUTguard',newtext.count(guard)==1 and newtext.index(guard)<newtext.index(anchor))
ck('3argvstrictSHA',"need(len(sys.argv) == 4" in newtext and "all(c in '0123456789abcdef' for c in value)" in newtext)
ck('unboundfutureSHA',"SCOPE_SHA = None" in newtext and "GRANT_SHA = None" in newtext and h['actual_scope'] is None and h['actual_grant'] is None)
ck('onceemptyxb',"OUT.is_dir() and not any(OUT.iterdir())" in newtext and newtext.count('subprocess.run(')==1 and "open('xb')" in newtext)
ck('budgetsunchanged',all(x in newtext for x in ["timeout=7800", "scope['outer_seconds'] == 7500", "scope['inner_seconds'] == 7200", "scope['cleanup_seconds'] == 5", "scope['controller_evidence_reserve_seconds'] == 60", "scope['launcher_evidence_reserve_seconds'] == 60"]))
ck('nullablefirstcause',"result.returncode if result else None" in newtext and "'caller_error': error" in newtext and "'actual_outer_tool_exit': None" in newtext)
ck('noOSclaim',newtext.count("'caller_OS_lifecycle_qualification': False")==2)
ck('publicenvironment',"{'SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'PATHEXT'}" in newtext)
ck('no_site_pinned_launcher',"argv = [PYTHON, '-I', '-S', '-X', 'utf8', launcher['path']" in newtext)
ck('allocatedOUTabsent',not Path(alloc['caller_output']).exists())
ck('new4sourceleavesabsent',all(not Path(a[k]).exists() for k in ('new_output_root','new_wrapper_root','new_authorization_root','new_grant_preflight_root','new_export_root')))
au=save('audit.json',{'schema':'researchos.readonly-source-audit.v1','checks':checks,'passed':sum(c['passed'] for c in checks),'total':len(checks),'allocation_ref':ar,'source_ref':h['selected_ref'],'candidate_imported':False,'candidate_executed':False})
origin=pin(O/'failure-origin.a3e96b.json')
rv={'schema':'researchos.desktop58-root-caller-independent-source-review.v1','reviewer':'codex:/root/w05_merge_review','non_author':True,'decision':'READY_SOURCE_PREPARATION_ONLY' if all(c['passed'] for c in checks) else 'REQUEST_CHANGES','requested_changes':[c for c in checks if not c['passed']],'source_ref':h['selected_ref'],'caller_sha256':h['selected_ref']['sha256'],'author_handoff_ref':pin(S/'handoff.json'),'author_manifest_ref':h['manifest_ref'],'allocation_ref':ar,'audit_ref':au,'changed_logical_literals_or_guards':4,'candidate_imported':False,'candidate_executed':False,'source_acceptance':False,'formal_increment':0,'caller_OS_lifecycle_qualification':False,'actual_launch_authorized':False,'new_failure_count':1,'new_failure_origins':[origin],'open':['Actual reviewed new bound scope, CAS/seal/unique grant and their exact SHA arguments required.','Root must allocate exactly baaf output as new empty physical directory before invocation.','Preflight failures before subprocess try retain tool stderr; no owned-job or OS lifecycle proof claimed by thin caller.','Scope-read-to-EOF tail and 3 helper implementations reused exactly; no resource-tree or future qualification claim.'],'status':'STOPPED'}
rr=save('review.json',rv)
report=save('report.json',{'decision':rv['decision'],'scope':'Four logical changes only: REG, AUTH_ROOT, RUN_UUID and fixed argv OUT equality. Full inverse preserves original 7250B caller; selected is7393B.','checks':{'passed':sum(c['passed'] for c in checks),'total':len(checks)},'future_input_boundary':rv['open'],'actual_tool_failure':origin})
hd=save('handoff.json',{'schema':'researchos.independent-source-review-handoff.v1','review_ref':rr,'report_ref':report,'audit_ref':au,'decision':rv['decision'],'new_failure_count':1,'new_failure_origins':[origin],'status':'STOPPED'})
es=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mm=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':es,'count':len(es),'self_excluded':True,'mutable_after_seal':False})
print(json.dumps({'review':rr,'handoff':hd,'manifest':mm,'passed':sum(c['passed'] for c in checks),'total':len(checks),'findings':rv['requested_changes']},ensure_ascii=False))

