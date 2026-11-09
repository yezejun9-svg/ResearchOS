import json, os, subprocess, sys, hashlib, datetime
from pathlib import Path
MAIN=Path(r'D:\作品集\ResearchOS\research-os')
E=Path(__file__).parent
WT=MAIN/'.local/worktrees/react-workbench-independent-review-20261025'
TMP=MAIN/'.local/react-workbench-independent-review-20261025-tmp'
ASCII=Path(r'C:\Users\yqyyds\.codex\researchos-fixture-cache\react-workbench-independent-review-20261025')
AUTHOR=MAIN/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat'
SHA='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e'
BASE='4f4023c956f84d65743f39ce77d6c8899a21ada1'
PY=sys.executable
NODE=r'C:\nvm4w\nodejs\node.exe'
PLAY=r'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\playwright\driver\package'
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ledger(kind,status,detail):
 with (E/'LEDGER.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind=kind,status=status,detail=detail),ensure_ascii=False)+'\n')
def run(name,argv,cwd=WT,env=None,start=False):
 target=E/'commands'/name; target.mkdir(parents=True,exist_ok=False)
 current=os.environ.copy(); current.update(env or {})
 save(target/'recipe.json',dict(argv=[str(x) for x in argv],cwd=str(cwd),env=env or {},mode='start' if start else 'run'))
 with (target/'stdout.bin').open('wb') as out,(target/'stderr.bin').open('wb') as err:
  if start:
   p=subprocess.Popen(argv,cwd=cwd,env=current,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)); save(target/'result.json',dict(pid=p.pid)); return p
  r=subprocess.run(argv,cwd=cwd,env=current,stdout=out,stderr=err)
 save(target/'result.json',dict(native_exit=r.returncode)); ledger(name,'PASS' if r.returncode==0 else 'FAIL',str(target))
 if r.returncode: raise RuntimeError(f'{name} exit {r.returncode}, see raw streams')
 return (target/'stdout.bin').read_text(encoding='utf-8',errors='replace').strip()
def git(name,args,cwd=WT): return run(name,['git','-c','maintenance.auto=false','-c','gc.auto=0',*args],cwd)
def prepare():
 assert not WT.exists(); TMP.mkdir(parents=True,exist_ok=True); ASCII.mkdir(parents=True,exist_ok=True)
 git('001-worktree',['worktree','add','--detach','--no-checkout',str(WT),SHA],MAIN)
 git('002-sparse',['sparse-checkout','set','--no-cone','/AGENTS.md','/go.mod','/go.sum','/apps/web/','/apps/desktop/','/apps/control/','/tests/ui/','/tests/support/','/internal/','/adapters/','/migrations/','/spec/','/evaluation/','/ops/ci/'])
 git('003-checkout',['checkout','--detach',SHA])
 run('004-dependency-junction',['pwsh','-NoProfile','-Command',f"New-Item -ItemType Junction -Path '{WT / 'apps/web/node_modules'}' -Target '{MAIN / 'apps/web/node_modules'}' | Out-Null"])
 print('prepared')
def verify():
 seal=json.loads((AUTHOR/'SOURCE14-SEAL.json').read_text()); checks={}
 checks['head']=git('005-head',['rev-parse','HEAD'])==SHA
 checks['tree']=git('006-tree',['rev-parse','HEAD^{tree}'])==seal['final_tree']
 checks['clean']=git('007-clean',['status','--porcelain=v1'])==''
 changes=git('008-paths',['diff','--name-only',BASE,SHA]).splitlines()
 checks['paths']=changes==seal['actual_changed_paths']
 checks['source_hashes']=all(hashlib.sha256((WT/p).read_bytes()).hexdigest()==h for p,h in seal['source_sha256'].items())
 checks['full_patch']=hashlib.sha256((AUTHOR/'source14-full.patch').read_bytes()).hexdigest()==seal['full_patch_sha256']
 checks['ci_patch']=hashlib.sha256((AUTHOR/'source14-ci.patch').read_bytes()).hexdigest()==seal['ci_delta_patch_sha256']
 checks['ci_probe']=hashlib.sha256((AUTHOR/'SOURCE14-CI-PROBE.json').read_bytes()).hexdigest()==seal['ci_ast_probe_sha256']
 checks['author_clean']=git('009-author-clean',['status','--porcelain=v1'],Path(seal['worktree']))==''
 git('010-diff-check',['diff','--check',BASE,SHA])
 for d in ['browser-fixture-05','real-isolated-03']:
  report=json.loads((AUTHOR/d/'report.json').read_text()); shots=report.get('screenshots',[]) or [report['screenshot']]
  checks[d]=report['status']=='PASS' and all(hashlib.sha256(Path(s['path']).read_bytes()).hexdigest()==s['sha256'] for s in shots)
 save(E/'PIN-CHECKS.json',dict(checks=checks,changed=changes)); assert all(checks.values()),checks
 print(json.dumps(checks))
def build():
 run('011-web-build',[r'C:\Windows\System32\cmd.exe','/d','/c',r'C:\nvm4w\nodejs\npm.cmd','run','build'],WT/'apps/web')
 run('012-w13-react',[NODE,'--test','tests/ui/desktop/w13-react.test.js'])
 run('013-core-build',[str(MAIN/'.local/tools/go1.27.1/go/bin/go.exe'),'build','-o',str(ASCII/'control.exe'),'./apps/control'],env={'GOMODCACHE':str(MAIN/'.local/tools/gopath/pkg/mod'),'GOTOOLCHAIN':'local','GOPROXY':'off'})
 print('build checks pass')
if __name__=='__main__': globals()[sys.argv[1]]()
