import hashlib,json
from pathlib import Path
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
PRIOR=MAIN/'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat/T3R-historical-pins.json'
PINS=MAIN/'execution/v2.4/receipts/W17/W17-03/historical22_queue_fixture_resource_map_codex/20261015-current-chat/SOURCE-PINS-502.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads(PRIOR.read_text(encoding='utf-8'))
pins={x['relative_path']:x for x in json.loads(PINS.read_text(encoding='utf-8'))['files']}
checks=[]
for key in ('program_source22','program_target23'):
    item=prior[key];p=Path(item['path']);actual={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    assert actual['bytes']==item['bytes'] and actual['sha256']==item['sha256']
    checks.append(actual)
root=Path(prior['frozen_root']['path'])
release=sorted([p for p in (root/'migrations/sqlite').glob('[0-9][0-9][0-9][0-9]_*.sql') if int(p.name[:4])<=22])
release += [root/'migrations/sqlite/next_v24_sessions.sql']
release += [root/'spec/v2.0/contracts/domain.schema.json',root/'spec/v2.0/contracts/openapi.json']
release += sorted(p for p in (root/'internal/api/contracts').glob('*') if p.is_file())
assert len(release)==prior['frozen_root']['count']==27 and len([p for p in release if p.parent.name=='sqlite' and p.name[:4].isdigit()])==22
for p in release:
    rel=p.relative_to(root).as_posix(); pin=pins[rel]
    actual={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    assert actual['bytes']==pin['bytes'] and actual['sha256']==pin['sha256']
    checks.append(actual)
result={'schema':'researchos.historical22-native-pins-fresh-check.v1','prior_report':str(PRIOR),'prior_report_sha256':sha(PRIOR),'verified_entries':len(checks),'programs':2,'release_files':27,'numbered_sql':22,'entries':checks}
(OUT/'fresh-native-pins.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(result['verified_entries'])
