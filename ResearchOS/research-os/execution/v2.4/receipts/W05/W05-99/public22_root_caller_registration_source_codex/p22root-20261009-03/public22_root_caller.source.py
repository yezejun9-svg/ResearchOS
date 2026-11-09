"""Root-only public schema22 caller. Import and Source review perform no product work.

The runner is a leaf: this caller supplies a live, non-JSON capability whose
registration/lease is rechecked against current Canon before every phase.
"""
import hashlib
import json
import ntpath
import re
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

R=Path(r'D:\作品集\ResearchOS\research-os')
V=R/'execution/v2.4'
B=V/'receipts/W05/W05-99'
N=Path(__file__).resolve().parent
ROOT_INPUT=V/'receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
CANON=[V/(x+'.json') for x in ('checkpoint','path_ownership','step_state','commands')]
SLICE='PUBLIC22_BOOTSTRAP_BACKUP_VERIFY'
KEY='public22_bootstrap_backup_verify'
STATE='ROOT_REGISTERED_PENDING_PUBLIC22_ACTUAL'
AUTHOR='codex:/root/w09_formal_profile_source_impl'
ROOT='codex:/root'
PHASES=('prepare','bootstrap22','keygen22','backup22','verify22')
EXPECTED_SOURCE_HDF=('e5f5611c4ebae96a3fc640fde86543e44b134812904736cf4021edfe60aadd31',3281)
EXPECTED_RUNNER=('c157e0a213406267d56d3f24ee07092413c26bb3c6bafaf9ac5469fbf4829da7',24984)
EXPECTED_CONTRACT=('24d24cf6535b79355ad0a4e9a9ef518b93039f4c67bd01ad74cae5d66a127976',10863)

def need(ok,code):
    if not ok: raise ValueError(code)

def strict(raw):
    def pairs(rows):
        out={}
        for k,v in rows:
            need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,
                      parse_constant=lambda x:need(False,'NONFINITE_JSON_NUMBER'))

def regular_path(path):
    need(type(path) is str and path and not any(ord(c)<32 for c in path),'REF_PATH')
    value=path.replace('/','\\')
    drive,tail=ntpath.splitdrive(value)
    need(re.fullmatch('[A-Za-z]:',drive) is not None and tail.startswith('\\')
         and not tail.startswith('\\\\') and ':' not in tail,'REF_LOCAL_PATH')
    parts=tail[1:].split('\\')
    need(all(x and x not in ('.','..') and not x.endswith((' ','.'))
             and re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?',x) is None
             for x in parts),'REF_REGULAR_PATH')
    return ntpath.normcase(ntpath.normpath(value))

def same_ref(left,right):
    return (regular_path(left['path'])==regular_path(right['path']) and
            left['sha256']==right['sha256'] and left['bytes']==right['bytes'])

def pin(path):
    p=Path(path)
    lexical=regular_path(str(p))
    need(p.is_absolute() and not p.is_symlink(),'PIN_PATH')
    p=p.resolve(strict=True)
    need(p.is_file() and not p.is_symlink() and regular_path(str(p))==lexical,
         'PIN_NOT_FILE')
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def checked(ref):
    need(type(ref) is dict and set(ref)=={'path','sha256','bytes'} and
         type(ref['path']) is str and type(ref['sha256']) is str and
         re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None and
         type(ref['bytes']) is int and 0<=ref['bytes']<=512*1024*1024,
         'REF_SHAPE')
    actual=pin(ref['path'])
    need(same_ref(actual,ref),'REF_CHANGED')
    return Path(ref['path']).read_bytes()

def doc(ref): return strict(checked(ref))

def module(ref,name):
    m=types.ModuleType(name)
    exec(compile(checked(ref),ref['path'],'exec'),m.__dict__)
    return m

def unique_refs(refs):
    seen={}
    for ref in refs:
        checked(ref)
        key=regular_path(ref['path'])
        need(key not in seen or same_ref(seen[key],ref),'CONFLICTING_REF')
        seen[key]=ref
    return list(seen.values())

def save_new(path,value):
    with Path(path).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(path)

