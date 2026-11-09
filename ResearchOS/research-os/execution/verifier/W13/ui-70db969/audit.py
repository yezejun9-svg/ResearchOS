"""Exact source lineage and frozen machine-contract audit, read only."""
import hashlib, json
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
ROOT = REPO / '.local/worktrees/w13-ui-review'
def digest(path): return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
old_runs = ['5a0d5f262e5b4e4a9f511a1786564330','81f8a13a059a4d46bac844b1fd0b8f7e','2b1f7326c1374823b2ad6dc2a4380911','26c8cc1c78cb431f9cda632e8a3b2b52','88c7be0324ee4191b0459452e33fde11']
audit = {'frozen_head':'70db9698635e4cb363e58908f61ac61bc8decd07','author_lineage':[]}
for run in old_runs:
    path = REPO / 'execution/receipts/W13/frontend' / run / 'report.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    changed = []
    for file, hash_ in report['source_hashes'].items():
        current = ROOT / file
        if not current.is_file() or digest(current) != hash_:
            changed.append({'file':file,'recorded':hash_,'frozen':digest(current) if current.is_file() else None})
    audit['author_lineage'].append({'run':run,'reported_head':report['head'],'checks':report.get('check_count'),
        'responsive_cases':report.get('responsive_case_count'),'changed_since_run':changed,
        'screenshot_hashes_verified':all(digest(path.parent / name)==hash_ for name,hash_ in report.get('screenshot_hashes',{}).items())})
contract = json.loads((ROOT / 'spec/v2.0/contracts/ui.contract.json').read_text(encoding='utf-8'))
schema = json.loads((ROOT / 'spec/v2.0/contracts/domain.schema.json').read_text(encoding='utf-8'))
api = json.loads((ROOT / 'spec/v2.0/contracts/openapi.json').read_text(encoding='utf-8'))
ops = json.loads((ROOT / 'apps/web/src/operations.js').read_text(encoding='utf-8').split('export const operations = ',1)[1])
canonical = {data['operationId']:{'method':method.upper(),'path':path} for path,entry in api['paths'].items() for method,data in entry.items() if isinstance(data,dict) and 'operationId' in data}
audit['operation_mapping'] = [{'operation':op,'matches':canonical.get(op)==value} for op,value in ops.items()]
audit['screen_fields'] = [{'screen':screen['id'],'entity':binding['entity'],'field':binding['field'],'exists':binding['field'] in schema['$defs'][binding['entity']]['properties']} for screen in contract['screens'] for binding in screen['field_bindings']]
audit['declared_operations_registered'] = all(op in ops for screen in contract['screens'] for op in screen['operation_ids'])
audit['scope_notes'] = ['Registration proves method/path mapping, not permission or runtime integration.','Schema binding names are checked mechanically; populated payload and UI behavior are separately exercised by browser reports.','No single historical source head is invented; each report retains its own observed hashes and narrow behavior scope.']
assert all(x['matches'] for x in audit['operation_mapping'])
assert all(x['exists'] for x in audit['screen_fields'])
assert audit['declared_operations_registered']
(OUT / 'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'operations':len(ops),'field_bindings':len(audit['screen_fields']),'lineage_deltas':{r['run']:[x['file'] for x in r['changed_since_run']] for r in audit['author_lineage']}},ensure_ascii=False))
