import pathlib,hashlib,json,subprocess,datetime,sys
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
PACKAGE=pathlib.Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
OUT=pathlib.Path(__file__).resolve().parent
PROPOSAL='execution/v2.4/receipts/W05/W05-99/host_configuration_handler_scope_readonly_codex/7e34df584e1b45a1b68f06ce62fcdb95/'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,obj):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
start=datetime.datetime.now(datetime.timezone.utc).isoformat();calls=[]
for label,path,args in [('head',ROOT,['rev-parse','HEAD']),('tracked',ROOT,['status','--short','--untracked-files=no']),('protected-candidate',ROOT/'.local/worktrees/codex-w0599-host-configuration-upgrade',['status','--short','--untracked-files=no'])]:
 argv=['git','-C',str(path),*args];p=subprocess.run(argv,capture_output=True)
 calls.append({'actualargv':argv,'exit':p.returncode,'stdout_ref':write(label+'.stdout',p.stdout),'stderr_ref':write(label+'.stderr',p.stderr)})
 assert p.returncode==0
files=['AGENTS.md','execution/project_identity.json',PROPOSAL+'scope_proposal.json',PROPOSAL+'handoff.json',PROPOSAL+'frozen_contract_extract.json',
 'internal/domain/client_protocol.go','internal/domain/client_configuration.go','internal/domain/client_command_identity.go','internal/domain/client_protocol_sessions.go','internal/domain/runtime_sessions_windows.go','internal/domain/runtime_coordinator_windows.go','internal/api/server.go','apps/control/main.go',
 'internal/domain/backup_host_configuration.go','internal/domain/client_configuration_test.go','internal/domain/client_command_identity_test.go','internal/domain/client_session_fence.go','internal/domain/v24_sessions.go','internal/domain/session_service.go','internal/domain/client_protocol_queue_control.go','internal/domain/client_protocol_journal.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_model.go','internal/domain/client_protocol_goals.go',
 'internal/host/host.go','internal/host/vault.go','internal/host/native.go','internal/host/state.go','internal/host/bootstrap.go','internal/host/surface.go','internal/host/model_credential.go','internal/api/v2.go','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json',
 'migrations/sqlite/0023_host_model_configuration.sql','migrations/sqlite/next_v24_sessions.sql','go.mod']
entries=[];missing=[]
for group,root,paths in [('main',ROOT,files),('frozen',PACKAGE,['22_CLIENT_INTERFACE_DETAILS.md','19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md','contracts/client.protocol.schema.json','contracts/domain.schema.json'])]:
 for path in paths:
  p=root/path
  if not p.is_file():missing.append({'group':group,'path':path});continue
  raw=p.read_bytes();r=write('snapshots/'+group+'/'+path,raw)
  entries.append({'group':group,'path':path,'original':str(p),'sha256':sha(raw),'bytes':len(raw),'snapshot_ref':r})
proposal=json.loads((ROOT/(PROPOSAL+'scope_proposal.json')).read_bytes())
assert sha((ROOT/(PROPOSAL+'scope_proposal.json')).read_bytes())=='0aa52199962d9730b8d465920ca0f5ad895e0f3a1342819be8ef2251a62a7c34'
assert sha((ROOT/(PROPOSAL+'handoff.json')).read_bytes())=='8a0f0cacebe0e9639a260e9bed36feacf064e95021681c7d0b9a98dd42e89d34'
write('input.before.json',{'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':entries,'missing_inputs':missing,'timing':'after initial exploratory read; subsequent assessment uses these snapshots; no claim this vector covered earlier reads'})
write('capture.invocation.json',{'actualargv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(pathlib.Path.cwd()),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'git_calls':calls,'operations':'only public exact-file reads plus owned receipt writes','product_calls':0})
print(json.dumps({'count':len(entries),'missing':missing,'namespace':OUT.relative_to(ROOT).as_posix()},ensure_ascii=False))
