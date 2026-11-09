import hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
res=read(N/'057-selector-cp545.recipe.result.json');assert res['native_exit']==0
sel=read(N/'057-selector-cp545.recipe.stdout.raw');assert sel['state_source']=='VALIDATED_FILE' and sel['step']['id']=='W05-99' and sel['product_acceptance']=='NOT_ASSERTED'
cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json');assert cp['revision']==545 and ow['revision']==331 and len(cp['failure_counters'])==2186
resume=N/'continuation-cp545/RESUME.current.json';assert ref(resume)['sha256']=='2a4a6b04341c927bc20487faae7d32ea813a320791818c46d1fc6d4377a35a70'
cur=read(resume);assert cur['accepted_formal_cases']==0 and cur['required_formal_cases']==42 and cur['required_parent_tasks']==22
pointer=read(R/'execution/v2.4/current_spec.json');spec=R/pointer['snapshot_relative_to_candidate_branch_worktree'];assert ref(spec/'contracts/execution.plan.json')['sha256']==pointer['plan_sha256']
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *a:subprocess.check_output(git+list(a),cwd=R)
head=g('rev-parse','HEAD').decode().strip();assert head==cur['current_Main_HEAD'] and not g('diff','--cached','--name-only')
base=read(N/'React-Main-integration-baseline.json');dirty=g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0));assert dirty==base['dirty_paths']
root_shared={'execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/HANDOFF_RESUME_PACK.md'}
for x in base['dirty_files']:
 if x['relative_path']in root_shared:continue
 p=R/x['relative_path'];assert p.is_file()==x['exists']
 if x['exists']:assert ref(p)['sha256']==x['sha256']
for x in base['protected_source']+base['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:
 assert ref(Path(x['path']))['sha256']==x['sha256']
assert ref(R/'execution/project_identity.json')['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
assert ref(R/'execution/v2.4/step_state.json')['sha256']=='168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e'
out={'schema':'researchos.current-goal-cp545-live-resume.v1','status':'VERIFIED_CONTINUE_EXISTING_C57','previous_goal_turn':'PROGRESS_CP541_TO_CP545_C51_PRESEAL_AND_LIFETIME_FIX_NATIVE_SD_CONTRACT_FINDINGS','checkpoint':545,'ownership':331,'mixed_records_preserved':2186,'state_source':sel['state_source'],'selected_step':'W05-99','Main_HEAD':head,'dirty_path_count_preserved':len(dirty),'protected9_exact':True,'original_dist33_exact':True,'staged_bundle3_exact':True,'identity_gitconfig_stepstate_exact':True,'formal_accepted':0,'formal_required':42,'parents_required':22,'C57_scope':cur['active_source_cards'],'prior_resume':ref(resume),'selector_result_ref':ref(N/'057-selector-cp545.recipe.result.json'),'source_change':False,'original_runtime_data_action':False}
with(N/'CP545-live-resume-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items()if k not in ['C57_scope','prior_resume','selector_result_ref']},ensure_ascii=False))
