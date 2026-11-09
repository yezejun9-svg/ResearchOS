import hashlib
import json
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99/online_backup_source_resource_map_codex/20261015-current-chat'


def ref(p):
    b = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


files = [ref(p) for p in sorted(E.rglob('*')) if p.is_file()]
external = [ref(B / name) for name in ('collect_online_backup_source_inputs.py', 'collect_online_backup_source_phase02.py', 'collect-online-backup-source-inputs.recipe.json', 'collect-online-backup-source-inputs.stdout.raw', 'collect-online-backup-source-inputs.stderr.raw', 'collect-online-backup-source-inputs.result.json', 'collect-online-backup-source-phase02.recipe.json', 'collect-online-backup-source-phase02.stdout.raw', 'collect-online-backup-source-phase02.stderr.raw', 'collect-online-backup-source-phase02.result.json')]
out = E / 'COLLECTION-manifest.json'
with out.open('x', encoding='utf8') as f:
    json.dump({'schema': 'researchos.online-backup-source-resource-map.v1', 'status': 'EXISTING_PRODUCTION_INTERFACE_IDENTIFIED_NOT_LIVE_QUALIFIED', 'source_commit': '4f4023c956f84d65743f39ce77d6c8899a21ada1', 'files': files, 'external_refs': external, 'actual_DB_API_access': False, 'tests_executed': 0, 'SourceC_or_actual_authority': False, 'formal_increment': 0, 'self_exclusion': 'COLLECTION-manifest.json'}, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'manifest': ref(out), 'files': len(files), 'external_refs': len(external)}))
