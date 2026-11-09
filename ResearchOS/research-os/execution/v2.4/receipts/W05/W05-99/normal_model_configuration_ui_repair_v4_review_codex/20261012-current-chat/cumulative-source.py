from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v4-20261012'
BUILD=WT/'.local/v4-bound-build-6'
candidate='57ec9b4408835483bf0c4c30397968d7a11a0b2c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
names=subprocess.check_output(['git','diff','--name-only','292ad860f9e76cf2795d5a3010da1d114d01ff56',candidate],cwd=WT,text=True).splitlines()
for name in names:
    raw=subprocess.check_output(['git','show',f'{candidate}:{name}'],cwd=WT)
    p=OUT/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    expected=hashlib.sha256(raw).hexdigest()
    current=WT/name;bound=BUILD/name
    rows.append(dict(path=name,git_sha256=expected,worktree_exists=current.is_file(),worktree_sha256=sha(current) if current.is_file() else None,bound_source_exists=bound.is_file(),bound_source_sha256=sha(bound) if bound.is_file() else None))
    if current.is_file():assert sha(current)==expected
    if bound.is_file():assert sha(bound)==expected
assert [r['path'] for r in rows if not r['worktree_exists']]==['tests/ui/continuity/surfaces_driver.js']
(OUT/'cumulative-source-verification.json').write_text(json.dumps(dict(candidate=candidate,base='292ad860f9e76cf2795d5a3010da1d114d01ff56',files=rows,missing_sparse_file_read_from_git=True),indent=2)+'\n',encoding='utf-8')
(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff','292ad860f9e76cf2795d5a3010da1d114d01ff56',candidate],cwd=WT))
argv=['C:/nvm4w/nodejs/node.exe',str(OUT/'source/tests/ui/continuity/surfaces_driver.js'),str(WT)]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
run=subprocess.run(argv,cwd=OUT,capture_output=True,timeout=30)
(OUT/'cumulative-surfaces.stdout').write_bytes(run.stdout);(OUT/'cumulative-surfaces.stderr').write_bytes(run.stderr)
(OUT/'cumulative-surfaces.invocation.json').write_text(json.dumps(dict(argv=argv,cwd=str(OUT),exit_code=run.returncode,started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n',encoding='utf-8')
print(run.stdout.decode('utf-8'));print(run.stderr.decode('utf-8'))
raise SystemExit(run.returncode)
