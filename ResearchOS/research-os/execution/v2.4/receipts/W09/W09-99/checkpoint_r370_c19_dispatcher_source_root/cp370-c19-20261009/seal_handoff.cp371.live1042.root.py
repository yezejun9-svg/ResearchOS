from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[v for v in t.body if isinstance(v,ast.FunctionDef) and v.name in ('pin','save','outputs','capture')],type_ignores=[]),'prior_root_helpers_only','exec'),globals())
priorpath=N/'RESUME.cp371-source-sealed.live1041.root.json';resume=json.loads(priorpath.read_bytes())
canonical=resume['canonical_refs'];assert [pin(Path(v['path'])) for v in canonical]==canonical
captured=capture(AUDIT,1041,lambda c,r:any(v.get('chunk_id')=='8d2665' for v in outputs(r['payload'].get('output'))),root=True);assert captured
pending=json.loads(Path(resume['pending_diagnostics_ref']['path']).read_bytes())
pending['pending'].append(dict(ordinal=1041,origin_ref=captured[0],origin_selector='$',description='Root queried an unlisted Main23 Source contract filename; its absence was reported. Actual Git identity and 11 preexisting tracked deletions unchanged. Subsequent Source reads use observed directory members only.',capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',capture_binding_ref=captured[1],actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
pending['next_original_failure_ordinal']=1042
assert [v['ordinal'] for v in pending['pending']]==list(range(1024,1042))
pendingref=save('pending-diagnostics.cp371.live1042.root.json',pending)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=pin(priorpath),pending_diagnostics_ref=pendingref,pending_diagnostic_originals=list(range(1024,1042)),next_original_failure_ordinal_live=1042,Git_branch='main',Git_HEAD='adc460c2138528f163f7fdab5e8d81dde157b7fb',preexisting_tracked_deletions=11)
pa=R/'execution/v2.4/receipts/W05/W05-99/public22_leaf_v3_independent_source_review_codex/review-01a12145'
resume.update(public22_leaf_v3_review_hdf_ref=pin(pa/'HDF.json'),public22_leaf_v3_review_mf_ref=pin(pa/'MF.json'),public22_leaf_v3_review_decision_ref=pin(pa/'decision.json'),public22_leaf_v3_recheck_contract_ref=pin(pa/'next-root-recheck-contract.json'),public22_leaf_v3_status='ACCEPTED_SOURCE_ONLY_NEW_READONLY_CALLER_PENDING_NO_RERUN')
resumeref=save('RESUME.cp371-leaf-v3-source-accepted.live1042.root.json',resume)
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK_R371.md'
text='''# ResearchOS v2.4 continuation — current Canon 371

Goal remains ACTIVE. Read the exact Root resume below before selecting a card. The older R156/R370 documents remain historical.

- Project UUID: aede0678-7308-43dc-b9f2-cfe3d90cfdfb. HEAD main adc460c2138528f163f7fdab5e8d81dde157b7fb; 11 old tracked deletions retained.
- Canon checkpoint371 / ownership175 / commands39; step_state hash unchanged. Canon failure records1021 through ordinal1023, next1024. Pending originals1024..1041 are preserved once; Root live next1042. No counters reset.
- Current formal accepted0/42. Six historical parent records cannot establish current22-parent acceptance.
- Public22 Root registration independently qualified. Four Owned children exited0, idle/closed. Original1025 remains FAILED at verify22. Independent review proved exact frozen recovery trigger and credentials revoked0→1; leaf v3 Source accepted after1964 checks and100 Source controls, no new Native call. A new reviewed Root readonly caller/Scope must bind the original case-request and all original artifacts before recheck.
- Main23 builder Source accepted; Main23 Root caller v2 repairing two Source findings, pending non-author review. Old Main23 binary drifts; no fresh build has been run.
- W09 v5/CM40 Source independently accepted but not adopted. Full G01/G02/A06 producer Source sealed69 controls, independent review underway. Old C19 Native/2 consumers already executed and reviewed; do not rerun them. Formal W09 requires current full routes, Source/Native provenance, real role captures and independent full acceptance.
- Root alone integrates Main/Canon/shared registries. Active construction parents W05/W09. Missing resources stop only the corresponding branch. No new paid provider trial while old request termination/billing remains unknown.

Exact Root resume: %s
SHA256: %s
Bytes: %s

Use contracts/execution.plan.json + tools/task_packet.py; last readonly next selection W05-99, product acceptance NOT_ASSERTED. Do not turn Source controls or old PASS into formal acceptance.
'''%(resumeref['path'],resumeref['sha256'],resumeref['bytes'])
with handoff.open('xb') as f:f.write(text.encode('utf-8'));f.flush();os.fsync(f.fileno())
handoffref=pin(handoff)
current=R/'execution/v2.4/HANDOFF_RESUME_PACK.md'
protected=False
def walk(v):
    if isinstance(v,dict):
        if set(v)=={'path','sha256','bytes'} and Path(v['path']).name=='HANDOFF_RESUME_PACK.md':yield v
        for a in v.values():yield from walk(a)
    elif isinstance(v,list):
        for a in v:yield from walk(a)
for v in canonical:
    if list(walk(json.loads(Path(v['path']).read_bytes()))):protected=True
priorref=pin(current)
if not protected:
    before=current.read_bytes()
    with (N/'historical.HANDOFF_RESUME_PACK.before-cp371-update.md').open('xb') as f:f.write(before);f.flush();os.fsync(f.fileno())
    marker=('<!-- R371 continuation: read HANDOFF_RESUME_PACK_R371.md and its exact pinned live1042 Root resume. Older continuation/body content below is historical; current Canon is authoritative. -->\n\n').encode('utf-8')
    with current.open('wb') as f:f.write(marker+before);f.flush();os.fsync(f.fileno())
    assert current.read_bytes()[len(marker):]==before
pointerref=save('HANDOFF_RESUME_POINTER.cp371.live1042.root.json',dict(issued_by='codex:/root',handoff_ref=handoffref,resume_ref=resumeref,pending_ref=pendingref,prior_canonical_handoff_ref=priorref,current_canonical_handoff_ref=pin(current),canonical_handoff_protected=protected,Canon_unchanged=True,formal_acceptance=False))
assert [pin(Path(v['path'])) for v in canonical]==canonical
print(json.dumps(dict(resume_ref=resumeref,pending_ref=pendingref,handoff_ref=handoffref,pointer_ref=pointerref,checkpoint_revision=371,Root_live_next1042=True,current_formal_accepted=0),ensure_ascii=False),flush=True)
