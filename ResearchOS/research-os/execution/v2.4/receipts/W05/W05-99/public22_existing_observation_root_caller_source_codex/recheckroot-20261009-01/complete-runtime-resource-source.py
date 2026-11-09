"""Explicit Source supplement for original 1043; no runtime gate relaxation."""
import json,types
from pathlib import Path
N=Path(__file__).resolve().parent
def main():
    p=N/'public22_recheck_root.source.py';m=types.ModuleType('complete_runtime_source');m.__file__=str(p)
    exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
    old_raw=(N/'source-inputs.json').read_bytes();i=m.strict(old_raw);old=m.doc(i['runtime_resources_ref'])
    additions=[m.GUARD_REF,m.TP_REF]
    for ref in additions:m.need(any(m.same(ref,r) for r in i['source_resource_refs']),'EXISTING_SOURCE_CLOSURE_REQUIRED')
    guard=m.load(m.GUARD_REF,'supplement_SourceGuard').SourceReadGuard(per_file_cap=m.MAX,total_cap=2*1024*1024*1024)
    try:
        resources=m.refs_unique(old['resource_refs']+additions);guard.acquire(resources)
        complete=dict(old,resource_refs=resources,prior_runtime_manifest_ref=i['runtime_resources_ref'],explicit_added_resource_refs=additions,
            reason='Original1043 strict subset rejected two explicitly required Source modules omitted from initial runtime-only list.',
            gate_unchanged=True,original1043_result='FAILED_RETAINED',requires_non_author_Source_review=True)
        ref=m.save(N,'runtime-resources.complete.json',complete)
        with (N/'source-inputs.initial.json').open('xb') as f:f.write(old_raw)
        i['runtime_resources_ref']=ref
        m.need((N/'source-inputs.json').read_bytes()==old_raw,'UNCHANGED_INITIAL_INPUTS')
        (N/'source-inputs.json').write_bytes(m.encoded(i))
    finally:
        closed=guard.close();m.save(N,'runtime-supplement-guard.closed.json',closed)
        m.need(closed['closed'] is True and not closed['errors'] and closed['retained_handles_count']==0,'SUPPLEMENT_GUARD_CLOSED')
    print(json.dumps(dict(status='SOURCE_RUNTIME_MANIFEST_COMPLETED_PENDING_REVIEW',old_count=len(old['resource_refs']),new_count=len(resources),new_manifest_ref=ref),ensure_ascii=False))
if __name__=='__main__':main()
