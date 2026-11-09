import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,re,importlib.util,traceback
P=pathlib.Path;O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
T=R/'.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371'
C=B/'historical20_resource_route_readonly_codex/current_target_actual_review_01'
H=C/'historical-source';Q=B/'historical20_upgrade_contract_readonly_codex/h20-contract-20261009-source-review'
A=B/'historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check';AR=B/'historical20_upgrade_source_independent_review_codex/h20r1-20261009-source-review'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
refs={};origin={};checks=[];g=None
def pin(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def add(v,why):
 v={k:v[k] for k in ('path','sha256','bytes')};v['path']=str(P(v['path']));v['sha256']=v['sha256'].removeprefix('sha256:');k=v['path'].casefold()
 if k in refs:assert refs[k]==v,'conflicting Source pin: '+v['path']
 else:refs[k]=v
 origin.setdefault(k,[]).append(why)
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def ck(n,v,detail=None):checks.append(dict(check=n,passed=bool(v),detail=detail))
def main():
 global g
 anchors=[]
 packages=[(C,'a046899ff4d1d46f0e0b2441bc2c54bd336d70756eb97afd4e567086effdee9f',4771,'3971b407c6fe728dd8abfa3fbea14707efe1e05db8190ee031bc16c37542935d',158880),(Q,'e4ff0bfad192bd56806055c2eaf765723bade00f3e7b3c9c0992536481cd10da',2164,'d76152cf29fc4f90c8368f970eefc384913edec65d34a7e3cd6e59fd40eae0ff',31053),(A,'08d1b809b51f4d246c4b272dba3d7e1bad9c9d3090b52f3464d635a8e18e49de',4294,'c46bbdb08c3cec2c29fd04b135e466c3326ed7a7d68edd383051b3de72afe790',3777)]
 for p,hh,hb,mh,mb in packages:
  add(dict(path=str(p/'HDF.json'),sha256=hh,bytes=hb),'Root-provided-HDF')
  add(dict(path=str(p/'MF.json'),sha256=mh,bytes=mb),'Root-provided-MF')
 for p in [C/'historical-source.pins.json',C/'current-source.pins.json',C/'report.md',C/'resource-inventory.json',Q/'report.md',Q/'contract-boundary.json',AR/'HDF.json',AR/'MF.json',AR/'report.md',G,P(__file__),P(sys.executable)]:add(pin(p),'research-input')
 ah=json.loads((A/'HDF.json').read_bytes())
 for v in ah['candidate_files']:add(v,'Source-accepted-H20R1-candidate')
 # The negative reachability claim is limited to these production source roots.
 scan=[]
 for root in [T/'internal/domain',T/'internal/host',T/'internal/api',T/'apps',T/'ops']:
  scan.extend(p for p in root.rglob('*.go') if not p.name.endswith('_test.go'))
 scan=sorted(set(scan))
 for p in scan:add(pin(p),'current-production-reachability-scan')
 for p in sorted((T/'migrations/sqlite').glob('*.sql')):add(pin(p),'current-migration-DDL')
 for rel in ['internal/domain/client_session_bootstrap_test.go','internal/domain/legacy_migration_fixture_test.go','internal/domain/backup_queue_upgrade_test.go','internal/store/store.go','apps/cli/cli_contract.go']:
  p=T/rel
  if p.is_file():add(pin(p),'specific-support-source')
 hp=json.loads((C/'historical-source.pins.json').read_bytes())
 selected=[]
 wanted={'apps/control/main.go','apps/cli/main.go','internal/domain/store.go','internal/domain/backup_migration.go','internal/domain/client_session_fence.go','internal/domain/v24_sessions.go','ops/backup/main.go','go.mod','go.sum'}
 for v in hp:
  rel=v['tree_entry']['path']
  if rel in wanted or rel.startswith('migrations/sqlite/'):
   add(v['source_copy'],'historical-declared-blob');selected.append(v)
 currentpins=json.loads((C/'current-source.pins.json').read_bytes());oldcurrent=[]
 for v in currentpins:
  if v['original']['path'].casefold() in refs:
   add(v['original'],'earlier-current-source-pin');add(v['copy'],'earlier-current-source-copy');oldcurrent.append(v)
 assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
 spec=importlib.util.spec_from_file_location('a21_readonly_guard',G);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
 g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(list(refs.values()))
 def raw(p):return g.get_buffer(str(P(p)))
 def txt(p):return raw(p).decode('utf-8-sig')
 def obj(p):return json.loads(raw(p))
 for v in refs.values():ck('pin:'+v['path'],hashlib.sha256(raw(v['path'])).hexdigest()==v['sha256'] and len(raw(v['path']))==v['bytes'])
 save('input-pins.json',list(refs.values()));save('input-provenance.json',origin)
 blobs=[]
 for v in selected:
  b=raw(v['source_copy']['path']);oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();ok=oid==v['tree_entry']['oid'];ck('historical-blob:'+v['tree_entry']['path'],ok);blobs.append(dict(path=v['tree_entry']['path'],blob_oid=oid,passed=ok))
 save('historical-selected-blob-checks.json',blobs)
 for v in oldcurrent:ck('earlier-T9-snapshot-equal:'+v['original']['path'],raw(v['original']['path'])==raw(v['copy']['path']))
 # Extract function spans by top-level Go declarations. This is Source text analysis, not Go parsing or execution.
 def fn(p,name):
  s=txt(p);matches=list(re.finditer(r'^func [^\n]*\b'+re.escape(name)+r'\(',s,re.M));assert len(matches)==1,(p,name,len(matches));start=matches[0].start();nextdecl=re.search(r'^func ',s[start+1:],re.M);end=start+1+nextdecl.start() if nextdecl else len(s)
  part=s[start:end];line=s[:start].count('\n')+1;anchors.append(dict(path=str(p),symbol=name,start_line=line,end_line=line+part.count('\n'),text=part));return part
 new=fn(T/'internal/domain/store.go','New');guard=fn(T/'internal/domain/backup_migration.go','CheckMigrationSafety');authority=fn(T/'internal/domain/backup_migration.go','migrationAuthorityPresent');session=fn(T/'internal/domain/client_session_fence.go','installClientSessionFence')
 ordinary=fn(T/'internal/domain/client_session_fence.go','EnsureClientSessionFence');queue=fn(T/'internal/domain/backup_queue_upgrade.go','upgradeQueueTemplate');qm=fn(T/'internal/domain/backup_queue_upgrade.go','upgradeQueueMigration');ql=fn(T/'internal/domain/backup_queue_upgrade.go','upgradeQueueLocal');qr=fn(T/'internal/domain/backup_queue_upgrade.go','upgradeQueueRelease')
 bf=fn(T/'internal/domain/backup_recovery.go','backupFence');bs=fn(T/'internal/domain/backup.go','backupSchema');hist=fn(H/'internal/domain/store.go','New')
 ht=fn(A/'candidate-root/internal/domain/backup_history20_upgrade.go','upgradeHistory20Template');hl=fn(A/'candidate-root/internal/domain/backup_history20_upgrade.go','upgradeHistory20Local')
 fn(T/'internal/domain/backup_configuration_upgrade.go','upgradeConfigurationTemplate');fn(T/'internal/domain/backup_configuration_upgrade.go','upgradeConfigurationLocal');fn(T/'internal/domain/session_service.go','OpenClientSession');fn(T/'internal/domain/v24_sessions.go','MapClientSession');fn(T/'apps/cli/cli_contract.go','cliInit')
 for p in [T/'apps/control/main.go',T/'internal/host/host.go',H/'apps/control/main.go',H/'apps/cli/main.go',T/'ops/backup/main.go',T/'internal/domain/client_protocol_sessions.go']:
  lines=txt(p).splitlines();hits=[]
  for i,line in enumerate(lines):
   if any(s in line for s in ['NewCurrentMu(','domain.New(','store.Bootstrap(','bootstrapOwner','session.create','MapClientSession(','command !=','upgrade-local','domain.UpgradeLocal(']):hits.append(dict(line=i+1,text=line))
  anchors.append(dict(path=str(p),line_hits=hits))
 ck('ordinary-constructor-guard-before-DDL',new.index('CheckMigrationSafety(db, files)')<new.index('tx, e := db.Begin()')<new.index('next_v24_sessions.sql')<new.index('installClientSessionFence(context.Background(), tx, false)')<new.index('tx.Commit()'))
 ck('numbered-inventory-validated-first','checkMigrationInventory(db, files)' in new and new.index('checkMigrationInventory(db, files)')<new.index('CheckMigrationSafety(db, files)'))
 ck('authority-rejects-numbered-mismatch-before-additive',guard.index('if applied != len(files)')<guard.index('next_v24_sessions.sql') and 'MIGRATION_PREBACKUP_REQUIRED' in guard and 'Hash(got) != Hash(want)' in guard)
 ck('authority-includes-owner-and-recovery-rows','name == "schema_migrations"' in authority and 'resource_write_lock' in authority and 'if n != 0' in authority and 'auth_credentials' not in authority)
 ck('public-ensure-not-creation-entry','installClientSessionFence(ctx, ex, true)' in ordinary and session.index('if present == 0')<session.index('ALTER TABLE client_sessions') and 'CREATE TABLE IF NOT EXISTS client_sessions' not in session)
 ck('ordinary-fence-does-not-seed-recovery','if restored {' in session and 'INSERT INTO backup_restore_barriers' in session and 'ON CONFLICT(project,run) DO UPDATE' in session)
 ck('historical-constructor-numbered-only','next_v24_sessions' not in hist and 'installClientSessionFence' not in hist and 'EnsureClientSessionFence' not in hist and 'INSERT OR IGNORE INTO schema_migrations' in hist)
 ddl=txt(T/'migrations/sqlite/next_v24_sessions.sql');ddlhash=hashlib.sha256(raw(T/'migrations/sqlite/next_v24_sessions.sql')).hexdigest();ck('current-additive-pin',ddlhash=='1ca3930f96f7c2c99e7bc6e668dd5658393264cf1e6bf6352b47fb3de8c7dfe3')
 ck('current-additive-no-version-ledger-write',not re.search(r'\b(?:INSERT|UPDATE|DELETE)\b[^;]*schema_migrations',ddl,re.I) and 'transcript_artifact_id' in ddl and 'CREATE UNIQUE INDEX IF NOT EXISTS client_sessions_run' in ddl)
 ck('queue-source-template-before-run-restore-fence',queue.index('string(sqls[22])')<queue.index('installClientSessionFence(ctx, db, false)')<queue.index('before, e := backupSchema(db)')<queue.index('.backupFence(ctx)'))
 ck('H20-target-template-after-run-restore-fence',ht.index('.backupFence(ctx)')<ht.index('upgradeHistory20Migration(ctx, db, sqls[20])')<ht.index('after, e := backupSchema(db)') and 'installClientSessionFence' not in ht)
 numbered=[p for p in (T/'migrations/sqlite').glob('0*.sql')]
 numbered_fence_hits=[str(p) for p in numbered if any(x in txt(p) for x in ['backup_require_fresh_observation','backup_restore_barriers','client_sessions'])]
 ck('numbered-migrations-do-not-create-session-or-restore-fence',not numbered_fence_hits,numbered_fence_hits)
 ck('run-restore-trigger-exists-and-is-global-schema','CREATE TRIGGER IF NOT EXISTS backup_require_fresh_observation BEFORE UPDATE ON domain_objects' in bf and 'SELECT type,name,tbl_name,coalesce(sql,\'\') FROM sqlite_master ORDER BY type,name' in bs)
 ck('queue-source-strict-schema-before-snapshot',ql.index('schema != expectedSourceSchema')<ql.index('svc.createBackupPolicy') and 'UPGRADE_SOURCE_SCHEMA' in ql)
 ck('queue-reinstall-explicitly-not-repair','no-op, not a repair' in qm and 'UPGRADE_MIGRATION_MUTATED_HISTORY' in qm and 'UPGRADE_UNEXPECTED_TABLE' in qm)
 ck('queue-release-exact-numbered-additive','len(files) != count' in qr and 'Digest(additive) != upgradeQueueSessionHash' in qr and 'UPGRADE_CONTRACT_HASH' in qr)
 ck('program-hash-not-program-invocation','programHashes[name] = Digest(raw)' in ql and 'exec.Command' not in ql and 'exec.Command' not in hl)
 r1=obj(AR/'HDF.json');ck('H20R1-only-Source-accepted',r1['status']=='SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME' and r1['formal_acceptance'] is False and r1['overall20_to24']=='OPEN')
 keywords=['EnsureClientSessionFence(', 'installClientSessionFence(', 'next_v24_sessions.sql', 'domain.New(', 'domain.NewCurrentMu(']
 calls=[]
 for p in scan:
  for i,line in enumerate(txt(p).splitlines()):
   if any(x in line for x in keywords):calls.append(dict(path=str(p),line=i+1,text=line))
 save('production-reachability-scan.json',dict(roots=[str(T/x) for x in ['internal/domain','internal/host','internal/api','apps','ops']],scanned_files=[pin(p) for p in scan],patterns=keywords,matches=calls,qualification='Text inventory and manual call-chain review, not runtime trace or complete Go type resolution.'))
 save('source-anchors.json',anchors)
 save('static-findings.json',dict(schema='researchos.A21-session-continuation-static-findings.v1',checks=checks,remaining_findings=[v for v in checks if not v['passed']],inputs=len(refs),source_scan_files=len(scan),historical_blobs=len(blobs),numbered_migrations=len(numbered),current_additive_sha256=ddlhash,current_additive_bytes=len(raw(T/'migrations/sqlite/next_v24_sessions.sql')),H20_restored21_extra_run_trigger='backup_require_fresh_observation',SQL_executed=False,Go_executed=False,formal_acceptance=False))
 closure=g.close();save('guard.final.json',closure);assert closure['closed'] and closure['retained_handles_count']==0 and not closure['errors']
 print(json.dumps(dict(status='READONLY_SOURCE_CAPTURE_COMPLETE',checks=len(checks),passed=sum(v['passed'] for v in checks),remaining=[v for v in checks if not v['passed']],inputs=len(refs),source_scan_files=len(scan),historical_blobs=len(blobs),all_guards_closed=True)))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if g is not None:
  c=g.close()
  if not (O/'guard.final.json').exists():save('guard.final.json',c)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
