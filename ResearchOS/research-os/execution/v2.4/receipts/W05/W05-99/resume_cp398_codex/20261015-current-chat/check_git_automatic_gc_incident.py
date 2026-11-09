import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99'
O = E / 'git_automatic_gc_incident_codex/20261015-current-chat'
O.mkdir(parents=True, exist_ok=False)


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def new(p, v):
    with p.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')


def ref(p):
    v = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(v).hexdigest(), 'bytes': len(v)}


index = []


def git(label, args, stdin=None, cwd=R):
    argv = ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0'] + args
    recipe = O / (label + '.recipe.json')
    out, err = O / (label + '.stdout.raw'), O / (label + '.stderr.raw')
    input_ref = None
    if stdin is not None:
        inp = O / (label + '.stdin.raw')
        with inp.open('xb') as f:
            f.write(stdin)
        input_ref = ref(inp)
    new(recipe, {'argv': argv, 'cwd': str(cwd), 'env_override': {}, 'inherited_environment': True,
                 'stdin_ref': input_ref, 'read_only': True,
                 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    with out.open('xb') as fo, err.open('xb') as fe:
        p = subprocess.run(argv, cwd=cwd, input=stdin, stdout=fo, stderr=fe)
    result = {'label': label, 'recipe': ref(recipe), 'stdout': ref(out), 'stderr': ref(err), 'native_exit_code': p.returncode}
    new(O / (label + '.result.json'), result)
    index.append(result)
    assert p.returncode == 0, result
    return out.read_bytes()


new(O / 'scope.json', {'purpose': 'Bounded read-only containment after automatic GC triggered by B commit lacking command-local suppression',
    'no_git_object_or_configuration_writes': True, 'no_process_or_actual_root_actions': True,
    'historical_repair_or_full_fsck': False, 'formal_increment': 0})
manifest = read(E / 'qualification_failure_b_source_codex/20261015-current-chat/B-evidence-manifest.json')
assert manifest['candidate_commit'] == '75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603'
assert manifest['candidate_tree'] == 'ba3f9d4c101df39ab17856158d5fc72a9f0600ce'
head = git('01-main-head', ['rev-parse', 'HEAD']).decode().strip()
assert head == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
dirty = git('02-main-dirty', ['status', '--porcelain=v1', '--untracked-files=no'])
assert len(dirty.splitlines()) == 20
assert not git('03-main-index', ['diff', '--cached', '--name-only'])
assert ref(R / '.git/config')['sha256'] == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
protected = []
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    actual = ref(R / item['path'])
    assert actual['sha256'] == item['sha256']
    protected.append(actual)
assert len(protected) == 9
trees = []
for number, (name, commit) in enumerate((('Main', head), ('A', manifest['base_commit']), ('B', manifest['candidate_commit'])), 4):
    listing = git(f'{number:02d}-{name}-tree', ['ls-tree', '-r', '-t', commit])
    objects = {commit}
    for line in listing.splitlines():
        objects.add(line.split(b'\t', 1)[0].split()[2].decode('ascii'))
    root_tree = git(f'{number:02d}-{name}-root', ['rev-parse', commit + '^{tree}']).decode().strip()
    objects.add(root_tree)
    checks = git(f'{number:02d}-{name}-objects', ['cat-file', '--batch-check'], stdin=('\n'.join(sorted(objects)) + '\n').encode())
    rows = checks.decode().splitlines()
    assert len(rows) == len(objects)
    assert all(len(row.split()) == 3 and row.split()[1] in ('blob', 'tree', 'commit') and row.split()[2].isdigit() for row in rows)
    trees.append({'name': name, 'commit': commit, 'tree': root_tree, 'objects': len(objects),
                  'all_current_tree_object_headers_readable': True, 'full_ancestral_history_checked': False})
assert not git('07-B-dirty', ['status', '--porcelain=v1', '--untracked-files=no'], cwd=Path(manifest['worktree']))
old = E / 'git_object_recovery_diagnosis_codex/20261015-current-chat/historical-remaining62.json'
remaining = read(old)
bad = '064d33818101c336e5a587e65e844c107d2e97f2'
assert remaining['count'] == 62 and bad in remaining['objects'] and remaining['objects'][bad]['type'] == 'tree'
new(O / 'command-index.json', index)
new(O / 'containment.json', {'status': 'CURRENT_SELECTED_TREES_AVAILABLE_HISTORICAL_GAP_REMAINS',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'main_head': head,
    'main_dirty_lines': 20, 'main_index_empty': True, 'git_config': ref(R / '.git/config'),
    'protected_source': protected, 'selected_trees': trees,
    'old_remaining62_ref': ref(old), 'gc_bad_tree': bad, 'gc_bad_tree_already_in_preserved_missing_set': True,
    'execution_deviation': 'B commit omitted required command-local maintenance.auto=false and gc.auto=0; automatic GC/repack failed',
    'scope_limit': 'Read-only current selected tree/header availability; does not certify full history, no causal claim about old missing pack',
    'source_or_actual_acceptance': False, 'formal_increment': 0})
files = [ref(p) for p in sorted(O.iterdir()) if p.is_file()]
new(O / 'COLLECTION-manifest.json', {'files': files, 'self_exclusion': 'COLLECTION-manifest.json'})
print(json.dumps({'containment': ref(O / 'containment.json'), 'manifest': ref(O / 'COLLECTION-manifest.json'), 'trees': trees, 'native_nonzero_count': 0}))
