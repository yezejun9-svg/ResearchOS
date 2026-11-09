from pathlib import Path
import datetime,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
refs={
 'migrations/sqlite/0002_domain.sql':'outbox primary/event uniqueness',
 'migrations/sqlite/0023_host_model_configuration.sql':'immutable command identity triple/receipt FK',
 'migrations/sqlite/0024_prepared_run_abandonment.sql':'highest existing numbered source migration',
 'migrations/sqlite/next_v24_sessions.sql':'existing unnumbered client session mapping',
 'internal/domain/store.go':'normal startup inventory/safety and existing sessions addon',
 'internal/domain/backup_migration.go':'hard24 source ceiling, authority detection and prebackup gate',
 'internal/domain/backup_host_configuration.go':'hard24 backup/configuration source/schema support',
 'internal/domain/backup_prepared_abandonment_upgrade.go':'fixed23to24 plan/hash boundary',
 'internal/domain/backup.go':'whole schema, fixed inventory, typed integrity and restore publication',
 'internal/domain/client_command_identity.go':'exact raw headers, canonical identity and unique response lookup',
 'internal/domain/client_protocol.go':'same-label renewal, foreign lease path, original creation attribution and settlement',
 'internal/domain/client_protocol_sessions.go':'fresh MapClientSession epoch1 from caller label',
 'internal/domain/client_protocol_journal.go':'outbox plus watermark inside caller transaction/savepoint',
 'internal/domain/v24_sessions.go':'Map/AdvanceWatermark/HandoffEpoch',
 'internal/domain/client_session_fence.go':'restored session/run barriers',
 'internal/domain/client_protocol_auth.go':'sameTx/service/private principal credential metadata',
 'internal/host/host.go':'ephemeral random boot generation versus stable InstanceID',
 'internal/host/native.go':'typed private peer capability and unchanged legacy wire handlers',
 'internal/host/native_pipe_windows.go':'OS PID producer path',
 'internal/domain/coding_delivery_binding.go':'protected earlier unadopted foundation',
 'internal/domain/coding_delivery_binding_store.go':'protected earlier unadopted foundation',
 'internal/domain/contracts/coding_delivery_bindings.sql':'protected earlier unadopted prepared SQL',
 'internal/domain/coding_delivery_binding_test.go':'protected earlier foundation tests',
 'execution/path_ownership.json':'base Root shared ownership',
 'execution/v2.4/path_ownership.json':'current active integrator plus historical platform owner'
}
files=[{'path':name,'sha256':sha(MAIN/name),'bytes':(MAIN/name).stat().st_size,'supports':support} for name,support in refs.items()]
sql=sorted(path.name for path in (MAIN/'migrations/sqlite').glob('[0-9][0-9][0-9][0-9]_*.sql'))
assert sql[-1]=='0024_prepared_run_abandonment.sql' and len(sql)==24
ownership=json.loads((MAIN/'execution/v2.4/path_ownership.json').read_bytes())
lock=json.loads((MAIN/'execution/toolchains/locked.json').read_bytes())
git=lock['tools']['git']['path']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest()==lock['tools']['git']['sha256']
gitread={}
for name,args in [('head',['rev-parse','HEAD']),('tracked-status',['status','--porcelain=v1','--untracked-files=no'])]:
 argv=[git,'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(MAIN)]+args
 result=subprocess.run(argv,capture_output=True,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),timeout=30)
 assert result.returncode==0
 (ROOT/('main-'+name+'.stdout.raw')).write_bytes(result.stdout)
 (ROOT/('main-'+name+'.stderr.raw')).write_bytes(result.stderr)
 gitread[name]={'argv':argv,'exit_code':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest()}
 if name=='head':gitread['actual_head']=result.stdout.decode('ascii').strip()
 if name=='tracked-status':gitread['tracked_status_lines']=result.stdout.decode('utf-8').splitlines()
doc={'schema':'researchos.cp597-w14-readonly-source-index.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':files,'numbered_source_inventory':sql,'highest_source_version':24,'database_applied_version':'NOT_READ_NOT_CLAIMED','ownership':{'active_integrator':ownership.get('active_integrator'),'historical_shared_integrator':ownership.get('shared_integrator'),'revision':ownership.get('revision'),'policy':'Root serially registers exact new scopes; historical ownership is retained, no Qoder CLI invocation.'},'git_readback':gitread,'recommendation_artifacts':{name:sha(ROOT/name) for name in ('IMPLEMENTATION_BRIEF.md','scope-proposal.json')},'diagnostics':[{'raw_chunk_id':'be4e30','outer_exit_code':1,'classification':'READ_ONLY_EXPECTED_RG_NO_MATCH','message':'Child search found no ordinary startup adoption of old coding-delivery-binding SQL; expected no match. No test or DB activity.'}],'truncated_output_notes':['1b160d ownership broad read truncated; conclusions rely on subsequent exact property reads 1d1509/8da435/4e7c24.','Child5906f6 truncated; backup conclusions rely on subsequent narrow source reads.'],'operations':{'source_control_writes':0,'DB_or_Go_test_or_probe_or_model_runs':0,'migration_numbers_allocated_by_reviewer':0,'formal_increment':0,'counter_reset':False}}
target=ROOT/'source-index.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(doc,stream,indent=2,ensure_ascii=False);stream.write('\n')
print(json.dumps({'index':str(target),'index_sha256':sha(target),'brief_sha256':sha(ROOT/'IMPLEMENTATION_BRIEF.md'),'scope_sha256':sha(ROOT/'scope-proposal.json'),'main_head':gitread['actual_head'],'tracked_status_count':len(gitread['tracked_status_lines']),'highest_source_version':24},ensure_ascii=False))
