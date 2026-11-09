"""Fresh Root context after an exact independent CP369 Source decision; no Canon write."""
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
import sys, types
N=Path(__file__).resolve().parent
writer=N/'register_cp369.source.py'
raw=writer.read_bytes()
assert len(raw)==14628 and hashlib.sha256(raw).hexdigest()=='b0c4e3efdc5a1500d57ad804a9b6f56c7d46f20e10e887db70ee9c1735ac4adb'
m=types.ModuleType('cp369_root_postseal');m.__file__=str(writer);sys.modules[m.__name__]=m
exec(compile(raw,str(writer),'exec'),m.__dict__)
def main():
    m.require(len(sys.argv)==4,'SPEC_PATH SPEC_SHA SPEC_BYTES')
    spec_ref=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]));spec=m.load(spec_ref)
    m.require(set(spec)=={'schema','issued_by','source_review_handoff_ref','source_review_manifest_ref','pending_diagnostics_ref','next_original_failure_ordinal'},'EXACT_ROOT_SPEC')
    m.require(spec['schema']=='researchos.root-cp369-postseal-context-spec.v1' and spec['issued_by']==m.ACTOR,'ROOT_SPEC')
    rh,refs=m.pair(spec['source_review_handoff_ref'],spec['source_review_manifest_ref']);dr=rh['source_decision_ref'];d=m.load(dr)
    m.require(dr in refs and rh['actor_id']==d['actor_id'] and d['actor_id']=='codex:/root/native_temp_independent_review','SEALED_INDEPENDENT_DECISION_MEMBER')
    m.require(d['schema']=='researchos.root-cp369-native-independent-source-decision.v1' and d['decision']=='SOURCE_ACCEPTED_FOR_ROOT_CP369_MAIN_C19_REGISTRATION' and d['actor_role']=='INDEPENDENT_NON_AUTHOR','NONAUTHOR_SOURCE_ACCEPTED')
    for key in ('all_handles_closed',):m.require(d[key] is True,'CLOSED_REVIEW')
    m.require(type(d['retained_handles_count']) is int and d['retained_handles_count']==0 and d['actual_executed'] is False and type(d['formal_case_accepted_delta']) is int and d['formal_case_accepted_delta']==0,'SOURCE_ONLY_BOUNDARY')
    facts_ref=m.pin(N/'checkpoint.execution.facts.json');facts=m.load(facts_ref)
    expected=dict(source_handoff_ref=m.pin(N/'HDF.json'),source_manifest_ref=m.pin(N/'MF.json'),writer_ref=m.pin(writer),facts_ref=facts_ref,scope_ref=facts['scope_ref'],current_before_canonical_refs=facts['canonical_refs'])
    m.require(all(d[key]==ref for key,ref in expected.items()),'FULL_EXACT_SOURCE_REVIEW_BINDING')
    for ref in facts['canonical_refs']:m.read(ref)
    ident=dict(path=str((m.R/'execution/project_identity.json').resolve(strict=True)),sha256='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',bytes=420)
    m.require(m.load(ident)['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','CURRENT_PERMANENT_IDENTITY')
    pending=m.load(spec['pending_diagnostics_ref']);next_live=spec['next_original_failure_ordinal']
    m.require(pending['schema']=='researchos.root-diagnostic-pending.v1' and pending['issued_by']==m.ACTOR and pending['source_cutoff']=={'highest_ordinal':965,'next_failure_ordinal':966} and pending['next_original_failure_ordinal']==next_live,'ROOT_ALL_POSTCUT_PENDING')
    live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by=m.ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=pending['source_cutoff'],next_original_failure_ordinal=next_live,pending=pending['pending'])
    m.validate_live(live)
    lr=m.save('live-context.postseal.actual.root.json',live)
    proof=m.save('postseal-authorization-check.root.json',dict(schema='researchos.root-cp369-postseal-authorization.v1',source_review_handoff_ref=spec['source_review_handoff_ref'],source_review_manifest_ref=spec['source_review_manifest_ref'],source_decision_ref=dr,**expected,identity_ref=ident,live_context_ref=lr,all_postcut_originals_included=True,actual_Canon_executed=False,formal_case_accepted_delta=0))
    argv=[str(Path(sys.executable).resolve(strict=True)),'-I','-S','-B','-X','utf8',str(writer.resolve(strict=True)),'activate',facts_ref['sha256'],str(facts_ref['bytes']),lr['path'],lr['sha256'],str(lr['bytes'])]
    ar=m.save('registration.argv.postseal.actual.root.json',dict(schema='researchos.root-cp369-canonical-argv.v1',argv=argv,cwd=str(m.R),live_context_ref=lr,authorization_ref=proof,current_before_canonical_refs=facts['canonical_refs'],Source_actual_grant_only=True,formal_case_accepted_delta=0))
    print(json.dumps(dict(argv_ref=ar,live_context_ref=lr,source_review_handoff_ref=spec['source_review_handoff_ref'],next_original_failure_ordinal=next_live,actual_Canon_executed=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
