from pathlib import Path
import json, hashlib, subprocess, datetime
R=Path.cwd(); O=R/'execution/verifier/W18/formal-be03d90d-fd7d-49b8-aa28-98813a37eebc'; CODE='58303736ca02aabbd26bdf666ed536a6f49fb65e'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[]
def ck(k,ok,details=None):
 checks.append({'id':k,'pass':bool(ok),'details':details})
 if not ok:print('FAIL',k)
for run in ['5015e545-e644-433c-ad9c-9c7fb6b1fc8a','77c910ec-66fe-4f00-8f0b-d3607c2c97e1']:
 p=R/'execution/receipts/W18'/run; d=load(p/'report.json'); a={x['assertion_id']:x for x in d['assertions']}; n=load(p/'native-restore.json'); m=n['manifest']; r=n['report']; recovery=r['recovery']
 ck(run+':inventory_snapshot_exact',m['inventory']==r['before']==a['A12-01-INVENTORY']['actual']==a['A12-01-INVENTORY']['expected'])
 ck(run+':manifest_complete',set(['state.sqlite','portable.json']).issubset({x['name'] for x in m['files']}) and len(m['files'])==m['inventory']['uploaded_content']+2 and all(x['hash'].startswith('sha256:') and x['size']>0 for x in m['files']))
 ck(run+':two_projects_and_nonempty_state',a['A12-01-REQUIRED-STATE']['evidence']['ProjectProfile']==2 and all(v>0 for v in a['A12-01-REQUIRED-STATE']['evidence'].values()))
 ck(run+':consistent_wal',a['A12-01-CONSISTENT-WAL']['evidence']['paired_snapshot'][0]==a['A12-01-CONSISTENT-WAL']['evidence']['paired_snapshot'][1]>0)
 ck(run+':receipt_preserved_current',any(x['effective'] and x['receipt_hash']==n['acceptance_hash'] for x in recovery['acceptance_revalidation']['accepted_tasks_recomputed']))
 ck(run+':sealed_source_readback',any(x['hash']==a['A12-01-ACCEPTANCE-HASH']['evidence']['source_hash'] for x in m['files']) and a['A12-01-ACCEPTANCE-HASH']['evidence']['source_relocated'])
 ck(run+':external_fence',recovery['external_actions_dispatched']==0 and recovery['effects_requiring_reconciliation']>0 and recovery['active_runs_fenced']>0 and 'REVOKED' in recovery['credentials'])
 ck(run+':fresh_observation_gate','RESTORE_FRESH_RECONCILIATION_REQUIRED' in a['A12-02-FRESH-OBSERVATION']['evidence']['error'])
 ck(run+':task_checkpoint_resume',a['A12-02-RESUME']['evidence']['new_status']=='RUNNING' and bool(a['A12-02-RESUME']['evidence']['run_id']) and any(x['hash']==a['A12-02-RESUME']['evidence']['checkpoint_hash'] for x in m['files']))
 ck(run+':single_replay_notification',a['A12-02-REPLAY']['actual']==a['A12-02-NOTIFICATION']['actual']==1 and a['A12-02-REPLAY']['evidence']['external_dispatch_count']==0)
 ck(run+':audit_order',m['started_at']<=m['snapshot_completed_at']<=r['started_at']<=r['finished_at'] and r['backup_id']==m['id'] and r['duration_ms']>=0)
 ck(run+':expected_restore_differences',r['status']=='RESTORED_RECONCILIATION_REQUIRED' and r['before']['uploaded_content']==r['after']['uploaded_content'] and r['before']['source_pages']==r['after']['source_pages'] and len(recovery['expected_differences'])==5)
 for name in ['missing','corrupt','wrong-key','wrong-schema','interrupted','migration-failed','irreversible','occupied']:
  e=a['W18-G01-'+name]['evidence'];ck(run+':negative:'+name,e['original_unchanged'] and bool(e['error']))
 ck(run+':restartable_after_failure',a['A12-03-RESTARTABLE']['evidence']=={'backup_retained':True,'retry':'RESTORED_RECONCILIATION_REQUIRED'})
 ck(run+':migration_preflight',all(a['A12-03-MIGRATION-PREFLIGHT']['evidence'][k] for k in ['direct_guard_rejected','startup_rejected']) and not a['A12-03-MIGRATION-PREFLIGHT']['evidence']['migration_applied'])
 for variant in ['DOT','WINDOWS-CASE','WINDOWS-SEPARATORS']:
  good=a['W18-ALIAS-'+variant+'-IDENTICAL']['evidence'];bad=a['W18-ALIAS-'+variant+'-CONFLICT']['evidence'];ck(run+':alias:'+variant,good['both_aliases_read_sealed_bytes'] and good['snapshot_paths_and_artifacts_preserved'] and good['source_and_package_unchanged'] and bad['source_and_package_unchanged'] and bad['destination_unpublished'] and bad['error']=='RESTORE_SOURCE_CONFLICT')
 ck(run+':replaced_native_identity',a['W18-ALIAS-REPLACED-IDENTITY']['evidence']=={'error':'RESTORE_SOURCE_CONFLICT','native_identity_changed':True,'same_bytes':True})
 c=load(p/'cli.json');cm=c['manifest'];cr=c['report'];cmds=c['commands']
 ck(run+':real_cli_sequence',[x['argv'][3] for x in cmds]==['keygen','export','restore'] and all(x['exit_code']==0 for x in cmds))
 ck(run+':cli_restore_complete',cr['backup_id']==cm['id'] and cr['before']==cm['inventory'] and cr['status']=='RESTORED_RECONCILIATION_REQUIRED')
 ck(run+':key_separate',c['key_retained_in_evidence'] is False and not any('key' in x.name for x in (p/'encrypted-cli-package').iterdir()) and cm['key_policy'].startswith('AES-256-GCM'))
 ck(run+':package_manifest_exact',load(p/'encrypted-cli-package/manifest.json')==cm)
 ck(run+':ciphertext_inventory',{x.name for x in (p/'encrypted-cli-package').iterdir()}=={'manifest.json'}|{x['name']+'.enc' for x in cm['files']})
 ck(run+':protected_content_refused',a['W18-G01-PROTECTED-CONTENT']['evidence']=={'error':'PROTECTED_BACKUP_REQUIRES_W17','published':False})
