import hashlib,json,os,pathlib,shutil,subprocess
P=pathlib.Path(__file__).resolve().parent
W=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012')
A=P.parent.parent/'workspace_projection_repair_codex'/'20261012-current-chat'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(W),*args]).decode('utf-8').strip()
m=json.loads((A/'author-manifest.json').read_text('utf-8-sig'))
checks=[]
def check(label,actual,expected):
 checks.append(dict(label=label,actual=actual,expected=expected,pass_=actual==expected))
check('author manifest',sha(A/'author-manifest.json'),'4c5894536bb889cb866732a5a9d35ff7457366c34f9389ac3ccba617cbfaa56f')
check('HEAD',git('rev-parse','HEAD'),m['source_commit'])
check('tree',git('rev-parse','HEAD^{tree}'),m['source_tree'])
check('tracked status',git('status','--short','--untracked-files=no'),'')
check('base parent',git('rev-parse','HEAD^'),m['base_commit'])
check('delta scope',sorted(git('diff','--name-only',m['base_commit'],'HEAD').splitlines()),sorted(x['path'] for x in m['source_files']))
for x in m['source_files']:check(x['path'],sha(W/x['path']),x['sha256'])
for x in m['raw_evidence']:check(x['file'],sha(A/x['file']),x['sha256'])
check('bundle',sha(A/m['bundle']['file']),m['bundle']['sha256'])
check('scope',sha(P.parents[6]/m['scope_ref']),m['scope_sha256'])
check('schema',sha(W/'internal/api/contracts/client.protocol.schema.json'),'8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b')
r=subprocess.run(['git','-C',str(W),'bundle','verify',str(A/m['bundle']['file'])],capture_output=True)
(P/'bundle-verify.stdout').write_bytes(r.stdout);(P/'bundle-verify.stderr').write_bytes(r.stderr)
check('bundle verify exit',r.returncode,0)
inputs=[]
for path in git('ls-files','go.mod','go.sum','internal','adapters','migrations','spec','evaluation','ops').splitlines():
 p=W/path
 if p.is_file():inputs.append(dict(path=path,bytes=p.stat().st_size,sha256=sha(p)))
(P/'input-verification.json').write_text(json.dumps(dict(checks=checks,source_inputs=inputs),ensure_ascii=False,indent=2),'utf-8')
(P/'candidate.diff').write_bytes(subprocess.check_output(['git','-C',str(W),'diff',m['base_commit'],'HEAD']))
assert all(c['pass_'] for c in checks),checks
print('INPUT_BINDING_PASS',len(checks),'source inputs',len(inputs),flush=True)
cache=P/'go-cache'
if not cache.exists():shutil.copytree(W/'.local/go-cache',cache)
for folder in ['go-tmp','test-tmp','native-http-evidence']:(P/folder).mkdir(exist_ok=True)
print('OWN_CACHE_READY',flush=True)