def resolve_runner_source_hdf(review_hdf,runner_ref,contract_ref):
    source_hdf=doc(review_hdf['source_hdf_ref'])
    need(source_hdf.get('schema')=='researchos.schema22-public-runner-source-handoff.v2'
         and all(type(source_hdf.get(k)) is dict for k in
                 ('manifest_ref','runner_ref','contract_ref','source_inputs_ref'))
         and same_ref(source_hdf['manifest_ref'],review_hdf['source_mf_ref'])
         and same_ref(source_hdf['runner_ref'],runner_ref)
         and same_ref(source_hdf['contract_ref'],contract_ref),
         'RUNNER_SOURCE_HDF_BINDING')
    source_mf=doc(source_hdf['manifest_ref'])
    need(type(source_mf.get('members')) is list and
         all(any(same_ref(source_hdf[k],m) for m in source_mf['members'])
             for k in ('runner_ref','contract_ref','source_inputs_ref')),
         'RUNNER_SOURCE_MANIFEST_BINDING')
    checked(source_hdf['source_inputs_ref'])
    return source_hdf

def source_and_review(scope):
    hdf_ref=scope['source_hdf_ref']; hdf=doc(hdf_ref)
    need((hdf_ref['sha256'],hdf_ref['bytes'])==EXPECTED_SOURCE_HDF,'RUNNER_REVIEW_PIN')
    need(hdf['decision']=='ACCEPTED_SOURCE_ONLY' and hdf['formal_acceptance'] is False
         and hdf['actor_role']=='INDEPENDENT_NON_AUTHOR' and hdf['actor_id']!=ROOT,
         'RUNNER_NOT_INDEPENDENTLY_REVIEWED')
    runner_ref=hdf['runner_ref']; contract_ref=hdf['contract_ref']
    need((runner_ref['sha256'],runner_ref['bytes'])==EXPECTED_RUNNER and
         (contract_ref['sha256'],contract_ref['bytes'])==EXPECTED_CONTRACT,
         'RUNNER_EXACT_SOURCE')
    checked(hdf['manifest_ref']); checked(runner_ref); checked(contract_ref)
    runner_source_hdf=resolve_runner_source_hdf(hdf,runner_ref,contract_ref)
    review=doc(scope['caller_review_ref']); source=doc(scope['caller_hdf_ref'])
    mf=doc(source['manifest_ref'])
    review_hdf=doc(scope['caller_review_hdf_ref'])
    review_mf=doc(scope['caller_review_mf_ref'])
    review_host=doc(scope['root_review_hostpair_binding_ref'])
    need(review_hdf.get('manifest_ref')==scope['caller_review_mf_ref'] and
         review_hdf.get('source_decision_ref')==scope['caller_review_ref'] and
         review_hdf.get('source_hdf_ref')==scope['caller_hdf_ref'] and
         review_hdf.get('source_mf_ref')==scope['caller_mf_ref'] and
         review_hdf.get('actor_id')==scope['caller_reviewer'] and
         type(review_mf.get('members')) is list and
         scope['caller_hdf_ref'] in review_mf['members'] and
         scope['caller_mf_ref'] in review_mf['members'] and
         review_host.get('issued_by')==ROOT and
         review_host.get('review_hdf_ref')==scope['caller_review_hdf_ref'] and
         review_host.get('review_mf_ref')==scope['caller_review_mf_ref'] and
         review_host.get('review_decision_ref')==scope['caller_review_ref'] and
         review_host.get('original_capture_ref') is not None,
         'ROOT_EXTERNAL_REVIEW_NOT_BOUND')
    checked(review_host['original_capture_ref'])
    need(source['caller_ref']==pin(__file__) and source['contract_ref']==scope['calling_contract_ref']
         and source['registrar_ref']==scope['registrar_ref'] and
         mf['members'] and scope['caller_mf_ref']==source['manifest_ref'],
         'CALLER_SOURCE_MANIFEST')
    need(review.get('decision')=='ACCEPTED_SOURCE_ONLY' and
         review.get('actor_role')=='INDEPENDENT_NON_AUTHOR' and
         review.get('actor_id')==scope['caller_reviewer'] and
         review.get('actor_id') not in (AUTHOR,ROOT) and
         review.get('source_author_id')==AUTHOR and
         review.get('source_hdf_ref')==scope['caller_hdf_ref'] and
         review.get('source_mf_ref')==scope['caller_mf_ref'] and
         review.get('caller_ref')==pin(__file__) and
         review.get('registrar_ref')==scope['registrar_ref'] and
         review.get('formal_acceptance') is False and
         review.get('execution_grant') is False,
         'CALLER_REVIEW_NOT_BOUND')
    for ref in mf['members']+review_mf['members']: checked(ref)
    return hdf,runner_ref,contract_ref,mf,runner_source_hdf

