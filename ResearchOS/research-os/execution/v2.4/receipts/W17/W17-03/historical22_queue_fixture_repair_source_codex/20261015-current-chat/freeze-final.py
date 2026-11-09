import datetime,hashlib,json,subprocess
from pathlib import Path
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
WT=MAIN/'.local/worktrees/historical22-queue-fixture-repair-20261015'
SRC=MAIN/'.local/resources/historical22-active-queue-helper-20261015'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,cwd=WT):return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*args],cwd=cwd).decode().strip()
head=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');parent=git('rev-parse','HEAD^')
assert parent=='2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02'
changes=git('diff','--name-only',parent,head).splitlines();assert changes==['internal/domain/backup_configuration_upgrade_test.go']
assert git('status','--porcelain','--untracked-files=no')==''
main_head=git('rev-parse','HEAD',cwd=MAIN)
assert main_head=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
v=json.loads((OUT/'final-input-verification-02.json').read_text(encoding='utf-8'))
assert len(v['vector_drift'])==len(v['source_502_drift'])==0 and v['closed_db_record_match']
ledger=json.loads((OUT/'FAILURE-LEDGER.json').read_text(encoding='utf-8'))
assert ledger['attempt_count']==18 and ledger['failed_count']==7 and ledger['passed_count']==11
for label,names in [('active7',['TestConfigurationUpgradeActiveQueueRecovery']),('adjacent',['TestConfigurationUpgradeFrozen22ProgramLock','TestConfigurationUpgradeNativeCLI'])]:
    item=json.loads((OUT/f'candidate-{label}.invocation.json').read_text(encoding='utf-8'))
    assert item['native_exit']==0 and item['source_unchanged'] and sorted(item['test_results'])==sorted(names) and all(x=='pass' for x in item['test_results'].values())
record=json.loads((OUT/'closed-source22-05.json').read_text(encoding='utf-8'))
assert record['schema_min']==1 and record['schema_max']==22 and record['schema_count']==22 and record['identities_table_count']==0 and record['external_dispatch_count']==0
assert len(record['public_replies'])==9 and record['row_counts']['client_command_queue']==7 and record['row_counts']['resource_effects']==3
native=json.loads((OUT/'fresh-native-pins.json').read_text(encoding='utf-8'))
assert native['verified_entries']==29 and native['programs']==2 and native['release_files']==27
refs=['reconstruction.json','final-input-verification-02.json','fresh-native-pins.json','closed-source22-05.json','build-helper-05.invocation.json','run-helper-05.invocation.json','candidate-active7.invocation.json','candidate-adjacent.invocation.json','FAILURE-LEDGER.json','candidate-git.patch']
manifest={'schema':'researchos.historical22-active-queue-fixture-repair-final.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'CP496 exact1 source fixture repair','base':parent,'candidate_commit':head,'candidate_tree':tree,'candidate_branch':'historical22-queue-fixture-repair-20261015','candidate_worktree':str(WT),'candidate_clean':True,'changed_paths_exact':changes,'main_head_unchanged':main_head,'historical_git_tree_checkout':False,'historical_reconstruction':'validated 502-file archive copy; old tree object unavailable','historical_helper_path':str(SRC/'internal/domain/active_queue_fixture_child_test.go'),'historical_helper_sha256':sha(SRC/'internal/domain/active_queue_fixture_child_test.go'),'closed_db_path':record['db_path'],'closed_db_sha256':record['db_sha256'],'closed_db_schema':[1,22,22],'identities_table_count':0,'public_replies_count':9,'queue_rows':7,'control_requests':1,'effects':3,'external_dispatch_count':0,'workspace_path_rebound_for_process_boundary':True,'synthetic_phase_advancement':record['synthetic_phase_advancement'],'compiler_prior_input_vector_count':v['prior_vector_count'],'compiler_prior_input_vector_drift':len(v['vector_drift']),'historical_source_pins_count':v['source_502_count'],'historical_source_drift':len(v['source_502_drift']),'historical_native_pins_ref':'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat/T3R-historical-pins.json','focused_tests':{'TestConfigurationUpgradeActiveQueueRecovery':'PASS','TestConfigurationUpgradeFrozen22ProgramLock':'PASS','TestConfigurationUpgradeNativeCLI':'PASS'},'attempt_ledger':{'count':18,'failed':7,'passed':11},'formal_increment':0,'independent_review':'PENDING','main_integration':'NOT_DONE','refs':{name:{'path':str(OUT/name),'sha256':sha(OUT/name),'bytes':(OUT/name).stat().st_size} for name in refs}}
(OUT/'FINAL-02.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidate_commit':head,'candidate_tree':tree,'main_head':main_head,'changed_paths':changes,'ledger_failed':7,'final_sha256':sha(OUT/'FINAL-02.json')},ensure_ascii=False))
