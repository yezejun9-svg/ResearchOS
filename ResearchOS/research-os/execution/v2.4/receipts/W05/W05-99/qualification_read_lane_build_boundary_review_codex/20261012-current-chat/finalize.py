import datetime,hashlib,json,pathlib
OUT=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
obs=json.loads((OUT/'observations.json').read_text(encoding='utf-8'))
acl=json.loads((OUT/'installer-acl-02.json').read_text(encoding='utf-8'))
assert acl['protected'] and len(acl['rules'])==1 and acl['rules'][0]=={'sid':acl['owner_sid'],'rights':'FullControl','type':'Allow','inherited':False}
before=json.loads((OUT/'inputs.before.json').read_text(encoding='utf-8'))
drift=[p['path'] for p in before if sha(pathlib.Path(p['path']))!=p['sha256']]
assert not drift,drift
spec=ROOT/'.local/worktrees/v24-continuation/spec/v2.4/PACKAGE_MANIFEST.json'
pointer=json.loads((ROOT/'execution/v2.4/current_spec.json').read_text(encoding='utf-8'))
assert sha(spec)==pointer['manifest_sha256']
effective={**obs['checks'],'old_installer_acl_protected_owner_only':True,'spec_manifest_matches':True}
assert all(effective.values()),effective
observer=ROOT/'execution/v2.4/receipts/W05/W05-99/normal_qualification_actual_observer_codex/20261012-current-chat'
observer_inputs=[{'path':str(observer/n),'sha256':sha(observer/n),'bytes':(observer/n).stat().st_size} for n in ['observe.py','launch_and_wait.py','readiness-manifest-01.json']]
put('observer-static-review.json',{'mode':'SOURCE_READ_ONLY_NOT_EXECUTED','inputs':observer_inputs,'actual_sqlite_reads':0,'actual_launches':0,'assessment':'READINESS_WITH_EXPLICIT_BINDING_LIMITS','required_root_checks':['Original request stored-body hash comparison must be true','Require supplied Run id equals original request consume_rows.body.run_ref.id','Require actual Run Task/Goal active budget ancestry, not mere presence of GLOBAL PROJECT GOAL policy types','Package/descriptor/install binding separately required before launcher','Electron numeric wait does not infer Core worker or verifier wait'],'sensitive_boundaries':['Fixed request field set; omit idempotency headers and credential tables','Run lease_token_hash removed','Effects retain model payload/SSE; this is not a general sensitive-data audit','Do not export private verifier Job token']})
put('final-bindings.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs_unchanged':len(before),'drift':drift,'spec_manifest':{'path':str(spec),'sha256':sha(spec),'bytes':spec.stat().st_size},'effective_checks':effective,'acl_correction':'First subprocess observation is unavailable due to module load failure; second native PS7 observation proves current old package ACL. Original failure preserved.'})
put('report.json',{'schema':'researchos.read-lane-build-boundary-review/1','decision':'CORE_REUSE_CONDITIONAL_PENDING_UI_FREEZE_REVIEW_BUILD','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_ui_candidate_reviewed':False,'new_combined_package_accepted':False,'source_scope_sha256':'f83c964c67118aed5f7164519ac96b3bb0c33f46d61df047894a265235815a46','main_commit':obs['head'][0],'main_tree':obs['head'][1],'component_requirements':{'core_source':'cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8','control_sha256':'326f70d5d9097d6f648bc4479a1e9a609c8969f1052a74ff13ddb93f550487a3','verifier_sha256':'28ea9cc1af6d7b7bbe96765b19b17e6ac08f77ac9e89dc781407b023910aa9eb','ui_source':'PENDING_FROZEN_CANDIDATE_AND_INDEPENDENT_REVIEW','mu_source':'8dfebe36508ac0c2508735bb866756dab9283e74','validator':'REBUILD_WITH_FRESH_FULL_INPUT_DIGEST','descriptor_components_source_snapshot':'FRESH_HONEST_COMPONENT_VECTOR_REQUIRED'},'effective_checks':effective,'checklist':{'path':'report.md','sha256':sha(OUT/'report.md')},'private_raw_evidence_missing':['management stdout frames','verifier result frame','verifier independent numeric Wait exit'],'verification_scope':'Read-only source/package/hash/ACL and validated taskpacket; no product execution or actual qualification','task_packet':{'state_source':obs['task_packet_state_source'],'next_step':obs['next_step'],'exit':obs['task_packet_exit']},'actual_model_calls':0,'actual_tool_calls':0,'product_launches':0,'real_sqlite_reads':0,'source_or_canon_writes':0,'formal_increment':0,'parent_acceptance':False})
members=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['manifest.json','seal.json']]
put('manifest.json',{'schema':'researchos.readonly-review-manifest/1','members':members,'count':len(members)})
put('seal.json',{'report_sha256':sha(OUT/'report.json'),'checklist_sha256':sha(OUT/'report.md'),'manifest_sha256':sha(OUT/'manifest.json')})
print((OUT/'seal.json').read_text())
