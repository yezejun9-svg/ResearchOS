from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,copy
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6];BASE='execution/v2.4/receipts/W04/W04-99/'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def read(p):return json.loads(p.read_bytes())
def save(n,v):
 with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def need(v,s):
 if not v:raise ValueError(s)
detail=ROOT/BASE/'independent-review-codex-round2-20261006-3be14ac9/review_detail.json'
manifest=ROOT/BASE/'executor_codex/runs/20261005T224949Z-418d17844405/source_snapshot_manifest.json'
old_audit=ROOT/BASE/'independent-review-codex-final-20261006-61a0d2e7/audit_result.json'
statecopy=ROOT/BASE/'integration_codex/step_state_before_acceptance.json'
need(ref(manifest)['sha256']=='98e6c224e47a7a1a9fd28c0a90901aa344f6b79826e45a03a5cca6d9356f2aeb','manifest')
need(ref(old_audit)['sha256']=='b2ffa00c4f842ba2b1e9f45da5570f86b01970f95a719ebf552b03129baf6e27','audit')
oldhash='64ef113e768e530d721977cf10c736d4c285fd9896ba00727871ff449c422760'
need(ref(statecopy)['sha256']==oldhash,'actual old copy')
statekey=str(ROOT/'execution/v2.4/step_state.json')
need(read(old_audit)['input_hashes'][statekey]==oldhash,'actual observed state hash')
mapping=next(x for x in read(manifest)['snapshots'] if x['original_ref']['path']==BASE+'executor_codex/expected.json')
need(mapping['original_ref']['sha256']=='075cdf560c9b4e791493218e056325c27010987f6f43242720d25282197f24ce','old expected hash')
need(mapping['snapshot_ref']['sha256']==mapping['original_ref']['sha256']==ref(ROOT/mapping['snapshot_ref']['path'])['sha256'],'bound old source copy')
refs=[]
def walk(v,loc=''):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:refs.append({'location':loc,'reference':v})
  for k,x in v.items():walk(x,loc+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,loc+'/'+str(i))
walk(read(detail))
manifest_refs=[x for x in refs if x['reference']['sha256']==ref(manifest)['sha256']]
need(manifest_refs,'round2 binds historical manifest')
earlier_refs=[x for x in refs if x['reference']['sha256']==ref(old_audit)['sha256']]
need(earlier_refs,'round2 binds earlier audit')
copy_ref_occurrences=[x for x in refs if x['reference']['path'].endswith('step_state_before_acceptance.json')]
need(not copy_ref_occurrences,'unexpected old copy explicit binding')
commit='f68c83c2918ae25d9811e4e9f703f1a158e143d2'
relative=statecopy.relative_to(ROOT).as_posix()
git_blob=subprocess.check_output(['git','show',commit+':'+relative],cwd=ROOT)
need(git_blob==statecopy.read_bytes(),'Git old copy bytes')
first=subprocess.check_output(['git','log','--diff-filter=A','--format=%H %aI %s','--',relative],cwd=ROOT,text=True).strip()
need(first.startswith(commit),'first tracked provenance')
scripts=[ROOT/BASE/'integration_codex'/n for n in ('accept_parent_codex.py','accept_parent_attempt1_source.py')]
for p in scripts:
 s=p.read_text(encoding='utf-8');need("('step_state_before_acceptance.json',state_raw)" in s and "stream.write(raw_before)" in s,'original raw copy code')
