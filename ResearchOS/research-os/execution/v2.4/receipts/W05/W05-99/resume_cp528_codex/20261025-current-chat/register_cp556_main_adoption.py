import datetime,json,os,sys
from pathlib import Path
from preserve_desktop_main_ecc28 import verify
from preserve_main_baseline import read,ref,R,N
from verify_cp554_main_preflight import BASE,CANDIDATE,TREE,FILES
def new(p,v):
 with p.open('x',encoding='utf8')as s:json.dump(v,s,ensure_ascii=False,indent=2);s.write('\n')
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp556.pending')
 with q.open('xb')as s:s.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
review=Path(sys.argv[1]);assert ref(review)['sha256']==sys.argv[2]
seal=read(review);assert seal['verdict']=='EXACT_MAIN_FAST_FORWARD_POST_REVIEW_PASS'and seal['blocking_findings']==0 and seal['new_unexpected_diagnostics']==0
assert seal['main_commit']==CANDIDATE and seal['main_tree']==TREE and seal['direct_parent']==BASE and seal['C57_merged']is False and seal['formal_increment']==0
assert seal['scope_sha256']==ref(N/'continuation-cp555/Desktop-Main-integration-scope.json')['sha256']
manifest=review.parent/'POST-MANIFEST.json';assert ref(manifest)['sha256']==seal['manifest_sha256'];review_refs=[]
for x in read(manifest)['files']:
 a=ref(review.parent/x['path']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];review_refs.append(a)
