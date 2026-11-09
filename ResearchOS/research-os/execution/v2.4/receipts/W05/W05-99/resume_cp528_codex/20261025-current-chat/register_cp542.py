import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp542'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix() if p.is_relative_to(R.resolve()) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute() else R/p;a=ref(p);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'],str(p)
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp542.pending')
 with q.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==541 and ow['revision']==327 and len(cp['failure_counters'])==2128
prior=read(N/'continuation-cp541/RESUME.current.json')
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *a:subprocess.check_output(git+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD'] and not g('diff','--cached','--name-only')
baseline=read(N/'React-Main-integration-baseline.json')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==baseline['dirty_paths']
for x in baseline['protected_source']+baseline['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:verify(x)
for name in ['041-selector-cp541','042-cp541-live-resume','043-c57-os-token-consultation-verify','044-boot6-v5-author-byte-verify']:
 assert read(N/(name+'.recipe.result.json'))['native_exit']==0
review=read(N/'C57-OS-token-consultation-root-verification.json')
assert review['verified_count']==51
for x in review['verified_refs']:verify(x)
boot=read(N/'C57-boot6-v5-root-verification.json')
assert boot['verified_count']==65 and boot['ledger_records']==21 and len(boot['failed_or_source_finding_records'])==10
for x in boot['verified_refs']:verify(x)
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'root-readonly-display-diagnostics.json',{'schema':'researchos.readonly-capture-diagnostics.v1','events':[{'id':'boot6-large-read-display-truncated','observed':'Tool response exceeded available model context before compaction; no original output/native exit was visible to Root','native_exit':None,'raw_capture':False,'resolution':'Bounded reads and captured044 verified exact author bytes; no product action'},{'id':'outer-agents-path-absent','observed':'Read-only Get-Content D:/作品集/ResearchOS/AGENTS.md produced nonterminating missing-file error; next repository AGENTS read succeeded','tool_chunk':'50262a','tool_native_exit':0,'separate_stdout_stderr_capture':False,'resolution':'Repository AGENTS loaded; no filesystem mutation'}],'verification_script_note':'044 contains a dead conditional assert with an unused hash literal; it does not assert or report that literal as verified. Actual seal SHA is recorded in verified_refs and each sealed artifact was checked. Later supplement verifier will omit this dead statement.'})
new(O/'C57-progress-unaccepted.json',{'schema':'researchos.C57-progress-not-final-acceptance.v3','at':now,'boot6_source_status':'SIX_AUTHOR_FROZEN_HASHES_VERIFIED_PENDING_INDEPENDENT_SOURCE_REVIEW','boot6_verification_ref':ref(N/'C57-boot6-v5-root-verification.json'),'boot6_execution_scope':'v5 actual native PE fixture outside registered roots, cleanup verified; v6 unchanged-source rerun under explicit owned environment pending; no retroactive authorization','parent51_status':'Actual planned writer commit and rollback fixtures passed; replacement exact-own recovery tests passed; actual held five-plan lease tests and two ops early gates passed per author; final owned-environment captures and57freeze pending','old_schema22_test':'Author reports exact085b isolated baseline native1 and corrected candidate native0 (032/033); legacy fixture corrected without lowering original active Run/UNKNOWN/CAS/history assertions; final evidence verification pending','same_plan_replay':'Source corrected to read-only87-table APPLIED check and same OutcomeHash; full Host positive grant still unproven','business_management_identity':'Separate native held frozen business Owner/DB identity and distinct elevated management boundary token; final independent review pending','two_ops_test_handoff':'CANCELED_UNISSUED; both remain parent exclusive51 owner and are implemented by parent','prepared_independent_assertions':73,'new_review_ref':ref(N/'C57-OS-token-consultation-root-verification.json'),'phase1_static_review':'Existing reviewer performing read-only frozen6 closure review only; no candidate tests or acceptance before Root combined57 amendment','candidate_frozen':False,'formal_increment':0})
records=[]
for x in boot['failed_or_source_finding_records']:
 records.append({'origin_key':'20261025|boot6-author-v5|'+x['event'],'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':x,'native_exit':'NOT_CAPTURED_OR_NOT_A_NATIVE_COMMAND','evidence_ref':ref(R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat/diagnostic-ledger.jsonl'),'counter_reset':False})
for ident,detail,evidence in [
 ('root-boot6-display-truncation','Read-only large display unavailable; original native exit unknown; bounded captured044 supersedes lookup only.',O/'root-readonly-display-diagnostics.json'),
 ('root-outer-agents-path-absent','Read-only missing parent AGENTS path emitted PowerShell error; combined command exit0; actual repository AGENTS read.',O/'root-readonly-display-diagnostics.json'),
 ('c57-author-fixture-environment-scope','Boot6 v5 native PE used default user Temp outside registered roots and parent GOCACHE; cleanup verified. Parent reports034-041 no explicit TEMP/TMP/GOTMPDIR; original captures retained and owned-environment reruns pending. One shared environment diagnostic; future author supplements should reference rather than double-count this root origin.',N/'C57-boot6-v5-root-verification.json')]:
 records.append({'origin_key':'20261025|'+ident,'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':detail,'evidence_ref':ref(evidence),'counter_reset':False})
assert len(records)==13 and len({x['origin_key']for x in records})==13
assert not ({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']})
new(O/'new-records-ledger.json',{'distinct_mixed_records':13,'records':records,'boot6_ledger_total':21,'boot6_success_records_not_counted_as_failures':11,'product_failure_count':False,'parent_failure_ledger':'PENDING_FROZEN_AUTHOR_IMPORT_NOT_ZERO'})
before=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert len(cp['failure_counters'])==2141 and cp['failure_counters'][:2128]==before
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v120',at=now,checkpoint_revision=542,ownership_revision=328,failure_records_preserved=2141,C57_boot6_v5_root_verification_ref=ref(N/'C57-boot6-v5-root-verification.json'),C57_OS_token_consultation_verified_ref=ref(N/'C57-OS-token-consultation-root-verification.json'),C57_unaccepted_progress_ref=ref(O/'C57-progress-unaccepted.json'),current_goal_live_resume_verification_ref=ref(N/'CP541-live-resume-verification.json'),C57_independent_prepared_assertions=73)
resume['next_command']='Verify unchanged-source Boot6 v6 owned-environment supplement and read-only independent closure findings. Parent retains51 including two ops tests; complete own-environment final captures and combined57 exact commit/tree/hash manifest, preserve40Source43 pins and author failure/capture gaps. Root exactfreeze amendment before independent phase2 candidate tests. MainReact7d retained; originaldata untouched; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=542,expected_previous_revision=541,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp542=rr,C57_boot6_v5_root_verification_ref=ref(N/'C57-boot6-v5-root-verification.json'),C57_OS_token_consultation_verified_ref=ref(N/'C57-OS-token-consultation-root-verification.json'))
cp['evidence_index'].append({'kind':'C57_BOOT6_AUTHOR_BYTES_AND73_PREPARED_ASSERTIONS_VERIFIED_SCOPE_DEVIATION_PENDING_SUPPLEMENT','ref':rr,'formal_increment':0})
ow.update(revision=328,expected_previous_revision=327,updated_at=now,updated_by='codex:/root')
ow['special_paths']['C57_boot6_source'].update(state='SIX_SOURCE_AUTHOR_FROZEN_V6_OWN_ENV_SUPPLEMENT_PENDING',evidence_ref=ref(N/'C57-boot6-v5-root-verification.json'))
ow['special_paths']['C57_independent_review'].update(state='PHASE1_PREPARED73_AND_FROZEN6_STATIC_REVIEW_NO_CANDIDATE_TESTS',evidence_ref=ref(N/'C57-OS-token-consultation-root-verification.json'))
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(hp,raw[hp],('# Current verified continuation CP542'+chr(10)*2+'Read '+rr['path']+' first. MainReact7d dirty20/protected9/oldDist33/staged3 preserved; Source43 limited source adoption unchanged. Boot6 exact6 and65refs verified, author v5 temp scope deviation pendingv6; parent51 final captures/57freeze pending. Prepared73 independent assertions, frozen6 static review only. Formal0/42/all22open, mixedrecords2141 plus pending parent ledger. Two ops tests remain parent-owned, unissued transfer canceled.'+chr(10)*2).encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':542,'ownership':328,'mixed_records':2141,'review_refs':51,'boot6_refs':65,'prepared_assertions':73,'resume':rr},ensure_ascii=False))

