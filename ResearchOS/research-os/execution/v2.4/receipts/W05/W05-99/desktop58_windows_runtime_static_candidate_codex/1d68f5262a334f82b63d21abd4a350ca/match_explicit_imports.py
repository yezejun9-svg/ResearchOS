"""Bounded name-only System32 lookup for explicit PE imports; no native loads."""
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
pe = json.loads((here / 'pe-explicit-static-read.json').read_text(encoding='utf-8'))
catalog_path = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882/runtime-resources.desktop58.json')
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
root = Path('C:/Windows/System32')
names = set()
edges = []
for parent, target in pe['targets'].items():
    for kind in ('imports', 'delay_imports'):
        for name in target['pe'][kind]:
            names.add(name.casefold())
            edges.append({'from': target['path'], 'import_kind': kind, 'raw_name': name})
matched = {}
system32_entries_examined = 0
with os.scandir(root) as stream:
    for ent in stream:
        system32_entries_examined += 1
        if ent.name.casefold() in names:
            matched.setdefault(ent.name.casefold(), []).append(str(root / ent.name))
catalog_paths = {r['path'].casefold(): r for r in catalog['files']}
for edge in edges:
    low = edge['raw_name'].casefold()
    edge['api_set_unresolved'] = low.startswith(('api-ms-', 'ext-ms-'))
    edge['system32_filename_matches'] = matched.get(low, [])
    edge['catalog_matches'] = [catalog_paths[p.casefold()] for p in matched.get(low, []) if p.casefold() in catalog_paths]
result = {'schema':'researchos.desktop58-direct-import-name-matches.v1', 'stage':'SOURCE_RESOURCE_CANDIDATE_ONLY',
          'catalog_ref':str(catalog_path), 'catalog_file_count':len(catalog['files']),
          'system32_entries_examined':system32_entries_examined, 'system32_directory_only':True,
          'edges':edges, 'api_set_mapping_proven':False, 'native_target_executed':False}
with (here / 'direct-import-name-matches.json').open('xb') as stream:
    stream.write((json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf-8'))
missing = sorted({p for e in edges if not e['api_set_unresolved'] and not e['catalog_matches'] for p in e['system32_filename_matches']})
print('edges', len(edges), 'system32_entries', system32_entries_examined, 'missing_direct_non_api', len(missing))
for p in missing: print(p)
