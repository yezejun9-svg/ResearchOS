from pathlib import Path
import json,hashlib,types,datetime,re
B=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
K=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
OUT=B/'remaining_boundary_independent_review_codex/boundary-20261009-01'
def pin(p):
 p=Path(p);raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,data):
 p=OUT/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
cp=B/'restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01/contract.json'
c=read(cp);roster=read(c['exact_source_roster']['path']);sources=roster['sources']
h=read(B/'restored21_runtime_v3_actual_independent_review_codex/actualreview-1a11fff/HDF.json')
cl=read(h['actual_validation_closed_ref']['path'])
refs=[pin(cp),c['exact_source_roster'],pin(B/'restored21_runtime_v3_actual_independent_review_codex/actualreview-1a11fff/HDF.json'),h['manifest_ref'],h['actual_decision_ref'],h['actual_validation_closed_ref'],h['source_handoff_ref'],h['source_manifest_ref'],c['h20_actual_review_handoff'],c['h20_actual_review_manifest'],c['h20_actual_closed'],c['a21_v2_source_handoff'],c['a21_v2_source_manifest'],c['a21_v2_overlay'],c['source_guard'],c['owned_job'],cl['typed_fixture_evidence_inventory_ref'],cl['actual_test_jsonl_primary_ref']]
refs+=list(sources.values())
contracts={x:pin(K/x) for x in ['contracts/execution.plan.json','contracts/tasks.json','06_ACCEPTANCE_TESTS.md']}
refs+=list(contracts.values())
resources={}
for name in ['python','go','node','mu_bundle','test2json']:
 expected=c[name];actual=pin(expected['path'])
 assert actual['sha256']==expected['sha256'],name
 if 'bytes' in expected:assert actual['bytes']==expected['bytes'],name
 resources[name]=actual;refs.append(actual)
guardraw=Path(c['source_guard']['path']).read_bytes()
assert hashlib.sha256(guardraw).hexdigest()==c['source_guard']['sha256']
module=types.ModuleType('finite_read_guard');exec(compile(guardraw,c['source_guard']['path'],'exec'),module.__dict__)
g=module.SourceReadGuard();g.acquire(refs)
facts={};excerpts={}
try:
 def held(ref):return g.get_buffer(ref['path'])
 hc=json.loads(held(h['actual_validation_closed_ref']))
 assert hc['pass_count']==13 and hc['fail_count']==0 and hc['skip_count']==0
 assert hc['genuine21_22_release_program_provenance']=='OPEN'
 assert hc['public_late_failure_no_publication']=='OPEN' and hc['overall20to24']=='OPEN'
 assert hc['individual_descendant_PID_FILETIME_and_raw_streams'] is None and hc['descendant_test_binary_exit'] is None
 assert hc['native_qualification_accepted'] is False and hc['component_validation_accepted'] is False
 assert len(sources)==63
 ti=json.loads(held(cl['typed_fixture_evidence_inventory_ref']))
 assert ti.get('files')==[]
 typed=held(sources['internal/domain/runtime_typed_client_fixture_windows_test.go']).decode()
 six=['TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite','TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite','TestRuntimePermissionDecisionWaitsForAnotherRequiredResource','TestRuntimeMuSessionToolAndIndependentAcceptance','TestRuntimeMuToolRefusalAllowsNextTurn','TestW05RuntimeEventBrokerBeforeIOAndRollback']
 assert all('"'+x+'"' in typed for x in six)
 assert not set(six).intersection(hc['exact_parent_names'])
 assert '"actual_native_child_pid": nil' in typed and '"actual_native_child_exit": nil' in typed
 for key,ranges in {
  'internal/domain/backup_history20_upgrade_test.go':[(18,34)],
  'internal/domain/backup_restored21_upgrade_test.go':[(19,34),(49,62),(86,92),(127,135)],
  'internal/domain/backup_restored21_upgrade.go':[(13,15),(180,237)],
  'internal/domain/backup_configuration_upgrade_test.go':[(403,460),(465,503)],
  'internal/domain/backup_historical22_bridge_test.go':[(104,115),(143,159)],
  'internal/domain/backup_prepared_abandonment_upgrade_windows_test.go':[(18,40)],
  'internal/domain/native_migration_authority_harness_windows_test.go':[(1,6),(32,46),(383,395),(409,415),(449,464)],
  'internal/domain/runtime_typed_client_fixture_windows_test.go':[(288,310),(325,363),(392,439)]
 }.items():
  lines=held(sources[key]).decode('utf-8').splitlines()
  excerpts[key]=[{'start':a,'end':min(z,len(lines)),'text':'\n'.join(lines[a-1:z])} for a,z in ranges]
 ep=json.loads(held(contracts['contracts/execution.plan.json']))
 tasks=json.loads(held(contracts['contracts/tasks.json']))
 def findtask(x):
  if isinstance(x,dict):
   if x.get('task_id')=='W05' and x.get('title'):return x
   for value in x.values():
    found=findtask(value)
    if found:return found
  if isinstance(x,list):
   for value in x:
    found=findtask(value)
    if found:return found
 task=findtask(tasks);assert task and task['owned_acceptance_ids']==['A04']
 facts={'development_passes':13,'failures':0,'skips':0,'selected_parents':hc['exact_parent_names'],'typed_parents_not_selected':six,'typed_expected_terminal_leaf_count':8,'typed_inventory':ti,'source_composition':{'accepted_h20':roster['accepted_h20_count'],'a21_overlay':roster['a21_overlay_count'],'composed':roster['composed_count']},'formal_owner':task['owned_acceptance_ids'],'affected_acceptances':task['acceptance_ids'],'gate_ids':[x['check_id'] for x in task['task_gate_checks']],'caller_open_boundaries':{x:hc[x] for x in ['genuine21_22_release_program_provenance','public_late_failure_no_publication','overall20to24','individual_descendant_PID_FILETIME_and_raw_streams','descendant_test_binary_exit']}}
