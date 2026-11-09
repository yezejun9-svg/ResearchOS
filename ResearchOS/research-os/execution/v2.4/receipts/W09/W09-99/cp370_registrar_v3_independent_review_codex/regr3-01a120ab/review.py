"""Source-only independent v3 review. Never invokes registrar entrypoints or consumers."""
import ast
import copy
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import sys
import types

N = Path(__file__).resolve().parent
W = N.parent.parent
S = W / 'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v3'
PREVIOUS = W / 'cp370_registrar_v2_independent_review_codex/regr2-01a120ab'
SEED_REVIEW = W / 'cp370_prepared_root_inputs_independent_review_codex/seed996r-01a12072'
CALLER = W / 'w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v6'
CALLER_REVIEW = W / 'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
checks = []

def pin(p):
    p=Path(p).resolve(strict=True); raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(p): return json.loads(Path(p).read_bytes())

def save(name,value):
    with (N/name).open('xb') as f: f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(N/name)

def record(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok: raise AssertionError(name)

def rejected(name,callback,expected):
    try: callback()
    except ValueError as e: record(name,str(e)==expected,str(e))
    else: record(name,False,'BAD_INPUT_ACCEPTED')

def mod(p):
    m=types.ModuleType('independent_'+Path(p).stem);m.__file__=str(p)
    exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__)
    return m

def functions(p):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(p).read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}

