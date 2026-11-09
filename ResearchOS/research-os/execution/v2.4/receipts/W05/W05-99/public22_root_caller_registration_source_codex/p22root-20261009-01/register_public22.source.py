"""Root-only CP371/OW175 public22 registrar. No action on import.

build creates owner then worker documents; check is read-only for Canon;
activate uses the accepted canonical update_pair transaction. This Source
neither creates Root external review facts nor grants execution by itself.
"""
import copy
import hashlib
import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

R=Path(r'D:\作品集\ResearchOS\research-os')
V=R/'execution/v2.4'
B=V/'receipts/W05/W05-99'
W=V/'receipts/W09/W09-99'
N=Path(__file__).resolve().parent
CANON=[V/(x+'.json') for x in ('checkpoint','path_ownership','step_state','commands')]
BEFORE=[('a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994',4489310),
        ('a612b51f23a5157aff5b99817caa09fb634a67c70879c56430daa4690d1da0bc',208629),
        ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
        ('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
ROOT_INPUT=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
ROOT='codex:/root'
AUTHOR='codex:/root/w09_formal_profile_source_impl'
SLICE='PUBLIC22_BOOTSTRAP_BACKUP_VERIFY'
KEY='public22_bootstrap_backup_verify'
STATE='ROOT_REGISTERED_PENDING_PUBLIC22_ACTUAL'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
EXPECTED_TP=('094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',6877)
EXPECTED_GUARD=('e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
RUNNER_REVIEW=(B/'public22_runner_independent_source_review_codex/pub22r-20261009-02/HDF.json',
               'e5f5611c4ebae96a3fc640fde86543e44b134812904736cf4021edfe60aadd31',3281)
BASE_PENDING=(ROOT_INPUT/'pending-diagnostics.cp370.live1013.root.json',
              '4013a2f77a6dced4e369159f84afc2d507b88519c7534c0a437c2fb380464005',8152)

def need(ok,code):
    if not ok:raise ValueError(code)

def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()

def pin(path):
    p=Path(path)
    need(p.is_absolute() and not p.is_symlink(),'PIN_PATH')
    p=p.resolve(strict=True);need(p.is_file() and not p.is_symlink(),'PIN_FILE')
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def exact(ref):
    need(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'REF_SHAPE')
    need(pin(ref['path'])==ref,'REF_CHANGED')
    return ref

def read(ref):return json.loads(Path(exact(ref)['path']).read_bytes())

def save(name,value):
    path=N/name
    with path.open('xb') as f:f.write(encoded(value))
    return pin(path)

def load_module(ref,name):
    m=types.ModuleType(name)
    exec(compile(Path(exact(ref)['path']).read_bytes(),ref['path'],'exec'),m.__dict__)
    return m

def before():
    refs=[pin(p) for p in CANON]
    need([(r['sha256'],r['bytes']) for r in refs]==BEFORE,'BEFORE_FULL4_DRIFT')
    cp,ow=map(lambda p:json.loads(p.read_bytes()),CANON[:2])
    need(cp.get('revision')==370 and ow.get('revision')==174 and
         ow.get('active_integrator',{}).get('id')==ROOT,'BEFORE_REVISIONS_OWNER')
    need(len(cp['failure_counters'])==1002 and
         cp['work_in_progress'].get('root_next_failure_ordinal_live')==1005,
         'BEFORE_FAILURE_CUTOFF')
    need(KEY not in ow['card_path_bindings']['W05-99']['subtasks'] and
         not any(type(w) is dict and w.get('slice_id')==SLICE for w in cp['workers']) and
         'public22_root_scope_ref' not in cp['work_in_progress'],
         'PUBLIC22_ALREADY_REGISTERED')
    return refs,cp,ow

def locked_python():
    lock=read(pin(R/'execution/toolchains/locked.json'))['tools']['python']
    current=pin(sys.executable)
    need(current['path']==lock['path'] and current['sha256']==lock['sha256'],
         'LOCKED_PYTHON_DRIFT')
    return current

def verify_source(request):
    hdf_ref=exact(request['source_hdf_ref']);hdf=read(hdf_ref)
    mf_ref=exact(hdf['manifest_ref']);mf=read(mf_ref)
    need(hdf.get('status')=='SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_AND_ROOT_REGISTRATION'
         and hdf.get('caller_ref')==pin(N/'public22_root_caller.source.py')
         and hdf.get('registrar_ref')==pin(__file__)
         and hdf.get('contract_ref')==pin(N/'root-calling-contract.source.json')
         and hdf.get('runner_review_ref')==pin(RUNNER_REVIEW[0])
         and request['source_mf_ref']==mf_ref,
         'CALLER_SOURCE_HANDOFF')
    need((hdf['runner_review_ref']['sha256'],hdf['runner_review_ref']['bytes'])==RUNNER_REVIEW[1:]
         and mf.get('excludes')==['MF.json','HDF.json'], 'RUNNER_REVIEW_OR_MANIFEST')
    for ref in mf['members']:exact(ref)
    decision_ref=exact(request['review_decision_ref']);decision=read(decision_ref)
    review_hdf_ref=exact(request['review_hdf_ref']);review_hdf=read(review_hdf_ref)
    review_mf_ref=exact(request['review_mf_ref']);review_mf=read(review_mf_ref)
    need(review_hdf.get('manifest_ref')==review_mf_ref and
         review_hdf.get('source_decision_ref')==decision_ref and
         review_hdf.get('actor_role')=='INDEPENDENT_NON_AUTHOR' and
         review_hdf.get('source_hdf_ref')==hdf_ref and
         review_hdf.get('source_mf_ref')==mf_ref and
         type(review_mf.get('members')) is list and
         all(exact(ref) for ref in review_mf['members']) and
         hdf_ref in review_mf['members'] and mf_ref in review_mf['members'],
         'REVIEW_HDF_MF_BINDING')
    witness_ref=exact(request['review_hostpair_binding_ref']);witness=read(witness_ref)
    need(Path(witness_ref['path']).parent==ROOT_INPUT and
         witness.get('issued_by')==ROOT and
         witness.get('review_hdf_ref')==review_hdf_ref and
         witness.get('review_mf_ref')==review_mf_ref and
         witness.get('review_decision_ref')==decision_ref and
         witness.get('original_capture_ref') is not None and
         witness.get('original_call_id') is not None,
         'ROOT_EXTERNAL_REVIEW_HOSTPAIR')
    exact(witness['original_capture_ref'])
    reviewer=decision.get('actor_id')
    need(decision.get('decision')=='ACCEPTED_SOURCE_ONLY' and
         decision.get('actor_role')=='INDEPENDENT_NON_AUTHOR' and
         reviewer not in (None,'',ROOT,AUTHOR) and
         reviewer==review_hdf.get('actor_id') and
         decision.get('source_author_id')==AUTHOR and
         decision.get('source_hdf_ref')==hdf_ref and
         decision.get('source_mf_ref')==mf_ref and
         decision.get('caller_ref')==hdf['caller_ref'] and
         decision.get('registrar_ref')==hdf['registrar_ref'] and
         decision.get('formal_acceptance') is False and
         decision.get('execution_grant') is False,
         'NONAUTHOR_REVIEW_NOT_BOUND')
    return hdf,mf_ref,decision_ref,reviewer

def pending(live_ref):
    live=read(live_ref);base=read({'path':str(BASE_PENDING[0]),
                                  'sha256':BASE_PENDING[1],'bytes':BASE_PENDING[2]})
    need(Path(live_ref['path']).parent==ROOT_INPUT and
         live.get('issued_by')==ROOT and live.get('source_cutoff')==base['source_cutoff'] and
         live.get('counter_reset') is False and
         live.get('registered_in_current_canon') is False and
         type(live.get('pending')) is list and
         live['pending'][:8]==base['pending'] and
         [x.get('ordinal') for x in live['pending']]==list(range(1005,live['next_original_failure_ordinal'])) and
         live['next_original_failure_ordinal']>=1013,
         'ROOT_PENDING_FULL_PREFIX')
    for row in live['pending']:
        exact(row['origin_ref'])
        if row.get('capture_binding_ref') is not None:
            binding=read(row['capture_binding_ref'])
            need(binding.get('original_capture_ref',row['origin_ref'])==row['origin_ref'],
                 'ORIGINAL_CAPTURE_BINDING')
        for field in ('actual_outer_exit','actual_python_exit','actual_native_exit',
                      'actual_dispatcher_exit','actual_model_exit'):
            value=row.get(field)
            need(value is None or type(value) is int,'UNKNOWN_EXIT_MUST_BE_NULL')
    return live

def root_build_request(ref):
    request=read(ref)
    need(Path(ref['path']).parent==ROOT_INPUT and
         request.get('schema')=='researchos.root-public22-registration-build.v1' and
         request.get('issued_by')==ROOT and
         request.get('before_canonical_refs')==[pin(p) for p in CANON] and
         request.get('source_hdf_ref') and request.get('source_mf_ref') and
         request.get('review_decision_ref') and request.get('review_hdf_ref') and
         request.get('review_mf_ref') and request.get('review_hostpair_binding_ref') and
         request.get('root_resume_ref') and request.get('reviewed_root_live_ref') and
         request.get('pending_ref') and
         request.get('case_request_ref') and
         request.get('formal_acceptance') is False and
         request.get('parent_acceptance') is False,
         'ROOT_BUILD_REQUEST')
    resume=read(request['root_resume_ref'])
    need(resume.get('checkpoint_revision')==370 and
         resume.get('ownership_revision')==174 and
         resume.get('commands_revision')==39 and
         resume.get('canonical_refs')==request['before_canonical_refs'] and
         resume.get('issued_by')==ROOT,'ROOT_RESUME_NOT_CURRENT')
    reviewed_live_ref=exact(request['reviewed_root_live_ref'])
    reviewed_live=read(reviewed_live_ref)
    review_hdf=read(request['review_hdf_ref'])
    def when(value):
        need(type(value) is str,'ROOT_LIVE_TIME')
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        need(dt.tzinfo is not None,'ROOT_LIVE_TIMEZONE')
        return dt
    need(Path(reviewed_live_ref['path']).parent==ROOT_INPUT and
         reviewed_live.get('issued_by')==ROOT and
         reviewed_live.get('root_resume_ref')==request['root_resume_ref'] and
         reviewed_live.get('review_decision_ref')==request['review_decision_ref'] and
         reviewed_live.get('current_canonical_refs')==request['before_canonical_refs'] and
         when(reviewed_live.get('created_utc'))>when(review_hdf.get('reviewed_utc')) and
         when(request.get('created_utc'))>=when(reviewed_live.get('created_utc')),
         'ROOT_POSTREVIEW_LIVE_REFRESH')
    case=read(request['case_request_ref'])
    need(type(case) is dict and set(case)=={'case_id','output_root','end_version'} and
         type(case.get('case_id')) is str and re_fullcase(case['case_id']) and
         case.get('end_version')==22 and case.get('output_root')==request.get('output_root'),
         'ROOT_CASE_REQUEST')
    root=Path(request['output_root'])
    receipt=Path(request['caller_receipt_root'])
    parent=B/'integration_codex'
    need(root.is_absolute() and receipt.is_absolute() and
         root.parent==parent and receipt.parent==parent and root!=receipt and
         root.name=='schema22-public-'+case['case_id'] and
         receipt.name=='schema22-public-caller-'+case['case_id'] and
         parent.resolve(strict=True)==parent and
         not parent.is_symlink() and not parent.is_junction() and
         not root.exists() and not receipt.exists() and
         request['lease_expires_at'] and
         datetime.fromisoformat(request['lease_expires_at'].replace('Z','+00:00'))>
             datetime.now(timezone.utc),'ROOT_OUTPUT_LEASE_SCOPE')
    pending(request['pending_ref'])
    verify_source(request)
    return request

def re_fullcase(value):
    import re
    return re.fullmatch('[0-9a-f]{32}',value) is not None

def build(build_ref):
    refs,_,_=before()
    locked_python()
    request=root_build_request(build_ref)
    hdf,mf_ref,decision_ref,reviewer=verify_source(request)
    common=dict(step_id='W05-99',slice_id=SLICE,state=STATE,
        scope_ref=None,output_root=request['output_root'],owner=ROOT,
        lease_status='ACTIVE',lease_expires_at=request['lease_expires_at'])
    # The scope has no owner/worker refs; owner is sealed before worker selects it.
    scope=dict(schema='researchos.root-public22-scope.v1',issued_by=ROOT,
        slice_id=SLICE,end_version=22,case_id=read(request['case_request_ref'])['case_id'],
        output_root=request['output_root'],caller_receipt_root=request['caller_receipt_root'],
        case_request_ref=request['case_request_ref'],source_hdf_ref=hdf['runner_review_ref'],
        runner_contract_ref=read(hdf['runner_review_ref'])['contract_ref'],
        caller_hdf_ref=request['source_hdf_ref'],caller_mf_ref=mf_ref,
        caller_review_ref=decision_ref,caller_reviewer=reviewer,
        caller_review_hdf_ref=request['review_hdf_ref'],
        caller_review_mf_ref=request['review_mf_ref'],
        root_review_hostpair_binding_ref=request['review_hostpair_binding_ref'],
        calling_contract_ref=hdf['contract_ref'],registrar_ref=hdf['registrar_ref'],
        formal_acceptance=False,parent_acceptance=False)
    scope_ref=save('scope-registration.root.json',scope)
    common['scope_ref']=scope_ref
    owner_ref=save('owner-document.root.json',dict(common,owner_id=ROOT,
              selected_worker_id=ROOT))
    worker_ref=save('worker-document.root.json',dict(common,worker_id=ROOT,
               selected_owner_ref=owner_ref))
    facts_ref=save('registration-facts.root.json',dict(
        schema='researchos.root-public22-registration-facts.v1',issued_by=ROOT,
        created_utc=request['created_utc'],before_canonical_refs=refs,
        build_request_ref=build_ref,root_resume_ref=request['root_resume_ref'],
        reviewed_root_live_ref=request['reviewed_root_live_ref'],
        pending_ref=request['pending_ref'],scope_ref=scope_ref,
        owner_ref=owner_ref,worker_ref=worker_ref,
        source_hdf_ref=request['source_hdf_ref'],source_mf_ref=mf_ref,
        review_hdf_ref=request['review_hdf_ref'],review_mf_ref=request['review_mf_ref'],
        review_hostpair_binding_ref=request['review_hostpair_binding_ref'],
        review_decision_ref=decision_ref,source_reviewer=reviewer,
        first_actual_request='NOT_CREATED',formal_acceptance=False,parent_acceptance=False))
    return facts_ref

def transform(old_cp,old_ow,facts,facts_ref,live):
    cp=copy.deepcopy(old_cp);ow=copy.deepcopy(old_ow)
    scope=read(facts['scope_ref']);owner=read(facts['owner_ref']);worker=read(facts['worker_ref'])
    need(worker['selected_owner_ref']==facts['owner_ref'] and
         owner['selected_worker_id']==worker['worker_id']==ROOT and
         facts['before_canonical_refs']==[pin(p) for p in CANON],
         'OWNER_WORKER_ACYCLIC')
    need(KEY not in ow['card_path_bindings']['W05-99']['subtasks'] and
         not any(x.get('slice_id')==SLICE for x in cp['workers']),
         'DUPLICATE_PUBLIC22_SLICE')
    task=dict(owner,current_source_writer=None,
        source_handoff_ref=facts['source_hdf_ref'],source_review_ref=facts['review_decision_ref'],
        owner_document_ref=facts['owner_ref'],worker_document_ref=facts['worker_ref'],
        formal_case_accepted_delta=0,parent_acceptance=False)
    worker_row=dict(worker,source_handoff_ref=facts['source_hdf_ref'],
        source_review_ref=facts['review_decision_ref'],worker_document_ref=facts['worker_ref'])
    ow['card_path_bindings']['W05-99']['subtasks'][KEY]=task
    cp['workers'].append(worker_row)
    seen={(row.get('original_payload',{}).get('immutable_origin_ref',{}).get('sha256'),
           row.get('original_payload',{}).get('origin_selector'))
          for row in cp['failure_counters']}
    for row in live['pending']:
        identity=(row['origin_ref']['sha256'],row['origin_selector'])
        need(identity not in seen,'ORIGINAL_INVOCATION_REUSED');seen.add(identity)
        payload=dict(observed_ordinal=row['ordinal'],immutable_origin_ref=row['origin_ref'],
            origin_selector=row['origin_selector'],capture_completeness=row['capture_completeness'],
            capture_binding_ref=row['capture_binding_ref'],
            actual_outer_exit=row['actual_outer_exit'],actual_python_exit=row['actual_python_exit'],
            actual_native_exit=row['actual_native_exit'],
            actual_dispatcher_exit=row['actual_dispatcher_exit'],
            actual_model_exit=row['actual_model_exit'],diagnostic=row['description'])
        cp['failure_counters'].append(dict(
            origin_key=hashlib.sha256((identity[0]+'#'+identity[1]).encode()).hexdigest(),
            evidence_ref=row['origin_ref'],original_payload=payload,
            counted_once=True,counter_reset=False,automatic_retry=False))
    need(cp['failure_counters'][:len(old_cp['failure_counters'])]==old_cp['failure_counters'],
         'HISTORICAL_FAILURE_ROWS_CHANGED')
    cp['work_in_progress']['public22_root_scope_ref']=facts['scope_ref']
    cp['work_in_progress']['public22_registration_facts_ref']=facts_ref
    cp['work_in_progress']['root_next_failure_ordinal_live']=live['next_original_failure_ordinal']
    cp['work_in_progress']['later_diagnostics_observed_after_cutoff'].extend(
        {k:copy.deepcopy(row[k]) for k in ('ordinal','origin_ref','description')}
        for row in live['pending'])
    cp.update(revision=371,expected_previous_revision=370,
              updated_at=facts['created_utc'],updated_by=ROOT,
              note='Root registered public22 Source-only actual caller; no product run or formal acceptance.')
    ow.update(revision=175,updated_at=facts['created_utc'],updated_by=ROOT)
    inverse_cp=copy.deepcopy(cp); inverse_ow=copy.deepcopy(ow)
    for k in ('failure_counters','workers','work_in_progress','revision',
              'expected_previous_revision','updated_at','updated_by','note'):
        inverse_cp[k]=copy.deepcopy(old_cp[k])
    del inverse_ow['card_path_bindings']['W05-99']['subtasks'][KEY]
    for k in ('revision','updated_at','updated_by'):
        inverse_ow[k]=copy.deepcopy(old_ow[k])
    need(encoded(inverse_cp)==encoded(old_cp) and encoded(inverse_ow)==encoded(old_ow),
         'INVERSE_FULL_BEFORE_PAIR')
    return cp,ow

def register(mode,facts_ref,live_ref):
    need(mode in ('check','activate'),'MODE')
    locked_python()
    refs,old_cp,old_ow=before();facts=read(facts_ref)
    need(Path(facts_ref['path']).parent==N and
         facts.get('schema')=='researchos.root-public22-registration-facts.v1' and
         facts.get('issued_by')==ROOT and facts.get('before_canonical_refs')==refs and
         facts.get('formal_acceptance') is False and
         facts.get('parent_acceptance') is False and
         facts.get('first_actual_request')=='NOT_CREATED',
         'ROOT_FACTS_NOT_BOUND')
    build_request=root_build_request(facts['build_request_ref'])
    need(facts['root_resume_ref']==build_request['root_resume_ref'] and
         facts['reviewed_root_live_ref']==build_request['reviewed_root_live_ref'] and
         facts['source_hdf_ref']==build_request['source_hdf_ref'] and
         facts['review_hdf_ref']==build_request['review_hdf_ref'] and
         facts['review_mf_ref']==build_request['review_mf_ref'] and
         facts['review_hostpair_binding_ref']==build_request['review_hostpair_binding_ref'] and
         facts['review_decision_ref']==build_request['review_decision_ref'] and
         facts['scope_ref']==pin(N/'scope-registration.root.json') and
         facts['owner_ref']==pin(N/'owner-document.root.json') and
         facts['worker_ref']==pin(N/'worker-document.root.json'),
         'ROOT_BUILD_FACTS_DRIFT')
    live=pending(live_ref)
    if mode=='check':
        need(live_ref==facts['pending_ref'],'CHECK_NOT_SOURCE_LIVE')
    else:
        need(live_ref!=facts['pending_ref'] and
             live.get('activation_witness_ref') is not None and
             live.get('review_decision_ref')==facts['review_decision_ref'] and
             live.get('scope_ref')==facts['scope_ref'],
             'ACTIVATION_REQUIRES_FRESH_ROOT_LIVE')
        witness=read(live['activation_witness_ref'])
        refreshed=read(facts['reviewed_root_live_ref'])
        need(witness.get('issued_by')==ROOT and
             witness.get('source_review_ref')==facts['review_decision_ref'] and
             witness.get('scope_ref')==facts['scope_ref'] and
             witness.get('external_hostpair_ref') is not None and
             datetime.fromisoformat(witness['created_utc'].replace('Z','+00:00'))>
                 datetime.fromisoformat(refreshed['created_utc'].replace('Z','+00:00')),
             'ACTIVATION_WITNESS_NOT_BOUND')
        exact(witness['external_hostpair_ref'])
    hdf,_,_,_=verify_source(build_request)
    mf=read(facts['source_mf_ref']);runner_review=read(hdf['runner_review_ref'])
    runner_mf=read(runner_review['manifest_ref'])
    source_guard=load_module(pin(GUARD),'public22_registration_guard')
    runtime=[facts_ref,live_ref,facts['build_request_ref'],facts['root_resume_ref'],
        facts['reviewed_root_live_ref'],
        facts['pending_ref'],facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],
        facts['source_hdf_ref'],facts['source_mf_ref'],facts['review_decision_ref'],
        facts['review_hdf_ref'],facts['review_mf_ref'],facts['review_hostpair_binding_ref'],
        hdf['runner_review_ref'],pin(__file__),locked_python(),
        pin(R/'execution/toolchains/locked.json'),pin(GUARD),pin(TP),*refs[2:]]
    runtime.extend(mf['members']);runtime.extend(runner_mf['members'])
    runtime.extend(read(facts['review_mf_ref'])['members'])
    runtime.append(read(facts['review_hostpair_binding_ref'])['original_capture_ref'])
    runtime.extend(row['origin_ref'] for row in live['pending'])
    runtime.extend(row['capture_binding_ref'] for row in live['pending']
                   if row['capture_binding_ref'] is not None)
    runtime.extend([pin(p) for p in CANON[2:]])
    for mod in tuple(sys.modules.values()):
        for key in ('__file__','__cached__'):
            p=getattr(mod,key,None)
            if p and Path(p).is_file():runtime.append(pin(p))
    merged={}
    for ref in runtime:
        exact(ref);key=ref['path'].casefold()
        need(key not in merged or merged[key]==ref,'CONFLICTING_HELD_RESOURCE')
        merged[key]=ref
    held=source_guard.SourceReadGuard(per_file_cap=512*1024*1024,
                                      total_cap=2*1024*1024*1024)
    held.acquire(list(merged.values()))
    transaction=None
    try:
        after=transform(old_cp,old_ow,facts,facts_ref,live)
        if mode=='activate':
            need((pin(TP)['sha256'],pin(TP)['bytes'])==EXPECTED_TP,'UPDATE_PAIR_DRIFT')
            tp=load_module(pin(TP),'public22_canonical_transaction')
            transaction=tp.update_pair(refs[:2],
                lambda cp,ow:transform(cp,ow,facts,facts_ref,live),N,'activate')
            need([pin(p) for p in CANON[2:]]==refs[2:],'SS_CM_CHANGED')
        else:need([pin(p) for p in CANON]==refs,'CHECK_MUTATED_CANON')
    finally:
        cleanup=held.close()
        save('source-guard.cleanup.'+mode+'.root.json',cleanup)
        need(cleanup['closed'] and cleanup['retained_handles_count']==0 and
             cleanup['errors']==[],'REGISTER_HELD_GUARD_NOT_CLOSED')
    return save('registration.'+mode+'.root.json',dict(
        schema='researchos.root-public22-registration-result.v1',mode=mode,
        scope_ref=facts['scope_ref'],source_review_ref=facts['review_decision_ref'],
        proposed_after_refs=[{'path':str(p),'sha256':hashlib.sha256(encoded(v)).hexdigest(),
                              'bytes':len(encoded(v))}
                             for p,v in zip(CANON[:2],after)],
        transaction=transaction,complete_inverse=True,
        old_failure_rows_preserved=1002,new_originals_registered=len(live['pending']),
        next_original_failure_ordinal=live['next_original_failure_ordinal'],
        SS_CM_unchanged=True,product_processes=0,formal_acceptance=False,
        parent_acceptance=False))

if __name__=='__main__':
    # Root launcher passes exact JSON refs; no author-side execution here.
    need(len(sys.argv)==8,'USAGE_mode_input3_live3')
    mode=sys.argv[1]
    first={'path':sys.argv[2],'sha256':sys.argv[3],'bytes':int(sys.argv[4])}
    live={'path':sys.argv[5],'sha256':sys.argv[6],'bytes':int(sys.argv[7])}
    result=build(first) if mode=='build' else register(mode,first,live)
    print(json.dumps(result,ensure_ascii=False),flush=True)
