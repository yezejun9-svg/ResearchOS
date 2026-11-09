from pathlib import Path
import hashlib,json
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\prepared_abandonment_schema_upgrade_revision_codex\\6b0cb88050554e688314092dbebc6ba6")
old=own.parent.parent/'prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2/candidate-root/internal/domain/backup_configuration_upgrade_test.go'
s=old.read_bytes().decode('utf-8'); start=s.index('func TestConfigurationUpgradeFreshAndAdditiveGuard')
part=s[start:]
a='\tctx := context.Background()';assert part.count(a)==1
part=part.replace(a,a+'\r\n\t// This historical guard verifies release23 even when Main has SQL24.\r\n\troot := configurationUpgradeReleaseFixture(t, 23)',1)
part=part.replace('"../../migrations/sqlite/0001_bootstrap.sql"','filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")',1)
part=part.replace('"../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"','filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql")',1)
p=own/'candidate-root/internal/domain/backup_configuration_upgrade_test.go';p.write_bytes((s[:start]+part).encode('utf-8'))
print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}))

