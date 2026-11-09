import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp683'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.cp683.new');assert not t.exists()
 with t.open('xb') as f:
  b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8');assert f.write(b)==len(b);f.flush();os.fsync(f.fileno())
 os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==682 and len(cp['failure_counters'])==2627 and cp['current_Main_HEAD']=='998fc6330ba735056cd31f8ebf68dd50a8251c1b' and not OUT.exists()
audit=BASE/'build13-independent-audit/REVIEW.json';assert sha(audit)=='03fcd1f62d53cfa73cf52481ddc50a7ce3f94cb1593bdd1dd0869180458c3f46'
a=read(audit);assert a['decision']=='BUILD_VERIFIED_NOT_NATIVE_QUALIFIED' and a['pending_blockers']==[]
post=BASE/'build13-root-evidence/product-v1-build13-root-postcheck.json';assert sha(post)=='0e15693b7e53607d05de49b5d95c5394865369882e23e5f8885eb2b5f4286f1b';p=read(post)
assert p['source_pins_verified']==67 and p['bundle_files_verified']==135 and p['protected_original_paths_verified']==18 and p['new_app_helper_native_model_calls']==0
now=datetime.now(timezone.utc).isoformat();original=list(cp['failure_counters']);known={x.get('origin_key') for x in original}
events=[
 dict(origin_key='build13-independent-review:readback-tool-errors',classification='REVIEW_TOOL_DIAGNOSTICS_CORRECTED_NOT_BUILD_FAILURE',attempts=5,detail='Independent reviewer recorded Git subprocess access denial, PowerShell H/Get-History alias collision, two null-property repair attempts, and a parser error before execution. Corrected explicit Get-AuditHash/Stop-on-error full readback completed. Frozen audit retains unusable null readback. These are review-tool diagnostics, not Native/model failures.'),
 dict(origin_key='native-synthetic-registrar:snapshot-exclusion-set',classification='PRE_EXECUTION_REGISTRAR_SOURCE_FINDING',attempts=1,detail='Unexecuted candidate01 required all67 union pins in Desktop snapshot, but snapshot covers58. Explicit9 CLI3/UItests6 exclusions required while every67 WT pin stays checked. Original candidate/review preserved; rev2 implementation running, no registration/App/Task.'),
 dict(origin_key='native-synthetic-registrar:outer-authority-scope-directory',classification='PRE_EXECUTION_REGISTRAR_SOURCE_FINDING',attempts=1,detail='Unexecuted candidate01 wrote outer only under review output; original f13 requires CONTROL/scopes. Fix formal authority path with exclusive same-byte review copy and fresh scope/run prechecks. No original Job or task launched.')]
for event in events:
 assert event['origin_key'] not in known
 cp['failure_counters'].append(dict(at=now,counter_reset=False,**event));known.add(event['origin_key'])
assert cp['failure_counters'][:len(original)]==original
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
progress=dict(checkpoint_revision=683,at=now,status='BUILD13_INDEPENDENTLY_VERIFIED_ACTUAL_SCOPE_REGISTRAR_FIXING',main_head=cp['current_Main_HEAD'],desktop=dict(bundle='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-13-20261105/.local/desktop-v1-build-13',manifest_sha256='5d9277b3d7be35f8577325859c2033d612dbad0b6077902964be15637533ad85',core_sha256=p['core_sha256'],bundle_files=135,scope_input_rows=91,integrated_source_pins=67,desktop_snapshot_pin_overlap=58,excluded_from_snapshot='CLI3 and UItests6; all67 independently hash-verified in Main/WT/state/scope, no drift',protected_old_paths=18,job_processes=1363,job_stop_proved=True,elapsed_seconds=p['elapsed_seconds'],native_tested=False),build_review_ref=str(audit.relative_to(ROOT)),build_review_sha256=sha(audit),root_postcheck_ref=str(post.relative_to(ROOT)),root_postcheck_sha256=sha(post),controller='prep02 independently approved/5 pure tests; source and fixture only',poststop='prep02 independently approved/6 pure tests; full live filesystem verifier not executed',actual_registrar='candidate01 source blocked on exactly2 fail-closed defects; original archived, candidate-rev2 implementation explicitly started via followup; no scope or freshGUIroot created',running_long_commands=[],real_model_requests=1,new_real_model_requests=0,actual_new_native_qualifications=0,product_journeys_accepted=0,product_journeys_required=13,legacy_formal_accepted=0,legacy_formal_required=42,historical_records=len(cp['failure_counters']),old_records_reset=False,origin_aliases={'product-v1-build-13:serial12-reference-corrected-before-execution':'root:desktop-build13-unconsumed-wrapper-reference','product-v1-build-12:original-helper-provenance-input-mismatch':'root:desktop-build12-helper-origin-input'},next='Finish registrar rev2 exact2 fixes, independently delta-review then run fresh supervised readonly artifact preflight (import helpers, never main). Only after actual pins pass register one new conditional synthetic Harness flow with exact fresh GUI root and original f13 Job. Preserve all old Task/echo2of2/failures/UNKNOWN; no duplicate operation or scope replay. No full product/formal completion claim.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';sr=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sr)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_BUILD13_INDEPENDENTLY_VERIFIED_NOT_NATIVE_TESTED',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False))
cp.update(revision=683,expected_previous_revision=682,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],formal_increment=0)
assert cpf.read_bytes()==raw and sf.read_bytes()==sr;put(sf,s);put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp683.new');assert not t.exists();t.write_bytes(('# Current resume CP683 - BUILD13 VERIFIED; REAL FLOW NOT RUN\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Build13 ended success, full135bundle/91scope rows/67integrated pins verified independently; all old18 paths protected. No running Root commands, no new Task/Native/model. Registrar rev2 exact2 fixes underway; do not execute candidate01. Old scopes/failures/UNKNOWN retained; journeys0/13 and legacyformal0/42.\n\n').encode('utf8')+old);os.replace(t,hf)
(OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=683,head=progress['main_head'],historical_records=progress['historical_records'],build_files=135,new_native_model_calls=0,long_commands=0)))
