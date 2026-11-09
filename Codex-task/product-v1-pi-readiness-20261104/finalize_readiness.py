from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
inventory = json.loads((root/'public-inventory.json').read_text(encoding='utf-8'))
package = Path(inventory['package']['path'])
assert not (root/'readiness.json').exists()
bad = [row['path'] for row in inventory['sources'] if sha(Path(row['path'])) != row['sha256']]
bad += [row['path'] for row in inventory['bundle']['files'] if sha(package/row['path']) != row['sha256']]
for row in inventory['direct_dependency_metadata']:
    if row['present_at_package_dependency_path'] and sha(package/'node_modules'/row['name']/'package.json') != row['package_sha256']:
        bad.append(row['name'])
assert not bad
assert not any(row.get('registered_pin_matches') is False for row in inventory['sources'])
ui = json.loads(Path(inventory['ui_freeze02']['path']).read_text(encoding='utf-8'))
assert all(sha(Path(ui['worktree'])/name) == digest for name,digest in (ui['source_sha256']|ui['test_sha256']).items())
source_refs = {Path(row['path']).as_posix().split('/pi-coding-agent/')[-1]:row['sha256'] for row in inventory['sources'] if '/pi-coding-agent/' in Path(row['path']).as_posix()}
gaps = [
    {'id':'PI-PREREQUISITE','stage':'before_source_implementation','status':'ROOT_TO_CONFIRM','detail':'Plan S07 depends on S06; S08 depends on S05/S07. Root requires the single-Harness real loop first. This artifact does not establish those journeys.'},
    {'id':'PI-OUTER-CONTRACT','stage':'before_source_implementation','status':'REQUIRED','detail':'Frozen harness.v1 revision2 is Codex-only. Root must register/freeze the actual multi-Harness DTO and source ownership.'},
    {'id':'PI-AUTH','stage':'before_real_execution','status':'UNVERIFIED','detail':'No provider-specific status command was run, no native credential/config file inspected, no login initiated. Do not assume Codex login authorizes Pi or that a model is usable.'},
    {'id':'PI-READONLY-BOUNDARY','stage':'before_real_review','status':'UNVERIFIED','detail':'Read accepts absolute/home-relative paths. Tools flags alone are not filesystem confinement. Root must choose no-tools fixed-input review or separately prove an allowed Windows boundary.'},
    {'id':'PI-STARTUP-STATE','stage':'before_real_execution','status':'REQUIRED','detail':'CLI help/version have startup settings/cleanup/cache side effects; no-session does not isolate config/auth. Respect platform policy and establish owned state without copying credentials.'},
    {'id':'PI-SETTINGS-MUTATORS','stage':'before_real_execution','status':'REQUIRED','detail':'set_auto_retry/set_auto_compaction save global settings. Define an owned settings strategy and automatic-work policy before using those commands.'},
    {'id':'PI-RPC-CANCEL-LIFECYCLE','stage':'before_real_acceptance','status':'UNVERIFIED','detail':'No handshake, provider request, event reconstruction, clear_queue/abort or Windows child/stream cleanup has been observed.'},
    {'id':'PI-DISTRIBUTION-NOTICES','stage':'before_distribution','status':'UNVERIFIED','detail':'MIT declaration observed; no top-level license/notice text found. Verify required copyright and all bundled/transitive notices before packaging.'},
]
diagnostics = [
    {'unique_origin':'PI-PLAN-LOCATOR','classification':'READONLY_LOCATOR','tool_origin':'1a9a07','detail':'docs/product-v1/plan.json was absent; PLAN.md identified execution/product-v1/plan.json, subsequently read.'},
    {'unique_origin':'PI-PUBLIC-DISCOVERY-OUTPUT','classification':'READONLY_OUTPUT_TRUNCATION','tool_origin':['435a80','117f0f'],'detail':'A broad public package file/docs discovery included nested dependencies and was truncated. Follow-ups used explicit dist/docs paths; no profile/private data was read.'},
    {'unique_origin':'PI-MODELS-LOCATOR','classification':'READONLY_LOCATOR','tool_origin':'77f0d9','detail':'A guessed public pi-ai/dist/models directory was absent. No runtime/import retry was attempted; installed direct dependency metadata was later collected explicitly.'},
]
report = {
    'schema':'researchos.pi-readiness/1','at':datetime.now(timezone.utc).isoformat(),
    'decision':'METADATA_SOURCE_PREPARATION_ONLY_WAIT_FOR_ROOT_SINGLE_HARNESS_LOOP_AND_SCOPE',
    'source_design_preparation_supported':True,'pi_implementation_exists':False,'implementation_status':'NOT_IMPLEMENTED',
    'native_execution_authorized':False,'resource_ready':False,'model_qualification':'UNVERIFIED','independent_acceptance':False,
    'installed':inventory['package'],
    'installation_metadata':{'package_present':True,'entry_shim_present':True,'bundle_files_pinned':inventory['bundle']['file_count'],'bundle_bytes':inventory['bundle']['bytes'],'direct_dependency_metadata_present':sum(row['present_at_package_dependency_path'] for row in inventory['direct_dependency_metadata']),'direct_dependencies':len(inventory['direct_dependency_metadata']),'registered_public_pin_matches':sum(row.get('registered_pin_matches') is True for row in inventory['sources']),'registered_public_pin_mismatches':0,'missing_package_metadata_blocker_observed':False},
    'help':{'source_observed':True,'cli_help_executed':False,'version_command_executed':False,'reason':'Installed main.js settings/cleanup and runtime/extension loading precede the version/help exits; no zero-side-effect CLI invocation was assumed.'},
    'authentication':{'state':'UNVERIFIED','status_command_documented':True,'status_command_executed':False,'safe_recipe_reference':'acceptance-recipes.json#auth_status_candidate_not_run','credential_output_flags_forbidden':True},
    'license':{'package_declaration':'MIT','readme_declaration':'MIT','top_level_notice_files_found':inventory['root_license_files'],'full_notice_and_transitive_distribution_verified':False},
    'protocol':{'source_documented':'RPC JSONL and JSON event stream','actual_handshake_verified':False,'reusable_draft':'interface-draft.json','acceptance_recipes':'acceptance-recipes.json','distinction':'Installed Pi0.99.2 is distinct from ResearchOS vendor0.87.1 and Lancer SDK1.4.0; multiple models/providers are not multiple Harnesses.'},
    'gaps':gaps,'diagnostic_events':diagnostics,'source_refs':source_refs,
    'ui_freeze02_unchanged':inventory['ui_freeze02'],
    'public_source_and_bundle_readback_verified':True,'user_auth_config_files_read_or_copied':0,'pi_cli_processes_started':0,
    'rpc_sessions_started':0,'qoder_sessions_started':0,'model_or_api_calls':0,'installs':0,'d_source_writes':0,'old_probe_replays':0,
    'formal_increment':0,'product_acceptance_increment':0,'pending_processes':[],
}
(root/'readiness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest = [{'path':path.relative_to(root).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(root.iterdir()) if path.is_file() and path.name != 'EVIDENCE_MANIFEST.json']
(root/'EVIDENCE_MANIFEST.json').write_text(json.dumps({'files':manifest,'file_count':len(manifest),'readiness_sha256':sha(root/'readiness.json'),'public_inputs_readback_verified':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'readiness_sha256':sha(root/'readiness.json'),'manifest_sha256':sha(root/'EVIDENCE_MANIFEST.json'),'files':len(manifest),'public_readback_bad':bad,'pi_processes_started':0}))
