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
EXECUTOR = 'codex:/root/w1102_impl'

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    save_new(path,value)
    return reference(ROOT,path)

def read(path): return strict_json(path.read_bytes())

def prepare(package):
    target=HERE/'frozen_inputs'/'package'
    if not target.exists(): shutil.copytree(package,target)
    # Every immutable package byte is retained, including its actual validator.
    original={p.relative_to(package).as_posix():digest(p) for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    copied={p.relative_to(target).as_posix():digest(p) for p in target.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if original!=copied: raise ValueError('frozen package differs')
    snapshot=HERE/'frozen_inputs'/'commands-v24-r37.json'
    if not snapshot.exists(): shutil.copyfile(ROOT/'execution/v2.4/commands.json',snapshot)
    registry=read(snapshot)
    if registry['revision']!=37: raise ValueError('wrong pre-W04 registry snapshot')
    entries={k:registry['commands'][k] for k in ('test.context','test.domain')}
    decoded=HERE/'frozen_inputs'/'legacy_entries.json'
    if not decoded.exists(): write(decoded,{'registry_ref':reference(ROOT,snapshot),'entries':entries})
    if read(decoded)['entries']!=entries: raise ValueError('legacy snapshot mismatch')
    return target

def freeze(run, package):
    locked_path=ROOT/'execution/toolchains/locked.json'
    locked=read(locked_path)
    for name in ('python','go'):
        tool=locked['tools'][name]
        if digest(Path(tool['path']))!=tool['sha256']:raise ValueError('locked tool changed '+name)
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
    return write(run/'version_vector.json',vector),locked

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
    args=parser.parse_args()
    package=prepare(args.package_input.resolve())
    if args.prepare_only:
        print(json.dumps({'status':'PREPARED_NOT_EXECUTED','package':str(package)}));return 0
    run=HERE/'runs'/(dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:12]);run.mkdir(parents=True)
    expected=read(HERE/'expected.json')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    vector_ref,locked=freeze(run,package)
    archive_sources(run,vector_ref)
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PATH')}
    go=locked['tools']['go']['path'];python=locked['tools']['python']['path']
    main_root=Path(go).parents[5]
    env.update({'GOTOOLCHAIN':'local','GOENV':'off','GOPATH':str(main_root/'.local/gopath'),'GOCACHE':str(main_root/'.local/gocache'),'PYTHONUTF8':'1',
       'RESEARCHOS_W04_PACKAGE_INPUT':str(package),'RESEARCHOS_MODE':'FIXTURE','RESEARCHOS_MEASUREMENT_MODE':'FIXTURE'})
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
    proof={'schema':'researchos.w04.observed-proof.v1','status':'PASS','mode':'FIXTURE','owner_step':'W04-99','run_id':run.name,
       'go_test_rosters':expected['go_test_rosters'],'go_package_rosters':expected['go_package_rosters'],'version_vector_ref':vector_ref,'go_invocation_ref':go_ref,'package_invocation_ref':package_ref,
       'code_revision':revision,'dirty':dirty,'started_at':go_result['started_at'],'ended_at':package_result['ended_at'],'transport_controls_ref':transport_ref}
    proof_ref=write(run/'proof.json',proof)
    pointer=HERE/'current_proof.json'
    pointer.write_text(json.dumps({'proof_ref':proof_ref},indent=2)+'\n',encoding='utf-8')
    _,rows,_=driver.verified_proof(expected)
    index={'schema':'researchos.w04.execution-index.v1','task_id':'W04','step_id':'W04-99','run_id':run.name,'executor_id':EXECUTOR,'cases':{},'parent_gates':{}}
    commands={}
    for entry in expected['case_entries']+expected['gate_entries']:
        case=entry.get('case_id','');check=entry.get('check_id','');key=entry['command_key'];selector={'case_id':case} if case else {'check_id':check}
        child_env={**env,'RESEARCHOS_TASK_ID':'W04','RESEARCHOS_CASE_ID':case,'RESEARCHOS_CHECK_ID':check}
        stem=(case or check)+'-'+key.replace('.','-')
        child_ref,child=invoke(run,stem,[python,'-B','-X','utf8',str(HERE/'parent_driver.py'),key],child_env,vector_ref)
        if child['exit_code']!=0:raise ValueError('direct exact reader failed: '+stem)
        command={**child,'schema':'researchos.w04.command.v1','command_key':key,'task_id':'W04','mode':'FIXTURE','run_id':run.name,
          'executor_id':EXECUTOR,'selector':selector,'invocation_kind':'DIRECT_DRIVER','registered_command_revision':None,'source_invocation_refs':[go_ref,package_ref]}
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
          'os':'Windows','arch':'amd64','timezone':'Asia/Shanghai','started_at':proof['started_at'],'ended_at':proof['ended_at'],'executor_id':EXECUTOR,'verifier_id':'codex:/root/w1702_review','verifier_assignment_status':'ASSIGNED_NOT_YET_REVIEWED'})
        refs['version_manifest']=write(run/(case_id+'.version_manifest.json'),{'schema':'researchos.w04.version-manifest.v1','case_id':case_id,'run_id':run.name,
          'code_revision':revision,'dirty':dirty,'version_vector_ref':vector_ref})
        refs['command_receipt']=write(run/(case_id+'.command_receipt.json'),{'schema':'researchos.w04.command-receipt.v1','case_id':case_id,'run_id':run.name,
          'commands':[commands[(case_id,key)] for key in spec['command_keys']]})
        refs['assertion_results']=write(run/(case_id+'.assertion_results.json'),{'schema':'researchos.w04.assertion-results.v1','case_id':case_id,'run_id':run.name,
          'assertions':case_rows,'scenario':{'expected':{'setup':spec['setup'],'input':spec['input'],'actions':spec['actions']},
          'actual':{r['assertion_id']:r['evidence'] for r in rows if r['assertion_id'] in ids},'raw_evidence_refs':[ref for r in case_rows for ref in r['raw_evidence_refs']]}})
        index['cases'][case_id]=refs
    index_ref=write(run/'execution_index.json',index)
    write(run/'handoff.json',{'status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','execution_index':index_ref,'version_vector_ref':vector_ref,'unique_formal_assertions':10,'formal_cases':3,'formal_command_bindings':6,'parent_gates':5})
    (HERE/'current_execution.json').write_text(json.dumps({'execution_index_ref':index_ref},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','execution_index':index_ref,'run':str(run)}));return 0

if __name__=='__main__':sys.exit(main())
