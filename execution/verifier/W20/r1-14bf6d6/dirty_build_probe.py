from pathlib import Path
import subprocess,hashlib,json,zipfile,sys,time
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent;PROBE=OUT/'dirty-build';PROBE.mkdir(exist_ok=True);CHECKOUT=PROBE/'source-checkout'
REV='14bf6d633ca58b4e2bf8b911719ac93e23f53239';commands=[]
def command(label,argv,cwd=ROOT,timeout=120):
 with (PROBE/(label+'.stdout.log')).open('wb') as stdout,(PROBE/(label+'.stderr.log')).open('wb') as stderr:result=subprocess.run(list(map(str,argv)),cwd=cwd,stdout=stdout,stderr=stderr,timeout=timeout)
 row={'label':label,'argv':list(map(str,argv)),'cwd':str(cwd),'exit_code':result.returncode};commands.append(row);assert result.returncode==0,(label,result.returncode);return (PROBE/(label+'.stdout.log')).read_text(encoding='utf-8',errors='replace')
command('clone',['git','clone','--shared','--no-checkout',ROOT,CHECKOUT])
patterns=['/'+x+'/' for x in ['adapters','apps','internal','ops','tests','bootstrap','evaluation','migrations','spec/v2.0','release','docs/installation','execution/command_dispatcher']]+['/'+x for x in ['execution/commands.json','execution/toolchains/locked.json','go.mod','go.sum','AGENTS.md']]
command('sparse',['git','sparse-checkout','set','--no-cone',*patterns],CHECKOUT)
command('checkout',['git','checkout','--detach',REV],CHECKOUT)
before=command('status-before',['git','status','--porcelain=v1'],CHECKOUT);assert not before.strip()
docs=CHECKOUT/'docs/installation/README.md';original=docs.read_bytes();docs.write_bytes(original+b'\nINDEPENDENT_SYNTHETIC_UNCOMMITTED_DOC_MARKER\n')
untracked=CHECKOUT/'release/independent-untracked.json';untracked.write_text('{"probe":"INDEPENDENT_SYNTHETIC_UNTRACKED_MARKER"}\n',encoding='utf-8')
dirty=command('status-dirty',['git','status','--porcelain=v1','--untracked-files=all'],CHECKOUT)
head=command('head',['git','rev-parse','HEAD'],CHECKOUT).strip();assert head==REV
lock=ROOT/'execution/toolchains/locked.json';tools=json.loads(lock.read_text(encoding='utf-8-sig'))['tools'];python=Path(tools['python']['path']);assert hashlib.sha256(python.read_bytes()).hexdigest()==tools['python']['sha256']
archive=PROBE/'dirty-input-candidate.zip';start=time.monotonic()
output=command('build',[python,'-X','utf8',CHECKOUT/'ops/release/build.py','--source',CHECKOUT,'--tool-lock',lock,'--output',archive],CHECKOUT,timeout=180)
receipt=json.loads(output);observed={'build_exit_code':0,'source_commit':receipt['source_commit'],'archive_sha256':receipt['archive_sha256'],'head':head,'dirty_status_before':dirty,'elapsed_seconds':time.monotonic()-start}
with zipfile.ZipFile(archive) as z:
 manifest=json.loads(z.read('release-manifest.json'));observed['manifest_source_commit']=manifest['source_commit'];observed['uncommitted_docs_packaged']=b'INDEPENDENT_SYNTHETIC_UNCOMMITTED_DOC_MARKER' in z.read('docs/installation/README.md');observed['untracked_json_packaged']='release/independent-untracked.json' in z.namelist() and b'INDEPENDENT_SYNTHETIC_UNTRACKED_MARKER' in z.read('release/independent-untracked.json');observed['source_tree_sha256']=manifest['source_tree_sha256']
after=command('status-after',['git','status','--porcelain=v1','--untracked-files=all'],CHECKOUT);observed['dirty_status_after']=after
(PROBE/'commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8');(PROBE/'result.json').write_text(json.dumps(observed,indent=2)+'\n',encoding='utf-8')
print(json.dumps(observed,indent=2))
