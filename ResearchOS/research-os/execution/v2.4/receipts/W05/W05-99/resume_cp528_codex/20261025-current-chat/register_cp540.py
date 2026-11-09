import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp540';V=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp540.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
verified=read(N/'C57-phase1-independent-root-verification-r2.json')
assert verified['verified_count']==90 and verified['assertion_count']==41 and not verified['source_acceptance']
for x in verified['verified_refs']:assert ref(Path(x['path']))['sha256']==x['sha256']
seal_p=V/'PHASE1-boot-plan-binding-addendum-seal.json';assert ref(seal_p)['sha256']=='dabf5e26c77608af81ad3f755c8f07083d4db44c689232bdf3b9ec2986ca892b'
seal=read(seal_p);addrefs=[ref(seal_p)]
for x in seal['entries']+[seal['original_phase1_manifest'],seal['original_phase1_seal']]:
 p=V/x['path'];a=ref(p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];addrefs.append(a)
finaldir=V/'016-boot-plan-binding-finalizer';fres=read(finaldir/'result.json');assert fres['native_exit']==0
for stream in ['stdout','stderr']:assert ref(finaldir/(stream+'.raw'))['sha256']==fres[stream+'_sha256']
for name in ['recipe.json','result.json','stdout.raw','stderr.raw']:addrefs.append(ref(finaldir/name))
assert seal['new_assertions']==9 and seal['new_native_nonzero']==0 and seal['cumulative_reviewer_native_nonzero']==2
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==539 and ow['revision']==325 and len(cp['failure_counters'])==2118
prior=read(N/'continuation-cp539/RESUME.current.json');baseline=read(N/'React-Main-integration-baseline.json')
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *x:subprocess.check_output(git+list(x),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD'] and not g('diff','--cached','--name-only')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==baseline['dirty_paths']
root_shared={'execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/HANDOFF_RESUME_PACK.md'}
for x in baseline['dirty_files']:
 if x['relative_path']in root_shared:continue
 p=R/x['relative_path'];assert p.is_file()==x['exists']
 if x['exists']:assert ref(p)['sha256']==x['sha256']
for x in baseline['protected_source']+baseline['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:assert ref(Path(x['path']))['sha256']==x['sha256']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'C57-review-preparation-verified.json',{'schema':'researchos.C57-independent-review-preparation-adoption.v1','status':'MATRIX_READY_NOT_CANDIDATE_ACCEPTANCE','phase1_root_verification':ref(N/'C57-phase1-independent-root-verification-r2.json'),'phase1_seal':ref(V/'PHASE1-seal.json'),'binding_addendum_refs':addrefs,'total_prepared_assertions':50,'candidate_tests_executed':0,'source_acceptance':False,'formal_increment':0,'binding_contract':'boundaryPlanSHA256 vs cPlanHash vs planFileSHA256 have distinct content/phase and common operation; post census final C plan is not preboot witness'})
items=[
 {'id':'root-goal-and-read-dispatch-aborted','detail':'functions.exec aborted before dispatch; no native command or product effects; successful read-only retry retained.','evidence_ref':ref(N/'ROOT-DISPATCH-DIAGNOSTIC-20261025.json')},
 {'id':'root-wait-dispatch-aborted','detail':'collaboration.wait_agent aborted before dispatch; no command/native exit/product effects.','evidence_ref':ref(N/'ROOT-WAIT-DISPATCH-DIAGNOSTIC-20261025.json')},
 {'id':'c57-review-phase1-bootstrap-path-native1','detail':'Independent phase1 initial wrong parent AGENTS path exit1; original combined tool output retained.','evidence_ref':ref(V/'000-original-failure-tool-result.json')},
 {'id':'c57-review-phase1-bootstrap-capture-limit','detail':'Initial read-only bootstrap commands lacked prewritten recipe/separate raw streams; later durable reread does not recreate missing original streams. Separate mixed diagnostic, not another native failure.','evidence_ref':ref(V/'PHASE1-diagnostics.json')},
 {'id':'c57-review-phase1-finalizer-native1','detail':'Independent011 finalizer expected entries but a fixed input used files; preserved failure, separate013 correction exit0.','evidence_ref':ref(V/'PHASE1-diagnostics-addendum-01.json')},
 {'id':'root035-nested-reference-origin','detail':'Root035 incorrectly rooted nested manifest basename at repository; original native1 captured.036 verifies absolute audit path with exact SHA/bytes and suffix then90refs pass. No candidate/source changes.','evidence_ref':ref(N/'035-c57-phase1-independent-verify.recipe.result.json')}
]
new(O/'new-records-ledger.json',{'distinct_mixed_records':len(items),'records':items,'product_failure_count':False,'author_C57_ledgers':'PENDING_FROZEN_AUTHOR_IMPORT_NOT_ZERO'})
before=list(cp['failure_counters'])
for x in items:cp['failure_counters'].append({'origin_key':'20261025|cp540-'+x['id'],'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':x['detail'],'evidence_ref':x['evidence_ref'],'counter_reset':False})
assert len(cp['failure_counters'])==2124 and cp['failure_counters'][:2118]==before
progress={'schema':'researchos.C57-author-progress-not-acceptance.v1','at':now,'source':'Agent progress messages, not a frozen author manifest or independent verification','parent51_reported_passed_receipts':['020-store schema24/87 existing-rw','021-journal pending/abort/unknown inventory','023-domain+journal compile','025-runtime compile','029-domain/store compile'],'parent51_implemented_not_fully_tested':['private raw/model/input native holds','initial five-version plan/transaction','create-new journal and existing-rw store'],'parent51_remaining':['Host preflight/commit/recover/abort still placeholder at last report','recovered outcome full-census protection','historical marker replay','complete entry/upgrade/replacement and transaction cutpoint fixtures'],'boot6_reported':'Six files implemented; own package tests exit0; crash/ACL fixture coverage still in progress; no final freeze','plan_digest_binding':'Builders informed of distinct boundary/C Core/FullPlan file digests','author_tests_do_not_equal_independent_acceptance':True,'formal_increment':0}
new(O/'C57-current-progress-unaccepted.json',progress)
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v118',at=now,checkpoint_revision=540,ownership_revision=326,failure_records_preserved=2124,C57_independent_review_preparation_verified_ref=ref(O/'C57-review-preparation-verified.json'),C57_unaccepted_progress_ref=ref(O/'C57-current-progress-unaccepted.json'),react_frontend_delivery_note_ref=ref(N/'React-frontend-delivery.md'))
resume['next_command']='Continue active C57 parent51 and boot6 builders to real implementation and meaningful tests; Host/recover/replay remain unfinished per author status. Keep exact085b base and exclusive file partition. After combined57 frozen commit/tree/manifest, verify author receipts and import failure ledgers, then issue independent phase2 amendment using prepared50 assertions. ReactMain7d integrated/stagedexact; originaldata/runtime untouched. Formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=540,expected_previous_revision=539,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp540=rr,C57_review_preparation_verified_ref=ref(O/'C57-review-preparation-verified.json'),react_frontend_delivery_note_ref=ref(N/'React-frontend-delivery.md'))
cp['evidence_index'].append({'kind':'C57_PREPARED50_INDEPENDENT_ASSERTIONS_AND_CURRENT_UNACCEPTED_PROGRESS_RECORDED','ref':rr,'formal_increment':0})
ow.update(revision=326,expected_previous_revision=325,updated_at=now,updated_by='codex:/root')
ow['special_paths']['C57_independent_review'].update(state='PHASE1_FROZEN_PREPARED50_WAITING_EXACT_CANDIDATE_FREEZE',evidence_ref=ref(O/'C57-review-preparation-verified.json'))
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode());swap(hp,raw[hp],('# Current verified continuation CP540'+chr(10)*2+'Read '+rr['path']+' first. C57 parent51/boot6 actively implementing; Host/recover/replay incomplete at author report. Independent50 assertions prepared, no candidate acceptance. MainReact7d reviewed integrated/stagedexact, delivery note linked. Originaldata unchanged. Formal0/42/all22open, mixedrecords2124; authorC57 ledgers pendingfreeze import.'+chr(10)*2).encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':540,'ownership':326,'mixed_records':2124,'independent_prepared_assertions':50,'addendum_refs_verified':len(addrefs),'resume':rr},ensure_ascii=False))
