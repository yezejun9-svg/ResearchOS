import pathlib,json,hashlib,datetime
P=pathlib.Path;R=P('D:/作品集/ResearchOS/research-os');E=P(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp564/Product-host-owned-native-scope.json'
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def js(p):return json.loads(P(p).read_bytes())
def req(v,m):
 if not v:raise RuntimeError(m)
def put(n,v):
 with (E/n).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
scope=js(S);req(sha(S)=='e4eb2b6dd6734abf76bfe7b9a13b95489adae9cbb9139bc2cb5a9e1172d2014d','scope changed')
A=P(scope['receipts_root']);O=P(scope['outer_receipts_root']);B=P(scope['bundle_root'])
outer=js(O/'exit.json');u=js(A/'UNRESOLVED.json');req(outer['exit']==1 and u['status']=='FAILED_OR_UNRESOLVED_PRESERVE_OWNED_STATE','unexpected result')
req('PRODUCT_PATH_TYPE' in u['error'] and 'pid=37624' in u['error'],'missing native failure')
req(u['first_witness'] is None and u['second_witness'] is None and u['third_witness'] is None,'unexpected reached host')
refs=[]
def capture(p,name):
 p=P(p);raw=p.read_bytes();dest=E/'snapshots'/name;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(raw)
 req(sha(p)==hashlib.sha256(raw).hexdigest(),'changed during capture')
 refs.append({'path':str(p),'snapshot':str(dest),'sha256':sha(p),'bytes':len(raw)})
for folder,label in [(A,'attempt-01'),(O,'attempt-01-outer')]:
 for p in sorted(folder.iterdir()):
  if p.is_file():capture(p,P(label)/p.name)
capture(S,P('scope.json'))
bound=[]
for r in scope['bound_files']:
 req(sha(r['path'])==r['sha256'] and P(r['path']).stat().st_size==r['bytes'],'bound changed '+r['path']);bound.append(r)
for rel in ['lib/server/electron/electron.js','lib/server/utils/processLauncher.js']:
 capture(P(scope['playwright_path'])/rel,P('framework')/rel)
for rel in ['apps/desktop/main/main.js','apps/desktop/main/lib/product-layout.js']:
 capture(B/rel,P('product')/rel)
capture(B/'installed-product.json',P('installed-product.json'))
for label,expected in [('version',0),('help',0),('doctor',3)]:
 pref={'version':'01','help':'02','doctor':'03'}[label]+'-nonstarting-'+label
 ex=js(A/(pref+'.exit.json'));req(ex['terminal'] and ex['exit']==expected,'CLI exit')
 rows=[json.loads(s) for s in (A/(pref+'.stdout.raw')).read_text(encoding='utf8').splitlines() if s]
 req(bool(rows),'CLI jsonl')
 if label=='doctor':req(rows[0]['reason']=='NOT_FOUND' and rows[0]['health']=='NOT_CHECKED','doctor')
lines=[json.loads(s) for s in (A/'assertions.jsonl').read_text(encoding='utf8').splitlines() if s];req(lines==u['assertions'] and len(lines)==8 and all(x['passed'] for x in lines),'assertions')
for k in ['stdout','stderr']:
 r=outer[k];req(sha(r['path'])==r['sha256'] and P(r['path']).stat().st_size==r['bytes'],'outer raw')
inv=js(A/'invocation.json');req(inv['scope_sha256']==sha(S) and inv['marker_id']==scope['installation_id'],'invocation bind')
asar=[r for r in js(B/'installed-product.json')['files'] if r['path'].endswith('.asar')]
req(asar==[{'bytes':109371,'path':'runtime/electron/resources/default_app.asar','sha256':'ecd526468d13b0d4d9d9f430e0834f25dbcdcfd910b6e38f59e6c66192bd41c4'}],'asar candidate')
for r in refs:req(sha(r['path'])==r['sha256'],'raw changed after read')
put('INPUTS.json',{'scope_sha256':sha(S),'bound_files_rechecked':len(bound),'bound_files':bound,'captured_originals':refs})
report={
 'schema':'researchos.independent-owned-native-attempt-review.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'NATIVE_ATTEMPT_FAILED_NOT_ACCEPTED','native_accepted':False,'formal_increment':0,
 'source_commit':scope['candidate_commit'],'source_tree':scope['candidate_tree'],'installation_id':scope['installation_id'],
 'scope_ref':{'path':str(S),'sha256':sha(S)},'outer_exit':1,
 'observed':{'nonstarting_cli_commands':3,'cli_exits':{'version':0,'help':0,'doctor':3},'nonstarting_assertions_passed':8,'doctor':'NOT_FOUND / health NOT_CHECKED; expected absence, not ready host','product_electron_launches_observed':1,'electron_pid':37624,'controller_pid':js(O/'spawn.json')['pid'],'product_core_ready_observed':False,'first_second_third_witness':None,'provider_listener_connections':u['provider_connections'],'project_session_creation_reached':False,'gui_cli_reopen_reached':False,'safeclose_reached':False},
 'findings':[
  {'id':'NATIVE-F01','priority':'P1','title':'Actual Electron load rejects packaged inventory before host startup','evidence':'Raw Electron PID37624 stack: PRODUCT_PATH_TYPE at product-layout.js:31 exactPath, :42 relativeFile, :93 loadProductLayout; main.js:30. Electron launch then times out after45000ms.','impact':'GUI entry cannot reach firstWindow/READY; duplicate GUI, init, session and reopen paths were not exercised.','root_cause_status':'NOT_PROVEN','hypothesis':'Electron ASAR-aware node:fs may view runtime/electron/resources/default_app.asar as virtual directory while plainNode/filesystem review sees physical file. Inventory has one such archive; driver has not identified the failing row.','next_evidence':'Root-owned bounded physical-vs-Electron stat/read diagnostic or instrumentation at exactPath under separately reviewed scope; do not launch or retry automatically.'},
  {'id':'NATIVE-F02','priority':'P1','title':'Playwright launch error invokes implicit kill path, contradicting no-force-termination assurance','evidence':'Scope-bound Playwright lib/server/electron/electron.js:238-240 catch awaits kill(); processLauncher.js:185-205 checks state then Windows taskkill /pid <spawnedPID> /T /F. Current error returned from this launch path.','impact':'UNRESOLVED forced_termination=false describes only driver own code and cannot establish framework nontermination. Actual PID37624 final condition and whether taskkill was executed successfully remain unobserved in provided raw receipts.','framework_kill_callback_inferred_invoked':True,'actual_taskkill_os_effect':'NOT_CAPTURED','reviewer_gap':'Earlier native-driver preview review missed imported framework launch-error cleanup; retained unchanged as historical review, corrected here.','next_evidence':'Root read-only PID/creation/image/process observation; subsequent controller must avoid implicit forced cleanup. No repeat using this driver until reviewed.'}
 ],
 'pending_root_observation':['PID37624 and exact related children termination/identity facts; no reader-triggered process action','Post-run bundle/source/input and isolated state observation if Root has not yet captured'],
 'not_claimed':['No productCore process ever existed: stack is pre-startup but no historical OS process trace was captured','Safe shutdown or clean product exit','Any native lifecycle PASS beyond three nonstarting CLI branches','Busy-close/installer/clean-Windows/provider/C57/full22parents42formal'],
 'preservation':{'originals_modified':False,'existing_source_build_review_rewritten':False,'cleanup_attempts_in_this_task':0,'product_processes_launched_by_reviewer':0,'automatic_retry_performed':False},
 'evidence_index':{'path':str(E/'INPUTS.json'),'sha256':sha(E/'INPUTS.json')}
}
put('REVIEW.json',report);print(json.dumps({'status':report['status'],'report_sha256':sha(E/'REVIEW.json'),'captured':len(refs),'bound_files':len(bound)}))
