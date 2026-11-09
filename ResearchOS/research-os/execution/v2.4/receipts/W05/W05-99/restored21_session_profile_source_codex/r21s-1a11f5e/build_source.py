import difflib,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W05/W05-99';N=Path(__file__).resolve().parent
A=W/'historical21_session_install_contract_readonly_codex/a21-contract-084378e0';H=W/'historical20_upgrade_test_revision_codex/h20r2-1a11ee4f162766098eda3028b0679f2/candidate-root';Q=W/'history20_r2_actual_independent_review_codex/h20r2a-20261009-review'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 actual=pin(v['path']);assert actual['sha256']==v['sha256'].removeprefix('sha256:') and actual['bytes']==v['bytes'];return actual
def save(name,v):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
assert (pin(A/'contract.json')['sha256'],pin(A/'contract.json')['bytes'])==('8cef3ba6540ee9c4f0def36bd1bf9095ebf95cf9e5b22cdaaef98621b52c2495',6516)
assert (pin(A/'MF.json')['sha256'],pin(A/'MF.json')['bytes'])==('90e56fadb90c5794618ff8d804c29cd0b4e5acac7005e3356320901dc7ed38ab',4479)
assert (pin(A/'report.md')['sha256'],pin(A/'report.md')['bytes'])==('d844bee7aee8755ffb25452efb51bb9bb77419af5c91abd400516cb97292584b',17832)
contract=json.loads((A/'contract.json').read_bytes());refs=[verify(v) for v in contract['source_refs'].values()]
refs += [pin(A/n) for n in ('HDF.json','MF.json','contract.json','report.md','source-anchors.json')]
reviewinputs=json.loads((Q/'input-pins.json').read_bytes())
for rel in ('internal/domain/backup.go','internal/domain/backup_upgrade.go','internal/domain/backup_history20_upgrade.go','internal/domain/backup_history20_upgrade_test.go','ops/backup/main.go'):
 p=H/rel;matches=[v for v in reviewinputs if Path(v['path'])==p];assert len(matches)==1;refs.append(verify(matches[0]))
T=Path(contract['source_refs']['queue21to22']['path']).parents[2]
for rel in ('internal/domain/backup_upgrade_test.go','internal/domain/backup_queue_upgrade_test.go','migrations/sqlite/0022_client_command_queue.sql'):
 refs.append(pin(T/rel))
refs += [pin(Q/n) for n in ('HDF.json','MF.json','report.md')]
refs=list({v['path']:v for v in refs}.values());save('input-pins.before.json',refs)
changes=[]
def write(rel,raw,oldpath=None):
 target=N/'source-root'/rel;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(raw)
 old=Path(oldpath).read_bytes() if oldpath else b'';a=old.decode().splitlines(keepends=True);b=raw.decode().splitlines(keepends=True);ops=[]
 for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_lines=a[i:j],new_lines=b[k:l]))
 assert ''.join(x for v in ops for x in v['old_lines']).encode()==old
 assert ''.join(x for v in ops for x in v['new_lines']).encode()==raw
 changes.append(dict(target=rel,original_ref=pin(oldpath) if oldpath else None,original_was_absent=oldpath is None,candidate_ref=pin(target),whole_original_byte_inverse=True,whole_candidate_byte_forward=True,opcodes=ops))
def replace_once(text,a,b):
 assert text.count(a)==1,a;return text.replace(a,b)
