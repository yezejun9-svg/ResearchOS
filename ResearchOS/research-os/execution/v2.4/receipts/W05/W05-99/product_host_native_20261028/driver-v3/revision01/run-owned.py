"""Capture one owned lifecycle attempt and hold a failed controller for Root reconciliation."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time

SCAN_SCRIPT=r'''
$ErrorActionPreference='Stop'
$names = @(ConvertFrom-Json -InputObject $env:ROS_SCAN_NAMES_JSON)
$knownPids = @(ConvertFrom-Json -InputObject $env:ROS_SCAN_KNOWN_PIDS_JSON)
$rows = foreach ($item in @(Get-CimInstance Win32_Process)) {
    if ($names -notcontains [string]$item.Name -and $knownPids -notcontains [int]$item.ProcessId) { continue }
    $createdNS = $null
    $readError = $null
    try {
        $native = Get-Process -Id $item.ProcessId -ErrorAction Stop
        $createdNS = [long](($native.StartTime.ToUniversalTime().Ticks - [long]621355968000000000) * [long]100)
    } catch { $readError = [string]$_.Exception.Message }
    [pscustomobject]@{ pid=[int]$item.ProcessId; image=[string]$item.ExecutablePath;
        created_ns=if($null -ne $createdNS){$createdNS.ToString()}else{$null};
        creation=[string]$item.CreationDate; read_error=$readError }
}
ConvertTo-Json -InputObject @($rows) -Depth 4 -Compress
'''

def reference(p):
    b=p.read_bytes()
    return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def write_new(p,value):
    with p.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n')

def require(condition,message):
    if not condition:
        raise RuntimeError(message)

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def normpath(value):
    return os.path.normcase(os.path.normpath(os.path.abspath(str(value)))).casefold()

def product_images(scope):
    bundle=Path(scope['bundle_root']).resolve()
    marker=json.loads((bundle/'installed-product.json').read_text(encoding='utf-8-sig'))
    require(marker['installation_id']==scope['installation_id'] and
            normpath(marker['install_root'])==normpath(bundle),'BUNDLE_MARKER_MISMATCH')
    paths={}
    for row in marker['files']:
        if not str(row['path']).casefold().endswith('.exe'):
            continue
        image=(bundle/row['path']).resolve()
        require(image.is_relative_to(bundle),'BUNDLE_IMAGE_OUTSIDE_ROOT')
        paths[normpath(image)]=str(image)
    for key in ('cli','control','electron'):
        image=(bundle/marker['binaries'][key]['path']).resolve()
        require(normpath(image) in paths,'BUNDLE_BINARY_NOT_IN_INVENTORY:'+key)
    return paths,marker

def known_identities(unresolved_path,scope,images,marker):
    data=json.loads(unresolved_path.read_text(encoding='utf-8-sig'))
    require(data['status']=='FAILED_OR_UNRESOLVED_PRESERVE_OWNED_STATE','BAD_CONTROLLER_UNRESOLVED')
    known={}
    def add(pid,image,created_ns=None):
        require(type(pid) is int and pid>0 and normpath(image) in images,'BAD_KNOWN_PRODUCT_IDENTITY')
        require(created_ns is None or (isinstance(created_ns,str) and created_ns.isdecimal()),
                'BAD_KNOWN_PRODUCT_CREATION')
        key=(pid,normpath(image))
        prior=known.get(key)
        require(prior is None or not prior['created_ns'] or not created_ns or
                prior['created_ns']==created_ns,'CONFLICTING_KNOWN_CREATION')
        known[key]={'pid':pid,'image':images[key[1]],
                    'created_ns':created_ns or (prior['created_ns'] if prior else None)}
    for child in data.get('children',[]):
        if child.get('terminal') is False and normpath(child.get('executable','')) in images:
            add(child['pid'],child['executable'])
    for key in ('first_witness','second_witness','third_witness','current_witness'):
        witness=data.get(key)
        if witness is None:
            continue
        require(isinstance(witness,dict) and not witness.get('read_error') and
                normpath(witness['install_root'])==normpath(scope['bundle_root']) and
                witness['installation_id']==marker['installation_id'],'BAD_KNOWN_WITNESS')
        for role in ('parent_process','control_process'):
            row=witness[role]
            image=(Path(scope['bundle_root'])/marker['binaries']['electron' if role=='parent_process' else 'control']['path']).resolve()
            add(row['PID'],image,row['CreatedNS'])
    return sorted(known.values(),key=lambda row:(row['pid'],normpath(row['image'])))

def scan_product_images(scope,images,root,known):
    env={key:value for key,value in os.environ.items() if key.upper() in {
        'SYSTEMROOT','WINDIR','COMSPEC','OS','PATHEXT','PATH'}}
    env['ROS_SCAN_NAMES_JSON']=json.dumps(sorted({Path(value).name for value in images.values()}))
    env['ROS_SCAN_KNOWN_PIDS_JSON']=json.dumps(sorted({row['pid'] for row in known}))
    try:
        result=subprocess.run([scope['powershell_path'],'-NoProfile','-NonInteractive','-Command',SCAN_SCRIPT],
            cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',errors='strict',
            creationflags=subprocess.CREATE_NO_WINDOW)
        require(result.returncode==0,'PROCESS_SCAN_FAILED:'+result.stderr[-1000:])
        rows=json.loads(result.stdout.lstrip('\ufeff'))
        require(isinstance(rows,list),'PROCESS_SCAN_NOT_ARRAY')
        for row in rows:
            require(type(row.get('pid')) is int and row['pid']>0,'PROCESS_SCAN_BAD_PID')
        return {'at':utc_now(),'status':'OBSERVED','rows':rows}
    except (Exception,KeyboardInterrupt) as error:
        return {'at':utc_now(),'status':'UNKNOWN','error':str(error)}

def blockers(observation,known,images):
    if observation['status']!='OBSERVED':
        return ['SCAN_UNKNOWN']
    result=[]
    known_pids={row['pid']:row for row in known}
    for row in observation['rows']:
        pid=row['pid']
        if pid in known_pids:
            expected=known_pids[pid]
            if (row.get('image') and normpath(row['image'])==normpath(expected['image']) and
                    (expected['created_ns'] is None or row.get('created_ns')==expected['created_ns'])):
                result.append('KNOWN_PRODUCT_IDENTITY_STILL_PRESENT:'+str(pid))
            else:
                result.append('KNOWN_PID_REUSED_OR_IDENTITY_UNKNOWN:'+str(pid))
        if not row.get('image') or row.get('read_error'):
            result.append('CANDIDATE_PROCESS_IDENTITY_UNKNOWN:'+str(pid))
        elif normpath(row['image']) in images:
            result.append('EXACT_BUNDLE_IMAGE_STILL_RUNNING:'+str(pid))
    return sorted(set(result))

def append_observation(path,value):
    with path.open('a',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False)
        stream.write('\n')

def safe_print(value):
    try:
        print(json.dumps(value),flush=True)
    except OSError:
        pass

def write_or_verify(path,value):
    if path.exists():
        require(json.loads(path.read_text(encoding='utf-8-sig'))==value,
                'EXISTING_EVIDENCE_MISMATCH:'+str(path))
    else:
        write_new(path,value)

def validate_release(release_path,waiting,known):
    require(waiting['known_identity_error'] is None,'KNOWN_IDENTITIES_UNRESOLVED')
    require(not waiting['release_preexisted_wait'],'ROOT_RELEASE_PREEXISTED_WAIT')
    raw=release_path.read_bytes()
    value=json.loads(raw.decode('utf-8-sig'))
    expected_keys={'schema','scope_sha256','outer_pid','controller_pid','controller_exit_sha256',
                   'release_nonce','known_product_identities','root_confirmed_identity_absence','confirmed_absent_at'}
    require(set(value)==expected_keys,'ROOT_RELEASE_FIELDS_MISMATCH')
    for key in ('scope_sha256','outer_pid','controller_pid','controller_exit_sha256','release_nonce'):
        require(value[key]==waiting[key],'ROOT_RELEASE_BINDING_MISMATCH:'+key)
    require(value['schema']=='researchos.native-driver-v3-root-release.v1' and
            value['known_product_identities']==known and
            value['root_confirmed_identity_absence'] is True,'ROOT_RELEASE_IDENTITY_MISMATCH')
    confirmed=datetime.datetime.fromisoformat(value['confirmed_absent_at'].replace('Z','+00:00'))
    ended=datetime.datetime.fromisoformat(waiting['controller_ended_at'])
    require(confirmed.tzinfo is not None and confirmed>=ended,'ROOT_RELEASE_PREMATURE')
    return hashlib.sha256(raw).hexdigest()

def wait_for_root_release(scope,root,outer,controller_pid,code,ended_at,scope_sha,images,marker):
    exit_sha=reference(outer/'exit.json')['sha256']
    known_error=None
    try:
        known=known_identities(Path(scope['receipts_root'])/'UNRESOLVED.json',scope,images,marker)
    except Exception as error:
        known=[]
        known_error=str(error)
    release_path=outer/'ROOT-RELEASE.json'
    waiting_path=outer/'WAITING_FOR_ROOT_RECONCILIATION.json'
    if waiting_path.exists():
        waiting=json.loads(waiting_path.read_text(encoding='utf-8-sig'))
        for key,value in {'status':'WAITING_FOR_ROOT_RECONCILIATION','controller_ended_at':ended_at,
                'controller_exit':code,'controller_pid':controller_pid,'outer_pid':os.getpid(),
                'scope_sha256':scope_sha,'controller_exit_sha256':exit_sha,
                'release_path':str(release_path),'known_product_identities':known,
                'known_identity_error':known_error,'bundle_images':sorted(images.values())}.items():
            require(waiting.get(key)==value,'EXISTING_WAITING_EVIDENCE_MISMATCH:'+key)
    else:
        waiting={'status':'WAITING_FOR_ROOT_RECONCILIATION','at':utc_now(),
                 'controller_ended_at':ended_at,'controller_exit':code,'controller_pid':controller_pid,
                 'outer_pid':os.getpid(),'scope_sha256':scope_sha,'controller_exit_sha256':exit_sha,
                 'release_nonce':secrets.token_hex(16),'release_path':str(release_path),
                 'known_product_identities':known,'known_identity_error':known_error,
                 'bundle_images':sorted(images.values()),'release_preexisted_wait':release_path.exists(),
                 'termination_mechanism':'NOT_OBSERVED','automatic_shutdown':False,'forced_termination':False}
        write_new(waiting_path,waiting)
    safe_print({'status':'WAITING_FOR_ROOT_RECONCILIATION','outer_pid':os.getpid(),
        'release_path':str(release_path)})
    observations=outer/'reconciliation-observations.jsonl'
    initial=scan_product_images(scope,images,root,known)
    initial['blockers']=blockers(initial,known,images)
    initial['phase']='controller_terminal'
    append_observation(observations,initial)
    prior_release_sha=None
    clean_scans=0
    last_report=None
    while True:
        if release_path.exists():
            try:
                release_sha=validate_release(release_path,waiting,known)
                observation=scan_product_images(scope,images,root,known)
                observation['blockers']=blockers(observation,known,images)
                observation['release_sha256']=release_sha
                observation['phase']='release_check'
                if observation['blockers']:
                    clean_scans=0
                else:
                    clean_scans=clean_scans+1 if release_sha==prior_release_sha else 1
                prior_release_sha=release_sha
                observation['consecutive_clean_scans']=clean_scans
                if observation['blockers']!=last_report or clean_scans>0:
                    append_observation(observations,observation)
                    last_report=observation['blockers']
                if clean_scans>=2:
                    write_new(outer/'ROOT-RELEASED.json',{'status':'ROOT_RECONCILIATION_RELEASED',
                        'at':utc_now(),'release_sha256':release_sha,'scope_sha256':scope_sha,
                        'outer_pid':os.getpid(),'controller_exit':code,
                        'consecutive_clean_scans':clean_scans,'last_observation':observation,
                        'termination_mechanism':'NOT_OBSERVED','product_acceptance':'NOT_ASSERTED'})
                    safe_print({'status':'ROOT_RECONCILIATION_RELEASED','controller_exit':code})
                    return code
            except (Exception,KeyboardInterrupt) as error:
                clean_scans=0
                reason='ROOT_RELEASE_UNRESOLVED:'+str(error)
                if reason!=last_report:
                    append_observation(observations,{'at':utc_now(),'phase':'release_check',
                        'status':'UNKNOWN','reason':reason})
                    last_report=reason
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            append_observation(observations,{'at':utc_now(),'phase':'waiting',
                'status':'INTERRUPT_IGNORED_PENDING_ROOT_RELEASE'})

def hold_failed_controller(scope,root,outer,controller_pid,code,ended_at,scope_sha,images,marker):
    while True:
        try:
            write_or_verify(outer/'exit.json',{'exit':code,'ended_at':ended_at,
                'stdout':reference(outer/'stdout.raw'),'stderr':reference(outer/'stderr.raw'),
                'product_acceptance':'NOT_ASSERTED','formal_increment':0})
            safe_print({'status':'OWNED_NATIVE_CONTROLLER_TERMINAL','exit':code})
            return wait_for_root_release(scope,root,outer,controller_pid,code,ended_at,
                scope_sha,images,marker)
        except (Exception,KeyboardInterrupt) as error:
            try:
                append_observation(outer/'wrapper-hold-errors.jsonl',{'at':utc_now(),
                    'status':'WAITING_FOR_ROOT_RECONCILIATION','error':str(error),
                    'controller_pid':controller_pid,'controller_exit':code})
            except OSError:
                pass
            safe_print({'status':'WAITING_FOR_ROOT_RECONCILIATION','error':str(error)})
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                pass

def main():
    scope_path=Path(sys.argv[1]).resolve()
    scope=json.loads(scope_path.read_text(encoding='utf-8-sig'))
    scope_sha=reference(scope_path)['sha256']
    require(scope['native_launch_authorized'] is True,'NATIVE_LAUNCH_NOT_AUTHORIZED')
    require(scope['independent_source_build_accepted'] is True,'SOURCE_BUILD_NOT_ACCEPTED')
    require(scope['mode']=='OWNED_PRODUCT_HOST_LIFECYCLE_NO_PROVIDER','WRONG_NATIVE_SCOPE')
    root=Path(scope['worktree']).resolve()
    outer=Path(scope['outer_receipts_root']).resolve()
    temporary=Path(scope['outer_temporary_root']).resolve()
    require(temporary.is_relative_to(root/'.local') and not temporary.exists(),'OUTER_TEMP_NOT_FRESH_OWNED')
    require(not outer.exists() and not Path(scope['receipts_root']).exists(),'RECEIPTS_ALREADY_EXIST')
    bound_paths={str(Path(row['path']).resolve()).casefold() for row in scope['bound_files']}
    for name in ('run-owned.py','lifecycle.mjs','choose-owned-folder.ps1','close-owned-window.ps1'):
        require(str(Path(__file__).with_name(name).resolve()).casefold() in bound_paths,
                'V3_DRIVER_NOT_BOUND:'+name)
    for row in scope['bound_files']:
        actual=reference(Path(row['path']))
        require(actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],'BOUND_FILE_CHANGED:'+row['path'])
    images,marker=product_images(scope)
    outer.mkdir();temporary.mkdir()
    env={key:value for key,value in os.environ.items() if key.upper() in {
        'SYSTEMROOT','WINDIR','COMSPEC','OS','PATHEXT','PATH'}}
    env.update(TEMP=str(temporary),TMP=str(temporary))
    argv=[scope['node_path'],str(Path(__file__).with_name('lifecycle.mjs')),str(scope_path)]
    write_new(outer/'invocation.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'argv':argv,'cwd':str(root),'scope':reference(scope_path),'environment':env,
        'wrapper':reference(Path(__file__)),'automatic_retry':False,'automatic_termination':False})
    with (outer/'stdout.raw').open('xb') as stdout,(outer/'stderr.raw').open('xb') as stderr:
        child=subprocess.Popen(argv,cwd=root,env=env,stdout=stdout,stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW)
        write_new(outer/'spawn.json',{'pid':child.pid,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'executable':argv[0],'argv':argv,'parent_pid':os.getpid()})
        safe_print({'status':'OWNED_NATIVE_CONTROLLER_LIVE','pid':child.pid})
        code=child.wait()
        ended_at=utc_now()
    if code==0:
        write_new(outer/'exit.json',{'exit':code,'ended_at':ended_at,
            'stdout':reference(outer/'stdout.raw'),'stderr':reference(outer/'stderr.raw'),
            'product_acceptance':'NOT_ASSERTED','formal_increment':0})
        safe_print({'status':'OWNED_NATIVE_CONTROLLER_TERMINAL','exit':code})
        return 0
    try:
        signal.signal(signal.SIGINT,signal.SIG_IGN)
        if hasattr(signal,'SIGBREAK'):
            signal.signal(signal.SIGBREAK,signal.SIG_IGN)
    except Exception as error:
        safe_print({'status':'WAITING_FOR_ROOT_RECONCILIATION','signal_guard_error':str(error)})
    return hold_failed_controller(scope,root,outer,child.pid,code,ended_at,scope_sha,images,marker)

if __name__=='__main__':sys.exit(main())
