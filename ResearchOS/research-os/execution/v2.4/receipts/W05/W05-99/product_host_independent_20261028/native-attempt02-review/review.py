import pathlib,json,hashlib,datetime
P=pathlib.Path;R=P('D:/作品集/ResearchOS/research-os');E=P(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp566/Product-host-owned-native-v2-scope.json'
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def js(p):return json.loads(P(p).read_bytes())
def req(c,m):
 if not c:raise RuntimeError(m)
def put(n,x):
 with (E/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
req(sha(S)=='78afa314b3d66795d43f8d565ee3a4bf7db46508082a095fc5ebd9cb5bd0a697','scope')
s=js(S);A=P(s['receipts_root']);O=P(s['outer_receipts_root']);C=A.parent/'attempt-02-reconcile';B=P(s['bundle_root'])
refs=[]
for d,label in [(A,'attempt-02'),(O,'attempt-02-outer'),(C,'reconcile')]:
 for p in sorted(d.iterdir()):
  if not p.is_file():continue
  raw=p.read_bytes();dest=E/'snapshots'/label/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw)
  req(sha(p)==sha(dest),'capture drift')
  refs.append({'path':str(p),'snapshot':str(dest),'sha256':sha(p),'bytes':len(raw)})
for r in s['bound_files']:req(sha(r['path'])==r['sha256'] and P(r['path']).stat().st_size==r['bytes'],'scope input drift '+r['path'])
u=js(A/'UNRESOLVED.json');w=js(A/'first.witness.json');st=js(A/'first.status.json');outer=js(O/'exit.json')
req(outer['exit']==1 and u['error']=='owned-folder-native-confirm','controller outcome')
req(w==u['first_witness']==u['current_witness'] and w['state']=='READY','witness')
req(w['parent_process']['PID']==js(A/'first.spawn.json')['pid']==66940 and w['control_process']['PID']==64080,'PID binding')
marker=js(B/'installed-product.json');req(w['installation_id']==s['installation_id']==marker['installation_id'] and w['inventory_digest']==marker['inventory_digest'],'install binding')
req(w['parent_process']['ImageSHA256']==marker['binaries']['electron']['sha256'] and w['control_process']['ImageSHA256']==marker['binaries']['control']['sha256'],'images')
req(st['ok'] and st['completed'] and st['result']['host_state']=='READY' and st['result']['host_instance_id']==w['host_id'],'desktop READY')
for n in ['05-cli-status-a','06-cli-status-b']:
 row=js(A/(n+'.stdout.raw'));req(row['exit_code']==0 and row['status']=='COMPLETED','CLI status')
 op=[o for o in row['operations'] if o['method']=='host.status'][0]
 req(op['result']['host_instance_id']==w['host_id'] and op['result']['host_state']=='READY' and op['result']['core_build_id']==st['result']['core_build_id'],'same host')
 req(js(A/(n+'.exit.json'))['exit']==0,'CLI process exit')
req(js(A/'04-duplicate-electron.exit.json')['exit']==0,'duplicate')
init=js(A/'07-cli-init.stdout.raw');event=js(A/'07-cli-init.events.jsonl');req(init['reason']=='NATIVE_WORKSPACE_CHOICE_FAILED' and init['detail']=='NATIVE_INVALID_REQUEST' and init['exit_code']==event['code']==1,'init rejection')
req(js(A/'08-owned-folder-confirm.exit.json')['exit']==1 and 'EXACT_OWNED_FOLDER_DIALOG_NOT_FOUND' in (A/'08-owned-folder-confirm.stderr.raw').read_text(encoding='utf8',errors='replace'),'chooser')
req(u['second_witness'] is None and u['third_witness'] is None and u['provider_connections']==0,'not reached')
assertions=[json.loads(x) for x in (A/'assertions.jsonl').read_text().splitlines()];req(assertions==u['assertions'] and len(assertions)==15 and all(x['passed'] for x in assertions),'assertions')
close=js(C/'close.exit.json');post=js(C/'post-close-observation.json');req(close['exit']==1 and not post['WM_CLOSE_reached'] and post['rows']==[] and post['data_witness_exists'] and post['termination_mechanism']=='NOT_OBSERVED','reconciliation')
for r in refs:req(sha(r['path'])==r['sha256'],'original changed during review')
put('INPUTS.json',{'scope':{'path':str(S),'sha256':sha(S),'bytes':S.stat().st_size},'bound_files_rechecked':len(s['bound_files']),'bound_files':s['bound_files'],'captured_originals':refs})
report={
 'schema':'researchos.independent-owned-native-attempt-review.v2','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'ATTEMPT02_PARTIAL_STARTUP_PROVEN_LIFECYCLE_FAILED','native_accepted':False,'formal_increment':0,
 'reviewer':'codex:/root/product_host_independent_20261028','source_commit':s['candidate_commit'],'source_tree':s['candidate_tree'],'installation_id':s['installation_id'],
 'outer_exit':1,'passed_assertions':15,'product_electron_primary_pid':66940,'product_core_pid':64080,'host_id':w['host_id'],
 'proven_partial_results':['Actual build05 Electron renders project-entry page and reports owned Core READY; previousASAR load failure is not reproduced','Desktop host.status and two concurrent CLI status commands all return samehost-3d6af32b818a/READY/core5c4c','Second Electron exits0 and current witness equals first; evidence supports reuse of observedhost, not full OS historical singleCore census','version/help exit0 and doctor NOT_FOUND exit3 without hostdata creation before startup','Counting loopback provider listener remains0 through recorded failed run; no model configuration/session.send reached'],
 'findings':[
  {'id':'A02-F01','priority':'P1','title':'Actual CLI init rejected before native folder chooser','evidence':'07-cli-init.stdout.raw: locallegWORKSPACE_PATH_VALIDATED, NATIVE_WORKSPACE_CHOICE_FAILED/detailNATIVE_INVALID_REQUEST, exit1; own event07:04:01.025Z. Folder helper subsequently exit1 EXACT_OWNED_FOLDER_DIALOG_NOT_FOUND.','root_cause':'Not established in this review; missing chooser is downstream observation, not evidence that automation click failed.','impact':'No project/session identities were created. Config/session/persistence/GUIreopen/CLIcoldreopen were not reached.'},
  {'id':'A02-F02','priority':'P1','title':'Process lifetime ended without observed controlled shutdown; READY witness remains','evidence':'Controller UNRESOLVED records primary66940 alive/notterminal and witnessREADY. Root later one close helper fails initial identity guard with OWNED_DESKTOP_IMAGE_MISMATCH; WM_CLOSE not sent. Post-close CIM07:07:00.869Z rows=[]; data witness exists; no first.events exit.','root_cause':'Termination mechanism NOT_OBSERVED. Execution-host job cleanup is a hypothesis only. The helper uses the same error for absent PID and wrongimage, so wrongimage existence is not proven.','impact':'Cannot accept safeClose or infer noforcedtermination from controller code. v2 no-kill static framework trace remains valid only at inspected code boundary; OS/execution-host lifecycle was not qualified.','automatic_retry_permitted':False},
  {'id':'A02-O01','priority':'OBSERVATION','title':'Rendered initial screenshot shows connection warning','evidence':'Independent visual inspection of first.png: project-entry rendered,0 accessibleprojects, top-right连接中断, STALE_RESPONSE banner.','impact':'API READY does not prove a clean user-facing initialscreen. Screenshot is one moment; persistence or rootcause not determined.'}
 ],
 'not_reached':['Native folder selection success','workspace.register/project.bootstrap success','Offline model configuration','Session create/open/get four identities','Nonempty session history preservation','Normal driver WM_CLOSE and safeExit','GUI reopen','CLI cold reopen','Final provider-zero assertion after completed lifecycle'],
 'reconciliation':{'root_only':True,'helper_exit':1,'WM_CLOSE_sent':False,'pids_absent_at':post['at'],'witness_still_exists':True,'termination_mechanism':'NOT_OBSERVED','close_retry_performed_by_reviewer':False},
 'process_evidence_limits':['UNRESOLVED carries process states at controller failure; controller exits before final childexit observation','Missing07-cli-init.exit.json is explained by assertion abort before init.wait; event/stdout/aggregate independently show exit1','No full historical OS process trace or naturalexit proof; no assertion of successfulsafeexit'],
 'reviewer_actions':{'product_process_starts':0,'product_process_stops':0,'product_retry':0,'cleanup':0,'source_edits':0,'original_receipt_edits':0},
 'inputs_ref':{'path':str(E/'INPUTS.json'),'sha256':sha(E/'INPUTS.json')},
 'scope_ref':{'path':str(S),'sha256':sha(S)},
 'previous_reports_preserved':True
}
put('REVIEW.json',report);print(json.dumps({'status':report['status'],'sha256':sha(E/'REVIEW.json'),'captured':len(refs),'bound':len(s['bound_files'])}))
