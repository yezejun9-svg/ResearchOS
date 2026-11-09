"""Reviewed Source for future Root-only registration and existing-artifact reads.

Import is inert. Future Root execution permits exactly three new public children.
"""
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

R=Path('D:/作品集/ResearchOS/research-os');V=R/'execution/v2.4';B=V/'receipts/W05/W05-99'
N=Path(__file__).resolve().parent
ROOT='codex:/root';AUTHOR='codex:/root/attach_restore_independent_review'
LEAF_AUTHOR='codex:/root/w09_formal_profile_source_impl'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT_AUDIT=r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'
CANON=[V/(name+'.json') for name in ('checkpoint','path_ownership','step_state','commands')]
KEY='public22_to_main23_continuation';SLICE='PUBLIC22_TO_MAIN23_CONTINUATION'
STATE='ROOT_REGISTERED_PUBLIC22_TO_MAIN23_CONTINUATION';MODE='PUBLIC22_TO_MAIN23_CONTINUATION_ONLY'
GUARD_REF=dict(path=str(B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
TP_REF=dict(path=str(B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=6877)
MAX=512*1024*1024

def need(ok,code):
    if not ok:raise ValueError(code)
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def strict(raw):
    def pairs(values):
        out={}
        for k,v in values:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'NONFINITE_JSON'))
def canonical(path):
    need(type(path) is str and ntpath.isabs(path) and '..' not in Path(path).parts,'ABSOLUTE_NORMAL_PATH')
    return ntpath.normcase(ntpath.normpath(path))
def shape(ref):
    need(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'EXACT_REF')
    canonical(ref['path'])
    need(type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256']) and type(ref['bytes']) is int and 0<=ref['bytes']<=MAX,'TYPED_REF')
    return ref
def same(a,b):
    shape(a);shape(b)
    return canonical(a['path'])==canonical(b['path']) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def physical(path,absent=False):
    canonical(str(path));p=Path(path)
    for item in reversed((p,*p.parents)):
        if not item.exists():need(absent and item==p,'MISSING_PARENT');continue
        need(not item.is_symlink() and not item.is_junction() and not(getattr(item.lstat(),'st_file_attributes',0)&0x400),'REPARSE_FORBIDDEN')
    need(canonical(str(p.resolve(strict=not absent)))==canonical(str(p)),'PATH_ALIAS')
    return p
def checked(ref):
    shape(ref);p=physical(ref['path']);need(p.is_file(),'REGULAR_FILE')
    with p.open('rb') as f:raw=f.read(ref['bytes']+1)
    need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'REF_DRIFT')
    return raw
def pin(path):
    p=physical(path);need(p.is_file(),'PIN_FILE')
    with p.open('rb') as f:raw=f.read(MAX+1)
    need(len(raw)<=MAX,'PIN_CAP');return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(ref):return strict(checked(ref))
def load(ref,name):
    m=types.ModuleType(name);m.__file__=ref['path'];exec(compile(checked(ref),ref['path'],'exec'),m.__dict__);return m
def save(root,name,value):
    need(Path(name).name==name,'RECEIPT_NAME');p=physical(root)/name;physical(p,True)
    with p.open('xb') as f:f.write(encoded(value));f.flush();os.fsync(f.fileno())
    return pin(p)
def refs_unique(refs,exclude=()):
    skipped={canonical(str(p)) for p in exclude};out={}
    for ref in refs:
        key=canonical(shape(ref)['path'])
        if key in skipped:continue
        checked(ref);need(key not in out or same(out[key],ref),'CONFLICTING_REFS');out.setdefault(key,ref)
    return list(out.values())
def pair(href,mref):
    h=doc(href);m=doc(mref);need(same(h['manifest_ref'],mref) and type(m['members']) is list and m['members'],'HDF_MF_BINDING')
    home=Path(mref['path']).parent
    for ref in m['members']:
        need(Path(ref['path']).is_relative_to(home),'MF_FOREIGN_MEMBER');checked(ref)
    return h,m,[href,mref,*m['members']]
def when(value):
    need(type(value) is str,'TIME_STRING');x=datetime.fromisoformat(value.replace('Z','+00:00'));need(x.tzinfo is not None,'TIMEZONE_REQUIRED');return x
def lease(q):
    need(type(q['lease_id']) is str and re.fullmatch('[0-9a-f]{32}',q['lease_id']),'LEASE_ID')
    issued,expires=when(q['lease_issued_at']),when(q['lease_expires_at'])
    need(0<(expires-issued).total_seconds()<=3600 and issued<=datetime.now(timezone.utc)<expires,'LIVE_READONLY_LEASE')
def inputs():return doc(pin(N/'source-inputs.json'))

def structured_values(value,depth=0):
    """Decode nested JSON and complete JSON fragments without executing text."""
    if depth>8:return []
    result=[value]
    if type(value) is dict:
        for child in value.values():result.extend(structured_values(child,depth+1))
    elif type(value) is list:
        for child in value:result.extend(structured_values(child,depth+1))
    elif type(value) is str and len(value)<=32*1024*1024:
        try:decoded=strict(value)
        except (ValueError,TypeError):decoded=None
        if decoded is not None and decoded!=value:result.extend(structured_values(decoded,depth+1))
        else:
            decoder=json.JSONDecoder();pos=0;count=0
            while pos<len(value) and count<8192:
                start=re.search(r'[{\[]',value[pos:])
                if start is None:break
                pos+=start.start()
                try:child,end=decoder.raw_decode(value,pos)
                except ValueError:pos+=1;continue
                result.extend(structured_values(child,depth+1));pos=end;count+=1
    return result
def contains_ref(value,ref):
    for item in structured_values(value):
        if type(item) is dict and set(item)=={'path','sha256','bytes'}:
            try:
                if same(item,ref):return True
            except (ValueError,TypeError):pass
    return False
def audit(binding_ref,actor,expected_refs):
    """Three real records from the fixed Root parent, with full typed ref binding."""
    a=doc(binding_ref);capture=a.get('original_capture_ref',a.get('actual_capture_ref'));raw=checked(capture)
    need(canonical(a.get('source_audit_path'))==canonical(ROOT_AUDIT),'FIXED_ROOT_AUDIT_PATH')
    lines=raw.splitlines(keepends=True);need(len(lines)==3 and all(v.endswith(b'\n') for v in lines),'THREE_ORIGINAL_RECORDS')
    head,first,last=[strict(v) for v in lines];fp=first.get('payload',{});lp=last.get('payload',{})
    need(head.get('type')=='session_meta' and head.get('ordinal')==0 and head.get('payload',{}).get('id')==ROOT_THREAD,'ROOT_PARENT_IDENTITY')
    need(type(first.get('ordinal')) is int and type(last.get('ordinal')) is int and 0<first['ordinal']<last['ordinal'],'AUDIT_RECORD_ORDER')
    if actor==ROOT:
        need(first.get('type')==last.get('type')=='response_item' and fp.get('type') in ('custom_tool_call','function_call')
            and lp.get('type') in ('custom_tool_call_output','function_call_output') and type(fp.get('call_id')) is str
            and fp['call_id']==lp.get('call_id')==a.get('original_call_id')
            and re.fullmatch(r'(?:[A-Za-z0-9_]+\.)*exec',fp.get('name','')) is not None,'ROOT_EXEC_CALL_AND_OUTPUT')
        content=lp.get('output')
    else:
        need(type(actor) is str and actor.startswith('codex:/root/'),'CANONICAL_PEER_ACTOR')
        actual_author=actor.removeprefix('codex:')
        need(first.get('type')=='inter_agent_communication_metadata' and last.get('type')=='response_item'
            and last['ordinal']==first['ordinal']+1 and first.get('timestamp')==last.get('timestamp')
            and lp.get('type')=='agent_message' and lp.get('author')==actual_author and lp.get('recipient')=='/root'
            and last.get('metadata',{}).get('client_authored') is False,'ACTUAL_PEER_DELIVERY_TO_ROOT')
        content=lp.get('content')
    need(all(contains_ref(content,ref) for ref in expected_refs),'STRUCTURED_FULL_REF_AUDIT_BINDING')
    offsets=a['source_line_offsets'];lengths=a['source_line_bytes'];hashes=a['original_line_sha256'];size=a['source_prefix_size_observed']
    need(type(offsets) is list and len(offsets)==3 and offsets==sorted(set(offsets)) and offsets[0]==0
        and all(type(v) is int and v>=0 for v in offsets) and type(size) is int and size>0
        and lengths==[len(v) for v in lines] and hashes==[hashlib.sha256(v).hexdigest() for v in lines],'AUDIT_RANGE_PINS')
    with Path(ROOT_AUDIT).open('rb') as f:
        for off,line in zip(offsets,lines):
            need(off+len(line)<=size,'AUDIT_PREFIX_BOUNDARY');f.seek(off);need(f.read(len(line))==line,'ORIGINAL_ROOT_BYTES')
    return dict(refs=[binding_ref,capture],call=first,result=last,result_time=when(last['timestamp']))

def source_chain(q):
    i=inputs();leaf,leafmf,lrefs=pair(i['leaf_hdf_ref'],i['leaf_mf_ref'])
    lh,lm,lr=pair(i['leaf_review_hdf_ref'],i['leaf_review_mf_ref']);ld=doc(i['leaf_review_decision_ref'])
    need(ld['decision']=='ACCEPTED_SOURCE_ONLY' and ld['actor_role']=='INDEPENDENT_NON_AUTHOR'
        and ld['actor_id']==lh['actor_id'] and ld['actor_id'] not in (ROOT,AUTHOR,LEAF_AUTHOR)
        and ld['source_author_id']==LEAF_AUTHOR and same(lh['source_decision_ref'],i['leaf_review_decision_ref']),'ACCEPTED_LEAF_REVIEW')
    for key in ('source_hdf_ref','source_mf_ref','runner_ref','contract_ref','source_inputs_ref'):
        want=i['leaf_hdf_ref'] if key=='source_hdf_ref' else i['leaf_mf_ref'] if key=='source_mf_ref' else leaf[key]
        need(same(ld[key],want),'LEAF_REVIEW_EXACT_'+key)
    source,sm,srefs=pair(q['source_hdf_ref'],q['source_mf_ref']);review,rm,rrefs=pair(q['review_hdf_ref'],q['review_mf_ref']);decision=doc(q['review_decision_ref'])
    need(source['source_author']==AUTHOR and source['status']=='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION'
        and same(source['caller_ref'],pin(__file__)) and same(source['source_inputs_ref'],pin(N/'source-inputs.json')),'OWN_SOURCE_BINDING')
    reviewer=decision['actor_id']
    need(decision['schema']=='researchos.public22-continuation-root-independent-source-decision.v1' and decision['decision']=='ACCEPTED_SOURCE_ONLY'
        and reviewer==review['actor_id'] and reviewer not in (ROOT,AUTHOR,LEAF_AUTHOR) and decision['actor_role']=='INDEPENDENT_NON_AUTHOR'
        and decision['source_author']==AUTHOR and decision['execution_grant'] is False and decision['formal_acceptance'] is False,'OWN_NONAUTHOR_REVIEW')
    need(same(review['source_decision_ref'],q['review_decision_ref']) and any(same(x,q['review_decision_ref']) for x in rm['members']),'OWN_REVIEW_MEMBER')
    for field,want in {'source_hdf_ref':q['source_hdf_ref'],'source_mf_ref':q['source_mf_ref'],'caller_ref':source['caller_ref'],
        'source_inputs_ref':source['source_inputs_ref'],'calling_contract_ref':source['calling_contract_ref'],'runtime_resources_ref':i['runtime_resources_ref'],'main23_bound_ref':i['main23_bound_ref'],'existing22_decision_ref':i['existing22_decision_ref']}.items():
        need(same(decision[field],want),'OWN_REVIEW_BINDING_'+field)
    need(decision['original1025_result']=='FAILED_RETAINED' and decision['continuation_only'] is True and decision['runtime_closure_reviewed'] is True,'REVIEW_READONLY_BOUNDARY')
    leaf_audit=audit(q['leaf_review_audit_ref'],ld['actor_id'],[i['leaf_review_hdf_ref'],i['leaf_review_mf_ref'],i['leaf_review_decision_ref']])
    own_audit=audit(q['review_audit_ref'],reviewer,[q['review_hdf_ref'],q['review_mf_ref'],q['review_decision_ref']])
    need(own_audit['result_time']>=when(review['reviewed_utc']),'REVIEW_DELIVERY_TIME')
    refs=lrefs+lr+srefs+rrefs+[i['leaf_review_decision_ref'],q['review_decision_ref'],pin(N/'source-inputs.json')]
    refs+=leaf_audit['refs']+own_audit['refs']+i['source_resource_refs']+reuse_chain(q,i)
    return dict(leaf=leaf,review=review,reviewer=reviewer,refs=refs,inputs=i)

def current_four(refs,revisions):
    need(type(refs) is list and len(refs)==4 and set(revisions)=={'checkpoint','path_ownership','step_state','commands'},'FOUR_CURRENT_CANON')
    raw=[];documents=[];physical_refs=[]
    for name,path,ref in zip(('checkpoint','path_ownership','step_state','commands'),CANON,refs):
        need(canonical(ref['path'])==canonical(str(path)),'CANONICAL_PATH');data=checked(ref);value=strict(data)
        need((revisions[name] is None or type(revisions[name]) is int) and value.get('revision')==revisions[name],'EXPECTED_REVISION_CAS')
        raw.append(data);documents.append(value);physical_refs.append(pin(path))
    need(type(revisions['checkpoint']) is int and revisions['checkpoint']>=371 and type(revisions['path_ownership']) is int
        and revisions['path_ownership']>=175 and documents[1]['active_integrator']['id']==ROOT
        and documents[0]['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','CURRENT_ROOT_CANON')
    return dict(raw=raw,documents=documents,refs=physical_refs,requested_refs=refs,revisions=revisions)

def native_observation(value):
    need(type(value) is dict and type(value.get('actual_exit')) is int and value['actual_exit']==0 and value.get('timed_out') is False
        and value.get('error') is None and type(value.get('owned_child_pid')) is int and 0<value['owned_child_pid']<=0xffffffff,'ORIGINAL_NATIVE_EXIT_PID')
    created=value.get('creation_time_100ns')
    need((type(created) is int or type(created) is str and re.fullmatch('[0-9]{1,20}',created))
        and 0<int(created)<=0xffffffffffffffff,'EXACT_UINT64_FILETIME')
    cleanup=value['job_cleanup']
    need(type(cleanup.get('active_processes_last_observed')) is int and cleanup['active_processes_last_observed']==0
        and cleanup.get('errors')==[] and all(cleanup.get(k) is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured',
        'assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed')),'ORIGINAL_NATIVE_CLOSED')
    return str(created)

def original_evidence(i):
    requirements=doc(i['recheck_contract_ref']);evidence=requirements['evidence'];refs=[i['recheck_contract_ref'],requirements['request_ref'],*evidence.values(),
        requirements['original_caller_record_ref'],requirements['original_case_closed_ref']]
    need(evidence==i['evidence'] and requirements['request_ref']==i['case_request_ref'],'FIXED_NINE_ORIGINAL_EVIDENCE')
    assignment=doc(evidence['original_assignment_ref']);state=doc(evidence['returned_state_ref']);caller=doc(requirements['original_caller_record_ref'])
    case=doc(requirements['request_ref']);closed=doc(requirements['original_case_closed_ref'])
    need(assignment['ordinal']==1025 and assignment['issued_by']==ROOT and assignment['successful_native_children']==4
        and assignment['formal_acceptance'] is False and state['request_ref']==requirements['request_ref'] and state['case_id']==case['case_id']
        and state['status']=='STOPPED_AT_FIRST_FAILURE' and state['first_failure']==assignment['first_failure']
        and state['first_failure']['message']=='PUBLIC_RESTORE_SCHEMA_MISMATCH','ORIGINAL1025_FAILED_RETAINED')
    need(caller['runner_returned_state']==state and caller['case_request_ref']==requirements['request_ref']
        and caller['caller_error'] is None and caller['formal_acceptance'] is False,'PERSISTED_CALLER_STATE')
    need(state['closed_receipt']['status']=='PUBLISHED' and state['closed_receipt']['ref']==requirements['original_case_closed_ref']
        and closed['closed_receipt']['status']=='PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF'
        and {k:v for k,v in state.items() if k!='closed_receipt'}=={k:v for k,v in closed.items() if k!='closed_receipt'},'ORIGINAL_CLOSED_SNAPSHOT')
    prior_request=caller['root_request_ref'];prior=doc(prior_request);refs.append(prior_request)
    original_audit=audit(requirements['original_actual_capture_binding_ref'],ROOT,[prior_request,requirements['request_ref']])
    need(same(assignment['original_capture_ref'],requirements['original_actual_capture_ref'])
        and same(assignment['capture_binding_ref'],requirements['original_actual_capture_binding_ref'])
        and same(assignment['caller_record_ref'],requirements['original_caller_record_ref']),'ASSIGNMENT_ORIGINAL_CAPTURE_BINDING')
    refs+=original_audit['refs']
    leaf_contract=doc(i['leaf_contract_ref']);leaf=load(i['leaf_runner_ref'],'readonly_original_projection')
    projection=leaf.compile_case(leaf_contract,case)
    need([c['phase'] for c in state['calls']]==['bootstrap22','keygen22','backup22','verify22'],'EXACT_FOUR_OLD_CHILDREN')
    for call,phase in zip(state['calls'],projection['phases']):
        native_observation(call['observation'])
        need(call['argv']==phase['argv'] and canonical(call['cwd'])==canonical(phase['cwd']) and type(call['actual_exit']) is int
            and call['actual_exit']==0 and call['timeout_seconds']==90,'EXACT_ORIGINAL_ARGV_CWD')
        for key in ('before_ref','result_ref','stdout_ref','stderr_ref'):checked(call[key]);refs.append(call[key])
        result=doc(call['result_ref']);before=doc(call['before_ref'])
        need(result=={k:v for k,v in call.items() if k!='result_ref'},'ORIGINAL_PERSISTED_RESULT')
        need(all(before[k]==call[k] for k in ('phase','argv','cwd','env','timeout_seconds','started_at_unix_ns')),'ORIGINAL_BEFORE_PROJECTION')
    baseline_ref=state['baseline_manifest_ref'];baseline=doc(baseline_ref);refs.append(baseline_ref)
    need(baseline['private_key_outside_baseline'] is True and baseline['source_guard_share']=='FILE_SHARE_READ_ONLY','BASELINE_CONTRACT')
    allowed_roots=[Path(case['output_root'])/'source22',Path(case['output_root'])/'backup22']
    for ref in baseline['references']:
        p=Path(ref['path']);need(any(p.is_relative_to(root) for root in allowed_roots),'BASELINE_NO_PRIVATE_KEY_OR_OWNER')
        checked(ref);need(bool(p.stat().st_file_attributes&stat.FILE_ATTRIBUTE_READONLY),'BASELINE_READONLY_ATTRIBUTE')
        need(any(canonical(row['path'])==canonical(str(p)) and row['readonly_attribute'] is True for row in baseline['file_attributes']),'RECORDED_BASELINE_ATTRIBUTE')
        refs.append(ref)
    need(len(baseline['references'])==len(baseline['file_attributes']),'BASELINE_COMPLETE_ATTRIBUTE_SET')
    return dict(refs=refs,requirements=requirements,evidence=evidence,case=case,baseline=baseline,assignment=assignment,state=state,prior=prior)

def runtime_refs(i):
    # Import SQLite before taking the loaded module closure, but perform no SQL.
    import sqlite3, _sqlite3
    resources=doc(i['runtime_resources_ref']);locked=doc(i['toolchain_lock_ref']);python=pin(sys.executable)
    need(canonical(python['path'])==canonical(locked['tools']['python']['path']) and python['sha256']==locked['tools']['python']['sha256'],'LOCKED_PYTHON')
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode and sys.flags.utf8_mode==1,'LOCKED_PYTHON_FLAGS')
    job=load(i['owned_job_ref'],'resource_paths_only_NO_JOB_CALL')
    required=[python,pin(_sqlite3.__file__),GUARD_REF,TP_REF,pin(__file__)]+[pin(p) for p in job.runtime_resource_paths()]
    for module in tuple(sys.modules.values()):
        for key in ('__file__','__cached__'):
            p=getattr(module,key,None)
            if p and Path(p).is_file():required.append(pin(p))
    allowed={canonical(r['path']):r for r in resources['resource_refs']}
    # Own Source scripts are separately pinned by the accepted own manifest.
    for ref in required:
        if Path(ref['path']).is_relative_to(N):continue
        need(canonical(ref['path']) in allowed and same(ref,allowed[canonical(ref['path'])]),'UNREVIEWED_LOADED_RUNTIME')
    return refs_unique([i['runtime_resources_ref'],i['toolchain_lock_ref'],i['owned_job_ref'],*resources['resource_refs'],*required])

