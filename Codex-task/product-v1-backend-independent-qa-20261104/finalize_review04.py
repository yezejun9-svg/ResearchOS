from pathlib import Path
import datetime,hashlib,json
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def obj(name):return json.loads((R/name).read_bytes())
def save(name,value):
 p=R/name;assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def evidence(name):
 p=R/name;return {'ref':name,'sha256':sha(p),'bytes':p.stat().st_size}
inputs=obj('run-04/inputs.json');nodrift=obj('run-04/no-drift.json')
assert inputs['source_sha256']==nodrift['source_sha256'] and nodrift['all_18_author_snapshot_and_current_worktree_match']
phases=['independent-unknown-atomic','independent-focused','independent-counterexamples','independent-vet']
checks=[]
for phase in phases:
 result=obj('run-04/'+phase+'.result.json');assert result['exit_code']==0
 refs={suffix:evidence('run-04/'+phase+'.'+suffix) for suffix in ['result.json','command.json','started.json','stdout.raw','stderr.raw','controller.py.txt']}
 assert result['stdout_sha256']==refs['stdout.raw']['sha256'] and result['stderr_sha256']==refs['stderr.raw']['sha256']
 checks.append({'phase':phase,**result,'evidence':refs})
assert checks[0]['counts']['pass']==1 and checks[1]['counts']['pass']==32 and checks[2]['counts']['pass']==14
compat=obj('run-03/independent-mu-parser-compat.result.json');assert compat['exit_code']==0 and compat['counts']['pass']==12
assert nodrift['legacy_parser_compatibility_reusable']
static={'reviewer':'codex:/root/implementation_review/prompt_flow_review','classification':'READONLY_FROZEN_C_SOURCE_REVIEW_NOT_RUNTIME_ACCEPTANCE','source_sha256':inputs['source_sha256']['internal/domain/runtime_harness_windows.go'],'decision':'NO_P1_FOUND_IN_NARROW_ATOMIC_DIFF','facts':['final03 to final04 production diff confined exactly to harnessUnknown body; all prefix/suffix bytes unchanged','runtime_coordinator_windows.go ad06eb82... unchanged; old Mu markUnknown unchanged','harnessUnknown lines1141-1178 shares write lock, abandonment guard, queue fence, state/reason, current session projection and terminal event in same Tx','Event failure rolls back the new transition; earlier STARTED claim remains durable and prevents relaunch','harnessTerminalInTx lines1209-1228 reads same-Tx view and deduplicates terminal event by status+Run; this is not a claim that repeated calls never change timestamp/revision'],'reported_tool_refs':['edbaae','2fd196'],'raw_local_copy':None,'dynamic_qualification':'Separate actual reviewer freshSQLite/owned fake atomic test passed; static reviewer did not run tests or DB'}
save('run-04/static-review-summary.json',static)
old1=obj('issues-freeze01.json');old3=obj('issues-freeze03.json')
aliases=old3['origin_aliases']
diags=[]
for issue in old1['issues']:
 canonical=aliases[issue['origin_key']]
 diags.append({'origin_key':canonical,'original_reviewer_alias':issue['origin_key'],'classification':'PRODUCTION_SOURCE_INDEPENDENT_REVIEW','severity':'P1','status':'RESOLVED_IN_FINAL04_INDEPENDENTLY_RECHECKED','raw_refs':issue['raw_refs'],'original_report':evidence('issues-freeze01.json'),'resolved_refs':['run-04/independent-counterexamples.result.json','run-04/independent-counterexamples.stdout.raw'],'counting_note':'Same origin as author diagnostics04; do not increment again for aliases or aggregate test FAIL events.','corrected_original_source_refs':['adapters/runtime/codex_driver_windows.go:151' if 'marker' in canonical else 'adapters/runtime/codex_driver_windows.go:347 / :372'],'old_report_ref_correction':'Original issue metadata line anchor was approximate; original report/raw preserved unchanged.'})
