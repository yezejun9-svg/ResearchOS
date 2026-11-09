from pathlib import Path
import subprocess,json,hashlib,os,datetime
R=Path.cwd();W=R/'.local/worktrees/w11-frozen-service-review-0252dcd';O=R/'execution/verifier/W11/frozen-service-0252dcd';G=R/'.local/tools/go1.27.1/go/bin/go.exe';env={k:v for k,v in os.environ.items() if 'JEV' not in k.upper() and 'TYPESAFE' not in k.upper()};h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
files=[p for pattern in ['adapters/protectedstore/*.go','adapters/protectedstore/*.json','adapters/protectedstore/cmd/canary-broker/*','adapters/decision/*.go','evaluation/holdout/jev/*.go','tests/jev/protected/*','go.mod','go.sum']for p in W.glob(pattern)if p.is_file()]
save(O/'source-before.json',{'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip(),'status':subprocess.check_output(['git','status','--porcelain'],cwd=W,text=True),'files':{p.relative_to(W).as_posix():h(p)for p in files},'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
B=W/'.local/reviewer/canary-broker.exe';B.parent.mkdir(parents=True,exist_ok=True)
commands=[]
def run(name,args):
 p=subprocess.run(args,cwd=W,env=env,capture_output=True,timeout=120);(O/(name+'.stdout.txt')).write_bytes(p.stdout);(O/(name+'.stderr.txt')).write_bytes(p.stderr);commands.append({'name':name,'argv':[str(a)for a in args],'exit':p.returncode});save(O/'commands.json',commands);return p
p=run('binary-rebuild',[G,'build','-trimpath','-o',B,'./adapters/protectedstore/cmd/canary-broker']);assert p.returncode==0
run('binary-build-info',[G,'version','-m',B]);sha=h(B);save(O/'binary.json',{'path':str(B),'sha256':sha,'expected':'938ed0dd2fb954e31d4fbd2c421da1a4ed4ca9859c2bc370009e483df6cee241','matches':sha=='938ed0dd2fb954e31d4fbd2c421da1a4ed4ca9859c2bc370009e483df6cee241'})
p=run('default-plan',['pwsh','-NoProfile','-File',W/'tests/jev/protected/deployment.ps1','-Binary',B,'-ExpectedSHA256',sha,'-ProjectRoot',R]);assert p.returncode==0
p=run('interactive-service-refusal',[B,'--service','--reader-sid','S-1-5-21-1-2-3-1001']);assert p.returncode!=0
p=run('missing-installed-service-status',[B,'--status']);assert p.returncode!=0
print(json.dumps({'binary_sha':sha,'matches_owner':sha=='938ed0dd2fb954e31d4fbd2c421da1a4ed4ca9859c2bc370009e483df6cee241','commands':[{k:x[k]for k in ['name','exit']}for x in commands]}))