def root_request(request_ref):
    q=doc(request_ref);need(q['schema']=='researchos.root-public22-continuation-registration-request.v1' and q['issued_by']==ROOT
        and q['mode']==MODE and q['formal_acceptance'] is False and q['parent_acceptance'] is False,'ROOT_READONLY_ENVELOPE')
    i=inputs();need(q['case_request_ref']==i['case_request_ref'] and q['evidence']==i['evidence'],'ORIGINAL_CASE_REQUEST_UNCHANGED')
    source=source_chain(q);original=original_evidence(i);current=current_four(q['before_canonical_refs'],q['expected_revisions']);lease(q)
    need(type(q['continuation_id']) is str and re.fullmatch('[0-9a-f]{32}',q['continuation_id']),'RECHECK_ID')
    root=B/'integration_codex'/('public22-continuation-registration-'+q['continuation_id']);out=B/'integration_codex'/('public22-continuation-'+q['continuation_id'])
    need(q['registration_root']==str(root) and q['receipt_root']==str(out) and not out.exists(),'FRESH_REVIEW_RECEIPT_ROOT')
    live=audit(q['postreview_live_audit_ref'],ROOT,q['before_canonical_refs']+[q['review_decision_ref'],q['case_request_ref']])
    need(live['result_time']>when(source['review']['reviewed_utc']) and when(q['created_utc'])>=live['result_time'],'POSTREVIEW_CURRENT_ROOT_CAPTURE')
    return q,current,source,original,[request_ref,*source['refs'],*original['refs'],*live['refs'],*runtime_refs(i)]

