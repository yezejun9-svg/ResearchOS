"""Independent finite runtime resource review; no programme or Root issuance."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import ast, hashlib, json, os, sys, types

R = Path('D:/作品集/ResearchOS/research-os')
B = R/'execution/v2.4/receipts/W05/W05-99'
D = R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
N = Path(__file__).resolve().parent
ACTOR = 'codex:/root/attach_fixture_source_review'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks = []
def pin(path):
    p=Path(path); raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(ref):
    return json.loads(Path(ref['path'] if isinstance(ref,dict) else ref).read_bytes())
def save(name,value):
    p=N/name
    with p.open('xb') as f: f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def check(name, result):
    checks.append(dict(name=name,passed=bool(result)))
def same(a,b):
    return os.path.normcase(os.path.abspath(a['path']))==os.path.normcase(os.path.abspath(b['path'])) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def load(ref,name):
    assert same(pin(ref['path']),ref),ref
    m=types.ModuleType(name);m.__file__=ref['path'];sys.modules[name]=m
    exec(compile(Path(ref['path']).read_bytes(),m.__file__,'exec'),m.__dict__)
    return m
def run():
    proposed_ref=pin(D/'main23.v4.runtime-resources.proposed.root.json')
    scope_ref=pin(D/'main23.v4.runtime-qualification.scope.actual.root.json')
    assert proposed_ref['sha256']=='a49f6dda6638b7cd80f1644ec0e31fa144a13296b7467498dbfe1fdcf35b67ed' and proposed_ref['bytes']==35255
    assert scope_ref['sha256']=='be30088c2112556ccb45fab5ea14dd59a0d2e511c12ca34f43f9e27f3c672847' and scope_ref['bytes']==1614
    proposed,scope=read(proposed_ref),read(scope_ref)
    previous_root=N.parent/'runtime-20261010-03-isolated'
    previous_decision_ref=pin(previous_root/'decision.json')
    assert previous_decision_ref['sha256']=='605c0eac898454d461429f11523aa1c7b8a8a2a0a97cc4662fd3705aac3135ad' and previous_decision_ref['bytes']==35935
    previous_decision=read(previous_decision_ref)
    caller_ref=proposed['caller_ref']
    # Bootstrap only the guard source already pinned in the proposed set.
    guard_ref=next(r for r in proposed['resource_refs'] if r['path'].replace('\\','/').endswith('/source_read_guard.py'))
    guard=load(guard_ref,'independent_main23_resource_guard')
    sh=read(proposed['source_hdf_ref']);sm=read(proposed['source_mf_ref'])
    contract=read(proposed['builder_contract_ref'])
    refs=proposed['resource_refs']+[proposed_ref,scope_ref,proposed['probe_guard_ref'],proposed['source_hdf_ref'],proposed['source_mf_ref'],proposed['builder_contract_ref'],previous_decision_ref]+sm['members']+[pin(__file__)]
    unique={}
    for ref in refs:
        key=os.path.normcase(os.path.abspath(ref['path']))
        assert key not in unique or same(unique[key],ref)
        unique[key]=ref
    refs=list(unique.values())
    held=guard.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=1024*1024*1024)
    held.acquire(refs)
    try:
        for ref in refs: check('pin:'+ref['path'],same(pin(ref['path']),ref))
        caller=load(caller_ref,'independent_main23_resource_caller')
        tp=load(caller.TP_REF,'independent_main23_resource_tp')
        job=load(contract['owned_job_ref'],'independent_main23_resource_owned')
        builder=load(contract['builder_ref'],'independent_main23_resource_builder')
        base=load(contract['base_helper_ref'],'independent_main23_resource_base')
        paths=list(job.runtime_resource_paths())
        for module in tuple(sys.modules.values()):
            for key in ('__file__','__cached__'):
                value=getattr(module,key,None)
                if value and Path(value).is_file():paths.append(value)
        paths += [sys.executable,contract['go_ref']['path'],caller_ref['path'],caller.GUARD_REF['path'],caller.TP_REF['path'],contract['owned_job_ref']['path'],contract['builder_ref']['path'],contract['base_helper_ref']['path']]
        observed={caller.canonical(p):pin(p) for p in paths}
        observer_key=caller.canonical(__file__)
        observer_only=observed.pop(observer_key)
        proposed_map={caller.canonical(r['path']):r for r in proposed['resource_refs']}
        previous_map={caller.canonical(r['path']):r for r in previous_decision['resource_refs']}
        unchanged=[r for k,r in proposed_map.items() if k in previous_map and same(r,previous_map[k])]
        removed=[r for k,r in previous_map.items() if k not in proposed_map]
        added=[r for k,r in proposed_map.items() if k not in previous_map]
        check('exact Task55 delta 143 unchanged and only caller plus Root observer replaced',len(unchanged)==143 and len(removed)==len(added)==2 and {Path(r['path']).name for r in added}=={'main23_root.source.py','prepare_main23_v4_runtime_qualification.root.py'} and {Path(r['path']).name for r in removed}=={'main23_root.source.py','prepare_main23_runtime_qualification.root.py'})
        check('M4 Source actual author unchanged',sh['source_author']=='codex:/root/backup_regression_resources')
        missing=[r for k,r in observed.items() if k not in proposed_map]
        mismatched=[r for k,r in observed.items() if k in proposed_map and not same(r,proposed_map[k])]
        extras=[r for k,r in proposed_map.items() if k not in observed]
        check('145 original ordered unique resources',len(proposed['resource_refs'])==len(proposed_map)==145 and list(proposed_map)==sorted(proposed_map))
        check('all independently observed target resources covered',not missing and not mismatched)
        check('only expected Root observer source extra',len(extras)==1 and caller.canonical(extras[0]['path'])==caller.canonical(str(D/'prepare_main23_v4_runtime_qualification.root.py')))
        check('python exact running executable',same(pin(sys.executable),proposed['python_ref']))
        check('Go exact builder pin',same(contract['go_ref'],proposed['go_ref']))
        check('Root scope identity and purpose',scope['schema']=='researchos.root-main23-runtime-qualification-scope.v2' and scope['issued_by']=='codex:/root' and scope['root_thread_id']==THREAD and scope['slice_id']=='MAIN23_RUNTIME_RESOURCE_QUALIFICATION' and scope['formal_acceptance'] is False and scope['execution_grant'] is False)
        check('Root scope live and already issued',datetime.fromisoformat(scope['created_utc'])<=datetime.now(timezone.utc)<datetime.fromisoformat(scope['lease_expires_at']))
        check('proposed exact scope pin',same(proposed['qualification_scope_ref'],scope_ref))
        for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref'):check('scope exact '+k,same(scope[k],proposed[k]))
        check('Source HDF binds exact caller and MF',same(sh['manifest_ref'],proposed['source_mf_ref']) and same(sh['caller_ref'],caller_ref))
        rg=read(proposed['probe_guard_ref'])
        check('Root guard completed closed clean',rg['verification']=='PASSED' and rg['closed'] is True and rg['retained_handles_count']==0 and rg['errors']==[] and rg['failure'] is None)
        check('Root guard exact 145 refs',len(rg['entries'])==145 and all(same(e,r) and e['verified'] is True and e['closed'] is True and e['final_path_match'] is True for e,r in zip(rg['entries'],proposed['resource_refs'])))
        for ref in refs:check('final pin:'+ref['path'],same(pin(ref['path']),ref))
    finally:closed=held.close()
    check('independent guard closed clean',closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[])
    guard_out=save('source-guard.closed.json',closed)
    closure=save('runtime-closure-observation.json',dict(proposed_resources_ref=proposed_ref,previous_Task55_decision_ref=previous_decision_ref,unchanged_resources=unchanged,removed_resources=removed,added_resources=added,observed_target_resources=list(observed.values()),observer_only_resource=observer_only,proposed_extra_resources=extras,missing_resources=missing,mismatched_resources=mismatched,excluded_observer_reason='Only this independent review script differs from the Root observer script; all imported target modules, their caches and loaded DLLs remain checked.',actual_Go_runs=0,actual_Native_runs=0,actual_SQL_queries=0,actual_dispatcher_runs=0,actual_model_requests=0,Canonical_written=False))
    failed=[x for x in checks if not x['passed']]
    finite=save('finitechecks.json',dict(checks=checks,passed=len(checks)-len(failed),failed=failed))
    common=dict(review_author=ACTOR,source_author='codex:/root/backup_regression_resources',builder_source_author='codex:/root/native_temp_independent_review',root_thread_id=THREAD,**{k:proposed[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','python_ref','go_ref')},qualification_scope_ref=scope_ref,formal_acceptance=False,execution_grant=False)
    decision=save('decision.json',dict(schema='researchos.main23-runtime-independent-review-decision.v2',**common,independent_non_author=True,verdict='RUNTIME_CLOSURE_ACCEPTED' if not failed else 'RUNTIME_CLOSURE_REJECTED',resource_refs=proposed['resource_refs'],finitechecks_ref=finite,Source_guard_ref=guard_out,closure_observation_ref=closure,programme_qualification=None))
    mf=save('MF.json',dict(schema='researchos.main23-runtime-independent-review-manifest.v2',members=refs+[guard_out,closure,finite,decision]))
    hdf=save('HDF.json',dict(schema='researchos.main23-runtime-independent-review-hdf.v2',**common,manifest_ref=mf,decision_ref=decision,reviewed_utc=datetime.now(timezone.utc).isoformat(),finitechecks_ref=finite,Source_guard_ref=guard_out,closure_observation_ref=closure,programme_qualification=None))
    print(json.dumps(dict(HDF=hdf,MF=mf,decision=decision,verdict=read(decision)['verdict'],checks=len(checks),failed=failed,held_refs=len(refs),proposed_resources=145,observed_resources=len(observed),Source_guard_closed=True,formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)
if __name__=='__main__':run()
