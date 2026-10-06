"""Read only ResearchOS source/public receipts and process credential fingerprints."""
from pathlib import Path
import hashlib,json,os,re,subprocess
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
SPEC=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':digest(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=[MAIN/p for p in ['AGENTS.md','apps/cli/main.go','apps/cli/cli_verbs.go','apps/cli/cli_stream.go','apps/cli/cli_contract.go','apps/cli/cli_v2.go','apps/cli/cli_queue_integration_windows_test.go','adapters/runtime/mu/worker.mjs','adapters/runtime/mu/worker-control.test.mjs','internal/domain/runtime_model_windows.go','internal/domain/runtime_session_events_windows.go','execution/v2.4/commands.json','execution/v2.4/route.json','tests/runtime/check/legacy.go','ops/ci/runtime.py','execution/v2.4/receipts/W05/W05-99/integration_codex/source_slice1.json','execution/v2.4/receipts/W05/W05-99/integration_codex/s4_cli_goal_source_scope_codex.json','execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_final_source_review.json','execution/v2.4/receipts/W05/W05-99/resource_readiness_codex/current_resource_delta.json','execution/v2.4/receipts/W14/W14-01/live_qualification_blocked_codex.json']]
paths += [SPEC/p for p in ['tasks/steps/W05-99.md','contracts/tasks.json','contracts/acceptance.json','contracts/harness.contract.json','contracts/product.contract.json','contracts/delivery.contract.json','14_CLI_DESKTOP_PRODUCT.md','17_USER_JOURNEYS_AND_VALUE.md','19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md']]
before=[ref(p) for p in paths]
write('inputs-before.json',before)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN).decode().strip()
(OUT/'main-tracked-status.raw').write_bytes(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=MAIN))
tasks=read(SPEC/'contracts/tasks.json');w05=next(x for x in tasks['tasks'] if x['task_id']=='W05')
acceptance=next(x for x in read(SPEC/'contracts/acceptance.json')['cases'] if x['id']=='A04')
product=read(SPEC/'contracts/product.contract.json');delivery=read(SPEC/'contracts/delivery.contract.json')
write('frozen-requirements.json',{'W05':w05,'A04':acceptance,'CLI':product['cli'],'P01':[x for x in product['capabilities'] if x.get('id')=='P01'],'U02':[x for x in delivery['capabilities'] if x.get('id')=='U02'],'first_real_coding_task_policy':delivery['first_real_coding_task_policy']})
commands=read(MAIN/'execution/v2.4/commands.json')['commands']
binding=commands['test.runtime']
write('registered-entry-facts.json',{'test.runtime':binding,'missing_required_selectors':[x for x in ('W05-H08','W05-P01','W05-U02') if x not in binding['selectors']['check_id']],
 'forwarding':{'file_ref':ref(MAIN/'tests/runtime/check/legacy.go'),'actual_argv_literal':['python','-X','utf8','ops/ci/runtime.py','--mode','fixture']},
 'current_worker_command_states':{k:v.get('state') for k,v in commands.items() if k.startswith('fork.')},
 'G02_A04_result_from_static_path':'ops/ci/runtime.py parser refuses fixture mode unless check W05-G01 with no case; G02/A04 cannot enter LIVE on registered path',
 'action':'Root must separately review/register exact parent handlers; CLI-only work cannot close this gate'})