def projection(cp0,ow0,scope_ref,owner_ref,worker_ref,facts_ref,owner,worker,created):
    """Pure TP callback: no reads or nested guard over its exclusive pair."""
    cp=copy.deepcopy(cp0);ow=copy.deepcopy(ow0)
    need(KEY not in ow['card_path_bindings']['W05-99']['subtasks'] and not any(w.get('slice_id')==SLICE for w in cp['workers']),'READONLY_SLICE_ALREADY_REGISTERED')
    need(owner['scope_ref']==worker['scope_ref']==scope_ref and worker['selected_owner_ref']==owner_ref
        and owner['selected_worker_id']==worker['worker_id']==ROOT,'ACYCLIC_SCOPE_OWNER_WORKER')
    ow['card_path_bindings']['W05-99']['subtasks'][KEY]=dict(owner,owner_document_ref=owner_ref,worker_document_ref=worker_ref,current_source_writer=None,formal_case_accepted_delta=0,parent_acceptance=False)
    cp['workers'].append(dict(worker,worker_document_ref=worker_ref))
    cp['work_in_progress']['public22_continuation_scope_ref']=scope_ref
    cp['work_in_progress']['public22_continuation_facts_ref']=facts_ref
    cp.update(revision=cp0['revision']+1,expected_previous_revision=cp0['revision'],updated_at=created,updated_by=ROOT)
    ow.update(revision=ow0['revision']+1,updated_at=created,updated_by=ROOT)
    restored_cp=copy.deepcopy(cp);restored_ow=copy.deepcopy(ow)
    for key in ('workers','work_in_progress','revision','expected_previous_revision','updated_at','updated_by'):
        if key in cp0:restored_cp[key]=copy.deepcopy(cp0[key])
        else:restored_cp.pop(key,None)
    del restored_ow['card_path_bindings']['W05-99']['subtasks'][KEY]
    for key in ('revision','updated_at','updated_by'):
        if key in ow0:restored_ow[key]=copy.deepcopy(ow0[key])
        else:restored_ow.pop(key,None)
    need(encoded(restored_cp)==encoded(cp0) and encoded(restored_ow)==encoded(ow0),'COMPLETE_CANONICAL_INVERSE')
    need(cp.get('failure_counters')==cp0.get('failure_counters') and cp['work_in_progress'].get('root_next_failure_ordinal_live')==cp0['work_in_progress'].get('root_next_failure_ordinal_live'),'FAILURE_LEDGER_UNCHANGED')
    return cp,ow

