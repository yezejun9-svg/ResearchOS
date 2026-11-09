import datetime
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
E = R / 'execution/v2.4/receipts/W05/W05-99'
B = E / 'verifier_replacement_package_codex/20261015-current-chat'
O = E / 'historical_qualification_public_provenance_codex/20261015-current-chat/verifier-dependency-inputs01'
W = R / '.local/worktrees/verifier-replacement-20261014'
T = R / '.local/builds/verifier-dependency-input-map-20261015'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def ref(p):
    data = p.read_bytes()
    return {'path': str(p), 'bytes': len(data), 'sha256': digest(data)}


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def new(name, value):
    p = O / name
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return ref(p)


def normalized(path):
    return os.path.normcase(os.path.abspath(path)).replace('\\', '/')


def run(label, argv, cwd, env):
    recipe = {'argv': argv, 'cwd': str(cwd), 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'environment_allowlist': {k: env[k] for k in ALLOW}, 'stdout': label + '.stdout.raw', 'stderr': label + '.stderr.raw'}
    new(label + '.recipe.json', recipe)
    with (O / recipe['stdout']).open('xb') as out, (O / recipe['stderr']).open('xb') as err:
        result = subprocess.run(argv, cwd=cwd, env=env, stdout=out, stderr=err, check=False)
    new(label + '.result.json', {'native_exit': result.returncode, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'stdout': ref(O / recipe['stdout']), 'stderr': ref(O / recipe['stderr'])})
    assert result.returncode == 0, (label, result.returncode)
    return (O / recipe['stdout']).read_bytes()


assert digest((B / 'runtime-verifier-build.stderr').read_bytes()) == '4514ddf56550118e96ba0aa58ab9e31e0f3fafb269c5e1114fb4ac4b5848eace'
assert digest((B / 'compiler-module-inputs.before.json').read_bytes()) == '3c73f1007cb88dbd2727811006a7172ba2845d8ba3d23f8cee764c3cb723b30d'
build = read(B / 'runtime-verifier-build.json')
assert build['native_exit'] == 0 and Path(build['cwd']) == W
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=W, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'status', '--porcelain=v1', '-uno'], cwd=W)
O.mkdir(exist_ok=False)
T.mkdir(exist_ok=False)
(T / 'go-tmp').mkdir()
(T / 'go-cache').mkdir()
new('root-read-diagnostics.json', {'items': [
    {'ordinal': 1, 'tool_chunk': 'd355e1', 'native_exit': 1, 'kind': 'ROOT_GUESSED_RECEIPT_FILENAME', 'detail': 'COLLECTION.json did not exist; recovered exact manifest members via rg --files. No source or actual state mutation.'},
    {'ordinal': 2, 'tool_chunk': '9cbbc4', 'native_exit': 0, 'kind': 'ROOT_OVERSIZED_DEPENDENCY_DISPLAY', 'detail': 'Link table display exceeded tool output budget. Original complete historical raw exists and is pinned; use bounded summaries thereafter.'},
]})
source_vector = read(B / 'compiler-module-inputs.before.json')
before_checks = []
for item in source_vector:
    p = Path(item['path'])
    actual = ref(p)
    assert actual['bytes'] == item['bytes'] and actual['sha256'] == item['sha256'], str(p)
    before_checks.append({'path': str(p), 'sha256': actual['sha256']})
new('01-recorded-union-fresh-hash-check.json', {'recorded_count': len(source_vector), 'fresh_drift': 0, 'source_vector_ref': ref(B / 'compiler-module-inputs.before.json'), 'entries': before_checks})
log = (B / 'runtime-verifier-build.stderr').read_text(encoding='utf8')
marker = 'importcfg.link << '
start = log.index(marker)
tail = log[start:]
link_block = tail[tail.index('\n') + 1:tail.index('\nEOF')]
packagefiles = []
for line in link_block.splitlines():
    if line.startswith('packagefile '):
        package, archive = line[len('packagefile '):].split('=', 1)
        packagefiles.append({'import_path': package, 'recorded_archive_path': archive, 'archive_exists_now': Path(archive).is_file()})
assert len({item['import_path'] for item in packagefiles}) == len(packagefiles)
new('02-historical-link-packagefiles.json', {'historical_stderr_ref': ref(B / 'runtime-verifier-build.stderr'), 'packages': packagefiles, 'count': len(packagefiles), 'claim': 'Exact packagefile table recorded for original verifier link; package inclusion alone is not initializer reachability or semantic closure.'})
env = os.environ.copy()
env.update(build['environment_allowlist'])
env.update(GOCACHE=str(T / 'go-cache'), GOTMPDIR=str(T / 'go-tmp'), TEMP=str(T / 'go-tmp'), TMP=str(T / 'go-tmp'), GOOS='windows', GOARCH='amd64', GOAMD64='v1', CGO_ENABLED='0', GOWORK='off')
ALLOW = list(dict.fromkeys(list(build['environment_allowlist']) + ['GOOS', 'GOARCH', 'GOAMD64', 'CGO_ENABLED', 'GOWORK']))
go = str(R / '.local/tools/go1.27.1/go/bin/go.exe')
raw = run('03-go-list-current-selected-source', [go, 'list', '-deps', '-json', '-mod=readonly', './apps/runtime-verifier'], W, env)
text = raw.decode('utf8')
decoder = json.JSONDecoder()
selected = []
position = 0
while position < len(text):
    while position < len(text) and text[position].isspace():
        position += 1
    if position == len(text):
        break
    item, position = decoder.raw_decode(text, position)
    selected.append(item)
