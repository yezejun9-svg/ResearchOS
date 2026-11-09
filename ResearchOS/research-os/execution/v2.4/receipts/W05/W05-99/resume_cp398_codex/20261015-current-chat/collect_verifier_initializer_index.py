import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
H = R / 'execution/v2.4/receipts/W05/W05-99/historical_qualification_public_provenance_codex/20261015-current-chat'
I = H / 'verifier-dependency-inputs01'
O = H / 'verifier-initializer-index01'
T = R / '.local/builds/verifier-dependency-input-map-20261015'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def new(name, value):
    p = O / name
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return ref(p)


assert ref(I / 'COLLECTION-manifest.json')['sha256'] == '99617d07ea92e2f5a0142ce09445394867074ba308e2b2800bf062a8be6b9c9e'
for item in read(I / 'COLLECTION-manifest.json')['files']:
    assert ref(Path(item['path'])) == item
O.mkdir(exist_ok=False)
helper = B / 'index_verifier_initializers.go'
selected = I / '04-selected-package-source-map.json'
go = str(R / '.local/tools/go1.27.1/go/bin/go.exe')
env = os.environ.copy()
env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(R / '.local/tools/go1.27.1/go'), GOPATH=str(R / '.local/tools/gopath'), GOMODCACHE=str(R / '.local/tools/gopath/pkg/mod'), GOCACHE=str(T / 'go-cache'), GOTMPDIR=str(T / 'go-tmp'), TEMP=str(T / 'go-tmp'), TMP=str(T / 'go-tmp'), GOPROXY='off', GOSUMDB='off', GOWORK='off', GOOS='windows', GOARCH='amd64', GOAMD64='v1', CGO_ENABLED='0', GOFLAGS='-mod=readonly')
keys = ['GOTOOLCHAIN', 'GOENV', 'GOROOT', 'GOPATH', 'GOMODCACHE', 'GOCACHE', 'GOTMPDIR', 'TEMP', 'TMP', 'GOPROXY', 'GOSUMDB', 'GOWORK', 'GOOS', 'GOARCH', 'GOAMD64', 'CGO_ENABLED', 'GOFLAGS']
argv = [go, 'run', str(helper), str(selected)]
new('01-index.recipe.json', {'argv': argv, 'cwd': str(R), 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'environment_allowlist': {k: env[k] for k in keys}, 'helper_ref': ref(helper), 'input_ref': ref(selected), 'stdout': '01-index.stdout.raw.json', 'stderr': '01-index.stderr.raw'})
with (O / '01-index.stdout.raw.json').open('xb') as out, (O / '01-index.stderr.raw').open('xb') as err:
    result = subprocess.run(argv, cwd=R, env=env, stdout=out, stderr=err, check=False)
new('01-index.result.json', {'native_exit': result.returncode, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'stdout': ref(O / '01-index.stdout.raw.json'), 'stderr': ref(O / '01-index.stderr.raw')})
assert result.returncode == 0
index = read(O / '01-index.stdout.raw.json')
nonstandard = [item for item in index['initializers'] if not item['standard']]
initial_functions = [item for item in nonstandard if item['kind'] == 'init_function']
initial_values_with_calls = [item for item in nonstandard if item['kind'] == 'package_variable_initializer' and item['call_syntax']['calls']]
new('02-nonstandard-initializer-index.json', {'initial_functions': initial_functions, 'initial_values_with_call_syntax': initial_values_with_calls, 'all_nonstandard_initializers': len(nonstandard), 'limits': index['limits'], 'claim': 'Syntax candidate index, not proof of executed calls or absence of OS/network/DB/background effects.'})
summary = {'parsed_go_files': index['parsed_go_files'], 'all_initializers': len(index['initializers']), 'all_functions': len(index['functions']), 'nonstandard_initializers': len(nonstandard), 'nonstandard_init_functions': len(initial_functions), 'nonstandard_package_values_with_call_syntax': len(initial_values_with_calls), 'source_writes': 0, 'actual_product_actions': 0, 'semantic_acceptance': False, 'formal_increment': 0}
new('03-summary.json', summary)
members = [ref(p) for p in sorted(O.iterdir()) if p.is_file()]
manifest = new('COLLECTION-manifest.json', {'schema': 'researchos.original-verifier-initializer-index-collection.v1', 'status': 'SYNTAX_RESOURCE_MAP_ONLY_NOT_SEMANTIC_ACCEPTANCE', 'files': members, 'input_manifest_ref': ref(I / 'COLLECTION-manifest.json'), 'helper_ref': ref(helper), 'actual_product_actions': 0, 'source_writes': 0, 'formal_increment': 0})
print(json.dumps({'manifest': manifest, 'summary': summary}))