def live_lease(scope_ref,request_ref,owner_ref,worker_ref,vector_ref,output_root,
               require_new=False):
    scope=doc(scope_ref); owner_doc=doc(owner_ref); worker_doc=doc(worker_ref)
    need(scope.get('schema')=='researchos.root-public22-scope.v1' and
         scope.get('issued_by')==ROOT and scope.get('slice_id')==SLICE and
         scope.get('end_version')==22 and scope.get('output_root')==output_root and
         scope.get('formal_acceptance') is False and
         scope.get('parent_acceptance') is False, 'SCOPE_INVALID')
    source_and_review(scope)
    vector=doc(vector_ref)
    refs=[pin(p) for p in CANON]
    need(vector.get('refs')==refs and vector.get('checkpoint_revision')==371 and
         vector.get('path_ownership_revision')==175 and
         vector.get('commands_revision')==39,'CURRENT_CANON_VECTOR_DRIFT')
    cp,ow=map(strict,(p.read_bytes() for p in CANON[:2]))
    need(cp.get('revision')==371 and ow.get('revision')==175 and
         cp.get('work_in_progress',{}).get('public22_root_scope_ref')==scope_ref,
         'CURRENT_CANON_REGISTRATION')
    need(ow.get('active_integrator',{}).get('id')==ROOT,'ROOT_NOT_ACTIVE_INTEGRATOR')
    card=ow.get('card_path_bindings',{}).get('W05-99',{})
    task=card.get('subtasks',{}).get(KEY)
    workers=[x for x in cp.get('workers',[]) if type(x) is dict and
             x.get('step_id')=='W05-99' and x.get('slice_id')==SLICE]
    need(type(task) is dict and len(workers)==1,'PUBLIC22_CANON_LEASE_ABSENT')
    worker=workers[0]
    for row in (task,worker,owner_doc,worker_doc):
        need(row.get('slice_id')==SLICE and row.get('state')==STATE and
             row.get('scope_ref')==scope_ref and row.get('output_root')==output_root and
             row.get('lease_status')=='ACTIVE' and row.get('owner',ROOT)==ROOT,
             'PUBLIC22_LEASE_BINDING')
        try: expiry=datetime.fromisoformat(row['lease_expires_at'].replace('Z','+00:00'))
        except (KeyError,ValueError) as exc: raise ValueError('PUBLIC22_LEASE_TIME') from exc
        need(expiry.tzinfo is not None and expiry>datetime.now(timezone.utc),'PUBLIC22_LEASE_EXPIRED')
    need(task.get('owner_document_ref')==owner_ref and task.get('worker_document_ref')==worker_ref
         and worker.get('selected_owner_ref')==owner_ref and
         worker.get('worker_document_ref')==worker_ref and
         owner_doc.get('selected_worker_id')==worker_doc.get('worker_id')==ROOT and
         worker_doc.get('selected_owner_ref')==owner_ref and
         task.get('source_review_ref')==scope['caller_review_ref'] and
         worker.get('source_review_ref')==scope['caller_review_ref'] and
         task.get('source_handoff_ref')==scope['caller_hdf_ref'] and
         worker.get('source_handoff_ref')==scope['caller_hdf_ref'],
         'PUBLIC22_OWNER_WORKER_NOT_BOUND')
    need(scope.get('case_request_ref')==request_ref and
         doc(request_ref)=={'case_id':scope['case_id'],'output_root':output_root,'end_version':22},
         'PUBLIC22_CASE_REQUEST_CHANGED')
    if require_new: need(not Path(output_root).exists(),'PUBLIC22_OUTPUT_ALREADY_EXISTS')
    return scope,vector

