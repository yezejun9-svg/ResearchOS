import argparse,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104'
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp651'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
ap=argparse.ArgumentParser();ap.add_argument('--scope-sha',required=True);ap.add_argument('--review',required=True);ap.add_argument('--review-sha',required=True);a=ap.parse_args()
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==650 and len(cp['failure_counters'])==2550 and not OUT.exists()
scope=CONTROL/'scopes/product-v1-layout-visual-01.json';assert sha(scope)==a.scope_sha and not (CONTROL/'runs/product-v1-layout-visual-01').exists()
review=Path(a.review);assert sha(review)==a.review_sha;rv=read(review)
assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and rv['formal_increment']==0 and not rv['pending_blockers']
events=list(rv.get('diagnostic_events',[]))+[dict(origin_key='root-native-controller03-archive-selection-outside-source',classification='ROOT_EVIDENCE_ARCHIVE_PREFLIGHT',detail='Initial C selection lived outside its declared source root, and archive helper includes the selection itself. Path containment assertion stopped before D target creation. Readback proved target absent; new selection02 uses common C root and explicit same frozen files plus preserved original selection. Archive completed once without source modification or GUI/model action.')]
events.append(dict(origin_key='root-layout-visual01:review-candidate-schema-preflight',classification='ROOT_SCOPE_REGISTRATION_PREFLIGHT',detail='Initial new registrar expected legacy approved_revision/source_root fields; actual independent visual07 report uses selected_candidate/candidate_manifest_sha256. KeyError stopped before any registration target creation. Root read actual schema, verified target absent, and bound exact absolute selected candidate plus manifest and source hashes without altering frozen report/controller. New scope registered once; no runtime action in error.'))
for e in events:assert isinstance(e,dict) and e.get('origin_key') and e.get('classification')
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw);(OUT/'scope.json').write_bytes(scope.read_bytes());(OUT/'independent-controller-review.json').write_bytes(review.read_bytes())
now=datetime.now(timezone.utc).isoformat();known={e.get('origin_key') for e in cp['failure_counters']}
for e in events:
 if e['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**e});known.add(e['origin_key'])
progress=dict(checkpoint_revision=651,at=now,status='NATIVE_LAYOUT_VISUAL01_REGISTERED_NOT_EXECUTED',main_head=cp['current_Main_HEAD'],scope_path=str(scope),scope_sha256=sha(scope),source_review_sha256=sha(review),scope_status='REGISTERED_NOT_EXECUTED',task_budget=0,model_budget=0,automatic_retry=0,
 read_scope='Fresh owned fixture only, real invalid/valid Shell path and Main ACTIVE binding. Then actual1440/390 dark/light viewport images plus raw/clipped geometry/scroll/focus and all findings. Initial scroll values must be independently checked0; no fake DOM/CSS or model/task submit.',real_model_requests_unit='PRIOR_ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION; THIS_VISUAL_OPERATION_ZERO_MODELS',
 prior_actual06_independent_review=dict(path='execution/product-v1/receipts/single-harness-20261104/tree-diagnostic-06/independent-runtime-review/report.json',sha256='c5b55ae45f0215b7314ad750cebf06e373ef1dbacdd60eb368cd74986f75a589'),
 real_model_requests=1,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Execute only newly registered layout-visual01 under exact f13 original unnamed Job. Inspect actual Native/Mainbinding, all1440/390 dark/light viewport screenshots/geometry, eachINITIAL document/transcript scroll0, actual overlaps/overflow/keyboard focus. Preserve real findings, do not crop/scroll-hide initial failure. Normal App close/original Job accounting plus complete postbundle check. Prior model Task stays failed closed/unreplayed; resourceMXC is separate local no-model startup check only.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);put(sf,s)
cp.update(revision=651,expected_previous_revision=650,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp651.new');assert not tmp.exists()
tmp.write_bytes(('# Current resume CP651 — NEW NATIVE PATH FLOW04 REGISTERED; TASK/MODEL BUDGET ZERO\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Source2b39fe3/build07 reviewed; frozen Native controller independently approved. No actual UI from this registration; verify consumed/RESULT before executing or retrying. V1 journeys0/13; histories and UNKNOWN retained.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_layout_visual_registration.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
