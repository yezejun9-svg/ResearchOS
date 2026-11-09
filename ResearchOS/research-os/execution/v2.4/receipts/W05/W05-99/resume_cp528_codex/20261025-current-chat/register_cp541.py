import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp541';V=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp541.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
seal_p=V/'PHASE1-persistent-fence-control-addendum-seal.json'
assert ref(seal_p)['sha256']=='4fc32056b6f7777fc06f0a219f1c81c399abd20ab921e021fa127355517f6122'
seal=read(seal_p);refs=[ref(seal_p)]
for x in seal['entries']+seal['prior_seals_unchanged']:
 p=V/x['path'];a=ref(p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
fdir=V/'021-fence-addendum-finalizer';fr=read(fdir/'result.json');assert fr['native_exit']==0
for st in ['stdout','stderr']:assert ref(fdir/(st+'.raw'))['sha256']==fr[st+'_sha256']
for name in ['recipe.json','result.json','stdout.raw','stderr.raw']:refs.append(ref(fdir/name))
assert len(seal['new_assertions'])==8 and seal['new_native_nonzero']==0 and seal['cumulative_reviewer_native_nonzero']==2 and seal['candidate_tests_executed']==0
for name in ['037-selector-cp540','038-cp540-live-resume','039-c57-live-scope-preservation','040-c57-ancestor-contract-observation']:
 assert read(N/(name+'.recipe.result.json'))['native_exit']==0
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==540 and ow['revision']==326 and len(cp['failure_counters'])==2124
prior=read(N/'continuation-cp540/RESUME.current.json')
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *a:subprocess.check_output(git+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD']and not g('diff','--cached','--name-only')
baseline=read(N/'React-Main-integration-baseline.json')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==baseline['dirty_paths']
for x in baseline['protected_source']+baseline['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:assert ref(Path(x['path']))['sha256']==x['sha256']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'C57-persistent-fence-review-verified.json',{'schema':'researchos.C57-phase1-persistent-control-review-registration.v1','status':'BOUNDED_MUTABLE_FINDINGS_REGISTERED_NOT_CANDIDATE_ACCEPTANCE','verified_refs':refs,'existing_prepared_assertions':50,'new_prepared_assertions':8,'total_prepared_assertions':58,'findings':seal['findings'],'closure_state':'NOT_INDEPENDENTLY_VERIFIED_CLOSED','code_findings':['arm before mutation ancestor control','managed records effective ACL','business token and owner/group semantics','samehandle exact SD restore without thirdparty overwrite'],'resource_gate':'distinct SID management owner transfer and exact restoration remains not proven','source_acceptance':False,'formal_increment':0})
new(O/'C57-current-progress-unaccepted.json',{'schema':'researchos.C57-progress-not-final-acceptance.v2','at':now,'source':'Latest active builder messages; author ledgers not frozen or imported','parent51':'Host preflight/commit/recover/abort now implemented and compiled; schema24/87 protected/residual census, nine-table applied classification and FullPlan hashes wired','parent_tests_reported':'Journal/store tests and Domain/Host compile passed. Real SQLite/WAL classification fixture NOT_APPLIED -> manually inserted nine-table APPLIED -> foreign outbox UNKNOWN passed. Early parameter and frozen subject tests passed. Actual planned-writer/five-version/replay/transaction-cutpoint testing continues. Manual rows are not actual writer or full Host grant proof.','business_management_identity':'C Host correcting legacy same-business-SID public identity reader to separate held native business host_state/DB Owner validation from distinct elevated management boot token; old reader unchanged','boot6':'Own packages/native PE and script rejection/RestartApps process registration readback/SQLite-WAL-lease/crossbuild reported. Target owner/ancestor/state/restore P1 source fixes reported, not final independent validation; original captures preserved. FullRestart/distinctSID privileged positive not run.','current_open_root_observation':ref(N/'C57-ancestor-contract-observation-cp540.json'),'root_observation_summary':'Revised ancestor predicate rejects adopted legitimate D-root BA/INHERIT_ONLY policy. Fix true token/ACE/OS ancestor semantics without blanket bypass or drive ACL rewrite; fresh bounded independent consultation active.','future_optional_test_split':{'status':'NOT_ISSUED_UNTIL_BOOT6_FROZEN','paths':['ops/backup/maintenance_gate_windows_test.go','ops/supervisor/release_host/maintenance_gate_windows_test.go'],'current_owner':'C57 parent; parent agreed not to edit pending Root transfer','current_signatures':['openBackupSourceLease(source string) (*backupSourceOwner,error)','openReleaseHostSourceLease(database string) (*rt.DataRootLease,error)'],'authority':'No third Source constructor before boot6 freeze; Root must register exclusive lease first'},'candidate_frozen':False,'formal_increment':0})
items=[
 ('root-initial-optional-recipe-path','Initial read-only lookup guessed nonexistent recipe path; original tool native1 with capture limitation, corrected exactpath and037/038captured success.',N/'ROOT-CP540-READONLY-PATH-DIAGNOSTIC.json'),
 ('root-wait-interruption-01','Async agent wait interrupted before dispatch; no native command/result/product effects.',N/'ROOT-CP540-WAIT-INTERRUPTION.json'),
 ('root-wait-interruption-02','Second async agent wait interrupted before dispatch; no native command/result/product effects.',N/'ROOT-CP540-WAIT-INTERRUPTION-02.json'),
 ('root-lookup-display-truncation','Exploratory lookup included archived largeJSON and display truncated; raw capture limit explicit,040 exact bounded verification preserved.',N/'ROOT-CP540-LOOKUP-DISPLAY-DIAGNOSTIC.json')
]
records=[{'origin_key':'20261025|cp541-'+i,'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':detail,'evidence_ref':ref(p),'counter_reset':False}for i,detail,p in items]
new(O/'new-records-ledger.json',{'distinct_mixed_records':4,'records':records,'product_failure_count':False,'author_C57_failure_ledgers':'PENDING_FROZEN_AUTHOR_IMPORT_NOT_ZERO'})
before=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert len(cp['failure_counters'])==2128 and cp['failure_counters'][:2124]==before
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v119',at=now,checkpoint_revision=541,ownership_revision=327,failure_records_preserved=2128,C57_persistent_fence_review_ref=ref(O/'C57-persistent-fence-review-verified.json'),C57_unaccepted_progress_ref=ref(O/'C57-current-progress-unaccepted.json'),current_goal_live_resume_verification_ref=ref(N/'CP540-live-resume-verification.json'),C57_live_scope_preservation_ref=ref(N/'C57-live-scope-preservation-cp540.json'),C57_root_ancestor_contract_observation_ref=ref(N/'C57-ancestor-contract-observation-cp540.json'),C57_independent_prepared_assertions=58)
resume['next_command']='Continue C57 parent51 actual writer/replay/transaction fixtures and separate business-vs-management identity. Boot6 must resolve persistent ACL/owner/restore findings AND adopted OS-ancestor/token semantics without drive ACL changes or blanket bypass. Collect bounded independent OS-policy addendum. After boot6 frozen package verified, optionally transfer two gate tests via exact Root ownership; only two active Source tasks. Combined57 freeze then author ledger/hash verification and independent phase2. MainReact7d retained; originaldata untouched; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=541,expected_previous_revision=540,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp541=rr,C57_persistent_fence_review_ref=ref(O/'C57-persistent-fence-review-verified.json'),C57_root_ancestor_observation_ref=ref(N/'C57-ancestor-contract-observation-cp540.json'))
cp['evidence_index'].append({'kind':'LIVE_CP540_PRESERVATION_AND_C57_PERSISTENT_FENCE_REVIEW_PROGRESS_REGISTERED','ref':rr,'formal_increment':0})
ow.update(revision=327,expected_previous_revision=326,updated_at=now,updated_by='codex:/root');ow['special_paths']['C57_independent_review'].update(state='PHASE1_PREPARED58_PLUS_BOUNDED_OS_ANCESTOR_CONSULTATION_NO_ACCEPTANCE',evidence_ref=ref(O/'C57-persistent-fence-review-verified.json'))
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode());swap(hp,raw[hp],('# Current verified continuation CP541'+chr(10)*2+'Read '+rr['path']+' first. Live selector VALIDATED_FILE/W05-99; Main7d dirty20/protected9 preserved. C57 Host now implemented/compiled and bounded SQLite classification passed, actual writer fixtures continue. Boot persistent ACL fixes + legitimate OS ancestor semantics still require freeze/review; two test transfer only future/unissued. Independent58 assertions prepared, no C57 acceptance. Formal0/42/all22open, mixedrecords2128 plus pending author ledgers.'+chr(10)*2).encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':541,'ownership':327,'mixed_records':2128,'persistent_review_refs_verified':len(refs),'prepared_assertions':58,'resume':rr},ensure_ascii=False))