queue=Path(contract['source_refs']['queue21to22']['path']).read_text(encoding='utf8')
coordinator=queue[queue.index('func upgradeQueueLocal('):queue.index('func (g *upgradeQueueProtection) refresh(')]
coordinator=replace_once(coordinator,'func upgradeQueueLocal(','func upgradeRestored21Local(')
coordinator=replace_once(coordinator,'expectedSourceSchema, expectedTargetSchema, e := upgradeQueueTemplate(ctx, sqls, contracts)','expectedSourceSchema, expectedSessionSchema, expectedTargetSchema, e := upgradeRestored21Template(ctx, sqls, contracts)')
coordinator=replace_once(coordinator,'policy.preserveQueueUpgradeWorkspaces =','policy.preserveRestored21UpgradeWorkspaces =')
coordinator=replace_once(coordinator,'upgradeQueueRecoveryInvariant(original, rows, opt.Destination)','upgradeRestored21RecoveryInvariant(original, rows, opt.Destination)')
coordinator=replace_once(coordinator,'"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination)}','"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination),\n        "session_schema_hash": expectedSessionSchema, "session_sql_hash": Digest(sqls[22]),\n        "origin_qualification": "RESTORED21_SCHEMA_PROFILE_ONLY_RELEASE_PROGRAM_PROVENANCE_SEPARATE"}')
coordinator=replace_once(coordinator,'svc := &Service{DB: db, Contracts: contracts}','var sessionEvidence Object\n    svc := &Service{DB: db, Contracts: contracts}')
coordinator=replace_once(coordinator,'return restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{','result, restoreErr := restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{')
coordinator=replace_once(coordinator,'return upgradeQueueMigration(ctx, target, sqls[21], sqls[22])','var installErr error\n            sessionEvidence, installErr = upgradeRestored21Sessions(ctx,target,sqls[22],expectedSourceSchema,expectedSessionSchema)\n            if installErr != nil { return installErr }\n            return upgradeQueueMigration(ctx, target, sqls[21], sqls[22])')
coordinator=replace_once(coordinator,'}, policy)\n}', '}, policy)\n    if result.Recovery != nil { result.Recovery["restored21_session_initialization"] = sessionEvidence }\n    return result, restoreErr\n}')
prefix=(N/'profile-prefix.go.txt').read_bytes();write('internal/domain/backup_restored21_upgrade.go',prefix+coordinator.encode())
save('coordinator-derivation.json',dict(original_ref=contract['source_refs']['queue21to22'],original_function='upgradeQueueLocal',candidate_function='upgradeRestored21Local',old_body=queue[queue.index('func upgradeQueueLocal('):queue.index('func (g *upgradeQueueProtection) refresh(')],new_body=coordinator,old_profiles_untouched=True))
path=H/'internal/domain/backup_upgrade.go';text=path.read_bytes().decode();newline='\r\n' if '\r\n' in text else '\n'
needle='func upgradeLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {'
text=replace_once(text,needle,needle+newline+'\tif opt.Plan == Restored21SessionUpgradePlan {'+newline+'\t\treturn upgradeRestored21Local(ctx, opt, verifier)'+newline+'\t}')
write('internal/domain/backup_upgrade.go',text.encode(),path)
path=H/'internal/domain/backup.go';text=path.read_bytes().decode();newline='\r\n' if '\r\n' in text else '\n'
needle='\tpreserveHistory20UpgradeWorkspaces'
lines=text.splitlines(keepends=True);matching=[s for s in lines if s.startswith(needle)];assert len(matching)==1
text=replace_once(text,matching[0],matching[0]+'\tpreserveRestored21UpgradeWorkspaces func(*sql.DB) error'+newline)
needle='\tif policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {'
new='''\tif policy != nil && policy.preserveRestored21UpgradeWorkspaces != nil {
        plan, ok := policy.purpose["plan"].(Object)
        if !ok || policy.format != localUpgradeFormat || plan["id"] != Restored21SessionUpgradePlan {
            return r, fmt.Errorf("RESTORE_RESTORED21_WORKSPACE_POLICY_MISMATCH")
        }
        e = policy.preserveRestored21UpgradeWorkspaces(db)
    } else if policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {'''.replace('\n',newline)
text=replace_once(text,needle,new);write('internal/domain/backup.go',text.encode(),path)
path=H/'ops/backup/main.go';text=path.read_bytes().decode();text=replace_once(text,'schema20-to21-research-pending-windows-v1 (exact releases only)','schema20-to21-research-pending-windows-v1 or restored21-session-to22-client-command-queue-v1 (exact releases only)');write('ops/backup/main.go',text.encode(),path)
save('whole-file-inverse.json',dict(files=changes,source_only=True,Go_compilation_executed=False))
for v in refs:assert pin(v['path'])==v
print(json.dumps(dict(status='SOURCE_MIRRORS_CREATED_NOT_COMPILED',files=[v['candidate_ref'] for v in changes],input_count=len(refs))))
