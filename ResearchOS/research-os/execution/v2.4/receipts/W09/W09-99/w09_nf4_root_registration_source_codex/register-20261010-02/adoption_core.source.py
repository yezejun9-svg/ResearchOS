"""Pure value rules for future Root adoption; no I/O or authority on import."""
import copy,hashlib,json,re
from datetime import datetime,timezone

ROOT='codex:/root'
AUTHOR='codex:/root/attach_restore_independent_review'
GENERATION='fullw09-20261010-05'
QKEY='w09_profile_cm40_adoption'
QSLICE='W09_PROFILE_CM40_ADOPTION'
QSTATE='ROOT_REGISTERED_PENDING_W09_PROFILE_ADOPTION'
QDONE='ROOT_ADOPTED_W09_PROFILE_CM40'
NKEY='full_w09_main_native_producer_fullw09-20261010-05'
NSLICE='FULL_W09_MAIN_NATIVE_PRODUCER_fullw09-20261010-05'
NSTATE='ROOT_REGISTERED_PENDING_SELECTOR_NATIVE'
SELECTORS=('W09-G01','W09-G02','A06','C19')
FALSE_FIELDS=('formal_acceptance','parent_acceptance','formal_dispatcher','automatic_retry')
ZERO_FIELDS=('formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes')
EXIT_FIELDS=('actual_outer_exit','actual_python_exit','actual_native_exit','actual_Go_exit','actual_SQLite_exit','actual_dispatcher_exit','actual_model_exit')

def require(ok,code):
    if not ok:raise ValueError(code)

def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin_raw(path,raw):return dict(path=str(path),sha256=sha(raw),bytes=len(raw))

def ref_shape(ref):
    require(type(ref) is dict and set(ref)=={'path','sha256','bytes'}
        and type(ref['path']) is str and bool(ref['path']) and type(ref['sha256']) is str
        and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None
        and type(ref['bytes']) is int and 0<=ref['bytes']<=512*1024*1024,'EXACT_PUBLIC_REF')
    return ref

def utc(value):
    require(type(value) is str,'TIME_STRING')
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None,'TIMEZONE_REQUIRED')
    return result

def validate_lease(lease,now,created=None):
    require(type(lease) is dict and set(lease)=={'lease_id','lease_issued_at','lease_expires_at'},'LEASE_FIELDS')
    issued,expires=utc(lease['lease_issued_at']),utc(lease['lease_expires_at'])
    require(type(lease['lease_id']) is str and re.fullmatch('[0-9a-f]{32}',lease['lease_id']) is not None,'LEASE_ID')
    require(0<(expires-issued).total_seconds()<=3600 and issued<=now<expires,'CURRENT_FINITE_LEASE')
    if created is not None:require(issued<=created<=now and created<expires,'CREATION_WITHIN_CURRENT_LEASE')

def validate_times(created,root_audit_time,source_audit_times,lease,now):
    created=utc(created);observed=utc(root_audit_time)
    validate_lease(lease,now,created)
    require(created<=observed<=now,'ACTUAL_ROOT_AUDIT_CAUSAL_TIME')
    require(type(source_audit_times) is list and len(source_audit_times)>=4
            and all(utc(t)<=created for t in source_audit_times),'SOURCE_PEER_PROOFS_PRECEDE_ROOT_REQUEST')

def check_no_grant(document):
    require(all(document.get(k) is False for k in FALSE_FIELDS),'NO_FORMAL_OR_RETRY_GRANT')
    require(all(type(document.get(k)) is int and document[k]==0 for k in ZERO_FIELDS),'EXACT_ZERO_BOUNDARIES')