class LiveScope:
    """Constructed only after current Canon/review/closure validation."""
    def __init__(self,scope_ref,case_ref,owner_ref,worker_ref,vector_ref,output_root,
                 held,context):
        self.args=(scope_ref,case_ref,owner_ref,worker_ref,vector_ref,output_root)
        self.held=held; self.context=context; self.next_phase=0
    def _fresh(self):
        need(self.held is not None,'ROOT_HELD_CLOSURE_RELEASED')
        return live_lease(*self.args)[0]
    def require_registered(self,contract_ref,request_ref,source_author):
        scope=self._fresh()
        need(contract_ref==scope['runner_contract_ref'] and
             request_ref==self.args[1] and
             source_author=='codex:/root/native_temp_independent_review',
             'ROOT_RUNNER_REGISTRATION_MISMATCH')
    def require_phase(self,phase,request_ref,exact_output_root):
        self._fresh()
        need(request_ref==self.args[1] and exact_output_root==self.args[5] and
             self.next_phase<len(PHASES) and phase==PHASES[self.next_phase],
             'ROOT_PHASE_OR_SCOPE_MISMATCH')
        self.next_phase+=1
    def receipt_context(self): return self.context
    def qualified_current_main23(self,*unused):
        raise ValueError('MAIN23_NOT_QUALIFIED_FOR_THIS_END22_SCOPE')

