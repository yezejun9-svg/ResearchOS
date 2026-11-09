import pathlib,json,hashlib,subprocess
P=pathlib.Path;R=P('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/desktop-installed-delivery-20261025';E=P(__file__).resolve().parent
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def req(c,m):
 if not c:raise RuntimeError(m)
def git(*args):return subprocess.check_output(['git','-C',str(W),*args]).decode('utf8').strip()
head='5c4c94022bd92da68ef544f2779527bfe065c428';tree='133c6fdee17e1ad2f7758689c55c1486e778cec0'
req(git('rev-parse','HEAD')==head and git('rev-parse','HEAD^{tree}')==tree and not git('status','--porcelain'),'source freeze')
req(git('diff','--name-only',head+'^',head).splitlines()==['apps/desktop/main/main.js','tests/ui/desktop/product-host.test.mjs'],'exact2')
refs=[]
for rel in ['apps/desktop/main/main.js','apps/desktop/main/lib/product-layout.js','tests/ui/desktop/product-host.test.mjs']:
 p=W/rel;raw=p.read_bytes();dest=E/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(raw)
 req(hashlib.sha256(subprocess.check_output(['git','-C',str(W),'show',head+':'+rel])).hexdigest()==sha(dest)==sha(p),'source copy')
 refs.append({'path':str(p),'relative_path':rel,'snapshot':str(dest),'sha256':sha(p),'bytes':len(raw)})
req(refs[1]['sha256']=='4379be504232309f3f7be71b7cc0e2d9be54e331e34bfa84820c08c2f00009eb','unchanged loader')
(E/'exact2.diff').write_text(git('diff',head+'^',head)+'\n',encoding='utf8')
old=E.parent/'main-lifecycle-mock.cjs';s=old.read_text(encoding='utf8')
s=s.replace('const ready=deferred(), started=deferred();',"const ready=deferred(), started=deferred();\n  const physicalFs={reviewMarker:'ELECTRON_ORIGINAL_FS'};calls.physicalLoader=0;")
s=s.replace("'node:fs':{mkdirSync:name=>calls.writes.push(name)},","'node:fs':{mkdirSync:name=>calls.writes.push(name)},'original-fs':physicalFs,")
s=s.replace('loadProductLayout:()=>layout','loadProductLayout:(_root,io)=>{assert.strictEqual(io,physicalFs);calls.physicalLoader++;return layout;}')
s=s.replace("vm.runInNewContext(source,sandbox,{filename:'captured-main.js'});","vm.runInNewContext(source,sandbox,{filename:'captured-main.js'});\n  assert.equal(calls.physicalLoader,1,'MAIN_MUST_INJECT_ORIGINAL_FS_EXACTLY_ONCE');")
s=s.replace("results.push({id:'MAIN-BROKEN-STARTUP-KEEPS-DIAGNOSTIC-ENTRY',pass:true});","results.push({id:'MAIN-BROKEN-STARTUP-KEEPS-DIAGNOSTIC-ENTRY',pass:true});\n  results.push({id:'MAIN-PHYSICAL-FS-INJECTED-IN-ALL-FOUR-BRANCHES',pass:true});")
p=E/'main-lifecycle-physical-fs-mock.cjs';p.write_text(s,encoding='utf8')
node=P('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe');req(sha(node)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6','node')
argv=[str(node),str(p),str(E/'source'),str(E/'VM-RESULT.json')]
result=subprocess.run(argv,cwd=E,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
(E/'vm.stdout.raw').write_bytes(result.stdout);(E/'vm.stderr.raw').write_bytes(result.stderr)
req(all(sha(r['path'])==r['sha256']==sha(r['snapshot']) for r in refs),'source drift')
(E/'SOURCE-VM-REVIEW.json').write_text(json.dumps({'head':head,'tree':tree,'parent':git('rev-parse','HEAD^'),'exact2':True,'loader_unchanged':True,'inputs':refs,'original_vm_script':{'path':str(old),'sha256':sha(old)},'new_vm_script':{'path':str(p),'sha256':sha(p)},'argv':argv,'exit':result.returncode,'result_sha256':sha(E/'VM-RESULT.json'),'source_and_snapshot_stable':True,'product_processes':0,'formal_increment':0},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(result.stdout.decode('utf8'));req(result.returncode==0,'VM failed')