class SourceFailure(RuntimeError):
    def __init__(self,phase,primary,secondary):
        self.primary_exception=primary;self.secondary_errors=secondary
        super().__init__(phase+': '+json.dumps(dict(original_error=repr(primary) if primary is not None else None,secondary_errors=secondary),ensure_ascii=False))

def close_guard(guard,root,name,created):
    errors=[];cleanup=None;receipt=None
    try:cleanup=guard.close()
    except BaseException as exc:errors.append(dict(phase='guard-close',error=repr(exc)))
    if cleanup is not None:
        if cleanup.get('closed') is not True or cleanup.get('retained_handles_count')!=0 or cleanup.get('errors'):
            errors.append(dict(phase='guard-closed-observation',observation=cleanup))
        if created:
            try:receipt=save(root,name,cleanup)
            except BaseException as exc:errors.append(dict(phase='guard-cleanup-save',error=repr(exc),unsaved_cleanup=cleanup))
    return dict(errors=errors,cleanup=cleanup,receipt_ref=receipt)

def scope_projection(q,request_ref,source,original):
    return dict(schema='researchos.root-public22-continuation-scope.v1',issued_by=ROOT,mode=MODE,registration_request_ref=request_ref,
        case_request_ref=q['case_request_ref'],evidence=q['evidence'],leaf_contract_ref=source['leaf']['contract_ref'],leaf_runner_ref=source['leaf']['runner_ref'],
        original_case_root=original['case']['output_root'],receipt_root=q['receipt_root'],lease_id=q['lease_id'],lease_issued_at=q['lease_issued_at'],
        lease_expires_at=q['lease_expires_at'],main23_bound_ref=inputs()['main23_bound_ref'],existing22_decision_ref=inputs()['existing22_decision_ref'],phases=['upgrade22to23','backup23','verify23'],maximum_new_native_children=3,original1025_result='FAILED_RETAINED',formal_acceptance=False,parent_acceptance=False)

