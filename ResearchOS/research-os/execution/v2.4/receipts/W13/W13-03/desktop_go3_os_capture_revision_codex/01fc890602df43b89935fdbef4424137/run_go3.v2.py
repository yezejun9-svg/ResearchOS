"""Receipt-only proposal. Root grant required; no code runs on import."""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
import traceback
import types

HERE = Path(__file__).resolve().parent
OUT = HERE/'actual-once'
FLAGS = ['-I', '-S', '-X', 'utf8']


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def strict(raw):
    def pairs(items):
        obj = {}
        for key,value in items:
            require(key not in obj,'Duplicate JSON key '+key)
            obj[key] = value
        return obj
    def bad(value):
        raise ValueError('Nonfinite JSON '+value)
    return json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=pairs,parse_constant=bad)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def no_alias(p):
    p = Path(p)
    require(p.is_absolute() and '..' not in p.parts,'Absolute exact path required')
    require(p.resolve()==p.absolute(),'Alias path')
    for q in [p]+list(p.parents):
        if os.path.lexists(q):
            st=os.lstat(q)
            require(not q.is_symlink() and not getattr(st,'st_file_attributes',0)&0x400,'Reparse path')
    return p


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(name, value):
    raw=(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode('utf-8')
    p=OUT/name
    with p.open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return {'path':str(p),'sha256':sha(raw),'bytes':len(raw)}


class Inputs:
    def __init__(self):
        self.refs={}
    def read(self, ref):
        p=no_alias(ref['path'])
        raw=p.read_bytes()
        actual={'path':str(p),'sha256':sha(raw),'bytes':len(raw)}
        require(actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'],'Input mismatch '+str(p))
        prior=self.refs.get(str(p))
        require(prior is None or prior==actual,'Input changed during read '+str(p))
        self.refs[str(p)]=actual
        return raw
    def doc(self, ref):
        return strict(self.read(ref))
    def observe(self, p):
        p=no_alias(p);raw=p.read_bytes()
        ref={'path':str(p),'sha256':sha(raw),'bytes':len(raw)}
        self.read(ref)
        return ref
    def after(self):
        facts=[]
        for expected in self.refs.values():
            fact={'expected':expected,'actual':None,'error':None,'match':False}
            try:
                raw=no_alias(expected['path']).read_bytes()
                fact['actual']={'path':expected['path'],'sha256':sha(raw),'bytes':len(raw)}
                fact['match']=fact['actual']==expected
            except BaseException as exc:
                fact['error']=repr(exc)
            facts.append(fact)
        return facts


def module_from_bytes(inputs, reference, name):
    raw=inputs.read(reference)
    module=types.ModuleType(name)
    module.__file__=reference['path']
    exec(compile(raw,reference['path'],'exec'),module.__dict__)
    return module


def complete(result):
    if not isinstance(result,dict):return False
    c=result.get('job_cleanup',{})
    return (result.get('actual_exit')==0 and result.get('error') is None and
        result.get('timed_out') is False and result.get('resumed') is True and
        c.get('errors')==[] and all(c.get(k) is True for k in
        ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume',
         'primary_exit_confirmed','job_idle_confirmed','handles_closed']))


def runtime_inventory(inputs, spec, helper):
    catalog=inputs.doc(spec['runtime_catalog_ref'])
    approved={os.path.normcase(str(Path(x['path']).absolute())):x for x in catalog['files']}
    for key in ['runner_ref','debug_helper_ref','outer_helper_ref']:
        x=spec[key];approved[os.path.normcase(str(Path(x['path']).absolute()))]=x
    paths={Path(sys.executable).absolute()}
    for module in list(sys.modules.values()):
        for attr in ['__file__','__cached__']:
            p=getattr(module,attr,None)
            if isinstance(p,str) and Path(p).is_file():paths.add(Path(p).absolute())
    paths.update(Path(p).absolute() for p in helper.runtime_resource_paths())
    rows=[]
    for p in sorted(paths,key=str):
        require('site-packages' not in [x.lower() for x in p.parts],'Unapproved site startup')
        k=os.path.normcase(str(p))
        require(k in approved,'Unpinned actual Python/OS runtime '+str(p))
        inputs.read(approved[k]);rows.append(approved[k])
    return {'files':rows,'at':now(),'measurement':'POINT_IN_TIME_NOT_LIFECYCLE','transient_load_absence_proven':False}


def environment():
    env={k:v for k,v in os.environ.items() if k.upper() in
         {'SYSTEMROOT','WINDIR','SYSTEMDRIVE','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
    env.update(PATH='C:/Windows/System32;C:/Windows',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',
               GOTOOLCHAIN='local',GOENV='off')
    return env


def main():
    inner='--inner' in sys.argv[1:]
    # No existing execution directory is ever reused by another outer launch.
    no_alias(HERE)
    if not inner:
        OUT.mkdir(exist_ok=False)
    else:
        require(OUT.is_dir(),'Owned outer output absent')
        no_alias(OUT)
    phase='inner' if inner else 'outer'
    # A repeated phase cannot append to or overwrite the original failed phase.
    put(phase+'.started.json',{'at':now(),'actual_argv':sys.argv,'once':True})
    inputs=Inputs();first_failure=None;result=None;spec=None;helper=None
    stage='PARSE_AND_PIN';before_runtime=None;after_runtime=None;diagnostics=[]
    stdout=OUT/(phase+'.stdout.raw');stderr=OUT/(phase+'.stderr.raw')
    try:
        require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and
                not sys.flags.optimize and sys.dont_write_bytecode,'Require pinned Python -I -S -X utf8')
        parser=argparse.ArgumentParser()
        parser.add_argument('--grant-path',required=True)
        parser.add_argument('--grant-sha256',required=True)
        parser.add_argument('--inner',action='store_true')
        args=parser.parse_args()
        gp=no_alias(args.grant_path);gb=gp.read_bytes()
        require(sha(gb)==args.grant_sha256,'Grant SHA')
        grant=inputs.doc({'path':str(gp),'sha256':args.grant_sha256,'bytes':len(gb)})
        require(grant['authorized'] is True and grant['issuer']=='codex:/root' and
                grant['operation']=='GO3_SINGLE_DEBUG_EVENT_COMPONENT_EVIDENCE_V2' and
                grant['max_executions']==1,'Future Root one-run grant required')
        spec=inputs.doc(grant['spec_ref'])
        require(no_alias(grant['spec_ref']['path'])==HERE/'spec.v2.json','Exact spec path')
        for key in ['runner_ref','debug_helper_ref','outer_helper_ref','python_ref','runtime_catalog_ref']:
            require(grant[key]==spec[key],'Grant binding '+key);inputs.read(spec[key])
        require(no_alias(spec['runner_ref']['path'])==Path(__file__).resolve(),'Actual controller identity')
        require(no_alias(spec['python_ref']['path'])==Path(sys.executable).resolve(),'Actual pinned Python')
        require(spec['python_flags']==FLAGS and grant['python_flags']==FLAGS,'Flags binding')
        require(grant['source_commit']==spec['source_commit'] and grant['test_exe']==spec['test_exe'] and
                grant['selectors']==spec['selectors'] and grant['caps']==spec['caps'],'Exact source/roster/caps')
        require(spec['caps']['http']==0 and spec['caps']['sdk_model']==0 and spec['caps']['test_processes']==1,
                'Pure Go caps')
        require(grant['new_output_root']==str(OUT) and spec['new_output_root']==str(OUT),'Fresh output binding')
        # Read current compiled sources, generated WORK and archives before any native child.
        vector=inputs.doc(spec['input_vector_ref'])
        require(len(vector)==8577,'Original compiled input count')
        for row in vector:inputs.read(row)
        for ref in spec['compiled_evidence_refs']:inputs.read(ref)
        inputs.read(spec['test_exe'])
        for ref in grant['authority_refs']:inputs.read(ref)
        stage='LOAD_PINNED_PUBLIC_HELPER'
        key='debug_helper_ref' if inner else 'outer_helper_ref'
        helper=module_from_bytes(inputs,spec[key],phase+'_exact_owned_helper')
        before_runtime=runtime_inventory(inputs,spec,helper)
        put(phase+'.runtime.before.json',before_runtime)
        put(phase+'.inputs.before.json',list(inputs.refs.values()))
        if inner:
            argv=[spec['test_exe']['path'],'-test.run',spec['anchored_selector'],'-test.v',
                  '-test.count=1','-test.failfast','-test.timeout=120s']
            timeout=150
        else:
            argv=[spec['python_ref']['path']]+FLAGS+[str(Path(__file__).resolve()),'--inner',
                  '--grant-path',str(gp),'--grant-sha256',args.grant_sha256]
            timeout=600
        env=environment()
        stage='OWNED_CHILD_RUN'
        put(phase+'.invocation.json',{'at':now(),'argv':argv,'cwd':spec['cwd'],'environment':env,
             'timeout_seconds':timeout,'actual_exit':None,'result_record':phase+'.owned-result.json'})
        try:
            with stdout.open('xb') as so,stderr.open('xb') as se:
                if inner:
                    expected={'sha256':spec['test_exe']['sha256'],'bytes':spec['test_exe']['bytes']}
                    result=helper.run_owned(argv,spec['cwd'],env,so,se,timeout,expected_image=expected)
                else:
                    result=helper.run_owned(argv,spec['cwd'],env,so,se,timeout)
        finally:
            put(phase+'.owned-result.json',{'result':result,'actual_native_exit':result.get('actual_exit') if isinstance(result,dict) else None,
                'stdout_closed':locals().get('so') is None or so.closed,'stderr_closed':locals().get('se') is None or se.closed,
                'stdio':'EXPLICIT_FILE_HANDLES_NOT_PIPES'})
        require(complete(result),'Native result or owned-Job cleanup incomplete')
        if inner:
            d=result['debug_capture']
            require(d['complete'] and d['create_process_count']==1 and d['exit_process_count']==1 and
                    d['total_processes_last_observed']==1 and d['exit_event_code']==result['actual_exit'],
                    'Primary process debug capture incomplete')
            raw=stdout.read_bytes();text=raw.decode('utf-8',errors='strict')
            passes=re.findall(r'^\s*--- PASS: ([^ ]+)',text,re.MULTILINE)
            failures=re.findall(r'^\s*--- (?:FAIL|SKIP): ([^ ]+)',text,re.MULTILINE)
            put('inner.test-events.json',{'passes':passes,'failure_or_skip':failures,'stdout_sha256':sha(raw)})
            require(sorted(passes)==sorted(spec['expected_pass_records']) and not failures,'Exact64 PASS records required')
        else:
            child=strict((OUT/'inner.summary.json').read_bytes())
            require(child['status']=='COMPONENT_EVIDENCE_RECORDED' and child['first_failure'] is None,
                    'Inner component has not closed')
        stage='POST_EXECUTION_CLOSURE'
    except BaseException as exc:
        first_failure={'stage':stage,'error':repr(exc),'traceback':traceback.format_exc(),'at':now(),
            'actual_native_exit':result.get('actual_exit') if isinstance(result,dict) else None,
            'controller_exit':1,'automatic_retry':False,'counter_reset':False}
        # Save the original cause BEFORE any best-effort diagnostics.
        try:put(phase+'.failure.origin.json',first_failure)
        except BaseException as save_error:
            diagnostics.append({'stage':'SAVE_FIRST_FAILURE','error':repr(save_error)})
            print(json.dumps({'first_failure':first_failure,'save_error':repr(save_error)}),file=sys.stderr,flush=True)
    finally:
        if spec is not None and helper is not None:
            try:
                after_runtime=runtime_inventory(inputs,spec,helper)
                put(phase+'.runtime.after.json',after_runtime)
                if before_runtime is not None:
                    before_keys={x['path'] for x in before_runtime['files']}
                    extra=[x['path'] for x in after_runtime['files'] if x['path'] not in before_keys]
                    if extra:diagnostics.append({'stage':'RUNTIME_AFTER','new_paths':extra})
            except BaseException as exc:diagnostics.append({'stage':'RUNTIME_AFTER','error':repr(exc)})
        after=inputs.after()
        if any(not x['match'] for x in after):diagnostics.append({'stage':'INPUT_DRIFT','drift_count':sum(not x['match'] for x in after)})
        try:put(phase+'.inputs.after.json',after)
        except BaseException as exc:diagnostics.append({'stage':'SAVE_AFTER','error':repr(exc)})
        if first_failure is None and diagnostics:
            first_failure={'stage':'FINALIZE_EVIDENCE','error':diagnostics[0],'at':now(),
                'actual_native_exit':result.get('actual_exit') if isinstance(result,dict) else None,
                'controller_exit':1,'automatic_retry':False,'counter_reset':False}
            try:put(phase+'.failure.origin.json',first_failure)
            except BaseException as exc:print(repr(exc),file=sys.stderr,flush=True)
        summary={'status':'COMPONENT_EVIDENCE_RECORDED' if first_failure is None else 'FAILED_OR_INCOMPLETE_COMPONENT_EVIDENCE',
            'phase':phase,'at':now(),'first_failure':first_failure,'diagnostics':diagnostics,
            'actual_native_exit':result.get('actual_exit') if isinstance(result,dict) else None,
            'source_acceptance':False,'formal_increment':0,'Python_lifecycle_capture':False,
            'Go_condition':'DEBUG_ONLY_THIS_PROCESS, new observation not historical normal PASS'}
        try:put(phase+'.summary.json',summary)
        except BaseException as exc:
            print(json.dumps({'summary':summary,'save_error':repr(exc)}),file=sys.stderr,flush=True)
            first_failure=first_failure or {'stage':'SAVE_SUMMARY','error':repr(exc)}
        try:
            refs=[]
            for p in sorted(OUT.iterdir()):
                if p.is_file() and p.name != phase+'.manifest.json':
                    raw=p.read_bytes();refs.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw)})
            put(phase+'.manifest.json',{'entries':refs,'self_excluded':True})
        except BaseException as exc:
            print(repr(exc),file=sys.stderr,flush=True)
            first_failure=first_failure or {'stage':'SAVE_MANIFEST','error':repr(exc)}
    return 0 if first_failure is None else 1


if __name__=='__main__':
    raise SystemExit(main())
