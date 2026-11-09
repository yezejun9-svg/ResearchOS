from pathlib import Path
import ast, datetime, hashlib, json, types

D=Path(__file__).resolve().parent
B=D.parent.parent
N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-02'
OLD=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-01'
W=B.parents[1]/'W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('independent_receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
def read(p):return json.loads(Path(p).read_bytes())
c=s.inert(N/'public22_to23_root.source.py')
h=read(N/'HDF.json');mf=read(N/'MF.json');i=read(N/'source-inputs.json')
inverse=read(N/'revision-inverse.json');prefix=read(N/'historical-review-prefix.json')
author_audit_path=S/'w09.public22-main23-continuation-source02.actual-audit.root.json'
author_audit=read(author_audit_path)
runtime=read(D/'runtime-public-closure.json')
refs=[s.pin(__file__),s.pin(HELPER),s.pin(N/'HDF.json'),s.pin(N/'MF.json'),h['caller_ref'],
    h['source_inputs_ref'],h['calling_contract_ref'],h['revision_inverse_ref'],h['source_controls_ref'],h['historical_review_prefix_ref'],
    inverse['original_ref'],*prefix['independent_changes_required_refs'],prefix['prior_counterexample_ref'],
    prefix['prior_781_resource_closure_ref'],*prefix['prior_guard_closed_refs'],
    s.pin(author_audit_path),author_audit['original_capture_ref'],s.pin(D/'runtime-public-closure.json'),runtime['guard_closed_ref']]
refs=c.refs_unique(refs)
guard=s.guard();checks=[];result=dict(schema='researchos.public22-continuation-independent-delta-review.v1',
    actor_id='codex:/root/full_w09_source_review',source_author=c.AUTHOR,checks=checks,
    synthetic_controls_only=True,product_calls=0,execution_grant=False,formal_acceptance=False)