def build(request_ref):
    q,current,source,original,refs=root_request(request_ref);root=Path(q['registration_root']);need(not root.exists(),'NEW_REGISTRATION_NAMESPACE');physical(root,True)
    guard=load(GUARD_REF,'existing_source_guard').SourceReadGuard(per_file_cap=MAX,total_cap=2*1024*1024*1024)
    result=None;created=False;primary=None
    try:
        guard.acquire(refs_unique(refs+current['refs'],CANON[:2]));current_four(q['before_canonical_refs'],q['expected_revisions']);root.mkdir();created=True
        scope=scope_projection(q,request_ref,source,original)
        sr=save(root,'scope.root.json',scope)
        common=dict(step_id='W05-99',slice_id=SLICE,state=STATE,owner=ROOT,scope_ref=sr,lease_status='ACTIVE',lease_id=q['lease_id'],
            lease_issued_at=q['lease_issued_at'],lease_expires_at=q['lease_expires_at'],receipt_root=q['receipt_root'],mode=MODE)
        owner=dict(common,owner_id=ROOT,selected_worker_id=ROOT);oref=save(root,'owner.root.json',owner)
        worker=dict(common,worker_id=ROOT,selected_owner_ref=oref);wref=save(root,'worker.root.json',worker)
        archives=[]
        for index,raw in enumerate(current['raw']):
            path=root/(str(index)+'.before.raw.json')
            with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            archives.append(pin(path))
        facts=dict(schema='researchos.root-public22-continuation-registration-facts.v1',issued_by=ROOT,request_ref=request_ref,scope_ref=sr,owner_ref=oref,
            worker_ref=wref,before_canonical_refs=q['before_canonical_refs'],before_archive_refs=archives,expected_revisions=q['expected_revisions'],formal_acceptance=False)
        fref=save(root,'facts.root.json',facts);after=projection(*current['documents'][:2],sr,oref,wref,fref,owner,worker,q['created_utc'])
        for index,value in enumerate(after):save(root,str(index)+'.after.proposed.json',value)
        result=fref
    except BaseException as exc:primary=exc
    finally:closed=close_guard(guard,root,'build.guard.closed.json',created)
    if primary is not None or closed['errors']:raise SourceFailure('BUILD_FAILED_NO_RETRY',primary,closed['errors']) from primary
    return result

def registration(mode,facts_ref,activation_ref=None):
    need(mode in ('check','activate'),'CHECK_OR_ACTIVATE')
    facts=doc(facts_ref);q,current,source,original,refs=root_request(facts['request_ref']);root=Path(q['registration_root'])
    need(same(facts_ref,pin(root/'facts.root.json')) and facts['before_canonical_refs']==q['before_canonical_refs'],'FACTS_REQUEST_BINDING')
    scope=doc(facts['scope_ref']);owner=doc(facts['owner_ref']);worker=doc(facts['worker_ref'])
    need(scope==scope_projection(q,facts['request_ref'],source,original),'EXACT_READONLY_SCOPE_PROJECTION')
    need(scope['registration_request_ref']==facts['request_ref'] and scope['case_request_ref']==q['case_request_ref'] and scope['evidence']==q['evidence']
        and scope['mode']==MODE and scope['receipt_root']==q['receipt_root'] and scope['original1025_result']=='FAILED_RETAINED','SCOPE_FROZEN_REQUEST')
    for value in (scope,owner,worker):
        lease(value);need(all(value[k]==q[k] for k in ('lease_id','lease_issued_at','lease_expires_at')),'SAME_REGISTERED_LEASE')
    for value in (owner,worker):need(value['state']==STATE and value['owner']==ROOT and value['slice_id']==SLICE and value['scope_ref']==facts['scope_ref'],'REGISTERED_OWNER_WORKER')
    need(len(facts['before_archive_refs'])==4 and all(checked(ref)==raw for ref,raw in zip(facts['before_archive_refs'],current['raw'])),'FOUR_EXACT_BEFORE_ARCHIVES')
    if mode=='activate':
        activation=doc(activation_ref)
        need(activation['issued_by']==ROOT and activation['facts_ref']==facts_ref and activation['before_canonical_refs']==q['before_canonical_refs'],'ROOT_ACTIVATION')
        seen=audit(activation['actual_audit_ref'],ROOT,[facts_ref,*q['before_canonical_refs']])
        need(seen['result_time']>when(q['created_utc']),'FRESH_ACTIVATION_CAPTURE');refs.extend([activation_ref,*seen['refs']])
    refs.extend([facts_ref,facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],*facts['before_archive_refs'],GUARD_REF,TP_REF,*current['refs'][2:]])
    tp=load(TP_REF,'existing_canonical_TP');guard=load(GUARD_REF,'registration_source_guard').SourceReadGuard(per_file_cap=MAX,total_cap=2*1024*1024*1024)
    transaction=None;primary=None
    def transform(cp,ow):
        need(cp==current['documents'][0] and ow==current['documents'][1],'TP_EXPECTED_DOCUMENTS')
        return projection(cp,ow,facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],facts_ref,owner,worker,q['created_utc'])
    try:
        guard.acquire(refs_unique(refs,CANON[:2]));after=transform(*current['documents'][:2])
        if mode=='activate':transaction=tp.update_pair(current['refs'][:2],transform,root,'activate')
        else:current_four(q['before_canonical_refs'],q['expected_revisions'])
        need(all(same(pin(p),r) for p,r in zip(CANON[2:],current['refs'][2:])),'SS_CM_UNCHANGED')
    except BaseException as exc:primary=exc
    finally:closed=close_guard(guard,root,mode+'.guard.closed.json',True)
    if primary is not None or closed['errors']:raise SourceFailure('REGISTRATION_FAILED_NO_RETRY',primary,closed['errors']) from primary
    return save(root,mode+'.result.json',dict(schema='researchos.root-public22-continuation-registration-result.v1',mode=mode,facts_ref=facts_ref,scope_ref=facts['scope_ref'],
        transaction=transaction,proposed_after_refs=[dict(path=str(p),sha256=hashlib.sha256(encoded(v)).hexdigest(),bytes=len(encoded(v))) for p,v in zip(CANON[:2],after)],
        SS_CM_unchanged=True,complete_inverse=True,original1025_result='FAILED_RETAINED',maximum_new_native_children=3,formal_acceptance=False))

