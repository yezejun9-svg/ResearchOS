import pathlib,json,subprocess,hashlib,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
R=pathlib.Path.cwd();H=pathlib.Path(__file__).resolve().parent
GO_COMMIT='0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837';JS_COMMIT='6eb611b11364ba25a9560ba54c1b54f3a549eb32';BASE='6e9ac45bff1c76fac37f0462a051412f53ab11d8'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
trace=[];entries=[]
def read(p,kind='main',commit=None):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();dest=H/'snapshots'/kind/p;dest.parent.mkdir(parents=True,exist_ok=True)
 if commit:
  argv=['git','show',commit+':'+p];result=subprocess.run(argv,cwd=R,capture_output=True);data=result.stdout;err=result.stderr;code=result.returncode;source={'commit':commit,'path':p};op={'argv':argv,'cwd':str(R)}
 else:
  source={'path':p};op={'operation':'Path.read_bytes','absolute_path':str(R/p)}
  try:data=(R/p).read_bytes();err=b'';code=0
  except Exception as e:data=b'';err=str(e).encode();code=1
 dest.write_bytes(data);errorpath=H/'raw'/f'{len(trace):03d}.stderr';errorpath.parent.mkdir(exist_ok=True);errorpath.write_bytes(err)
 trace.append({**op,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':code,'stdout_ref':str(dest.relative_to(R)),'stdout_sha256':sha(data),'stderr_ref':str(errorpath.relative_to(R)),'stderr_sha256':sha(err)})
 if code:raise RuntimeError(str(source)+': '+err.decode())
 entries.append({'kind':kind,'source':source,'bytes':len(data),'sha256':sha(data),'snapshot':str(dest.relative_to(R))});return data
scope=['adapters/runtime/mu/worker.mjs','internal/domain/runtime_model.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_model_windows.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_test.go','internal/domain/runtime_provider_binding_windows_test.go','adapters/runtime/mu/worker-provider-binding.test.mjs']
architecture='execution/v2.4/receipts/W05/W05-99/provider_binding_readonly_codex/cfcce581-d452-48c4-8a3e-274044516a28/proposal.json'
review='execution/v2.4/receipts/W05/W05-99/streaming_combined_source_review_codex/f67e12e4-175f-4fd9-9442-8bdf1c0ecf5e/'
mainfiles=['AGENTS.md','execution/project_identity.json','go.mod','go.sum','execution/toolchains/locked.json','execution/v2.4/component_lock.json','third_party/VENDORED_FROM.md','third_party/mu.MANIFEST.json','third_party/mu/package-lock.json','third_party/mu/packages/ai/package.json','third_party/mu/packages/coding-agent/package.json','third_party/mu/packages/ai/src/api/openai-completions.ts','third_party/mu/packages/ai/dist/api/openai-completions.js','third_party/mu/packages/ai/src/types.ts','third_party/mu/packages/ai/src/utils/event-stream.ts','third_party/mu/packages/agent/src/agent.ts','third_party/mu/packages/agent/src/agent-loop.ts','third_party/mu/packages/coding-agent/src/core/agent-session.ts','adapters/runtime/mu/build.mjs','internal/domain/runtime_sessions_windows.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_admission.go','internal/domain/runtime_qualification.go','internal/domain/durability.go','internal/domain/backup.go','internal/domain/backup_command_queue.go','migrations/sqlite/0022_client_command_queue.sql','migrations/sqlite/next_v24_sessions.sql','internal/host/model_credential.go','apps/control/main.go','internal/domain/runtime_model_windows_test.go','internal/domain/runtime_model_verification_test.go','internal/api/contracts/client.protocol.schema.json',architecture,review+'quarantine-alias-probe.stdout',review+'quarantine-alias-probe.invocation.json',review+'sdk_reasoning_alias_probe.stdout',review+'sdk_reasoning_alias_probe.mjs']+scope[:5]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
for p in mainfiles:read(p)
if sha((R/architecture).read_bytes())!='68bd39015ecdb9942a8f5be8167166f608462c442482a1375edd1abac1d2eef4':raise RuntimeError('architecture input changed')
for p in scope[:5]+['internal/domain/runtime_model_stream.go','internal/domain/runtime_model_stream_windows.go','internal/domain/runtime_model_stream_test.go','internal/domain/runtime_model_stream_windows_test.go','internal/domain/backup_command_queue.go','internal/domain/runtime_command_queue_windows.go','adapters/runtime/mu/worker-stream.test.mjs']:
 read(p,'go_candidate',GO_COMMIT)
read(scope[0],'js_candidate',JS_COMMIT)
for p in ['.local/worktrees/v24-continuation/spec/v2.4/22_CLIENT_INTERFACE_DETAILS.md','.local/worktrees/v24-continuation/spec/v2.4/14_RUNTIME_ADAPTER_SPEC.md','.local/worktrees/v24-continuation/spec/v2.4/17_RUNTIME_QUALIFICATION_PROTOCOL.md']:
 if (R/p).exists():read(p,'frozen_spec')
# Do not probe private Host/DB paths or source fixtures; only the pinned tool binaries are hashed.
tools=[]
for p in [R/'.local/tools/go1.27.1/go/bin/go.exe',pathlib.Path('C:/nvm4w/nodejs/node.exe')]:tools.append({'path':str(p),'sha256':sha(p.read_bytes()),'executed':False})
save('read_trace.json',trace);save('inputs.before.json',entries);save('tools.json',tools)
after=[]
for e in entries:
 s=e['source'];b=subprocess.check_output(['git','show',s['commit']+':'+s['path']],cwd=R) if 'commit' in s else (R/s['path']).read_bytes()
 after.append({'kind':e['kind'],'source':s,'sha256':sha(b),'bytes':len(b),'snapshot_equal':b==(R/e['snapshot']).read_bytes()})
save('inputs.after.json',after)
drift=[{'before':a,'after':b} for a,b in zip(entries,after) if a['sha256']!=b['sha256'] or not b['snapshot_equal']]
if drift:raise RuntimeError('input drift '+repr(drift))
save('read_audit.json',{'requested_main':BASE,'actual_head_before':head,'actual_head_after':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip(),'frozen_go':GO_COMMIT,'frozen_js':JS_COMMIT,'input_count':len(entries),'drift':drift,'exact8':[{'path':p,'exists_main':(R/p).exists(),'main_sha256':sha((R/p).read_bytes()) if (R/p).exists() else None} for p in scope],'actual_builds':0,'actual_tests':0,'provider_requests':0,'credential_reads':0,'private_database_reads':0,'source_mutations':0,'canonical_mutations':0,'note':'All subprocesses were git read commands. Source snapshots and raw reading traces are proposal evidence only.'})
print(str(H));print('inputs',len(entries),'drift',len(drift))