def validate_peer_roles(profile_author,profile_reviewer,producer_author,producer_reviewer):
    actors=(profile_author,profile_reviewer,producer_author,producer_reviewer)
    require(all(type(x) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*',x) for x in actors),'ACTUAL_PEER_ACTORS')
    require(profile_author!=profile_reviewer and producer_author!=producer_reviewer,'NONAUTHOR_SOURCE_REVIEW')

def validate_own_review(decision,href,mref,bindings):
    actor=decision.get('actor_id')
    require(decision.get('schema')=='researchos.w09-nf4-registration-independent-source-decision.v1'
        and decision.get('decision')=='SOURCE_ACCEPTED_FOR_ROOT_NF4_REGISTRATION'
        and decision.get('actor_role')=='INDEPENDENT_NON_AUTHOR'
        and type(actor) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*',actor)
        and actor not in (AUTHOR,ROOT) and decision.get('source_author_id')==AUTHOR
        and decision.get('source_handoff_ref')==href and decision.get('source_manifest_ref')==mref
        and all(decision.get(k)==v for k,v in bindings.items())
        and decision.get('actual_executed') is False and decision.get('formal_acceptance') is False
        and decision.get('execution_grant') is False,'OWN_NONAUTHOR_REVIEW_NO_GRANT')
    return actor

def merge_pending(cp,pending,current4):
    """Append a complete contiguous suffix; never reconstruct or reset old rows."""
    require(type(cp.get('failure_counters')) is list and type(cp.get('work_in_progress')) is dict,'CANON_COUNTER_LAYOUT')
    start=cp['work_in_progress'].get('root_next_failure_ordinal_live')
    require(type(start) is int and start>0,'CURRENT_NEXT_ORDINAL_EXACT_INT')
    require(pending.get('schema')=='researchos.root-pending-diagnostics.v1' and pending.get('issued_by')==ROOT
            and pending.get('counter_reset') is False and pending.get('registered_in_current_canon') is False
            and pending.get('current_canonical_refs')==current4,'CURRENT_ROOT_PENDING')
    cutoff=pending.get('source_cutoff_original_failure_ordinal');stop=pending.get('next_original_failure_ordinal')
    rows=pending.get('pending')
    require(type(cutoff) is int and cutoff==start-1 and type(stop) is int and stop>=start
            and type(rows) is list and len(rows)==stop-start,'COUNTER_NONDECREASE_AND_LENGTH')
    require(all(type(row) is dict and type(row.get('ordinal')) is int for row in rows)
            and [row['ordinal'] for row in rows]==list(range(start,stop)),'COUNTER_CONTIGUOUS_EXACT_INT')
    old=cp['failure_counters'];seen=set();ordinals=set()
    for entry in old:
        payload=entry.get('original_payload',{})
        ordinal=payload.get('observed_ordinal')
        if ordinal is not None:
            require(type(ordinal) is int and ordinal<start,'PRIOR_ORDINAL_BOUNDS')
            require(ordinal not in ordinals,'PRIOR_DUPLICATE_ORDINAL');ordinals.add(ordinal)
        origin=payload.get('immutable_origin_ref');selector=payload.get('origin_selector')
        if type(origin) is dict and type(selector) is str:
            seen.add((origin.get('sha256'),selector))
    merged=copy.deepcopy(old)
    for row in rows:
        ref=ref_shape(row.get('origin_ref'));selector=row.get('origin_selector')
        require(type(selector) is str and bool(selector),'ORIGINAL_SELECTOR_REQUIRED')
        identity=(ref['sha256'],selector)
        require(identity not in seen,'ORIGINAL_INVOCATION_DUPLICATE');seen.add(identity)
        require(type(row.get('description')) is str and bool(row['description']),'ORIGINAL_DESCRIPTION_REQUIRED')
        ref_shape(row.get('capture_binding_ref'))
        require(all(k in row and (row[k] is None or type(row[k]) is int) for k in EXIT_FIELDS),'UNKNOWN_EXITS_MUST_REMAIN_NULL')
        payload={k:copy.deepcopy(row[k]) for k in EXIT_FIELDS}
        payload.update(observed_ordinal=row['ordinal'],immutable_origin_ref=copy.deepcopy(ref),origin_selector=selector,
            capture_binding_ref=copy.deepcopy(row['capture_binding_ref']),diagnostic=row['description'])
        if 'capture_completeness' in row:payload['capture_completeness']=copy.deepcopy(row['capture_completeness'])
        merged.append(dict(origin_key=sha((ref['sha256']+'#'+selector).encode()),evidence_ref=copy.deepcopy(ref),
            original_payload=payload,counted_once=True,counter_reset=False,automatic_retry=False))
    require(merged[:len(old)]==old,'ORIGINAL_COUNTER_PREFIX_UNCHANGED')
    return merged,stop




def make_native_scopes(request,pins,choice,contract):
    out={}
    require(set(request['native_leases'])==set(SELECTORS),'FOUR_NATIVE_LEASES')
    require(len({v['lease_id'] for v in request['native_leases'].values()})==4,'DISTINCT_SELECTOR_LEASES')
    for selector in SELECTORS:
        c={**choice['common'],**choice['selectors'][selector]}
        scope=dict(schema=contract['scope_schema'],status='ROOT_AUTHORIZED_SINGLE_SELECTOR_NATIVE',issued_by=ROOT,executor=ROOT,
            source_handoff_ref=pins['NF_hdf'],source_manifest_ref=pins['NF_mf'],
            source_review_handoff_ref=pins['NR_hdf'],source_review_manifest_ref=pins['NR_mf'],source_review_decision_ref=pins['NR_decision'],
            source_author_audit_ref=request['reviewed_source_audit_refs']['producer-author'],
            source_review_audit_ref=request['reviewed_source_audit_refs']['producer-review'])
        scope.update(copy.deepcopy(contract['bound_source_refs']))
        for key in ('selector_key','selector','mode','native_scope','packages','source_root','run_id','receipt_root','scratch_root',
                    'output_root','selected_tests','expected_native_ids','source21','generation','resource_parent_ref','resource_owner_ref','resource_audit_ref'):
            scope[key]=copy.deepcopy(c[key])
        scope.update(copy.deepcopy(request['native_leases'][selector]))
        scope.update(list_timeout_seconds=240,producer_timeout_seconds=420,inner_Go_timeout_seconds=180,
                     maximum_go_test_runs=1,maximum_go_list_runs=1)
        for name in ('formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry'):
            scope[name]=False
        for name in ZERO_FIELDS:scope[name]=0
        require(set(scope)==set(contract['scope_required_fields']),'EXACT_NF4_SCOPE_FIELDS')
        out[selector]=scope
    return out

def native_owner_worker(scope,scope_ref):
    owner=dict(generation=scope['generation'],owner=ROOT,current_source_writer=None,state=NSTATE,scope_ref=scope_ref,
        source_handoff_ref=scope['source_handoff_ref'],source_manifest_ref=scope['source_manifest_ref'],
        source_review_handoff_ref=scope['source_review_handoff_ref'],source_review_manifest_ref=scope['source_review_manifest_ref'],
        source_root=scope['source_root'],selector=scope['selector_key'],run_id=scope['run_id'],receipt_root=scope['receipt_root'],
        scratch_root=scope['scratch_root'],output_root=scope['output_root'],lease_id=scope['lease_id'],
        lease_issued_at=scope['lease_issued_at'],lease_expires_at=scope['lease_expires_at'],formal_case_accepted_delta=0,parent_acceptance=False)
    worker=dict(generation=scope['generation'],step_id='W09-99',slice_id=NSLICE+'_'+scope['selector_key'],owner=ROOT,state=NSTATE,scope_ref=scope_ref,
        source_handoff_ref=scope['source_handoff_ref'],source_review_handoff_ref=scope['source_review_handoff_ref'],
        run_id=scope['run_id'],lease_id=scope['lease_id'])
    return owner,worker

def value_at(document,path):
    current=document
    for key in path[:-1]:current=current[key]
    key=path[-1]
    return (key in current,copy.deepcopy(current.get(key)))

def put(document,path,value,exists=True):
    current=document
    for key in path[:-1]:current=current[key]
    if exists:current[path[-1]]=copy.deepcopy(value)
    else:del current[path[-1]]

def apply_operations(before,operations):
    after=copy.deepcopy(before)
    for op in operations:
        exists,value=value_at(after,op['path'])
        require(exists==op['before_exists'] and value==op['before'],'PATCH_BEFORE_VALUE')
        put(after,op['path'],op['after'])
    return after

def inverse_operations(after,operations):
    restored=copy.deepcopy(after)
    for op in reversed(operations):
        exists,value=value_at(restored,op['path'])
        require(exists and value==op['after'],'INVERSE_AFTER_VALUE')
        put(restored,op['path'],op['before'],op['before_exists'])
    return restored

def canonical_changes(cp,ow,request,scope_refs,scopes,pending,archives,own,commit_ref=None):
    """Only append NF4 generation slots; all historical scopes and counters survive."""
    require(type(cp['revision']) is int and type(ow['revision']) is int,'EXACT_CANON_REVISIONS')
    require(cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
        and ow['active_integrator']['id']==ROOT and ow['shared_integrator']=='qoder-desktop:/root/platform_owner'
        and ow['card_path_bindings']['W09-99']['owner']==ROOT,'CURRENT_ROOT_ROLE')
    require(request['kind']=='NATIVE_SCOPES' and request['generation']==GENERATION and commit_ref is not None,'NF4_ONLY_NO_MAIN_ADOPTION')
    require(type(cp['workers']) is list and set(scopes)==set(scope_refs)==set(SELECTORS),'EXACT_FOUR_SCOPES')
    merged,next_ordinal=merge_pending(cp,pending,request['before_canonical_refs'])
    co=[];oo=[];work=copy.deepcopy(cp);owners=copy.deepcopy(ow)
    def change(doc,ops,path,value):
        exists,before=value_at(doc,path);op=dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value))
        ops.append(op);put(doc,path,value)
    workers=copy.deepcopy(cp['workers']);subtasks=ow['card_path_bindings']['W09-99']['subtasks']
    require(subtasks[QKEY]['state']==QDONE,'ALREADY_ADOPTED_CURRENT_PROFILE')
    prior=cp['work_in_progress']['w09_native_producer_scopes']
    require(set(prior)=={'W09-G01','W09-G02','A06'},'PRESERVED_OLD_THREE_SCOPES')
    for selector in ('W09-G01','W09-G02','A06'):
        old_owner=subtasks['full_w09_main_native_producer_'+selector]
        old_workers=[x for x in workers if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_'+selector]
        require(len(old_workers)==1,'UNIQUE_OLD_NATIVE_WORKER')
        old_worker=old_workers[0]
        require(old_owner['scope_ref']==old_worker['scope_ref']==prior[selector]
            and old_owner['state']==old_worker['state']
            and old_owner['state'] in ('CLOSED_QUALIFIED_HISTORICAL_SOURCE_CHANGED','CLOSED_ACTUAL_NATIVE_FAILED'),'OLD_NATIVE_MUST_BE_CLOSED')
        for record in (old_owner,old_worker):
            require(record['actual_closed']['all_guards_closed'] is True
                and record['actual_closed']['all_owned_jobs_closed'] is True,'OLD_NATIVE_RESOURCES_CLOSED')
        require(all(scopes[k]['run_id']!=old_worker['run_id'] for k in SELECTORS),'NEW_RUN_IDS_ONLY')
    generations=copy.deepcopy(cp['work_in_progress'].get('w09_native_producer_scope_generations',{}))
    registrations=copy.deepcopy(cp['work_in_progress'].get('w09_nf4_scope_registrations',{}))
    require(type(generations) is dict and type(registrations) is dict
        and GENERATION not in generations and GENERATION not in registrations,'FRESH_FOUR_SELECTOR_GENERATION')
    for selector in SELECTORS:
        require(scopes[selector]['generation']==GENERATION,'EXACT_SCOPE_GENERATION')
        require(NKEY+'_'+selector not in subtasks
            and not any(x.get('slice_id')==NSLICE+'_'+selector for x in workers),'FRESH_GENERATION_OWNER_WORKER')
        owner,worker=native_owner_worker(scopes[selector],scope_refs[selector]);workers.append(worker)
        change(owners,oo,['card_path_bindings','W09-99','subtasks',NKEY+'_'+selector],owner)
    generations[GENERATION]=copy.deepcopy(scope_refs)
    registrations[GENERATION]=dict(scope_refs=copy.deepcopy(scope_refs),before_canonical_archive_refs=archives,
        pending_ref=request['pending_ref'],profile_adoption_ref=commit_ref,
        source_handoff_ref=own['hdf'],source_review_decision_ref=own['decision'],
        formal_case_accepted_delta=0,parent_acceptance=False)
    if merged!=cp['failure_counters']:change(work,co,['failure_counters'],merged)
    change(work,co,['work_in_progress','root_next_failure_ordinal_live'],next_ordinal)
    change(work,co,['work_in_progress','w09_native_producer_scope_generations'],generations)
    change(work,co,['work_in_progress','w09_nf4_scope_registrations'],registrations)
    change(work,co,['workers'],workers)
    for key,value in dict(revision=cp['revision']+1,expected_previous_revision=cp['revision'],updated_at=request['created_utc'],
        updated_by=ROOT,note='Root bounded NF4 four-selector generation registration; no formal acceptance.').items():change(work,co,[key],value)
    for key,value in dict(revision=ow['revision']+1,updated_at=request['created_utc'],updated_by=ROOT).items():change(owners,oo,[key],value)
    require(inverse_operations(work,co)==cp and inverse_operations(owners,oo)==ow,'COMPLETE_STRUCTURAL_INVERSE')
    require(work['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters'],'ALL_OLD_FAILURES_UNCHANGED')
    require(work['work_in_progress']['w09_native_producer_scopes']==prior,'OLD_SCOPE_REFS_UNCHANGED')
    return work,owners,co,oo