def live(actual):
    facts=doc(actual['facts_ref']);scope=doc(facts['scope_ref']);q=doc(facts['request_ref']);lease(scope)
    need(actual['scope_ref']==facts['scope_ref'] and scope['registration_request_ref']==facts['request_ref']
        and scope['case_request_ref']==actual['case_request_ref']==inputs()['case_request_ref'] and scope['mode']==MODE,'LIVE_EXACT_SCOPE')
    revisions=dict(q['expected_revisions']);revisions['checkpoint']+=1;revisions['path_ownership']+=1
    current=current_four(actual['current_canonical_refs'],revisions);cp,ow=current['documents'][:2]
    need(cp['work_in_progress']['public22_continuation_scope_ref']==facts['scope_ref']
        and cp['work_in_progress']['public22_continuation_facts_ref']==actual['facts_ref'],'LIVE_CURRENT_REGISTRATION')
    owner=doc(facts['owner_ref']);worker=doc(facts['worker_ref']);workers=[w for w in cp['workers'] if w.get('slice_id')==SLICE]
    need(len(workers)==1,'ONE_LIVE_WORKER');task=ow['card_path_bindings']['W05-99']['subtasks'][KEY]
    need(task==dict(owner,owner_document_ref=facts['owner_ref'],worker_document_ref=facts['worker_ref'],current_source_writer=None,formal_case_accepted_delta=0,parent_acceptance=False)
        and workers==[dict(worker,worker_document_ref=facts['worker_ref'])],'EXACT_CANON_OWNER_WORKER_DOCUMENTS')
    for value in (owner,worker):
        lease(value);need(value['owner']==ROOT and value['state']==STATE and value['lease_status']=='ACTIVE' and value['scope_ref']==facts['scope_ref']
            and value['lease_id']==scope['lease_id'] and value['receipt_root']==scope['receipt_root'],'LIVE_OWNER_LEASE_STATE')
    need(worker['selected_owner_ref']==facts['owner_ref'] and owner['selected_worker_id']==worker['worker_id']==ROOT,'LIVE_OWNER_WORKER_LINK')
    return scope,facts,q,current

def reuse_chain(q,i):
    bound=doc(i['main23_bound_ref']);contract=doc(i['leaf_contract_ref'])
    need(bound['schema']=='researchos.root-current-main23-programme-qualification.v1'
        and bound['issued_by']==ROOT and bound['root_thread_id']==ROOT_THREAD
        and bound['status']=='QUALIFIED_CURRENT_MAIN23_BUILD'
        and bound['independent_non_author'] is True and bound['execution_grant'] is False
        and bound['source_refs']==contract['current_main_source_refs'],'EXACT_EXISTING_MAIN23_QUALIFICATION')
    need(bound['program_ref']!=contract['main23_candidate_only'] and bound['review_author'] not in (ROOT,bound['source_author']),'NO_UNREBOUND_CANDIDATE')
    need(bound['program_ref']==i['main23_program_ref'],'FIXED_MAIN23_BINARY')
    existing=doc(i['existing22_decision_ref'])
    need(existing['decision']=='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED'
        and existing['original1025_result']=='FAILED_RETAINED'
        and existing['readonly83_oracle_source_ref']==i['leaf_runner_ref']
        and existing['new_Native_children_by_reviewer']==0 and existing['formal_acceptance'] is False,'EXISTING22_COMPONENT_ONLY')
    expected=[i['existing22_hdf_ref'],i['existing22_mf_ref'],i['existing22_decision_ref']]
    prior_audit=audit(q['existing22_review_audit_ref'],existing['actor_id'],expected)
    programme_audit=audit(q['main23_review_audit_ref'],bound['review_author'],bound['review_refs'][:3])
    root_programme=audit(q['main23_root_binding_audit_ref'],ROOT,[i['main23_bound_ref']])
    refs=[i['main23_bound_ref'],bound['program_ref'],bound['qualification_ref'],bound['provenance_ref'],
        *bound['source_refs'],*bound['review_refs'],*expected,*prior_audit['refs'],*programme_audit['refs'],*root_programme['refs']]
    for ref in refs:checked(ref)
    return refs

def continuation_projection(contract,original_case,receipt_root,program,leaf):
    old=leaf.compile_case(contract,original_case)
    need(original_case['end_version']==22,'EXISTING22_ONLY')
    root=Path(receipt_root)
    paths=dict(old['paths'])
    for k,rel in {'root':'.','work22':'working22','workdb22':'working22/researchos.sqlite',
        'snapshot23':'upgrade22to23.snapshot','candidate23':'candidate23','db23':'candidate23/researchos.sqlite',
        'backup23':'backup23','verify23':'verified23','raw':'raw','tmp':'tmp'}.items():
        paths[k]=str(root if rel=='.' else root/rel)
    # Old original data/backup/key paths are never rewritten. No owner credential is read.
    phases=leaf.upgrade23_phases(contract,dict(paths=paths),program)
    need([p['id'] for p in phases]==['upgrade22to23','backup23','verify23'],'THREE_UNCOVERED_PHASES_ONLY')
    need(canonical(paths['workdb22'])!=canonical(paths['db22']),'ORIGINAL_NOT_UPGRADE_INPUT')
    return dict(paths=paths,phases=phases)

def retain_observation(invocation,observed,ended):
    # Retain returned native facts before either output stream can fail to close.
    invocation['observation']=observed
    invocation['actual_exit']=observed.get('actual_exit')
    invocation['ended_at_unix_ns']=ended
    invocation['creation_time_100ns_decimal']=str(observed['creation_time_100ns']) if type(observed.get('creation_time_100ns')) is int else None

def record_observation(invocation,observed,ended,stdout_path,stderr_path,pinner):
    retain_observation(invocation,observed,ended)
    invocation['stdout_ref']=pinner(stdout_path)
    invocation['stderr_ref']=pinner(stderr_path)

class ObservedOutput:
    def __init__(self,path,label,invocation,state):
        self.path=path;self.label=label;self.invocation=invocation;self.state=state
    def __enter__(self):
        self.stream=self.path.open('xb')
        return self.stream
    def __exit__(self,kind,primary,traceback):
        try:self.stream.close()
        except BaseException as close_error:
            detail=dict(phase=self.label+'-close',type=type(close_error).__name__,message=str(close_error))
            self.invocation.setdefault('output_close_errors',[]).append(detail)
            if primary is None:raise
            # A pre-existing child/body/inner-close error stays primary.
            self.state['secondary_errors'].append(detail)
        return False

