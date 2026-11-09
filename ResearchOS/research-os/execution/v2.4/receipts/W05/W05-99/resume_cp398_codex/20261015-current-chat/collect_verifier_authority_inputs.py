import datetime,hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';P=E/'verifier_replacement_package_codex/20261015-current-chat';O=E/'historical_qualification_public_provenance_codex/20261015-current-chat/verifier-authority-inputs01';O.mkdir(exist_ok=False);inputs=[];gaps=[]
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):inputs.append(ref(p));return json.loads(p.read_bytes())
def verify(v):
 p=Path(v['path']);assert ref(p)['sha256']==v['sha256'];assert p.stat().st_size==v['bytes'];return p
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
f=read(P/'FINAL-manifest.json');C=f['source_commit'];assert C=='4f4023c956f84d65743f39ce77d6c8899a21ada1';src=Path(f['source_worktree']);before=read(verify(f['compiler_module_inputs_before']));after=read(verify(f['compiler_module_inputs_after']));assert len(before)==2294 and all(v['sha256']==v['current_sha256'] for v in after)
binary=verify(f['runtime_verifier_binary']);install=read(verify(f['installation_manifest']));assert install['executable_hash']=='sha256:'+ref(binary)['sha256'];assert install['source_commit']==C
rows=[]
for v in before:
 p=Path(v['path'])
 if not p.resolve().is_relative_to(src.resolve()):continue
 rel=p.relative_to(src).as_posix()
 if rel.startswith('apps/runtime-verifier/') or rel.startswith('internal/verifier/'):
  verify(v);b=subprocess.check_output(['git','show',C+':'+rel],cwd=R);assert hashlib.sha256(b).hexdigest()==v['sha256'];rows.append({'path':rel,'source':ref(p),'exact_4f_blob_match':True,'present_in_historical_compile_vector':True})
assert any(v['path']=='apps/runtime-verifier/main_windows.go' for v in rows) and any(v['path']=='internal/verifier/client.go' for v in rows)
builds=[]
for p in sorted(P.glob('*verifier*build*.json')):
 v=read(p)
 if isinstance(v,dict) and isinstance(v.get('argv'),list):builds.append({'ref':ref(p),'invocation':v})
if not builds:gaps.append('NO_MATCHING_VERIFIER_BUILD_INVOCATION_FOUND')
new(O/'01-verifier-package-and-compiled-input-bindings.json',{'source_commit':C,'source_tree':f['source_tree'],'runtime_verifier':ref(binary),'installation_ref':f['installation_manifest'],'installation_public':{k:install.get(k) for k in ['schema','service_id','protocol','executable','executable_hash','source_commit','arguments']},'compile_input_count':len(before),'compile_input_ref':f['compiler_module_inputs_before'],'source_rows':rows,'build_invocations':builds,'limits':['2294-entry vector is the recorded union for both binaries; no new claim that every union entry is a dependency of verifier.','Source-to-binary provenance uses original build/package receipts, not remote attestation or protection against same-SID tampering.','Native original verifier exit/handle result not captured by this collection.'],'gaps':gaps})
A=E/'normal_desktop_verifier_replacement_activation_codex/20261015-current-chat/attempt01';Q=E/'normal_desktop_qualification_diagnosis_independent_codex/20261015-current-chat';reads=[]
for p in [A/'launch.json',A/'05-after-confirm-ui.txt',A/'07-original-request-status-resolved-ui.txt',A/'11-call-observation.json',Q/'01-public-observation.json']:
 v=ref(p);inputs.append(v);reads.append(v)
new(O/'02-historical-response-and-state-inputs.json',{'input_refs':reads,'original_request':'bc269e772ada7e1bce54439fd080550c','run_id':'f3dcb996b2e43cf52cba874be7abfc70','conditional_source_claim_to_review':'Same exact installed verifier starts/handshakes before ExecuteLocalQualification; short verifier token and Job transfer occur only after that synchronous execution and settled review succeed. Historical UNKNOWN/ERROR evidence must independently establish which branch actually returned.','NOT_CLAIMED':['Original verifier numeric exit','Original native wait result','Native closure from PID absence','Unconditional NEVER_JOB_AUTHORIZED acceptance','Credential issuance census or all initialized transitive dependencies proved inert'],'actual_database_opens':0,'private_frame_reads':0})
new(O/'03-input-index.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'refs':inputs,'actual_database_opens':0,'current_os_queries':0,'model_calls':0,'process_signals':0,'private_key_or_credential_content_reads':0})
new(O/'COLLECTION-manifest.json',{'schema':'researchos.verifier-authority-public-inputs.v1','status':'BINDING_INPUTS_ONLY_CONDITIONAL_AUTHORITY_PROOF_NOT_ACCEPTED','files':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'gaps':gaps,'formal_increment':0})
print(json.dumps({'manifest':ref(O/'COLLECTION-manifest.json'),'source_rows':len(rows),'build_invocations':len(builds),'gaps':gaps}))
