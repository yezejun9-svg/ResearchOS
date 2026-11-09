"""Root-only once launcher. Merely importing this file never launches anything."""
import sys
sys.dont_write_bytecode = True
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
import types

ROOT = Path(r'D:/作品集/ResearchOS/research-os')
DRAFT = ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft'
SCOPE_PATH = DRAFT/'root_finite14_scope.v3.json'
GATE_PATH = DRAFT/'authorization_gate.v3.py'
HELPER_SHA = '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pinned_module(path, expected_sha, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_sha, 'Code SHA: ' + str(path))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def save(root, name, value):
    path = root/name
    raw = (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw)
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def raw_ref(path):
    raw = path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def complete(result):
    if not isinstance(result,dict):
        return False
    cleanup = result.get('job_cleanup',{})
    return (result.get('actual_exit') == 0 and result.get('error') is None and
            result.get('timed_out') is False and result.get('resumed') is True and
            cleanup.get('errors') == [] and all(cleanup.get(k) is True for k in
                ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed',
                 'job_idle_confirmed','handles_closed']))


def runtime_observation(gate, reader, scope, helper):
    # Only called after completed registration has been verified without DLL/native calls.
    paths = {Path(p).absolute() for p in helper.runtime_resource_paths()}
    for module in list(sys.modules.values()):
        for attr in ['__file__','__cached__']:
            p = getattr(module,attr,None)
            if isinstance(p,str) and Path(p).is_file():
                paths.add(Path(p).absolute())
    paths.add(Path(sys.executable).absolute())
    expected = {os.path.normcase(str(Path(x['path']).absolute())):x for x in reader.doc(scope['runtime_resources_ref'])['files']}
    for key in ['launcher_ref','authorization_gate_ref','owned_process_helper_ref']:
        item = scope[key]
        expected[os.path.normcase(str(gate.bounded_path(item['path'])))] = item
    observed = []
    for p in sorted(paths,key=str):
        key = os.path.normcase(str(p))
        require(key in expected,'Runtime file not pre-pinned: '+str(p))
        reader.verify(expected[key],external=not p.is_relative_to(ROOT))
        observed.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    return {'at':now(),'files':observed,'all_observed_inputs_pre_pinned':True,
            'cached_bytecode_included_when_present':True,'loaded_DLLs_actual':True}