def validate_upgrade23(leaf,sealed,target,report,snapshot,contract,program):
    leaf.validate_ledger(sealed,22);leaf.validate_ledger(target,23)
    new={'client_command_identities','host_model_configurations','host_model_config_heads'}
    need(set(target['tables'])==set(sealed['tables'])|new,'EXACT_THREE_ADDED_TABLES')
    need(all(target['tables'][k]==v for k,v in sealed['tables'].items() if k not in ('schema_migrations','auth_credentials')),'ALL_OLD_TABLE_STATE_PRESERVED')
    need(all(target['tables'][k]['count']==0 for k in new),'NEW_TABLES_EMPTY')
    need(target['credentials']['all_revoked_one'] is True
        and target['tables']['auth_credentials']['count']==sealed['tables']['auth_credentials']['count']
        and target['tables']['auth_credentials']['rows_sha256']==sealed['credentials']['expected_revoked_rows_sha256'],'EXACT_OWNER_CREDENTIAL_REVOCATION')
    plan=snapshot['purpose']['plan']
    need(plan['id']==contract['plan22to23'] and plan['source_versions']==list(range(1,23))
        and plan['target_versions']==list(range(1,24)),'EXACT_UPGRADE_PLAN')
    need(plan['program_hashes']==dict(source='sha256:'+contract['old22_control']['sha256'],target='sha256:'+program['sha256']),'NATIVE_PROGRAMME_HASH_BINDING')
    need(plan['source_schema_hash']=='sha256:'+sealed['schema_sha256']
        and plan['target_schema_with_restore_fence_hash']=='sha256:'+target['schema_sha256'],'NATIVE_SOURCE_TARGET_SCHEMA_BINDING')
    need(report['status']==leaf.RESTORED and report['backup_id']==snapshot['id']
        and report['before']==snapshot['inventory'],'UPGRADE_PUBLIC_RECEIPT_BINDING')
    return True

def validate_backup23(leaf,before,after,manifest):
    leaf.validate_ledger(after,23)
    need(after['tables']==before['tables'] and after['schema_rows']==before['schema_rows'],'BACKUP23_SOURCE_UNCHANGED')
    need(manifest['migrations']==list(range(1,24)) and manifest['schema_hash']=='sha256:'+after['schema_sha256'],'BACKUP23_SCHEMA_LEDGER')
    return True

def validate_restore23(leaf,before,after,manifest,report):
    leaf.validate_ledger(after,23)
    need(before['schema_rows']==after['schema_rows'] and before['schema_sha256']==after['schema_sha256'],'RESTORE23_EXACT_EXISTING_FENCE_SCHEMA')
    need(before['tables']==after['tables'] and after['credentials']['all_revoked_one'] is True,'RESTORE23_ALL_TABLE_HASHES')
    need(report['status']==leaf.RESTORED and report['backup_id']==manifest['id']
        and report['before']==report['after']==manifest['inventory']
        and report['recovery']['credentials']=='REVOKED_REPROVISION_LOCALLY','RESTORE23_PUBLIC_REPORT')
    return True

