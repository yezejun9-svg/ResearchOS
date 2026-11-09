from pathlib import Path

main = Path('D:/作品集/ResearchOS/research-os')
candidate = main / '.local/worktrees/historical22-queue-fixture-repair-20261015/internal/domain/backup_configuration_upgrade_test.go'
target = main / '.local/resources/historical22-active-queue-helper-20261015/internal/domain/active_queue_fixture_child_test.go'
assert not target.exists()
source = candidate.read_text(encoding='utf-8')
start = source.index('\tclient := "queue-upgrade-client"', source.index('func TestConfigurationUpgradeActiveQueueRecovery'))
end = source.index('\tconfigurationEvidenceSnapshot(t, f.db, "source22")', start)
body = source[start:end]
body = body.replace('configurationSchema(t)', 'clientHistoryDoc(t)')
body = body.replace('configurationUpgradePort{workspace, Fail(503, "RESOURCE_UNAVAILABLE", "storage-only fixture; no provider")}', 'goalClientPort{workspace: workspace, model: "fixture-unqualified-model", admitErr: Fail(503, "RESOURCE_UNAVAILABLE", "storage-only fixture; no provider")}')
body = body.replace('configurationUpgradePort{workspace, nil}', 'goalClientPort{workspace: workspace, model: "fixture-unqualified-model"}')
body = body.replace('configurationPublicCommand(t, f, svc, ', 'historicalPublicCommand(t, f, svc, &replies, ')
body = body.replace('\tstart := historicalPublicCommand', '\tvar replies []any\n\tstart := historicalPublicCommand', 1)
header = '''//go:build windows

package domain

import (
    "context"
    "encoding/json"
    "os"
    "path/filepath"
    "strings"
    "testing"
    "time"
)

func historicalPublicCommand(t *testing.T, f *fixture, svc *ClientService, replies *[]any, env *Envelope) *Response {
    t.Helper()
    reply, replay := goalCommand(t, f, svc, env)
    if replay { t.Fatal("unexpected public replay") }
    *replies = append(*replies, Object{"method": *env.Method, "command_id": *env.CommandID, "response": reply})
    return reply
}

func TestHistorical22ActiveQueueFixtureChild(t *testing.T) {
    output := os.Getenv("RESEARCHOS_HISTORICAL22_FIXTURE_OUT")
    record := os.Getenv("RESEARCHOS_HISTORICAL22_RECORD_OUT")
    if output == "" || record == "" { t.Skip("explicit isolated fixture output required") }
    if _, e := os.Stat(output); !os.IsNotExist(e) { t.Fatal("fixture output exists", e) }
    if _, e := os.Stat(record); !os.IsNotExist(e) { t.Fatal("record output exists", e) }
    opt, f := queueUpgradeFixture(t)
    raw, e := os.ReadFile("../../migrations/sqlite/0022_client_command_queue.sql")
    if e != nil { t.Fatal(e) }
    add, e := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
    if e != nil { t.Fatal(e) }
    if e = upgradeQueueMigration(context.Background(), f.db, raw, add); e != nil { t.Fatal(e) }
    _ = opt
    ctx := context.Background()
    var workspace string
    if e = f.db.QueryRow(`SELECT id FROM domain_objects WHERE kind='WorkspaceBinding'`).Scan(&workspace); e != nil { t.Fatal(e) }
'''
tail = '''
    var min, max, count, identities int
    if e = f.db.QueryRow(`SELECT min(version),max(version),count(*) FROM schema_migrations`).Scan(&min, &max, &count); e != nil || min != 1 || max != 22 || count != 22 { t.Fatal(min,max,count,e) }
    if e = f.db.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_command_identities'`).Scan(&identities); e != nil || identities != 0 { t.Fatal(identities,e) }
    rows, e := upgradeRows(f.db)
    if e != nil { t.Fatal(e) }
    if _, e = f.db.Exec(`VACUUM INTO '` + strings.ReplaceAll(output, `'`, `''`) + `'`); e != nil { t.Fatal(e) }
    if e = f.db.Close(); e != nil { t.Fatal(e) }
    dbBytes, e := os.ReadFile(output)
    if e != nil { t.Fatal(e) }
    facts := Object{"schema_min":min,"schema_max":max,"schema_count":count,"identities_table_count":identities,"db_path":output,"db_sha256":Digest(dbBytes),"db_bytes":len(dbBytes),"project":f.project,"run_id":run.run["id"],"run_lease_epoch":run.run["lease_epoch"],"session_id":sid,"public_replies":replies,"preupgrade_rows_hash":Hash(rows),"row_counts":Object{"client_command_queue":len(rows["client_command_queue"]),"client_control_requests":len(rows["client_control_requests"]),"client_control_receipts":len(rows["client_control_receipts"]),"resource_effects":len(rows["resource_effects"]),"idempotency":len(rows["idempotency"]),"domain_objects":len(rows["domain_objects"]),"runtime_dispatches":len(rows["runtime_dispatches"])},"external_dispatch_count":0,"synthetic_phase_advancement":"fixture-only: appendClientReceipt + queue state update for six non-ENQUEUED sends; no provider dispatch"}
    encoded, e := json.MarshalIndent(facts, "", "  ")
    if e != nil { t.Fatal(e) }
    if e = os.WriteFile(record, append(encoded,'\\n'), 0600); e != nil { t.Fatal(e) }
    t.Log("HISTORICAL22_ACTIVE_QUEUE_FIXTURE " + string(encoded))
    _ = filepath.Base(output)
}
'''
target.write_text(header + body + tail, encoding='utf-8')
print(target)
