from pathlib import Path
import json,subprocess,hashlib,tarfile,io,datetime
r=Path.cwd();n=r/'execution/v2.4/receipts/W05/W05-99/handler38_independent_replay_codex/39b9d78230514551bee80c7970bfa160';w=r/'.local/independent-handler38-a639cfcf';git=json.loads((r/'execution/toolchains/locked.json').read_bytes())['tools']['git']['path'];commit='22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
def run(label,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();q=subprocess.run([git,*args],cwd=r,capture_output=True);(n/(label+'.stdout')).write_bytes(q.stdout);(n/(label+'.stderr')).write_bytes(q.stderr);(n/(label+'.invocation.json')).write_text(json.dumps({'argv':[git,*args],'cwd':str(r),'started_at':start,'exit':q.returncode},indent=2),encoding='utf8');assert q.returncode==0;return q.stdout
assert not w.exists()
run('worktree-create',['worktree','add','--detach','--no-checkout',str(w),commit])
prefixes=['apps/','internal/','adapters/','ops/','migrations/','contracts/','tests/runtime/','spec/v2.0/contracts/','spec/v2.4/contracts/']
tracked=run('candidate-files',['ls-tree','-rz','--name-only',commit]).decode('utf8').split('\0');fixed=['AGENTS.md','VERSION','go.mod','go.sum','release/fixture-config.json','execution/toolchains/locked.json','execution/toolchains/go.json']
paths=[p for p in tracked if p and (p in fixed or any(p.startswith(x) for x in prefixes))]
# Archive exact public files, no evaluation/SDK/old receipt export.
archive=run('public-source-archive',['archive','--format=tar',commit,*sorted(set(p.split('/')[0] for p in paths if p.split('/')[0] in ['apps','internal','adapters','ops','migrations','contracts'])),'tests/runtime','spec/v2.0/contracts','spec/v2.4/contracts',*fixed])
rows=[]
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
 for item in tar:
  if not item.isfile():continue
  p=(w/item.name).resolve();assert p.is_relative_to(w.resolve());b=tar.extractfile(item).read();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);rows.append({'path':item.name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(n/'public-source-export.json').write_text(json.dumps({'candidate':commit,'checkout':str(w),'files':rows,'evaluation_exports':0,'SDK_exports':0,'product_writes_outside_checkout':0},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'checkout':str(w),'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'exit':0},ensure_ascii=True))
