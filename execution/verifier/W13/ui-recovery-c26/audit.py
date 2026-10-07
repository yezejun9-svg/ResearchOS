"""Read only the frozen public source/evidence inventory; never run product/test helpers."""
import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
WT = ROOT / '.local/worktrees/ui-recovery-c26'
EVIDENCE = WT / 'execution/receipts/W13/c26-recovery'
SOURCE = '11501378b116663a9652c82058809a7fba76553d'
COMMIT = '6993ce4e831ef98b4c577aef7d43ec64350d29cb'
def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args], cwd=WT)
def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
manifest_bytes = (EVIDENCE / 'manifest.json').read_bytes()
m = json.loads(manifest_bytes)
assert digest(manifest_bytes) == 'sha256:b69cefa724c29f7cecbec024326e795c6ceb42443e0fe6ffe2d2ec1495c842e5'
assert m['source']['frozen_source_head'] == SOURCE
assert git('rev-parse', 'HEAD').decode().strip() == COMMIT
assert git('show', COMMIT + ':execution/receipts/W13/c26-recovery/manifest.json') == manifest_bytes
changes = git('diff', '--name-only', SOURCE, COMMIT).decode().splitlines()
assert all(p.startswith('execution/receipts/W13/c26-recovery/') for p in changes)
source_rows = []
for group in ['repaired_product_files', 'test_harness_files', 'remaining_frozen_inputs']:
    for rel, expected in m['source'][group].items():
        assert '__pycache__' not in rel
        current = (WT / rel).read_bytes()
        source_rows.append({'path': rel, 'group': group, 'hash': digest(current),
                            'manifest_match': digest(current) == expected,
                            'source_commit_match': current == git('show', SOURCE + ':' + rel)})
evidence_rows = []
for rel, expected in m['evidence_hashes'].items():
    assert '__pycache__' not in rel
    current = (EVIDENCE / rel).read_bytes()
    evidence_rows.append({'path': rel, 'hash': digest(current), 'manifest_match': digest(current) == expected,
                          'commit_match': current == git('show', COMMIT + ':execution/receipts/W13/c26-recovery/' + rel)})
runs = []
for run in m['runs']:
    before = json.loads((WT / run['before']).read_bytes())
    report = json.loads((WT / run['registered_report']).read_bytes())
    child = json.loads((WT / run['browser_report']).read_bytes())
    run_product_same = all(before['source_manifest'][p] == h for p, h in m['source']['repaired_product_files'].items())
    historical_hash_match = all(digest(git('show', run['head'] + ':' + p)) == h
                                for p, h in m['source']['repaired_product_files'].items())
    raw_binding = digest((WT / run['browser_report']).read_bytes()) == report['child_report_hash']
    raw_files_match = all(digest((WT / run['registered_report']).parent.joinpath(p).read_bytes()) == h
                         for p, h in report['raw_evidence_hashes'].items())
    runs.append({'registered_report': run['registered_report'], 'head_matches': before['code_revision'] == run['head'],
                 'exit_code': report['exit_code'], 'status': report['status'], 'child_status': child['status'],
                 'completed_checks': len(child['checks']), 'composite_check_count_match': len(child['checks']) == run['completed_checks'],
                 'product_matches_final': run_product_same, 'product_matches_historical_commit': historical_hash_match,
                 'raw_child_binding': raw_binding, 'raw_files_match': raw_files_match, 'source_drift': report['source_drift']})
result = {'source_commit': SOURCE, 'evidence_commit': COMMIT, 'input_manifest_hash': digest(manifest_bytes),
          'evidence_only_commit': True, 'evidence_commit_files': len(changes), 'source_files': len(source_rows),
          'evidence_files': len(evidence_rows), 'source_rows': source_rows, 'evidence_rows': evidence_rows, 'runs': runs,
          'new_test_or_browser_execution': False, 'ignored_cache_read_or_deleted': False}
result['all_hash_bindings_match'] = (all(x['manifest_match'] and x['source_commit_match'] for x in source_rows)
    and all(x['manifest_match'] and x['commit_match'] for x in evidence_rows)
    and all(x['head_matches'] and x['composite_check_count_match'] and x['product_matches_final'] and
            x['product_matches_historical_commit'] and x['raw_child_binding'] and x['raw_files_match'] for x in runs))
save('binding-audit.json', result)
print(json.dumps({k: v for k, v in result.items() if k not in ['source_rows', 'evidence_rows', 'runs']}, ensure_ascii=False))
