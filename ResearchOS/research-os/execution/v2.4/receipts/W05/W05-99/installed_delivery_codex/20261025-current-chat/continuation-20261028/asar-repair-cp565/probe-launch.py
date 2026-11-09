import os,sys,json,hashlib,subprocess,datetime
from pathlib import Path
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/desktop-installed-delivery-20261025'
A=W/'.local/asar-repair-cp565-20261028'
E=R/'execution/v2.4/receipts/W05/W05-99/installed_delivery_codex/20261025-current-chat/continuation-20261028/asar-repair-cp565'
B=W/'.local/product-layout-cp558-20261028-04'
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp565/ASAR-exact2-repair-scope.json'
def sha(p):
    x=hashlib.sha256()
    with Path(p).open('rb') as f:
        for z in iter(lambda:f.read(1048576),b''):x.update(z)
    return x.hexdigest()
def write(name,value):
    p=E/name
    assert not p.exists(),p
    p.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
assert sha(S)=='2356e030bf6a2ea303701444db6338901b333d78f3b872b3291e15c6fa5dac1f'
electron=B/'runtime/electron/electron.exe'
marker=B/'installed-product.json'
assert sha(electron)=='8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac'
assert sha(marker)=='37741bb91c67b7c5529e87f92e20b893bca919a68dbc83e1cb460f0185dee3b0'
assert sha(W/'apps/desktop/main/lib/product-layout.js')=='4379be504232309f3f7be71b7cc0e2d9be54e331e34bfa84820c08c2f00009eb'
profile={}
for name in ['LOCALAPPDATA','APPDATA','USERPROFILE','TEMP','TMP']:
    p=A/name.lower();p.mkdir(exist_ok=False);profile[name]=str(p)
systemroot=os.environ.get('SystemRoot',r'C:\Windows')
env={'SystemRoot':systemroot,'WINDIR':systemroot,'SystemDrive':os.environ.get('SystemDrive','C:'),
     'COMSPEC':str(Path(systemroot)/'System32/cmd.exe'),'PATH':str(Path(systemroot)/'System32')+';'+systemroot,
     'PATHEXT':'.COM;.EXE;.BAT;.CMD',**profile}
argv=[str(electron),str(A/'probe-app')]
write('probe-invocation.json',{'schema':'researchos.asar-physical-launch.v1',
     'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'cwd':str(A),
     'environment':env,'entry_sha256':sha(A/'probe-app/main.js'),'package_sha256':sha(A/'probe-app/package.json'),
     'electron_sha256':sha(electron),'marker_sha256':sha(marker),'scope_sha256':sha(S),
     'shell':False,'creationflags':'CREATE_NO_WINDOW','timeout_s':60,'timeout_action':'RECORD_AND_LEAVE_RUNNING'})
with (E/'probe-stdout.raw').open('xb') as out, (E/'probe-stderr.raw').open('xb') as err:
    p=subprocess.Popen(argv,cwd=A,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                       shell=False,creationflags=subprocess.CREATE_NO_WINDOW)
    write('probe-pid.json',{'pid':p.pid,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            'argv':argv,'executable':str(electron)})
    try:
        code=p.wait(timeout=60)
        terminal=True
    except subprocess.TimeoutExpired:
        code=None;terminal=False
write('probe-exit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,
                         'terminal':terminal,'exit_code':code,'timeout':not terminal,'forced_termination':False})
print(json.dumps({'pid':p.pid,'terminal':terminal,'exit_code':code}))
sys.exit(0 if terminal and code==0 else 1)