prior=R/'execution/verifier/W18/development-328d913';fix=R/'execution/verifier/W18/alias-repair-66a9420/fix-d46f9e5'
for folder in [prior,fix]:
 index=load(folder/'evidence-index.json')
 for f in (index['files'] if isinstance(index,dict) else index):ck('prior_evidence:'+f['path'],sha((R/f['path']).read_bytes())==f['sha256'].removeprefix('sha256:'))
 for f in load(folder/'source-hashes.json'):
  if f['path'] in ['internal/domain/backup_recovery.go','ops/ci/backup.py'] and folder==prior:continue
  ck('prior_source:'+folder.name+':'+f['path'],sha(subprocess.check_output(['git','show',CODE+':'+f['path']],cwd=R))==f['sha256'].removeprefix('sha256:'))
f=load(prior/'fresh-process.json');c=f['child'];result=c['result']['run'];obs=c['observation']
ck('independent:fresh_process',c['pid']!=c['parent_pid'] and c['pid']==obs['local_fixture_observer_pid'])
ck('independent:same_identity_new_epoch',result['id']==obs['spec']['run_id'] and result['task_id']==obs['spec']['task_id'] and result['lease_epoch']==obs['spec']['epoch']+1)
ck('independent:source_unchanged',f['source_schema_unchanged'])
fixr=load(fix/'review.json');ck('independent:fix_49_pass',fixr['checks']=={'total':49,'pass':49,'fail':0} and fixr['same_probe_identical_to_66a9420'])
summary={'checks':checks,'total':len(checks),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'scope':'Independent semantic audit of sealed raw records, plus previously executed independent actual Windows probes; no redundant test rerun or external provider call.'}
(O/'semantic-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in summary.items() if k!='checks'}))