def execute(actual_ref,preentry_ref):
    actual=doc(actual_ref)
    need(actual['schema']=='researchos.root-public22-continuation-actual-request.v1' and actual['issued_by']==ROOT
        and actual['formal_acceptance'] is False and actual['parent_acceptance'] is False,'ROOT_CONTINUATION_REQUEST')
    scope,facts,q,current=live(actual);source=source_chain(q);i=inputs();original=original_evidence(i)
    need(scope==scope_projection(q,facts['request_ref'],source,original),'EXACT_CONTINUATION_SCOPE')
    activation=doc(actual['registration_result_ref'])
    need(activation['mode']=='activate' and activation['facts_ref']==actual['facts_ref']
        and activation['scope_ref']==actual['scope_ref'] and activation['complete_inverse'] is True
        and activation['SS_CM_unchanged'] is True and activation['transaction'] is not None,'ACTUAL_ACTIVATION')
    journal=Path(activation['transaction']['transaction_journal'])
    need(journal.parent==Path(q['registration_root']),'EXACT_TP_JOURNAL')
    committed_ref=pin(journal/'committed.json');committed=doc(committed_ref)
    need(committed['both_verified_while_exclusively_held'] is True and committed['written_indices']==[0,1]
        and len(committed['after_refs'])==2 and all(same(a,b) for a,b in zip(committed['after_refs'],current['refs'][:2])),'ACTUAL_TP_CURRENT')
    witness=audit(preentry_ref,ROOT,
        [actual_ref,actual['registration_result_ref'],actual['scope_ref'],*actual['current_canonical_refs']])
    need(witness['result_time']>=when(q['created_utc']),'PREENTRY_AFTER_REGISTRATION')
    root=Path(scope['receipt_root']);physical(root,True);need(not root.exists(),'FRESH_UNUSED_CONTINUATION_OUTPUT')
    leaf=load(i['leaf_runner_ref'],'accepted_public22_v3_pure_helpers')
    contract=doc(i['leaf_contract_ref']);bound=doc(i['main23_bound_ref'])
    projection=continuation_projection(contract,original['case'],str(root),bound['program_ref'],leaf);paths=projection['paths']
    runtime=runtime_refs(i);job=load(i['owned_job_ref'],'continuation_owned_job')
    refs=refs_unique(source['refs']+original['refs']+witness['refs']+runtime+[actual_ref,actual['facts_ref'],
        actual['scope_ref'],facts['request_ref'],facts['owner_ref'],facts['worker_ref'],actual['registration_result_ref'],
        committed_ref,*current['refs']])
    guard=load(GUARD_REF,'continuation_held_guard').SourceReadGuard(per_file_cap=MAX,total_cap=2*1024*1024*1024)
    state=dict(schema='researchos.public22-to-main23-continuation-return.v1',actual_request_ref=actual_ref,
        status='STARTED',phase='prepare',calls=[],observations={},first_failure=None,secondary_errors=[],
        new_native_children_attempted=0,original1025_result='FAILED_RETAINED',original_four_children_replayed=False,
        original_baseline_refs=original['baseline']['references'],full20to24='OPEN',formal_acceptance=False,
        parent_acceptance=False,formal_case_accepted_delta=0,automatic_retry=False,
        source_guard_cleanup=None,closed_receipt_ref=None,external_original_hostpair_required=True)
    created=False
    try:
        guard.acquire(refs);live(actual);root.mkdir();created=True
        for key in ('work22','raw','tmp'):Path(paths[key]).mkdir()
        # Retained original observations remain immutable. Observe only the new byte-identical working input.
        retained=original['state']['observations']['sealed22']
        need(leaf.observed_ref(paths['db22'])==i['evidence']['source_db_ref'],'EXACT_RETAINED22_SOURCE')
        data=guard.get_buffer(paths['db22'])
        with Path(paths['workdb22']).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        need(pin(paths['workdb22'])['sha256']==i['evidence']['source_db_ref']['sha256'],'EXACT_WORKING_COPY')
        state['working_copy_before_ref']=pin(paths['workdb22'])
        sealed=leaf.readonly_database_observation(paths['workdb22']);leaf.validate_ledger(sealed,22)
        need(sealed['tables']==retained['tables'] and sealed['schema_sha256']==retained['schema_sha256'],'COPIED22_LOGICAL_STATE')
        state['observations']['working22_input']=sealed
        # Only the public child opens this existing opaque key. Caller never reads, hashes, copies or logs key bytes.
        physical(paths['key']);need(Path(paths['key']).is_file(),'OPAQUE_RECOVERY_KEY_EXISTS')
        env=leaf._environment(paths);env['RESEARCHOS_DATA_DIR']=paths['work22']
        manifest23=None
        for phase in projection['phases']:
            state['phase']=phase['id'];live(actual)
            need([x['phase'] for x in state['calls']]==['upgrade22to23','backup23','verify23'][:len(state['calls'])],'MONOTONIC_PHASE_ORDER')
            for ref in refs:checked(ref)
            outpath=Path(paths['raw'])/(phase['id']+'.stdout');errpath=Path(paths['raw'])/(phase['id']+'.stderr')
            invocation=dict(phase=phase['id'],argv=phase['argv'],cwd=phase['cwd'],env=env,timeout_seconds=90,
                started_at_unix_ns=time.time_ns(),observation=None,actual_exit=None,native_child_kind='public_go_program')
            state['calls'].append(invocation)
            invocation['before_ref']=save(Path(paths['raw']),phase['id']+'.before.json',invocation)
            with ObservedOutput(outpath,'stdout',invocation,state) as out,ObservedOutput(errpath,'stderr',invocation,state) as err:
                state['new_native_children_attempted']+=1
                observed=job.run_owned(phase['argv'],phase['cwd'],env,out,err,90,creation_flags=0x08000000)
                retain_observation(invocation,observed,time.time_ns())
            record_observation(invocation,observed,invocation['ended_at_unix_ns'],outpath,errpath,pin)
            invocation['result_ref']=save(Path(paths['raw']),phase['id']+'.result.json',invocation)
            leaf.closed_job(observed)
            need(outpath.stat().st_size<=4*1024*1024 and errpath.stat().st_size<=4*1024*1024,'RAW_OUTPUT_CAP')
            emitted=strict(outpath.read_bytes())
            if phase['id']=='upgrade22to23':
                persisted=strict((Path(paths['candidate23'])/'restore-report.json').read_bytes());leaf.same_json(emitted,persisted)
                target=leaf.readonly_database_observation(paths['db23'])
                snapshot=strict((Path(paths['snapshot23'])/'manifest.json').read_bytes())
                validate_upgrade23(leaf,sealed,target,emitted,snapshot,contract,bound['program_ref'])
                expected_fence=leaf.expected_restore_trigger_sql(checked(i['main_recovery_source_ref']).decode('utf-8'))
                need([row for row in target['schema_rows'] if row[:2]==['trigger','backup_require_fresh_observation']]
                    ==[['trigger','backup_require_fresh_observation','domain_objects',expected_fence]],'EXACT_MAIN23_RESTORE_FENCE')
                state['observations']['upgrade23']=target
                state['upgrade_manifest_ref']=pin(Path(paths['snapshot23'])/'manifest.json')
                state['upgrade_report_ref']=pin(Path(paths['candidate23'])/'restore-report.json')
            elif phase['id']=='backup23':
                manifest23=strict((Path(paths['backup23'])/'manifest.json').read_bytes());leaf.same_json(emitted,manifest23)
                target=leaf.readonly_database_observation(paths['db23'])
                validate_backup23(leaf,state['observations']['upgrade23'],target,manifest23)
                state['observations']['backup23_source']=target;state['backup23_manifest_ref']=pin(Path(paths['backup23'])/'manifest.json')
            else:
                report=strict((Path(paths['verify23'])/'restore-report.json').read_bytes());leaf.same_json(emitted,report)
                target=leaf.readonly_database_observation(Path(paths['verify23'])/'state.sqlite')
                validate_restore23(leaf,state['observations']['backup23_source'],target,manifest23,report)
                state['observations']['restored23']=target;state['restore23_report_ref']=pin(Path(paths['verify23'])/'restore-report.json')
            live(actual)
        need(len(state['calls'])==3,'EXACT_THREE_COMPLETED_PHASES')
        for ref in refs:checked(ref)
        state['status']='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW'
    except BaseException as exc:
        state['status']='STOPPED_AT_FIRST_FAILURE'
        state['first_failure']=dict(phase=state['phase'],type=type(exc).__name__,message=str(exc),
            last_child_exit=state['calls'][-1]['actual_exit'] if state['calls'] else None,
            Root_assignment_required=True,original_ordinal=None)
    finally:
        try:
            state['source_guard_cleanup']=guard.close()
            c=state['source_guard_cleanup']
            need(c['closed'] is True and c['retained_handles_count']==0 and c['errors']==[],'ALL_HELD_HANDLES_CLOSED')
        except BaseException as exc:
            state['secondary_errors'].append(dict(phase='guard-close',error=repr(exc)))
            state['status']='STOPPED_GUARD_CLEANUP_UNCONFIRMED'
        state['publication']={k:Path(paths[k]).exists() for k in ('root','work22','snapshot23','candidate23','backup23','verify23')}
        state['recoverability']=dict(original22_retained=True,old_backup22_path=paths['backup22'],opaque_key_path=paths['key'],
            key_bytes_read_by_caller=False,new_registration_required=True,automatic_recovery=False)
        if created:
            try:state['closed_receipt_ref']=save(root,'case.closed.json',state)
            except BaseException as exc:
                state['secondary_errors'].append(dict(phase='closed-receipt-save',error=repr(exc)))
                state['status']='STOPPED_CLOSED_RECEIPT_PUBLICATION_FAILED'
    print(json.dumps(state,ensure_ascii=False),flush=True)
    return state

def main(args):
    need(len(args) in (4,7),'MODE_AND_EXACT_REF_ARGUMENTS')
    mode=args[0];ref=dict(path=args[1],sha256=args[2],bytes=int(args[3]))
    if mode=='build':need(len(args)==4,'BUILD_ARGS');result=build(ref)
    elif mode=='check':need(len(args)==4,'CHECK_ARGS');result=registration('check',ref)
    elif mode=='activate':
        need(len(args)==7,'ACTIVATION_ARGS')
        result=registration('activate',ref,dict(path=args[4],sha256=args[5],bytes=int(args[6])))
    elif mode=='execute':
        need(len(args)==7,'PREENTRY_CAPTURE_ARGUMENTS')
        result=execute(ref,dict(path=args[4],sha256=args[5],bytes=int(args[6])))
        print(json.dumps(dict(mode=mode,result=result,formal_acceptance=False),ensure_ascii=False),flush=True)
        return 0 if result['status']=='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW' else 1
    else:raise ValueError('EXACT_FOUR_MODES_ONLY')
    print(json.dumps(dict(mode=mode,result_ref=result,formal_acceptance=False),ensure_ascii=False),flush=True)
    return 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
