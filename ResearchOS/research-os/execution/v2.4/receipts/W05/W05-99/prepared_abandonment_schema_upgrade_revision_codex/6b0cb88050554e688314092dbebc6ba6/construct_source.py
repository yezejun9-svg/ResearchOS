from pathlib import Path
import json, hashlib, uuid
root=Path(r'D:/作品集/ResearchOS/research-os')
old=root/'execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2'
own=root/'execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_revision_codex'/uuid.uuid4().hex
own.mkdir(parents=True,exist_ok=False)
def ref(p):
 b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
pins=[ref(old/'HDF.json'),ref(old/'MF.json')]
for p in (old/'candidate-root').rglob('*'):
 if p.is_file():
  dest=own/p.relative_to(old);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());pins.append(ref(p))
p=own/'candidate-root/internal/domain/backup_configuration_upgrade_test.go'
s=p.read_text(encoding='utf-8')
start=s.index('func TestConfigurationUpgradeFreshAndAdditiveGuard')
end=s.index('\n}', start)+2
part=s[start:end]
a='\tctx := context.Background()'
b='\tctx := context.Background()\n\t// This historical guard verifies release23 even when Main has SQL24.\n\troot := configurationUpgradeReleaseFixture(t, 23)'
assert part.count(a)==1
part=part.replace(a,b)
part=part.replace('"../../migrations/sqlite/0001_bootstrap.sql"','filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")')
part=part.replace('"../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"','filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql")')
assert part!=s[start:end]
s=s[:start]+part+s[end:]
p.write_text(s,encoding='utf-8',newline='\r\n')
(own/'base-refs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
print(json.dumps({'own':str(own),'source':ref(p),'pins':len(pins)}))

