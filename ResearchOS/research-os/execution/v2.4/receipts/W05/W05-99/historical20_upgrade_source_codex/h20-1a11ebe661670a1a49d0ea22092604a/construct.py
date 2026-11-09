from pathlib import Path
import hashlib,json,re
N=Path(__file__).parent
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371')
C=N/'candidate-root'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(rel,s):
 p=C/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8',newline='\n')
inputs=[p for p in (T/'internal/domain').glob('backup*.go')]+[T/'internal/domain/client_session_fence.go',T/'internal/domain/auth.go',T/'internal/domain/store.go',T/'ops/backup/main.go']+list((T/'migrations/sqlite').glob('*.sql'))+list((T/'spec/v2.0/contracts').glob('*.json'))
before=[pin(p) for p in inputs]
(N/'input-pins.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
q=(T/'internal/domain/backup_queue_upgrade.go').read_text(encoding='utf-8')
u=(T/'internal/domain/backup_upgrade.go').read_text(encoding='utf-8')
def section(s,a,b):return s[s.index(a):s.index(b)]
release=section(u,'func upgradeRelease(', 'func upgradeOpenExclusive(').replace('upgradeRelease(', 'upgradeHistory20Release(').replace('count != 13 && count != 14 && count != 20','count != 20 && count != 21')
release=release.replace('if e != nil || Digest(raw) != upgradeMigrationHashes[name] {','expected := upgradeMigrationHashes[name]\n\t\tif name == "0021_research_pending_windows.sql" { expected = upgradeHistory20SQLHash }\n\t\tif e != nil || Digest(raw) != expected {')
template=section(q,'func upgradeQueueTemplate(', 'func upgradeQueueMigration(').replace('upgradeQueueTemplate','upgradeHistory20Template').replace('len(sqls) != 23','len(sqls) != 21').replace('sqls[:21]','sqls[:20]')
remove='\tif _, e = db.ExecContext(ctx, string(sqls[22])); e != nil {\n\t\treturn "", "", e\n\t}\n\tif e = installClientSessionFence(ctx, db, false); e != nil {\n\t\treturn "", "", e\n\t}\n'
assert remove in template;template=template.replace(remove,'').replace('upgradeQueueMigration(ctx, db, sqls[21], sqls[22])','upgradeHistory20Migration(ctx, db, sqls[20])')
migration=section(q,'func upgradeQueueMigration(', 'func upgradeQueueFields(').replace('upgradeQueueMigration(ctx context.Context, db *sql.DB, raw, additive []byte)','upgradeHistory20Migration(ctx context.Context, db *sql.DB, raw []byte)').replace('Digest(raw) != upgradeQueueSQLHash || Digest(additive) != upgradeQueueSessionHash','Digest(raw) != upgradeHistory20SQLHash').replace('upgradeVersions(21)','upgradeVersions(20)').replace('VALUES(22)','VALUES(21)').replace('upgradeQueueTables','upgradeHistory20Tables')
start=migration.index('\t// The exact additive schema');end=migration.index('\tif _, e = tx.ExecContext(ctx, string(raw))',start);migration=migration[:start]+migration[end:]
invariant=section(q,'func upgradeQueueRecoveryInvariant(', 'func upgradeQueueRelease(').replace('upgradeQueueRecoveryInvariant(before, after upgradeData, destination string)','upgradeHistory20RecoveryInvariant(before, after upgradeData, destination string, migrated bool)').replace('version != 22','version != 21').replace('upgradeQueueTables[table]','(migrated && upgradeHistory20Tables[table])')
needle='\t\tcase "schema_migrations":\n';assert needle in invariant
invariant=invariant.replace(needle,needle+'\t\t\tif !migrated {\n\t\t\t\tif Hash(old) != Hash(current) { return fmt.Errorf("UPGRADE_RECOVERY_CHANGED_MIGRATIONS") }\n\t\t\t\tcontinue\n\t\t\t}\n')
local=section(q,'func upgradeQueueLocal(', 'func (g *upgradeQueueProtection) refresh(').replace('upgradeQueueLocal','upgradeHistory20Local').replace('upgradeQueueRelease','upgradeHistory20Release').replace('upgradeQueueTemplate','upgradeHistory20Template').replace('opt.SourceRoot, 21','opt.SourceRoot, 20').replace('opt.TargetRoot, 22','opt.TargetRoot, 21').replace('upgradeVersions(21)','upgradeVersions(20)').replace('upgradeVersions(22)','upgradeVersions(21)').replace('exact 1..21','exact 1..20').replace('Digest(sqls[21])','Digest(sqls[20])').replace('preserveQueueUpgradeWorkspaces','preserveHistory20UpgradeWorkspaces').replace('upgradeQueueRecoveryInvariant(original, rows, opt.Destination)','upgradeHistory20RecoveryInvariant(original, rows, opt.Destination, true)')
needle='\t\t\treturn upgradeQueueMigration(ctx, target, sqls[21], sqls[22])';assert needle in local
local=local.replace(needle,'''\t\t\t// Recovery is checked before any numbered migration executes. The roots
\t\t\t// still point inside the unpublished restore stage at this point.
\t\t\tvar sequence int
\t\t\tvar name, databasePath string
\t\t\tif e := target.QueryRowContext(ctx, "PRAGMA database_list").Scan(&sequence, &name, &databasePath); e != nil { return e }
\t\t\trecovered, e := upgradeRows(target)
\t\t\tif e != nil { return e }
\t\t\tif e = upgradeHistory20RecoveryInvariant(original, recovered, filepath.Dir(databasePath), false); e != nil { return e }
\t\t\treturn upgradeHistory20Migration(ctx, target, sqls[20])''')
local=local.replace('"source_versions": versions,','"source_shape": "HISTORICAL20_NUMBERED_BASE_ONLY", "continuation": "SESSION_INSTALLATION_AND_21_TO24_NOT_IMPLEMENTED_BY_THIS_PLAN", "source_versions": versions,')
header='''package domain

// History20SchemaUpgradePlan upgrades the exact numbered schema20 base into an
// isolated schema21 candidate. It does not install additive client sessions,
// qualify a release binary, perform cutover, or authorize a Product Owner.
import (
 "context"
 "database/sql"
 "fmt"
 "os"
 "path/filepath"
 "reflect"
 "strings"

 "researchos.local/research-os/internal/store"
)

const History20SchemaUpgradePlan = "schema20-to21-research-pending-windows-v1"
const upgradeHistory20SQLHash = "sha256:36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32"
var upgradeHistory20Tables = map[string]bool{"research_pending_windows": true}

'''
write('internal/domain/backup_history20_upgrade.go',header+release+template+migration+local+invariant)
needle='func upgradeLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {\n';assert u.count(needle)==1
newu=u.replace(needle,needle+'\tif opt.Plan == History20SchemaUpgradePlan {\n\t\treturn upgradeHistory20Local(ctx, opt, verifier)\n\t}\n')
write('internal/domain/backup_upgrade.go',newu)
b=(T/'internal/domain/backup.go').read_text(encoding='utf-8')
field='\tpreserveHistory20UpgradeWorkspaces          func(*sql.DB) error\n'
b=b.replace('\tpreserveQueueUpgradeWorkspaces',field+'\tpreserveQueueUpgradeWorkspaces',1)
needle='\tif policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {';assert b.count(needle)==1
branch='''\tif policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {
\t\tplan, ok := policy.purpose["plan"].(Object)
\t\tif !ok || policy.format != localUpgradeFormat || plan["id"] != History20SchemaUpgradePlan {
\t\t\treturn r, fmt.Errorf("RESTORE_HISTORY20_WORKSPACE_POLICY_MISMATCH")
\t\t}
\t\te = policy.preserveHistory20UpgradeWorkspaces(db)
\t} else if policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {'''
b=b.replace(needle,branch);write('internal/domain/backup.go',b)
cli=(T/'ops/backup/main.go').read_text(encoding='utf-8')
cli=cli.replace('upgrade: exact schema13 release root','upgrade: exact source release root for the selected fixed plan').replace('schema13-to20-research-runtime-v1 (exact releases only)','schema13-to20-research-runtime-v1 or schema20-to21-research-pending-windows-v1 (exact releases only)')
write('ops/backup/main.go',cli)
assert newu.replace('\tif opt.Plan == History20SchemaUpgradePlan {\n\t\treturn upgradeHistory20Local(ctx, opt, verifier)\n\t}\n','')==u
assert b.replace(field,'').replace(branch,needle)==(T/'internal/domain/backup.go').read_text(encoding='utf-8')
after=[pin(p) for p in inputs];assert before==after
(N/'construction-checks.json').write_text(json.dumps({'source_only':True,'go_executed':False,'sql_executed':False,'native_executed':False,'input_files_unchanged':True,'dispatch_and_policy_exact_inverse':True,'inputs':len(before),'candidates':[pin(p) for p in C.rglob('*') if p.is_file()]},indent=2),encoding='utf-8')
print(json.dumps({'source_constructed':True,'candidate_files':4,'inputs_unchanged':len(before)}))
