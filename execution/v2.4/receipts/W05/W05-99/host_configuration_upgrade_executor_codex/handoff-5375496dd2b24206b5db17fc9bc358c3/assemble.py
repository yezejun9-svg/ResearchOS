import datetime, hashlib, json, pathlib

out=pathlib.Path(__file__).resolve().parent
root=out.parents[6]
receipts=out.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p,locator=None):
    value={'path':p.relative_to(root).as_posix(),'sha256':sha(p)}
    if locator is not None: value['locator']=locator
    return value
def save(name,value): (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rows=json.loads((out/'all_actual_runs.json').read_text('utf8'))
focused=next(r for r in rows if r['directory']=='closure-1bdf02a977c9459cb024a3e803593c64')
fullcli=next(r for r in rows if r['directory']=='closure-a2594db073c34772889321d4d20c8a20')
legacy=next(r for r in rows if r['directory']=='closure-214eca5bd7b542f195ff14c505c46e9f')
hardpin=next(r for r in rows if r['directory']=='closure-61315ea6c5a04739b32a7e394fe3d25d')
def testrefs(prefixes,run=focused):
    return [dict(test=x['test'],action=x['action'],raw=ref(receipts/run['directory']/'test.stdout',{'line_start':x['line'],'line_end':x['line']})) for x in run['assertions'] if any(x['test']==p or x['test'].startswith(p+'/') for p in prefixes)]
limits=[
    'No program-source self-attestation protocol exists. Actual source22/target23 builds are externally bound to captured compiler inputs and executable hashes. Stable bytes from a wrongly asserted source cannot be detected solely by current public executable protocol; independent verifier must judge external release binding.',
    'store.Open has already selected WAL before domain migration guards. Refusal is before domain/additive/fence DDL, not a claim of zero filesystem writes.',
    'SQLite WAL readers can succeed while the exclusive writer transaction is held. Genuine frozen22 product writes are denied during all measured publication phases; after close the old product can reopen the original database. Explicit single-writer cutover remains required.',
    'Original schema22 hardpin test remains failed. Two additional original historical14 tests fail when paired with current-runtime/current-control dependencies. No protected tests were edited; no full-domain PASS is claimed.',
    'Unconditional idempotency UPDATE trigger 1811 remains. This prerequisite does not fix CANCEL ACK-to-final F08 finalization, expose host.configure, prove provider usability, or sign formal acceptance.',
    'This worktree is based on 396287cc plus immutable foundation5. Later MAIN L02 composition is not present and requires Root integration validation.',
]
gate_specs=[
 ('G01','EXECUTED_WITH_PROTOCOL_LIMIT',['TestConfigurationUpgradeNativeCLI','TestConfigurationUpgradeReleaseAndMigrationRefusals','TestConfigurationUpgradePostSnapshotFaults'],'Fixed22/23 roots and exact SQL/additive/contracts; genuine captured old22 and target23 build inputs/programs; native path/alias/root negatives and before/after drift guards. See explicit self-attestation limitation.'),
 ('G02','EXECUTED',['TestConfigurationUpgradeNumberedOnlyAndMalformedRefusal'],'Numbered-only22 source without runtime session/fence is refused before snapshot/publication.'),
 ('G03','EXECUTED',['TestConfigurationUpgradeHostOnlyStartupGuard','TestConfigurationUpgradeFutureBeforeDomainDDL','TestConfigurationUpgradeFreshAndAdditiveGuard'],'Populated host authority and malformed/future/gapped schema inventory cannot take empty-store migration; lower WAL open remains documented.'),
 ('G04','EXECUTED',['TestBackupHostConfigurationFrozenSchemas','TestBackupHostConfigurationSchemaRefusals','TestBackupHostConfigurationCompleteHistoryRefusals'],'Full three-table columns/schema/digest; frozen schema mirrors/source hashes; all history typed validation, valid-JSON tamper refusal and absent embed compile refusal.'),
 ('G05','EXECUTED',['TestBackupHostConfigurationCompleteHistoryRefusals','TestBackupHostConfigurationPublicRoundTrip'],'Owner/principal full contiguous history and current head/latest correspondence, orphan/foreign records refused.'),
 ('G06','EXECUTED',['TestBackupHostConfigurationOtherMethodIdentity','TestBackupHostConfigurationCompleteHistoryRefusals'],'Every global principal+command identity joins exactly one original journal; typed method/result/hash/principal/project checks; non-configuration identities included.'),
 ('G07','EXECUTED',['TestBackupHostConfigurationPublicRoundTrip','TestConfigurationUpgradePublicRoundTrip'],'Public backup/restore/rebackup, populated23 and nonconfig identities, restored auth revocation, historical credential references remain unqualified; no Vault reads.'),
 ('G08','EXECUTED',['TestConfigurationUpgradeActiveQueueRecovery','TestConfigurationUpgradePostSnapshotFaults','TestConfigurationUpgradeReleaseAndMigrationRefusals'],'Real admitted queue/control/ACK and active Run/effect fenced to UNKNOWN with original identity and no added dispatch. Stable snapshot retained across target dependency/drift failure; source and protected rows unchanged.'),
 ('G09','EXECUTED_WITH_SINGLE_WRITER_LIMIT',['TestConfigurationUpgradeFrozen22ProgramLock','TestConfigurationUpgradeLegacyWriterLock'],'Genuine Git396287 frozen22 control binary: native write before/after lock succeeds and five in-lock writes fail. Separate direct SQL process records WAL read success; no universal read-denial claim.'),
 ('G10','OPEN_HISTORICAL_REGRESSION',['TestQueueUpgradeHistoricalPlans','TestQueueUpgradeFrozenInputAndOperationalDrift','TestQueueUpgradePopulatedBootstrapRoundTrip'],'Fixed old13->14/13->20/21->22 release hashes and dispatch preserved; historical-plan and queue-upgrade controls pass. Original fresh22 hardpin and two historical14 current-runtime combinations remain explicit failures.'),
 ('G11','EXECUTED_F08_STILL_OPEN',['TestBackupHostConfigurationPublicRoundTrip','TestConfigurationUpgradePublicRoundTrip','TestConfigurationUpgradeActiveQueueRecovery'],'Original SQL0002 unconditional immutable trigger remains1811; original ACK/UNKNOWN records retained. No ACK-to-final rewrite bypass.'),
 ('G12','EXECUTOR_FREEZE_ONLY_INDEPENDENT_REVIEW_PENDING',[],'Actual tool/source/SDK before-after-current 39568-input audit and all originals retained. Formal increment0; MAIN23 HOLD until non-author source review and combined-source validation.'),
]
gates=[dict(id=i,status=s,claim=c,raw_test_refs=testrefs(ts)) for i,s,ts,c in gate_specs]
save('gates.json',gates)
proposal={
 'schema':'researchos.configuration-upgrade-followup-test-scope-proposal.v1','status':'PROPOSAL_ONLY_NOT_AUTHORIZED_NOT_IMPLEMENTED','actor':'codex:/root/sources_parent_impl',
 'requested_exact_path':'internal/domain/backup_command_queue_test.go','original_source_ref':ref(root/'internal/domain/backup_command_queue_test.go'),
 'failure':dict(test='TestClientQueueFreshNumberedSchema',source_line=121,invocation=hardpin['invocation'],stdout=hardpin['stdout'],actual_exit=1,actual='backup_command_queue_test.go:122: migration=23 <nil>'),
 'minimal_change':[
   'Only split the fresh-current expectation from a new explicit historical22 fixture in this test file. Keep every existing empty clientQueueTables check and numbered0022 SQL presence assertion.',
   'Fresh-current version must equal the complete exact installed numbered migration inventory through fixed0023; verify contiguous versions and fixed0022/0023 bytes using existing pinned release readers. Do not use >=22, max-only acceptance, or silently accept future versions.',
   'Add explicit historical22 SQL fixture from exactly pinned001..022 (existing release helper/byte hashes), prove highest version22, no0023 three-table schema, and retain the identical original queue-table empty/presence guards. Numbered-only22 is a schema fixture, not a matching startup/upgrade source; full matching22 session/fence positive remains separate.',
   'No production, numberedSQL, foundation5, other old test functions or thresholds changed. Run original queue/backup suite plus newcurrent/historical selectors with exact before-after closure. Current raw failed run remains immutable.'
 ],
 'separate_unclosed_historical14':[
   dict(test='TestW17UpgradeActiveRecovery',path='internal/domain/backup_upgrade_test.go',line=770,actual='current ResumeCheckpoint on exact historical14 schema reaches absent runtime_dispatches',action='No production compatibility shim or table injection proposed. Needs independent choice of a matching historical executor fixture or separate current-schema recovery qualification that preserves the historical14 assertions; not covered by this one-path scope.'),
   dict(test='TestW17UpgradeCLI',path='internal/domain/backup_upgrade_test.go',line=1060,actual='optional fixed14 artifact environment absent; current23 control fallback refused old14 additive/fence mismatch',action='Prefer existing pinned RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL artifact with its original exact hash/buildinfo; no source change necessary if artifact is available. Preserve current actual failed invocation and record a separate rerun/tool vector.')
 ],
 'historical14_raw':dict(invocation=legacy['invocation'],stdout=legacy['stdout'],stderr=legacy['stderr'],actual_exit=1),
 'no_source_edited_for_this_proposal':True
}
save('followup_test_scope_proposal.json',proposal)
save('handoff.json',dict(
 schema='researchos.configuration-upgrade-executor-handoff.v1',status='CANDIDATE_FOR_INDEPENDENT_REVIEW_WITH_OPEN_GATES',actor='codex:/root/sources_parent_impl',independent_verifier='codex:/root/w05_merge_review',root='codex:/root',formal_increment=0,main23_hold=True,
 exact_source_paths=[r['path'] for r in json.loads((out/'source.before_after.json').read_text())],source=ref(out/'source.before_after.json'),protected=ref(out/'protected_sources.json'),current_compiled_closure=ref(out/'current_compiled_closure_audit.json'),scope=ref(receipts/'implementation-df2b17aedb254da9b0fb902ca7f8575f/scope.original.json'),schema_mirror_scope=ref(receipts/'implementation-df2b17aedb254da9b0fb902ca7f8575f/schema_mirror_scope.original.json'),foundation=ref(receipts/'implementation-df2b17aedb254da9b0fb902ca7f8575f/foundation_composition.json'),
 all_actual_runs=ref(out/'all_actual_runs.json'),failures=ref(out/'failure_origins.final.json'),gates=ref(out/'gates.json'),followup_scope=ref(out/'followup_test_scope_proposal.json'),
 current_focused={'counts':focused['counts'],'top_level_pass':focused['top_level_pass'],'actual_exit':0,'invocation':focused['invocation']},current_full_cli={'counts':fullcli['counts'],'top_level_pass':fullcli['top_level_pass'],'actual_exit':0,'invocation':fullcli['invocation']},old_hardpin={'counts':hardpin['counts'],'actual_exit':1},historical_regression={'counts':legacy['counts'],'actual_exit':1,'zero_assertion_parent':{'test':'TestW17UpgradeChild','raw_pass_included':True,'gate_credit':False,'reason':'Original top-level helper returns when child environment is absent; real spawned child assertions remain within actual parent invocations.'}},
 old22_build_result=ref(receipts/'old22-build-40e94f3f6e53442fa07068089c0de64a/result.json'),target23_build=ref(receipts/'closure-f7166f2b1e974cbdba4e2855c45966ab/test.invocation.json'),target23_program=ref(receipts/'implementation-df2b17aedb254da9b0fb902ca7f8575f/target23-final-backup.exe'),native_refusals=ref(receipts/'native-refusals-d425787e6b054bf08e0620b7554505ed/result.json'),mirror_missing_compile_negative=ref(receipts/'mirror-compile-negative-b7c0582714774bc694c8c19e15f26962/invocation.json'),closed_sqlite_snapshots=[ref(p) for p in sorted((receipts/focused['directory']/'actual-fixtures').rglob('*.sqlite'))],limitations=limits,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
print(json.dumps({'handoff':ref(out/'handoff.json'),'proposal':ref(out/'followup_test_scope_proposal.json')},ensure_ascii=False))