assert len(review_refs)==seal['reference_count']==25
assert ref(review.parent/'DIAGNOSTICS.json')['sha256']==seal['diagnostics_sha256']
selector=read(N/'091-selector-Main-ecc28.recipe.stdout.raw')
assert read(N/'091-selector-Main-ecc28.recipe.result.json')['native_exit']==0
assert selector['state_source']=='VALIDATED_FILE' and selector['read_only']is True and selector['product_acceptance']=='NOT_ASSERTED' and selector['step']['id']=='W05-99'
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==555 and ow['revision']==341 and len(cp['failure_counters'])==2250
preserved=verify();I=N/'desktop-main-integration-01';result=read(I/'result.json')
assert result['Main']==CANDIDATE and result['tree']==TREE and result['git_native_exit']==0
assert read(I/'git-result.json')['native_exit']==0 and read(N/'090-desktop-main-integration.recipe.result.json')['native_exit']==0
assert preserved==read(I/'preservation.after.json')
prior=read(N/'continuation-cp555/RESUME.current.json');O=N/'continuation-cp556';O.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
adopt={'schema':'researchos.desktop-main-integration-limited-adoption.v1','at':now,'status':'EXACT_SEVEN_PATH_MAIN_INTEGRATION_INDEPENDENTLY_ACCEPTED_LIMITED','Main_HEAD':CANDIDATE,'Main_tree':TREE,'previous_Main':BASE,'allowed_paths':FILES,'integration_result_ref':ref(I/'result.json'),'independent_post_review_seal_ref':ref(review),'source_build_and_native_adoption_ref':prior['Desktop_owned_native_adoption_ref'],'original20dirty_preserved':True,'original48refs_preserved':True,'seven_disk_files_equal_reviewed_git_blobs':True,'evidence_reuse':'Existing immutable isolated source/build and owned native smoke evidence applies to identical candidate bytes; no Main-root GUI/native test was run','platform_commands':'desktop.shell_launch and desktop.installer_build remain UNBOUND; release.reproduce remains ABSENT','C57':'03aa frozen, not merged; administrator USER_PREPARING_NOT_VERIFIED','original_data_action':False,'formal_increment':0,'formal_accepted':0,'formal_required':42,'all22parents_open':True}
new(O/'Desktop-Main-integration-limited-adopted.json',adopt);new(O/'Main-preservation.current.json',preserved)
new(O/'Root-independent-post-ref-verification.json',{'verified_refs':review_refs,'review_seal_ref':ref(review),'blocking_findings':0,'new_review_diagnostics':0})
record={'origin_key':'20261025|root-main-post-review-wait-aborted','attempts':1,'status':'TOOL_PROTOCOL_DIAGNOSTIC_PRESERVED','detail':'collaboration.wait_agent timeout40000 aborted before dispatch adjacent to post-review seal message; tool transcript only; no native operation','native_exit':None,'counter_reset':False}
assert record['origin_key']not in {x.get('origin_key')for x in cp['failure_counters']}
old_counters=list(cp['failure_counters']);cp['failure_counters'].append(record);assert cp['failure_counters'][:2250]==old_counters and len(cp['failure_counters'])==2251
new(O/'new-records-ledger.json',{'records':[record],'mixed_record_increment':1,'source_or_product_failure':False,'counter_reset':False})
new(O/'Selector-current.json',{'state_source':'VALIDATED_FILE','read_only':True,'product_acceptance':'NOT_ASSERTED','selected_step':'W05-99','result_ref':ref(N/'091-selector-Main-ecc28.recipe.result.json'),'raw_stdout_ref':ref(N/'091-selector-Main-ecc28.recipe.stdout.raw'),'formal_increment':0})
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v134',at=now,checkpoint_revision=556,ownership_revision=342,head=CANDIDATE,current_Main_HEAD=CANDIDATE,current_Main_tree=TREE,Desktop_Main_integration_adoption_ref=ref(O/'Desktop-Main-integration-limited-adopted.json'),Desktop_Main_preservation_gate_ref=ref(N/'preserve_desktop_main_ecc28.py'),active_source_cards=[])
resume['failure_records_preserved']=2251
resume['legacy_pid_fields_are_historical_not_current_liveness_evidence']=True
resume['next_command']='Desktop exact7 is integrated on Main ecc28 by local fast-forward and independently reviewed; original20dirty/48refs and C57 frozen03aa preserved. Source/build and one owned native smoke evidence reuse only for identical candidate bytes; no Main-root GUI run or installer/formal acceptance. C57 administrator USER_PREPARING_NOT_VERIFIED: verify fresh ready distinctSID/elevation before any scoped original recovery. Continue dependency-ready development branches; mixed2251;formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=556,expected_previous_revision=555,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'],current_Main_HEAD=CANDIDATE,current_Main_tree=TREE);cp['work_in_progress'].update(current_chat_continuation_cp556=rr,Desktop_Main_integration_adoption_ref=ref(O/'Desktop-Main-integration-limited-adopted.json'));cp['evidence_index'].append({'kind':'DESKTOP_EXACT_SEVEN_MAIN_INTEGRATION_INDEPENDENTLY_ACCEPTED_LIMITED_FORMAL_ZERO','ref':rr,'formal_increment':0})
ow.update(revision=342,expected_previous_revision=341,updated_at=now,updated_by='codex:/root');ow['special_paths']['Desktop_Main_integration'].update(state='EXACT_SEVEN_FAST_FORWARD_INDEPENDENTLY_ACCEPTED_LIMITED',source_edit_authority=False,evidence_ref=ref(O/'Desktop-Main-integration-limited-adopted.json'));ow['special_paths']['Desktop_Main7d_development_build'].update(state='ECC28_DEVELOPMENT_IMPLEMENTATION_INTEGRATED_MAIN_SOURCE_BUILD_OWNED_NATIVE_LIMITED',source_edit_authority=False,evidence_ref=ref(O/'Desktop-Main-integration-limited-adopted.json'))
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as s:s.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());swap(hp,raw[hp],('# Current verified continuation CP556\n\nRead '+rr['path']+' first. Main ecc28 now includes exact7 Desktop development build/launcher/smoke source after independent pre/post integration review. React workbench retained. Original20dirty/48refs and C57 frozen03aa unchanged. Reuse source/build/owned native evidence only for identical bytes; platform commands still UNBOUND and no installer/formal acceptance. Administrator USER_PREPARING_NOT_VERIFIED. All failures and cleanup denials retained. Mixed2251;formal0/42/all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':556,'ownership':342,'mixed_records':2251,'Main':CANDIDATE,'adoption':ref(O/'Desktop-Main-integration-limited-adopted.json'),'resume':rr,'formal_increment':0},ensure_ascii=False))