actual_packages = {item['ImportPath'] for item in selected}
historical_packages = {item['import_path'] for item in packagefiles}
assert historical_packages <= actual_packages
vector_by_path = {normalized(item['path']): item for item in source_vector}
file_rows, packages = [], []
for item in selected:
    files = []
    for kind in ('GoFiles', 'CgoFiles', 'CFiles', 'CXXFiles', 'MFiles', 'HFiles', 'FFiles', 'SFiles', 'SwigFiles', 'SwigCXXFiles', 'SysoFiles', 'EmbedFiles'):
        for filename in item.get(kind, []):
            p = Path(item['Dir']) / filename
            row = ref(p)
            old = vector_by_path.get(normalized(p))
            row.update(import_path=item['ImportPath'], kind=kind, standard=item.get('Standard', False), recorded_union_match=old is not None and old['sha256'] == row['sha256'] and old['bytes'] == row['bytes'])
            if old is not None:
                assert row['recorded_union_match']
            file_rows.append(row)
            files.append(str(p))
    packages.append({'import_path': item['ImportPath'], 'dir': item['Dir'], 'standard': item.get('Standard', False), 'imports': item.get('Imports', []), 'selected_files': files, 'in_historical_link_table': item['ImportPath'] in historical_packages})
new('04-selected-package-source-map.json', {'kind': 'CURRENT_METADATA_RECONSTRUCTION_USING_ORIGINAL_SOURCE_AND_TOOLCHAIN', 'packages': packages, 'package_count': len(packages), 'historical_link_count': len(packagefiles), 'current_only_packages': sorted(actual_packages - historical_packages), 'historical_package_set_missing': [], 'source_files': file_rows, 'selected_file_count': len(file_rows), 'recorded_union_matched_files': sum(row['recorded_union_match'] for row in file_rows), 'not_in_recorded_union': [row['path'] for row in file_rows if not row['recorded_union_match']], 'limits': ['go list output captured now; not an original historical selected-source capture.', 'Historical link table plus unchanged source/toolchain and current metadata supports a reconstruction; initializer/background semantics remain unaudited.', 'No verifier or product executable was run. Toolchain source not found in original union remains separately identified.']})
binary = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015/apps/desktop/resources/control/runtime-verifier.exe')
assert digest(binary.read_bytes()) == 'f255f4d49c5b217462bb38a8ec2292e9d62889d8506488569ff3638237708a43'
nm = run('05-original-binary-symbols', [go, 'tool', 'nm', '-size', str(binary)], W, env).decode('utf8')
symbol_rows = []
for line in nm.splitlines():
    parts = line.split()
    if len(parts) >= 4 and (parts[3].endswith('..inittask') or re.search(r'\.init(?:\.|$)', parts[3])):
        symbol_rows.append({'address': parts[0], 'bytes': int(parts[1]), 'type': parts[2], 'symbol': parts[3]})
new('06-original-binary-initializer-symbols.json', {'binary_ref': ref(binary), 'symbols': symbol_rows, 'count': len(symbol_rows), 'claim': 'Observed symbols in original exact binary; not a complete dynamic callgraph or OS-effect proof.'})
for item in source_vector:
    p = Path(item['path'])
    assert digest(p.read_bytes()) == item['sha256'] and p.stat().st_size == item['bytes']
assert not subprocess.check_output(['git', 'status', '--porcelain=v1', '-uno'], cwd=W)
new('07-summary.json', {'union_inputs_fresh_drift': 0, 'historical_link_packages': len(packagefiles), 'current_go_list_packages': len(packages), 'selected_files': len(file_rows), 'historical_union_matched_files': sum(row['recorded_union_match'] for row in file_rows), 'initializer_symbols': len(symbol_rows), 'scope': 'PUBLIC_EXISTING_INPUT_RESOURCE_MAP_ONLY', 'source_writes': 0, 'actual_product_actions': 0, 'semantic_acceptance': False, 'formal_increment': 0})
members = [ref(p) for p in sorted(O.iterdir()) if p.is_file()]
manifest_ref = new('COLLECTION-manifest.json', {'schema': 'researchos.original-verifier-dependency-input-map.v1', 'status': 'READONLY_RESOURCE_MAP_NOT_SEMANTIC_OR_OPERATIONAL_ACCEPTANCE', 'files': members, 'formal_increment': 0, 'actual_product_actions': 0, 'source_writes': 0})
print(json.dumps({'manifest': manifest_ref, 'summary': read(O / '07-summary.json')}))