base=MAIN/'execution/v2.4/receipts/W05/W05-99/queue_integration_codex';test_records={}
for kind in ('cli','sdk'):
 b=base/kind;result=read(b/'result.json');source=read(b/'inputs-before.json');after=read(b/'inputs-after.json')
 for k in ('stdout','stderr'):
  assert digest(MAIN/result[k]['path'])==result[k]['sha256']
 mismatches=[x['path'] for x in source if not (MAIN/x['path']).is_file() or digest(MAIN/x['path'])!=x['sha256']]
 item={'result_ref':ref(b/'result.json'),'command_ref':ref(b/'command.json'),'actual_exit':result['exit_code'],'original_source_before_after_equal':source==after,'current_source_mismatches':mismatches,'measurement_mode':'FIXTURE_NOT_LIVE','raw_refs':[result['stdout'],result['stderr']]}
 if kind=='cli':
  events=[json.loads(x) for x in (b/'stdout.raw').read_text(encoding='utf-8').splitlines() if x.strip()]
  item['test_top_level_pass']=sum(x.get('Action')=='pass' and 'Test' in x and '/' not in x['Test'] for x in events)
  item['test_pass_including_subtests']=len(result['test_events']['pass']);item['fail']=len(result['test_events']['fail']);item['skip']=len(result['test_events']['skip'])
 else:item['node_counts']=result['node_counts']
 test_records[kind]=item
write('existing-test-qualification.json',test_records)
old_resource=read(MAIN/'execution/v2.4/receipts/W05/W05-99/resource_readiness_codex/current_resource_delta.json')
blocked=read(MAIN/'execution/v2.4/receipts/W14/W14-01/live_qualification_blocked_codex.json')
# Do not inspect credential files, private databases, or user configuration stores.
credential_names=[n for n in os.environ if re.fullmatch(r'(DEEPSEEK|OPENAI|ANTHROPIC|AZURE_OPENAI|RESEARCHOS|MU|PI)_[A-Z0-9_]*(API_KEY|TOKEN|CREDENTIAL|SECRET)',n)]
fingerprints=[{'name':n,'present_nonempty':bool(os.environ[n]),'sha256_utf8':hashlib.sha256(os.environ[n].encode('utf-8')).hexdigest() if os.environ[n] else None} for n in sorted(credential_names)]
write('resource-readiness.json',{'scope':'process variable names and irreversible SHA256 only; no credential values, private DB, DPAPI record, other project, or user chat profile read',
 'selected_route':read(MAIN/'execution/v2.4/route.json')['selected_route'],'existing_authorized_profile_from_retained_receipt':old_resource['route']['observed_old_w14_profile'],
 'credential_process_fingerprints':fingerprints,'comparison_to_old_401_fingerprint':'INDETERMINATE: original inference and later 401 receipt do not bind an exposed credential fingerprint; older local review reported same imported material but withheld digest. No newly different authorized resource proved.',
 'old_live_run_id':blocked['run_id'],'old_live_inference_attempts':blocked['inference_attempts'],'old_live_retries':blocked['automatic_retries'],
 'old_live_effect_last_state':blocked['effects'][-1]['state'],'later_readonly_catalog_status':blocked['read_only_diagnostic']['http_status'],
 'new_network_calls':0,'new_model_calls':0,'changed_resource_candidate':None,'old_UNKNOWN_replayed':False,
 'live_required':['Authorized fixed model endpoint plus usable scoped credential and bounded budget','Qualification on actual selected Mu worker, real model read/edit/test/Goal task and captured costs/usage','Fresh issue baseline frozen immediately before product-agent demonstration','Independent acceptance and registered LIVE parent handlers'],
 'resource_alone_does_not_close':['TUI missing client behavior','H08/P01/U02 selector and parent handler implementation','Q10 current integrated regression']})
review=read(MAIN/'execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_final_source_review.json')
write('Q10-retained-status.json',{'original_ref':ref(MAIN/'execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_final_source_review.json'),
 'Q10':[{k:v for k,v in x.items() if k in ('id','verdict','conclusion')} for x in review['Q01_Q10'] if x['id']=='Q10'],
 'interpretation':'Historical Q10 NOT_CLOSED is not rewritten. Root has since integrated a narrow W17 historical14 fixture fix; that source change is not proof that the complete current integrated Q10 regression passed.'})