audit={'schema':'researchos.w04.historical-purpose-independent-audit.v1','at':datetime.now(timezone.utc).isoformat(),'round2_detail_ref':ref(detail),'old_bound_manifest_ref':ref(manifest),'manifest_bindings_from_round2':manifest_refs,'old_expected_source_mapping':mapping,'current_expected_source_ref':ref(ROOT/BASE/'executor_codex/expected.json'),'earlier_audit_ref':ref(old_audit),'earlier_audit_bindings':earlier_refs,'observed_input_key':statekey,'observed_old_state_sha256':oldhash,'actual_old_copy_ref':ref(statecopy),'copy_first_git_provenance':first,'git_blob_sha256':sha(git_blob),'original_root_writer_source_refs':[ref(p) for p in scripts],'old_detail_explicit_copy_refs':copy_ref_occurrences,'current_state_ref_for_separation_only':ref(ROOT/'execution/v2.4/step_state.json'),'reader_refs':[ref(ROOT/'execution/v2.4/formal_case_index.py'),ref(ROOT/BASE/'formal_validator_codex/validate.py')],'source_changes':0,'state_changes':0}
save('historical_purpose_audit.json',audit)
save('historical_purpose_scope_clarification.json',{'schema':'researchos.w04.independent-historical-purpose-clarification.v1','reviewer_id':'codex:/root/w05_merge_review','issued_at':datetime.now(timezone.utc).isoformat(),'decision':'EXACT_PURPOSE_SCOPE_READY_REQUIRES_HELPER_FIX_REVIEW','audit_ref':ref(OUT/'historical_purpose_audit.json'),'source_asset_ruling':{'permitted_exact_original_ref':mapping['original_ref'],'required_exact_old_mapping_manifest_ref':ref(manifest),'permitted_exact_snapshot_ref':mapping['snapshot_ref'],'purpose':'Historical expected.json is a frozen source/expected-roster asset in the earlier run vector. Its old manifest explicitly binds original bytes to copy. This exact version may be recovered from that exact old bound snapshot. It is not a proof/review/message substitution and must not replace the final run expected.json or alter actual expected IDs.','guard':'Match exact original path+075cdf digest+98e6 manifest+snapshot path/digest and confirm original is in that manifest own source_files vector; no suffix-based blanket JSON allowance. Keep current 24b3 source value separately observed.'},'mutable_state_observation_ruling':{'parent_audit_ref':ref(old_audit),'field':'input_hashes','original_path':statekey,'historical_sha256':oldhash,'classification':'HISTORICAL_READ_OBSERVATION_WITH_NEW_TRANSITION_CORROBORATION','corroboration_ref':ref(statecopy),'first_tracked_commit':commit,'purpose':'The original audit input_hashes records the mutable canonical state bytes read before original acceptance. The unchanged old v1 reader produces such read snapshots; it does not require future canonical state to remain identical forever or recursively treat every nested hash map as a present receipt ref. Original audit bytes remain mandatory and unchanged.','truth_claim':'The existing old Root saved raw copy matches the exact old observed SHA and is already present in the original acceptance Git commit. This transition may add a transparent corroboration ref proving those historical bytes now. The old review did not explicitly bind that copy path, so this is NOT an original-review-authorized snapshot-map edge.','guard':'Handle only this exact immutable parent audit hash, input_hashes field, original canonical path and old SHA. Verify existing copy bytes+Git provenance+original writer code; record the new corroboration classification separately. Do not install generic STATE→snapshot fallback; all current state reads/CAS must still use actual current raw bytes. Do not call the old state current or invent a missing original reference.','failure_rule':'If the actual copy or provenance cannot be verified, report unavailable corroboration; do not synthesize a copy or claim historical state replay PASS. Changed mandatory old receipt/raw/message refs still fail closed.'},'implementation_constraints':['Preserve all original receipts, roots, metadata and copy bytes. Change only already scoped register.py/test_register.py with explicit purpose guards; do not modify frozen formal reader or old evidence.','New archive/graph/plan must expose exact source-map evidence and separately additional historical corroboration ref and provenance. Independent transition review signs this new interpretation explicitly.','The actual current STATE must not remain in a historical drift list requiring prewrite hash after own successful write. Keep historical observation separate from normal current-state CAS; only own known write may change current state guard at postcommit.','Negative controls: wrong parent audit/hash/field/path/version, unbound alternate expected JSON, changed snapshot/copy bytes, fabricated Git provenance, any receipt/message substitution, reuse of old copy as current CAS all refuse.'],'formal_acceptance_delta':0,'source_or_canonical_changes':0})
# Separate exact registry candidate assessment; no mutation/dispatcher call.
rdir=ROOT/BASE/'integration_codex/command-registry-candidate-17a8c4c045da40b6a1acb433998c9243'
plan=read(rdir/'change-plan.json');old=read(rdir/'commands-r39.original.json');new=read(rdir/'commands-r40.candidate.json')
need(ref(rdir/'change-plan.json')['sha256']=='2220ae8098afee7c389dc5046dc645d6bbb452534981d394d50c44f234517fee','registry plan')
need(ref(rdir/'commands-r40.candidate.json')['sha256']=='a5d5bbe34792151f14f46e61e8fda395bb81825acfcea6b7bacc1bebd214602a','registry candidate')
need(sha((ROOT/'execution/v2.4/commands.json').read_bytes())==plan['old_ref']['sha256']==ref(rdir/'commands-r39.original.json')['sha256'],'live registry CAS baseline')
wanted=copy.deepcopy(old);wanted['revision']=40
changed=('test.context','test.domain','package.validate');prefix=BASE+'executor_codex/';replacement=BASE+'executor_revalidation_codex/'
for key in changed:
 for field in ('argv','expected_artifacts'):wanted['commands'][key][field]=[x.replace(prefix,replacement) if isinstance(x,str) else x for x in wanted['commands'][key][field]]
need(new==wanted,'registry unexpected difference')
unchanged=set(old['commands'])-set(changed);need(len(unchanged)==29 and all(old['commands'][k]==new['commands'][k] for k in unchanged),'29 unchanged')
for key in changed:
 for p in new['commands'][key]['expected_artifacts']:need((ROOT/p).is_file(),'integrated target missing '+p)
save('registry_scope_review.json',{'schema':'researchos.w04.independent-registry-candidate-scope-review.v1','reviewer_id':'codex:/root/w05_merge_review','issued_at':datetime.now(timezone.utc).isoformat(),'decision':'EXACT_SCOPE_READY_PENDING_ROOT_HELPER_SOURCE_READY','change_plan_ref':ref(rdir/'change-plan.json'),'old_ref':ref(rdir/'commands-r39.original.json'),'candidate_ref':ref(rdir/'commands-r40.candidate.json'),'live_ref':ref(ROOT/'execution/v2.4/commands.json'),'actual_diff':'Exactly revision39→40 and executor_codex→executor_revalidation_codex path replacement within argv/expected_artifacts for three named entries. All other top-level fields and complete selectors/env/limits/notes unchanged.','changed_commands':list(changed),'unchanged_other_entries':29,'target_files_exist':True,'old_commands_snapshot_byte_preserved':True,'preapply_conditions':['Root helper must become independently SOURCE_READY first, per change plan.','Root serial CAS recheck actual commands SHA/revision immediately before atomic application; preserve complete original r39 raw and candidate.','Then final MAIN source/registry freeze, fresh W04 collection and eleven actual dispatches; scope approval is not native product proof.','Application changes exact registry vector and makes prior A05 CURRENT stale; preserve its original evidence and perform fresh final-vector W07 revalidation.'],'source_or_registry_changes':0,'formal_acceptance_delta':0})
print(json.dumps({'historical_clarification':ref(OUT/'historical_purpose_scope_clarification.json'),'historical_audit':ref(OUT/'historical_purpose_audit.json'),'registry_scope':ref(OUT/'registry_scope_review.json')},ensure_ascii=False))
