import pathlib,json,hashlib,subprocess,sys,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); W=R/'.local/worktrees/codex-w0599-host-configuration-handler'; P=R.parent/'ResearchOS_Implementation_Package_v2.4'; N=pathlib.Path(sys.argv[1]); D=R/'execution/v2.4/receipts/W05/W05-99/cli_contract_failure_diagnostic_codex/92448a208996455da289e7682304296a'
def sha(b): return hashlib.sha256(b).hexdigest()
def save(n,o): (N/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inputs=[]
def capture(p,label):
 b=p.read_bytes(); s=N/'snapshots'/label; s.parent.mkdir(parents=True,exist_ok=True); s.write_bytes(b); inputs.append({'path':str(p),'sha256':sha(b),'bytes':len(b),'snapshot':str(s.relative_to(N))}); return b
checks=[]
for p,h in [('diagnostic_matrix.json','3f420a44706c34c8cd07f5c6cd4cf6fdeb5d24271a89881d70e90376b258f6a4'),('product_gaps_and_scope_proposal.json','d171b50d7ec48bd0654b231861ca7a11db3d81c27c46b1a53e9cd4d32b8223e0'),('manifest.json','3646e82eac60c956cebfc9ace91823b852e4a57fa528c4aa4ab20cc078f57766')]:
 b=(D/p).read_bytes(); checks.append({'path':str(D/p),'expected':h,'actual':sha(b),'equal':sha(b)==h})
for p in sorted(D.iterdir()):
 if p.is_file(): capture(p,'diagnostic/'+p.name)
paths={x['path'] for x in json.loads((D/'frozen38-git-binding.json').read_text(encoding='utf-8-sig'))}
paths.update(['apps/cli/cli_verbs.go','apps/cli/cli_v2.go','apps/cli/cli_stream.go','apps/cli/cli_doctor.go','apps/cli/cli_contract.go','apps/cli/cli_stream_test.go','apps/cli/cli_sessions_test.go','tests/runtime/cli_contract/main.go','tests/runtime/cli_contract/v2verbs.go','internal/domain/client_protocol.go','internal/domain/client_protocol_schema.go','internal/domain/client_protocol_journal.go','internal/domain/client_protocol_sessions.go','internal/domain/client_protocol_queue_control.go','internal/domain/client_protocol_control_windows_test.go','internal/domain/durability.go','internal/domain/durability_test.go','internal/domain/durability_session.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_coordinator_windows_test.go','internal/domain/research_driver.go','internal/domain/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.domain.schema.json'])
gitrows=[]
for p in sorted(paths):
 b=capture(W/p,'handler/'+p)
 cp=subprocess.run(['git','show','22752a6a41732c8c158d7d7e1b8932ec958f8cb8:'+p],cwd=R,capture_output=True)
 gitrows.append({'argv':['git','show','22752a6a41732c8c158d7d7e1b8932ec958f8cb8:'+p],'exit_code':cp.returncode,'stderr':cp.stderr.decode('utf-8','replace'),'blob_sha256':sha(cp.stdout),'current_sha256':sha(b),'equal':cp.returncode==0 and cp.stdout==b})
 if (R/p).exists(): capture(R/p,'main/'+p)
for p in ['14_CLI_DESKTOP_PRODUCT.md','22_CLIENT_INTERFACE_DETAILS.md','contracts/product.contract.json','contracts/client.protocol.schema.json','contracts/domain.schema.json','contracts/openapi.json']:
 capture(P/p,'package/'+p)
for p in ['AGENTS.md','execution/project_identity.json']: capture(R/p,'main/'+p)
O=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/contract-native-runner-18fc6ba4559e47e3944c6c7bd0032a8d/run-1f5a7a1af626420792706b764cd6ef37'
for p in ['command.invocation.json','result.json','command.stdout']:
 capture(O/p,'original-run/'+p)
save('input.before.json',inputs);save('git-binding.json',gitrows);save('authority_hash_check.json',checks)
old=json.loads((N/'snapshots/original-run/result.json').read_text(encoding='utf-8-sig'))
mat=json.loads((N/'snapshots/diagnostic/diagnostic_matrix.json').read_text(encoding='utf-8-sig'))
save('capture_facts.json',{'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':len(inputs),'authority_matches':all(x['equal'] for x in checks),'handler_git_matches':all(x['equal'] for x in gitrows),'git_count':len(gitrows),'original_result_keys':list(old),'matrix_keys':list(mat) if isinstance(mat,dict) else 'array'})
print(json.dumps({'namespace':str(N),'inputs':len(inputs),'git_count':len(gitrows),'mismatches':[x for x in gitrows if not x['equal']],'old':old,'matrix_keys':list(mat) if isinstance(mat,dict) else 'array'},ensure_ascii=False))
