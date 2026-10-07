import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('D:/作品集/ResearchOS/research-os'); OUT=Path(__file__).resolve().parent
PACKAGE=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
FOUND='fef0ee2d56351e74ceed11b0b37d3f87e9c83494'
FREC='execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_executor_codex/implementation-1cc1b20e27534da8a78e7350fa533ea3/'
REVIEW='execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json'
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def write(name,v):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def save(name,b):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
 return ref(p)
invocations=[]
def run(name,argv,accepted=(0,)):
 start=now();p=subprocess.run(argv,cwd=ROOT,capture_output=True)
 row={'actualargv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':now(),'exit':p.returncode,
 'stdout_ref':save(name+'.stdout.raw',p.stdout),'stderr_ref':save(name+'.stderr.raw',p.stderr),'measurement_mode':'READ_ONLY_PUBLIC_SOURCE'}
 write(name+'.invocation.json',row);invocations.append(ref(OUT/(name+'.invocation.json')))
 if p.returncode not in accepted:raise RuntimeError(name)
 return p.stdout
head=run('head.before',['git','rev-parse','HEAD']).decode().strip()
run('status.before',['git','status','--porcelain=v1','--untracked-files=no'])
paths=['AGENTS.md','execution/project_identity.json','execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json',
 'internal/domain/client_protocol.go','internal/domain/client_protocol_queue_control.go','internal/domain/client_protocol_journal.go',
 'internal/domain/client_protocol_queue_control_test.go','internal/domain/client_protocol_control_windows_test.go',
 'internal/domain/client_command_queue.go','internal/domain/durability.go','internal/domain/runtime.go','internal/domain/runtime_command_queue_windows.go',
 'internal/domain/backup.go','internal/domain/backup_command_queue.go','internal/domain/backup_command_queue_test.go',
 'internal/domain/backup_migration.go','internal/domain/backup_boundaries_test.go','internal/domain/backup_recovery.go',
 'internal/domain/backup_workspace.go','internal/domain/backup_upgrade.go','internal/domain/backup_queue_upgrade.go',
 'internal/domain/backup_queue_upgrade_test.go','internal/domain/backup_upgrade_final.go','internal/domain/store.go',
 'internal/api/contracts/client.protocol.schema.json',REVIEW]
paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'migrations/sqlite').glob('*.sql'))]
before=[]
for path in paths:
 b=(ROOT/path).read_bytes();before.append({'origin':'MAIN','path':path,'sha256':sha(b),'bytes':len(b),'snapshot_ref':save('snapshots/main/'+path,b)})
for path in ['22_CLIENT_INTERFACE_DETAILS.md','contracts/client.protocol.schema.json','contracts/acceptance.json','contracts/harness.contract.json','tasks/steps/W05-99.md']:
 b=(PACKAGE/path).read_bytes();before.append({'origin':'FROZEN_PACKAGE','path':str(PACKAGE/path),'sha256':sha(b),'bytes':len(b),'snapshot_ref':save('snapshots/package/'+path,b)})
immutable=[]
for idx,path in enumerate(['migrations/sqlite/0023_host_model_configuration.sql','internal/domain/client_command_identity.go',
 'internal/domain/client_command_identity_test.go','internal/domain/client_configuration.go',FREC+'cancel_finalization_issue.json',
 FREC+'run-238574514fa345f89e5468d9c9be5237/result.json',FREC+'run-238574514fa345f89e5468d9c9be5237/stdout.raw']):
 data=run('foundation-blob-'+str(idx),['git','show',FOUND+':'+path],(0,128))
 rc=json.loads((OUT/('foundation-blob-'+str(idx)+'.invocation.json')).read_bytes())['exit']
 if rc==0:immutable.append({'commit':FOUND,'path':path,'sha256':sha(data),'raw_ref':ref(OUT/('foundation-blob-'+str(idx)+'.stdout.raw'))})
 else:immutable.append({'commit':FOUND,'path':path,'status':'REQUESTED_PATH_NOT_PRESENT','invocation_ref':ref(OUT/('foundation-blob-'+str(idx)+'.invocation.json'))})
run('foundation-run-tree',['git','ls-tree','-r','--name-only',FOUND,'--',FREC+'run-238574514fa345f89e5468d9c9be5237/'])
run('source-call-sites',['rg','-n','finalizeClientCancel|UPDATE idempotency|validateBackupQueue|backupInventory|CheckMigrationSafety|QueueSchemaUpgradePlan|upgradeQueueRelease|effectsReconciled|acknowledgeRunCancellation','internal/domain','-g','*.go'])
run('frozen-cancel-contract',['rg','-n','ACKNOWLEDGED|CANCEL|settled|幂等|取消',str(PACKAGE/'22_CLIENT_INTERFACE_DETAILS.md')])
run('trigger-and-control-schema',['rg','-n','idempotency_immutable|client_control_requests|final_response|CREATE TRIGGER','migrations/sqlite/0002_domain.sql','migrations/sqlite/0022_client_command_queue.sql'])
write('source.before.json',{'observed_head':head,'inputs':before,'immutable_foundation_inputs':immutable})
print(json.dumps({'head':head,'inputs':len(before),'immutable':immutable,'namespace':OUT.relative_to(ROOT).as_posix()},ensure_ascii=False))
