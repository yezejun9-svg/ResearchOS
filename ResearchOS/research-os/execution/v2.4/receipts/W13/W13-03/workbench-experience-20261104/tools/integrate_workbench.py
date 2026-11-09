from resume_workbench import REPO, RECEIPT, CANDIDATE, digest, write_json
import json
import subprocess
from datetime import datetime, timezone

BASE = 'ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'
HEAD = '3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5'

def git(*args):
    return subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args], cwd=REPO, check=True, capture_output=True).stdout

def main():
    baseline = json.loads((RECEIPT / 'scope-and-baseline.json').read_bytes())
    review = json.loads((RECEIPT / 'independent-review.json').read_bytes())
    rendered = json.loads((RECEIPT / 'candidate-render-r3/report.json').read_bytes())
    assert review['verdict'] == 'LIMITED_SOURCE_REVIEW_PASSED'
    assert review['suitable_for_limited_source_integration'] is True
    assert review['candidate_head'] == HEAD and not review['open_findings']
    assert rendered['status'] == 'PASS' and len(rendered['checks']) == 54
    assert review['source_manifest'] and {x['path']:x['sha256'] for x in review['source_manifest']} == {x['path']:x['sha256'] for x in rendered['source_manifest']}
    assert git('rev-parse', 'HEAD').decode().strip() == BASE, 'Main moved; reconcile before integration'
    assert git('show', '-s', '--format=%P', HEAD).decode().strip() == BASE
    paths = {x['path'] for x in review['source_manifest']}
    assert set(git('diff', '--name-only', BASE, HEAD).decode().splitlines()) == paths
    for row in review['source_manifest']:
        assert digest((CANDIDATE / row['path']).read_bytes()) == row['sha256'], row['path']
        target = REPO / row['path']
        original = baseline['source_and_dist_before'].get(row['path'])
        assert (digest(target.read_bytes()) if target.exists() else None) == original, 'Main target changed: '+row['path']
    exempt = {'execution/v2.4/checkpoint.json', 'execution/v2.4/HANDOFF_RESUME_PACK.md'}
    for relative, original in baseline['protected_tracked_before'].items():
        if relative in exempt:
            continue
        target = REPO / relative
        assert (digest(target.read_bytes()) if target.exists() else 'ABSENT_BEFORE') == original, 'Protected content changed: '+relative
    state_hash = digest((REPO / 'execution/v2.4/step_state.json').read_bytes())
    assert state_hash == baseline['step_state_sha256_before']
    merged = git('merge', '--ff-only', HEAD)
    (RECEIPT / 'integration.stdout.txt').write_bytes(merged)
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    for row in review['source_manifest']:
        assert digest((REPO / row['path']).read_bytes()) == row['sha256'], 'Integrated source hash mismatch'
    assert git('status', '--porcelain=v1', '-uno') == (RECEIPT / 'git-tracked.before.txt').read_bytes(), 'Existing status changed'
    old_dist = {key:sha for key,sha in baseline['source_and_dist_before'].items() if key.startswith('apps/web/dist/')}
    assert all(digest((REPO / key).read_bytes()) == sha for key,sha in old_dist.items()), 'Old dist changed'
    checkpoint = json.loads((REPO / 'execution/v2.4/checkpoint.json').read_bytes())
    assert len(checkpoint['failure_counters']) == baseline['failure_counter_count_before']
    assert digest(json.dumps(checkpoint['failure_counters'],sort_keys=True,ensure_ascii=False).encode()) == baseline['failure_counter_sha256_before']
    write_json(RECEIPT / 'integration.json', {
        'at':datetime.now(timezone.utc).isoformat(), 'integrator':'codex:/root', 'status':'SOURCE_FAST_FORWARD_INTEGRATED',
        'base_head':BASE,'head':HEAD,'tree':git('show','-s','--format=%T',HEAD).decode().strip(),
        'source_manifest':review['source_manifest'], 'independent_review_sha256':digest((RECEIPT / 'independent-review.json').read_bytes()),
        'render_report_sha256':digest((RECEIPT / 'candidate-render-r3/report.json').read_bytes()),
        'protected_tracked_status_unchanged':True,'protected_tracked_count':len(baseline['protected_tracked_before']),
        'old_dist_preserved_files':len(old_dist),'original_failure_counters_preserved':len(checkpoint['failure_counters']),
        'step_state_unchanged':True,'formal_increment':0,'original_installed_desktop_updated':False,
        'next':'Build source-bound Desktop development bundle if existing resources suffice; installer/native/formal gates remain open.'
    })
    print(json.dumps({'head':HEAD,'source_files':len(paths),'protected_tracked':20,'old_dist_preserved':len(old_dist),'status':'SOURCE_INTEGRATED'}))

if __name__ == '__main__':
    main()
