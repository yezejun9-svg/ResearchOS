import argparse,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp646'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
ap=argparse.ArgumentParser();ap.add_argument('--scope-sha',required=True);ap.add_argument('--metadata-review',required=True);ap.add_argument('--metadata-review-sha',required=True);a=ap.parse_args()
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==645 and len(cp['failure_counters'])==2546 and not OUT.exists()
scope=CONTROL/'scopes/product-v1-single-task-flow-02.json';assert sha(scope)==a.scope_sha and not (CONTROL/'runs/product-v1-single-task-flow-02').exists()
meta=Path(a.metadata_review);assert sha(meta)==a.metadata_review_sha;mr=read(meta);assert mr['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and mr['formal_increment']==0 and not mr['pending_blockers']
assert mr['source_sha256']['register_product_v1_single_task_flow02.py']=='5b518d944ea0d5551a6bbe230036f1d785187ba39804c8a0f158a86ea76482d0'
inner=read(HERE/'product-v1-single-task-flow-02-registration/real-flow.scope.json');assert inner['bundle']['source_binding_review']==inner['source']['pin_status']=='ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE'
review=BASE/'one-task-controller04/reviews/REVIEW.json';assert sha(review)=='509372d819c522feb214ce35352d64d59fcf3c1def95bb68060736e86167095d';rv=read(review);assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and rv['formal_increment']==0 and not rv['pending_blockers']
reg=read(HERE/'product-v1-single-task-flow-02-registration/REGISTRATION.json');assert reg['prior_model_tasks_submitted']==0 and reg['task_budget']==1
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw);(OUT/'scope.json').write_bytes(scope.read_bytes());(OUT/'independent-controller-review.json').write_bytes(review.read_bytes());(OUT/'metadata-review.json').write_bytes(meta.read_bytes())
now=datetime.now(timezone.utc).isoformat()
event=dict(at=now,attempts=2,counter_reset=False,origin_key='root-single-task-registration02:preparation-string-replacement',classification='ROOT_C_CHECKPOINT_WRITER_PREPARATION',detail='First C-only derivation asserted on a replacement already consumed by an earlier overlapping replacement, before output creation. Dependent apply_patch then found no target. Neither operation wrote D or launched anything. New derivation removed the redundant replacement and created the new writer; original source and failed output preserved in tool history.')
assert event['origin_key'] not in {e.get('origin_key') for e in cp['failure_counters']};cp['failure_counters'].append(event)
progress=dict(checkpoint_revision=646,at=now,status='SINGLE_READONLY_NATIVE_HARNESS_TASK02_REGISTERED_NOT_EXECUTED',main_head=cp['current_Main_HEAD'],scope_path=str(scope),scope_sha256=sha(scope),scope_status='REGISTERED_NOT_EXECUTED',source_review_sha256=sha(review),task_budget=1,native_harness_invocation_budget=1,internal_model_api_calls='NOT_MEASURED',automatic_retry=0,
 native_prerequisite='CP643 independently verified complete real invalid/valid Unicode path and Main ACTIVE binding; exact original runner/f13/review/postbundle files are outer fixed inputs. CP645 old01 preflight failure retained; new02 metadata assignment follows complete integrity checks and independent static review.',metadata_review_sha256=sha(meta),
 execution_scope='Fresh own canary fixture only, normal Desktop DOM once, typed Host LOGGED_IN/chatgpt gate immediately before submit. Stable original request/task/run references across all snapshots/events/reconciliation. No API/paid/login fallback or manual auth/config/credential reads.',
 real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Execute only newly registered single-task-flow02 under exact f13 original unnamed Job. Do not rerun consumed Native/model scopes. Actual gate failure means stop that branch; UNKNOWN keeps original refs/no retry/newID. Require same Task/Run public events and final canary from fixture, unchanged fixture hashes, normal close/original Job accounting and postbundle checks. Save exact failure/phase; no private CoT, enforcement/READY or full-journey claims. Layout proposal remains C-only.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);put(sf,s)
cp.update(revision=646,expected_previous_revision=645,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp646.new');assert not tmp.exists();tmp.write_bytes(('# Current resume CP646 — ONE FRESH READONLY HARNESS TASK SCOPE REGISTERED\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Not executed; actual Native flow04 independently verified CP643. Newscope single-task-flow02 requires real ChatGPT gate and one normal DOM submit, no UNKNOWN replay. NativeHarness invocation budget1; internal LLM API calls NOT_MEASURED. Models still0/Journeys0/13; all history preserved.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_single_task_registration02.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
