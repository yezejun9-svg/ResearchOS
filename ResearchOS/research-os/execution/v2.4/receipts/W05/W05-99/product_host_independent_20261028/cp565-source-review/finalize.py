import pathlib,json,hashlib,datetime,subprocess
P=pathlib.Path;E=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/desktop-installed-delivery-20261025'
A=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028/asar-repair-cp565'
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp565/ASAR-exact2-repair-scope.json'
root=S.parent/'product-host-build05-root-verification.json'
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def js(p):return json.loads(P(p).read_bytes())
def req(c,m):
 if not c:raise RuntimeError(m)
def put(n,x):
 with (E/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
mf=A/'FINAL-MANIFEST.json';req(sha(mf)=='90c8104c972f60e31f127d324cd35debd0ee25c4e1a10a2534cc2935ecebfa03','author final')
req(sha(root)=='0d2f1553bc55e698a59b8fdb57ede83a5bf216a1460eaf1ca807c0a5dc2fabee','root review')
req(sha(S)=='2356e030bf6a2ea303701444db6338901b333d78f3b872b3291e15c6fa5dac1f','scope')
refs={}
def walk(x):
 if isinstance(x,dict):
  if all(k in x for k in ['path','sha256','bytes']) and P(x['path']).is_absolute():
   key=str(P(x['path'])).lower();v={k:x[k] for k in ['path','sha256','bytes']};req(key not in refs or refs[key]==v,'conflicting ref');refs[key]=v
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(js(mf))
for r in refs.values():req(sha(r['path'])==r['sha256'] and P(r['path']).stat().st_size==r['bytes'],'author ref changed '+r['path'])
put('AUTHOR-REFERENCE-AUDIT.json',{'status':'PASS','manifest_sha256':sha(mf),'unique_references_checked':len(refs),'references':list(refs.values())})
before=js(A/'tests-source.before.json');after=js(A/'tests-source.after.json');req(before['files']==after['files'] and before['node_sha256']==after['node_sha256'],'tests drift')
for r in before['files']:req(sha(W/r['path'])==r['sha256'],'tests current bytes')
raw=(A/'node8.stdout.raw').read_text(encoding='utf8');req('tests 9' in raw and 'pass 9' in raw and 'fail 0' in raw,'node9 raw')
req(js(A/'tests-exit.json')['node8_exit']==0,'node9 exit')
vm=js(E/'VM-RESULT.json');req(len(vm['results'])==5 and all(r['pass'] for r in vm['results']),'ownVM')
probe=js(A/'probe-stdout.raw');ex=js(A/'probe-exit.json');inv=js(A/'probe-invocation.json');pid=js(A/'probe-pid.json')
req(ex['terminal'] and ex['exit_code']==0 and not ex['timeout'] and ex['pid']==pid['pid']==probe['electron_pid']==54912,'probe exit')
req(probe['patched']=={'file':False,'directory':True},'patched asar')
req(probe['physical']['file'] and not probe['physical']['directory'] and probe['physical']['realpath_native'] and probe['physical']['sha256']=='ecd526468d13b0d4d9d9f430e0834f25dbcdcfd910b6e38f59e6c66192bd41c4','physical asar')
req(not probe['default_loader']['ok'] and probe['default_loader']['code']=='PRODUCT_PATH_TYPE','default reproduce')
req(probe['physical_loader']=={'ok':True,'installation_id':'0060129e118af8981a6f7a17e6835b11e19fc4e6647b412e4bf7a64f6e6ef39c','file_count':133},'physical success')
entry=W/'.local/asar-repair-cp565-20261028/probe-app/main.js';pkg=entry.with_name('package.json')
req(sha(entry)==inv['entry_sha256'] and sha(pkg)==inv['package_sha256'] and sha(S)==inv['scope_sha256'],'probe inputs')
req(sha(inv['argv'][0])==inv['electron_sha256'],'electron pin')
build=js(E/'BUILD05-REVIEW.json');req(build['head']=='5c4c94022bd92da68ef544f2779527bfe065c428','build commit')
req(subprocess.check_output(['git','-C',str(W),'status','--porcelain']).strip()==b'','worktree drift')
evidence=[S,mf,root,E/'BUILD05-REVIEW.json',E/'BUILD05-INPUTS.json',E/'BUILD05-DEPENDENCY-DELTA.json',E/'SOURCE-VM-REVIEW.json',E/'VM-RESULT.json',E/'AUTHOR-REFERENCE-AUDIT.json',entry,pkg,A/'probe-launch.py',A/'probe-invocation.json',A/'probe-pid.json',A/'probe-stdout.raw',A/'probe-stderr.raw',A/'probe-exit.json',A/'tests-source.before.json',A/'tests-source.after.json',A/'tests-exit.json',A/'node8.stdout.raw',A/'node8.stderr.raw',E.parent/'native-attempt01-review/REVIEW-FINAL.json',E.parent/'final-448af-review/FINAL-REVIEW.json']
report={
 'schema':'researchos.independent-product-host-source-build-review.v2','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'codex:/root/product_host_independent_20261028','status':'LIMITED_CP565_SOURCE_BUILD_AND_DIAGNOSTIC_ACCEPTED',
 'source_build_accepted':True,'accepted_commit':build['head'],'accepted_tree':build['tree'],'accepted_build':str(W/'.local/product-layout-cp558-20261028-05'),'accepted_marker_sha256':build['marker_sha256'],'accepted_installation_id':build['installation_id'],
 'scope':'CP565 exact2 ASAR physical-fs main entry injection plus unchanged loader, relevant tests, one isolated diagnostic Electron probe and fresh build05; previous limited evidence retained by immutable references',
 'exact_changed_paths':['apps/desktop/main/main.js','tests/ui/desktop/product-host.test.mjs'],
 'unchanged_loader_sha256':'4379be504232309f3f7be71b7cc0e2d9be54e331e34bfa84820c08c2f00009eb',
 'source_checks':['main requires original-fs and passes it only to loadProductLayout','No process.noAsar global switch, no skipped archive entry, no hash/type/path validation relaxed','New fixture tests virtual-directory rejection, physical-file success, content tamper rejection and real-directory substitution rejection'],
 'observed_evidence':{
  'asar_mechanism':'One author Electron37.10.3 diagnostic pid54912 exit0: same physical .asar becomes directory in node:fs, physical file in original-fs; unchanged build04 full133 loader rejects default PRODUCT_PATH_TYPE and accepts injectedfs at sameinstallationID',
  'author_node_tests':'9/9 PASS; run before commit at448af+exact2 bytes, before/after main/test/loader hashes equal final5c4c; not claimed rerun postcommit',
  'independent_main_vm':'4 lifecycle branches plus physical-fs injection assertion PASS against exact5c4c snapshot; every branch calls loader exactly once with mocked original-fs; no real process/network',
  'build05':build,'author_manifest_refs_verified':len(refs)
 },
 'diagnostic_electron_runs_by_author':1,'diagnostic_electron_runs_by_reviewer':0,'productCore_runs':0,'productElectron_runs':0,'actual_product_native_replay_after_repair':False,'formal_increment':0,
 'native_attempt01_followup':{'PRODUCT_PATH_TYPE_root_cause':'CONFIRMED_BY_ISOLATED_REAL_ELECTRON_FS_PROBE','source_repair':'VERIFIED_EXACT_MAIN_INJECTION_AND_NEW_BUILD','product_native_recovery':'NOT_YET_EXECUTED','implicit_Playwright_kill_finding':'Handled by separate driver-v2 source review; oldattempt01 and uncertainty remain immutable'},
 'not_rerun':['Unchanged GoProduct8+helper andPython2 source-bound9361 evidence','ModelStream7+5semantic at5ee with prior delta impact analysis','Metadata status3 targeted fixture fromCP562','FullCLI/renderer/HTTP and prior build03 nonhost consumers'],
 'remaining':['Full productnative attempt using separately bound driver-v2','Native ready/singleton/CLI init/session/persistence/safeclose/reopen acceptance','W18 pagination CONTINUATION_HTTP_403','Busy-close/installer/cleanWindows/upgrade/rollback/uninstall/C57/provider/overnight','All22parents42formal; formalincrement0'],
 'limitations':['Probe executed unchanged build04 helper withphysicalfs injection; build05 productmain itself has not been run','Prior source/build/native failure/rejected cleanup receipts are preserved, not overwritten','Current acceptance is limited source/build/diagnostic evidence, not whole matrix dynamic acceptance'],
 'evidence_refs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence]
}
put('FINAL-REVIEW.json',report);print(json.dumps({'source_build_accepted':True,'sha256':sha(E/'FINAL-REVIEW.json'),'author_refs':len(refs)}))
