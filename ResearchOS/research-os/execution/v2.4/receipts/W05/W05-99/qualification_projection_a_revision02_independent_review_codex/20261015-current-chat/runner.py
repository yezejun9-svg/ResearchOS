import os, json, hashlib, subprocess, pathlib, datetime, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
E=pathlib.Path(__file__).parent
S=ROOT/'execution/v2.4/receipts/W05/W05-99/qualification_projection_a_revision02_source_codex/20261015-current-chat'
W=ROOT/'.local/worktrees/qualification-projection-a-r2-20261015'
T=ROOT/'.local/qualification-projection-r2-independent-review-20261015'
GO=str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe')
ENV=os.environ.copy()
ENV['PYTHONIOENCODING']='utf-8'
ENV.update(GOCACHE=str(T/'cache'),GOPATH=str(ROOT/'.local/tools/gopath'),GOTMPDIR=str(T/'tmp'),TMP=str(T/'tmp'),TEMP=str(T/'tmp'),RESEARCHOS_MU_BUNDLE=str(ROOT/'.local/builds/current-chat-runtime-assets-20261012/mu-worker.mjs'))
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(n,v): (E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(n,argv,cwd=W,show=True):
 recipe={'argv':argv,'cwd':str(cwd),'env_allowlist':{k:ENV[k] for k in ('GOCACHE','GOPATH','GOTMPDIR','TMP','TEMP','RESEARCHOS_MU_BUNDLE','PYTHONIOENCODING')},'recipe_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw':n+'.raw'}
 save(n+'.recipe.json',recipe)
 try:
  with (E/(n+'.raw')).open('wb') as f:p=subprocess.run(argv,cwd=cwd,env=ENV,stdout=f,stderr=subprocess.STDOUT)
  result={**recipe,'native_exit':p.returncode,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_sha256':sha(E/(n+'.raw'))}
 except Exception as exc:
  result={**recipe,'native_exit':None,'tool_exception':str(exc)}
 save(n+'.result.json',result)
 with (E/'diagnostic-ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False)+'\n')
 print(n,result.get('native_exit'),flush=True)
 if show: print((E/(n+'.raw')).read_text(encoding='utf-8',errors='strict'),flush=True)
 return (E/(n+'.raw')).read_bytes()
def guards(n):
 values={}
 for name,cwd in [('main',ROOT),('candidate',W)]:
  raw=run(n+'-'+name+'-status',['git','--no-optional-locks','status','--porcelain=v1','-uno'],cwd,False)
  head=run(n+'-'+name+'-head',['git','--no-optional-locks','rev-parse','HEAD','HEAD^{tree}'],cwd,False).decode().splitlines()
  index=run(n+'-'+name+'-index',['git','--no-optional-locks','diff','--cached','--name-only'],cwd,False).decode()
  paths=run(n+'-'+name+'-dirty-paths',['git','--no-optional-locks','diff','--name-only'],cwd,False).decode().splitlines()
  values[name]={'head':head,'status':raw.decode(),'index':index,'dirty_file_hashes':{p:sha(cwd/p) for p in paths if (cwd/p).is_file()}}
 values['bundle']={'path':ENV['RESEARCHOS_MU_BUNDLE'],'sha256':sha(ENV['RESEARCHOS_MU_BUNDLE'])}
 save(n+'-guards.json',values)
if __name__=='__main__':
 for sub in ('tmp','cache'):(T/sub).mkdir(parents=True,exist_ok=True)
 mode=sys.argv[1]
 if mode=='inspect':
  guards('before')
  m=read(S/'source-manifest.revision02.json')
  run('source-manifest',['python','-B','-c','import pathlib; print(pathlib.Path('+repr(str(S/'source-manifest.revision02.json'))+').read_text(encoding="utf-8-sig"))'])
  run('complete-A-diff',['git','--no-optional-locks','diff','--binary','4f4023c956f84d65743f39ce77d6c8899a21ada1','f48fca0e4013bda19913a34d91da0cd23157a08b'],show=False)
  run('r2-diff',['git','--no-optional-locks','diff','--binary','525a9c923a8761a9491070123de3c94aa5618d71','f48fca0e4013bda19913a34d91da0cd23157a08b'],show=False)
 elif mode=='exec': run(sys.argv[2],sys.argv[3:])
 elif mode=='guards': guards(sys.argv[2])
