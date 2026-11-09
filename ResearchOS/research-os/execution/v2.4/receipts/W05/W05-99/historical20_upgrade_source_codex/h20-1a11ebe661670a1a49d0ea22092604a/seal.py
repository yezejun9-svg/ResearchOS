from pathlib import Path
import json,hashlib,re
N=Path(__file__).parent;C=N/'candidate-root'
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371')
B=T.parents[2]/'execution/v2.4/receipts/W05/W05-99'
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
initial=json.loads((N/'input-pins.json').read_text())
for item in initial:assert pin(Path(item['path']))==item,item['path']
for rel in ['internal/domain/backup_upgrade.go','internal/domain/backup.go','ops/backup/main.go']:
 raw=(T/rel).read_bytes();now=(C/rel).read_text()
 if b'\r\n' in raw:
  assert b'\n' not in raw.replace(b'\r\n',b'')
  (C/rel).write_bytes(now.replace('\n','\r\n').encode())
u=(C/'internal/domain/backup_upgrade.go').read_text()
remove='\tif opt.Plan == History20SchemaUpgradePlan {\n\t\treturn upgradeHistory20Local(ctx, opt, verifier)\n\t}\n'
assert u.count(remove)==1
assert u.replace(remove,'')==(T/'internal/domain/backup_upgrade.go').read_text()
b=(C/'internal/domain/backup.go').read_text();orig=(T/'internal/domain/backup.go').read_text()
field='\tpreserveHistory20UpgradeWorkspaces          func(*sql.DB) error\n'
assert b.count(field)==1
a=b.index('\tif policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {')
z=b.index('\t} else if policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {',a)
undo=b[:a]+'\tif policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {'+b[z+len('\t} else if policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {'):]
assert undo.replace(field,'')==orig
cli=(C/'ops/backup/main.go').read_text().replace('upgrade: exact source release root for the selected fixed plan','upgrade: exact schema13 release root').replace('schema13-to20-research-runtime-v1 or schema20-to21-research-pending-windows-v1 (exact releases only)','schema13-to20-research-runtime-v1 (exact releases only)')
assert cli==(T/'ops/backup/main.go').read_text()
def tokens(s):
 # Lexical delimiter preflight only; this is not a Go parser or compiler.
 out=[];i=0
 while i<len(s):
  if s.startswith('//',i):
   j=s.find('\n',i);i=len(s) if j<0 else j;continue
  if s.startswith('/*',i):
   j=s.find('*/',i+2);assert j>=0;i=j+2;continue
  if s[i] in ['"',"'",chr(96)]:
   q=s[i];i+=1
   while i<len(s):
    if s[i]=='\\' and q!=chr(96):i+=2;continue
    if s[i]==q:i+=1;break
    i+=1
   else:raise AssertionError('unterminated literal')
   continue
  if s[i] in '()[]{}':out.append(s[i])
  i+=1
 return out
for p in C.rglob('*.go'):
 stack=[]
 for t in tokens(p.read_text()):
  if t in '([{':stack.append(t)
  else:assert stack and stack.pop()=={')':'(',']':'[','}':'{'}[t],str(p)
 assert not stack,str(p)
new=(C/'internal/domain/backup_history20_upgrade.go').read_text()
assert 'RestoreBackupMigration' not in (C/'internal/domain/backup_history20_upgrade_test.go').read_text()
assert 'installClientSessionFence' not in new
assert 'sqls[22]' not in new and 'sqls[21]' not in new
assert new.index('upgradeHistory20RecoveryInvariant(original, recovered')<new.index('return upgradeHistory20Migration(ctx, target')
assert new.index('tx.ExecContext(ctx, string(raw))')<new.index('INSERT INTO schema_migrations(version) VALUES(21)')<new.index('return tx.Commit()')
assert 'if !migrated {' in new and 'version != 21' in new
assert hashlib.sha256((T/'migrations/sqlite/0021_research_pending_windows.sql').read_bytes()).hexdigest()=='36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32'
tests=re.findall(r'^func (TestHistory20\w+)\(', (C/'internal/domain/backup_history20_upgrade_test.go').read_text(),re.M)
assert len(tests)==5
additional=[]
for d in ['historical20_upgrade_contract_readonly_codex/h20-contract-20261009-source-review','historical20_resource_route_readonly_codex/current_target_actual_review_01']:
 for name in ['HDF.json','MF.json','report.md']:
  additional.append(pin(B/d/name))
checks={'scope':'SOURCE_TEXT_ONLY','go_parser':False,'gofmt':False,'go_compiler':False,'go_tests_executed':False,'sql_executed':False,'native_executed':False,'git_executed':False,'model_executed':False,'exact_inverse_of_existing_source_changes':True,'lexical_delimiters_balanced':True,'separate_recovery_before_migration':True,'numbered_sql_before_ledger_same_transaction':True,'historical_sql_unchanged':True,'historical_templates_unchanged':True,'test_parents':tests,'test_execution_status':'NOT_RUN','historical20_to24':'OPEN','product_owner_authorization':'NOT_PROVEN','source_program_release_binding':'NOT_PROVEN','source_inputs':len(initial),'additional_research_refs':additional}
put(N/'source-checks.json',checks)
guard={'source_inputs':initial,'research_refs':additional,'all_source_inputs_unchanged':True,'main_or_checkpoint_written':False}
put(N/'guard.final.json',guard)
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ['MF.json','HDF.json','seal.original-tool-io.json']]
put(N/'MF.json',{'schema':'researchos.source-manifest.v1','scope':'SOURCE_ONLY','members':members})
h={'schema':'researchos.history20-upgrade-source-handoff.v1','status':'SOURCE_IMPLEMENTED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_RUNTIME','overall20_to24':'OPEN','candidate_root':str(C),'candidate_files':[pin(p) for p in sorted(C.rglob('*')) if p.is_file()],'manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'report_ref':pin(N/'report.md'),'contract_ref':pin(N/'public-api-contract.md'),'checks_ref':pin(N/'source-checks.json'),'guard_ref':pin(N/'guard.final.json'),'native_or_sql_or_go_execution':False,'failure_origins':[pin(N/'failure-origin.900.json'),pin(N/'failure-origin.901.json')],'stop_after_handoff':True}
put(N/'HDF.json',h)
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members':len(members),'candidates':h['candidate_files'],'test_parents':tests}))
