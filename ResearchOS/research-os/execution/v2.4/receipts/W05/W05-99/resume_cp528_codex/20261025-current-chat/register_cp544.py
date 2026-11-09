import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp544'
B=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute()else R/p;a=ref(p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes']
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp544.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==543 and ow['revision']==329 and len(cp['failure_counters'])==2153
prior=read(N/'continuation-cp543/RESUME.current.json')
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD']and not g('diff','--cached','--name-only')
baseline=read(N/'React-Main-integration-baseline.json')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==baseline['dirty_paths']
for x in baseline['protected_source']+baseline['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:verify(x)
assert read(N/'051-c51-preseal-verify-r3.recipe.result.json')['native_exit']==0
c51=read(N/'C51-root-preseal-verification-r3.json')
for x in c51['verified_refs']+c51['source51_observed']+c51['inherited40_observed']:verify(x)
assert c51['verified_count']==220 and c51['ledger_snapshot_entries']==89
increment_refs=[]
for name in ['C51-DIAGNOSTIC-INCREMENT-053.jsonl','C51-DIAGNOSTIC-INCREMENT-054.jsonl']:
 p=B/name
 if p.exists():
  increment_refs.append(ref(p))
  for row in p.read_text(encoding='utf-8-sig').splitlines():
   ev=json.loads(row)
   for x in ev.get('files',[]):
    a=ref(B/x['name']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];increment_refs.append(a)
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'C51-preseal-registration.json',{'status':'AUTHOR51_SOURCE_AND220_ARTIFACT_REFS_VERIFIED_NO_ACCEPTANCE','verification_ref':ref(N/'C51-root-preseal-verification-r3.json'),'additional_increment_refs':increment_refs,'source51_count':51,'actual_changed_count':46,'inherited40_exact':True,'base085b_index_empty':True,'patchcheck_native_exit':0,'ledger_history':'Initial86 derived ledger was overwritten by regeneration; separately reconstructed86 exactSHA matches original announced hash; current89 and reconstruction preserved. Original raw receipts independently hashed. Reconstruction is not uninterrupted original-file continuity.','source_tests':'042-049 ownedenv correspond to their old source snapshot;050-052 native0 include lifetime test but Boot6 changed during batch, no frozen57 proof','baseline_032_033_limit':'Native1/0 and declared head085b recipe/raw retained; prior actual HEAD/clean/delete range observed only in tool conversation, no separate persisted output. Baseline temp env not explicit.054 is postfactabsence only.','parent_full_candidate_acceptance':False,'formal_increment':0})
new(O/'root-current-diagnostics.json',{'events':[{'id':'lookup-parent-index','tool_chunk':'d520c5','native_exit':1,'cause':'Read-only ledger lookup derived wrong R using parents[5], yielding execution/execution path; corrected explicitR lookup. Original tool combinedoutput preserved only in conversation.'},{'id':'preseal-049','native_exit':1,'receipt':ref(N/'049-c51-preseal-verify.recipe.result.json'),'cause':'Correctly detected that current ledger first86bytes do not match original announced hash; actual author rewrite incident.'},{'id':'preseal-050','native_exit':1,'receipt':ref(N/'050-c51-preseal-verify-r2.recipe.result.json'),'cause':'Root verifier assumed only .native-exit.txt suffix; receipt018 valid .exit.txt; corrected in051, prior captures kept.'},{'id':'agent-wait-aborted','native_exit':None,'cause':'collaboration.wait_agent returned aborted before dispatch when new author message arrived; no native command or product action.'}],'resolution':'051 succeeds and stores220 exactref verification; no counter reset'})
new(O/'C57-current-progress-unaccepted.json',{'at':now,'C51_registration_ref':ref(O/'C51-preseal-registration.json'),'parent51':'Presealed; sync cancellation/commiterror hold fixture captured in050 native0; source unchanged at registration; waiting new6 before affected finalintegration and57commit','boot6':'Mutablev7 fixes threeP1; fourfocused tests authorreported0; fullnative suite still1 with2ACLskips+childsentinelSkip+staleSDfailure. Exact failure now descriptor expectedG/P vs observednoG/PAI; no claim source/native accepted','independent_review':'Existing reviewer doing bounded read-only SECURITY_INFORMATION/SDDL semantics consultation; fixed73 and old3P1 unchanged. Full57 phase2 notauthorized until exactfreeze','author_v7_failures':'PENDING_FROZEN_INCREMENT_NOT_ZERO','cleanup_exception':read(N/'C57-boot6-v6-root-verification.json')['auto_review_cleanup'],'formal_increment':0})
records=[]
def record(key,status,detail,evidence,attempts=1):
 records.append({'origin_key':'20261025|'+key,'attempts':attempts,'status':status,'detail':detail,'evidence_ref':ref(evidence),'counter_reset':False})
for x in c51['early_raw_FAIL_unknown_numeric_exit']:record('C51-early-raw-FAIL-'+str(x['ordinal']),'TEST_FAILURE_OBSERVED_NATIVE_EXIT_NOT_CAPTURED',x,N/'C51-root-preseal-verification-r3.json')
for x in c51['interim_failures_unknown_native_exit']:
 if x['ordinal']!=35:record('C51-interim-'+str(x['ordinal']),'FAILURE_OBSERVED_NO_INDEPENDENT_NATIVE_CAPTURE',x,N/'C51-DIAGNOSTIC-LEDGER.root-snapshot-89-r3.jsonl')
for x in c51['captured_nonzero_commands']:record('C51-numbered-'+str(x['ordinal']),'NATIVE_FAILURE_PRESERVED',x,N/'C51-root-preseal-verification-r3.json')
record('C51-format-007-009','SCOPE_DEVIATION_RESTORED_EXACT_CURRENT_BYTES','007 formatted2 outside paths,009 another14;010 restored20 including4 then-unedited allowlistedtests;011 andRoot05140pins exact. Original pre-restore full diff/hash capture missing.',B/'C51-EARLY-RAW-ADDENDUM.md',2)
record('C51-historical-capture-gap','CAPTURE_LIMITATION_PRESERVED',{'entries_with_gap':54,'native_exit_unknown_not_inferred':True,'full89ledger_preserved':True},N/'C51-root-preseal-verification-r3.json')
record('C51-derived-ledger-rewrite','APPEND_ONLY_PROCESS_ERROR_PRESERVED_WITH_HASH_MATCHED_RECONSTRUCTION','Original86 file was regenerated with additional fields; current89 kept; reconstructed86 hash exactly matches prior declared hash, clearly labeled reconstructed.',B/'C51-LEDGER-REWRITE-INCIDENT.json')
for x in read(O/'root-current-diagnostics.json')['events']:record('root-cp543-'+x['id'],'DIAGNOSTIC_PRESERVED',x,O/'root-current-diagnostics.json')
assert len(records)==29
assert not({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']})
new(O/'new-records-ledger.json',{'distinct_mixed_records':29,'records':records,'deduplicated':'interim35 maps numbered034-041 (039failure); interim36 maps042-049passes; sharedenvdeviation alreadyCP542; repeated same-cause baseline invocations remain distinct attempts','product_failure_count':False,'boot6_v7_failure_import':'PENDING_NOT_ZERO'})
before=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert cp['failure_counters'][:2153]==before and len(cp['failure_counters'])==2182
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v122',at=now,checkpoint_revision=544,ownership_revision=330,failure_records_preserved=2182,C51_root_preseal_verified_ref=ref(O/'C51-preseal-registration.json'),C57_unaccepted_progress_ref=ref(O/'C57-current-progress-unaccepted.json'))
resume['next_command']='Complete Boot6 threeP1 sourcefixes plus Windows descriptor field/control semantics and owned native suite; collect immutable new6 freeze and v7 diagnostic increment. C51 preseal51/46changes/40pins+220refs verified; parent retains51, only affected finalintegration after new6, then exactcombined57commit/tree/manifest. Root amendment before independentphase2; preserve ledger rewrite incident/reconstructed86/current89 and all raw failures. MainReact7d protected, originaldata untouched, cleanup-policy denial unchanged, formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=544,expected_previous_revision=543,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp544=rr,C51_root_preseal_verified_ref=ref(O/'C51-preseal-registration.json'))
cp['evidence_index'].append({'kind':'C51_PRESEAL_VERIFIED_AUTHOR_FAILURES_AND_LEDGER_REWRITE_PRESERVED_BOOT6_FIXES_CONTINUE','ref':rr,'formal_increment':0})
ow.update(revision=330,expected_previous_revision=329,updated_at=now,updated_by='codex:/root')
ow['special_paths']['C57_maintenance_source'].update(state='OWNED51_PRESEALED_AWAITING_NEW_BOOT6_FOR_AFFECTED_FINAL_INTEGRATION',evidence_ref=ref(O/'C51-preseal-registration.json'))
ow['special_paths']['C57_independent_review'].update(state='PHASE1_BOUNDED_NATIVE_DESCRIPTOR_CONSULTATION_NO_CANDIDATE_TESTS')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(hp,raw[hp],('# Current verified continuation CP544'+chr(10)*2+'Read '+rr['path']+' first. MainReact7d/dirty20/protected9/oldDist33/staged3 preserved. C51preseal51/46actual/40pins/220refs verified; author ledger rewrite explicitly retained with exactSHA reconstructed86 and current89. Boot6mutablev7 threeP1fixes/focused4passed but fullnativeSDDLmismatch unresolved; bounded reviewer consultation active. Combined57notfrozen/no phase2. Cleanupdiagnostic retained after blocked by policy. Formal0/42/all22open, mixedrecords2182 plus pendingv7increment.'+chr(10)*2).encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':544,'ownership':330,'mixed_records':2182,'C51_refs':220,'increment_refs':len(increment_refs),'resume':rr},ensure_ascii=False))

