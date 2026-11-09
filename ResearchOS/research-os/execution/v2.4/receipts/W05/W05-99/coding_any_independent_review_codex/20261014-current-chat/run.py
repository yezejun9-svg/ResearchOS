import pathlib,json,subprocess,os,time,sys
R=pathlib.Path(__file__).parent;S=R/'source';G='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe';O=R/'runs';O.mkdir(exist_ok=True);T=R/'fixture-temp';T.mkdir(exist_ok=True)
env=os.environ.copy();env.update(GOFLAGS='-buildvcs=false',TEMP=str(T),TMP=str(T),REVIEW_SCOPE_INPUT=str(R/'scope-input.json'),REVIEW_ACTUAL326_FIXTURE=str(R/'actual326-fixture'))
for name in sys.argv[1:]:
 e=env.copy()
 if name=='baseline':e['REVIEW_BASELINE']='1';args=['-overlay',str(R/'baseline-overlay.json'),'-run','^TestIndependent']
 elif name=='candidate':e['REVIEW_BASELINE']='0';args=['-run','^TestIndependent|^TestProductCoding(CheckInventory|PrivateFrames)$']
 else:raise ValueError(name)
 cmd=[G,'test','./internal/host',*args,'-count=1','-v'];start=time.time()
 with (O/(name+'.stdout.txt')).open('xb') as out,(O/(name+'.stderr.txt')).open('xb') as err:p=subprocess.run(cmd,cwd=S,env=e,stdout=out,stderr=err,timeout=120)
 result={'argv':cmd,'cwd':str(S),'exit':p.returncode,'elapsed':time.time()-start,'env':{k:e[k] for k in ['GOFLAGS','REVIEW_SCOPE_INPUT','REVIEW_ACTUAL326_FIXTURE','REVIEW_BASELINE']}}
 (O/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'name':name,'exit':p.returncode,'seconds':result['elapsed']}),flush=True)
 if p.returncode:sys.exit(p.returncode)
