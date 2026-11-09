import hashlib,json,subprocess,os
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
N=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310'
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (HERE/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(HERE/n)
def load(p):return json.loads(Path(p).read_bytes())
prepared=load(N/'prepared_refs.json');verified=[]
for row in prepared['verified_refs']:
 a=ref(ROOT/row['path'])
 if a!=row:raise RuntimeError('REFERENCE:'+row['path'])
 verified.append(a)
copied=[]
for row in prepared['canonical_before']:
 p=ROOT/row['path'];raw=p.read_bytes()
 if ref(p)!=row:raise RuntimeError('CANONICAL:'+str(p))
 dst=HERE/('before-'+p.name)
 with dst.open('xb') as f:f.write(raw)
 copied.append(ref(dst))
cp=load(ROOT/'execution/v2.4/checkpoint.json');ow=load(ROOT/'execution/v2.4/path_ownership.json')
if [cp['revision'],ow['revision'],len(cp['failure_counters'])]!=[309,137,379]:raise RuntimeError('TUPLE')
oldkeys={r.get('origin_key') for r in cp['failure_counters']};newkeys=[r['origin_key'] for r in prepared['origins']]
if len(newkeys)!=5 or len(set(newkeys))!=5 or any(k in oldkeys for k in newkeys):raise RuntimeError('ORIGIN_COUNT')
for row in prepared['origins']:
 if row['actual_outer_exit']!=1:raise RuntimeError('ORIGIN_EXIT')
 obj=load(ROOT/row['evidence_ref']['path'])
 if 'json_pointer' in row:
  for part in row['json_pointer'].strip('/').split('/'):
   obj=obj[int(part)] if isinstance(obj,list) else obj[part]
  if obj!=row['original_payload']:raise RuntimeError('ORIGIN_PAYLOAD')
lock=load(ROOT/'execution/toolchains/locked.json')['tools'];git=Path(lock['git']['path'])
if hashlib.sha256(git.read_bytes()).hexdigest()!=lock['git']['sha256']:raise RuntimeError('GIT_LOCK')
env={k:os.environ[k] for k in ('SystemRoot','WINDIR','ComSpec','PATH','PATHEXT') if k in os.environ}
env.update(GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_OPTIONAL_LOCKS='0')
gitresults=[]
for label,args,cwd in [('main-head',['rev-parse','HEAD'],ROOT),('main-status',['status','--porcelain=v1','--untracked-files=no'],ROOT),('main-index',['diff','--cached','--name-only'],ROOT),('g2-head',['rev-parse','HEAD'],ROOT/'.local/worktrees/codex-w0599-provider-g2-finite-r307'),('g2-status',['status','--porcelain=v1'],ROOT/'.local/worktrees/codex-w0599-provider-g2-finite-r307')]:
 argv=[str(git),*args]
 with (HERE/(label+'.stdout.raw')).open('xb') as out,(HERE/(label+'.stderr.raw')).open('xb') as err:
  r=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=err)
 inv=save(label+'.invocation.json',dict(argv=argv,cwd=str(cwd),actual_exit=r.returncode,stdout=ref(HERE/(label+'.stdout.raw')),stderr=ref(HERE/(label+'.stderr.raw'))))
 if r.returncode!=0:raise RuntimeError('GIT_READ:'+label)
 gitresults.append(inv)
status=(HERE/'main-status.stdout.raw').read_bytes()
if hashlib.sha256(status).hexdigest()!=prepared['git_status_sha256'] or len(status.splitlines())!=13 or sum(x[:2]==b' D' for x in status.splitlines())!=11:raise RuntimeError('STATUS')
if (HERE/'main-head.stdout.raw').read_text().strip()!=prepared['head'] or (HERE/'main-index.stdout.raw').read_bytes():raise RuntimeError('HEAD_INDEX')
if (HERE/'g2-head.stdout.raw').read_text().strip()!='9a34aacbaeb775566e524f5af3518ea86a5d41b9' or (HERE/'g2-status.stdout.raw').read_bytes():raise RuntimeError('G2_STATE')
for name in ('register.py','run.py','list_replay.py','g2_replay.v3.py','prepared_refs.json','audit.json'):
 with (HERE/('original-'+name)).open('xb') as f:f.write((N/name).read_bytes())
a=save('original_draft_audit.json',dict(decision='REQUEST_CHANGES_STATIC_EXECUTION_CLOSURE_GAPS',actual_registration_executed=False,verified_refs=verified,canonical_before=prepared['canonical_before'],copied_canonical_before_refs=copied,git=gitresults,new_origin_keys=newkeys,actual_new_failures=0,findings=[dict(id='R310-01',path='list_replay.py',function='main/runtime_paths',issue='SourceFileLoader helper is not registered in sys.modules. Its actually referenced __cached__ path may be absent from runtime inventory. Freeze actual helper module file/cache explicitly or load hash-verified source bytes without importlib cache.'),dict(id='R310-02',path='g2_replay.v3.py',function='Replay.prepare',issue='Initial resources.before is replaced with newly derived paths after export/go-list without checking prior baseline. Compare initial resource hashes before broadening inventory and retain exact original resources in build/case baselines.')],boundary='Only immutable input/read/hash/Git-read audit. No registrar/helper/controller import, DLL load, Go/Node/SQL/HTTP or test execution. Await new immutable draft before final decision.'))
print(json.dumps(a,ensure_ascii=False))
