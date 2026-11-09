from pathlib import Path
import json,hashlib,subprocess,sys,re,datetime
sys.stdout.reconfigure(encoding='utf-8')
R=Path.cwd();W=R/'.local/worktrees/codex-w0599-provider-binding';N='execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63';P=W/N;O=Path(__file__).parent;C='976c8c9a6bdf8703475e02b79b77f4c5fab2d650'
H=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':H(b),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(n,j):(O/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':C,'manifest':ref(P/'manifest.json'),'handoff':ref(P/'handoff.json'),'matrix':ref(P/'P01-P12-evidence-matrix.json')}
m=read(P/'manifest.json');bad=[]
for n,e in m['entries'].items():
 b=(P/n).read_bytes()
 if H(b)!=e['sha256'] or len(b)!=e['bytes']:bad.append(n)
audit['manifest_entries']={'count':len(m['entries']),'mismatch':bad}
paths=subprocess.check_output(['git','-C',str(W),'diff-tree','--no-commit-id','--name-only','-r',C]).decode('utf-8').splitlines();gitbad=[]
for n in paths:
 b=subprocess.check_output(['git','-C',str(W),'show',C+':'+n])
 if b!=(W/n).read_bytes():gitbad.append(n)
audit['commit_blobs']={'count':len(paths),'outside_source_or_namespace':[n for n in paths if n not in read(P/'handoff.json')['exact_source_paths'] and not n.startswith(N+'/')],'mismatch':gitbad}
src=read(P/'source-final.json');audit['source9']=[]
for e in src['paths']:
 b=(W/e['path']).read_bytes();f=W/e['frozen_copy']['path'];audit['source9'].append({'path':e['path'],'sha256':H(b),'matches_final_and_frozen':H(b)==e['after_sha256'] and b==f.read_bytes()})
c=P/'closure-f7bf47acb6f94c48b5a0095b200cc9e8';before=read(c/'inputs-before.json');after=read(c/'inputs-after.json');audit['closure']={'refs':[ref(c/n) for n in ['inputs-before.json','inputs-after.json','compiled-inputs.json','compiled-inputs-after.json','summary.json']],'sections':{}}
for group,base in [('source',W),('actual_main_sdk_and_dependencies',R)]:
 missing=[];drift=[]
 for n,e in before[group].items():
  p=base/n
  if not p.exists():missing.append(n)
  elif H(p.read_bytes())!=e['sha256']:drift.append(n)
 audit['closure']['sections'][group]={'count':len(before[group]),'before_after_equal':before[group]==after[group],'missing_now':missing,'drift_now':drift}
bc=read(c/'compiled-inputs.json');ac=read(c/'compiled-inputs-after.json');drift=[]
for n,e in bc['files'].items():
 p=Path(n)
 if not p.exists() or H(p.read_bytes())!=e['sha256']:drift.append(n)
audit['closure']['compiled']={'files':len(bc['files']),'packages':len(bc['packages']),'before_after_equal':bc==ac,'drift_now':drift}
audit['closure']['tools']=[{'path':n,'sha256':h,'current_matches':H(Path(n).read_bytes())==h} for n,h in before['tools'].items()]
audit['closure']['bundle']={'expected':before['bundle'],'actual':ref(Path(before['bundle']['path']))}
raw=(c/'js.stdout').read_text(encoding='utf-8');audit['actual_js_counts']={k:int(re.search(r'(?m)^ℹ '+k+r' (\d+)',raw).group(1)) for k in ['tests','pass','fail','skipped','cancelled']}
audit['no_tests_or_network_executed']=True
save('final_read_audit.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k not in ['source9','closure']},ensure_ascii=False));print('closure',json.dumps(audit['closure'],ensure_ascii=False))