finally:
 cleanup=g.close()
cleanupref=save('source-guard.closed.json',cleanup)
assert cleanup['verification']=='PASSED' and cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
boundaries=[
 {'id':'REAL_RELEASE_21_22','status':'OPEN','source_gap':'Current H20/A21 helpers assemble schema profiles and write PUBLIC_FIXTURE_* program bytes; maintenance plan explicitly does not authenticate historical release binaries or authorize single-writer cutover.','minimal_source_work':['Add or locate exact independently frozen schema21/schema22 release program resources and their source/SQL/contracts/build manifests. Do not relabel current head or byte placeholders as historical release programs.','Add a bounded public-entry fixture/driver using the actual pinned program for each release, with caller-side release/program identity verification. Keep stage-specific plan semantics.'],'new_validation':['Run the exact versions against their matching disposable data and release roots; capture actual executable/argv/cwd, PID plus creation FILETIME, raw stdout/stderr/exit and resulting DB schema/ledger/typed-row hashes.','Exercise public 21-to22 upgrade with the real release resources and ensure the same output used by the next stage is pinned.'],'reuse_source_keys':['internal/domain/backup_restored21_upgrade.go','internal/domain/backup_restored21_upgrade_test.go','internal/domain/backup_historical22_bridge_test.go'],'not_proven':['Historical provenance by merely hashing arbitrary program bytes','Actual single-writer or Owner authority from schema shape']},
 {'id':'PUBLIC_20_TO_24_CHAIN','status':'OPEN','source_gap':'Existing 20-to21 and 21-to22 component receipts do not chain through actual 22-to23 and 23-to24 public outputs. preparedUpgradePublicFixture directly invokes upgradeConfigurationMigration to construct schema23, so it is not continuous chain evidence.','minimal_source_work':['Add one bounded orchestration case passing the actual public output DB/root of each stage as the next public input: 20-to21, restored21 session plus queue-to22, configuration22-to23, prepared-abandonment23-to24.','Preserve each stage plan, authenticated snapshot, schema/version/typed storage invariants, workspace and restore fences; do not replace the contracts with one permissive migration path.'],'new_validation':['A new actual Windows public CLI/entry chain with exact inputs, complete provenance and emitted/persisted report equality per stage; verify source unchanged and the final database is the exact24 profile.','If claiming original-data cutover, separately satisfy current Owner/native purpose token/lease/single-writer checks; a restored rehearsal cannot establish original cutover.'],'reuse_source_keys':['internal/domain/backup_history20_upgrade.go','internal/domain/backup_restored21_upgrade.go','internal/domain/backup_upgrade.go','internal/domain/backup_configuration_upgrade_test.go','internal/domain/backup_prepared_abandonment_upgrade.go','internal/domain/backup_prepared_abandonment_upgrade_windows_test.go','internal/domain/native_migration_authority_harness_windows_test.go'],'not_proven':['A concatenation of independent fixture PASS reports','23-to24 synthetic native harness as genuine21/22 provenance']},
 {'id':'PUBLIC_LATE_FAILURE','status':'OPEN','source_gap':'Restored21 tests prove session transaction rollback and internal queue ledger rollback, while four malformed source cases fail before snapshot. Configuration post-snapshot fault test uses internal upgradeLocal with fake verifier and another plan. None supplies A21 public post-DDL/prepublication failure causality.','minimal_source_work':['Add one deterministic bounded test of public UpgradeLocal/upgrade-local for Restored21SessionUpgradePlan where failure occurs after actual isolated session/queue DDL and before target/report publication.','Prefer existing context/cancellation or program/release validation boundaries with a deterministic phase witness. If inaccessible, add a narrowly scoped test harness seam; do not add a production bypass, timing-only race, source-profile mutation or acceptance shortcut.'],'new_validation':['Prove the intended post-DDL phase was reached and the expected error returned through the public entry.','Assert original typed rows/schema/ledger unchanged, destination and success restore-report absent, candidate staging discarded, and authenticated snapshot retained if it was already durably created. Distinguish private candidate rollback/discard from a false claim that already committed internal session work never happened.'],'reuse_source_keys':['internal/domain/backup_restored21_upgrade.go','internal/domain/backup_restored21_upgrade_test.go','internal/domain/backup.go','internal/domain/backup_configuration_upgrade_test.go'],'not_proven':['Internal helper failure as public coordinator failure','Pre-snapshot rejection as late failure','Failed result or missing target without phase witness']},
 {'id':'TYPED_NATIVE_DESCENDANTS','status':'OPEN','source_gap':'Selected dev13 parents never invoke typedRuntimeFixtureChild. Existing typed helper records test2json runner PID/exit and raw streams but deliberately leaves actual native child PID/exit NULL pending Root reconciliation; FILETIME/raw/exit closure cannot be inferred from Job idle.','minimal_source_work':['Reuse the existing six-parent/eight-leaf typed Source fixture and synthetic loopback TLS setup. Add or reuse a reviewed Root-owned process observer/caller capable of exact descendant executable identity, PID plus creation FILETIME, parent linkage, raw stream attribution, exit and Job closure.','Join child-invocation/result/parent-result/event-verdict with actual process records and exact binary/tool pins; NULL stays OPEN until observed. Keep synthetic fixture classification.'],'new_validation':['Run only the newly selected six typed parents/eight leaves under the explicit owned Windows Job; collect complete exact selector test2json corpus and per-case child artifacts.','Supply existing pinned Go1.27.1/GOROOT, official test2json plus SHA, Node/Mu bundle, absolute fresh RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR and correct fallback-root child environment. No paid provider needed for this local synthetic qualification.'],'exact_parent_names':six,'reuse_source_keys':['internal/domain/runtime_typed_client_fixture_windows_test.go','internal/domain/runtime_permission_windows_test.go','internal/domain/runtime_tool_integration_windows_test.go','internal/domain/runtime_session_events_windows_test.go','internal/domain/client_protocol_goal_test.go'],'not_proven':['Dev13 primary test2json identity as typed descendant identity','Synthetic TLS leaves as live real-model A04 completion']},
 {'id':'W05_FORMAL_SCOPE','status':'OPEN_SEPARATE_GATE','source_gap':'The packet is component partial and formal_case_accepted_delta is zero. The current task does not establish a complete live A04 receipt inventory.','minimal_source_work':['After component closure, map exact current receipts to W05-G01/G02/H08/P01/U02 and A04-01..06. Implement or run only uncovered/changed assertions. Keep C11 and C15 as affected links; their frozen final owner is W12.'],'new_validation':['At least one fixed authorized real executor: settled completion without self-ACCEPTED, cancellation of tools and queue, crash/timeout recovery and workspace/credential isolation, nested parent/run/tool linkage plus budget/cancel/model/version/security-patch checks.','Own installed CLI interactive and JSONL read/edit/shell/goal/resume/cancel plus U02 real issue Chinese/streaming/handlers; independent acceptance required. New live provider use stays within existing authorization, not this read-only review.'],'reuse_source_keys':[],'not_proven':['20-to24 component proof as full A04 acceptance','C11/C15 final ownership transferred to W05']}
]
errors=[pin(OUT/'original-error-1b770f.json'),pin(OUT/'original-error-cdd1a7.json')]
report={'schema':'researchos.w05-remaining-boundary-independent-review.v1','status':'READ_ONLY_MINIMUM_BOUNDARIES_IDENTIFIED','actor':'codex:/root/native_temp_independent_review','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'basis_refs':refs[:18],'frozen_contract_refs':contracts,'source_roster_ref':c['exact_source_roster'],'source_resources':sources,'runtime_resources':resources,'facts':facts,'source_excerpts':excerpts,'remaining_boundaries':boundaries,'reuse_without_rerun':[{'scope':'Current unchanged 13 development tests','ref':h['actual_validation_closed_ref'],'independent_review':pin(B/'restored21_runtime_v3_actual_independent_review_codex/actualreview-1a11fff/HDF.json')},{'scope':'Accepted H20 five-parent/four-drift actual component evidence only','ref':c['h20_actual_closed'],'independent_review':c['h20_actual_review_handoff']}],'execution_order':['First pin genuine21/22 resources and implement the smallest missing public chain/late-failure harness.','Independently review Source/caller, then Root executes only causal new scenarios with fresh finite input/compiled closure.','Typed six-parent/eight-leaf local Native descendant qualification can be independently prepared; reuse existing resource pins, no paid provider.','Independently review actual receipts; keep full W05 formal gates separate and reuse still-current prior evidence.'],'guard_cleanup_ref':cleanupref,'held_input_count':len(cleanup['entries']),'retained_handles_count':0,'original_errors':[{'ordinal':988,'chunk':'1b770f','ref':errors[0],'stage':'SourcePy read-only roster dictionary indexed as list','outer_exit':1,'native_exit':None,'model_exit':None},{'ordinal':989,'assignment':'ASSIGNED_BY_ROOT','chunk':'cdd1a7','ref':errors[1],'stage':'read-only Get-Content absent workspace-top AGENTS.md','outer_exit':1,'native_exit':None,'model_exit':None}],'limitations':['Finite exact-reference review only; no broad receipt search or exhaustive proof that no other artifact exists. Resource candidates listed are the pinned sources and runtime tools already available in this packet; genuine21/22 program resources have not been established by this packet.','No Go/test2json/native/model rerun. Prior actual evidence is reused at its original scope. No new component/formal acceptance, Main adoption or live provider grant.'],'source_or_canonical_written':False,'native_test_executions':0,'model_requests':0,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'STOP':True,'FINAL':True}
rr=save('review.json',report)
md='''W05 最小剩余边界已明确，当前仍为 COMPONENT_PARTIAL，正式验收增量为 0。\n\n1. dev13 的 13 PASS 和 H20 已独审的原收据可按原范围复用，不重跑。当前 A21 测试写入 PUBLIC_FIXTURE 程序字节，未证明真实21/22发布程序。\n2. 新增一个连续公共20→21→22→23→24链；每段使用上一段真实输出，保存每段schema、ledger、typed rows、快照与返回/落盘报告一致性。现有23 fixture直接调用内部迁移，不是连续公共链。\n3. 补 A21 公共入口的实际DDL后、发布前失败；必须有达到阶段的证据，验证源不变、目标/成功报告未发布、临时候选清理，已生成的认证快照按合同保留。\n4. 复用现有 typed 六父例/八叶例源码与本地 synthetic TLS 资源，新运行由 Root 对账每个子代的 binary/PID/FILETIME/父子关系/raw/exit/Job。dev13 未选择这些父例，现有 helper 子代PID/exit仍为空。\n5. 这些组件通过后仍需独立对照 W05-G01/G02/H08/P01/U02 与 A04-01..06。C11/C15 的冻结最终负责人是 W12，不能混作W05正式全例。\n\n完整精确refs、源码行段、最小实施/验证断言、可复用资源与限制见 review.json。本次只写本 review namespace，SourceGuard已closed、retained_handles=0；没有新Native/Go/model运行、没有自验收。\n'''
with (OUT/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
mf=save('MF.json',{'schema':'researchos.w05-remaining-boundary-review-manifest.v1','members':[rr,pin(OUT/'REPORT.md'),cleanupref,*errors,pin(OUT/'review_boundary.py')]})
hh=save('HDF.json',{'schema':'researchos.w05-remaining-boundary-review-handoff.v1','status':report['status'],'review_ref':rr,'manifest_ref':mf,'guard_cleanup_ref':cleanupref,'held_input_count':len(cleanup['entries']),'all_handles_closed':True,'retained_handles_count':0,'remaining_boundaries':[x['id'] for x in boundaries],'reusable_dev13_without_rerun':True,'original_error_refs':errors,'new_original_errors':[988,989],'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'source_or_canonical_written':False,'native_test_executions':0,'model_requests':0,'STOP':True,'FINAL':True})
print(json.dumps({'HDF':hh,'MF':mf,'review':rr,'guard':cleanupref,'held_inputs':len(cleanup['entries']),'original_errors':errors},ensure_ascii=False))

