"""Root-only future single-use launcher. PREPARATION scope cannot launch.

Root separately registers scope and seals grant/canonical originals. This program
does not create authority, update canonical state, or infer native from outer exit.
"""
import hashlib
import json
import os
import sys
import traceback
import types
from pathlib import Path


def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode) or len(sys.argv)!=5:
        raise RuntimeError('Python -I -S -X utf8 launcher scope scopeSHA grant grantSHA required')
    sys.dont_write_bytecode=True
    scope_path,scope_sha,grant_path,grant_sha=sys.argv[1:]
    raw=Path(scope_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=scope_sha:
        raise RuntimeError('Scope SHA mismatch')
    # Duplicate-safe parsing before any helper/DLL/native call.
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise ValueError('Duplicate key')
            d[k]=v
        return d
    scope=json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=pairs,
                     parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    if scope.get('preparation_only') is not False or scope.get('execution_authorized') is not True:
        raise RuntimeError('PREPARATION_ONLY: actual Root scope/grant missing')
    def module(ref,name):
        b=Path(ref['path']).read_bytes()
        if len(b)!=ref['bytes'] or hashlib.sha256(b).hexdigest()!=ref['sha256']:
            raise RuntimeError('Pinned controller mismatch')
        m=types.ModuleType(name);m.__file__=ref['path'];exec(compile(b,ref['path'],'exec'),m.__dict__);return m
    gate=module(scope['authorization_gate_ref'],'cli43_gate')
    verified=gate.validate_grant(scope_path,scope_sha,grant_path,grant_sha)
    util=module(scope['runner_ref'],'cli43_controller_definitions')
    util.need(util.pin(__file__)==scope['launcher_ref'],'Launcher self pin')
    util.need(Path(sys.executable).resolve()==Path(scope['python_ref']['path']).resolve(),'Actual pinned Python')
    util.verify(scope['python_ref'])
    # Freeze copies inside authority; live canonical checked only at this actual launch boundary.
    for item in verified['grant']['canonical_copies']:
        util.need((util.ROOT/item['canonical_path']).read_bytes()==gate.Reader().verify(item['ref']),
                  'Live registration not equal to authorized original copy')
    out=None;primary=None;secondary=[];result=None;helper=None;stage='CREATE_WRAPPER_LEAF'
    try:
        candidate=util.safe(scope['new_wrapper_root'],util.ROOT/'execution/v2.4/receipts/W05/W05-99',True)
        util.need(candidate.parent.is_dir(),'Root must precreate bounded parent')
        candidate.mkdir();out=candidate
        runtime=util.strict(util.verify(scope['runtime_resources_ref']))
        allowed=runtime['files']+[scope[k] for k in ['runner_ref','launcher_ref','authorization_gate_ref',
                    'owned_process_helper_ref','debug_tree_helper_ref']]
        for r in allowed: util.verify(r)
        stage='IMPORT_OWNED_HELPER_AFTER_PIN'
        helper=module(scope['owned_process_helper_ref'],'cli43_launcher_owned')
        util.save(out/'python-os.before.json',util.module_observation(allowed,helper))
        argv=[scope['python_ref']['path'],'-I','-S','-X','utf8',scope['runner_ref']['path'],
              str(Path(scope_path).absolute()),scope_sha,str(Path(grant_path).absolute()),grant_sha]
        env=dict(scope['public_environment'])
        util.need(set(env).issubset({'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'}),'Nonpublic environment')
        util.need(scope['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,
                  'termination_cleanup_seconds':5},'Fixed finite launch limits')
        util.save(out/'invocation.intent.json',{'argv':argv,'cwd':str(util.ROOT),'environment':env,
                  'timeout_seconds':3600,'automatic_retry':False,'counter_reset':False})
        stage='INNER_PROCESS'
        try:
            with (out/'stdout.raw').open('xb') as stdout,(out/'stderr.raw').open('xb') as stderr:
                result=helper.run_owned(argv,str(util.ROOT),env,stdout,stderr,3600)
        finally:
            util.save(out/'invocation.result.json',{'result':result,'actual_native_exit':result['actual_exit'] if result else None,
                     'actual_outer_tool_exit':None})
        util.job_ok(result)
        stage='CLOSED_INNER_RESULT'
        inner=util.strict((Path(scope['new_output_root'])/'result.json').read_bytes())
        util.need(inner['status']=='BOUNDED_DEVELOPMENT_EVIDENCE_REPORTED' and len(inner['cases'])==2
                  and not inner['NOT_RUN'] and inner['first_cause'] is None,'Inner finite evidence incomplete')
    except BaseException as e:
        primary={'stage':stage,'error':repr(e),'traceback':traceback.format_exc(),
                 'actual_stage_native_exit':None,'last_child_result':result,'automatic_retry':False,'counter_reset':False}
        if out is None: sys.stderr.write(json.dumps(primary,ensure_ascii=False)+'\n')
    finally:
        if out is not None:
            if helper:
                try: util.save(out/'python-os.after.json',util.module_observation(allowed,helper))
                except BaseException as e: secondary.append({'stage':'point-in-time-after','error':repr(e)})
            if primary is None and secondary: primary={'stage':'FINALIZE','error':secondary[0],'actual_stage_native_exit':None}
            try:
                if primary is not None: util.save(out/'failure.origin.json',primary)
                util.save(out/'completed.json',{'program_reported_exit':0 if primary is None else 1,
                         'actual_outer_tool_exit':None,'actual_inner_native_exit':result['actual_exit'] if result else None,
                         'first_cause':primary,'secondary':secondary,'source_acceptance':False,'formal_increment':0})
                rows=[util.pin(p) for p in util.files(out)]
                util.save(out/'manifest.json',{'files':rows,'count':len(rows),'excluded_only_self':True})
            except BaseException as e:
                secondary.append({'stage':'FINAL_RECEIPT_WRITE','error':repr(e)})
                primary=primary or {'stage':'FINAL_RECEIPT_WRITE','error':repr(e),'actual_native_exit':None}
                sys.stderr.write(json.dumps({'first_cause':primary,'secondary':secondary,
                    'partial_wrapper_manifest_not_success':True,'actual_native_exit':None},ensure_ascii=False)+'\n')
    return 0 if primary is None else 1


if __name__=='__main__':
    try:
        exit_code=main()
    except BaseException as exc:
        # Prior to a validated safe owned leaf, Root's caller must retain original stderr.
        sys.stderr.write(json.dumps({'stage':'PRE_OWNED_LEAF_OR_UNHANDLED_FINALIZE',
            'error':repr(exc),'traceback':traceback.format_exc(),'actual_native_exit':None,
            'local_origin_available':False,'outer_raw_stderr_is_authority':True,
            'automatic_retry':False,'counter_reset':False},ensure_ascii=False)+'\n')
        exit_code=1
    raise SystemExit(exit_code)
