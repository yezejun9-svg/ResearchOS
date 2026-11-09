from pathlib import Path
import hashlib,json,uuid
r=Path(r'D:/作品集/ResearchOS/research-os'); b=r/'execution/v2.4/receipts/W05/W05-99'
old=b/'host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'
prior=b/'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6'
own=b/'schema22_public_fixture_bridge_source_codex'/uuid.uuid4().hex
own.mkdir(parents=True,exist_ok=False)
def ref(p):
 v=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)}
pins=[ref(old/'git_source.json'),ref(prior/'HDF.json'),ref(prior/'MF.json'),ref(prior/'candidate-root/internal/domain/backup_configuration_upgrade_test.go')]
manifest=json.loads((old/'git_source.json').read_text(encoding='utf-8'))
assert manifest['commit']=='396287cc5427eb125aaedb8a2b7fadf63e6b9322'
assert len(manifest['files'])==502
for rel,want in manifest['files'].items():
 p=old/'frozen_source'/rel;v=ref(p);assert v['sha256']==want,rel;pins.append(v)
data={'commit':manifest['commit'],'files':manifest['files']}
p=own/'historical22-overlay/internal/domain/schema22_bridge_inputs.json'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n',encoding='utf-8')
(own/'base-refs.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'own':str(own),'inputs':ref(p),'pins':len(pins),'frozen_files':len(manifest['files'])}))

