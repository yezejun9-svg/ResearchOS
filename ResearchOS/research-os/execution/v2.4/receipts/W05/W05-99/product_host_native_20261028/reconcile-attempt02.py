"""One explicit controlled window close after the failed init; never kill/retry."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path

HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    original=HERE/'attempt-02';out=HERE/'attempt-02-reconcile';assert not out.exists()
    failure=read(original/'UNRESOLVED.json');w=read(original/'first.witness.json')
    assert failure['first_witness']==w and failure['current_witness']==w
    assert read(HERE/'attempt-02-outer/exit.json')['exit']==1
    assert not any('close' in r['label'] for r in failure['children'])
    bundle=Path(w['install_root']);data=Path(w['data_root']);witness=data/'product-supervisor.json'
    assert read(witness)==w and w['state']=='READY'
    assert w['parent_process']['PID']==66940 and w['control_process']['PID']==64080
    assert read(bundle/'installed-product.json')['installation_id']==w['installation_id']
    helper=HERE/'driver-v2/close-owned-window.ps1'
    assert ref(helper)['sha256']=='0919774c0542b522977f397b93f1b63e605a9163275ff87afa5dfabbe8d5a762'
    electron=bundle/'runtime/electron/electron.exe';assert ref(electron)['sha256']==w['parent_process']['ImageSHA256']
    ps=Path('C:/Users/yqyyds/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
    out.mkdir();env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','OS','PATH','PATHEXT']}
    for key,leaf in [('LOCALAPPDATA','LocalAppData'),('APPDATA','Roaming'),('USERPROFILE','User'),('TEMP','Temp'),('TMP','Temp')]:env[key]=str(data.parents[2]/leaf)
    argv=[str(ps),'-NoProfile','-NonInteractive','-File',str(helper),'-OwnedDesktopPid',str(w['parent_process']['PID']),'-OwnedDesktopImage',str(electron),'-OwnedDesktopCreatedNS',w['parent_process']['CreatedNS'],'-OwnedDesktopSHA256',w['parent_process']['ImageSHA256']]
    new(out/'scope.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'codex:/root','action':'ONE_EXPLICIT_OWNED_WINDOW_WM_CLOSE_THROUGH_EXISTING_SAFE_SHUTDOWN','reason':'attempt02 reached READY, init rejected; no prior shutdown sent; exact witnessed owned processes reconciled by helper before message','witness_ref':ref(original/'first.witness.json'),'failure_ref':ref(original/'UNRESOLVED.json'),'helper_ref':ref(helper),'argv':argv,'automatic_retry':False,'force_kill':False,'original_user_data_actions':False})
    with (out/'close.stdout.raw').open('xb') as stdout,(out/'close.stderr.raw').open('xb') as stderr:
        child=subprocess.Popen(argv,cwd=bundle,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        new(out/'close.spawn.json',{'pid':child.pid,'argv':argv});code=child.wait()
    new(out/'close.exit.json',{'exit':code,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stdout':ref(out/'close.stdout.raw'),'stderr':ref(out/'close.stderr.raw')})
    if code!=0:return code
    script='$limit=[DateTime]::UtcNow.AddSeconds(35); do { $rows=@(); foreach($ownedId in @(66940,64080)) { $p=Get-CimInstance Win32_Process -Filter ("ProcessId="+$ownedId); $rows+=@{pid=$ownedId;present=($null -ne $p);image=if($p){$p.ExecutablePath}else{$null};creation=if($p){[string]$p.CreationDate}else{$null}} }; if(-not($rows | Where-Object present)){break}; Start-Sleep -Milliseconds 200 } while([DateTime]::UtcNow -lt $limit); ConvertTo-Json -InputObject @($rows) -Depth 4 -Compress'
    result=subprocess.run([str(ps),'-NoProfile','-NonInteractive','-Command',script],cwd=bundle,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW,check=False)
    (out/'pids.stdout.raw').write_bytes(result.stdout);(out/'pids.stderr.raw').write_bytes(result.stderr)
    rows=json.loads(result.stdout.decode('utf-8-sig')) if result.returncode==0 else []
    absent=result.returncode==0 and len(rows)==2 and all(not r['present'] for r in rows)
    final={'status':'CONTROLLED_OWNED_CLOSE_OBSERVED' if absent and not witness.exists() else 'CLOSE_UNRESOLVED_NO_RETRY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid_query_exit':result.returncode,'processes':rows,'witness_retired':not witness.exists(),'data_retained':data.is_dir(),'exit_codes_of_product_processes':'NOT_AVAILABLE_AFTER_CONTROLLER_EXIT','native_attempt_acceptance':False,'formal_increment':0,'force_kill':False}
    new(out/'FINAL.json',final);print(json.dumps(final));return 0 if absent and not witness.exists() else 1

if __name__=='__main__':raise SystemExit(main())