def main():
    hdfref=pin(S/'HDF.json');mfref=pin(S/'MF.json')
    record('exact supplied HDF', (hdfref['sha256'],hdfref['bytes'])==('246a870b96519fedcafe2840ef23bb778f01631236a205d6b08a4a15f124457a',3388))
    record('exact supplied MF',(mfref['sha256'],mfref['bytes'])==('1c8754af40371f08711d2356def2ba626a04c2b8e9249de3a79386a7f77aaba6',8749))
    hdf=read(hdfref['path']);mf=read(mfref['path']);source=hdf['registrar_ref']
    record('Source/contract coherent',hdf['manifest_ref']==mfref and source==mf['registrar_ref'] and pin(source['path'])==source and hdf['root_contract_ref']==mf['root_contract_ref'])
    m=mod(source['path'])
    refs=[hdfref,mfref,pin(__file__),pin(PREVIOUS/'HDF.final.json'),pin(PREVIOUS/'MF.final.json'),pin(SEED_REVIEW/'HDF.json'),pin(SEED_REVIEW/'MF.json'),*mf['members']]
    refs.extend({k:e[k] for k in ('path','sha256','bytes')} for e in read(hdf['guard_cleanup_ref']['path'])['entries'])
    for p in (PREVIOUS/'HDF.final.json',PREVIOUS/'MF.final.json',SEED_REVIEW/'HDF.json',CALLER/'HDF.json',CALLER_REVIEW/'HDF.json'):
        refs.append(pin(p));refs.extend(m.embedded_refs(read(p)))
    guard,count=m.held_guard(refs,False)
    pair_cleanup_ref=None
    try:
        for ref in mf['members']: record('Source manifest pin '+Path(ref['path']).name,pin(ref['path'])==ref)
        previous_hdf=read(mf['prior_source_hdf_ref']['path'])
        oldfunctions=functions(previous_hdf['registrar_ref']['path']);newfunctions=functions(source['path'])
        changed={k for k in oldfunctions if newfunctions.get(k)!=oldfunctions[k]}
        added=set(newfunctions)-set(oldfunctions)
        record('bounded three-root-cause diff only',changed=={'validate_root_witness','validate_activation_context','validate_qualification_continuity','held_guard'} and added=={'validate_observed_result','validate_postseal_host_provenance'},dict(changed=sorted(changed),added=sorted(added)))
        before,cp,ow=m.check_before_pair()
        record('actual baseline CP369 OW173',cp['revision']==369 and ow['revision']==173)
        caller=m.ensure_caller_source(pin(CALLER/'HDF.json'),pin(CALLER/'MF.json'))
        crh=read(CALLER_REVIEW/'HDF.json')
        request=dict(review_hdf_ref=pin(CALLER_REVIEW/'HDF.json'),review_mf_ref=crh['manifest_ref'],review_decision_ref=crh['source_decision_ref'])
        rh,rm,rd,decision=m.validate_review(request,caller)
        record('full real final Caller6 review remains accepted',decision['actor_id']==m.DESIGNATED_REVIEWER)
        rejected('empty independent review manifest rejected',lambda:m.validate_review_members(dict(read(rm['path']),members=[]),rd,caller),'REVIEW_MANIFEST_NOT_BOUND')
        for actor in ('/root',m.ROOT,m.AUTHOR,'codex:/root/other'):
            rejected('canonical independent reviewer '+actor,lambda actor=actor:m.validate_reviewer_actor(actor),'REVIEWER_NOT_CANONICAL_NONAUTHOR')
        for label,p in [('boundary',W),('dotdot',W/'SYNTHETIC_NOT_CREATED'/'..'),('outside',W.parent),('relative',Path('relative'))]:
            rejected('strict output '+label,lambda p=p:m.canonical_output_root(str(p)),'OUTPUT_ROOT_SCOPE')
        output=str((N/'synthetic-no-output').resolve())
        record('strict child accepted',m.canonical_output_root(output)==output)
        qref=mf['qualification_seed_ref'];q=read(qref['path'])
        pending=read(q['source_pending_ref']['path'])['pending']
        seed=dict(schema='researchos.root-cp370-source-live-context.v2',issued_by=m.ROOT,root_thread_id=m.ROOT_THREAD_ID,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=q['source_cutoff'],next_original_failure_ordinal=q['next_original_failure_ordinal'],pending=[{k:r[k] for k in ('ordinal','origin_ref','description')} for r in pending],qualification_ref=qref,seed_witness_ref=mf['actual_seed_witness_ref'])
        qualified=m.validate_live(seed)
        witness,wrefs=m.validate_root_witness(seed['seed_witness_ref'],seed,'SEED')
        record('real Seed996 qualification and three actual audit ranges accepted',len(qualified)==30)
        record('prior full Seed996 review retained',read(SEED_REVIEW/'HDF.json')['checks']==166 and read(SEED_REVIEW/'HDF.json')['decision']=='PREPARED_ROOT_SEED_INPUTS_VERIFIED_NONAUTHORITATIVE')
        original=read(witness['original_tool_io_ref']['path'])
        observed=read(witness['original_tool_io_ref']['path'])['result']['output'].splitlines()
        observed=json.loads(observed[0])
        m.validate_observed_result(observed,seed,q['source_pending_ref'],witness,0,'ROOT_SOURCE_PYTHON_EXIT=0')
        record('actual stdout qualifies exact q pending ordinal',True)
        for label,changed_live,changed_pending,python_exit,line in (
            ('changed qualification',dict(seed,qualification_ref=dict(qref,sha256='0'*64)),q['source_pending_ref'],0,'ROOT_SOURCE_PYTHON_EXIT=0'),
            ('changed pending',seed,dict(q['source_pending_ref'],sha256='0'*64),0,'ROOT_SOURCE_PYTHON_EXIT=0'),
            ('changed ordinal',dict(seed,next_original_failure_ordinal=997),q['source_pending_ref'],0,'ROOT_SOURCE_PYTHON_EXIT=0'),
            ('bool interpreter',seed,q['source_pending_ref'],False,'ROOT_SOURCE_PYTHON_EXIT=0'),
            ('wrong actual interpreter marker',seed,q['source_pending_ref'],1,'ROOT_SOURCE_PYTHON_EXIT=0')):
            rejected('F1 stdout rejects '+label,lambda changed_live=changed_live,changed_pending=changed_pending,python_exit=python_exit,line=line:m.validate_observed_result(observed,changed_live,changed_pending,witness,python_exit,line),'HOST_STDOUT_QUALIFICATION_NOT_BOUND')
        origload=m.load
        # Real Seed host lines stay original: only witness metadata is overlaid in memory.
        overlay=copy.deepcopy(witness);overlay.update(phase='POSTSEAL_ACTIVATION',registrar_review_refs=[rh,rm,rd],created_utc=datetime.now(timezone.utc).isoformat())
        replay_live=dict(seed,created_utc=(datetime.now(timezone.utc)+timedelta(microseconds=100)).isoformat())
        m.load=lambda ref:copy.deepcopy(overlay) if ref==seed['seed_witness_ref'] else origload(ref)
        try:
            rejected('F1 exact v2 seed replay now rejected',lambda:m.validate_root_witness(seed['seed_witness_ref'],replay_live,'POSTSEAL_ACTIVATION'),'HOST_POSTSEAL_REVIEW_CANON_NOT_BOUND')
        finally:m.load=origload
        modified_io=copy.deepcopy(original);modified_io['args']['cmd']='UNRELATED_SYNTHETIC_COMMAND_NOT_EXECUTED'
        m.load=lambda ref:copy.deepcopy(modified_io) if ref==witness['original_tool_io_ref'] else origload(ref)
        try:
            rejected('F1 different call command rejected against actual host input',lambda:m.validate_root_witness(seed['seed_witness_ref'],seed,'SEED'),'HOST_CALL_ARGUMENTS_NOT_BOUND')
        finally:m.load=origload
        binding=read(witness['capture_binding_ref']['path'])
        review_at=datetime.now(timezone.utc)
        fresh_binding=dict(binding,original_call_id='SYNTHETIC_NEW_CALL_NOT_AUTHORITY',tool_call_timestamp=(review_at+timedelta(seconds=1)).isoformat(),tool_result_timestamp=(review_at+timedelta(seconds=2)).isoformat())
        fresh_capture=dict(witness['actual_host_capture_ref'],sha256='f'*64)
        m.validate_postseal_host_provenance(binding,fresh_binding,review_at.isoformat(),witness['actual_host_capture_ref'],fresh_capture)
        record('F1 different postreview call positive pure memory only',True)
        for label,fb,fc in [('same capture',fresh_binding,witness['actual_host_capture_ref']),('same call ID',dict(fresh_binding,original_call_id=binding['original_call_id']),fresh_capture),('call before review',dict(fresh_binding,tool_call_timestamp=binding['tool_call_timestamp']),fresh_capture),('result before review',dict(fresh_binding,tool_result_timestamp=binding['tool_result_timestamp']),fresh_capture)]:
            rejected('F1 distinct physical postreview '+label,lambda fb=fb,fc=fc:m.validate_postseal_host_provenance(binding,fb,review_at.isoformat(),witness['actual_host_capture_ref'],fc),'POSTSEAL_REQUIRES_NEW_HOST_CALL_AFTER_REVIEW')
        post_witness=dict(witness,phase='POSTSEAL_ACTIVATION',registrar_review_refs=[rh,rm,rd])
        post_observed=dict(observed,registrar_review_refs=[rh,rm,rd],canonical_refs=before)
        m.validate_observed_result(post_observed,seed,q['source_pending_ref'],post_witness,0,'ROOT_SOURCE_PYTHON_EXIT=0')
        record('F1 postseal exact review triple Canon positive pure memory',True)
        for label,value in [('wrong review triple',dict(post_observed,registrar_review_refs=[rm,rh,rd])),('wrong Canon',dict(post_observed,canonical_refs=[]))]:
            rejected('F1 '+label,lambda value=value:m.validate_observed_result(value,seed,q['source_pending_ref'],post_witness,0,'ROOT_SOURCE_PYTHON_EXIT=0'),'HOST_POSTSEAL_REVIEW_CANON_NOT_BOUND')
        # Mutating a legacy exit creates a different q byte digest, which cannot borrow
        # the sealed actual stdout even if the structural qualification helper accepts it.
        for field,value in [('actual_outer_exit',0),('actual_native_exit',0)]:
            changedq=copy.deepcopy(q);changedq['rows'][1][field]=value
            raw=m.encoded(changedq);changedref=dict(qref,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            rejected('F1 legacy 967 '+field+' cannot reuse exact actual stdout',lambda changedref=changedref:m.validate_observed_result(observed,dict(seed,qualification_ref=changedref),q['source_pending_ref'],witness,0,'ROOT_SOURCE_PYTHON_EXIT=0'),'HOST_STDOUT_QUALIFICATION_NOT_BOUND')
        # F2: legitimate append changes only prior diagnostic container reference.
        fresh=copy.deepcopy(seed);fresh['next_original_failure_ordinal']=997
        fresh['pending'].append(dict(ordinal=996,origin_ref=source,description='SYNTHETIC_NEW_ORIGINAL_NOT_ACTUAL'))
        new_pending=dict(q['source_pending_ref'],sha256='a'*64)
        fresh_q=copy.deepcopy(qualified)
        for row in fresh_q.values():row['exit_qualification']['diagnostic_source_ref']=new_pending
        fresh_q[996]=dict(ordinal=996,origin_ref=source,origin_selector='SYNTHETIC_NEW_EVENT')
        m.validate_qualification_continuity(seed,qualified,fresh,fresh_q)
        record('F2 same required diagnostic rebind append now accepted',True)
        for field,value in [('actual_outer_exit',0),('actual_native_exit',0),('origin_selector','CHANGED_EVENT'),('capture_completeness','OBSERVED_NOT_FULL'),('description','CHANGED_DESCRIPTION')]:
            altered=copy.deepcopy(fresh_q);altered[967][field]=value
            rejected('F2 immutable event '+field,lambda altered=altered:m.validate_qualification_continuity(seed,qualified,fresh,altered),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
        altered=copy.deepcopy(fresh_q);altered[967]['exit_qualification']['authority']='CHANGED_AUTHORITY'
        rejected('F2 immutable original capture authority',lambda:m.validate_qualification_continuity(seed,qualified,fresh,altered),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
        altered2=copy.deepcopy(fresh_q);altered2[967]['exit_qualification']['diagnostic_source_selector']='pending[ordinal=999]'
        rejected('F2 diagnostic selector remains bound ordinal',lambda:m.validate_qualification_continuity(seed,qualified,fresh,altered2),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
        altered3=copy.deepcopy(fresh_q);altered3[987]['actual_outer_exit']=0
        rejected('F2 unknown exit remains NULL',lambda:m.validate_qualification_continuity(seed,qualified,fresh,altered3),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
        pair=copy.deepcopy([qualified[971],qualified[972]])
        record('same file different invocation selectors allowed',pair[0]['origin_ref']==pair[1]['origin_ref'] and pair[0]['origin_selector']!=pair[1]['origin_selector'])
        m.validate_invocation_identities(pair)
        pair[1]['origin_selector']=pair[0]['origin_selector']
        rejected('same event duplicate rejected',lambda:m.validate_invocation_identities(pair),'ORIGINAL_INVOCATION_REUSED')
        # F3: use actual transitive refs; no check/register/transaction is called.
        nested=[*refs,*m.embedded_refs(witness),*m.embedded_refs(q)]
        pair_guard,pair_count=m.held_guard(nested,True)
        pair_cleanup=pair_guard.close();pair_cleanup_ref=save('sourceguard.pair-excluded.closed.json',pair_cleanup)
        pair_paths={entry['path'].casefold() for entry in pair_cleanup['entries']}
        record('F3 exactly mutable CP OW excluded',str(m.CANON[0]).casefold() not in pair_paths and str(m.CANON[1]).casefold() not in pair_paths and all(str(p).casefold() in pair_paths for p in m.CANON[2:]))
        record('F3 actual nested guard closed zero',pair_cleanup['closed'] is True and pair_cleanup['retained_handles_count']==0 and pair_cleanup['errors']==[])
        record('F3 all other supplied refs remain held',all(ref['path'].casefold() in pair_paths for ref in nested if ref['path'].casefold() not in {str(p).casefold() for p in m.CANON[:2]}))
        tx=Path(m.TP).read_text(encoding='utf-8')
        record('trusted transaction still compares exclusive pair before transform/write','0x80000000|0x40000000,0,None,3,0x80,None' in tx and 'canonical expected bytes changed under exclusive ownership' in tx and tx.index('canonical expected bytes changed under exclusive ownership')<tx.index('result=transform(')<tx.index('journal.mkdir()'))
        # Exact original builder expression, evaluated into memory only.
        ch=read(CALLER/'HDF.json')
        tree=ast.parse(Path(source['path']).read_text(encoding='utf-8'))
        builder=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_root_docs')
        expression=next(n.value for n in builder.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scope' for t in n.targets))
        request.update(frozen_plan_ref=ch['frozen_plan_ref'],native_hdf_ref=ch['native_qualified_hdf_ref'],native_handoff_ref=ch['native_handoff_ref'],native_historical_request_ref=source,authorized_output_root=output)
        scope=eval(compile(ast.Expression(expression),str(source['path']),'eval'),m.__dict__,dict(request=request,decision=decision,decision_ref=rd,caller=caller,refs=before))
        fake_ref=lambda name:dict(path=str(N/name),sha256='0'*64,bytes=0)
        sr,orr,wr,fr=[fake_ref(n) for n in ('synthetic.scope','synthetic.owner','synthetic.worker','synthetic.facts')]
        common=dict(step_id='W09-99',slice_id=m.SLICE,state=m.STATE,scope_ref=sr,output_root=output,routes=m.ROUTES,lease_status='ACTIVE',lease_expires_at=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat())
        owner=dict(common,owner_id=m.ROOT,selected_worker_id=m.ROOT);worker=dict(common,worker_id=m.ROOT,selected_owner_ref=orr)
        facts=dict(scope_ref=sr,owner_document_ref=orr,worker_document_ref=wr,source_hdf_ref=caller[0],source_review_decision_ref=rd)
        synthetic={sr['path']:scope,orr['path']:owner,wr['path']:worker}
        m.load=lambda ref:copy.deepcopy(synthetic[ref['path']]) if ref['path'] in synthetic else origload(ref)
        try:
            cp2,ow2=m.transformed_pair(copy.deepcopy(cp),copy.deepcopy(ow),facts,seed,cp,ow,fr)
            record('real Caller6 lease and complete inverse pure transform',cp2['revision']==370 and ow2['revision']==174 and len(cp2['failure_counters'])==993)
            record('old 963 failures all workers preserved',cp2['failure_counters'][:963]==cp['failure_counters'] and cp2['workers'][:-1]==cp['workers'])
            record('old CP369 pending four preserved',cp2['work_in_progress']['later_diagnostics_observed_after_cutoff'][:4]==cp['work_in_progress']['later_diagnostics_observed_after_cutoff'])
            record('single new worker owner two routes zero formal grant',len(cp2['workers'])==len(cp['workers'])+1 and ow2['card_path_bindings']['W09-99']['subtasks'][m.KEY]['routes']==m.ROUTES and scope['formal_acceptance'] is False and scope['parent_acceptance'] is False and scope['formal_case_accepted_delta']==0)
            cm=mod(caller[2]['path'])
            badcp=copy.deepcopy(cp2);badcp['workers'].append(copy.deepcopy(cp2['workers'][-1]))
            rejected('Caller6 duplicate worker reject',lambda:cm.validate_canon_lease(badcp,ow2,scope,sr,caller[0],rd,orr,wr,owner,worker,Path(output)/'child'),'CANON_WORKER_NOT_UNIQUE')
            expired=dict(owner,lease_expires_at='2020-01-01T00:00:00Z')
            rejected('Caller6 expired typed lease reject',lambda:cm.validate_canon_lease(cp2,ow2,scope,sr,caller[0],rd,orr,wr,expired,worker,Path(output)/'child'),'LEASE_EXPIRED')
        finally:m.load=origload
        record('no registrar entrypoint invoked',True,'Only read validators, held_guard and pure transformed_pair on copies; no build_root_docs/register/main/update_pair.')
        record('four Canon unchanged',[pin(p) for p in m.CANON]==before)
        for ref in refs:record('final pin '+Path(ref['path']).name,pin(ref['path'])==ref)
    finally:
        cleanup=guard.close();cleanup_ref=save('sourceguard.closed.json',cleanup)
    record('finite review guard closed zero',cleanup['closed'] is True and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
    controls=save('independent-controls.json',dict(schema='researchos.cp370-v3-independent-controls.v1',SyntheticNonAuthoritative=True,checks=checks,count=len(checks),guard_refs=count,pair_guard_refs=pair_count,actual_registrar_run=False,Main_or_Canon_written=False))
    findings=save('findings.json',dict(blocking_findings=[],closed_v2_root_causes=['F1 actual host binding and postreview provenance','F2 append-only immutable event continuity','F3 mutable pair excluded from nested SourceGuard'],scope_limit='Definition Source only. Future real Root seed/build facts/postseal inputs and actual registration are not reviewed or executed in this package.'))
    decision=dict(schema='researchos.w09-cp370-registrar-independent-source-decision.v1',decision='ACCEPTED_SOURCE_ONLY',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=m.AUTHOR,source_hdf_ref=hdfref,source_mf_ref=mfref,registrar_ref=source,root_contract_ref=hdf['root_contract_ref'],reviewed_at=datetime.now(timezone.utc).isoformat(),blocking_findings=0,findings_ref=findings,checks_ref=controls,source_guard_ref=cleanup_ref,pair_guard_ref=pair_cleanup_ref,actual_registration=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,Main_or_Canon_written=False,Native_or_dispatcher_executed=False,new_original_failures=[],Root_next_original_observed_before_review=1004,SourceAcceptedonly=True,noactualorformal=True)
    dr=save('source-decision.json',decision)
    mr=save('MF.json',dict(schema='researchos.cp370-registrar-independent-review-manifest.v1',source_hdf_ref=hdfref,source_mf_ref=mfref,members=[pin(__file__),controls,findings,cleanup_ref,pair_cleanup_ref,dr]))
    hr=save('HDF.json',dict(schema='researchos.cp370-registrar-independent-review-handoff.v1',decision=decision['decision'],actor_id=decision['actor_id'],actor_role=decision['actor_role'],manifest_ref=mr,source_decision_ref=dr,source_hdf_ref=hdfref,source_mf_ref=mfref,registrar_ref=source,root_contract_ref=hdf['root_contract_ref'],guard_ref_count=count,pair_guard_ref_count=pair_count,guard_closed=True,retained_handles_count=0,blocking_findings=0,checks=len(checks),Main_or_Canon_written=False,build_check_activate_executed=False,STOP=True,FINAL=True))
    for ref in (hr,mr,dr,*refs):assert pin(ref['path'])==ref
    print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,checks=len(checks),guard_refs=count,pair_guard_refs=pair_count),ensure_ascii=False))

if __name__=='__main__':main()