quotes=[]
for p,needles in [(SPEC/'14_CLI_DESKTOP_PRODUCT.md',['交互TUI','长输出可展开/保存','检查能力/模型']), (SPEC/'17_USER_JOURNEYS_AND_VALUE.md',['工具折叠/展开','STEER/FOLLOW_UP']), (MAIN/'apps/cli/cli_verbs.go',['func cliInteractive','bufio.NewScanner','strings.HasSuffix(line','out, code := runCLIVerb']), (MAIN/'apps/cli/cli_stream.go',['signals, outJSON','f.options.emit(map','outJSON(out)']), (MAIN/'apps/cli/main.go',['case "doctor"','hostGet(d.URL + "/healthz")']), (MAIN/'internal/domain/runtime_model_windows.go',['io.ReadAll']), (MAIN/'adapters/runtime/mu/worker.mjs',['await protocol.effect("MODEL"','await session.prompt','actual_cost: null'])]:
 for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if any(needle in line for needle in needles):quotes.append({'file_ref':ref(p),'line':n,'text':line})
write('contract-and-source-locators.json',quotes)
after=[ref(p) for p in paths];write('inputs-after.json',after);assert before==after
write('audit-summary.json',{'status':'READ_ONLY_READINESS_ASSESSMENT','actor':'codex:/root/sources_parent_impl','created_at':datetime.now(timezone.utc).isoformat(),'main_head':head,'sources_and_frozen_inputs_unchanged':True,'tests_rerun':False,'network_calls':0,'model_calls':0,'private_databases_read':False,'production_source_edits':0,'shared_metadata_edits':0,'formal_acceptances_created':0,
 'findings':['Required interactive TUI presentation remains missing despite functional line-mode interaction and S6 durable controls','Doctor only probes healthz; host.status capability/model diagnostics remain a CLI-only source opportunity','Selected broker currently buffers complete SSE before Mu reads it: true user-visible token deltas cannot be delivered by CLI rendering alone','Registered G02/A04 route is fixture-only/refused, H08/P01/U02 selectors absent','Q10 full integrated gate is still unproven; historical qualification is not current formal qualification','No demonstrably changed usable authorized provider credential established; do not retry old UNKNOWN/401'],
 'existing_cli_tests':test_records['cli'],'existing_sdk_tests':test_records['sdk'],
 'safe_next_minimal_cli_scope':{'proposal_only':True,'existing':['apps/cli/main.go'],'new':['apps/cli/cli_doctor.go','apps/cli/cli_doctor_test.go'],'behavior':'Use existing authenticated v2 host.status through current discovery/context helpers; expose required capability/model/config diagnostics truthfully, keep JSONL + exact exit codes and redact secrets; no provider.probe or model request. Preserve current health diagnostics as compatibility evidence.','contract_basis':['product.contract.json cli.commands[id=doctor].local_operations=host.status','14 section4 doctor/config checks capability/model/local host'],'excluded':['domain','S6','commands registry','model route/fixed model','provider network','formal acceptance']},
 'subsequent_TUI_source_slice':{'proposal_only':True,'existing':['apps/cli/cli_verbs.go','apps/cli/cli_stream.go','apps/cli/cli_contract.go','apps/cli/cli_stream_test.go'],'new':['apps/cli/cli_interactive_view.go','apps/cli/cli_interactive_view_test.go'],'bounded_behavior':'TTY presentation of actual event IDs/state, tool output fold/expand/save and safe multiline/paste input, reuse existing follower emit callback and single writer; preserve non-TTY JSONL and S6 queue semantics. Reuse audit of pinned Mu terminal components required before choosing editor implementation; renderer-only slice must not claim full TUI or real token streaming.','remaining_after_slice':['True upstream incremental token path','Installed real Windows keyboard/paste/resize and first-use journey','Real fixed-provider P01/U02 task','H08 qualification and parent gate bindings']}})
print(json.dumps({'output':str(OUT),'summary_ref':ref(OUT/'audit-summary.json'),'credential_names_only':[x['name'] for x in fingerprints],'CLI_top_level':test_records['cli']['test_top_level_pass'],'CLI_including_subtests':test_records['cli']['test_pass_including_subtests']},ensure_ascii=False))
