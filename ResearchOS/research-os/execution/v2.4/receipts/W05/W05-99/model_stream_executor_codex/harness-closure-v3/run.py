import os, sys, json, uuid, subprocess, datetime, hashlib
from pathlib import Path
root = Path(__file__).resolve().parents[7]
main = Path('D:/作品集/ResearchOS/research-os')
assert (root / 'go.mod').is_file()
out = root / 'execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex' / ('closure-' + uuid.uuid4().hex)
out.mkdir()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name, value): (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
go = main / '.local/tools/go1.27.1/go'
node = Path('C:/nvm4w/nodejs/node.exe')
env = os.environ.copy()
env.update(GOROOT=str(go), GOTOOLCHAIN='local', GOENV='off', GOPATH=str(main / '.local/gopath'), GOCACHE=str(main / '.local/gocache'), GOPROXY='off', GOSUMDB='off', RESEARCHOS_NODE=str(node), RESEARCHOS_MU_BUNDLE=str(root / '.local/model-stream/mu-worker.mjs'), RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR=str(out / 'actual-fixtures'))
def invoke(name, argv):
    start = now()
    with (out / (name+'.stdout')).open('wb') as stdout, (out / (name+'.stderr')).open('wb') as stderr:
        result = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr)
    record = dict(actualargv=argv, cwd=str(root), started_at=start, ended_at=now(), exit=result.returncode)
    save(name+'.invocation.json', record)
    return result.returncode
list_argv = [str(go/'bin/go.exe'), 'list', '-deps', '-test', '-json', './adapters/runtime', './internal/domain', './apps/cli', './tests/runtime/cli_contract']
if invoke('go-list', list_argv):
    print(str(out)); sys.exit(1)
raw = (out/'go-list.stdout').read_text('utf8'); decoder = json.JSONDecoder(); packages=[]
while raw.strip():
    raw=raw.lstrip(); package, end=decoder.raw_decode(raw); packages.append(package); raw=raw[end:]
paths = set()
for p in packages:
    if not p.get('Dir'): continue
    directory=Path(p['Dir'])
    # All platform/test Go files in every actual compiler package, including local packages.
    paths.update(x for x in directory.glob('*.go') if x.is_file())
    for key in ['EmbedFiles', 'TestEmbedFiles', 'XTestEmbedFiles', 'SFiles', 'HFiles', 'SysoFiles', 'CFiles', 'CXXFiles']:
        for name in p.get(key, []):
            candidate=directory/name
            if candidate.is_file(): paths.add(candidate)
    if p.get('Module', {}).get('GoMod'): paths.add(Path(p['Module']['GoMod']))
for folder in ['internal', 'adapters', 'apps', 'tests/runtime', 'migrations', 'spec/v2.0/contracts']:
    paths.update(p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ['.go','.mjs','.json','.sql'])
for name in ['go.mod','go.sum']: paths.add(root/name)
for folder in ['packages', 'node_modules']:
    paths.update(p for p in (main/'third_party/mu'/folder).rglob('*') if p.is_file() and '.git' not in p.parts)
for name in ['third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json']:
    if (main/name).is_file(): paths.add(main/name)
paths.update([go/'bin/go.exe', node, Path(env['RESEARCHOS_MU_BUNDLE'])])
paths.update(p for p in (go/'pkg/tool').rglob('*') if p.is_file())
paths=sorted(paths)
def source():
    result={}
    for p in paths:
        if p.is_relative_to(root): key='repo:'+p.relative_to(root).as_posix()
        elif p.is_relative_to(main): key='main:'+p.relative_to(main).as_posix()
        else: key='absolute:'+p.as_posix()
        result[key]=sha(p) if p.is_file() else 'MISSING'
    return result
save('environment.json', {k: env[k] for k in ['GOROOT','GOTOOLCHAIN','GOENV','GOPATH','GOCACHE','GOPROXY','GOSUMDB','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE']})
invoke('git-status', ['git','status','--porcelain=v1'])
invoke('go-version', [str(go/'bin/go.exe'),'version'])
invoke('node-version', [str(node),'--version'])
before=source(); save('source_before.json', before)
argv=[str(go/'bin/go.exe'), *sys.argv[1:]]
if sys.argv[1]=='node': argv=[str(node),*sys.argv[2:]]
result=invoke('test', argv)
after=source(); save('source_after.json', after)
record=dict(measurement_mode='FIXTURE_NOT_LIVE_NOT_FORMAL', exit=result, source_drift=before!=after, input_count=len(before), bundle_sha256=sha(Path(env['RESEARCHOS_MU_BUNDLE'])))
save('result.json',record)
print(out); print(json.dumps(record)); print((out/'test.stdout').read_text('utf8',errors='replace')[-20000:]); print((out/'test.stderr').read_text('utf8',errors='replace')[-8000:])
sys.exit(result if result else int(before!=after))
