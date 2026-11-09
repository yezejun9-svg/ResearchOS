from pathlib import Path
import hashlib,json,subprocess

root=Path(__file__).resolve().parent
repo=root.parents[5]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git',*args],cwd=repo).decode('utf-8').strip()
def write(name,value): (root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

head=git('rev-parse','HEAD')
paths=[v['path'] for v in read(root/'source_before.json')['inputs']]
paths+=['apps/cli/cli_stream_test.go','internal/domain/backup_upgrade_test.go','internal/domain/backup_upgrade_final_test.go']
assert len(paths)==len(set(paths))==33
write('source_after.json',{'source_commit':head,'files':[{'path':p,'bytes':(repo/p).stat().st_size,'sha256':sha(repo/p)} for p in paths]})
runs={r['run']:r for r in read(root/'run_index.json')}
final_names=['final-cli','final-current-matrix','final-sdk','current-control-startup']
for name in final_names:
    r=runs[name]
    assert r['result']['exit_code']==0 and not r['fail_events'] and not r['skip_events']
    assert r['full_input_vector_equal'] and not r['result']['source_drift']
for name in final_names[:3]: assert runs[name]['command']['head']==head
assert git('diff','--name-only','49e1d2b5',head)=='internal/domain/runtime_command_queue_windows_test.go'
frozen='internal/api/contracts/client.protocol.schema.json'
assert git('diff','fbf661c142a98db72d273204615a9b20641b3cc3',head,'--',frozen)==''
assert sha(repo/frozen)==sha(root/'frozen-package-input/contracts/client.protocol.schema.json')
supp=read(Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_review_codex/durable_queue_scope_supplement.json'))
matrix=[
 ('Q01',['final-sdk','final-current-matrix','final-cli'],['TestRuntimeClientQueueActualMuSameProcess','TestCLIActualMuInteractiveDurableQueue'],'Actual pinned AgentSession, bounded loopback model fixture, one original process/session/Task/Run, stable customMessage IDs and exact repeated user text.'),
 ('Q02',['final-sdk','final-current-matrix'],['TestRuntimeClientQueueActualMuCancelUnknownEffect','TestBridgeControlIdentityRejectsForeignProcessAndEpoch'],'Shared frame sequence and pending registration, nonblocking control while MODEL pending, initialization waits durable host ACK, late aborted-effect UNKNOWN ACK remains attributable.'),
 ('Q03',['final-sdk','final-current-matrix'],['TestClientQueueSealAndCapacityRejectBeforeSuccess','TestBridgeQueueEmptyNeedsSDKProof'],'Transactional enqueue/seal watermarks; actual SDK custom queue plus ledger and idle; prepare/commit seal with post-fence rejection.'),
 ('Q04',['final-cli','final-current-matrix'],['TestRuntimeClientQueueGoalCancelClaimOrdering','TestClientQueueGoalCancelBeforeRun','TestCLIActualGoalCancelBeforeRun'],'Both deterministic claim/cancel transaction orderings. No-Run cancellation creates no placeholder; admitted original PREPARED dispatch stays fenced/pending; repeated coordinator scans do not launch successor.'),
 ('Q05',['final-sdk','final-current-matrix','final-cli'],['TestRuntimeClientQueueActualMuCancelUnknownEffect','TestCLIActualMuInteractiveCancelUnknown'],'Same-worker clear/abort, process/effect proof and original request replay. Unknown external effect retains pending cancellation; no fabricated confirmation after process stop.'),
 ('Q06',['final-current-matrix'],['TestClientQueueEnqueueCommitBoundary','TestClientQueueAppendOnlyReceipts','TestClientQueueBackupAllPhasesAndPendingControl','TestClientQueueRestoredNoRunCannotHideUnknownWithNewTurn'],'SQL commit/receipt boundaries and all persisted queue phases are exercised with authenticated receipt replay, restored epoch fence and no blind resend. State-boundary fixtures are not claimed as an OS crash at every individual instruction.'),
 ('Q07',['final-current-matrix'],['TestQueueUpgradePopulatedBootstrapRoundTrip','TestQueueUpgradeActiveRecovery','TestQueueUpgradeHistoricalPlans','TestClientQueueFreshInstallRollsBackMissingAdditiveSchema'],'Current22 fresh install and actual public populated21 upgrade/restore/rebackup with four typed opaque kinds, active recovery and sessions. Historical source guards retained. Separate older full-process gates remain blocked as listed.'),
 ('Q08',['final-current-matrix'],['TestClientQueueBackupRestorePreservesHistoryAndFencesNoRun','TestClientQueueBackupRequiresMatchingPortableSidecar','TestClientQueueBackupCorruptionFailsClosed'],'Versioned sidecar validates all four operational tables and bindings; restore fences runnable/noRun state; drain accounts unresolved queue/control evidence.'),
 ('Q09',['final-cli'],['TestCLIActualMuInteractiveDurableQueue','TestCLIActualMuInteractiveCancelUnknown','TestW05CLIInteractiveBeforeEOFAndSlash'],'Compiled CLI stdin through native host, named pipe, real API/SQLite and original Mu while first Run remains active; single flow writer and pending/confirmed cancellation.'),
 ('Q10',final_names,[],'Current targeted matrix, complete CLI, real SDK and built control startup have zero skips and exact before/after vectors. Broad domain regression is not green: four historical fixture/program gates remain blocked. No LIVE/provider or formal W05/A04 acceptance.')
]
coverage=[]
for q,evidence,tests,note in matrix:
    required=next(x for x in supp['acceptance_matrix'] if x['id']==q)
    for t in tests: assert any(t in runs[r]['pass_events'] for r in evidence),(q,t)
    coverage.append({'id':q,'case':required['case'],'assessment':'CURRENT_LOCAL_EVIDENCE_READY_FOR_INDEPENDENT_REVIEW' if q not in ('Q07','Q10') else 'CURRENT_SLICE_PASS_HISTORICAL_REGRESSION_BLOCKERS_REMAIN','runs':evidence,'tests':tests,'proof_scope':note})
origins=[
 ('sdk-test-01','PRODUCT','Queue identity metadata leaked into model text; stripped metadata while retaining stable SDK details.'),
 ('sdk-test-02','FIXTURE_CLEANUP','Windows EBUSY deleting live SDK directory; await exit plus bounded removal retries. Original failure retained.'),
 ('queue-test-01','FIXTURE','Workspace fixture was READ_ONLY instead of required read/write.'),
 ('queue-backup-test-01','COMPILE_AND_ASSERTION','Test initialization/compile fixes and bridge cancel idle-proof assertion aligned with real SDK predicate.'),
 ('cli-queue-test-01','FIXTURE_SQL','Test queried run_id rather than actual runtime_dispatches.run.'),
 ('queue-backup-test-03','FIXTURE_ORDER','Workspace revoked before later queue input; corrected fixture ordering.'),
 ('combined-regression-01','RUNNER_AND_PRODUCT','Missing RESEARCHOS_GO and package input caused many child-process failures; old13 constructor/new source mismatch and old cancel fixture; genuine NOT_APPLIED effect protocol poisoning also found.'),
 ('queue-regression-fix-01','PRODUCT_FIX_INCOMPLETE','Prompt catch alone did not remove fatal effect poisoning; the failed first fix remains recorded.'),
 ('legacy-fixture-fix-01','FIXTURE_AND_HISTORICAL','Old target constructor needed narrow historical helper; active public-upgrade test incorrectly expected epoch advancement instead of preserved epoch plus restore barrier.'),
 ('combined-queue-cli-02','PRODUCT_RACE','Actual cancel startup timed out; first fixture was cleaned by original test and cannot be reconstructed. Raw/vector retained.'),
 ('cli-cancel-diagnosis-01','DIAGNOSTIC_PASS_ONLY','Single passing diagnostic run does not exclude the observed race.'),
 ('cli-cancel-concurrency-diagnosis-02','PRODUCT_RACE','CLI diagnostic passed but domain first actual-worker startup timed out; second passed. Motivated failed DB capture.'),
 ('startup-failure-cause-03','PRODUCT_AND_COMPILE','Captured SQLite shows initialized worker then no MODEL effect: worker had not waited for durable host ACK. Diagnostic Go test also lacked os import.'),
 ('init-ack-fix-current-04','PRODUCT_AND_COMPILE','Missing diagnostic os import retained. After init fix, late original UNKNOWN effect ACK collided with deleted aborted waiter; clear=2 abort=0 unknown=1.'),
 ('sdk-build-09','PRODUCT_FIX','Worker waits globally sequenced initialization ACK before SDK prompt.'),
 ('sdk-build-10','PRODUCT_FIX','Retain aborted waiter until late original ACK is matched; Node adversarial test injects delayed UNKNOWN after clear.'),
 ('current-and-legacy-fix-05','HISTORICAL_BLOCKED','Two authentic schema14 tests reach missing runtime_dispatches/current-program additive boundary.'),
 ('final-combined-regression-03','HISTORICAL_AND_INPUT','Four historical failures retained. Fifth W04 failure caused unlisted original external package files; isolated exact147-file manifest fixture resolves original W04 test without changing its guard.')
 ,('finalize_report.py first invocation','REPORT_HELPER','Report helper selected parents[6] instead of parents[5]; failed before writing source_after.json. Corrected repository resolution, no source or test run affected.')
 ,('finalize_report.py second invocation','REPORT_HELPER','Report helper used external-package-relative contract path at repository root; corrected to internal/api/contracts and asserted equality with frozen package copy. No source or test run affected.')
]
blocks=[
 {'test':'TestW17UpgradeActiveRecovery','source_line':'internal/domain/backup_upgrade_test.go:770','reason':'Authentic schema14 lacks runtime_dispatches (introduced0017), current ResumeCheckpoint requires it. No table injected and no durability.go relaxation.'},
 {'test':'TestW17UpgradeCLI','source_line':'internal/domain/backup_upgrade_test.go:1012','reason':'Test always builds current control, then issues credentials against historical target14 root without next_v24_sessions.sql. Real process/API gate retained. Existing test has no historical artifact selector.'},
 {'test':'TestW16ControlReplayNative','source_line':'internal/domain/evolution_control_test.go:177','reason':'Historical release helper requires exact1..20 but receives current22 release; no protected old guard widened.'},
 {'test':'TestW16ControlBusinessNoGain','source_line':'internal/domain/evolution_control_test.go:277','reason':'Historical release helper requires exact1..20 but receives current22 release; no protected old guard widened.'}
]
selected={n:{'exit_code':runs[n]['result']['exit_code'],'pass_events':len(runs[n]['pass_events']),'top_level_passes':sum('/' not in t for t in runs[n]['pass_events']),'fail_events':len(runs[n]['fail_events']),'skip_events':len(runs[n]['skip_events']),'node_counts':runs[n]['node_counts'],'full_input_vector_equal':runs[n].get('full_input_vector_equal'),'result_sha256':sha(root/n/'result.json'),'command_sha256':sha(root/n/'command.json'),'stdout_sha256':runs[n]['result']['stdout_sha256']} for n in final_names}
report={
 'classification':'DEVELOPMENT_CANDIDATE_NOT_FORMAL_OR_PARENT_ACCEPTANCE',
 'source_commit':head,'production_source_commit':'49e1d2b5ce3756575ffc098a90b3d8d8d55d311a','base':'fbf661c142a98db72d273204615a9b20641b3cc3',
 'source_commits':git('log','--format=%H %s','fbf661c1..HEAD').splitlines(),
 'scope':{'source_paths':33,'manifest':'source_after.json','protected_scope_audit':'scope_boundaries.json','frozen_client_schema_sha256':sha(repo/frozen),'only_change_after_production_freeze':'internal/domain/runtime_command_queue_windows_test.go'},
 'final_tests':selected,'coverage':coverage,
 'broad_regression':{'run':'final-combined-regression-03','exit_code':1,'pass_events':980,'fail_events':5,'skip_events':6,'remaining_failures':blocks,'resolved_input_failure':{'test':'TestW04CurrentA01','evidence':'claim-order-and-frozen-input and final-current-matrix','manifest_sha256':'4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964','receipt':'frozen_package_input_receipt.json','original_package_unchanged':True},'skipped_tests':runs['final-combined-regression-03']['skip_events'],'later_exercised_skip':'TestRuntimeCoordinatorControlStartup passed with current rebuilt control; see control-startup-environment.json'},
 'failure_origins':[{'run':r,'origin':o,'cause_and_resolution':d} for r,o,d in origins],
 'failure_accounting':'Every attempted run remains in run_index.json with exact argv, exit, stdout/stderr hashes, source vector and attributed source:line errors. No counter reset, deletion, baseline blanket exemption or compile-only zero-assert acceptance.',
 'sdk':{'source_sha256':sha(repo/'adapters/runtime/mu/worker.mjs'),'bundle_sha256':sha(repo/'.local/w1401-mu-worker/mu-worker.mjs'),'build_receipt':'sdk-build-10','version':'0.87.1','mu_commit':'8dfebe36508ac0c2508735bb866756dab9283e74','esbuild':'0.28.2','verified_vendor_files':5083,'proof':'Actual pinned AgentSession/customMessage consumption and cancellation; bounded local fixture provider only.'},
 'control_binary':read(root/'control-startup-environment.json'),
 'limits':['External provider LIVE, protected holdout, privileged owner gate, W06ContextContinuation and W05Live not enabled or claimed.','WindowsDesktop UI interaction is outside this source slice; shared host/API semantics are implemented and actual CLI/native-host path exercised.','Four historical regression gates prevent a blanket Q10/all-repository PASS claim. Independent source/runtime review remains required.','Historical artifact discovered by Root is not substituted into protected tests without a reviewed exact-span amendment.','Original source21 and stable user databases were not migrated in place; all upgrades/restores used isolated fixtures.'],
 'cleanup':{'rejected_action':'Remove abandoned SDK test temp directory C:/Users/yqyyds/AppData/Local/Temp/researchos-queue-sdk-kak0GL','automatic_review_result':'blocked by policy','action_executed':False,'bypassed':False,'generated_binary':'current-control-build/control.exe retained locally as tested artifact; excluded from git receipts commit'},
 'index':{'path':'run_index.json','sha256':sha(root/'run_index.json')}
}
write('execution_report.json',report)
(root/'REVIEW.md').write_text('''# S6 implementation candidate\n\nSource frozen at `7f46cb59bdb4215fc5072b17b50e186e5ae0a429`; production code at `49e1d2b5ce3756575ffc098a90b3d8d8d55d311a`. Only the additional Goal-cancel/claim test differs. This is an implementation submission for independent review, not formal acceptance.\n\nCurrent final runs: full CLI **108 PASS / 0 skip** (42 top-level tests); queue/bridge/upgrade/W18/W04 matrix **88 PASS / 0 skip**; actual pinned SDK **2 PASS / 0 skip**; current built control startup **1 PASS / 0 skip**. Each has exact before/after source vectors with no drift, tool/bundle hashes, actual argv and raw output. Counts include Go subtests and must not be added as unique independent assertions.\n\nImplemented durable same-worker queues, real Mu stable-ID consumption, globally ordered initialization/control ACKs, SDK-backed prepare/commit seal, original-request Goal/Run cancel with no-Run/UNKNOWN truth, recovery fencing, numbered0022, explicit typed21-to22 isolated upgrade and portable queue inventory, and active CLI stdin through one flow writer. Two real races found and fixed: prompt started before durable init ACK; aborted effect late ACK lost its pending identity. Final Node tests exercise both counterexamples.\n\nFull broader regression was **980 PASS events, 5 failures, 6 skips**. Original W04 test now passes using an exact frozen-manifest fixture. Four historical gates remain blocked: `TestW17UpgradeActiveRecovery`, `TestW17UpgradeCLI`, `TestW16ControlReplayNative`, `TestW16ControlBusinessNoGain`. No schema17 table was injected into schema14 and no legacy release guard was widened. Q10 is therefore not blanket green. See `execution_report.json` for exact source lines, causes and unrun LIVE gates.\n\n`run_index.json` retains every attempted run and failure; `scope_boundaries.json` proves registered legacy spans and S5 suffix unchanged. `source_after.json` pins all33 authorized source files. `receipt_manifest.json` pins receipts. `current-control-build/control.exe` is a retained local tested artifact, excluded from Git.\n\nAutomatic approval review rejected cleanup of one abandoned SDK temp directory with “blocked by policy”; no deletion occurred and no alternate deletion route was attempted.\n''',encoding='utf-8')
files=[]
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.name=='receipt_manifest.json':continue
    rel=p.relative_to(root).as_posix()
    files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'git_included':rel!='current-control-build/control.exe'})
write('receipt_manifest.json',{'source_commit':head,'files':files})
print(json.dumps({'source':head,'source_files':len(paths),'receipt_files':len(files),'git_bytes':sum(f['bytes'] for f in files if f['git_included']),'final':selected},indent=2))
