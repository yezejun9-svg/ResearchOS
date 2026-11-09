import base64,ctypes,datetime,hashlib,json,subprocess
from ctypes import wintypes
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';O=E/'historical_qualification_public_provenance_codex/20261015-current-chat';O.mkdir(parents=True,exist_ok=False)
P=E/'verifier_replacement_package_codex/20261015-current-chat';A=E/'normal_desktop_verifier_replacement_activation_codex/20261015-current-chat/attempt01';D=E/'normal_desktop_qualification_diagnosis_independent_codex/20261015-current-chat';C='4f4023c956f84d65743f39ce77d6c8899a21ada1';refs=[];gaps=[]
def read(p):
 b=p.read_bytes();refs.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)});return json.loads(b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def verify(v):
 p=Path(v['path']);assert sha(p)==v['sha256'];assert p.stat().st_size==v['bytes'];return p
def go_bytes(v):
 return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e').replace('\u2028','\\u2028').replace('\u2029','\\u2029').encode()
def digest(v):return 'sha256:'+hashlib.sha256(go_bytes(v)).hexdigest()
def native_process(pid):
 k=ctypes.WinDLL('kernel32',use_last_error=True);a=ctypes.WinDLL('advapi32',use_last_error=True)
 k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.CloseHandle.argtypes=[wintypes.HANDLE];k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4;k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)];k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];k.WaitForSingleObject.restype=wintypes.DWORD
 a.OpenProcessToken.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)];a.GetTokenInformation.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)];a.ConvertSidToStringSidW.argtypes=[ctypes.c_void_p,ctypes.POINTER(wintypes.LPWSTR)];k.LocalFree.argtypes=[ctypes.c_void_p]
 h=k.OpenProcess(0x1000|0x100000,False,pid)
 if not h:raise ctypes.WinError(ctypes.get_last_error())
 token=wintypes.HANDLE();sidtext=wintypes.LPWSTR()
 try:
  c,x,t,u=[wintypes.FILETIME() for _ in range(4)]
  if not k.GetProcessTimes(h,ctypes.byref(c),ctypes.byref(x),ctypes.byref(t),ctypes.byref(u)):raise ctypes.WinError(ctypes.get_last_error())
  n=wintypes.DWORD(32768);buf=ctypes.create_unicode_buffer(n.value)
  if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):raise ctypes.WinError(ctypes.get_last_error())
  if not a.OpenProcessToken(h,8,ctypes.byref(token)):raise ctypes.WinError(ctypes.get_last_error())
  size=wintypes.DWORD();a.GetTokenInformation(token,1,None,0,ctypes.byref(size));tb=ctypes.create_string_buffer(size.value)
  if not a.GetTokenInformation(token,1,tb,size.value,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
  sid=ctypes.cast(tb,ctypes.POINTER(ctypes.c_void_p))[0]
  if not a.ConvertSidToStringSidW(sid,ctypes.byref(sidtext)):raise ctypes.WinError(ctypes.get_last_error())
  ticks=(c.dwHighDateTime<<32)|c.dwLowDateTime;unix_ns=(ticks-116444736000000000)*100;image=Path(buf.value)
  before=image.stat();image_hash=sha(image);after=image.stat();assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
  return {'pid':pid,'created_filetime_ticks':str(ticks),'created_unix_ns':str(unix_ns),'created_utc':(datetime.datetime(1970,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(microseconds=unix_ns//1000)).isoformat(),'image':str(image),'image_sha256':image_hash,'image_bytes':before.st_size,'owner_sid':sidtext.value,'wait_original_handle':k.WaitForSingleObject(h,0),'same_handle_identity_and_wait':True,'access':'PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE; TOKEN_QUERY','signal_or_terminate':False,'handle_closed_in_finally':True}
 finally:
  if sidtext:k.LocalFree(ctypes.cast(sidtext,ctypes.c_void_p))
  if token:k.CloseHandle(token)
  k.CloseHandle(h)
f=read(P/'FINAL-manifest.json');assert f['source_commit']==C and f['core_binary']['sha256']=='c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24';verify(f['core_binary'])
build=read(verify(f['composition']));br=read(verify(build['build']));before=read(verify(f['compiler_module_inputs_before']));after=read(verify(f['compiler_module_inputs_after']));assert len(before)==br['input_count']==2294;assert [dict((k,v) for k,v in x.items() if k!='current_sha256') for x in after]==before and all(x['sha256']==x['current_sha256'] for x in after)
critical=['internal/domain/runtime_broker_windows.go','internal/domain/runtime_model.go','internal/domain/runtime_tools_windows.go','internal/domain/runtime_dispatch.go','internal/domain/runtime_command_queue_windows.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_qualification_confirmation_windows.go','internal/host/runtime_qualification_windows.go','adapters/runtime/bridge_windows.go','adapters/runtime/bridge_program.go','ops/experiment_sandbox/sandbox_windows.go','internal/store/sqlite.go','apps/control/main.go']
src=Path(f['source_worktree']);by={str(Path(v['path']).resolve()).lower():v for v in before};critical_rows=[]
for rel in critical:
 p=src/rel;v=by[str(p.resolve()).lower()];verify(v);raw=subprocess.check_output(['git','show',C+':'+rel],cwd=R);assert hashlib.sha256(raw).hexdigest()==v['sha256'];critical_rows.append({'path':rel,'source':ref(p),'exact_commit_blob_match':True,'present_in_historical_compile_vector':True})
all_drift=[]
for v in before:
 p=Path(v['path'])
 if not p.is_file() or sha(p)!=v['sha256']:all_drift.append(v['path'])
new(O/'01-core-build-chain.json',{'schema':'researchos.historical-core-build-provenance.v1','source_commit':C,'source_tree':f['source_tree'],'core':f['core_binary'],'build_result_ref':ref(verify(build['build'])),'build_invocation':read(P/'control-build.json'),'packaged_buildinfo_invocation':read(P/'control-packaged-buildinfo.json'),'packaged_buildinfo_stdout':ref(P/'control-packaged-buildinfo.stdout'),'compile_input_count':2294,'before_after_inputs_equal':True,'fresh_compile_input_drift':all_drift,'critical_sources':critical_rows,'protected_holdout':False,'trust_basis':'Existing append-only local build/package receipts plus independently reviewed package; not remote attestation or protection against same-user tampering'})
core=native_process(54076);hist=read(A/'09-process-identities.json');hc=next(x for x in hist if x['ProcessId']==54076);assert Path(core['image']).resolve()==Path(hc['ExecutablePath']).resolve() and core['image_sha256']==f['core_binary']['sha256'] and datetime.datetime.fromisoformat(core['created_utc'])==datetime.datetime.fromisoformat(hc['CreationDate']) and core['wait_original_handle']==258
new(O/'02-current-core-to-historical-identity.json',{'current_native_observation':core,'historical_snapshot':hc,'snapshot_ref':ref(A/'09-process-identities.json'),'launch_ref':ref(A/'launch.json'),'same_creation_path_and_existing_package_digest':True,'meaning':'Current live Core has the same creation identity as the already recorded historical run observer; no stop or process-memory read'})
ob=read(D/'01-public-observation.json');jp=Path(ob['source_refs'][0]['path']);assert sha(jp)==ob['source_refs'][0]['sha256'];j=read(jp);m=j['manifest'];ad=m['admission'];profile=ad['profile'];assert digest(m)==j['manifest_hash']==ob['manifest_hash']
dispatch=jp.parent;allowed=['worker.exe','mu-worker.mjs','worker.json','request.json'];staged=[]
for name in allowed:
 p=dispatch/'input'/name
 if p.is_file():staged.append({'name':name,**ref(p)})
 else:gaps.append({'kind':'STAGED_INPUT_MISSING','name':name})
inventory=read(verify(f['package_full_inventory']));rows={x['path']:x for x in inventory['files']};runtime='apps/desktop/resources/control/runtime/';bundlemeta=read(Path(inventory['package_root'])/(runtime+'mu-worker.mjs.build.json'))
for name in ['node.exe','mu-worker.mjs','mu-worker.mjs.build.json']:verify({'path':str(Path(inventory['package_root'])/(runtime+name)),**{k:rows[runtime+name][k] for k in ['sha256','bytes']}})
assert profile['build_hash']=='sha256:'+rows[runtime+'node.exe']['sha256'] and profile['bundle_hash']=='sha256:'+rows[runtime+'mu-worker.mjs']['sha256']
if len(staged)==4:
 sr={x['name']:x for x in staged};assert 'sha256:'+sr['worker.exe']['sha256']==profile['build_hash'];assert 'sha256:'+sr['mu-worker.mjs']['sha256']==profile['bundle_hash'];assert (dispatch/'input/worker.json').read_bytes()==go_bytes(profile['model_config']);assert digest(read(dispatch/'input/request.json'))==j['manifest_hash']
frames=[]
for line in base64.b64decode(j['sandbox_receipt']['stdout']).splitlines():
 v=json.loads(line);frames.append({k:v.get(k) for k in ['sequence','type','key','route','capability']})
new(O/'03-exact-staged-worker-bindings.json',{'bridge_ref':ref(jp),'manifest_hash':j['manifest_hash'],'project_id':m['project_id'],'task_id':m['task_id'],'run_id':m['run_id'],'epoch':m['epoch'],'dispatch_key':j['dispatch_key'],'manifest_canonical_hash_match':True,'profile_identity':{k:profile.get(k) for k in ['backend','sandbox','build_hash','bundle_hash','adapter_revision','command_id','argv']},'model_config_hash':digest(profile['model_config']),'model_qualification':profile['model_qualification'],'staged_files':staged,'package_worker_assets':[rows[runtime+n] for n in ['node.exe','mu-worker.mjs','mu-worker.mjs.build.json']],'bundle_build_metadata':bundlemeta,'frame_metadata':frames,'stdout_sha256':hashlib.sha256(base64.b64decode(j['sandbox_receipt']['stdout'])).hexdigest(),'native_identity':j['identity'],'native_closure':{k:j['sandbox_receipt'].get(k) for k in ['pid','process_created_ns','job','exit_code','children_stopped','job_total_processes','timed_out','streams_drained','cleanup_complete','output_copied','started_at','finished_at']},'observer_reads_private_credentials':False,'source_or_product_writes':False})
chain=[];cp=P/'composition.json';seen=set()
for _ in range(16):
 if str(cp) in seen:raise RuntimeError('composition cycle')
 seen.add(str(cp));v=read(cp);chain.append({'ref':ref(cp),**{k:v.get(k) for k in ['schema','source_commit','source_tree','core_source_commit','mu_source_commit']}})
 prior=v.get('old_composition')
 if not prior:break
 cp=verify(prior);assert cp.resolve().is_relative_to(E.resolve())
new(O/'04-package-composition-chain.json',{'chain':chain,'loop_limit':16,'stopped_without_old_composition':not bool(v.get('old_composition')),'mu_bundle_build_metadata_source_hash':bundlemeta['source_sha256'],'mu_commit':bundlemeta['mu_commit']})
old_mu=subprocess.run(['git','show',bundlemeta['mu_commit']+':adapters/runtime/mu/worker.mjs'],cwd=R,capture_output=True)
new(O/'05-mu-source-commit-probe.json',{'argv':['git','show',bundlemeta['mu_commit']+':adapters/runtime/mu/worker.mjs'],'native_exit':old_mu.returncode,'stdout_bytes':len(old_mu.stdout),'stdout_sha256':hashlib.sha256(old_mu.stdout).hexdigest(),'expected_source_sha256':bundlemeta['source_sha256'],'source_match':old_mu.returncode==0 and hashlib.sha256(old_mu.stdout).hexdigest()==bundlemeta['source_sha256'],'stderr_utf8':old_mu.stderr.decode('utf8','replace')})
if old_mu.returncode!=0 or hashlib.sha256(old_mu.stdout).hexdigest()!=bundlemeta['source_sha256']:gaps.append({'kind':'MU_SOURCE_COMMIT_NOT_MATCHING_BUILD_METADATA','native_exit':old_mu.returncode})
new(O/'06-input-ref-index.json',{'refs':refs,'public_receipt_reads_only':True,'actual_database_opened':False,'private_keys_or_credentials_read':False,'model_calls':0,'provider_calls':0,'signals':0,'terminations':0,'gaps':gaps})
new(O/'COLLECTION-manifest.json',{'schema':'researchos.historical-public-provenance-collection.v1','status':'COLLECTED_FOR_INDEPENDENT_SEMANTIC_REVIEW_NOT_CLOSURE_ACCEPTANCE','files':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'fresh_compile_input_drift':all_drift,'gaps':gaps,'formal_increment':0})
print(json.dumps({'manifest':ref(O/'COLLECTION-manifest.json'),'gaps':gaps,'compile_inputs':2294,'drift':len(all_drift),'staged_count':len(staged),'composition_depth':len(chain)}))
