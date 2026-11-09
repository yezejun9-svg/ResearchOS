import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;O=B/'continuation-cp499';E=R/'execution/v2.4/receipts/W05/W05-99';N=R/'execution/v2.4/receipts/W17/W17-03';H=N/'historical22_queue_fixture_repair_source_codex/20261015-current-chat';D=E/'qualification_fresh_attempt_input_map_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def check(v):
 p=Path(v['path']);p=p if p.is_absolute() else R/p
 assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
 if 'bytes' in v:assert p.stat().st_size==v['bytes']
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b;t=p.with_name(p.name+'.cp499.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==498 and ow['revision']==284 and len(cp['failure_counters'])==1518
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
assert len(subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=R,text=True).splitlines())==20
for v in read(E/'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(R/v['path'])['sha256']==v['sha256']
assert ref(H/'FINAL-02.json')['sha256']=='086b99c9f648c1d142cac6bc2448fc728c4904e03cae9e64733e5491da9e71ec'
hf=read(H/'FINAL-02.json');hl=read(H/'FAILURE-LEDGER.json')
for v in hf['refs'].values():check(v)
assert hl['attempt_count']==18 and hl['failed_count']==7
for x in hl['entries']:
 check({'path':x['record_path'],'sha256':x['record_sha256']});check(x['stdout']);check(x['stderr'])
assert ref(D/'evidence-manifest.json')['sha256']=='22c32110a7903d9d614bed61f372dd098452a7dbe0ce558383814b977087c433'
for v in read(D/'evidence-manifest.json')['files']:check(v)
W=Path(hf['candidate_worktree']);assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip()==hf['candidate_commit'];assert not subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=no'],cwd=W)
assert subprocess.check_output(['git','diff','--name-only',hf['base'],hf['candidate_commit']],cwd=W,text=True).splitlines()==['internal/domain/backup_configuration_upgrade_test.go']
now=datetime.datetime.now(datetime.timezone.utc).isoformat();O.mkdir(exist_ok=False)
scope={'schema':'researchos.historical22-fixture-independent-review.v1','at':now,'owner':'codex:/root/historical22_fixture_review','model':'gpt-6-astra','reasoning_effort':'high','model_choice_reason':'Independent acceptance of historical provenance fixture, state/effect/queue continuity and schema boundary','candidate_commit':hf['candidate_commit'],'candidate_tree':hf['candidate_tree'],'base_commit':hf['base'],'worktree':str(W),'allowed_candidate_diff':['internal/domain/backup_configuration_upgrade_test.go'],'author_final':ref(H/'FINAL-02.json'),'author_failure_ledger':ref(H/'FAILURE-LEDGER.json'),'construction_scope':ref(B/'continuation-cp496/historical22-queue-fixture-repair-scope.json'),'own_receipts':str(N/'historical22_queue_fixture_independent_review_codex/20261015-current-chat'),'requirements':['READONLY Source review: own only receipt directory; not alone, do not change/revert Main20/Aprojection/Source53/historicalSource or actual data. No globalcleanup/Gitobjectrestore/model/provider/stop/signature.','Verify exact1 candidate and full author ref chain, source22 historical502tar/sourcepins/5922priorinputvector/29nativepins, onlyoneaddedhelperinnewhistoricalroot, oldGitmissingtree remains recorded. Trace helper actual public old22 Execute goal.start+7send+control and publicorchestration; fixture SQL syntheticphase/workspacepath rebinding precisely bounded and declared, no SQL23identities injection.','Verify closed original DB hash and schema1..22/count22/noidentities; read any DB with mode=ro or inspect a new copy so originalSQLitebytes cannot be changed bycheckpoint. Compare before/after source/originalhelperbytes. No claim pureallpublicSDK/provider execution; syntheticfixture phases are fixture-only.','Review candidate retains original queue7phase/control/Run+lease/effectUNKNOWN/idempotency/operationalrow continuity assertions after UpgradeLocal22to23; no weakened acceptance or query fake. Inspect envpin trust and no-resource behavior/CI reproducibility; missing resource must not be silentlyaccepted.','Meaningful fresh targeted verification of ActiveQueueRecovery and related changed assertions using pinned author inputs and taskowned D temp siblingroots; do not repeat unrelated fullpackages or oldpassedchecks without justification. Capture actualargv/cwd/allowlistenv/nativeexit/rawlogs/assertioncounts and all fails/skips appendonly. No independentacceptance from exit0 orzeroassertions alone.','Freeze review.md/review.json, source/input/guard hashes and evidence-manifest; LIMITED_SOURCE_ACCEPTED only if justified. Old author7fails + priorT3all3fail remain; no broad allgreen claim. Not Main integration/package/originalmigration/formalacceptance; formal0/42/all22open.'],'source_authority':'NONE','actual_authority':'NONE','formal_increment':0}
new(O/'historical22-fixture-independent-review-scope.json',scope)
old=list(cp['failure_counters'])
for i,x in enumerate(hl['entries'],1):
 if x['status']!='FAIL':continue
 origin='20261015|historical22-fixture-source-attempt-'+str(i);assert not any(y.get('origin_key')==origin for y in old)
 cp['failure_counters'].append({'origin_key':origin,'attempts':1,'status':'SOURCE_FIXTURE_FAILURE_PRESERVED','detail':x,'evidence_ref':ref(H/'FAILURE-LEDGER.json'),'counter_reset':False})
for x in read(D/'diagnostic-ledger.json')['attempts']+[read(D/'freeze-attempt-01.failure.json')]:
 assert not any(y.get('origin_key')==x['origin_key'] for y in old)
 cp['failure_counters'].append({'origin_key':x['origin_key'],'attempts':1,'status':'ROOT_DIAGNOSTIC_PRESERVED','detail':x,'evidence_ref':ref(D/'evidence-manifest.json'),'counter_reset':False})
assert cp['failure_counters'][:1518]==old and len(cp['failure_counters'])==1528
resume=read(B/'continuation-cp498/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v77',at=now,checkpoint_revision=499,ownership_revision=285,failure_records_preserved=1528,active_source_cards=['CP497 qualificationAeffectiveprojection only; historical22builder completed pendingindependentreview'],historical22_fixture_candidate=hf,historical22_fixture_review_scope_ref=ref(O/'historical22-fixture-independent-review-scope.json'),fresh_attempt_input_map_ref=ref(D/'evidence-manifest.json'),next_command='Independently review historical22candidate680262exact1 and all7failures; AprojectionSource continues alone. B/C/STOP/D architecture independentlyreviewing with concretebinding/plan/maintenancegaps, noimplementationoractualauthorityyet. OriginalRunf3/requestbc269e77 UNKNOWN consumedNOREPLAY. Main4f/indexempty/old20 preserved; Source53notMain/package; formal0/42/all22open.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=499,expected_previous_revision=498,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp499=rr,historical22_fixture_candidate=hf,historical22_fixture_review_scope_ref=ref(O/'historical22-fixture-independent-review-scope.json'),fresh_attempt_input_map_ref=ref(D/'evidence-manifest.json'));cp['evidence_index'].append({'kind':'HISTORICAL22_FIXTURE_SOURCE_FREEZE_REVIEW_SCOPE_AND_FAILURE_IMPORT','ref':rr,'formal_increment':0})
ow.update(revision=285,expected_previous_revision=284,updated_at=now,updated_by='codex:/root');ow['special_paths']['historical22_fixture_repair']={'state':'SOURCE_FROZEN_REVIEW_PENDING','candidate':hf['candidate_commit'],'final_ref':ref(H/'FINAL-02.json'),'review_scope_ref':ref(O/'historical22-fixture-independent-review-scope.json')}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP499\n\nRead `'+rr['path']+'` first. Historical22fixturecandidate680262exact1 source frozen, threefocusedPASS, sevenfailurespreserved; independentreviewpending. Aprojectiononly activeSourcecard. B/C/STOP/D readonlyreviewcontinues. Main4f/originalUNKNOWNconsumedRun retained. Formal0/42/all22open; preservedrecords1528.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':499,'ownership':285,'failure_records':1528,'resume':rr,'review_scope':ref(O/'historical22-fixture-independent-review-scope.json')}))
