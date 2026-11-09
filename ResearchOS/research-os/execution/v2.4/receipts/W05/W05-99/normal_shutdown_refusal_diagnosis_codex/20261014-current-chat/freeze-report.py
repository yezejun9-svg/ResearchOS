import pathlib,json,hashlib,datetime
E=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((E/'shutdown-source-binding.json').read_text())
assert all(x.get('read_current_combined_source_same_bytes',x.get('installed_package_matches_commit')) for x in source)
proc=json.loads((E/'readonly-guard.process.json').read_text());out=(E/'readonly-guard.stdout.raw').read_text()
assert proc['native_exit']==0 and 'READ_ONLY_ORIGINAL_PRODUCTION_ACCOUNTING_GUARD_PASSES' in out and 'GUARD_REJECTS' not in out
state=json.loads((E/'db-readonly-state.json').read_text());assert state['counters']=={'unresolved_commands':0,'active_runs':0,'unresolved_effects':0,'unresolved_dispatches':0,'reservations':1}
prior=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry07_codex/20261014-current-chat/electron-process-wait.observed.json')
report={
 'schema':'researchos.shutdown-refusal-independent-diagnosis/1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'verdict':'READ_ONLY_DURABLE_GUARD_PASSES_ONE_NORMAL_RETRY_SUPPORTED','first_refusal_cause':'NOT_OBSERVED','first_private_error_frame':'NOT_OBSERVED',
 'scope':{'desktop_pid':65728,'core_pid':61952,'old_core_commit':'b955c8665281193d5cbf90a146f936c9212c7940','desktop_commit':'5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456','old_package':'normal-status-combined-5ddc0abb-20261014','original_run':'58293e8f129a4dd00be67e35019004fc'},
 'durable_observation':{'database_access':'SQLite file URI mode=ro + query_only=ON; no UPDATE/INSERT/DELETE; original production completedLocalUnknownCosts uses read-only BEGIN/ROLLBACK','counters':state['counters'],'run_status':'SETTLED','children_stopped':True,'queue_empty':True,'latest_effect_state':'CONFIRMED','ledger_operation':'UNKNOWN','money':None,'reservation':None,'production_guard_marker':'READ_ONLY_ORIGINAL_PRODUCTION_ACCOUNTING_GUARD_PASSES','native_exit':0,'test_seconds':proc['seconds'],'test_is_diagnostic':'Native test logs PASS/REJECTS rather than failing on domain rejection; report independently requires exact PASSES marker and absence of REJECTS marker.','in_memory_active_workers':'NOT_OBSERVED'},
 'source_findings':[
 {'claim':'Coding PREPARE freezer failure releases scanMu via defer, returns before confirmation INSERT, does not set qualificationActive or ManagedStartupHold.','source':'old-core-source/internal/domain/client_runtime_coding_windows.go','lines':[179,180,208,211,222]},
 {'claim':'Offline runtime preparation releases scanMu via defer and does not alter qualificationActive or startup hold in this wrapper.','source':'old-core-source/internal/domain/runtime_qualification_confirmation_windows.go','lines':[186,195]},
 {'claim':'drainGate Quiesce unlocks mutex on every return; in-flight write refusal restores quiesced=false; already-quiesced refusal does not clear pre-existing state.','source':'old-core-source/apps/control/drain_windows.go','lines':[56,69]},
 {'claim':'After HTTP gate is acquired, any coordinator shutdown error calls gate.Resume before returning; stop() runs only after both accept.','source':'old-core-source/apps/control/main.go','lines':[317,326]},
 {'claim':'Coordinator scan mutex always unlocks after successful acquisition; TryLock failure performs no state mutation. Scan/startup/already-quiesced failures preserve previous state.','source':'old-core-source/internal/domain/runtime_drain_windows.go','lines':[57,68]},
 {'claim':'Business-busy path clears quiesced and restores intake respecting prior managed fences. DB observation error clears quiesced but intentionally keeps intake closed. No claim that every error restores acceptance.','source':'old-core-source/internal/domain/runtime_drain_windows.go','lines':[75,98,116,123]},
 {'claim':'Serve calls Scan every second, using the same mutex; scan-busy is a possible transient reason but is not the observed first-refusal cause.','source':'old-core-source/internal/domain/runtime_coordinator_windows.go','lines':[227,248]},
 {'claim':'Host returns bounded validated ERROR MANAGEMENT_REJECTED with concrete message; Desktop clears pending for valid ERROR then replaces message with SHUTDOWN_REFUSED. shutdownAccepted remains false until ACCEPTED.','source':'installed-desktop-source/apps/desktop/main/lib/desktop-management.js','lines':[357,375,764,770]}
 ],
 'recovery':{'supported_action':'Root may dismiss original dialog, ensure no new pending operation, then send one ordinary WM_CLOSE using existing product shutdown path.','retry_loop':False,'guard_bypass':False,'if_refused_again':'Preserve refusal and stop repeated attempts; investigate product-level bounded cause visibility under separate source authorization.','success_interpretation':'Fresh normal-exit evidence only; never infer original rejection cause from later success.','root_retry_execution':'OWNED_BY_ROOT_NOT_PERFORMED_BY_REVIEWER'},
 'prior_close_receipt':{'path':str(prior),'sha256':sha(prior),'observed':json.loads(prior.read_text()),'interpretation':'Prior Electron numeric wait 0 is supporting history only; does not prove current Core exit or initial refusal reason.'},
 'unobserved':['original private SHUTDOWN ERROR text','instantaneous HTTP in-flight count at first close','instantaneous scanMu ownership','instantaneous qualificationActive and ManagedStartupHold','instantaneous active map and startupComplete'],
 'preserved_failures':[{'file':'initial-observer-setup-error.json','reason':'Initial metadata query used nonexistent namespace column; corrected to operation without writes.'}],
 'boundaries':{'source_changes':False,'package_changes':False,'database_writes':False,'process_kill_or_signal':False,'private_pipe_interception':False,'api_calls':False,'gui_actions':False,'new_model_calls':0,'new_tool_dispatches':0,'root_canon_changes':False,'formal_increment':0,'formal_accepted_cases':0,'parent_tasks_open':22},
 'evidence_source_bindings':source}
(E/'FINAL-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
manifest={'schema':'researchos.evidence-manifest/1','files':[{'path':p.relative_to(E).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']}
(E/'FINAL-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for p in [E/'FINAL-report.json',E/'FINAL-manifest.json']: print(p.name,sha(p))
print('members',len(manifest['files']))
