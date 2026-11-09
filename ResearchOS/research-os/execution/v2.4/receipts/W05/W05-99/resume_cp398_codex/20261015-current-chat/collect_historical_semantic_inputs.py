import datetime,hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); E=R/'execution/v2.4/receipts/W05/W05-99'; O=E/'historical_qualification_public_provenance_codex/20261015-current-chat/semantics01'; O.mkdir(exist_ok=False)
C='4f4023c956f84d65743f39ce77d6c8899a21ada1'; inputs=[]
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):inputs.append(ref(p));return json.loads(p.read_bytes())
def verify(v):
 p=Path(v['path']);assert ref(p)['sha256']==v['sha256'];assert p.stat().st_size==v['bytes'];return p
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
P=E/'verifier_replacement_package_codex/20261015-current-chat'; f=read(P/'FINAL-manifest.json');assert f['source_commit']==C
before=read(verify(f['compiler_module_inputs_before']));by={str(Path(v['path']).resolve()).lower():v for v in before};src=Path(f['source_worktree'])
paths=['internal/host/runtime_verifier_process_windows.go','internal/host/desktop_management_windows.go','internal/domain/runtime_qualification_execution_windows.go','ops/experiment_sandbox/async_windows.go','ops/experiment_sandbox/recovery_windows.go']
rows=[]
for rel in paths:
 p=src/rel;v=by[str(p.resolve()).lower()];verify(v);b=subprocess.check_output(['git','show',C+':'+rel],cwd=R);assert hashlib.sha256(b).hexdigest()==v['sha256'];rows.append({'path':rel,'source':ref(p),'present_in_historical_compile_vector':True,'exact_4f_blob_match':True})
new(O/'01-extra-compiled-source-bindings.json',{'source_commit':C,'compile_vector_ref':f['compiler_module_inputs_before'],'compile_input_count':len(before),'extra_sources':rows,'semantic_acceptance':False})
bref=read(E/'historical_qualification_public_provenance_codex/20261015-current-chat/attempt02/03-exact-staged-worker-bindings.json')['bridge_ref']; jp=verify(bref);j=read(jp);m=j['manifest'];n=j['sandbox_receipt']
assert j['dispatch_key']=='705b11ec99044fef19e85f57e2d2b712' and m['run_id']=='f3dcb996b2e43cf52cba874be7abfc70';assert ref(jp)==bref
new(O/'02-public-bridge-structural-metadata.json',{'bridge_ref':bref,'subject':{k:m.get(k) for k in ['project_id','task_id','run_id','runtime_id','epoch']},'artifacts':j.get('artifacts'),'artifacts_count':len(j.get('artifacts',[])),'queue_required':j.get('queue_required'),'manifest_queue_control_present':'queue_control' in m,'native_capabilities':n.get('capabilities'),'native_identity':j.get('identity'),'native_receipt_public_fields':{k:n.get(k) for k in ['pid','process_created_ns','job','profile','appcontainer_sid','executable','args','directory','capabilities','exit_code','children_stopped','job_total_processes','timed_out','streams_drained','cleanup_complete','output_copied','started_at','finished_at']},'raw_private_frame_or_credential_content_exported':False,'semantic_acceptance':False})
new(O/'03-verifier-closure-source-boundary.json',{'schema':'researchos.source-derived-closure-inputs.v1','source_commit':C,'compiled_source_refs':rows[:2],'source_chain':[{'path':'internal/host/desktop_management_windows.go','line':256,'fact':'Synchronous return of host.QualifyLocalRuntime within bounded management dispatch'},{'path':'internal/host/runtime_qualification_windows.go','line':184,'fact':'defer process.close after successful startRuntimeVerifier; before return to management dispatcher'},{'path':'internal/host/runtime_verifier_process_windows.go','line':219,'fact':'close cancels, closes pipes, calls original cmd.Wait if not waited, then sets waited; Wait error ignored'}],'limits':['No captured original verifier numeric exit status or independent original-handle wait receipt is added.','Source fact that cmd.Wait was called is distinct from observed native handle wait result; ignored Wait errors require independent semantic decision.','No current PID-absence, fresh fixture, currentOS handle observation or model call substitutes for historical closure.','STOP operational eligibility and C NO_EFFECT historical proof acceptance remain separate gates.'],'status':'INPUTS_FOR_INDEPENDENT_REVIEW_NOT_CLOSURE_ACCEPTANCE'})
new(O/'04-input-index.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_refs':inputs,'actual_database_opens':0,'current_os_queries':0,'process_signals':0,'model_or_provider_calls':0,'product_or_source_writes':0})
new(O/'COLLECTION-manifest.json',{'schema':'researchos.historical-semantic-supplement.v1','status':'PUBLIC_INPUTS_FROZEN_NO_SEMANTIC_OR_NATIVE_CLOSURE_ACCEPTANCE','files':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'formal_increment':0})
print(json.dumps({'manifest':ref(O/'COLLECTION-manifest.json'),'extra_sources':len(rows),'artifacts_count':len(j.get('artifacts',[])),'queue_required':j.get('queue_required'),'capabilities':n.get('capabilities')}))
