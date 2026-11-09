from pathlib import Path
import subprocess,hashlib,json,zipfile,os,struct,time
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=PRIOR.parents[3];CHECKOUT=OUT/'source-checkout'
REV='6de7543da751ace1d2d603a751f520e5fed71caa';commands=[];checks=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def command(label,argv,cwd=OUT,env=None,timeout=120):
 start=time.monotonic()
 with (OUT/(label+'.stdout.log')).open('wb') as stdout,(OUT/(label+'.stderr.log')).open('wb') as stderr:result=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,stdout=stdout,stderr=stderr,timeout=timeout)
 row={'label':label,'argv':list(map(str,argv)),'cwd':str(cwd),'exit_code':result.returncode,'seconds':time.monotonic()-start};commands.append(row);put(OUT/'build-commands.json',commands);return row,(OUT/(label+'.stdout.log')).read_text(encoding='utf-8',errors='replace')
def okcmd(*args,**kwargs):r,out=command(*args,**kwargs);assert r['exit_code']==0,r;return out
def check(id,condition,actual):checks.append({'id':id,'status':'PASS' if condition else 'FAIL','actual':actual});put(OUT/'build-assertions.json',checks);assert condition,(id,actual)
old=json.loads((PRIOR/'index.json').read_text());assert sha(PRIOR/'index.json')=='fad9e6f1ac1fa49ef06d7eb59b753eb7356fefcb53438b426e8948f5f4780ae6'
for row in old['files']:assert sha(PRIOR/row['path'])==row['sha256']
okcmd('clone',['git','clone','--shared','--no-checkout',ROOT,CHECKOUT])
dirs=['adapters','apps','bootstrap','contracts','evaluation','internal','migrations','ops','qualification','release','spec','tests','docs/installation','execution/command_dispatcher']
files=['.gitattributes','.gitignore','AGENTS.md','go.mod','go.sum','execution/commands.json','execution/toolchains/locked.json']
okcmd('sparse',['git','sparse-checkout','set','--no-cone',*['/'+p+'/' for p in dirs],*['/'+p for p in files]],cwd=CHECKOUT)
okcmd('checkout',['git','checkout','--detach',REV],cwd=CHECKOUT)
before=okcmd('status-before',['git','status','--porcelain=v1'],cwd=CHECKOUT);assert not before.strip()
lock=CHECKOUT/'execution/toolchains/locked.json';tools=json.loads(lock.read_text(encoding='utf-8-sig'))['tools'];python=Path(tools['python']['path']);assert sha(python)==tools['python']['sha256']
build=[python,'-X','utf8',CHECKOUT/'ops/release/build.py','--source',CHECKOUT,'--tool-lock',lock]
env=dict(os.environ,GOOS='linux',GOARCH='arm64',GOFLAGS='-must-not-reach-go',GOWORK=str(OUT/'must-not-use.work'),NODE_OPTIONS='--must-not-reach-node')
receipts=[]
for label in ['build-first','build-second']:
 archive=OUT/(label+'.zip');raw=okcmd(label,[*build,'--output',archive],env=env,timeout=180);receipt=json.loads(raw);assert sha(archive)==receipt['archive_sha256'];receipts.append(receipt)
check('two-independent-builds-byte-identical',receipts[0]['archive_sha256']==receipts[1]['archive_sha256'],[r['archive_sha256'] for r in receipts])
with zipfile.ZipFile(OUT/'build-first.zip') as z:
 manifest=json.loads(z.read('release-manifest.json'));put(OUT/'release-manifest.json',manifest)
 check('manifest-fixed-source',manifest['source_commit']==REV,manifest['source_commit'])
 names=z.namelist();listed={r['path']:r for r in manifest['files']};check('exact-sorted-zip-inventory',names==sorted(set(names)) and set(names)==set(listed)|{'release-manifest.json'},len(names))
 check('all-manifest-file-hashes',all(hashlib.sha256(z.read(n)).hexdigest()==r['sha256'] and len(z.read(n))==r['size'] for n,r in listed.items()),len(listed))
 machines={}
 for name in ['control','runtime','backup']:
  raw=z.read('bin/'+name+'.exe');offset=struct.unpack_from('<I',raw,0x3c)[0];machines[name]={'DOS':raw[:2].decode(),'PE':raw[offset:offset+4].hex(),'machine':struct.unpack_from('<H',raw,offset+4)[0]}
 check('actual-binaries-windows-amd64',all(r['DOS']=='MZ' and r['PE']=='50450000' and r['machine']==0x8664 for r in machines.values()),machines)
 check('manifest-scope-stays-nonlive',manifest['platform']=='windows/amd64' and manifest['acceptance']['normal_live_runtime']=='CLOSED' and manifest['acceptance']['W20']=='NOT_ACCEPTED',manifest['acceptance'])
 release=OUT/'fixture-release';release.mkdir();z.extractall(release)
after=okcmd('status-after-clean-builds',['git','status','--porcelain=v1','--untracked-files=all'],cwd=CHECKOUT)
check('clean-source-unchanged-after-builds',not after.strip(),after)
# Each refused candidate is a separate small negative; restore only our own file bytes.
for label,path,addition in [
 ('dirty-docs',CHECKOUT/'docs/installation/README.md',b'\nSYNTHETIC_UNCOMMITTED_DOC\n'),
 ('dirty-registry',CHECKOUT/'execution/commands.json',b'\n'),
 ('untracked-source',CHECKOUT/'release/independent-untracked.json',b'{"synthetic":true}\n')]:
 existed=path.exists();original=path.read_bytes() if existed else None
 try:
  path.write_bytes((original or b'')+addition);output=OUT/(label+'.zip');receipt,raw=command(label,[*build,'--output',output],env=env,timeout=30)
  error=(OUT/(label+'.stderr.log')).read_text(encoding='utf-8',errors='replace');check(label+'-refused',receipt['exit_code']!=0 and not output.exists() and ('frozen' in error),{'exit_code':receipt['exit_code'],'error':error,'output_exists':output.exists()})
 finally:
  if existed:path.write_bytes(original)
  else:path.unlink()
final=okcmd('status-final',['git','status','--porcelain=v1','--untracked-files=all'],cwd=CHECKOUT);check('negative-probes-restore-owned-checkout',not final.strip(),final)
source_files={p:sha(CHECKOUT/p) for p in ['ops/release/build.py','ops/release/start.ps1','ops/release/stop.ps1','ops/release/verify.ps1','docs/installation/README.md','tests/release/check.py','release/fixture-config.json','execution/commands.json','go.mod','go.sum','execution/toolchains/locked.json']}
for p in ['ops/release/build.py','ops/release/start.ps1','ops/release/stop.ps1','ops/release/verify.ps1','docs/installation/README.md','tests/release/check.py','release/fixture-config.json']:
 dest=OUT/'source'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((CHECKOUT/p).read_bytes())
put(OUT/'build-audit.json',{'source_revision':REV,'prior_index_sha256':sha(PRIOR/'index.json'),'prior_files_unchanged':len(old['files']),'build_receipts':receipts,'source_file_sha256':source_files,'hostile_environment_overrides':{k:env[k] for k in ['GOOS','GOARCH','GOFLAGS','GOWORK','NODE_OPTIONS']},'tool_python_sha256':sha(python),'actual_PE_headers':machines,'checks':len(checks)})
print(json.dumps({'source_revision':REV,'archive_sha256':receipts[0]['archive_sha256'],'assertions_pass':len(checks),'manifest_files':len(listed)},indent=2))
