"""Additional real peer spelling and immutable readonly-scope controls."""
import copy,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    m=types.ModuleType('peer_scope_controls');m.__file__=str(N/'public22_recheck_root.source.py')
    exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    rows=[]
    def check(name,ok,detail=None):
        if not ok:raise AssertionError(name)
        rows.append(dict(name=name,status='PASS',detail=detail))
    def reject(name,fn,code):
        try:fn()
        except (ValueError,KeyError,TypeError) as exc:check(name,code in str(exc));return
        raise AssertionError(name+' ACCEPTED')
    capture=dict(path=str(m.V/'receipts/W09/W09-99/full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261009-01/actual-Source-author-real-Root-peer.raw.jsonl'),
        sha256='e7f9d0880969406fb1438f8d2ef038f4c6313a885d9eb8b730a814e34d7b128e',bytes=24290)
    raw=m.checked(capture);lines=raw.splitlines(keepends=True);parsed=[json.loads(v) for v in lines]
    binding=dict(original_capture_ref=capture,source_audit_path=m.ROOT_AUDIT,source_prefix_size_observed=Path(m.ROOT_AUDIT).stat().st_size,
        source_line_offsets=[0,262908277,262908411],source_line_bytes=[len(v) for v in lines],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in lines])
    ref=m.save(N,'real-Source-peer.mapping-control.binding.json',binding)
    seen=m.audit(ref,m.AUTHOR,[])
    check('real_peer_canonical_actor_maps_to_raw_author',parsed[2]['payload']['author']=='/root/native_temp_independent_review'
        and seen['result']['payload']['author']==m.AUTHOR.removeprefix('codex:'))
    reject('raw_actor_string_cannot_replace_canonical_input',lambda:m.audit(ref,'/root/native_temp_independent_review',[]),'CANONICAL_PEER_ACTOR')
    reject('foreign_peer_actor_rejected',lambda:m.audit(ref,'codex:/root/other_actor',[]),'ACTUAL_PEER_DELIVERY_TO_ROOT')
    i=m.inputs()
    reject('real_peer_metadata_does_not_grant_unbound_ref',lambda:m.audit(ref,m.AUTHOR,[i['case_request_ref']]),'STRUCTURED_FULL_REF_AUDIT_BINDING')
    r=i['case_request_ref'];q=dict(case_request_ref=r,evidence=i['evidence'],receipt_root='CONTROL_RECEIPT',lease_id='a'*32,
        lease_issued_at='CONTROL_ISSUED',lease_expires_at='CONTROL_EXPIRES')
    source=dict(leaf=dict(contract_ref=i['leaf_contract_ref'],runner_ref=i['leaf_runner_ref']));old=dict(case=dict(output_root='CONTROL_OLD_CASE'))
    scope=m.scope_projection(q,r,source,old)
    check('scope_projection_readonly_flags',scope['new_native_children']==0 and scope['formal_acceptance'] is False
        and scope['parent_acceptance'] is False and scope['original1025_result']=='FAILED_RETAINED' and scope['mode']==m.MODE)
    check('scope_preserves_original_case_ref_and_nine_refs',scope['case_request_ref']==i['case_request_ref'] and scope['evidence']==i['evidence'])
    for field,value in [('new_native_children',4),('formal_acceptance',True),('leaf_runner_ref',r),('evidence',{}),('original_case_root','OTHER')]:
        bad=copy.deepcopy(scope);bad[field]=value
        check('exact_scope_rejects_'+field,bad!=m.scope_projection(q,r,source,old))
    result=m.save(N,'identity-and-scope-controls.json',dict(status='PASS_SOURCE_ONLY',controls=rows,real_peer_binding_ref=ref,
        actual_peer_example_is_not_new_review_authority=True,SQL_queries=0,new_native_children=0,actual_registration=False,
        original1043_result='FAILED_RETAINED',original1025_result='FAILED_RETAINED',execution_grant=False,formal_acceptance=False))
    print(json.dumps(dict(status='PASS_SOURCE_ONLY',checks=len(rows),result_ref=result),ensure_ascii=False))
if __name__=='__main__':main()