atomic=old3['diagnostic_events'][0].copy();atomic.update({'status':'RESOLVED_FINAL04_INDEPENDENT_FAULT_SCAN_RECOVER_SCAN','resolved_refs':['run-04/independent-unknown-atomic.result.json','run-04/independent-counterexamples.result.json'],'resolution':'UNKNOWN state/reason/session projection and terminal event share same Tx. Injected final EventEnvelope fault rolls back all. Scan during fault never launches again; after dropping only owned fresh trigger Recover+Scan yields UNKNOWN, exactly one terminal event and end=true.'});diags.append(atomic)
diags.append(old3['diagnostic_events'][1])
diags.extend(old1['diagnostic_events'])
diags.extend([
 {'origin_key':'backend-v1-review-json-anchor-patch-failed','classification':'REVIEW_METADATA_EDIT_NOT_APPLIED','raw_refs':['tool:apply_patch failed expected-lines validation; no chunk returned'],'detail':'Partial long JSON-line source-anchor correction failed; no file changed. Final source anchors corrected in this new report; old issue report kept intact.'},
 {'origin_key':'backend-v1-review-rg-option-locator','classification':'REVIEW_READONLY_LOCATOR','raw_refs':['tool:e0fe55','tool:d01b46'],'detail':'Outer command exited0 but inner rg interpreted pattern beginning --- FAIL as option. Corrected read used -e, no test rerun or source change.'},
 {'origin_key':'backend-v1-review-output-truncation','classification':'REVIEW_TRANSPORT_OUTPUT_ONLY','raw_refs':['tool:21c174','tool:595b0c','tool:287de1','tool:3511b6'],'detail':'Successful read output truncated. Narrow later reads or full pinned local input files used; no failure/acceptance inferred from missing displayed bytes.'}
])
assert len({d['origin_key'] for d in diags})==len(diags)
all_unique={}
for check in checks:
 if check['phase']=='independent-vet':continue
 for row in check['roster']:
  if row['action']=='pass':all_unique[(row['package'],row['test'])]=True
