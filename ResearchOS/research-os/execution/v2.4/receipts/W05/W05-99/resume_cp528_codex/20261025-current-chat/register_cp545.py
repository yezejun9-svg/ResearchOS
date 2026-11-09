import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp545'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute()else R/p;a=ref(p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'],str(p)
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp545.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==544 and ow['revision']==330 and len(cp['failure_counters'])==2182
prior=read(N/'continuation-cp544/RESUME.current.json')
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD']and not g('diff','--cached','--name-only')
baseline=read(N/'React-Main-integration-baseline.json')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==baseline['dirty_paths']
for x in baseline['protected_source']+baseline['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:verify(x)
for x in read(N/'C51-root-preseal-verification-r3.json')['source51_observed']:verify(x)
for name in ['053-sddl-consultations-verify','055-binary-sd-contract-verify-r2']:assert read(N/(name+'.recipe.result.json'))['native_exit']==0
advice=read(N/'C57-SDDL-consultation-root-verification.json');binary=read(N/'C57-binary-SD-contract-root-verification.json')
for x in advice['verified_refs']+binary['verified_refs']:verify(x)
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'C57-native-SD-contract-registration.json',{'status':'EXISTING_NATIVE_PREIMAGE_CONTRACT_VERIFIED_SOURCE_FIX_REQUIRED','SDDL_advice_ref':ref(N/'C57-SDDL-consultation-root-verification.json'),'binary_contract_ref':ref(N/'C57-binary-SD-contract-root-verification.json'),'historical_support':'22publictargets:16AI Cpackage and6noAI Drepo; permanent noAIrejection would drop adopted branch','contract':'Save original native binary preimage; restore every meaningful owner/group/control/ACE including inheritance. No newly invented query-buffer padding/layout memcmp threshold; originalraw retained and rawcompare reported honestly.','actual_problem':'Higher-level GetSecurityInfo projects legacy inheritance flags; SDDL reconstruction restored4ACEflags00->10. Entire nativebuffer172B has sameoffsets/control, so this is actual inheritance drift not padding.','fix_authorized_within_original6':'Use samehandle NtQuerySecurityObject to capture/store/bind originalraw and derivedisplay; restore consumes savedraw through correctdocumented samehandle API, checksmeaningfulnativefields andreportsbinarycomparison; nofailfallback, nooriginalenvironmentprobe','prepared_assertions_unchanged':73,'source_or_native_acceptance':False,'formal_increment':0})
new(O/'root-current-diagnostics.json',{'events':[{'id':'wait-interrupted-01','tool':'collaboration.wait_agent','result':'aborted before dispatch','native_exit':None,'note':'Asynchronous author/reviewer message arrived; no native command/product action'},{'id':'wait-interrupted-02','tool':'collaboration.wait_agent','result':'aborted before dispatch','native_exit':None,'note':'Second asynchronous wait interrupted before dispatch; no native command/product action'},{'id':'binary-verifier-schema','native_exit':1,'receipt':ref(N/'054-binary-sd-contract-verify.recipe.result.json'),'note':'Root verifier mistook4-elementoffsetlist forscalarcount4; corrected055 exactlistcheck, failure kept'}]})
new(O/'C57-current-progress-unaccepted.json',{'at':now,'C51':'Original51 remains authorfrozen, currentbytes reverified;46changes/40pins/220refs accepted as authorpreseal only; no combinedcommit','Boot6':'Authorv7-full05 reportednative0 onlychildsentinelskip; extraNtQueryprobe exposednativeACEflagsdrift despiteSDDLequality. This suitepass does not close fullrestore contract. Mutablebinarypreimagefix now inprogress; no final6freeze.','independent_review':'ThreeP1 and fullbinarypreimage obligation remain toverify againstfinal57. Latest twoSDDLadvisories88refs andbinaryclarification74refs verified; reviewer no candidate tests yet.','next_integration':'New6source/patch/diagnosticfreeze -> Rootbyteverify -> parentaffectedcompile/tests + exact57commit/tree/fullmanifest -> Rootphase2scope amendment -> independentreview; nooriginalDB/Core/STOP/fence/restart actions','pending_failure_import':'Authorv7/v8capturedfailures notfrozen/imported yet; never interpret aszero','cleanup_exception':read(N/'C57-boot6-v6-root-verification.json')['auto_review_cleanup'],'formal_increment':0})
records=[{'origin_key':'20261025|BOOT6-native-binary-preimage-and-ACEflags-drift','attempts':1,'status':'SOURCE_CONTRACT_GAP_CONFIRMED_FIX_IN_PROGRESS','detail':binary['observed_drift'],'evidence_ref':ref(O/'C57-native-SD-contract-registration.json'),'counter_reset':False}]
for x in read(O/'root-current-diagnostics.json')['events']:records.append({'origin_key':'20261025|root-cp544-'+x['id'],'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':x,'evidence_ref':ref(O/'root-current-diagnostics.json'),'counter_reset':False})
assert len(records)==4 and not({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']})
new(O/'new-records-ledger.json',{'distinct_mixed_records':4,'records':records,'product_failure_count':False,'author_v7_v8_increment':'PENDING_FROZEN_IMPORT_NOT_ZERO'})
before=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert cp['failure_counters'][:2182]==before and len(cp['failure_counters'])==2186
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v123',at=now,checkpoint_revision=545,ownership_revision=331,failure_records_preserved=2186,C57_native_SD_contract_ref=ref(O/'C57-native-SD-contract-registration.json'),C57_unaccepted_progress_ref=ref(O/'C57-current-progress-unaccepted.json'))
resume['next_command']='Continue Boot6 true native binarypreimage capture/store/bind/restore (legacy GetSecurityInfo SDDL projection caused4ACEflagdrifts). Existing adoptedcontract requires originalraw+allmeaningfulnativefields, not inventedpaddingmemcmp. Original51 frozen/46changes/40pins/220refs verified. Obtain new6 frozen source/tests/appendonlyv7+diagnostics, then parentaffectedintegration + exactcombined57commit/tree/manifest and Rootphase2amendment before independentcandidate review. MainReact7d protected; originaldata untouched; policydeniedcleanup remains; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=545,expected_previous_revision=544,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp545=rr,C57_native_SD_contract_ref=ref(O/'C57-native-SD-contract-registration.json'))
cp['evidence_index'].append({'kind':'C57_NATIVE_SD_RESTORE_CONTRACT_AND_REAL_ACEFLAGS_DRIFT_REGISTERED_BINARY_FIX_ACTIVE','ref':rr,'formal_increment':0})
ow.update(revision=331,expected_previous_revision=330,updated_at=now,updated_by='codex:/root')
ow['special_paths']['C57_boot6_source'].update(state='IMPLEMENTING_TRUE_NATIVE_BINARY_PREIMAGE_AFTER_SDDL_PROJECTION_DRIFT',evidence_ref=ref(O/'C57-native-SD-contract-registration.json'))
ow['special_paths']['C57_independent_review'].update(state='PHASE1_CONSULTATIONS_COMPLETE_WAIT_FINAL57_PHASE2_NO_CANDIDATE_TESTS')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(hp,raw[hp],('# Current verified continuation CP545'+chr(10)*2+'Read '+rr['path']+' first. MainReact7d dirty20/protected9/oldDist33/staged3 preserved. C51frozen51/46changes/40pins/220refs. Boot6 fullsuite0preceded discovery of4nativeACEflagdrifts viaGetSecurityInfo legacyprojection; truebinarypreimagefix active. Independentadvice88refs+binarycontract74refs verified; fixed73, final57phase2notstarted. Preserveallv7failures pendingimport anddeniedcleanupfile. Formal0/42/all22open, mixedrecords2186.'+chr(10)*2).encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':545,'ownership':331,'mixed_records':2186,'SDDL_refs':88,'binary_refs':74,'resume':rr},ensure_ascii=False))

