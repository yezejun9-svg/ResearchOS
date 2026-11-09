"""Independent definition review; only own receipts are written. No registrar entrypoints."""
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
S = W / 'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v2'
SEED_REVIEW = W / 'cp370_prepared_root_inputs_independent_review_codex/seed996r-01a12072'
CALLER = W / 'w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v6'
CALLER_REVIEW = W / 'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
checks = []
findings = []

def pin(p):
    p = Path(p).resolve(strict=True)
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def read(p):
    return json.loads(Path(p).read_bytes())

def save(name, value):
    with (N / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode())
    return pin(N / name)

def record(name, ok, detail=None):
    checks.append(dict(name=name, passed=bool(ok), detail=detail))
    if not ok: raise AssertionError(name)

def rejected(name, callback, expected):
    try:
        callback()
    except ValueError as e:
        record(name, str(e)==expected, str(e))
    else:
        record(name, False, 'BAD_INPUT_ACCEPTED')

def mod(p):
    m=types.ModuleType('independent_'+Path(p).stem)
    m.__file__=str(p)
    exec(compile(Path(p).read_bytes(), str(p), 'exec'),m.__dict__)
    return m

def main():
    source=pin(S/'register_cp370.source.py')
    hdfref=pin(S/'HDF.json'); mfref=pin(S/'MF.json')
    record('exact handed off Source pins',hdfref['sha256']=='392b2ed96f86c05c7a64df153158a97d097bab3878000851d3bf8d813691b4f4'
           and hdfref['bytes']==2985 and mfref['sha256']=='d15edb65aa8f6ac91240e72a53c291dd4e8ef38f59e88b314372d57ad58dead4' and mfref['bytes']==6707)
    record('registrar exact', source['sha256']=='1a03c4d09987367af96184d216d2c7c2690c0f16eb79cca943e2075fc96e15f6' and source['bytes']==55259)
    hdf=read(hdfref['path']); mf=read(mfref['path'])
    m=mod(source['path'])
    refs=[hdfref,mfref,pin(__file__),pin(SEED_REVIEW/'HDF.json'),pin(SEED_REVIEW/'MF.json')]
    refs.extend(mf['members'])
    refs.extend({k:e[k] for k in ('path','sha256','bytes')} for e in read(hdf['guard_cleanup_ref']['path'])['entries'])
    refs.extend([pin(CALLER/'HDF.json'),pin(CALLER/'MF.json'),pin(CALLER_REVIEW/'HDF.json'),pin(CALLER_REVIEW/'MF.json')])
    refs.extend(m.embedded_refs(read(SEED_REVIEW/'HDF.json')))
    refs.extend(m.embedded_refs(read(CALLER/'HDF.json')))
    refs.extend(m.embedded_refs(read(CALLER_REVIEW/'HDF.json')))
    guard,count=m.held_guard(refs,False)
    try:
        record('Source HDF MF coherence',hdf['manifest_ref']==mfref and hdf['registrar_ref']==source and source in mf['members'])
        record('contract exact',hdf['root_contract_ref']['sha256']=='d813e55e13a1ed0fbde5e8d529b1edd0fe316e6700071e998016411ad783d3fe' and hdf['root_contract_ref']['bytes']==5907)
        for ref in mf['members']: record('Source manifest pin '+Path(ref['path']).name,pin(ref['path'])==ref)
        before,cp,ow=m.check_before_pair()
        record('Canon remains CP369 OW173',cp['revision']==369 and ow['revision']==173)
        caller=m.ensure_caller_source(pin(CALLER/'HDF.json'),pin(CALLER/'MF.json'))
        crh=read(CALLER_REVIEW/'HDF.json')
        request=dict(review_hdf_ref=pin(CALLER_REVIEW/'HDF.json'),review_mf_ref=pin(CALLER_REVIEW/'MF.json'),review_decision_ref=crh['source_decision_ref'])
        rh,rm,rd,decision=m.validate_review(request,caller)
        record('real final Caller v6 full review accepted',decision['actor_id']==m.DESIGNATED_REVIEWER)
        manifest=read(rm['path'])
        rejected('empty independent members rejected',lambda:m.validate_review_members(dict(manifest,members=[]),rd,caller),'REVIEW_MANIFEST_NOT_BOUND')
        for actor in ('/root',m.ROOT,m.AUTHOR,'codex:/root/other'):
            rejected('noncanonical reviewer '+actor,lambda actor=actor:m.validate_reviewer_actor(actor),'REVIEWER_NOT_CANONICAL_NONAUTHOR')
        for label,p in [('boundary',W),('dotdot',W/'SYNTHETIC_NOT_CREATED'/'..'),('outside',W.parent),('relative',Path('relative'))]:
            rejected('output '+label,lambda p=p:m.canonical_output_root(str(p)),'OUTPUT_ROOT_SCOPE')
        output=str((N/'synthetic-no-output').resolve())
        record('canonical strict child accepted',m.canonical_output_root(output)==output)
        qref=mf['qualification_seed_ref']; q=read(qref['path'])
        pending=read(q['source_pending_ref']['path'])['pending']
        seed=dict(schema='researchos.root-cp370-source-live-context.v2',issued_by=m.ROOT,root_thread_id=m.ROOT_THREAD_ID,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=q['source_cutoff'],next_original_failure_ordinal=q['next_original_failure_ordinal'],pending=[{k:r[k] for k in ('ordinal','origin_ref','description')} for r in pending],qualification_ref=qref,seed_witness_ref=mf['actual_seed_witness_ref'])
        qualified=m.validate_live(seed)
        witness,wrefs=m.validate_root_witness(seed['seed_witness_ref'],seed,'SEED')
        record('actual Seed996 qualified including real three audit ranges',len(qualified)==30)
        record('prior 166-check seed review reused exact',read(SEED_REVIEW/'HDF.json')['checks']==166 and read(SEED_REVIEW/'HDF.json')['decision']=='PREPARED_ROOT_SEED_INPUTS_VERIFIED_NONAUTHORITATIVE')
        record('shared origin different selector remains legal',qualified[971]['origin_ref']==qualified[972]['origin_ref'] and qualified[971]['origin_selector']!=qualified[972]['origin_selector'])
        pair=copy.deepcopy([qualified[971],qualified[972]]);pair[1]['origin_selector']=pair[0]['origin_selector']
        rejected('same event selector duplicate rejected',lambda:m.validate_invocation_identities(pair),'ORIGINAL_INVOCATION_REUSED')
        for ordinal,field,value in [(967,'actual_outer_exit',0),(967,'actual_native_exit',0)]:
            changed=copy.deepcopy(q);changed['rows'][ordinal-966][field]=value
            got=m.validate_qualification(changed,seed)
            record('counterexample preseal changed exit accepted '+field,got[ordinal][field]==value,dict(original=qualified[ordinal][field],accepted=value))
        findings.append(dict(id='F3',priority=1,title='Seed qualification exits are not tied to original audit output',lines=[315,342],evidence='For original 967, actual_outer_exit 1 to 0 and actual_native_exit null to 0 both pass validate_qualification. First four pending rows have no exit fields. Root witness never compares output qualification_ref/next_original with witness qualification_ref/next.',fix='Bind exact qualification ref and pending/current ordinal to actual Root host result; independently qualify legacy exits. Keep null unknown.'))
        for ordinal in (967,987):
            changed=copy.deepcopy(qualified);changed[ordinal]['actual_outer_exit']=0
            rejected('postseed exits cannot change '+str(ordinal),lambda changed=changed:m.validate_qualification_continuity(seed,qualified,seed,changed),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
        # Any added original requires a different exact pending document ref. Each prior
        # row must then rebind its diagnostic_source_ref to that ref by lines 332-334.
        fresh=copy.deepcopy(seed);fresh['next_original_failure_ordinal']=997
        fresh['pending'].append(dict(ordinal=996,origin_ref=source,description='synthetic new distinct event; not an actual failure'))
        new_pending_ref=dict(q['source_pending_ref'],sha256='a'*64)
        fresh_q=copy.deepcopy(qualified)
        for row in fresh_q.values(): row['exit_qualification']['diagnostic_source_ref']=new_pending_ref
        fresh_q[996]=dict(ordinal=996)
        rejected('legitimate append with required diagnostic ref rebinding is rejected',lambda:m.validate_qualification_continuity(seed,qualified,fresh,fresh_q),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
        findings.append(dict(id='F2',priority=1,title='Append-only qualification cannot pass fresh continuity',lines=[332,544],evidence='Qualification binds every row diagnostic_source_ref to current source_pending_ref. Adding ordinal 996 requires new pending ref, but continuity compares entire old row dicts, rejecting exactly this required ref change.',fix='Compare immutable event identity/exits/completeness/description per common ordinal; validate new diagnostic container reference separately and allow append-only new rows.'))
        # Replaying the *real* seed host bytes under new in-memory witness metadata.
        # Only this witness load is overlaid. Original raw logs/bindings still read live.
        origload=m.load
        overlay=copy.deepcopy(witness);overlay['phase']='POSTSEAL_ACTIVATION';overlay['registrar_review_refs']=[rh,rm,rd]
        overlay['created_utc']=datetime.now(timezone.utc).isoformat()
        fake_live=copy.deepcopy(seed);fake_live['created_utc']=(datetime.now(timezone.utc)+timedelta(microseconds=100)).isoformat()
        m.load=lambda ref: copy.deepcopy(overlay) if ref==seed['seed_witness_ref'] else origload(ref)
        try:
            replay,_=m.validate_root_witness(seed['seed_witness_ref'],fake_live,'POSTSEAL_ACTIVATION')
            record('real seed host pair replayed as postseal witness accepted',replay['actual_host_capture_ref']==witness['actual_host_capture_ref'])
        finally: m.load=origload
        m.validate_postseal_times('2026-10-09T12:25:00Z','2026-10-09T12:30:00Z','2026-10-09T12:31:00Z','2026-10-09T12:32:00Z')
        record('postseal checker has no audit event timestamp input',True,'Real seed output 12:19:34 precedes synthetic review 12:30; accepted witness metadata 12:31 masks old audit event.')
        m.validate_postseal_times('2026-10-09T12:30:00Z','2026-10-09T12:25:00Z','2026-10-09T12:31:00Z','2026-10-09T12:32:00Z')
        record('contract seed before review order missing',True)
        findings.append(dict(id='F1',priority=1,title='Postseal gate permits seed host pair replay',lines=[469,537],evidence='Real Seed996 raw audit pair passes validate_root_witness under only in-memory phase/reviewrefs/created time metadata overlay. Actual call/output time is never compared to reviewed_at; neither host ref nor call ID is required to differ from seed. Original args are not compared to actual host input. Source seed-after-review also passes time helper contrary to contract.',fix='Bind paired original call args and parsed actual result to qualification/cutoff/Canon/review triple. Require distinct actual host call after review seal; compare actual call/output timestamps, not witness declaration time.'))
        nested=list(m.embedded_refs(witness))
        record('register witness expansion reintroduces CP OW',before[0] in nested and before[1] in nested)
        rejected('register guard rejects mandatory nested witness references',lambda:m.held_guard(nested,True),'CANON_PAIR_ONLY_TRANSACTION')
        findings.append(dict(id='F4',priority=1,title='Mandatory nested Canon refs make check and activate fail before transaction',lines=[913,932],evidence='The exact Seed996 witness canonical_refs contains CP369/OW173. register expands witness/qualification embedded_refs then calls held_guard(exclude_pair=True), which deterministically raises CANON_PAIR_ONLY_TRANSACTION.',fix='Partition mutable CP/OW from immutable held source pins consistently after transitive expansion; preserve current-pair exact checks and transaction-owned compare-and-update locking. Do not omit all transitive pin protection.'))
        # Construct only in-memory objects using the exact Source builder expression.
        ch=read(CALLER/'HDF.json'); nh=read(ch['native_handoff_ref']['path'])
        tree=ast.parse(Path(source['path']).read_text(encoding='utf-8'))
        builder=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_root_docs')
        expression=next(n.value for n in builder.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scope' for t in n.targets))
        request.update(frozen_plan_ref=ch['frozen_plan_ref'],native_hdf_ref=ch['native_qualified_hdf_ref'],native_handoff_ref=ch['native_handoff_ref'],native_historical_request_ref=source,authorized_output_root=output)
        # This ref is a placeholder because validate_scope does not read Native inputs.
        scope=eval(compile(ast.Expression(expression),str(source['path']),'eval'),m.__dict__,dict(request=request,decision=decision,decision_ref=rd,caller=caller,refs=before))
        fake_ref=lambda name:dict(path=str(N/name),sha256='0'*64,bytes=0)
        sr,orr,wr,fr=[fake_ref(n) for n in ('synthetic.scope','synthetic.owner','synthetic.worker','synthetic.facts')]
        common=dict(step_id='W09-99',slice_id=m.SLICE,state=m.STATE,scope_ref=sr,output_root=output,routes=m.ROUTES,lease_status='ACTIVE',lease_expires_at=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat())
        owner=dict(common,owner_id=m.ROOT,selected_worker_id=m.ROOT)
        worker=dict(common,worker_id=m.ROOT,selected_owner_ref=orr)
        facts=dict(scope_ref=sr,owner_document_ref=orr,worker_document_ref=wr,source_hdf_ref=caller[0],source_review_decision_ref=rd)
        synthetic={sr['path']:scope,orr['path']:owner,wr['path']:worker}
        m.load=lambda ref: copy.deepcopy(synthetic[ref['path']]) if ref['path'] in synthetic else origload(ref)
        try:
            cp2,ow2=m.transformed_pair(copy.deepcopy(cp),copy.deepcopy(ow),facts,seed,cp,ow,fr)
            record('pure actual Caller6 lease and complete inverse passed',cp2['revision']==370 and ow2['revision']==174 and len(cp2['failure_counters'])==993)
            record('pure old workers 963 failures retained',cp2['workers'][:-1]==cp['workers'] and cp2['failure_counters'][:963]==cp['failure_counters'])
            record('pure prior pending four remain identical',cp2['work_in_progress']['later_diagnostics_observed_after_cutoff'][:4]==cp['work_in_progress']['later_diagnostics_observed_after_cutoff'])
            record('one owner worker two frozen routes no formal grant',len(cp2['workers'])==len(cp['workers'])+1 and ow2['card_path_bindings']['W09-99']['subtasks'][m.KEY]['routes']==['test.research.fixture','test.retrieval'] and scope['formal_case_accepted_delta']==0 and scope['formal_acceptance'] is False and scope['parent_acceptance'] is False)
            caller_module=mod(caller[2]['path'])
            badcp=copy.deepcopy(cp2);badcp['workers'].append(copy.deepcopy(cp2['workers'][-1]))
            rejected('Caller6 duplicate worker reject',lambda:caller_module.validate_canon_lease(badcp,ow2,scope,sr,caller[0],rd,orr,wr,owner,worker,Path(output)/'child'),'CANON_WORKER_NOT_UNIQUE')
            badowner=copy.deepcopy(owner);badowner['lease_expires_at']='2020-01-01T00:00:00Z'
            rejected('Caller6 expired typed lease reject',lambda:caller_module.validate_canon_lease(cp2,ow2,scope,sr,caller[0],rd,orr,wr,badowner,worker,Path(output)/'child'),'LEASE_EXPIRED')
        finally: m.load=origload
        record('four Canon exact after pure review',[pin(p) for p in m.CANON]==before)
        for ref in refs: record('final source pin '+Path(ref['path']).name,pin(ref['path'])==ref)
    finally:
        cleanup=guard.close()
        cleanup_ref=save('sourceguard.closed.json',cleanup)
    record('real finite SourceGuard closed',cleanup['closed'] is True and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
    findings_ref=save('findings.json',findings)
    failures=[]
    audit=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
    target_chunks={'6d29ff':1002,'6e5aa2':None}
    calls={}; header=None; offset=0
    with audit.open('rb') as stream:
        for line in stream:
            item=json.loads(line)
            payload=item.get('payload',{})
            if item.get('type')=='session_meta' and header is None: header=(offset,line)
            if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call': calls[payload['call_id']]=(offset,line)
            if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call_output':
                blocks=payload.get('output',[])
                if isinstance(blocks,list):
                    for block in blocks:
                        if not isinstance(block,dict) or not isinstance(block.get('text'),str): continue
                        try: actual=json.loads(block['text'])
                        except (ValueError,TypeError): continue
                        if isinstance(actual,dict) and actual.get('chunk_id') in target_chunks:
                            chunk=actual['chunk_id']; call=calls[payload['call_id']]
                            records=[header,call,(offset,line)]
                            capname='failure-'+chunk+'.actual-host.raw.jsonl'
                            with (N/capname).open('xb') as out: out.write(b''.join(r[1] for r in records))
                            cap=pin(N/capname)
                            binding=save('failure-'+chunk+'.binding.json',dict(source_audit_path=str(audit),source_line_offsets=[r[0] for r in records],source_line_bytes=[len(r[1]) for r in records],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in records],capture_ref=cap,call_id=payload['call_id'],actual_outer_exit=actual['exit_code'],actual_python_exit=None,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,rg_child_exit=None,Root_ordinal=target_chunks[chunk],args_and_result='Original unmodified host call input and output records in capture_ref; OS error 2 is not an observed child exit code.'))
                            failures.append(dict(chunk=chunk,capture_ref=cap,binding_ref=binding))
            offset+=len(line)
    record('two original failed read observations captured exactly',len(failures)==2)
    # Recheck the immutable source set after audit extraction too.
    record('four Canon unchanged at final seal',[pin(p) for p in m.CANON]==before)
    controls_ref=save('independent-controls.json',dict(SyntheticNonAuthoritative=True,checks=checks,check_count=len(checks),guard_ref_count=count,actual_registrar_run=False,build_check_activate_executed=False))
    d=dict(schema='researchos.w09-cp370-registrar-independent-source-decision.v1',decision='REQUEST_CHANGES',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=m.AUTHOR,source_hdf_ref=hdfref,source_mf_ref=mfref,registrar_ref=source,root_contract_ref=hdf['root_contract_ref'],reviewed_at=datetime.now(timezone.utc).isoformat(),blocking_findings=4,findings_ref=findings_ref,checks_ref=controls_ref,source_guard_ref=cleanup_ref,actual_registration=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,Main_or_Canon_written=False,Native_or_dispatcher_executed=False,new_original_failures=failures)
    dr=save('source-decision.json',d)
    mm=save('MF.json',dict(schema='researchos.cp370-registrar-independent-review-manifest.v1',source_hdf_ref=hdfref,source_mf_ref=mfref,members=[pin(__file__),controls_ref,findings_ref,cleanup_ref,dr,*[f[k] for f in failures for k in ('capture_ref','binding_ref')]]))
    hh=save('HDF.json',dict(schema='researchos.cp370-registrar-independent-review-handoff.v1',decision='REQUEST_CHANGES',actor_id=d['actor_id'],actor_role=d['actor_role'],manifest_ref=mm,source_decision_ref=dr,source_hdf_ref=hdfref,source_mf_ref=mfref,registrar_ref=source,root_contract_ref=hdf['root_contract_ref'],guard_ref_count=count,guard_closed=True,retained_handles_count=0,blocking_findings=4,checks=len(checks),Main_or_Canon_written=False,build_check_activate_executed=False,STOP=True,FINAL=True))
    print(json.dumps(dict(HDF=hh,MF=mm,decision=dr,checks=len(checks),blocking_findings=4,guard_refs=count),ensure_ascii=False))

if __name__=='__main__': main()
