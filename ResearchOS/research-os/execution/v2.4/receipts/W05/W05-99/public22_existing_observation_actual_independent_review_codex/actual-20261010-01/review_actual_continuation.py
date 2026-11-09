"""Continue past original1065 parser error; reuse its closed held-ref proof."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import textwrap

D=Path(__file__).resolve().parent
def main():
    original_script=D/'review_actual.py';raw=original_script.read_text(encoding='utf-8')
    declarations=raw[:raw.index('def main():')]
    ns={'__file__':str(original_script),'__name__':'continuation_declarations_ONLY'}
    exec(compile(declarations,str(original_script),'exec'),ns)
    doc,pin,save=ns['doc'],ns['pin'],ns['save'];b=doc(ns['P'])
    q=doc(b['source_caller_request_ref']['path']);a=doc(b['actual_request_ref']['path'])
    facts=doc(a['facts_ref']['path']);scope=doc(a['scope_ref']['path']);source=doc(q['source_hdf_ref']['path'])
    resources=doc(source['runtime_resources_ref']['path']);m=ns['module'](source['caller_ref'],'public22_finite_continuation_NO_PRODUCT')
    state=doc(q['evidence']['returned_state_ref']['path']);assignment=doc(q['evidence']['original_assignment_ref']['path'])
    original=dict(state=state,assignment=assignment,baseline=doc(state['baseline_manifest_ref']['path']))
    prior=doc(D/'independent-Source-guard.closed.json')
    assert prior['verification']=='PASSED' and prior['closed'] is True and prior['retained_handles_count']==0 and not prior['errors']
    assert all(x['verified'] and x['final_path_match'] and x['closed'] for x in prior['entries'])
    refs=[{k:x[k] for k in ('path','sha256','bytes')} for x in prior['entries']]
    # Original traceback is after every pre-host-loop check and the first host
    # pair identity/offset/time checks. The prior guard proves all selected pins.
    prefix_ref=save('original1065-reused-prefix.json',dict(Root_assigned_ordinal=1065,original_chunk_id='420c4b',
        original_script_ref=pin(original_script),original_closed_guard_ref=pin(D/'independent-Source-guard.closed.json'),
        completed_before_parser_error=['Root real accepted Source/peer chain','original exact3 request and9 evidence',
            'registered Scope owner worker lease','loaded149 actual coverage and933 closed guard',
            'CP371/OW175 to CP372/OW176 exact projection and inverse','failureledger unchanged',
            'SS andCM39 unchanged','committed TP exclusively-held before/after archives','exact canonical owner worker'],
        evidence_basis='Original actual traceback reaches line115; original script and fully PASSED finally guard are retained.',
        already_held_refs=refs,unchanged_resource_refs_not_rehashed=True,no_failure_reset=True,
        original_outer_exit=1,original_Python_exit=1,Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None))
    continuation_refs=[pin(ns['P']),b['source_caller_request_ref'],b['actual_request_ref'],b['caller_return_ref'],b['observation_ref'],
        source['caller_ref'],scope['leaf_runner_ref'],q['evidence']['returned_state_ref'],q['evidence']['original_assignment_ref'],
        state['baseline_manifest_ref'],pin(original_script),pin(__file__),prefix_ref,pin(D/'independent-Source-guard.closed.json')]
    for record in b['records'].values():continuation_refs.extend([record['raw_ref'],record['binding_ref']])
    continuation_refs=m.refs_unique(continuation_refs)
    guard=m.load(m.GUARD_REF,'public22_finite_continuation_guard_ONLY').SourceReadGuard(per_file_cap=m.MAX,total_cap=2*1024*1024*1024)
    checks=[dict(name='reuse verified original1065 prefix; no unchanged large resource re-read',passed=True,detail=prefix_ref)]
    def check(ok,name,detail=None):
        if not ok:raise AssertionError(name)
        checks.append(dict(name=name,passed=True,detail=detail))
    segment=raw[raw.index('        hostpairs={};phases='):raw.index('    finally:\n')]
    assert segment.count("if x.get('chunk_id')==record['chunk_id']")==1
    segment=segment.replace("if x.get('chunk_id')==record['chunk_id']","if type(x) is dict and x.get('chunk_id')==record['chunk_id']")
    assert segment.count("any(x.get('schema')==")==1
    segment=segment.replace("any(x.get('schema')==","any(type(x) is dict and x.get('schema')==")
    segment=segment.replace("save('actual-independent-checks.json'","save('actual-independent-checks-v2.json'")
    segment=segment.replace('held_refs=refs,','previously_held_refs=refs,current_continuation_held_refs=continuation_refs,prefix_reuse_ref=prefix_ref,')
    ns.update(dict(b=b,q=q,a=a,facts=facts,scope=scope,source=source,resources=resources,m=m,original=original,refs=refs,
        continuation_refs=continuation_refs,prefix_ref=prefix_ref,check=check,checks=checks))
    try:
        guard.acquire(continuation_refs)
        exec(compile(textwrap.dedent(segment),'original1065_remaining_checks_dict_filter_only','exec'),ns)
    finally:
        closed=guard.close();closed_ref=save('continuation-Source-guard.closed.json',closed)
    assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
    print(json.dumps(dict(status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',evidence_ref=ns['evidence'],
        checks=len(checks),closed_guard_ref=closed_ref,reused_original1065_prefix_ref=prefix_ref,
        unchanged_large_resources_not_rehashed=True,retained_handles_count=0,SQL_queries=0,new_Native_children=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
