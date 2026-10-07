import pathlib,json,hashlib,datetime,subprocess
D=pathlib.Path(__file__).resolve().parent; M=D.parents[6]; W=M/'.local/worktrees/codex-w0599-cli-read-interrupt'
def digest(b): return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes(); return {'path':p.relative_to(M).as_posix(),'sha256':digest(b),'bytes':len(b)}
def save(n,x):
 with (D/n).open('x',encoding='utf8',newline='\n') as f: json.dump(x,f,ensure_ascii=False,indent=2); f.write('\n')
proposal=M/'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_executor_codex/cause-amendment-r266/proposal.json'
assert ref(proposal)['sha256']=='e41f9599f723eb65851860e0fa7365f8b7ed90d5bfab99b1ee0162c69b86c188'
p=json.loads(proposal.read_text(encoding='utf8')); rows=[]; inputs=[]
def read(root,name,group):
 src=root/name; b=src.read_bytes(); snap=D/'public_snapshots'/group/name; snap.parent.mkdir(parents=True,exist_ok=True); snap.write_bytes(b)
 row={'source':str(src),'sha256':digest(b),'bytes':len(b),'snapshot_ref':ref(snap),'actual_read':'Path.read_bytes'}; inputs.append(row); return b
for row in p['source_before']:
 b=read(W,row['path'],'candidate'); assert digest(b)==row['worktree_sha256'],row['path']
 if row['main_sha256'] is not None: assert digest(read(M,row['path'],'main'))==row['main_sha256'],row['path']
for n in ['AGENTS.md','execution/project_identity.json','execution/v2.4/path_ownership.json',str(proposal.relative_to(M)),
 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-read-interrupt-scope-r266/scope_registration.json',
 'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_scope_review_codex/3dd10de3-d92f-4d2c-b31f-f130937dbf95/exact_scope_review.json',
 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-http-scope-06b665dcf2ee4c42bd8a98df3689faf4/scope_registration.json',
 'execution/v2.4/receipts/W05/W05-99/independent_cli_http_source_review/3c350a21-0f55-4821-a414-9b1a8c5c8d01/source_review.json',
 'apps/cli/cli_http_status_test.go','apps/cli/cli_stream_test.go','apps/cli/cli_doctor.go','apps/cli/cli_verbs.go']:
 read(M,n,'main')
