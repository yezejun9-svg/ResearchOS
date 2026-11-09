"""Explicit one-shot FIXTURE collection; direct readers never call this program."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from evidence_module import digest, enrolled_sources, reference, save_new, strict_json
import parent_driver as driver

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
ASSIGNMENT_SHA256 = '97b28880a7bc6f034b83ee5db199d563a3cc47f8d9a743d85651f7dc8f96535d'
PACKAGE_MANIFEST_SHA256 = '4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
LEGACY_REGISTRY_SHA256 = '04eea86be4c832e3d20f343c2ade2e020c210581a7a4ec561954c5ccdba1cb49'


def assigned_actors(path, executor, verifier, root):
    ids = (executor, verifier, root)
    if any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in ids) or len({x.casefold() for x in ids}) != 3:
        raise ValueError('three distinct nonempty actual actors required')
    if digest(path) != ASSIGNMENT_SHA256:
        raise ValueError('Root actor assignment changed')
    assignment = read(path)
    if assignment.get('schema') != 'researchos.w04.revalidation-actor-assignment.v1' or assignment.get('assigned_by') != root:
        raise ValueError('invalid Root actor assignment')
    if (assignment.get('executor_id'), assignment.get('reviewer_id'), assignment.get('root_id')) != ids:
        raise ValueError('actual actors differ from Root assignment')
    if assignment.get('executor_namespace') != HERE.relative_to(ROOT).as_posix()+'/' or HERE.name != 'executor_revalidation_codex':
        raise ValueError('assignment namespace differs')
    return assignment


def package_inventory(package):
    manifest = package/'PACKAGE_MANIFEST.json'
    if digest(manifest) != PACKAGE_MANIFEST_SHA256:
        raise ValueError('frozen package manifest changed')
    entries = read(manifest)['files']
    expected = {row['path']: row['sha256'] for row in entries}
    if len(entries) != 147 or len(expected) != 147:
        raise ValueError('exact 147 manifest entries required')
    expected['PACKAGE_MANIFEST.json'] = PACKAGE_MANIFEST_SHA256
    actual = {}
    for p in package.rglob('*'):
        if p.is_symlink() or p.is_junction(): raise ValueError('package links forbidden')
        if p.is_file() and '__pycache__' not in p.parts:
            actual[p.relative_to(package).as_posix()] = digest(p)
    if actual != expected: raise ValueError('frozen package differs')
    return actual


def new_run():
    run = HERE/'runs'/uuid.uuid4().hex
    run.mkdir(parents=True, exist_ok=False)
    return run

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    save_new(path,value)
    return reference(ROOT,path)

def read(path): return strict_json(path.read_bytes())

def prepare(package):
    original = package_inventory(package)
    target=HERE/'frozen_inputs'/'package'
    if not target.exists(): shutil.copytree(package,target)
    # Every immutable package byte is retained, including its actual validator.
    copied=package_inventory(target)
    if original!=copied: raise ValueError('frozen package differs')
    snapshot=HERE/'frozen_inputs'/'commands-v24-r37.json'
    if digest(snapshot)!=LEGACY_REGISTRY_SHA256: raise ValueError('historical r37 bytes changed')
    registry=read(snapshot)
    if registry['revision']!=37: raise ValueError('wrong pre-W04 registry snapshot')
    entries={k:registry['commands'][k] for k in ('test.context','test.domain')}
    decoded=HERE/'frozen_inputs'/'legacy_entries.json'
    if read(decoded)!={'registry_ref':reference(ROOT,snapshot),'entries':entries}: raise ValueError('legacy snapshot mismatch')
    return target

def locked_environment(locked, package):
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PATH')}
    go=Path(locked['tools']['go']['path']).resolve()
    main_root=go.parents[5]
    env.update({'GOROOT':str(go.parents[1]),'GOTOOLCHAIN':'local','GOENV':'off','GOPATH':str(main_root/'.local/gopath'),'GOCACHE':str(main_root/'.local/gocache'),'PYTHONUTF8':'1',
       'RESEARCHOS_W04_PACKAGE_INPUT':str(package),'RESEARCHOS_MODE':'FIXTURE','RESEARCHOS_MEASUREMENT_MODE':'FIXTURE'})
    return env


def freeze(run, package):
    locked_path=ROOT/'execution/toolchains/locked.json'
    locked=read(locked_path)
    env=locked_environment(locked,package)
    versions=[]
    for name in ('python','go'):
        tool=locked['tools'][name]
        if digest(Path(tool['path']))!=tool['sha256']:raise ValueError('locked tool changed '+name)
        version_ref,receipt=invoke(run,name+'-version',[tool['path'],*tool['version_argv']],env,None)
        actual=(ROOT/receipt['stdout']['path']).read_text(encoding='utf-8').strip()
        if receipt['exit_code']!=0 or actual!=tool['version_output']:raise ValueError('locked tool version differs '+name)
        versions.append({'tool':name,'actual_version':actual,'invocation_ref':version_ref})
    write(run/'actual_tool_versions.json',{'schema':'researchos.w04.actual-tool-versions.v1','versions':versions,'environment':env})
    identity=write(run/'tool_identity.json',{'schema':'researchos.w04.tool-identity.v1','locked_ref':reference(ROOT,locked_path),
        'tools':[{'name':name,'path':locked['tools'][name]['path'],'sha256':locked['tools'][name]['sha256'],'version':locked['tools'][name]['version_output']} for name in ('python','go')]})
    # Capture all compiled Go packages, test helpers, embedded schemas and migrations.
    sources=enrolled_sources(ROOT,HERE)
    specnames=['contracts/acceptance.json','contracts/tasks.json','contracts/execution.plan.json','PACKAGE_MANIFEST.json','15_NEW_PROJECT_WORKFLOW.md']
    spec=[reference(ROOT,package/name) for name in specnames]
    inputs=[reference(ROOT,p) for base in (package,ROOT/'spec/v2.0') for p in sorted(base.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    policy_ref=reference(ROOT,ROOT/'internal/domain/project_rules_v24.go')
    adapter_ref=reference(ROOT,ROOT/'adapters/local_workspace/inventory.go')
    vector={'schema':'researchos.w04.version-vector.v1','package_version':'2.4.0','spec_files':spec,
      'source_files':[reference(ROOT,p) for p in sorted(sources)],'input_files':inputs,
      'lock_files':[reference(ROOT,ROOT/n) for n in ('go.mod','go.sum','execution/toolchains/locked.json')],
      'tool_files':[identity],'environment':{'os':'Windows','arch':'amd64','timezone':'Asia/Shanghai'},
      'components':{'model':{'status':'not_applicable','reason':'Deterministic HTTP/SQLite/scanner fixtures; no model invocation.'},
       'adapter':{'status':'applicable','version':'repository local_workspace scanner at frozen source hash','refs':[adapter_ref]},
       'rubric':{'status':'not_applicable','reason':'Exact frozen assertion comparisons; no model rubric judgement.'},
       'policy':{'status':'applicable','version':'embedded project rules 1.1 from package 2.4.0','refs':[policy_ref]}}}
    return write(run/'version_vector.json',vector),locked,env


def compiled_inputs(packages):
    paths=set(enrolled_sources(ROOT,HERE))
    paths.update([ROOT/'go.mod',ROOT/'go.sum',ROOT/'execution/toolchains/locked.json',HERE/'test_collect.py'])
    for package in packages:
        directory=Path(package.get('Dir','')).resolve()
        for field in ('GoFiles','CgoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles'):
            for name in package.get(field,[]):
                path=(directory/name).resolve()
                if not path.is_file():raise ValueError('compiled input missing: '+str(path))
                paths.add(path)
        if directory.is_relative_to(ROOT) and directory.relative_to(ROOT).parts[:1]!=('.local',):
            paths.update(p.resolve() for p in directory.glob('*.go') if p.is_file())
    return [{'path':str(p),'sha256':digest(p)} for p in sorted(paths,key=str)]


def compilation_freeze(run, locked, env, vector_ref, assignment_path):
    argv=[locked['tools']['go']['path'],'list','-deps','-test','-json','./internal/domain','./internal/host','./tests/context/parent']
    invocation_ref,receipt=invoke(run,'compiled-dependencies',argv,env,vector_ref)
    if receipt['exit_code']!=0:raise ValueError('actual compiled closure unavailable')
    raw=(ROOT/receipt['stdout']['path']).read_text(encoding='utf-8');decoder=json.JSONDecoder();offset=0;packages=[]
    while offset<len(raw):
        while offset<len(raw) and raw[offset].isspace():offset+=1
        if offset==len(raw):break
        package,offset=decoder.raw_decode(raw,offset);packages.append(package)
    if not packages:raise ValueError('empty compiled package inventory')
    files=compiled_inputs(packages)
    bound={row['path']:row['sha256'] for row in files}
    for path in [assignment_path,*[Path(locked['tools'][name]['path']) for name in ('python','go')]]:
        bound[str(path)]=digest(path)
    files=[{'path':path,'sha256':value} for path,value in sorted(bound.items())]
    write(run/'compiled-inputs-before.json',{'schema':'researchos.w04.auxiliary-compiled-inputs.v1','invocation_ref':invocation_ref,'files':files,
        'tooling_only_ref':reference(ROOT,HERE/'test_collect.py'),'strict_source_coverage':'UNCHANGED_SIX_ROOTS_AND_EIGHT_FILES'})
    return files


def verify_compilation(run, files, name):
    paths={Path(row['path']) for row in files}
    paths.update(enrolled_sources(ROOT,HERE))
    for path in list(paths):
        if path.suffix=='.go' and path.is_relative_to(ROOT) and path.relative_to(ROOT).parts[:1]!=('.local',):
            paths.update(p for p in path.parent.glob('*.go') if p.is_file())
    after=[{'path':str(path),'sha256':digest(path) if path.is_file() else None} for path in sorted(paths,key=str)]
    write(run/name,{'schema':'researchos.w04.auxiliary-compiled-inputs.v1','files':after,'unchanged':files==after})
    if after!=files:raise ValueError('compiled dependency or tooling changed during collection')

def invoke(run,name,argv,env,vector_ref):
    start=now()
    out=run/(name+'.stdout');err=run/(name+'.stderr')
    with out.open('xb') as stdout,err.open('xb') as stderr:
        result=subprocess.run(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,check=False)
    receipt={'schema':'researchos.w04.source-invocation.v1','status':'PASS' if result.returncode==0 else 'FAIL','mode':'FIXTURE',
      'actual_argv':argv,'cwd':str(ROOT),'environment_variable_names':sorted(env),'exit_code':result.returncode,
      'executable_sha256':digest(Path(argv[0])),'started_at':start,'ended_at':now(),
      'stdout':reference(ROOT,out),'stderr':reference(ROOT,err),'version_vector_ref':vector_ref}
    return write(run/(name+'.json'),receipt),receipt

def archive_sources(run,vector_ref):
    vector=read(ROOT/vector_ref['path'])
    refs={ref['path']:ref for group in ('spec_files','source_files','input_files','lock_files','tool_files') for ref in vector[group]}
    snapshots=[]
    for path,ref in refs.items():
        source=ROOT/path
        if digest(source)!=ref['sha256']:raise ValueError('source moved during freeze: '+path)
        destination=run/'source_snapshot'/path
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
        snapshots.append({'original_ref':ref,'snapshot_ref':reference(ROOT,destination)})
    write(run/'source_snapshot_manifest.json',{'schema':'researchos.execution-source-snapshot.v1','version_vector_ref':vector_ref,'snapshots':snapshots,'unavailable_originals':[]})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--package-input',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--executor-id',required=True)
    parser.add_argument('--verifier-id',required=True)
    parser.add_argument('--root-id',required=True)
    parser.add_argument('--actor-assignment',type=Path,required=True)
    args=parser.parse_args()
    assignment=assigned_actors(args.actor_assignment.resolve(),args.executor_id,args.verifier_id,args.root_id)
    package=prepare(args.package_input.resolve())
    if args.prepare_only:
        print(json.dumps({'status':'PREPARED_NOT_EXECUTED','package':str(package)}));return 0
    run=new_run()
    write(run/'actor_assignment.json',{'assignment':assignment,'original_assignment_ref':reference(ROOT,args.actor_assignment.resolve())})
    expected=read(HERE/'expected.json')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    vector_ref,locked,env=freeze(run,package)
    archive_sources(run,vector_ref)
    go=locked['tools']['go']['path'];python=locked['tools']['python']['path']
    files=compilation_freeze(run,locked,env,vector_ref,args.actor_assignment.resolve())
    try:
        return execute(run,package,args,expected,revision,dirty,vector_ref,go,python,env,files)
    finally:
        verify_compilation(run,files,'compiled-inputs-after.json')


def execute(run,package,args,expected,revision,dirty,vector_ref,go,python,env,files):
    executor=args.executor_id
    names=[name for name in expected['go_test_rosters'] if '/' not in name]
    transport_ref,transport=invoke(run,'transport-controls',[python,'-B','-X','utf8',str(HERE/'test_bridge.py')],env,vector_ref)
    if transport['exit_code']!=0:
        print(json.dumps({'status':'FAIL','stage':'SYNTHETIC_TRANSPORT_ONLY','receipt':transport_ref}));return 1
    argv=[go,'test','-count=1','-json','-run','^('+'|'.join(names)+')$','./internal/domain','./internal/host','./tests/context/parent']
    go_ref,go_result=invoke(run,'go',argv,env,vector_ref)
    if go_result['exit_code']!=0:
        print(json.dumps({'status':'FAIL','stage':'GO','receipt':go_ref}));return 1
    package_ref,package_result=invoke(run,'package',[python,'-B','-X','utf8',str(package/'tools/validate_package.py')],env,vector_ref)
    if package_result['exit_code']!=0:
        print(json.dumps({'status':'FAIL','stage':'PACKAGE','receipt':package_ref}));return 1
    verify_compilation(run,files,'compiled-inputs-preproof.json')
    proof={'schema':'researchos.w04.observed-proof.v1','status':'PASS','mode':'FIXTURE','owner_step':'W04-99','run_id':run.name,
       'go_test_rosters':expected['go_test_rosters'],'go_package_rosters':expected['go_package_rosters'],'version_vector_ref':vector_ref,'go_invocation_ref':go_ref,'package_invocation_ref':package_ref,
       'code_revision':revision,'dirty':dirty,'started_at':go_result['started_at'],'ended_at':package_result['ended_at'],'transport_controls_ref':transport_ref}
    proof_ref=write(run/'proof.json',proof)
    pointer=HERE/'current_proof.json'
    pointer.write_text(json.dumps({'proof_ref':proof_ref},indent=2)+'\n',encoding='utf-8')
    _,rows,_=driver.verified_proof(expected)
    index={'schema':'researchos.w04.execution-index.v1','task_id':'W04','step_id':'W04-99','run_id':run.name,'executor_id':executor,'cases':{},'parent_gates':{}}
    commands={}
    for entry in expected['case_entries']+expected['gate_entries']:
        case=entry.get('case_id','');check=entry.get('check_id','');key=entry['command_key'];selector={'case_id':case} if case else {'check_id':check}
        child_env={**env,'RESEARCHOS_TASK_ID':'W04','RESEARCHOS_CASE_ID':case,'RESEARCHOS_CHECK_ID':check}
        stem=(case or check)+'-'+key.replace('.','-')
        child_ref,child=invoke(run,stem,[python,'-B','-X','utf8',str(HERE/'parent_driver.py'),key],child_env,vector_ref)
        if child['exit_code']!=0:raise ValueError('direct exact reader failed: '+stem)
        command={**child,'schema':'researchos.w04.command.v1','command_key':key,'task_id':'W04','mode':'FIXTURE','run_id':run.name,
          'executor_id':executor,'selector':selector,'invocation_kind':'DIRECT_DRIVER','registered_command_revision':None,'source_invocation_refs':[go_ref,package_ref]}
        command_ref=write(run/(stem+'.command.json'),command)
        commands[(case,key)]=command
        if check:index['parent_gates'][check]=command_ref
    acceptance=read(package/'contracts/acceptance.json')
    for case_id,ids in expected['cases'].items():
        spec=next(c for c in acceptance['cases'] if c['id']==case_id)
        case_rows=[]
        for assertion in spec['assertions']:
            observed=next(r for r in rows if r['assertion_id']==assertion['id'])
            case_rows.append({'id':assertion['id'],'expected':assertion['expected'],'actual':observed['actual'],'status':observed['status'],
               'command_keys':spec['command_keys'],'raw_evidence_refs':observed['raw_evidence_refs']})
        refs={}
        refs['run_receipt']=write(run/(case_id+'.run_receipt.json'),{'schema':'researchos.w04.run-receipt.v1','case_id':case_id,'run_id':run.name,'environment_mode':'FIXTURE',
          'os':'Windows','arch':'amd64','timezone':'Asia/Shanghai','started_at':proof['started_at'],'ended_at':proof['ended_at'],'executor_id':executor,'verifier_id':args.verifier_id,'verifier_assignment_status':'ASSIGNED_NOT_YET_REVIEWED'})
        refs['version_manifest']=write(run/(case_id+'.version_manifest.json'),{'schema':'researchos.w04.version-manifest.v1','case_id':case_id,'run_id':run.name,
          'code_revision':revision,'dirty':dirty,'version_vector_ref':vector_ref})
        refs['command_receipt']=write(run/(case_id+'.command_receipt.json'),{'schema':'researchos.w04.command-receipt.v1','case_id':case_id,'run_id':run.name,
          'commands':[commands[(case_id,key)] for key in spec['command_keys']]})
        refs['assertion_results']=write(run/(case_id+'.assertion_results.json'),{'schema':'researchos.w04.assertion-results.v1','case_id':case_id,'run_id':run.name,
          'assertions':case_rows,'scenario':{'expected':{'setup':spec['setup'],'input':spec['input'],'actions':spec['actions']},
          'actual':{r['assertion_id']:r['evidence'] for r in rows if r['assertion_id'] in ids},'raw_evidence_refs':[ref for r in case_rows for ref in r['raw_evidence_refs']]}})
        index['cases'][case_id]=refs
    index_ref=write(run/'execution_index.json',index)
    verify_compilation(run,files,'compiled-inputs-prepublish.json')
    write(run/'handoff.json',{'status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','execution_index':index_ref,'version_vector_ref':vector_ref,'unique_formal_assertions':10,'formal_cases':3,'formal_command_bindings':6,'parent_gates':5})
    (HERE/'current_execution.json').write_text(json.dumps({'execution_index_ref':index_ref},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','execution_index':index_ref,'run':str(run)}));return 0

if __name__=='__main__':sys.exit(main())