assert len(all_unique)==46,len(all_unique)
limitations=[
 'This approval covers exact18 source and development fixtures only. It is not real Codex/model, Windows configured-readonly enforcement, Desktop usability, or product journey acceptance.',
 'No actual Codex executable, account/model request, Host metadata constructor CLI probe, GUI, old user DB or provider was executed by this independent QA. Fake processes are owned Go children with real Windows Job/BeforeResume/drain behavior; SQLite fixtures are fresh.',
 'Rev2 D03 PLATFORM_POLICY retains native platform/account policy ownership. Requested hooks/plugins disables are not proof that managed hooks/MCP are disabled; no per-tool permission bridge is implemented or qualified.',
 'Requested workspace-read profile remains UNVERIFIED for actual Codex/filesystem enforcement. Windows Job ownership is not AppContainer or same-OS-user tamper resistance.',
 'Installation/login metadata is distinct from execution/model/quota/cancellation qualification. Exact native0.166 support and real launch need separately registered qualification.',
 'Underlying existing canonical JSON/JCS producer rejects sequence beyond losslessly representable integers. Legal native producer tested at9007199254740991; string-only HTTP/Decimal consumers independently preserve9007199254740993 and9223372036854775807. Full-int64 producer sustainability is not accepted.',
 'COMPLETED is reconciled execution only, not business acceptance. No old Goal503 gate, Mu formal result, old22/42-case acceptance or V1 thirteen-journey acceptance is upgraded.',
 'V1 write/resume/pause/per-tool approval/file diff/file list/file artifacts/attachments/token delta remain unsupported; no invented observations.',
 'Desktop PATH/HOME integration was outside Backend18 and later parent-reported as separately integrated Main744d4944; this reviewer did not qualify its real GUI/native account launch. Isolated smoke profile loggedout does not establish normal account state.',
 'Review uses exact18 C snapshots/Go overlays with necessary baseline package/spec/build dependencies read-only from author worktree. Main merge, protected old modifications and control-state guards are integration-controller responsibilities, not claims from these tests.'
]
report={
 'schema':'researchos.product-v1-independent-backend-review.v1','reviewer':'codex:/root/implementation_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_acceptance_increment':0,'pending_blockers':[],
 'scope_id':'PRODUCT_V1_SINGLE_HARNESS_BACKEND','base_head':inputs['base_head'],'interface_sha256':inputs['interface_sha256'],
 'source_sha256':inputs['source_sha256'],'source_count':18,'production_count':13,'test_count':5,
 'manifest_sha256':inputs['author_pins']['final-04/source-manifest.json'],'source_manifest_sha256':inputs['author_pins']['final-04/source-manifest.json'],
 'freeze_sha256':inputs['author_pins']['final-04/freeze.json'],'summary_sha256':inputs['author_pins']['final-04/summary.json'],'author_diagnostics_sha256':inputs['author_pins']['diagnostics-04.json'],
 'freeze_ref':'run-04/author/final-04/freeze.json','manifest_ref':'run-04/author/final-04/source-manifest.json',
 'evidence_manifest':'EVIDENCE-MANIFEST.json','source_readback':evidence('run-04/no-drift.json'),'inputs':evidence('run-04/inputs.json'),
 'independent_checks':checks,'independent_vet':{'exit_code':0,'ref':'run-04/independent-vet.result.json','sha256':sha(R/'run-04/independent-vet.result.json'),'tests_executed':0},
 'reused_unchanged_evidence':{'legacy_mu_parser':{'result':evidence('run-03/independent-mu-parser-compat.result.json'),'stdout':evidence('run-03/independent-mu-parser-compat.stdout.raw'),'exit_code':0,'counts':compat['counts'],'reason':'adapters/runtime/codex.go exactSHA29ffe8235d10e15e8c3468745a7863390e00358c555cc84da7ad881b6fac865a unchanged final03 to final04; old parser compatibility selector is pure'}},
 'counting':{'final04_unique_pass_test_events':46,'atomic_direct_pass_is_duplicate_of_independent_phase':True,'helper_parent_skips_are_not_passes':True,'legacy_compatibility_applicable_pass_events':12,'no_aggregate_phase_sum_or_vet_compile_as_test_acceptance':True,'formal_increment':0},
 'static_review':evidence('run-04/static-review-summary.json'),
 'reviewed_boundaries':['Actual same Coordinator.Scan and original authoritative DB/Task/Run/lease/dispatch/outbox/ArtifactUse','Idempotent same request and lost ACK lookup/replay; UNKNOWN Recover/Scan never redispatch','Current Host principal/workspace authority rechecked at launch and revoke; distinct can_submit metadata vs native launch admission','Queued exact revision cancel and active exact Run/epoch CAS; CANCEL_REQUESTED waits actual owned stop/drain','Fixed driver argv/stdin/regular recognized private cwd marker; new-driver-only immutable thread identity validation; legacy parser unchanged','Project/task-specific event cursor reset, legal canonical producer and complete int64string transport consumers','Strict HTTP request body refuses caller exe/argv/token/authority fields; Recorder-only API boundary','New Harness UNKNOWN sameTx projection+terminal event rollback, no redispatch, eventual explicit trusted reconciliation'],
 'diagnostic_events':diags,'origin_aliases':aliases,'author_diagnostics_reference':evidence('run-04/author/diagnostics-04.json'),
 'diagnostic_merge_policy':'Root merges author and reviewer diagnostics by canonical origin_key. Raw FAIL events remain; source/fixture/approval/infrastructure classifications distinct. No old counter reset.',
 'limitations':limitations,'outstanding_product_qualifications':['Actual Codex0.166 bounded task and observed native event/cancel/permission behavior','Actual Desktop freshuserData with normal native account integration','Remaining V1 product journeys including dualHarness/diff/acceptapply; beyond this readonly slice'],
 'pending_operations':[],'uncertain_outcomes':[],'counter_reset':False,'no_d_source_writes':True,'real_cli_or_model_run':False,
 'approval_rejection_summary':'Original whole-base git archive was automatically rejected before execution because it exceeded exactBackend18 source-copy scope. It remains stopped and was not retried. Exact18 snapshots+overlays completed as the narrower authorized alternative; full verbatim action/target/reason/outcome is retained in diagnostic_events.'
}
save('review.json',report)
paths=[]
for p in sorted(R.iterdir()):
 if p.is_file() and p.suffix in ['.json','.py','.go','.txt'] and p.name!='EVIDENCE-MANIFEST.json':paths.append(p)
for dirname in ['prepared-inputs','run-01','run-03','run-04']:
 for p in sorted((R/dirname).rglob('*')):
  if p.is_file() and 'private' not in p.relative_to(R/dirname).parts:paths.append(p)
entries=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]
assert not any('private/' in e['path'] for e in entries)
manifest={'schema':'researchos.independent-review-evidence-manifest.v1','scope':'EXACT18_SOURCE_SNAPSHOTS_AND_REVIEWER_TESTS_LOGS_REPORTS_ONLY','root':str(R),'review':evidence('review.json'),'files':entries,'file_count':len(entries),'total_bytes':sum(e['bytes'] for e in entries),'excluded':['private caches/temp/profiles/module inputs','whole Git repository/archive','unrelated project source/history'],'formal_increment':0}
save('EVIDENCE-MANIFEST.json',manifest)
print(json.dumps({'decision':report['decision'],'report':str(R/'review.json'),'report_sha256':sha(R/'review.json'),'evidence_manifest_sha256':sha(R/'EVIDENCE-MANIFEST.json'),'evidence_files':len(entries),'evidence_bytes':manifest['total_bytes'],'formal_increment':0}))
