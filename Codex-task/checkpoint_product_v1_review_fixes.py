import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp606'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpfile=ROOT/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==605 and len(cp['failure_counters'])==2449 and not OUT.exists()
pins={'product-v1-workbench-independent-qa-20261104/review01/review.json':'627c1c1977906aa94f058606f00bb24f58659133c5420643fce9253539783767','product-v1-backend-author/final/source-manifest.json':'ddfcfd8530b1fe88aa065c02bae3a9443e8354939a8649ec2bc5e5c4411ce3f5','product-v1-managed-environment-author/FROZEN.json':'516db4d831df24bb74d59eed7f4e33f0fec62635e88d2048f00733db7314cbb4','cp605-desktop-resource-readiness/MANIFEST.json':'17ec363e75450a387d487e5ff14548102374f6b2114154a6e6c022406ba12c6d'}
for ref,digest in pins.items():assert sha(HERE/ref)==digest,ref
OUT.mkdir();(OUT/'checkpoint.cp605.before.json').write_bytes(raw);now=datetime.now(timezone.utc).isoformat()
nextstep='Finish independent QA of new UI/backend freezes and managed discovery environment. Integrate approved exact source slices serially, build one clean source-bound Windows tree, then verify actual Codex/GUI using fresh owned data/userData. Source and fixture checks never imply V1 journey acceptance.'
progress=dict(checkpoint_revision=606,at=now,status='INDEPENDENT_REVIEW_CORRECTIONS_IN_PROGRESS',main_head=cp['current_Main_HEAD'],evidence_pins=pins,
 workbench=dict(freeze01='NEEDS_FIX',defect='Late ACK clears newer draft, including edit-back-to-original-text.',correction='Two exact-scope paths updated; author46pure and Vite passed, new freeze and independent QA pending.'),
 backend=dict(freeze01='MARKER_FIX_REQUIRED',author_checks='fmt/test/vet0;23pass+1helperSKIP;oldparser12pass',independent_checks='freeze01 focused23pass+1helperSKIP;18pins NoDrift; not approved.',defect='Empty .git without HEAD skipped by Codex0.166 root discovery; replace with dedicated Host marker.',correction='Author may now fix within original18 paths after old focused QA ended.'),
 managed_environment=dict(scope_ref='execution/product-v1/receipts/single-harness-20261104/managed-environment/scope.json',status='FROZEN_FOR_INDEPENDENT_QA',checks='syntax0,22purePASS,diffcheck0',purpose='Minimal non-secret installed CLI discovery environment; no auth copying.'),
 resources=dict(status='LOCKED_LOCAL_RESOURCES_FOUND_NOT_RUNTIME_QUALIFIED',installation_needed='NOT_ESTABLISHED',owned_supervisor='C-only preparation'),
 active_source_owners=['codex:/root/resource_controller_review','codex:/root/delivery_binding_impl'],product_v1_journeys_accepted=0,product_v1_journeys_required=13,legacy_formal_accepted=0,legacy_formal_required=42,historical_records=2449,old_records_reset=False,pending_diagnostics='Original author/QA/source/fixture/tool diagnostics and raw attempts retained; aggregate unique origins at source closure. No failed attempt erased.',old_worktrees_paused=True,real_model_requests=0,real_electron_qualification='NOT_RUN',next=nextstep)
put(OUT/'RESUME.json',progress)
leasesfile=ROOT/'execution/product-v1/leases.json';lr=leasesfile.read_bytes();leases=json.loads(lr);(OUT/'leases.before.json').write_bytes(lr)
for s in leases['source_owners']:s['status']='FROZEN_FOR_INDEPENDENT_QA' if s['scope_id']=='PRODUCT_V1_MANAGED_HARNESS_DISCOVERY_ENV' else 'IMPLEMENTING_CORRECTION'
assert sum(s['status'].startswith('IMPLEMENTING') for s in leases['source_owners'])==2
leases.update(revision=leases['revision']+1,at=now);put(leasesfile,leases)
statefile=ROOT/'execution/product-v1/state.json';sr=statefile.read_bytes();s=json.loads(sr);(OUT/'state.before.json').write_bytes(sr)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=nextstep,active_scopes=leases['source_owners']);put(statefile,s)
cp.update(revision=606,expected_previous_revision=605,updated_at=now,next_command=nextstep+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=progress['active_source_owners'],formal_increment=0)
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(OUT/'handoff.cp605.before.md').write_bytes(before)
t=handoff.with_name(handoff.name+'.cp606.new');assert not t.exists();t.write_bytes(('# Current resume CP606 — INDEPENDENT REVIEW CORRECTIONS\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. UI draft and backend marker fixes need new independently reviewed freezes before integration. Managed environment2-file source has22pure checks; independent QA pending. V1 journeys0/13; real Harness and Electron NOT_RUN. Historical failures, UNKNOWN and paused worktrees preserved.\n\n').encode('utf8')+before);os.replace(t,handoff)
(OUT/'checkpoint_product_v1_review_fixes.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=606,main_head=cp['current_Main_HEAD'],active_source_authors=2,journeys_accepted=0,historical_records=2449)))
