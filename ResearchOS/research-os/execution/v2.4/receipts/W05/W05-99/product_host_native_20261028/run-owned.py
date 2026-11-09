"""Capture one Root-authorized owned lifecycle attempt without timeout or retry."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

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

def main():
    scope_path=Path(sys.argv[1]).resolve()
    scope=json.loads(scope_path.read_text(encoding='utf-8-sig'))
    require(scope['native_launch_authorized'] is True,'NATIVE_LAUNCH_NOT_AUTHORIZED')
    require(scope['independent_source_build_accepted'] is True,'SOURCE_BUILD_NOT_ACCEPTED')
    require(scope['mode']=='OWNED_PRODUCT_HOST_LIFECYCLE_NO_PROVIDER','WRONG_NATIVE_SCOPE')
    root=Path(scope['worktree']).resolve()
    outer=Path(scope['outer_receipts_root']).resolve()
    temporary=Path(scope['outer_temporary_root']).resolve()
    require(temporary.is_relative_to(root/'.local') and not temporary.exists(),'OUTER_TEMP_NOT_FRESH_OWNED')
    require(not outer.exists() and not Path(scope['receipts_root']).exists(),'RECEIPTS_ALREADY_EXIST')
    for row in scope['bound_files']:
        actual=reference(Path(row['path']))
        require(actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'],'BOUND_FILE_CHANGED:'+row['path'])
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
        print(json.dumps({'status':'OWNED_NATIVE_CONTROLLER_LIVE','pid':child.pid}),flush=True)
        code=child.wait()
    write_new(outer/'exit.json',{'exit':code,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'stdout':reference(outer/'stdout.raw'),'stderr':reference(outer/'stderr.raw'),
        'product_acceptance':'NOT_ASSERTED','formal_increment':0})
    print(json.dumps({'status':'OWNED_NATIVE_CONTROLLER_TERMINAL','exit':code}),flush=True)
    return code

if __name__=='__main__':sys.exit(main())