raw=subprocess.run(['git','diff','--','apps/cli/cli_v2.go','apps/cli/cli_stream.go','apps/cli/cli_continuation.go'],cwd=W,capture_output=True)
(D/'candidate.diff').write_bytes(raw.stdout); (D/'candidate.diff.stderr').write_bytes(raw.stderr)
save('actual_read_invocation.json',{'actualargv':['git','diff','--','apps/cli/cli_v2.go','apps/cli/cli_stream.go','apps/cli/cli_continuation.go'],'cwd':str(W),'exit':raw.returncode,'stdout_ref':ref(D/'candidate.diff'),'stderr_ref':ref(D/'candidate.diff.stderr')})
after=[{'source':x['source'],'before':x['sha256'],'after':digest(pathlib.Path(x['source']).read_bytes())} for x in inputs]
assert all(x['before']==x['after'] for x in after)
save('read_audit.json',{'inputs':inputs,'after':after,'source_drift':0,'source_edits':0,'tests_run':0,'paid_calls':0,'private_state_reads':0,'review_kind':'independent static scope review, not implementation or source acceptance'})
review={
 'schema':'researchos.cli-read-interrupt-independent-cause-scope.v1','decision':'SOURCE_SCOPE_READY_EXACT4_WITH_MANDATORY_GUARDS','reviewer':'codex:/root/sources_parent_impl','executor':'codex:/root','future_source_verifier':'codex:/root/w05_merge_review','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'gpt-6-astra','reasoning_effort':'high','proposal_ref':ref(proposal),'read_audit_ref':ref(D/'read_audit.json'),
 'exact_paths':p['exact_paths'],'additional_path':'apps/cli/cli_v2.go','additional_path_before_sha256':'072afeb88f1a2f028df1c99b55735b3c583c729e86b2a53b9e60e889e6a2c304',
 'minimum_scope_reason':'Current v2CallTransport loses the actual Do/readErr cause when converting to old public reason/exit triples. cli_stream.go cannot reconstruct that cause by checking its context later. One private detailed transport outcome in the existing file avoids duplicated HTTP/auth/envelope/identity logic. Continuation independently needs its actual per-GET/body cause; same three old wrapper values remain available.',
 'actual_findings':[
  {'id':'L02-CAUSE-01','location':'candidate apps/cli/cli_stream.go:179-181,671-672','fact':'Both paths infer interruption from the final parent context plus broad reason strings; a real unrelated I/O error followed by an accepted signal can become130. Current209-pass candidate does not prove the proposed repair.'},
  {'id':'L02-CAUSE-02','location':'main apps/cli/cli_v2.go:242-260','fact':'Do errors collapse to HOST_UNREACHABLE; read error and oversize collapse to INCOMPLETE_OR_OVERSIZE_REPLY. MainL01 correctly classifies non2xx before body; retain that precedence and nil reply.'},
  {'id':'L02-CAUSE-03','location':'candidate apps/cli/cli_continuation.go:55-72','fact':'Continuation reads body before checking HTTPstatus; it therefore needs an explicit known-non200 terminal guard on cancellation cause. Non200 headers followed by canceled body cannot become local130 simply because errors.Is(readErr,Canceled). This can be done without changing old wrapper reason/exit semantics.'},
  {'id':'L02-CAUSE-04','location':'candidate apps/cli/cli_read_interrupt_test.go:484-504','fact':'Existing protocol-fault control finalizes observer before submitting the later signal. It does not exercise fault→accepted signal→finalization, nor valid reply→accepted signal→finalization. New deterministic barriers must cover those exact orders.'}
 ],
 'mandatory_implementation_guards':[
  'Add only a private detailed outcome (e.g. canceledIO bool or private struct). Set from errors.Is(the actual client.Do error or the actual ReadAll error, context.Canceled) at that operation; never derive from budget.Err, context.Cause, reason prefixes or mere accepted signal after the error.',
  'All original v2Call, v2CallContext and v2CallTransport signatures/triples remain wrappers with original strictIdentity mode,8s timeout,no redirects,request identity/requestLog,envelope/auth,2xx parse/adoption,reason and exit classification. Active run/goal/send/control callers consume the original triples; only status,/status consume detailed cause.',
  'Typed transport non2xx status remains prior to all body parsing/cancellation classification:500..599→1; other non2xx→3; nil reply; no body echo. >1MiB body is terminal oversize even if the same read returns context.Canceled.',
  'Continuation: wrapper Background+8s; status detailed wrapper uses parent+8s. Preserve2MiB aggregate/10pages/100items/cursor/project-session-goal-task-run-context checks and projection. If non200 headers have already been observed, detailed canceledIO must be false even if subsequent body read is canceled; oversize also forces false. Keep original triple behavior for every old caller, including legacy error precedence.',
  'Only accepted registered signal plus actual canceled I/O can replace a failed read with130. DeadlineExceeded without signal remains old timeout; unrelated failure remains original even if signal is accepted before finish. On completed valid read, an accepted signal before the single finalization linearization point may yield130. A typed/protocol/HTTP/domain projection failure is already terminal and cannot be masked.',
  'One observer owns status signal reception. Its finish linearization freezes observed state and joins; no request/goroutine survives return; observer never writes v2Context/requestLog/snapshot/output. Nil/closed/unsupported channels, repeated signals and finalization-after-signal semantics stay explicit; active flows unchanged.',
  'No read-only writer renewal/attach/write/control/send/goal mutation, no retry to obtain a different outcome, no public schema/status enum changes. Do not alter Doctor, old L01 tests, S5 cli_stream_test suffix, frozen contracts or other product paths.'
 ],
 'required_meaningful_controls':[
  'Deterministic actual Do connection failure→accepted signal→finish retains HOST_UNREACHABLE/1; actual200 unexpectedEOF→signal→finish retains old incomplete/1;200 oversize with concurrent cancellation retains oversize/1.',
  'Each continuation stage Goal, Task page, active Run and ContextBundle: true canceled headers/body maps130 only with accepted signal. Real EOF/connection error followed by signal stays old failure. Non200 headers+held/canceled body stays terminal original failure; no HTTP-status-as-interrupt inference.',
  'Actual valid typed identity/result response→synchronized ctx.Done confirmation→finish returns130; invalid identity/schema/malformed/HTTP failure accepted before same barrier retains original failure. Signal after finish cannot change final result. Avoid sleep-only ordering tests.',
  'Existing nil/closed/unsupported/repeated/no-signal timeout and success cases; observer/request join verified, no second command signal stolen. Original read bounds, continuation paging and original active controls remain unchanged.',
  'Rebuild and run hidden-console realWindows CTRL_BREAK compiledCLI case with exact childPID/group and Win32 delivery result; real loopback server observes request.Context.Done, no session.control or execution claim; no secret in output.',
  'After final source freeze rerun focused cause controls, historical L01 HTTPcontrols and fullCLI (including actualSDK old queue/cancel/stream controls where finalcomposition contains them); actual source/tool/env/compiled before-after closure and0skip. Previous209PASS/39050 vector is historical only. Capture actual race-check result if supported; otherwise explicitly retain unavailable tool gate without claiming racePASS. Other-platform compile delta must not conceal preexisting platform failures.'
 ],
 'ownership':{'historical_L01_state':'SOURCE_READY_INTEGRATED_MAIN','historical_owner':'codex:/root','historical_candidate':'b7249b1b1dbd3625a1d8f6b7af845dbfbd20ad8b','historical_source_review_sha256':'005b880289f30e3245c5cb0af096391375b55bf50218a2167dad0ac1b83025fd','required_root_transition':'Before implementation record narrow cli_v2.go construction lease under L02 sameRoot owner, preserve L01 accepted source/ref as immutable history and keep cli_http_status_test.go protected. Originalexact3 protected list must remove only approved transport wrapper/detailed-helper range, not entirefile historical protections. Record pathownership/checkpoint serially; this review does not register or grant the lease.','other_scopes':'No overlap with frozen GoT08 exact3 or JS2/provider9; no transfer of their ownership.'},
 'scope_authorization_boundary':'Root may adopt this scope review, register exact4+mandatory guards and then implement. This is independent scope readiness only; implementation/source acceptance still requires w05_merge_review after new frozen candidate, no formal acceptance increment.',
 'findings_requiring_more_than_exact4':[],'source_ready':False,'formal_acceptance_delta':0,'paid_api_calls':0,'private_data_reads':0}
save('scope_review.json',review)
save('failure_origins.json',{'product_tests_executed':0,'new_test_failure_origins':[],'existing_scope_failure_preserved':'L02 originalexact2 NEEDS_FIX_SCOPE476171e...; current candidate causal masking conditions remain implementation findings, not silently closed.','prior_L01_and_L02_raw_modified':False,'previous209PASS_reused_as_repair_proof':False})
save('handoff.json',{'decision':review['decision'],'scope_review_ref':ref(D/'scope_review.json'),'audit_ref':ref(D/'read_audit.json'),'failure_origins_ref':ref(D/'failure_origins.json'),'next':'Root exact4 lease registration then implementation; independent source review remainsw05_merge_review','no_registration_or_implementation_performed':True})
save('manifest.json',{'files':[ref(f) for f in sorted(D.rglob('*')) if f.is_file()]})
print(json.dumps({'scope_review':ref(D/'scope_review.json'),'handoff':ref(D/'handoff.json'),'manifest':ref(D/'manifest.json'),'read_files':len(inputs)},ensure_ascii=False))
