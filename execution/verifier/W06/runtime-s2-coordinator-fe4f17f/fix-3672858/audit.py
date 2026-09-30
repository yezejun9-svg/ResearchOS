from pathlib import Path
import subprocess,json,hashlib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[4]
def rawgit(rev,path):return subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
audits=[]
for revision,label,prefix in [('43d7724','recovery','execution/receipts/W06/runtime-s2/coordinator-recovery-1/'),('53728f1','seal-retry','execution/receipts/W06/runtime-s2/seal-retry-bound/')]:
 target=OUT/'author-evidence'/label;target.mkdir(parents=True,exist_ok=True);names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--',prefix],cwd=ROOT).decode().splitlines();files=[]
 for name in names:
  raw=rawgit(revision,name);p=target/Path(name).name;p.write_bytes(raw);files.append({'git_path':name,'sha256':digest(raw),'bytes':len(raw)})
 receipt=json.loads((target/'receipt.json').read_bytes());events=[json.loads(line) for line in (target/'stdout.jsonl').read_bytes().splitlines()]
 for name,expected in receipt.get('artifacts',{}).items():assert digest((target/name).read_bytes())==expected,(label,name)
 source_checks=[]
 for name,expected in receipt.get('source_sha256',{}).items():
  raw=rawgit(receipt['source_commit'],name);assert digest(raw)==expected,(label,name);source_checks.append({'path':name,'sha256':digest(raw),'match':True})
 audits.append({'revision':revision,'receipt':receipt,'files':files,'source_checks':source_checks,'test_runs':sum(x['Action']=='run' for x in events),'test_passes':sum(x['Action']=='pass' and bool(x.get('Test')) for x in events),'test_skips':[x for x in events if x['Action']=='skip' and x.get('Test')],'package_skips':[x for x in events if x['Action']=='skip' and not x.get('Test')],'failures':[x for x in events if x['Action']=='fail'],'highlights':[x for x in events if 'RUNTIME_' in x.get('Output','')]})
put(OUT/'author-audit.json',{'mode':'Read-only inspection of existing Git-frozen receipts; no tests or native workers executed.','audits':audits})
print(json.dumps([{'revision':r['revision'],'tests':r['test_runs'],'passes':r['test_passes'],'source_hashes':len(r['source_checks']),'failures':len(r['failures'])} for r in audits]))
