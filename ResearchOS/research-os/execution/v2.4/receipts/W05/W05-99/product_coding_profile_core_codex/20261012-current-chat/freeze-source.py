import json,hashlib,pathlib,subprocess,datetime,sys
out=pathlib.Path(__file__).resolve().parent
repo=out.parents[6]
wt=repo/'.local/worktrees/w05-product-coding-profile-core-20261012'
root=repo/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat'
scopes=[('continuation-cp417/coding-core-scope.json','1ef04e88a1c07cfdf65fd2c3854f7b06013f77bb1d52734419cdc45b9c7e96bc'),('continuation-cp418/coding-scope-amendment.json','fadb7e95a3cab1545ea70a9aaae058e70cee3ebf46920eb4430f09fca8d2152f'),('continuation-cp420/coding-exit-scope-amendment.json','bf59ac3bd40fbb5a27c4f15a5c73943fd059fb8759393e5e58ad30da316c8a78'),('continuation-cp421/coding-runtime-repair-scope.json','2a469990a14a811eea075dca33e92a2217dfa9d660ae2a16900e6f612bc0040e'),('continuation-cp422/check-createdns-scope.json','5c7f6db1a3dc6364bfa5d7ad53814d2b8a2be3df5517425dfac9c25884c90e5f'),('continuation-cp423/canonical-zero-hold-usage-test-scope.json','79798e7598f618a7ef12042163c714d37a13a5e5e4cc5da5b82ce9b64fb0157f')]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=wt)
allowed=set();refs=[]
for name,digest in scopes:
 p=root/name;raw=p.read_bytes();assert sha(raw)==digest,(name,sha(raw));o=json.loads(raw);allowed.update(o.get('paths',o.get('new_paths',[])));refs.append(dict(path=p.relative_to(repo).as_posix(),sha256=digest,bytes=len(raw)))
assert len(allowed)==30,len(allowed)
base='d3a0fcaf506f1a3dd88f3f5d0a46f7bc1f0b56c1'
if sys.argv[1]=='commit':
 assert git('rev-parse','HEAD').decode().strip()==base
 assert not git('diff','--cached','--name-only').strip()
 changed=set(git('diff','--name-only','-z').decode().strip('\0').split('\0'))|set(git('ls-files','--others','--exclude-standard','-z').decode().strip('\0').split('\0'));changed.discard('')
 assert changed and changed<=allowed,sorted(changed-allowed)
 subprocess.run(['git','diff','--check'],cwd=wt,check=True)
 (out/'source-paths.json').write_text(json.dumps(sorted(changed),indent=2),encoding='utf-8')
 subprocess.run(['git','add','--',*sorted(changed)],cwd=wt,check=True)
 assert set(git('diff','--cached','--name-only').decode().splitlines())==changed
 (out/'source-code.diff').write_bytes(git('diff','--cached','--binary'))
 result=subprocess.run(['git','commit','-m','feat(runtime): authorize bounded workspace coding and preserve native receipts'],cwd=wt,capture_output=True)
 (out/'source-commit.stdout').write_bytes(result.stdout);(out/'source-commit.stderr').write_bytes(result.stderr)
 if result.returncode:raise SystemExit(result.returncode)
assert not git('status','--porcelain').strip()
commit=git('rev-parse','HEAD').decode().strip()
files=[]
for name in git('diff','--name-only',base,commit).decode().splitlines():
 assert name in allowed
 raw=(wt/name).read_bytes();assert git('show',commit+':'+name)==raw
 files.append(dict(path=name,sha256=sha(raw),bytes=len(raw)))
meta=dict(schema='researchos.product-coding-core-frozen-source.v1',base=base,candidate=commit,worktree=str(wt),clean=True,allowed_paths=sorted(allowed),scope_refs=refs,source_files=files,real_model_calls=0,formal_acceptance_increment=0)
(out/'source-frozen.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(dict(candidate=commit,files=len(files),sha256=sha((out/'source-frozen.json').read_bytes()))))
