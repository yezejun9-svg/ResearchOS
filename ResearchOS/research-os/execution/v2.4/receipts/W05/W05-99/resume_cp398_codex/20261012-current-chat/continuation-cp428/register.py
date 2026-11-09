import copy,datetime,hashlib,json,os,pathlib
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');CANON=ROOT/'execution/v2.4';OUT=pathlib.Path(__file__).resolve().parent
paths=[CANON/'checkpoint.json',CANON/'path_ownership.json',CANON/'HANDOFF_RESUME_PACK.md'];old={p:p.read_bytes() for p in paths}
cp=json.loads(old[paths[0]].decode('utf-8-sig'));ow=json.loads(old[paths[1]].decode('utf-8-sig'));assert cp['revision']==427 and ow['revision']==215
failures=copy.deepcopy(cp['failure_counters']);state=(CANON/'step_state.json').read_bytes();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def ref(p):
 raw=p.read_bytes();return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write_new(p,d):
 assert not p.exists(),str(p);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
base=OUT.parent/'continuation-cp426/first-use-contract-scope.json';scope=json.loads(base.read_text(encoding='utf-8-sig'))
assessment=ref(CANON/'receipts/W05/W05-99/normal_first_use_contract_repair_review_codex/20261012-current-chat/scope-addendum-sixth-file-01.json')
assert assessment['sha256']=='36dd338801723a878b57a207bae4e4b7167e88d1bf7b5ca66741ab6e3122b101'
scope.update(schema='researchos.exact-causal-source-scope.v2',at=now,prior_scope_ref=ref(base),independent_sixth_path_assessment_ref=assessment)
scope['paths'].append('tests/ui/desktop/http-wire-boundary.test.mjs')
scope['repairs'].append('Correct only old host.status revision=1 HTTP boundary expectation to VALID and add schema-invalid revision=0 negative; preserve all adjacent identity negatives.')
scope['limits'][0]='Only these six source paths in the original isolated first-use repair worktree.'
write_new(OUT/'first-use-contract-scope-six.json',scope);sr=ref(OUT/'first-use-contract-scope-six.json')
cp.update(revision=428,expected_previous_revision=427,updated_at=now,updated_by='codex:/root')
ow.update(revision=216,expected_previous_revision=215,updated_at=now,updated_by='codex:/root')
ow['path_lease_transfers'].append({'at':now,'actor':'codex:/root','new_owner':'codex:/root/w05_main24','new_subtask':'W05-99/normal_first_use_contract_repair','new_worktree':scope['worktree'],'paths':['tests/ui/desktop/http-wire-boundary.test.mjs'],'scope_ref':sr,'kind':'SINGLE_INVALID_OLD_TEST_EXPECTATION_CAUSAL_SCOPE_AMENDMENT'})
p=CANON/'receipts/W05/W05-99/normal_first_use_contract_repair_codex/20261012-current-chat'
for key,attempts,status,evidence in [
 ('first-use-source-sparse-dependencies',2,'ORIGINAL_EVALUATION_AND_SPEC_ABSENCE_FAILS_PRESERVED_AFTER_TRACKED_INPUT_MATERIALIZATION_PASS',[ref(p/'go-targeted-run1.log'),ref(p/'go-targeted-run2.log')]),
 ('first-use-bound-test-flag-serialization',1,'ORIGINAL_FLAG_PROVIDED_BUT_NOT_DEFINED_TEST_DIAGNOSTIC_PRESERVED_CORRECT_ARGV_PASS',[ref(p/'bound-validator-targeted.log'),ref(p/'bound-validator-targeted-run2.log')]),
 ('first-use-http-old-invalid-revision-expectation',1,'BOUND_180_OF_181_OLD_TEST_EXPECTATION_CONTRADICTS_FROZEN_SCHEMA_NEW_EXACT_SIXTH_SCOPE',[ref(p/'bound-http-suite.log'),assessment]),
 ('own-cli-target-dependency-sparse-input',1,'GO_LIST_EXIT1_MISSING_TRACKED_EVALUATION_PRESERVED_NEW_INPUT_OFFLINE_LIST_EXIT0_SOURCE_UNCHANGED',[ref(CANON/'receipts/W05/W05-99/own_cli_product_target_preparation_codex/20261012-current-chat/dependency-list-01.invocation.json'),ref(CANON/'receipts/W05/W05-99/own_cli_product_target_preparation_codex/20261012-current-chat/dependency-list-02.invocation.json')]),
]:
 origin='current-chat-20261012|'+key;assert not any(x.get('origin_key')==origin for x in failures)
 cp['failure_counters'].append({'origin_key':origin,'attempts':attempts,'status':status,'counter_reset':False,'evidence_refs':evidence,'actual_models':0})
cp['work_in_progress'].update(first_use_contract_scope_ref=sr,first_use_source_status='FIVE_PRODUCTION_AND_TEST_SCOPE_CAUSAL_FIX_ADDITIONAL_SIXTH_INVALID_OLD_TEST_PENDING_FINAL_BOUND_BUILD')
cp['next_command']='Finish minimal old host.status HTTP expectation correction in six-path firstuse scope, new frozen bound build then independent review. Coding exact8 repair remains parallel source-only, full builds serialized. Reuse original Native data in next real Desktop after accepted components; no model until explicit qualification. Formal0/42/all22 open.'
resume={'schema':'researchos.current-chat-resume.v24','at':now,'checkpoint_revision':428,'ownership_revision':216,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'goal_status':'ACTIVE','failure_records_preserved':len(cp['failure_counters']),'firstuse_scope_six_ref':sr,'coding_repair_scope_ref':cp['work_in_progress']['coding_client_repair_scope_ref'],'active_source_limit':2,'original_data_preserved':True,'real_models_this_preparation':0,'phone_user_answer':'USE_REAL_PHONE_WHEN_PRODUCT_PAIRING_READY','phone_ready':False,'next_command':cp['next_command']}
write_new(OUT/'RESUME.current.json',resume);cp['artifacts'].extend([assessment,sr,ref(OUT/'RESUME.current.json')]);cp['work_in_progress']['current_chat_resume_ref']=ref(OUT/'RESUME.current.json')
assert cp['failure_counters'][:len(failures)]==failures;assert cp['no_progress_rounds']==json.loads(old[paths[0]].decode('utf-8-sig'))['no_progress_rounds']
for f,name in zip(paths,['checkpoint.before.raw.json','ownership.before.raw.json','HANDOFF.before.raw.md']):
 assert not (OUT/name).exists();(OUT/name).write_bytes(old[f]);assert f.read_bytes()==old[f]
assert (CANON/'step_state.json').read_bytes()==state
handoff=('# Current verified continuation CP428\n\nRead `'+ref(OUT/'RESUME.current.json')['path']+'` first. First-use scope now exactly six files to correct one old invalid expectation; preserve failed 180/181 suite and all diagnostics. Coding repair retains separate exact8 scope, both source branches pending independent acceptance. Formal0/42/all22 open.\n\n').encode()+old[paths[2]]
for f,raw in [(paths[0],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode()),(paths[1],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode()),(paths[2],handoff)]:
 tmp=f.with_name(f.name+'.cp428.tmp');assert not tmp.exists();tmp.write_bytes(raw);os.replace(tmp,f)
print(json.dumps({'checkpoint':428,'ownership':216,'source_scope':sr,'resume':ref(OUT/'RESUME.current.json'),'old_failure_records':len(failures),'new_failure_records':4,'formal_increment':0},ensure_ascii=False))
