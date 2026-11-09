import hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==582 and len(cp['failure_counters'])==2359
assert not (out/'checkpoint.cp582.before-integration.json').exists()
integration=json.loads((out/'integration.json').read_bytes())
design=json.loads((out/'reviews/delivery-contract-design-review.json').read_bytes())
assert sha(out/'reviews/delivery-contract-design-review.json')=='10c48adcb3423d2717454ad69509a6629e81eb03399a9520bffd99cb8b64adb0'
initial=cp['failure_counters'][:];now=datetime.now(timezone.utc).isoformat()
(out/'checkpoint.cp582.before-integration.json').write_bytes(raw)
imported=[]
for relative,key in [('author/diagnostics.json','records'),('reviews/delivery-contract-design-review.json','diagnostics'),('reviews/prompt-review.json','diagnostics')]:
    doc=json.loads((out/relative).read_bytes())
    for index,event in enumerate(doc.get(key,[])):
        imported.append({'origin_key':f'20261104|cli-prompt-bridge|{relative}|{index}','at':now,'attempts':1,'status':'PRESERVED_DEVELOPMENT_OR_TOOL_DIAGNOSTIC','detail':event,'source_ref':{'path':str((out/relative).relative_to(root)),'sha256':sha(out/relative)},'counter_reset':False})
for origin,chunk,exitcode,detail,ref in [
    ('scope-porcelain-leading-space','7dcdcc',0,'Root .strip() removed first porcelain leading space; first protected path key lost e. Saved v1 and corrected exact actual deleted path; no product source or deleted-file changes.','metadata-correction.json'),
    ('sparse-add-unsupported-option','6d4fc6',1,'sparse-checkout add rejected --no-cone with Git129 before applying patterns. Confirmed existing non-cone mode and directed retry ee77d9 materialized12 production Go files, preserving all7 CLI hashes.','source-closure-repair.json')]:
    imported.append({'origin_key':'20261104|cli-prompt-bridge|root|'+origin,'at':now,'attempts':1,'status':'ROOT_CONTROL_OR_RESOURCE_DIAGNOSTIC','tool_chunk':chunk,'exit':exitcode,'detail':detail,'source_ref':{'path':str((out/ref).relative_to(root)),'sha256':sha(out/ref)},'counter_reset':False})
known={r.get('origin_key') for r in initial}
for record in imported:
    assert record['origin_key'] not in known;cp['failure_counters'].append(record);known.add(record['origin_key'])
assert cp['failure_counters'][:2359]==initial
put(out/'diagnostic-import.json',{'before':2359,'after':len(cp['failure_counters']),'prefix_preserved':True,'imported':imported,'mixed_development_and_tool_diagnostics_not_native_product_failure_count':True})
refs={}
for relative in ['integration.json','author/author-summary.json','author/source-manifest.json','reviews/prompt-review.json','reviews/delivery-contract-design-review.json','metadata-correction.json','source-closure-repair.json','local-runtime-inventory.json']:
    refs[relative]={'path':str((out/relative).relative_to(root)),'sha256':sha(out/relative)}
state=root/'execution/v2.4/step_state.json'
assert sha(state)=='168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e'
cp['expected_previous_revision']=582;cp['revision']=583;cp['updated_at']=now;cp['updated_by']='codex:/root'
cp['head']=integration['main_head'];cp['current_Main_HEAD']=integration['main_head'];cp['current_Main_tree']=integration['main_tree']
cp['current_effective_formal_status']['current_head']=integration['main_head'];cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
status=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks','status','--porcelain=v1','-uno'],cwd=root).decode('utf-8')
cp['dirty_paths']=status.splitlines()
next_command='Build the reviewed source in the existing isolated workbench worktree into new development-ui-20261104-r3 using tools/compatibility-development-build.py '+integration['main_head']+'. Keep r2 unchanged. Offline build and launcher dry-run only; no native/model replay. Read CLI scope RESUME first. Ordinary LIVE delivery contract design remains CHANGES_REQUIRED, not implemented.'
resume={'schema':'researchos.cp583-resume.v1','checkpoint_revision':583,'status':'CLI_PROMPT_SOURCE_INTEGRATED_DEVELOPMENT_BUILD_PENDING','main_head':integration['main_head'],'main_tree':integration['main_tree'],'current_card':'W05-99','refs':refs,'formal_accepted':0,'formal_required':42,'all_22_parents_accepted':False,'formal_increment':0,'failure_records':len(cp['failure_counters']),'counter_reset':False,'step_state_unchanged':True,'native_calls_this_scope':0,'provider_inference_calls_this_scope':0,'actual_functionality':['task and run --prompt / --prompt-file use existing authenticated session.send -> finiteGoal path; this is not a direct goal.start call.','Strict bounded UTF8 parsing precedes host/auth/HTTP; exact int64 preserved; legacy dispatch remains.'],'baseline_blocker':'Existing TestW14CLICommandsUseRealSessionHTTP fails WRITER_BUSY in both candidate and exact-base overlay; tests/gates unchanged.','business_acceptance_design':'CHANGES_REQUIRED: untrusted go test output can spoof events, and current Goal/Task shared contract cannot converge. No LIVE503 gate was changed.','remaining':['W05 Mu formal LIVE driver absent','Trusted first-use workspace selection and current qualification required','Declared local model endpoint refused connection; no Ollama process observed','Ordinary business LIVE acceptance requires an independently reviewed trusted checker and separate Task/Goal contracts','W14 writer takeover baseline fixture remains unresolved'],'next':next_command}
put(out/'RESUME.json',resume)
cp['next_command']=next_command
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'integration_ref':refs['integration.json'],'active_construction_owners':[],'formal_increment':0}
cp['workers'].append({'step_id':'W05-99','slice_id':'CLI_PROMPT_BRIDGE_20261104','owner':'codex:/root/workbench_builder','worktree':str(root/'.local/worktrees/cli-prompt-bridge-20261104'),'state':'INDEPENDENT_SOURCE_REVIEWED_AND_INTEGRATED_BASELINE_W14_QUALIFICATION_BLOCKED','main_source_head':integration['main_head'],'integration_ref':refs['integration.json']})
cp['blocked_resources'].append({'resource_id':'CURRENT_CODING_DELIVERY_CONTRACT_DESIGN','status':'CHANGES_REQUIRED_BEFORE_LIVE_GOAL_EXCEPTION','blocks':['Ordinary coding business LIVE acceptance only'],'evidence':refs['reviews/delivery-contract-design-review.json'],'other_branches_remain_eligible':True,'recorded_at':now})
cp['blocked_resources'].append({'resource_id':'EXISTING_W14_WRITER_TAKEOVER_FIXTURE','status':'BASE_AND_CANDIDATE_WRITER_BUSY','blocks':['W14 CLI/Desktop writer takeover qualification only'],'evidence':refs['author/author-summary.json'],'other_branches_remain_eligible':True,'recorded_at':now})
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp582.before-integration.md').write_bytes(before)
prefix=('# Current resume CP583\n\nRead execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/RESUME.json. CLI explicit prompt compatibility is source-reviewed and integrated at '+integration['main_head']+'. New prompt checks pass; W14 takeover fixture fails equally at base/candidate and remains open. Development bundle r3 pending. LIVE coding contract design has two blockers; ordinary503 unchanged. Failure history retained; no native/model inference; formal0/42 and not all22parents.\n\n').encode()
temp=handoff.with_name(handoff.name+'.cp583.new');temp.write_bytes(prefix+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':583,'main_head':integration['main_head'],'failure_records':len(cp['failure_counters']),'formal_increment':0}))
