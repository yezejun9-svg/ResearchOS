from pathlib import Path
import json,hashlib

scope=json.loads(Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_legacy_target_fixture_scope_amendment.json').read_text(encoding='utf-8-sig'))
root=Path(__file__).parent
original={p:Path(p).read_bytes() for p in scope['minimal_diff_bounds']}
for p,raw in original.items():
    assert hashlib.sha256(raw).hexdigest()==scope['source_hashes_at_review'][p]['candidate_sha256']
    (root/(Path(p).name+'.before_target_scope')).write_bytes(raw)

helper='''// Historical fixture validation never starts or migrates the current product.
func upgradeHistoricalFixtureService(t *testing.T, db *sql.DB, root string, version int, restored bool) *Service {
	t.Helper()
	if (version != 13 && version != 14 && version != 20) || (!restored && version != 13) { t.Fatal("invalid explicit historical fixture case") }
	_, sqls, e := upgradeRelease(root, version)
	if e != nil { t.Fatal(e) }
	contracts, e := LoadContracts(filepath.Join(root, "spec/v2.0/contracts"))
	if e != nil { t.Fatal(e) }
	before, e := upgradeRows(db)
	if e != nil { t.Fatal(e) }
	versions, e := backupMigrations(db)
	if e != nil || Hash(versions) != Hash(upgradeVersions(version)) { t.Fatal("historical version mismatch",versions,e) }
	pre, post, e := upgradeTemplate(context.Background(), sqls, contracts)
	if e != nil { t.Fatal(e) }
	want := pre
	if restored { want = post }
	actual, e := backupSchema(db)
	if e != nil || actual != want { t.Fatal("historical schema mismatch", version, restored, e) }
	after, e := upgradeRows(db)
	if e != nil || Hash(before) != Hash(after) { t.Fatal("historical validation changed rows",e) }
	afterSchema,e := backupSchema(db)
	if e != nil || afterSchema != actual { t.Fatal("historical validation changed schema",e) }
	upgradeAssert(t,fmt.Sprintf("HISTORICAL%d-EXACT-SCHEMA-restored-%t",version,restored),true,true)
	return &Service{DB:db,Contracts:contracts}
}

'''
replacements={
'internal/domain/backup_upgrade_test.go':[
'\tupgradeHistoricalFixtureService(t, upgraded, opt.TargetRoot, 14, true)\n',
'\tupgradeAssert(t, "HISTORICAL14-SCHEMA-VALIDATED", upgradeVersions(14), versions)\n',
'\tupgradeHistoricalFixtureService(t, source, opt.SourceRoot, 13, false)\n',
'\tversion := 14\n\tswitch plan { case LocalUpgradePlan: case FinalSchemaUpgradePlan: version = 20; default: t.Fatal("unknown historical plan") }\n\tsvc := upgradeHistoricalFixtureService(t, db, opt.TargetRoot, version, true)\n',
None,None,None,None],
'internal/domain/backup_upgrade_final_test.go':[
'\tupgradeHistoricalFixtureService(t, db, opt.TargetRoot, 20, true)\n',
'\tfinalUpgradeAssert(t, "HISTORICAL20-SCHEMA-VALIDATED", upgradeVersions(20), versions)\n',
'\tupgradeHistoricalFixtureService(t, source, opt.SourceRoot, 13, false)\n',
'\tupgradeHistoricalFixtureService(t, db, opt.SourceRoot, 13, true)\n',
'\tfinalUpgradeAssert(t, "RETAINED-BACKUP-HISTORICAL13-SCHEMA-VALIDATED", upgradeVersions(13), versions)\n']}
spans=scope['minimal_diff_bounds']['internal/domain/backup_upgrade_test.go']
child=spans[4]['original_text'].replace('// Real process boundary using the normal Service.New, without a fixture provider.','// Real process boundary validating an explicitly selected historical fixture schema.')
child=child.replace('\t_, e = New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))\n\tif e != nil {\n\t\tt.Fatal(e)\n\t}\n','\tversion, restored := 0, false\n\tswitch os.Getenv("RESEARCHOS_UPGRADE_CASE") { case "original13": version = 13; case "new14": version, restored = 14, true; default: t.Fatal("explicit historical child case required") }\n\tupgradeHistoricalFixtureService(t, db, root, version, restored)\n')
replacements['internal/domain/backup_upgrade_test.go'][4:]=[child,spans[5]['original_text'],spans[6]['original_text'].replace('child.Env = append(os.Environ(),','child.Env = append(os.Environ(), "RESEARCHOS_UPGRADE_CASE="+entry.label,'),spans[7]['original_text'].replace('NEW-PROCESS-NORMAL-STARTUP','NEW-PROCESS-HISTORICAL-SCHEMA-VALIDATED')]
for p,spans in scope['minimal_diff_bounds'].items():
    edits=[(s['start_byte'],s['end_byte_exclusive'],r.encode()) for s,r in zip(spans,replacements[p])]
    if p==scope['new_helper_insertion']['path']:
        n=scope['new_helper_insertion']['byte_offset'];edits.append((n,n,helper.encode()))
    raw=original[p]
    for a,b,replacement in sorted(edits,reverse=True): raw=raw[:a]+replacement+raw[b:]
    Path(p).write_bytes(raw)

