import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99'
O = E / 'qualification_repair_composition_input_map_codex/20261015-current-chat'
BASE = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
A = 'f48fca0e4013bda19913a34d91da0cd23157a08b'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def new(p, obj):
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def ref(p):
    data = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


O.mkdir(parents=True, exist_ok=False)
new(O / 'command.json', {'argv': [os.sys.executable, '-B', '-X', 'utf8', str(Path(__file__))], 'cwd': str(R), 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'kind': 'READ_ONLY_SOURCE_AND_SCOPE_MAP', 'source_write_authority': False, 'actual_authority': False})
shared = [R / 'execution/v2.4' / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'HANDOFF_RESUME_PACK.md']]
before = {p: p.read_bytes() for p in shared}
before_refs = [ref(p) for p in shared]
commands = []


def git(name, args):
    argv = ['git'] + args
    new(O / (name + '.command.json'), {'argv': argv, 'cwd': str(R), 'relevant_env': {'GIT_OPTIONAL_LOCKS': '0'}})
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    p = subprocess.run(argv, cwd=R, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (O / (name + '.stdout.raw')).write_bytes(p.stdout)
    (O / (name + '.stderr.raw')).write_bytes(p.stderr)
    new(O / (name + '.result.json'), {'exit': p.returncode})
    commands.append({'name': name, 'exit': p.returncode})
    p.check_returncode()
    return p.stdout.decode('utf8').strip()


assert git('head', ['rev-parse', 'HEAD']) == BASE
assert not git('index', ['diff', '--cached', '--name-only'])
status = git('status', ['status', '--short', '--untracked-files=no'])
assert len(status.splitlines()) == 20
a_paths = git('A-paths', ['diff', '--name-only', BASE, A]).splitlines()
assert len(a_paths) == 15
scope_paths = {
    'STOP': B / 'continuation-cp508/owned-stop-anchor-revision02-source-scope.json',
    'B': B / 'continuation-cp512/qualification-failure-B-source-scope.json',
    'C': E / 'qualification_failure_revision03_architecture_codex/20261015-current-chat/C-lease-exact-scope.json',
    'D': E / 'qualification_failure_revision02_architecture_codex/20261015-current-chat/D-exact-scope.json',
}
fields = {
    'STOP': ['allowed_existing_production', 'allowed_existing_tests', 'allowed_new_paths'],
    'B': ['allowed_existing_source', 'allowed_new_source', 'allowed_tests'],
    'C': ['production_existing', 'production_new', 'tests_allowed'],
    'D': ['production_existing', 'production_new', 'tests_allowed'],
}
paths = {'A': a_paths}
for label, p in scope_paths.items():
    d = read(p)
    paths[label] = [item for key in fields[label] for item in d[key]]
    assert len(paths[label]) == len(set(paths[label]))
assert {k: len(v) for k, v in paths.items()} == {'A': 15, 'STOP': 19, 'B': 9, 'C': 51, 'D': 17}
overlap = {}
labels = list(paths)
for i, x in enumerate(labels):
    for y in labels[i + 1:]:
        common = sorted(set(paths[x]) & set(paths[y]))
        overlap[x + '+' + y] = common
guards = read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']
for item in guards:
    assert ref(R / item['path'])['sha256'] == item['sha256']
result = {
    'schema': 'researchos.qualification-repair-composition-input-map.v1',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'base': BASE,
    'A_accepted_candidate': A,
    'A_status': 'LIMITED_SOURCE_ACCEPTED_NOT_MAIN',
    'B_STOP_status': 'ACTIVE_SOURCE_NOT_FROZEN_NOT_ACCEPTED',
    'C_D_status': 'DESIGN_ONLY_NO_SOURCE_AUTHORITY',
    'input_refs': [ref(p) for p in scope_paths.values()] + [ref(B / 'continuation-cp511/C-design-adopted-constraints.json')],
    'paths': paths,
    'pairwise_overlap': overlap,
    'combined_unique_path_count': len(set().union(*(set(v) for v in paths.values()))),
    'composition_rules': [
        'Use accepted A candidate and subsequently independently accepted B candidate as C base; never recreate B private proof API as a fixture or stub.',
        'STOP has separate exact19 paths; only its independently accepted complete candidate may be composed. No acceptance follows from disjoint paths.',
        'C carries all adopted C-LD01..03 and classification addenda. C design may be implemented only after new Root source card and concurrency slot.',
        'D uses actual accepted B/C validation helper and existing real JS runners; new Root source card must bind final accepted base and exact source paths.',
        'Reconcile overlapping source changes in isolated composition, retain protected Main dirty bytes and all historical records; Main remains unchanged until concrete source review and integration scope.',
        'Schema25 source remains a later separately scoped composition; no schema24 product migration or original operation is authorized by this map.',
    ],
    'shared_before': before_refs,
    'protected_source_guards': guards,
    'commands': commands,
    'formal_increment': 0,
    'source_authority': False,
    'actual_authority': False,
}
for p, data in before.items():
    assert p.read_bytes() == data
new(O / 'INPUT-MAP.json', result)
new(O / 'COLLECTION-manifest.json', {'schema': 'researchos.readonly-composition-map-manifest.v1', 'files': [ref(p) for p in sorted(O.iterdir()) if p.is_file()], 'helper': ref(Path(__file__)), 'source_authority': False, 'actual_authority': False})
print(json.dumps({'manifest': ref(O / 'COLLECTION-manifest.json'), 'path_counts': {k: len(v) for k, v in paths.items()}, 'overlap': overlap, 'combined_unique_paths': result['combined_unique_path_count'], 'shared_unchanged': True}, ensure_ascii=False))
