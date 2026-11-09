import os, sys, json, hashlib, subprocess, pathlib, datetime, time
P=pathlib.Path
R=P('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/desktop-installed-delivery-20261025'
E=P(__file__).resolve().parent
EXPECTED='9361c1b63fa658251f730771bc12633ff5f12c08'
NODE=P('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')
PY=P('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
GO=R/'.local/tools/go1.27.1/go/bin/go.exe'
def sha(p): return hashlib.sha256(P(p).read_bytes()).hexdigest()
def write(n,x): (E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args): return subprocess.check_output(['git','-C',str(W),*args]).decode('utf-8').strip()
def snap():
    names=git('ls-files','--','apps/cli','internal','go.mod','go.sum','apps/desktop','tests/ui/desktop/product-host.test.mjs','tests/ui/desktop/product-layout.test.py').splitlines()
    files=[{'path':n,'sha256':sha(W/n),'bytes':(W/n).stat().st_size} for n in names if (W/n).is_file()]
    return {'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain'),'files':files,'tools':[{'path':str(p),'sha256':sha(p)} for p in (NODE,PY,GO)]}
before=snap(); write('source.before.json',before)
if before['head']!=EXPECTED or before['status']: raise RuntimeError('source precondition')
env=dict(os.environ)
removed=[]
for k in list(env):
    if k.upper().startswith(('RESEARCHOS','ROS_DESKTOP','NODE','ELECTRON')) or 'PROXY' in k.upper():
        removed.append(k); del env[k]
for k,folder in {'TMP':'tmp','TEMP':'tmp','GOTMPDIR':'gotmp','GOCACHE':'gocache','LOCALAPPDATA':'profile/local','APPDATA':'profile/roaming','USERPROFILE':'profile','HOME':'profile'}.items():
    p=E/folder; p.mkdir(parents=True,exist_ok=True); env[k]=str(p)
env.update(GOENV='off',GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOMODCACHE=str(R/'.local/tools/gopath/pkg/mod'),GOPATH=str(E/'gopath'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
write('environment.json',{'removed_inherited_names':removed,'overrides':{k:env[k] for k in ['TMP','TEMP','GOTMPDIR','GOCACHE','LOCALAPPDATA','APPDATA','USERPROFILE','HOME','GOENV','GOTOOLCHAIN','GOPROXY','GOSUMDB','GOMODCACHE','GOPATH','PYTHONDONTWRITEBYTECODE','PYTHONUTF8']}})
commands=[('node',[str(NODE),'--test','tests/ui/desktop/product-host.test.mjs']),('python',[str(PY),'-B','-X','utf8','tests/ui/desktop/product-layout.test.py']),('go',[str(GO),'test','./apps/cli','-run','^TestProduct','-count=1','-timeout=300s','-v'])]
out=[]
for name,argv in commands:
    start=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.monotonic()
    write(name+'.recipe.json',{'argv':argv,'cwd':str(W),'started_at':start,'source_before_sha256':sha(E/'source.before.json'),'environment_sha256':sha(E/'environment.json')})
    with (E/(name+'.stdout.raw')).open('wb') as so,(E/(name+'.stderr.raw')).open('wb') as se:
        p=subprocess.Popen(argv,cwd=W,env=env,stdout=so,stderr=se)
        write(name+'.process.json',{'pid':p.pid,'argv':argv,'started_at':start})
        rc=p.wait(timeout=420)
    item={'name':name,'exit_code':rc,'seconds':time.monotonic()-t,'stdout_sha256':sha(E/(name+'.stdout.raw')),'stderr_sha256':sha(E/(name+'.stderr.raw'))}
    write(name+'.result.json',item); out.append(item); print(json.dumps(item),flush=True)
after=snap(); write('source.after.json',after)
write('RESULT.json',{'source_unchanged':before==after,'commands':out,'all_exit_zero':all(x['exit_code']==0 for x in out),'scope':'SOURCE_BOUND_PURE_MOCK_FILESYSTEM_AND_CLI_TEST_CHILD_ONLY_NO_PRODUCT_CORE_ELECTRON_NATIVE'})
if before!=after or not all(x['exit_code']==0 for x in out): sys.exit(1)
