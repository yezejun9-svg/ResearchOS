"""Restore exact missing Git objects with native git; never alter any index.

Every source is byte-verified against the independent recovery manifest and Git
object ID before native hash-object can write it. No missing data is inferred.
"""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=Path(__file__).parent.resolve()
M=E/'recovery-manifest-complete.json'
assert hashlib.sha256(M.read_bytes()).hexdigest()=='fb98d1dc4548f151ebaae6174d8067c00061412915c114641a9748517870516c'
m=json.loads(M.read_bytes());assert m['count']==4354 and not m['remaining'] and m['root_reconstruction_matches']
def git(argv,cwd=R,**kw):return subprocess.run(['git']+argv,cwd=cwd,capture_output=True,check=True,**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git(['rev-parse','HEAD']).stdout.decode().strip()==m['head']
indices=[]
for cwd in [R,R/'.local/worktrees/verifier-replacement-20261014']:
 p=Path(git(['rev-parse','--path-format=absolute','--git-path','index'],cwd).stdout.decode().strip());indices.append((p,sha(p)))
assert indices[0][1]==m['index_sha256']
assert not git(['diff','--cached','--name-only']).stdout
started=datetime.datetime.now(datetime.timezone.utc).isoformat();seen=set();verified=[]
for v in m['entries']:
 p=Path(v['path']);p=p if p.is_absolute() else R/p
 assert p.resolve().is_relative_to(R.resolve()) and not p.is_symlink()
 assert v['type'] in ['blob','tree'] and v['oid'] not in seen;seen.add(v['oid'])
 b=p.read_bytes();assert len(b)==v['size'] and hashlib.sha256(b).hexdigest()==v['sha256']
 assert hashlib.sha1(v['type'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==v['oid']
 verified.append((v,p))
print(json.dumps({'state':'ALL4354_INPUTS_AND_GIT_IDS_VERIFIED','bytes':sum(v['size'] for v,p in verified)}),flush=True)
out=E/'root-restore-objects.attempts.jsonl';assert not out.exists();count=0
try:
 with out.open('x',encoding='utf8') as log:
  for v,p in verified:
   # Recheck just before writing: unrelated agents can be writing elsewhere.
   assert p.stat().st_size==v['size'] and sha(p)==v['sha256']
   t=time.monotonic();result=subprocess.run(['git','hash-object','-w','-t',v['type'],'--',str(p)],cwd=R,capture_output=True)
   actual=result.stdout.decode().strip();entry={'oid':v['oid'],'type':v['type'],'source':str(p),'native_exit':result.returncode,'actual_oid':actual,'elapsed_seconds':time.monotonic()-t}
   if result.returncode:entry['stderr']=result.stderr.decode('utf8',errors='strict')
   log.write(json.dumps(entry,ensure_ascii=False)+'\n');log.flush()
   assert result.returncode==0 and actual==v['oid'];count+=1
   if count%500==0:print(json.dumps({'restored':count,'total':len(verified)}),flush=True)
finally:
 unchanged=all(sha(p)==before for p,before in indices)
 summary={'started':started,'ended':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':sha(M),'verified_inputs':len(verified),'native_writes_completed':count,'indices_unchanged':unchanged,'index_pins':[{'path':str(p),'sha256':before} for p,before in indices],'working_files_written':0,'refs_written':0,'history_objects_not_covered':4924,'formal_increment':0}
 with (E/'root-restore-summary.json').open('x',encoding='utf8') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
 assert unchanged
assert count==4354
git(['cat-file','-t','6140a5b5ead748e28487b78a777bf9c8d07192e8']);git(['ls-tree','HEAD','--','execution/v2.4/checkpoint.json'])
print(json.dumps(summary,ensure_ascii=True),flush=True)