def execute(root_request_ref):
    """Root runtime entry after registration. Root records outer tool hostpair separately."""
    root_request=doc(root_request_ref)
    need(Path(root_request_ref['path']).parent==ROOT_INPUT and
         root_request.get('schema')=='researchos.root-public22-actual-request.v1' and
         root_request.get('issued_by')==ROOT and root_request.get('end_version')==22,
         'ROOT_ACTUAL_REQUEST')
    scope_ref=root_request['scope_ref']; case_ref=root_request['case_request_ref']
    owner_ref=root_request['owner_ref']; worker_ref=root_request['worker_ref']
    vector_ref=root_request['current_canonical_vector_ref']
    output_root=root_request['output_root']
    scope,_=live_lease(scope_ref,case_ref,owner_ref,worker_ref,vector_ref,output_root,
                       require_new=True)
    need(root_request.get('source_review_ref')==scope['caller_review_ref'] and
         root_request.get('runner_contract_ref')==scope['runner_contract_ref'],
         'ROOT_ACTUAL_SOURCE_OR_HOST_INTENT')
    registration=doc(root_request['registration_result_ref'])
    need(Path(root_request['registration_result_ref']['path'])==N/'registration.activate.root.json' and
         registration.get('mode')=='activate' and
         registration.get('scope_ref')==scope_ref and
         registration.get('source_review_ref')==scope['caller_review_ref'] and
         registration.get('complete_inverse') is True and
         registration.get('SS_CM_unchanged') is True and
         registration.get('proposed_after_refs')==[pin(p) for p in CANON[:2]] and
         registration.get('transaction') is not None and
         registration.get('formal_acceptance') is False,
         'ROOT_ACTIVATION_RESULT_NOT_CURRENT')
    intent=doc(root_request['host_call_intent_ref'])
    need(Path(root_request['host_call_intent_ref']['path']).parent==ROOT_INPUT and
         intent.get('issued_by')==ROOT and intent.get('case_request_ref')==case_ref
         and intent.get('scope_ref')==scope_ref and
         intent.get('kind')=='ACTUAL_HOST_CALL_INTENT' and
         intent.get('external_hostpair_required') is True,
         'ROOT_HOST_CALL_INTENT_NOT_BOUND')
    runner_review,runner_ref,contract_ref,caller_mf,runner_source_hdf=source_and_review(scope)
    need(contract_ref==scope['runner_contract_ref'],'RUNNER_CONTRACT_SCOPE')
    source_mf=doc(runner_source_hdf['manifest_ref'])
    source_inputs=doc(runner_source_hdf['source_inputs_ref'])
    locked_ref=pin(R/'execution/toolchains/locked.json')
    locked=doc(locked_ref)
    python_ref=pin(sys.executable)
    need(python_ref['path']==locked['tools']['python']['path'] and
         python_ref['sha256']==locked['tools']['python']['sha256'],
         'LOCKED_PYTHON_DRIFT')
    refs=[root_request_ref,scope_ref,case_ref,owner_ref,worker_ref,vector_ref,
          root_request['registration_result_ref'],root_request['host_call_intent_ref'],
          scope['caller_review_ref'],scope['caller_hdf_ref'],scope['caller_mf_ref'],
          scope['caller_review_hdf_ref'],scope['caller_review_mf_ref'],
          scope['root_review_hostpair_binding_ref'],
          scope['calling_contract_ref'],scope['registrar_ref'],runner_review['manifest_ref'],
          runner_review['source_hdf_ref'],runner_source_hdf['manifest_ref'],
          runner_ref,contract_ref,runner_source_hdf['source_inputs_ref'],python_ref,
          locked_ref,
          pin(V/'../project_identity.json'),*[pin(p) for p in CANON]]
    refs.extend(caller_mf['members']);refs.extend(source_mf['members'])
    refs.extend(doc(scope['caller_review_mf_ref'])['members'])
    refs.append(doc(scope['root_review_hostpair_binding_ref'])['original_capture_ref'])
    refs.extend(source_inputs['references'])
    contract=doc(contract_ref)
    refs.extend(contract[k] for k in ('old22_control','old22_backup','source_guard','owned_job'))
    guard_module=module(contract['source_guard'],'public22_root_guard')
    job_module=module(contract['owned_job'],'public22_root_owned_job')
    refs.extend(pin(p) for p in job_module.runtime_resource_paths())
    for m in tuple(sys.modules.values()):
        for attr in ('__file__','__cached__'):
            p=getattr(m,attr,None)
            if p and Path(p).is_file():refs.append(pin(p))
    held=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,
                                      total_cap=2*1024*1024*1024)
    held.acquire(unique_refs(refs))
    receipt_root=Path(scope['caller_receipt_root'])
    state=None; error=None; cleanup=None
    try:
        live_lease(scope_ref,case_ref,owner_ref,worker_ref,vector_ref,output_root)
        need(not receipt_root.exists() and receipt_root.parent.is_dir() and
             not receipt_root.parent.is_symlink() and
             not receipt_root.parent.is_junction(),
             'CALLER_RECEIPT_ROOT_NOT_FRESH')
        receipt_root.mkdir()
        live=LiveScope(scope_ref,case_ref,owner_ref,worker_ref,vector_ref,output_root,
                       held,{'root_request_ref':root_request_ref,'scope_ref':scope_ref,
                             'registration_result_ref':root_request['registration_result_ref'],
                             'host_call_intent_ref':root_request['host_call_intent_ref'],
                             'source_review_ref':scope['caller_review_ref']})
        runner=module(runner_ref,'public22_reviewed_runner')
        state=runner.run_registered_case(contract_ref,case_ref,live)
    except BaseException as exc:
        error={'type':type(exc).__name__,'message':str(exc),'phase':'root_caller',
               'last_child_exit':None,'original_ordinal':None,
               'Root_assignment_required':True}
    finally:
        try: cleanup=held.close()
        except BaseException as exc:
            cleanup={'closed':False,'error':{'type':type(exc).__name__,
                                            'message':str(exc)}}
            if error is None:
                error={'type':type(exc).__name__,'message':str(exc),
                       'phase':'root_source_guard_close','last_child_exit':None,
                       'original_ordinal':None,'Root_assignment_required':True}
    record={'schema':'researchos.root-public22-caller-return.v1',
            'root_request_ref':root_request_ref,'case_request_ref':case_ref,
            'runner_returned_state':state,'caller_error':error,
            'source_guard_cleanup':cleanup,'external_original_hostpair_required':True,
            'original_failure_assignment_required':bool(error or
                (state and state.get('first_failure'))),
            'formal_acceptance':False,'parent_acceptance':False}
    if receipt_root.is_dir():
        record['return_record_ref']=save_new(receipt_root/'caller-return.root.json',record)
        if state is not None and (state.get('closed_receipt',{}).get('status')!=
                                  'PUBLISHED' or state.get('first_failure')):
            record['persisted_returned_state_ref']=save_new(
                receipt_root/'runner-returned-state.root.json',state)
    return record

if __name__=='__main__':
    need(len(sys.argv)==4,'USAGE_root_request_path_sha_bytes')
    request_ref={'path':sys.argv[1],'sha256':sys.argv[2],'bytes':int(sys.argv[3])}
    print(json.dumps(execute(request_ref),ensure_ascii=False),flush=True)
