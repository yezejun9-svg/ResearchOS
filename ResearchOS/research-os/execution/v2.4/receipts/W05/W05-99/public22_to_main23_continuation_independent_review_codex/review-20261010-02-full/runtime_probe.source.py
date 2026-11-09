"""Independent public resource inventory only; no stage, SQL, Job or process call."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import sys
import types
import time

D=Path(__file__).resolve().parent
B=D.parent.parent
N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-02'

def pin(p):
    p=Path(p);data=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
def write(name,value):
    p=D/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def load(p,name):
    p=Path(p);m=types.ModuleType(name);m.__file__=str(p)
    exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
    return m

c=load(N/'public22_to23_root.source.py','independent_public_caller_inert')
h=c.doc(pin(N/'HDF.json'));mf=c.doc(h['manifest_ref']);i=c.doc(h['source_inputs_ref'])
resources=c.doc(i['runtime_resources_ref'])
leaf=c.load(i['leaf_runner_ref'],'public_leaf_inert_NO_METHOD_CALL')
job=c.load(i['owned_job_ref'],'public_owned_inert_NO_JOB_CALL')
g=c.load(c.GUARD_REF,'public_guard_for_resource_inventory')
tp=c.load(c.TP_REF,'public_TP_inert_NO_TRANSACTION_CALL')
import sqlite3, _sqlite3
locked=c.doc(i['toolchain_lock_ref'])
python=pin(sys.executable)
guard=g.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
held=c.refs_unique([pin(__file__),pin(N/'HDF.json'),h['manifest_ref'],*mf['members'],
    i['runtime_resources_ref'],i['toolchain_lock_ref'],i['leaf_runner_ref'],i['owned_job_ref'],c.GUARD_REF,c.TP_REF,
    *resources['resource_refs']])
result=dict(schema='researchos.public22-continuation-independent-public-runtime-closure.v1',
    actor_id='codex:/root/full_w09_source_review',source_caller_ref=h['caller_ref'],
    runtime_resources_ref=i['runtime_resources_ref'],runtime_manifest_resource_count=len(resources['resource_refs']),
    held_input_refs=held,inertly_loaded_sources=[h['caller_ref'],i['leaf_runner_ref'],i['owned_job_ref'],c.GUARD_REF,c.TP_REF],
    instrumentation_source_ref=pin(__file__),excluded_instrumentation_refs=[],missing=[],
    actual_product_calls=0,SQL_connections=0,Job_calls=0,TP_calls=0,Root_stage_calls=0,
    execution_grant=False,formal_acceptance=False,future_Root_runtime_qualification_issued=False)
try:
    guard.acquire(held)
    dlls=[pin(p) for p in job.runtime_resource_paths()]
    required=[python,pin(_sqlite3.__file__),c.GUARD_REF,c.TP_REF,h['caller_ref'],*dlls]
    module_resources=[]
    for name,module in tuple(sys.modules.items()):
        for key in ('__file__','__cached__'):
            p=getattr(module,key,None)
            if p and Path(p).is_file():
                ref=pin(p)
                if c.same(ref,result['instrumentation_source_ref']):
                    result['excluded_instrumentation_refs'].append(dict(module=name,field=key,ref=ref,
                        reason='Actual reviewer entry file, not the future __main__ Caller; Caller exact file separately included.'))
                else:
                    required.append(ref);module_resources.append(dict(module=name,field=key,ref=ref))
    required=c.refs_unique(required)
    allowed={c.canonical(r['path']):r for r in resources['resource_refs']}
    own={c.canonical(r['path']):r for r in mf['members']}
    for ref in required:
        table=own if Path(ref['path']).is_relative_to(N) else allowed
        target=table.get(c.canonical(ref['path']))
        if target is None or not c.same(ref,target):result['missing'].append(ref)
    result.update(required_refs=required,required_count=len(required),actual_loaded_dll_refs=dlls,
        loaded_module_resources=module_resources,
        locked_Python_path_and_sha=c.canonical(python['path'])==c.canonical(locked['tools']['python']['path']) and python['sha256']==locked['tools']['python']['sha256'],
        locked_Python_flags=dict(isolated=sys.flags.isolated,no_site=sys.flags.no_site,dont_write_bytecode=sys.dont_write_bytecode,utf8_mode=sys.flags.utf8_mode),
        complete_exact_loaded_public_closure=not result['missing'])
finally:
    result['guard_closed_ref']=write('runtime-sourceguard.closed.json',guard.close())
write('runtime-public-closure.json',result)
print(json.dumps(dict(required_count=result.get('required_count'),manifest_count=result['runtime_manifest_resource_count'],
    missing=result['missing'],complete=result.get('complete_exact_loaded_public_closure'),
    guard_closed_ref=result['guard_closed_ref'],product_calls=0),ensure_ascii=False))
