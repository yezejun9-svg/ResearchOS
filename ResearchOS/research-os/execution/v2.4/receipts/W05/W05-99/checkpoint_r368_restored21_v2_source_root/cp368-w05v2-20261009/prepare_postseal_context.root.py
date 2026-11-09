"""Seal a fresh Root live context after nonauthor Source acceptance, no Canon write."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import types
N=Path(__file__).resolve().parent
writer=N/'register_cp368.source.py'
m=types.ModuleType('cp368_root_context');m.__file__=str(writer);sys.modules[m.__name__]=m
exec(compile(writer.read_bytes(),str(writer),'exec'),m.__dict__)
B=m.B;W=m.R/'execution/v2.4/receipts/W09/W09-99'
REVIEW=B/'checkpoint_r368_w05_v2_independent_review_codex/cp368v2r-01a11fea'
def main():
    href=dict(path=str((REVIEW/'HDF.json').resolve(strict=True)),sha256='0e4e6ce7d0f80c6357c05e68f23197ca5868a3f8731d993c19009ff0842404c9',bytes=4609)
    mref=dict(path=str((REVIEW/'MF.json').resolve(strict=True)),sha256='db49bb6cec19bd724203099c682b30359c70cc74566af8aa9d037fc41815a1cf',bytes=4031)
    h,refs=m.pair(href,mref);d=m.load(h['source_decision_ref'])
    m.require(d['decision']=='SOURCE_ACCEPTED_FOR_ROOT_CP368_W05_REGISTRATION' and d['actor_role']=='INDEPENDENT_NON_AUTHOR' and d['actor_id']=='codex:/root/attach_fixture_source_review' and d['all_handles_closed'] is True and d['actual_executed'] is False,'SEALED_NONAUTHOR_SOURCE_ACCEPTED')
    m.require(d['source_handoff_ref']==m.pin(N/'HDF.json') and d['source_manifest_ref']==m.pin(N/'MF.json') and d['writer_ref']==m.pin(writer) and d['facts_ref']==m.pin(N/'checkpoint.execution.facts.json'),'EXACT_REVIEWED_SOURCE')
    facts=m.load(d['facts_ref'])
    for ref in facts['canonical_refs']:m.read(ref)
    ident=dict(path=str((m.R/'execution/project_identity.json').resolve(strict=True)),sha256='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',bytes=420)
    m.require(m.load(ident)['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','CURRENT_PERMANENT_IDENTITY')
    m.require(len(sys.argv)==2 and int(sys.argv[1])==957,'ROOT_CURRENT_LIVE957')
    data=[(953,B/'checkpoint_r368_w05_independent_review_codex/cp368r-01a11fea/failure953.original-tool-io.json','5526df6a460b1541612533ba44dca285bb756180568d1cc5766efb13d11f0015',1375,'Original independent CP368 Source read c3b898: outer1, guessed missing filename; Python/Native/model NULL.'),(954,W/'main_c19_root_producer_v2_independent_review_codex/review-1a11fff/failure954.original-tool-io.json','447ef857ee89b6094b798f7905cb3870fc3a72fbd4f7c0c4b3c4487bdd200e15',3469,'Original MainNative v2 Source read36b716: outer1, guessed missing HANDOFF.md; Python/Native/model NULL.'),(955,W/'w09_formal_profile_gap_map_readonly_codex/query955-20261009/original-tool-io.json','ab7867e2863e929edadada46d5bd51695b9157bbb170f5927bf5827aab1f9fb6',9614,'Original mapping query8cf996: failed rg child exit2, original outer0 after successful last child; Python/Native/model NULL.')]
    last=m.load(m.pin(N/'failure956.exact-origin.binding.root.json'))
    m.require(last['ordinal']==956 and last['actual_outer_exit']==1 and last['actual_python_exit'] is None and last['actual_native_exit'] is None,'ROOT_ORIGINAL956_BINDING')
    pending=[]
    for ordinal,p,sha,size,description in data:
        ref=dict(path=str(p.resolve(strict=True)),sha256=sha,bytes=size);m.read(ref);pending.append(dict(ordinal=ordinal,origin_ref=ref,description=description))
    m.read(last['origin_ref']);pending.append(dict(ordinal=956,origin_ref=last['origin_ref'],description=last['description']))
    live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by=m.ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=dict(highest_ordinal=952,next_failure_ordinal=953),next_original_failure_ordinal=957,pending=pending)
    m.validate_live(live)
    lr=m.save('live-context.postseal.actual.root.json',live)
    m.save('postseal-authorization-check.root.json',dict(source_review_handoff_ref=href,source_review_manifest_ref=mref,source_decision_ref=h['source_decision_ref'],source_handoff_ref=d['source_handoff_ref'],facts_ref=d['facts_ref'],writer_ref=d['writer_ref'],identity_ref=ident,canonical_refs=facts['canonical_refs'],live_context_ref=lr,all_postcut_originals_included=True,actual_Canon_executed=False,formal_case_accepted_delta=0))
    print(json.dumps(dict(live_context_ref=lr,source_review_handoff_ref=href,next_original_failure_ordinal=957,actual_Canon_executed=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
