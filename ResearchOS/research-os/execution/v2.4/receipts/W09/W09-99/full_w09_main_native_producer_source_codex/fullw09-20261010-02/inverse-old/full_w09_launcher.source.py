"""Reserve only this runner's single evidence UUID; Main and stdlib bytes stay exact."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import types
import uuid

N=Path(__file__).resolve().parent
RUNTIME_SHA='49b6aedb3028225445991acc76b0229278bb0257ac2fee75baa2fa538b8d1849'

class OneShotEvidenceUUID:
    __slots__=('_value','_used')
    def __init__(self,run_id):
        object.__setattr__(self,'_value',uuid.UUID(hex=run_id));object.__setattr__(self,'_used',False)
    def __getattribute__(self,name):
        if name!='uuid4':raise ValueError('UUID_ADAPTER_OTHER_ATTRIBUTE_FORBIDDEN')
        return object.__getattribute__(self,name)
    def uuid4(self):
        if object.__getattribute__(self,'_used'):raise ValueError('UUID_ADAPTER_SECOND_CALL_FORBIDDEN')
        object.__setattr__(self,'_used',True)
        return object.__getattribute__(self,'_value')

def main(args):
    if len(args)!=3:raise ValueError('THREE_EXACT_PERMIT_ARGUMENTS')
    runtime_path=N/'full_w09_runtime.source.py';raw=runtime_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=RUNTIME_SHA:raise ValueError('PINNED_RUNTIME_DRIFT')
    m=types.ModuleType('c19_launcher_runtime');m.__file__=str(runtime_path)
    exec(compile(raw,str(runtime_path),'exec'),m.__dict__)
    permit_ref=dict(path=args[0],sha256=args[1],bytes=int(args[2]));permit=m.decode(m.read_ref(permit_ref));c=m.choice(permit['selector'])
    m.require(set(permit)=={'schema','request_ref','selector','run_id','output_root','launcher_ref','runner_ref','environment'},'PERMIT_FIELDS')
    m.require(permit['schema']=='researchos.w09-three-selector-launcher-permit.v1','PERMIT_SCHEMA')
    m.validate_authority(permit['request_ref'],c)
    root=Path(c['receipt_root'])/'producer'
    m.require(permit_ref['path']==str(root/'launcher.permit.json') and permit['launcher_ref']==m.pin(__file__), 'EXACT_LAUNCHER_AND_PERMIT')
    m.require(permit['run_id']==c['run_id'] and permit['output_root']==c['output_root'] and not Path(c['output_root']).exists(),'FIXED_ABSENT_NATIVE_OUTPUT')
    m.require(permit['environment']==m.build_environment(c),'LAUNCHER_EXPLICIT_ENVIRONMENT')
    for name,value in permit['environment'].items():m.require(__import__('os').environ.get(name)==value,'ACTUAL_ENV_'+name)
    runner_ref=next(ref for ref in c['source21'] if ref['path']==str(m.R/'ops/ci/retrieval.py'))
    m.require(permit['runner_ref']==runner_ref,'EXACT_MAIN_RUNNER')
    runner_raw=m.read_ref(runner_ref);tree=ast.parse(runner_raw)
    attrs=[n for n in ast.walk(tree) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='uuid']
    m.require(len(attrs)==1 and attrs[0].attr=='uuid4' and any(isinstance(n,ast.Call) and n.func is attrs[0] and not n.args and not n.keywords for n in ast.walk(tree)),'EXACT_SINGLE_EVIDENCE_UUID_USE')
    m.save(root,'launcher.started.json',dict(permit_ref=permit_ref,launcher_ref=m.pin(__file__),runner_ref=runner_ref,
        fixed_run_id=c['run_id'],fixed_output_root=c['output_root'],source_root=str(m.R),adapter='RUNNER_PRIVATE_UUID_OBJECT_ONLY',
        stdlib_uuid_modified=False,Main_source_modified=False,Source21=c['source21']))
    runner=types.ModuleType('c19_exact_main_retrieval');runner.__file__=runner_ref['path']
    exec(compile(runner_raw,runner_ref['path'],'exec'),runner.__dict__)
    original_uuid=runner.uuid;stdlib_uuid4=uuid.uuid4;provider=OneShotEvidenceUUID(c['run_id'])
    returned=None;error=None;primary=None;cleanup_errors=[]
    try:
        m.require(runner.ROOT==m.R,'RUNNER_ACTUAL_MAIN_ROOT')
        runner.uuid=provider
        returned=runner.main()
        m.require(object.__getattribute__(provider,'_used') is True,'UUID_ADAPTER_NOT_USED')
        m.require(type(returned) is int,'ACTUAL_RUNNER_RETURN_CODE')
    except BaseException as exc:primary=exc;error=repr(exc)
    finally:
        try:runner.uuid=original_uuid
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-uuid-restore',exc)
        try:m.require(uuid.uuid4 is stdlib_uuid4 and runner.uuid is original_uuid,'UUID_MODULE_RESTORED_UNMODIFIED')
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-uuid-observation',exc)
        launcher_ref=None;consumed=None
        try:launcher_ref=m.pin(__file__)
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-source-pin',exc)
        try:consumed=object.__getattribute__(provider,'_used')
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-uuid-consumed',exc)
        observation=dict(permit_ref=permit_ref,runner_ref=runner_ref,launcher_ref=launcher_ref,
            runner_returned_exit=returned,error=error,one_uuid_consumed=consumed,cleanup_errors=cleanup_errors,
            stdlib_uuid_modified=False,Main_source_modified=False,unknown_individual_descendant_exit=None)
        try:m.save(root,'launcher.closed.json',observation)
        except BaseException as exc:m.evidence_error(cleanup_errors,'launcher-closed-save',exc)
    if primary is not None or cleanup_errors:
        raise m.EvidenceFailure('LAUNCHER_FAILED_NO_AUTOMATIC_RETRY',primary,cleanup_errors,observation) from primary
    return returned

if __name__=='__main__':sys.exit(main(sys.argv[1:]))
