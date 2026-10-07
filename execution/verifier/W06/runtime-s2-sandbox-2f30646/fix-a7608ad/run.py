from pathlib import Path
import subprocess,os,hashlib,json,time
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=PRIOR.parents[3];REV='a7608ad49906b174506e2198073415a4483f8408'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
oldindices=[]
for path,wanted in [(PRIOR/'index.json','ec5729b5bd65247383025e244a7351e43fa4d70f24e9bc93554006b1a64c0e14'),(PRIOR/'fix-678a68c/index.json','6f680749121900619370719fd17f0b3d33014299d080a5dc25b5fc160f576221')]:
 assert sha(path)==wanted;old=json.loads(path.read_text());[(_ for _ in ()).throw(AssertionError(row['path'])) for row in old['files'] if sha(path.parent/row['path'])!=row['sha256']];oldindices.append({'path':str(path.relative_to(ROOT)),'sha256':wanted,'files_verified':len(old['files'])})
replace={};source=[]
for name in ['async_windows.go','async_windows_test.go','sandbox_windows.go']:
 path='ops/experiment_sandbox/'+name;dest=OUT/'source'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(git('show',REV+':'+path));replace[str(ROOT/path)]=str(dest);source.append({'path':path,'sha256':sha(dest)})
author=[]
for path in git('ls-tree','-r','--name-only','1bcec7c','execution/receipts/W06/runtime-s2/sandbox-identity-json').decode().splitlines():
 dest=OUT/'author-evidence'/Path(path).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(git('show','1bcec7c:'+path));author.append({'path':path,'sha256':sha(dest)})
replace[str(ROOT/'internal/domain/independent_sandbox_identity_test.go')]=str(OUT/'identity_nested_test.go');put(OUT/'overlay.json',{'Replace':replace})
domain=ROOT/'internal/domain/contracts.go';before=sha(domain)
put(OUT/'source-audit.json',{'source_revision':REV,'main_head':git('rev-parse','HEAD').decode().strip(),'sources':source,'source_diff':git('diff','678a68c',REV,'--','ops/experiment_sandbox').decode(),'domain_decoder_sha256':before,'prior_indices':oldindices,'author_evidence':author})
lock=json.loads((ROOT/'execution/toolchains/go.json').read_text(encoding='utf-8-sig'));exe=Path(lock['executable']);assert sha(exe)==lock['executable_sha256'];env=dict(os.environ,GOTOOLCHAIN='local',GOENV='off')
args=[str(exe),'test','-json','-count=1','-timeout=60s','-overlay='+str(OUT/'overlay.json'),'./internal/domain','-run','^TestIndependentSandboxIdentityNestedJSON$'];start=time.monotonic()
with (OUT/'stdout.jsonl').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:proc=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=90)
put(OUT/'command.json',{'argv':args,'cwd':str(ROOT),'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start,'go_sha256':lock['executable_sha256'],'domain_decoder_unchanged':sha(domain)==before})
assertions=[]
for line in (OUT/'stdout.jsonl').read_text().splitlines():
 event=json.loads(line);out=event.get('Output','')
 if out.startswith('S2_IDENTITY_ASSERT '):assertions.append(json.loads(out.removeprefix('S2_IDENTITY_ASSERT ')))
put(OUT/'assertions.json',assertions);print(json.dumps({'exit_code':proc.returncode,'assertions':len(assertions),'failures':[r for r in assertions if r['status']!='PASS'],'stderr':(OUT/'stderr.log').read_text()},indent=2))
