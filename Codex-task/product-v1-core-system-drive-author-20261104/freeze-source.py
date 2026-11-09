from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
BASE=Path(__file__).resolve().parent
WT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-core-system-drive-20261104')
SCOPE=Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/core-system-drive/scope.json')
scope=json.loads(SCOPE.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
directory=BASE/'final';directory.mkdir(exist_ok=False)
results=json.loads((BASE/'checks-01/results.json').read_text())
assert all(row['exit_code']==0 for row in results)
check=json.loads((BASE/'checks-01/scope-check.json').read_text())
assert check['paths_exact'] and check['base_matches']
tap=(BASE/'checks-01/focused-node-tests.stdout.raw').read_text(encoding='utf-8')
assert '# tests 54\n' in tap and '# pass 54\n' in tap and '# fail 0\n' in tap and '# skipped 0\n' in tap
pins={}
for rel in scope['production_paths']+scope['test_paths']:
    p=directory/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((WT/rel).read_bytes())
    pins[rel]=sha(p);assert pins[rel]==sha(WT/rel)
    assert p.read_bytes()==(BASE/'source-write-01/after'/rel).read_bytes()
rel='apps/desktop/main/lib/desktop-management.js'
before=(BASE/'source-write-01/before'/rel).read_bytes();after=(WT/rel).read_bytes()
begin=b'function managedControlEnvironment(ambient, options) {'
end=b'\nfunction createDesktopManagement(options)'
prefix=before.split(begin,1)[0];suffix=before.split(end,1)[1]
assert prefix==after.split(begin,1)[0]
assert suffix==after.split(end,1)[1]
preserved={'all_code_before_environment_function_unchanged':True,'before_environment_prefix_sha256':digest(prefix),'all_code_after_environment_function_unchanged':True,'after_environment_suffix_sha256':digest(suffix),'core_cwd_startup_native_identity_pipe_job_stop_behavior_unchanged':True}
manifest={'schema':'researchos.core-system-drive.source-manifest/1','scope_path':str(SCOPE),'scope_sha256':sha(SCOPE),'worktree':str(WT),'base_head':scope['base_head'],'source_sha256':pins,'baseline_sha256':scope['baseline_sha256'],'preserved_boundaries':preserved,'exact2_git_status':True,'all_snapshots_match_live':True,'construction_frozen':True,'source_modification_permitted':False,'formal_increment':0}
write(directory/'source-manifest.json',manifest)
diagnostics={'schema':'researchos.core-system-drive.diagnostics/1','diagnostic_events':[],'failed_attempts_this_slice':0,'prior_context':{'rootcause_proposal':'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-systemdrive-rootcause-20261104/proposal.json','sha256':'1190a49389bede880d37d61fe3e3229134d58196d0db5dc6e582579023261cd2','carryforward_only':True,'count_again':False},'old_bundle_cache_and_failure_evidence_untouched':True}
write(directory/'diagnostics.json',diagnostics)
summary={'schema':'researchos.core-system-drive.author-summary/1','status':'IMPLEMENTED_SOURCE_FROZEN_FOR_INDEPENDENT_QA','decision':'AUTHOR_NOT_SELF_APPROVED','source_sha256':pins,
 'behavior':['Validate a required case-normalized SystemRoot as a nonempty absolute drive-qualified system directory, rejecting unresolved, relative, UNC/device/control/stream/traversal forms.','Require WINDIR, if retained, to name the same normalized system directory.','Derive one canonical SystemDrive from the validated root volume; ignore ambient SystemDrive and its case aliases entirely.','Keep original retained normal-account/PATH variables, case collisions, sensitive-variable drops and owned RESEARCHOS overrides.','Keep Core cwd and relative installed-resource loading unchanged; this does not implement full process cwd isolation.'],
 'checks':{'focused_node':{'exit_code':0,'tests':54,'pass':54,'fail':0,'skip':0,'top_level':27,'subtests':27,'environment_cases':34,'existing_management_smoke_cases':20,'raw_stdout':'checks-01/focused-node-tests.stdout.raw','raw_stderr':'checks-01/focused-node-tests.stderr.raw','selected_files':['tests/ui/desktop/managed-environment.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/development-smoke.test.mjs']},'management_syntax':0,'test_syntax':0,'git_diff_check':0,'git_exact2':True,'base_matches':True},
 'test_fixture_changes':'Two existing positive fixtures now supply the required synthetic public SystemRoot; their optional-home/PATH assertions remain. Four original tests retained, plus30 new actual environment cases.',
 'preserved_boundaries':preserved,'limits':['Pure source/environment/management fixtures do not prove Windows Shell cache expansion or actual fresh GUI behavior.','Root must build a fresh valid bundle and separately scope any actual Desktop/model run. No poisoned bundle modification, cache deletion or manifest-guard relaxation.','Go Harness child environment and standard launcher SystemDrive forwarding are separate paths outside this Core-only slice.'],
 'real_execution':{'app_gui':0,'native':0,'model':0,'auth_file_access':0,'old_user_db_access':0,'cache_db_access':0,'poisoned_bundle_writes':0,'old_probe_replay':0},'pending_author_sessions':0,'independent_review_required':True,'formal_increment':0,'product_acceptance_increment':0}
write(directory/'summary.json',summary)
frozen={'schema':'researchos.core-system-drive.freeze/1','at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'source_manifest_sha256':sha(directory/'source-manifest.json'),'summary_sha256':sha(directory/'summary.json'),'diagnostics_sha256':sha(directory/'diagnostics.json'),'all2_source_pins_match_live':True,'pending_author_sessions':0,'author_self_acceptance':False,'formal_increment':0,'product_acceptance_increment':0}
write(directory/'FROZEN.json',frozen)
selected=sorted([p for p in BASE.rglob('*') if p.is_file() and p.name not in ['EVIDENCE_MANIFEST.json','archive-file-list.json']],key=lambda p:p.relative_to(BASE).as_posix())
write(BASE/'EVIDENCE_MANIFEST.json',{'schema':'researchos.core-system-drive.evidence/1','source_sha256':pins,'files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in selected],'runtime_data_or_cache_included':False})
write(BASE/'archive-file-list.json',{'schema':'researchos.core-system-drive.archive/1','root':str(BASE),'files':[p.relative_to(BASE).as_posix() for p in selected]+['EVIDENCE_MANIFEST.json','archive-file-list.json'],'note':'Exact2 before/after/final source snapshots, commands/raw logs and evidence only; no node_modules/cache/dist/executable/profile/auth/DB/cache DB.','evidence_manifest_sha256':sha(BASE/'EVIDENCE_MANIFEST.json')})
for rel,digest_value in pins.items():assert sha(WT/rel)==digest_value
print(json.dumps({'status':'FROZEN','source_manifest_sha256':sha(directory/'source-manifest.json'),'freeze_sha256':sha(directory/'FROZEN.json'),'summary_sha256':sha(directory/'summary.json'),'diagnostics_sha256':sha(directory/'diagnostics.json'),'evidence_sha256':sha(BASE/'EVIDENCE_MANIFEST.json'),'archive_list_sha256':sha(BASE/'archive-file-list.json'),'evidence_files':len(selected),'source_sha256':pins,'all2_live_pins_match':True,'construction_frozen':True}),flush=True)
