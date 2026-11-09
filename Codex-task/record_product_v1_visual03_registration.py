import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';CONTROL=HERE/'product-v1-owned-verification-20261104';OUT=BASE/'progress-cp662'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==661 and len(cp['failure_counters'])>=2567 and not OUT.exists()
reg=read(HERE/'product-v1-layout-visual-03-registration/REGISTRATION.json');scope=Path(reg['scope_path']);assert sha(scope)==reg['scope_sha256'] and not (CONTROL/'runs/product-v1-layout-visual-03').exists()
inner=read(HERE/'product-v1-layout-visual-03-registration/real-flow.scope.json');assert inner['budget']['task_submissions']==inner['budget']['model_calls']==0 and inner['source']['head']==cp['current_Main_HEAD']
review=BASE/'layout-visual-03/independent-controller-review.json';rv=read(review);assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and not rv['pending_blockers'] and rv['formal_increment']==0
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw);(OUT/'visual03.scope.json').write_bytes(scope.read_bytes());now=datetime.now(timezone.utc).isoformat()
old_records=list(cp['failure_counters']);known={e.get('origin_key') for e in old_records}
for e in rv.get('diagnostic_events',[]):
 assert e.get('origin_key') and e.get('classification')
 if e['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**e});known.add(e['origin_key'])
assert cp['failure_counters'][:len(old_records)]==old_records
progress=dict(checkpoint_revision=662,at=now,status='BUILD10_REAL_RESPONSIVE_VISUAL03_REGISTERED_NOT_EXECUTED',main_head=cp['current_Main_HEAD'],visual=dict(scope_id='product-v1-layout-visual-03',scope_sha256=sha(scope),review_sha256=sha(review),source_head=reg['source_head'],bundle_manifest_sha256=reg['bundle_manifest_sha256'],model_budget=0,task_budget=0,automatic_retry=0),real_model_requests=1,real_model_requests_unit='PRIOR_ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION; INFERENCE_NOT_CONFIRMED',product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,next='Execute only new zero-model visual03 under unchanged f13 original Job. Inspect actual Native binding and all1440/390 dark/light initial/scroll/focus screenshots and geometry, allINITIAL scroll0, no occlusion/overflow/control miss; normal App close+originalJobzero+full postbundle. Record initial main-area/document/transcript all scroll0 and real ancestor overflow clips; do not waive any old geometry, visibility or after-scroll hit/focus gate. No fake banners or DOM. MXC startup-only diagnosis is already complete2/2; no further echo/model replay, permission relaxation/admin/setup/saved config change.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';sr=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sr);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);put(sf,s)
cp.update(revision=662,expected_previous_revision=661,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0);assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp662.new');assert not t.exists();t.write_bytes(('# Current resume CP662 - NEW BUILD10 VISUAL03 REGISTERED; TASK/MODEL BUDGET ZERO\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Actual responsive verification must use only new scope and owned fixture; prior visual01 remains consumed failure. MXC fixed local startup diagnosis complete2/2, fine-grained permissions/model remain unverified; no additional echo or model replay. Original04/model failure history intact. No permission changes or model task replay.\n\n').encode('utf8')+old);os.replace(t,hf);(OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
