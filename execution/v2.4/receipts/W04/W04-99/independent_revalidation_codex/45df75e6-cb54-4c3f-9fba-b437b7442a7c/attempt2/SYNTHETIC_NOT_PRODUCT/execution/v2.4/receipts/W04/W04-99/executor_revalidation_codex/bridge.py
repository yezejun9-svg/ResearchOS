"""Exact W04 evidence reuse plus unchanged pre-W04 registered transport."""
import json
import os
from pathlib import Path
import subprocess
import sys

from evidence_module import digest, strict_json
import parent_driver as driver

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]

def read(path):return strict_json(path.read_bytes())

def route(key, env):
    if key not in ('test.context','test.domain','package.validate'):raise ValueError('unknown command key')
    task,check,case=(env.get('RESEARCHOS_'+name,'') for name in ('TASK_ID','CHECK_ID','CASE_ID'))
    if task=='W04' and (check in ('W04-G01','W04-G02','W04-G03','W04-H01','W04-B01') or case in ('C03','C04','A01')):
        driver.selector(key,task,check,case,read(HERE/'expected.json'))
        if env.get('RESEARCHOS_MODE','FIXTURE')!='FIXTURE' or env.get('RESEARCHOS_MEASUREMENT_MODE','FIXTURE')!='FIXTURE':raise ValueError('exact W04 requires FIXTURE')
        return 'current',None
    if key=='package.validate':raise ValueError('new formal package entry only accepts W04 A01')
    if check in ('W04-G01','W04-G02','W04-G03','W04-H01','W04-B01'):raise ValueError('wrong parent owner')
    snapshot=read(HERE/'frozen_inputs/legacy_entries.json')
    registry=read(driver.verified_ref(snapshot['registry_ref']))
    entry=snapshot['entries'][key]
    if entry!=registry['commands'][key]:raise ValueError('legacy entry changed')
    selectors=entry['selectors']
    for field,value in (('task_id',task),('check_id',check),('case_id',case)):
        allowed=selectors[field]
        if value and value not in allowed and '*' not in allowed:raise ValueError('unregistered legacy selector')
    if check and case:raise ValueError('mixed legacy selector')
    return 'legacy',entry

def forward(entry,inherited,call=subprocess.call):
    locked=read(ROOT/'execution/toolchains/locked.json')['tools']
    env={name:inherited[name] for name in entry['allowed_env'] if name in inherited}
    env.update(entry['fixed_env'])
    for name in ('RESEARCHOS_TASK_ID','RESEARCHOS_CHECK_ID','RESEARCHOS_CASE_ID'):
        if inherited.get(name):env[name]=inherited[name]
    for name,tool_name in entry['tool_env'].items():
        tool=locked[tool_name]
        if digest(Path(tool['path']))!=tool['sha256']:raise ValueError('legacy tool changed '+tool_name)
        env[name]=tool['path']
    tool=locked[entry['executable_tool']]
    if digest(Path(tool['path']))!=tool['sha256']:raise ValueError('legacy executable changed')
    return call([tool['path'],*entry['argv']],cwd=ROOT/entry['cwd'],env=env)

def main():
    try:
        if len(sys.argv)!=2:raise ValueError('one explicit command key required')
        key=sys.argv[1];kind,entry=route(key,os.environ)
        if kind=='legacy':return forward(entry,os.environ)
        result=driver.report(key,os.environ.get('RESEARCHOS_TASK_ID',''),os.environ.get('RESEARCHOS_CHECK_ID',''),os.environ.get('RESEARCHOS_CASE_ID',''))
        index_ref=read(HERE/'current_execution.json')['execution_index_ref']
        index=read(driver.verified_ref(index_ref))
        if index['run_id']!=result['run_id']:raise ValueError('execution index and current proof differ')
        result['execution_index_ref']=index_ref
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,KeyError,TypeError,OSError) as error:
        print(json.dumps({'status':'FAIL','assertions':0,'assertion_ids':[],'error':str(error)},ensure_ascii=False));return 1

if __name__=='__main__':sys.exit(main())
