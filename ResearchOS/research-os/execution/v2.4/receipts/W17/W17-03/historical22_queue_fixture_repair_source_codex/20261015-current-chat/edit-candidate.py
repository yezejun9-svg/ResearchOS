import hashlib
from pathlib import Path

main=Path('D:/作品集/ResearchOS/research-os')
path=main/'.local/worktrees/historical22-queue-fixture-repair-20261015/internal/domain/backup_configuration_upgrade_test.go'
raw=path.read_bytes()
source=raw.decode('utf-8')
start=source.index('func TestConfigurationUpgradeActiveQueueRecovery(t *testing.T) {')
end=source.index('\tf.db.Close()', start)+len('\tf.db.Close()')
old=source[start:end]
assert 'configurationPublicCommand' in old and 'PrepareEffect' in old and 'configurationEvidenceSnapshot' in old
new='''func TestConfigurationUpgradeActiveQueueRecovery(t *testing.T) {
    opt, f := configurationUpgradeFixture(t)
    f.db.Close()
    recordPath := os.Getenv("RESEARCHOS_HISTORICAL22_ACTIVE_RECORD")
    expectedHash := os.Getenv("RESEARCHOS_HISTORICAL22_ACTIVE_RECORD_SHA256")
    if recordPath == "" || expectedHash == "" {
        t.Fatal("pinned historical22 active queue fixture record required")
    }
    recordRaw, e := os.ReadFile(recordPath)
    if e != nil || Digest(recordRaw) != expectedHash { t.Fatal("fixture record pin", e) }
    var record struct {
        DBPath string `json:"db_path"`
        DBSHA string `json:"db_sha256"`
        SchemaMin int `json:"schema_min"`
        SchemaMax int `json:"schema_max"`
        SchemaCount int `json:"schema_count"`
        Identities int `json:"identities_table_count"`
        Project string `json:"project"`
        RunID string `json:"run_id"`
        RunEpoch int64 `json:"run_lease_epoch"`
        BeforeHash string `json:"preupgrade_rows_hash"`
        ExternalDispatches int `json:"external_dispatch_count"`
    }
    if e = json.Unmarshal(recordRaw, &record); e != nil { t.Fatal(e) }
    dbRaw, e := os.ReadFile(record.DBPath)
    if e != nil || Digest(dbRaw) != record.DBSHA || record.SchemaMin != 1 || record.SchemaMax != 22 || record.SchemaCount != 22 || record.Identities != 0 || record.ExternalDispatches != 0 || record.RunID == "" || record.Project == "" {
        t.Fatal("historical22 fixture bytes or claims", e)
    }
    opt.Source = record.DBPath
    sourceDB, e := store.Open(opt.Source)
    if e != nil { t.Fatal(e) }
    var min, max, count, identities int
    if e = sourceDB.QueryRow(`SELECT min(version),max(version),count(*) FROM schema_migrations`).Scan(&min,&max,&count); e != nil || min != 1 || max != 22 || count != 22 { t.Fatal(min,max,count,e) }
    if e = sourceDB.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_command_identities'`).Scan(&identities); e != nil || identities != 0 { t.Fatal(identities,e) }
    before, e := upgradeRows(sourceDB)
    if e != nil || Hash(before) != record.BeforeHash { t.Fatal("historical22 row pin",e) }
    configurationEvidenceSnapshot(t, sourceDB, "source22")
    if e = sourceDB.Close(); e != nil { t.Fatal(e) }
    ctx := context.Background()'''
updated=source[:start]+new+source[end:]
# Only the active-recovery function references its own historical Run value.
fn_end=updated.index('\n// Child process deliberately',start)
active=updated[start:fn_end].replace('run.run["id"]','record.RunID').replace('run.run["lease_epoch"]','record.RunEpoch')
updated=updated[:start]+active+updated[fn_end:]
updated=updated.replace('"database/sql"\n','"database/sql"\n\t"encoding/json"\n',1)
assert updated.count('func TestConfigurationUpgradeActiveQueueRecovery')==1
path.write_text(updated,encoding='utf-8',newline='\n')
print('original_sha256',hashlib.sha256(raw).hexdigest())
print('candidate_sha256',hashlib.sha256(path.read_bytes()).hexdigest())