def main():
    require(len(sys.argv)==3 and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize and sys.flags.utf8_mode,
            'Usage: pinned Python -I -S -X utf8 launch.v3.py exact-scope-path exact-scope-SHA')
    require(Path(sys.argv[1]).absolute()==SCOPE_PATH,'Wrong scope path')
    # Bootstrap only the pinned gate; it will independently strict-parse the same scope.
    scope_raw = SCOPE_PATH.read_bytes()
    require(hashlib.sha256(scope_raw).hexdigest()==sys.argv[2],'Scope SHA')
    bootstrap = json.loads(scope_raw.decode('utf-8',errors='strict'))
    require(ROOT/bootstrap['authorization_gate_ref']['path']==GATE_PATH,'Gate path')
    gate = pinned_module(GATE_PATH,bootstrap['authorization_gate_ref']['sha256'],'root_authorization_gate')
    reader = gate.Reader()
    scope, scope_ref = gate.load_scope(reader,SCOPE_PATH,sys.argv[2])
    require(gate.bounded_path(scope['launcher_ref']['path'])==Path(__file__).resolve(),'Launcher identity')
    require(scope['launch_limits']['timeout_seconds']==3600,'Launcher timeout scope')
    canonical = [{'canonical_path':p,'ref':reader.ref(ROOT/p)} for p in gate.CANONICAL]
    registration = gate.registration_refs(reader)
    authority = gate.validate_authority(reader,scope,scope_ref,canonical,registration)
    outputs = [gate.bounded_path(scope[k],False) for k in
               ['new_output_root','new_export_root','new_authorization_root']]
    require(all(not os.path.lexists(p) for p in outputs),'Run root already exists; no retry')
    auth = outputs[2]
    require(auth.parent.is_dir(),'Authorization parent must already exist')
    auth.mkdir()  # Sole exclusive once marker. Never removed, even on failure.
    stage = 'COPY_REGISTERED_CANONICAL'
    actual_result = None
    try:
        copies = []
        for entry in canonical:
            raw = reader.verify(entry['ref'])
            target = auth/Path(entry['canonical_path']).name
            with target.open('xb') as stream:
                stream.write(raw)
            copies.append({'canonical_path':entry['canonical_path'],'ref':raw_ref(target)})
        save(auth,'launch.intent.json',{'at':now(),'scope_ref':scope_ref,'binding':gate.binding(scope),
             'registration_refs':registration,'canonical_copies':copies,'automatic_retry':False})
        stage = 'PIN_TOOLCHAIN_AND_RUNTIME'
        lock_ref = reader.ref(ROOT/'execution/toolchains/locked.json')
        tools = reader.doc(lock_ref)['tools']
        for key in ['python','git']:
            tool = tools[key]
            raw = reader.read(tool['path'],external=True)
            require(hashlib.sha256(raw).hexdigest()==tool['sha256'],'Toolchain '+key)
        require(Path(sys.executable).resolve()==Path(tools['python']['path']).resolve(),'Python executable')
        require(scope['owned_process_helper_ref']['sha256']==HELPER_SHA,'Owned process helper pin')
        helper = pinned_module(gate.bounded_path(scope['owned_process_helper_ref']['path']),HELPER_SHA,'root_owned_process')
        runtime_refs = [save(auth,'runtime.before_git.json',runtime_observation(gate,reader,scope,helper))]
        env = {k:v for k,v in os.environ.items() if k.upper() in
               {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
        env.update(PATH='C:/Windows/System32;C:/Windows',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',
                   GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',
                   GIT_CONFIG_GLOBAL=os.devnull)
        git_checks = []
        for kind,args in [('head',['rev-parse','HEAD']),
                          ('status',['status','--porcelain=v1','--untracked-files=no']),
                          ('index',['diff','--cached','--name-only'])]:
            stage = 'GIT_'+kind.upper()
            argv = [tools['git']['path']]+args
            result = None
            wrapper_error = None
            started = now()
            try:
                with (auth/(kind+'.stdout.raw')).open('xb') as so,(auth/(kind+'.stderr.raw')).open('xb') as se:
                    result = helper.run_owned(argv,str(ROOT),env,so,se,60)
            except BaseException as exc:
                wrapper_error = repr(exc)
            finally:
                save(auth,kind+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'environment':env,
                     'started_at':started,'ended_at':now(),'result':result,'wrapper_error':wrapper_error,
                     'actual_exit':result.get('actual_exit') if isinstance(result,dict) else None})
            require(wrapper_error is None and complete(result),'Git preflight failed: '+kind)
            git_checks.append({'kind':kind,'argv':argv,'result':result,
                               'stdout_ref':raw_ref(auth/(kind+'.stdout.raw')),
                               'stderr_ref':raw_ref(auth/(kind+'.stderr.raw'))})
        head = reader.verify(git_checks[0]['stdout_ref']).decode('ascii').strip()
        status = reader.verify(git_checks[1]['stdout_ref'])
        index = reader.verify(git_checks[2]['stdout_ref'])
        require(head==scope['main_git']['head'] and index==b'','HEAD/index changed')
        require(len(status)==scope['main_git']['status_bytes'] and
                hashlib.sha256(status).hexdigest()==scope['main_git']['status_sha256'] and
                len(status.splitlines())==13 and sum(x.startswith(b' D ') for x in status.splitlines())==11,
                'Main status changed')
        stage = 'PRELAUNCH_CAS'
        for entry in canonical:
            require(reader.verify(entry['ref'])==reader.verify(copies[gate.CANONICAL.index(entry['canonical_path'])]['ref']),
                    'Live canonical advanced before launch')
        gate.validate_authority(reader,scope,scope_ref,copies,registration)
        runtime_refs.append(save(auth,'runtime.before_inner.json',runtime_observation(gate,reader,scope,helper)))
        prelaunch = save(auth,'prelaunch.json',{'at':now(),'git':git_checks,'toolchain_lock_ref':lock_ref,
                         'runtime_resources_ref':scope['runtime_resources_ref']})
        stage = 'CREATE_IMMUTABLE_GRANT'
        grant = save(auth,'authorization.execute.json',{
            'schema':'researchos.root-finite14-authorization.v2','status':'ROOT_REGISTERED_EXECUTION_AUTHORIZED',
            'actor':'codex:/root','at':now(),'actual_registration_completed':True,'scope_ref':scope_ref,
            'binding':gate.binding(scope),'registration_refs':registration,'canonical_copies':copies,
            'authority_review_refs':authority,'prelaunch_evidence_ref':prelaunch,
            'runtime_observation_refs':runtime_refs,'source_acceptance':False,'formal_increment':0})
        validated = gate.validate_grant(SCOPE_PATH,scope_ref['sha256'],ROOT/grant['path'],grant['sha256'])
        save(auth,'authorization.inputs.json',validated['authorization_input_refs'])
        require(all(not os.path.lexists(p) for p in outputs[:2]),'OUT/EXPORT raced')
        # Do not create OUT/EXPORT: the inner runner retains exclusive creation.
        stage = 'INNER_ROOT_FINITE14'
        argv = [tools['python']['path']] + scope['python_flags'] + [
                str(gate.bounded_path(scope['runner_ref']['path'])),str(SCOPE_PATH),scope_ref['sha256'],
                str(ROOT/grant['path']),grant['sha256']]
        wrapper_error = None
        started = now()
        try:
            with (auth/'inner.stdout.raw').open('xb') as so,(auth/'inner.stderr.raw').open('xb') as se:
                actual_result = helper.run_owned(argv,str(ROOT),env,so,se,scope['launch_limits']['timeout_seconds'])
        except BaseException as exc:
            wrapper_error = repr(exc)
        finally:
            save(auth,'inner.invocation.json',{'argv':argv,'cwd':str(ROOT),'environment':env,
                 'started_at':started,'ended_at':now(),'result':actual_result,'wrapper_error':wrapper_error,
                 'actual_exit':actual_result.get('actual_exit') if isinstance(actual_result,dict) else None})
        require(wrapper_error is None and complete(actual_result),'Inner finite14 failed or cleanup incomplete')
        stage = 'AFTER_INNER_AUTHORITY_INPUT_CHECK'
        gate.validate_grant(SCOPE_PATH,scope_ref['sha256'],ROOT/grant['path'],grant['sha256'])
        save(auth,'runtime.after_inner.json',runtime_observation(gate,reader,scope,helper))
        save(auth,'completed.json',{'at':now(),'actual_exit':0,'grant_ref':grant,
             'source_acceptance':False,'formal_increment':0,'status':'ROOT_FINITE14_EXECUTION_FINISHED_REVIEW_PENDING'})
        return 0
    except BaseException as exc:
        # Preserve the first actual failure before further diagnostics. Never retry or remove evidence.
        save(auth,'failure.origin.json',{'at':now(),'stage':stage,'error':repr(exc),'traceback':traceback.format_exc(),
             'actual_inner_exit':actual_result.get('actual_exit') if isinstance(actual_result,dict) else None,
             'launcher_exit':1,'automatic_retry':False,'counter_reset':False})
        raise


if __name__ == '__main__':
    sys.exit(main())
