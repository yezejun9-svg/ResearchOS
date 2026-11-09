"""Preserve CP369 and append the actual Main C19 / live981 recovery snapshot."""
from datetime import datetime, timezone
import hashlib, json, os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
def pin(p):
    p=p.resolve(strict=True); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(v):
    assert set(v)=={'path','sha256','bytes'} and type(v['bytes']) is int
    b=Path(v['path']).read_bytes()
    assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
    return b
def fixed(p,sha,size):
    v=dict(path=str(p.resolve(strict=True)),sha256=sha,bytes=size);read(v);return v
def save(name,obj):
    with (N/name).open('xb') as f:
        f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
canonical=[pin(R/'execution/v2.4'/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
expected=[('dd997457f14314374ee4577fff6fd87317e05ad908f4c24d01ce302af72edeb7',4370868),('da777233cf369e433d4db61f75b579cfcd9a3b9f5092f6b7acafc7c3106cc5d2',206009),('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
assert [(v['sha256'],v['bytes']) for v in canonical]==expected
for v in canonical:
    p=N/('historical.cp369.'+Path(v['path']).name)
    if p.exists(): assert p.read_bytes()==read(v)
    else:
        with p.open('xb') as f:f.write(read(v));f.flush();os.fsync(f.fileno())
identity=fixed(R/'execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',420)
pending=json.loads((N/'pending-diagnostics.live970.root.json').read_bytes())['pending']
FP=W/'w09_formal_profile_v3_source_codex/profv3-01a12c09'
first=fixed(FP/'original-tool-failures.md','f0c3c0fb22d5edfc4eb3fe505022ddd4b258289bc9cf25388e70c60bc0ef7e45',4646)
second=fixed(FP/'original-tool-failures-followup.md','094f36dfe31986931715740b6320cb1cee9dd537eeb33f6c4d5244233b2a5f32',8928)
rows=[
 (970,fixed(W/'cp369_registration_actual_independent_review_codex/review-1a12035/failure-2f1e13.original-tool-io.json','15a3b8355297bf90f3b670835c15f73bf67421e7f3ef94529ee1f76ddd76ae75',6909),'2f1e13',1,None,'Readonly guessed absent root AGENTS; later read success does not reset.'),
 (971,first,'apply_patch first verification',None,None,'Patch verification failed before mutation; every unobserved numeric exit NULL.'),
 (972,first,'50cbef',1,None,'rg Windows literal wildcard path failed; original child/outer observations retained.'),
 (973,first,'6024ee',1,None,'rg no matches exit1; no Native or dispatcher.'),
 (974,first,'apply_patch missing leading plus',None,None,'One patch verification failure; no edit; ordinal fixed by Root.'),
 (975,fixed(N/'failure975.original-tool-io.root.json','8080a1f1c12f8a9b77b1266d46756cb698956f1e1dc560bad66b6616a56b6c1e',1521),'fb70da',1,1,'Original delivery selector mismatch before capture write.'),
 (976,second,'ad6c1b',1,1,'Source control rejected CRLF normalization; no Main write.'),
 (977,second,'0a239f',1,1,'Python -c shell quoting SyntaxError before Source execution.'),
 (978,second,'fb400c',1,1,'Source negative-control expected wrong Reader ref schema; same original call output fragments counted once.'),
 (979,second,'d0305e',1,1,'Source control expected wrong original audit content type; actual input_text corrected separately.'),
 (980,fixed(W/'w09_formal_profile_v3_independent_review_codex/profv3r-01a12c09/failure-ec51ed.original-tool-io.json','71ff32b6ed7dc335a799d35a0bb7705d724dbdd80408e1a46817abe9186469dd',1538),'ec51ed',1,1,'Reviewer CRLF diff comparison assertion failed; true guard closed0; author diff subsequently verified.')] 
for ordinal,ref,selector,outer,py,description in rows:
    pending.append(dict(ordinal=ordinal,origin_ref=ref,description=description,origin_selector=selector,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
assert [v['ordinal'] for v in pending]==list(range(966,981))
for v in pending:read(v['origin_ref'])
pending_ref=save('pending-diagnostics.live981.root.json',dict(schema='researchos.root-diagnostic-pending.v1',issued_by='codex:/root',source_cutoff=dict(highest_ordinal=965,next_failure_ordinal=966),next_original_failure_ordinal=981,pending=pending,counter_reset=False))
mr=W/'main_c19_native_actual_independent_review_codex/review-1a12035-v2'
mh=fixed(mr/'HDF.json','49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270',6428)
mm=fixed(mr/'MF.json','eba83d3e4d1ade81a0566fed856e9cb3df3b1fa488f43868cf67f53b0254940a',6343)
mode=fixed(mr/'two-consumer-mode-interface.json','669208b0f10e2bb130299fb04f796695837a5911efbd9b554d110efffe7fb355',4334)
handoff=fixed(N/'Main-C19-actual-handoff.root.json','cc4e8de2bf69b1b322fb500369b85bc4d737b26f761fa746a52e8088c6257835',4474)
c=json.loads(read(canonical[0]));o=json.loads(read(canonical[1]))
assert c['revision']==369 and o['revision']==173 and len(c['failure_counters'])==963
resume=dict(schema='researchos.root-resume.v1',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),identity_ref=identity,canonical_refs=canonical,historical_canonical_refs=[pin(N/('historical.cp369.'+Path(v['path']).name)) for v in canonical],checkpoint_revision=369,ownership_revision=173,commands_revision=39,registered_failures=963,highest_registered_ordinal=965,next_at_source_cutoff=966,checkpoint_live_snapshot=970,next_original_failure_ordinal_live=981,pending_diagnostics_ref=pending_ref,Main_C19_actual_handoff_ref=handoff,Main_C19_actual_independent_handoff_ref=mh,Main_C19_actual_independent_manifest_ref=mm,Main_C19_qualified_two_consumer_interface_ref=mode,Main_C19_status='ACTUAL_MAIN_C19_NATIVE_COMPONENT_AND_FIXTURE_MODES_QUALIFIED',Main_C19_actual_consumers_run=False,W05_qualification='ACTUAL_DEVELOPMENT_13_EVIDENCE_VERIFIED_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',W09_formal_profile_source_status='V3_REQUEST_CHANGES_NATIVE_PACKAGE_TERMINAL_ORDER_V4_IMPLEMENTING',active_construction_parents=['W05','W09'],historical_parent_records=6,current_formal_accepted=0,required_parents=22,required_formal=42,formal_acceptance=False,parent_acceptance=False,counter_reset=False,next_action='Source-qualify a separately scoped Root two-consumer C19 caller using qualified MainNative and exact TEMP/TMP; register its own CP370 scope before actual dispatch. Repair remaining Native package terminal causal gap in formal profile v4. Do not repeat successful producer or claim partial C19 as W09 full acceptance.')
out=save('RESUME.cp369-native-qualified.live981.root.json',resume)
assert [pin(Path(v['path'])) for v in canonical]==canonical
print(json.dumps(dict(resume_ref=out,pending_diagnostics_ref=pending_ref,canonical_unchanged=True,formal_delta=0),ensure_ascii=False),flush=True)