def check(name,ok,details=None):checks.append(dict(name=name,passed=bool(ok),details=details))
try:
    guard.acquire(refs)
    check('Source02_HDF_exact',s.pin(N/'HDF.json')==dict(path=str(N/'HDF.json'),sha256='59c0917ac7b778a6c15308602e73f2d4a47175958559bd2cca20bbda24f6373d',bytes=5790))
    check('Source02_MF_complete_already_held_by_resource_probe',h['manifest_ref']==s.pin(N/'MF.json') and all(r in runtime['held_input_refs'] for r in mf['members']),dict(member_count=len(mf['members'])))
    newer=guard.get_buffer(h['caller_ref']['path']);older=guard.get_buffer(inverse['original_ref']['path']);reconstructed=newer
    unique=[]
    for block in inverse['replacement_blocks']:
        after=block['after'].encode();before=block['before'].encode();unique.append(reconstructed.count(after)==1)
        reconstructed=reconstructed.replace(after,before,1)
    check('complete_byte_inverse_to_01',all(unique) and reconstructed==older,dict(before=inverse['original_ref'],after=h['caller_ref']))
    def definitions(raw):
        return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(raw).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
    olddefs,newdefs=definitions(older),definitions(newer)
    changed=[k for k,v in olddefs.items() if newdefs.get(k)!=v];added=[k for k in newdefs if k not in olddefs]
    check('exact_function_delta_and_authority_gate_unchanged',set(changed)=={'execute','record_observation'} and set(added)=={'retain_observation','ObservedOutput'},dict(changed=changed,added=added,unchanged_count=len(olddefs)-len(changed)))
    check('source_inputs_bytes_unchanged',s.pin(OLD/'source-inputs.json')['sha256']==h['source_inputs_ref']['sha256'],dict(source_inputs_ref=h['source_inputs_ref']))
    author_controls=read(N/'delta-source-controls.json')
    check('reuse_author_three_closed_output_controls_without_rerun',author_controls['count']==3 and all(x['passed'] for x in author_controls['controls']) and author_controls['actual_Native_Go_SQL_TP_Rootstage_calls']==0,dict(ref=h['source_controls_ref']))
    oldreview=read(prefix['independent_changes_required_refs'][2]['path'])
    check('prior_finding_and_resource_prefix_preserved',oldreview['decision']=='SOURCE_CHANGES_REQUIRED' and prefix['old14_success_preserved_not_rerun'] is True and prefix['prior_review_runtime_closure_reviewed'] is False,dict(ref=prefix['independent_changes_required_refs'][2],historical_781_ref=prefix['prior_781_resource_closure_ref']))
    raw=guard.get_buffer(author_audit['original_capture_ref']['path']);lines=raw.splitlines(keepends=True);rows=[c.strict(v) for v in lines]
    offsets=author_audit['source_line_offsets'];raw_ranges_ok=True
    with Path(c.ROOT_AUDIT).open('rb') as f:
        for off,line in zip(offsets,lines):f.seek(off);raw_ranges_ok=raw_ranges_ok and f.read(len(line))==line
    head,meta,final=rows;fp=final['payload'];required_delivery=[s.pin(N/'HDF.json'),s.pin(N/'MF.json'),h['calling_contract_ref'],h['caller_ref']]
    check('actual_Attach_author_Root_peer_three_records_and_original_offsets',len(lines)==3 and all(x.endswith(b'\n') for x in lines) and head['payload']['id']==c.ROOT_THREAD and meta['type']=='inter_agent_communication_metadata' and final['ordinal']==meta['ordinal']+1 and meta['timestamp']==final['timestamp'] and fp['type']=='agent_message' and fp['author']==c.AUTHOR.removeprefix('codex:') and fp['recipient']=='/root' and final['metadata']['client_authored'] is False and raw_ranges_ok and author_audit['original_line_sha256']==[hashlib.sha256(x).hexdigest() for x in lines] and all(c.contains_ref(fp['content'],ref) for ref in required_delivery),dict(audit_ref=s.pin(author_audit_path),source_line_offsets=offsets,original_line_bytes=[len(x) for x in lines],timestamp=final['timestamp']))
    # Only new combined failure/preservation edges. Author normal/stdout/stderr cases are reused.
    class CloseFaultStream:
        def __init__(self,label,events):self.label=label;self.events=events
        def close(self):self.events.append(self.label+'-close');raise OSError(self.label+' independent CLOSE_FAULT')
    class FakePath:
        def __init__(self,label,events):self.label=label;self.events=events
        def open(self,mode):self.events.append(self.label+'-'+mode);return CloseFaultStream(self.label,self.events)
    invocation=dict(observation=None,actual_exit=None);state=dict(secondary_errors=[]);events=[];primary=RuntimeError('BODY_PRIMARY_NO_OBSERVATION');caught=None
    try:
        with c.ObservedOutput(FakePath('stdout',events),'stdout',invocation,state),c.ObservedOutput(FakePath('stderr',events),'stderr',invocation,state):raise primary
    except BaseException as exc:caught=exc
    check('unknown_child_exit_NULL_and_primary_body_preserved_under_both_close_faults',caught is primary and invocation['observation'] is None and invocation['actual_exit'] is None and len(state['secondary_errors'])==2 and [x['phase'] for x in invocation['output_close_errors']]==['stderr-close','stdout-close'],dict(invocation=invocation,secondary_errors=state['secondary_errors'],events=events))
    observation=dict(actual_exit=7,creation_time_100ns=0xffffffffffffffff,job_cleanup=dict(handles_closed=True,job_idle_confirmed=True,errors=[]))
    invocation={};c.retain_observation(invocation,observation,1234567890123456789)
    check('known_nonzero_exit_and_uint64_FILETIME_exact_integer_retention',invocation['observation'] is observation and invocation['actual_exit']==7 and invocation['creation_time_100ns_decimal']=='18446744073709551615' and int(invocation['creation_time_100ns_decimal'])==observation['creation_time_100ns'] and invocation['observation']['job_cleanup'] is observation['job_cleanup'],dict(invocation=invocation))
    primary=OSError('PIN_PRIMARY');caught=None
    def bad_pin(path):raise primary
    try:c.record_observation(invocation,observation,987654321,'unused-stdout','unused-stderr',bad_pin)
    except BaseException as exc:caught=exc
    check('fallible_hash_preserves_returned_exit_and_Job_cleanup',caught is primary and invocation['observation'] is observation and invocation['actual_exit']==7 and invocation['ended_at_unix_ns']==987654321 and 'stdout_ref' not in invocation,dict(invocation=invocation))
    invocation=dict(observation=None,actual_exit=None);state=dict(secondary_errors=[]);events=[];caught=None
    try:
        with c.ObservedOutput(FakePath('stdout',events),'stdout',invocation,state),c.ObservedOutput(FakePath('stderr',events),'stderr',invocation,state):c.retain_observation(invocation,observation,1234)
    except BaseException as exc:caught=exc
    check('both_close_faults_preserve_inner_primary_and_known_nonzero_observation',type(caught) is OSError and str(caught)=='stderr independent CLOSE_FAULT' and invocation['observation'] is observation and invocation['actual_exit']==7 and [x['phase'] for x in state['secondary_errors']]==['stdout-close'],dict(invocation=invocation,secondary_errors=state['secondary_errors']))
    invocation={};c.retain_observation(invocation,dict(actual_exit=None,creation_time_100ns=None,job_cleanup=dict(handles_closed=True)),1234)
    check('unobserved_exit_and_FILETIME_stay_NULL',invocation['actual_exit'] is None and invocation['creation_time_100ns_decimal'] is None,dict(invocation=invocation))
    rg=read(runtime['guard_closed_ref']['path'])
    check('actual_public_runtime_closure_exact149_and_guard_closed',runtime['complete_exact_loaded_public_closure'] is True and runtime['missing']==[] and runtime['locked_Python_path_and_sha'] is True and runtime['locked_Python_flags']==dict(isolated=1,no_site=1,dont_write_bytecode=True,utf8_mode=1) and rg['closed'] is True and rg['retained_handles_count']==0 and rg['errors']==[],dict(runtime_ref=s.pin(D/'runtime-public-closure.json'),required_count=runtime['required_count'],manifest_count=runtime['runtime_manifest_resource_count'],excluded_instrumentation=runtime['excluded_instrumentation_refs']))
    check('Root_lease_scope_TP_counter_and_false_acceptance_not_changed',all(newdefs[name]==olddefs[name] for name in ('source_chain','root_request','projection','registration','runtime_refs','live','original_evidence')) and h['execution_grant'] is False and h['formal_acceptance'] is False and h['original1025']=='FAILED_RETAINED',dict(original_failure_ordinals=h['original_failure_ordinals']))
    result['code_evidence']=s.code_evidence(newer,N/'public22_to23_root.source.py',['retain_observation','record_observation','ObservedOutput','runtime_refs','source_chain','execute'])
    result['held_refs']=refs
finally:
    result['guard_closed_ref']=s.write('delta-sourceguard.closed.json',guard.close())
result['passed_count']=sum(x['passed'] for x in checks);result['check_count']=len(checks)
result['all_passed']=all(x['passed'] for x in checks)
s.write('independent-delta-result.json',result)
s.write('actual-runtime-probe-hostpair.json',s.capture('d8a4e4',0,0))
print(json.dumps(dict(check_count=len(checks),passed=result['passed_count'],failed=[x for x in checks if not x['passed']],guard_closed_ref=result['guard_closed_ref'],product_calls=0),ensure_ascii=False))
