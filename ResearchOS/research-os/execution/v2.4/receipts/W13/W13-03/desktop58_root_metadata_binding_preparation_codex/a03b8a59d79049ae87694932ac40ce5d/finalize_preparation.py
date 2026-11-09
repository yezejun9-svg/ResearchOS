"""Pure IO/AST audit and immutable source-preparation documentation. No candidate import."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
P13=ROOT/'execution/v2.4/receipts/W13/W13-03'
BASE=P13/'fresh58_cli2_root_metadata_preparation_codex/900837a405be433f83524eddcc1c6bd8'
def ref(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def save(name,data):
    raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f:f.write(raw)
    return ref(OUT/name)
inputs=read(OUT/'inputs.before.json')+read(OUT/'additional-inputs.json')
extra=[BASE/'build_binding.current58.proposed.py',
 P13/'desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060/build-metadata-templates.py',
 P13/'desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060/metadata-engine.template.py',
 P13/'desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf/prepare-resource-correction.v2.py',
 P13/'fresh58_desktop169_go3_revision_preparation_codex/736e757cdbc148a286c1d2426b8a7382/desktop_controller.v3.proposed.py']
inputs += [ref(p) for p in extra]
unique={}
for row in inputs:
    key=str(Path(row['path']).resolve())
    current=ref(Path(row['path']))
    assert current['sha256']==row['sha256'] and current['bytes']==row['bytes'],key
    if key in unique:assert unique[key]['sha256']==row['sha256']
    unique[key]=row
save('inputs.final.json',{'entries':list(unique.values()),'count':len(unique),'drift_count':0,'resource_files_rehashed':False})
module=OUT/'metadata_pipeline.desktop58.proposed.py'
old=(BASE/'metadata_pipeline.current58.proposed.py').read_bytes()
new=module.read_bytes()
inverse=read(OUT/'pipeline.inverse.json')
text=new.decode()
for edit in reversed(inverse['edits']):
    if edit['after']:
        assert text.count(edit['after'])==1
        text=text.replace(edit['after'],edit['before'])
    else:
        anchor="    save(root/'preflight-copy-map.json'"
        assert text.count(anchor)==1
        text=text.replace(anchor,edit['before']+anchor)
assert text.encode()==old
wrappers=[]
for name in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py'):
    oldtext=(BASE/name).read_text(encoding='utf-8')
    newtext=(OUT/name).read_text(encoding='utf-8')
    reverted=newtext.replace(repr(str(module)),repr(str(BASE/'metadata_pipeline.current58.proposed.py'))).replace(ref(module)['sha256'],hashlib.sha256(old).hexdigest())
    assert reverted==oldtext,name
    wrappers.append({'selected':ref(OUT/name),'baseline':ref(BASE/name),'inverse_equal':True,'changes':['metadata module path','metadata module SHA256']})
save('wrapper-inverse.json',wrappers)
ast_rows=[]
for path in sorted(OUT.glob('*.py')):
    tree=ast.parse(path.read_bytes(),filename=str(path))
    ast_rows.append({'ref':ref(path),'syntax':'AST_PARSE_ONLY','top_level_definitions':[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]})
controller=extra[-1].read_text(encoding='utf-8')
lines=controller.splitlines()
builder_excerpt=[{'line':i+1,'text':line} for i,line in enumerate(lines) if 148<=i+1<=166]
assert "176" in controller
save('controller-operation-source-excerpt.json',{'source_ref':ref(extra[-1]),'lines':builder_excerpt,'target_executed':False})
contract={
 'schema':'researchos.desktop58-root-metadata-source-preparation-contract.v1',
 'owner':'codex:/root/command_queue_impl','state':'SOURCE_PREPARATION_ONLY_PENDING_NONAUTHOR_REVIEW',
 'source_commit':'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7',
 'product_source_writes':0,'canonical_writes':0,'candidate_imports':0,'native_target_calls':0,
 'actual_scope':None,'actual_registration':None,'actual_grant':None,
 'source_lineage':{'pipeline':ref(BASE/'metadata_pipeline.current58.proposed.py'),'builder':ref(BASE/'build_binding.current58.proposed.py'),
   'reuse':'Existing current58 CLI metadata two-file CAS/run/seal/preflight algorithm. No second registration framework.',
   'old_Desktop_source_import_producer':'Read as provenance only: source-import permission/materialization cannot authorize Node169/Go3 execution.'},
 'writes_proposed':{'checkpoint_WIP':['desktop58_finite_validation_scope_ref','desktop58_finite_validation_current_source_authority_ref','desktop58_finite_validation_controller_review_ref','desktop58_finite_validation_CLI2_qualification_ref','desktop58_finite_validation_state'],
   'ownership_path':'card_path_bindings.W13-03.subtasks.desktop58_finite_validation',
   'lease_state':'REGISTERED_PENDING_ONCE_EXECUTION','source_writer':None,'Root_adoption_required':True,
   'preserved':'All prior failure payloads plus explicit caller origin cut; ST/CM original bytes; all unrelated CP/OW fields. No source/formal acceptance.'},
 'phase_interface':{'scope_builder':'--binding-ref --output --scope-template-ref','prepare':'--binding-ref --output --scope-ref','register':'--binding-ref --output --review-ref','run':'--binding-ref --output --review-ref','seal':'--binding-ref --output','grant_preflight':'--binding-ref --output --scope-ref'},
 'review_contracts':{'controller':{'schema':'researchos.desktop58-controller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE','pins':['scope_sha256','controller_sha256','launcher_sha256','gate_sha256']},
   'registration':{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','pins':['register_sha256','wrapper_sha256','prepared_refs_sha256','audit_sha256'],'original_four_copy_binding':True}},
 'authority_flow':read(OUT/'binding-interface.json')['cycle_free_order'],
 'observations':[
   {'stage':'admission.runtime','producer':'git_guard(b,pf,admission) -> runtime before first head/status/index checks','timing':'Before authorization leaf exists; all files verified before module observation','copied_path':'<new_authorization_root>/admission.runtime.json'},
   {'stage':'grant-final.runtime','producer':'git_guard(b,pf,grant-final) -> runtime before second head/status/index checks','timing':'After actual admission and authorization leaf creation; before final Git guards','copied_path':'<new_authorization_root>/grant-final.runtime.json'},
   {'stage':'grant-final.runtime.after','producer':'explicit runtime(b,pf,grant-final.runtime.after)','timing':'After final Git head/status/index; before live-four immediate pre-grant guard','copied_path':'<new_authorization_root>/grant-final.runtime.after.json'}],
 'observation_rules':{'scope_freezes':'Nonempty exact ordered absolute paths and stage names, no prospective SHA256.',
   'grant_freezes':'Only actual observed raw bytes copied unchanged from own preflight to auth; ordered actual SHA256/bytes refs in both prelaunch and grant.',
   'count_basis':'Three real calls in reused producer; not inferred from an arbitrary required count.',
   'semantics':'Python files/cached files/loaded DLL observation is point-in-time only; no all-lifecycle proof.',
   'canonical_timing':'First actual four snapshots, sealed authority and Git before auth creation; repeated authority and final Git afterwards; immediate live four comparison before grant.',
   'immutable_chain':'Original preflight fact paths retained inside records; original/copy map preserves bytes; separate complete preflight/auth manifests.'},
 'finite_lanes':{'Node':169,'Node_components':'162 HTTP/wire + 7 original regressions','Go_top_units':3,'Go_native_processes':1,
   'controller_native_top_cap':176,'top_accounting':{'git_head':1,'export':1,'builder':1,'buildinfo':3,'Go_lane':1,'Node':169},
   'builder_internal_commands':9,'builder_note':'Nested builder commands remain descendants, separately evidenced; not extra Node cases.',
   'HTTP_cap':390,'offscreen_renderer_controls':2,'visible_installed_GUI':0,'SDK_model_external_paid':0,
   'alias_roots':20,'image_launch_aliases':15,'aliases_precreated':False,
   'timing_values':'All Root inner/outer/builder and evidence reserves NULL until explicit allocation; adapter enforces normal25+cleanup5+evidence reserve relationship.'},
 'runtime_resource_contract':{'actual_resource_catalog':None,'runtime_resources_ref':None,'compiler_resources_ref':None,
   'requirements':'Actual physical public Go/module/tool/Node/Electron/web/OS rows and current staged builder/module/six wrappers/utility/controller code, all exact path/SHA/bytes.',
   'old_counts_are_not_current_coverage':True,'old_metadata8_overlay_inherited':False,
   'staging_script':'resource_catalog.proposed.py selects verified provenance rows; complete_public_roots_frozen remains False and adapter rejects it as execution catalog.',
   'Root_remaining':'Root must establish complete current relevant public roots and OS/Node/Electron support, freeze actual catalog and new metadata overlay, get independent review, then provide literal refs.'},
 'known_current_CLI2':read(OUT/'current58-CLI2-reference-provenance.json'),
 'unchanged_targets':['Desktop controller','Desktop launcher','authority adapter','owned Job helper','debug future-image helper','169 original Node assertions','3 original Go units','HTTP observer/evaluator','negative alias instrumentation'],
 'OPEN':['Root actual resource coverage/current metadata overlay','Root future tuple/cut/original four and status refs','Root new UUID/directories and stage paths','Root actual numeric budgets and evidence reserves','Whole bound controller scope nonauthor review','Actual registration draft review/CAS/seal','Actual admission/runtime observations and grant','Fresh build/Go3/Node169/offscreen2 evidence and independent qualification'],
 'actual_future_execution':'NOT_RUN','self_acceptance':False}
save('contract.json',contract)
save('static-audit.json',{'schema':'researchos.desktop58-metadata-preparation-static-audit.v1','pipeline_whole_inverse':True,
 'pipeline_edit_count':len(inverse['edits']),'unchanged_definitions':read(OUT/'definition-audit.json')['unchanged_AST_definitions'],
 'wrapper_inverse_count':6,'AST_files':ast_rows,'input_count':len(unique),'input_drift':0,
 'CLI2_provenance_keys':read(OUT/'current58-CLI2-reference-provenance.json')['schema_check_only'],
 'new_framework':False,'resource_catalog_ready':False,'candidate_imported':False,'candidate_executed':False,
 'future_negative_controls':'NOT_RUN: missing qualification, old a510, stale metadata overlay, empty/foreign/duplicate observation paths, scope/review cycle, unregistered lease, changed four originals, substituted manifest, incomplete resource roots.'})
selected=[ref(OUT/n) for n in ['metadata_pipeline.desktop58.proposed.py','build_binding.desktop58.proposed.py','resource_catalog.proposed.py','scope.desktop58.template.json']]
selected += [ref(OUT/n) for n in ('scope_builder.py','prepare.py','register.py','run.py','seal.py','grant_preflight.py')]
save('handoff.json',{'schema':'researchos.desktop58-root-metadata-preparation-handoff.v1','owner':'codex:/root/command_queue_impl',
 'state':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','selected_sources':selected,
 'contract_ref':ref(OUT/'contract.json'),'static_audit_ref':ref(OUT/'static-audit.json'),'inputs_ref':ref(OUT/'inputs.final.json'),
 'inverse_refs':[ref(OUT/n) for n in ('pipeline.inverse.json','builder.inverse.json','wrapper-inverse.json')],
 'actual_target_calls':0,'actual_canonical_writes':0,'actual_current58_qualification_reexecuted':False,
 'resource_catalog_complete':False,'future_actual_Root_scope_grant':None,'source_acceptance':False,'formal_increment':0,
 'new_failure_origins':[],'Root_next':'Independent source/ABI review, then actual Root resource coverage and bound scope, independent full-scope and registration review before any metadata or target execution.',
 'manifest_filename':'manifest.json','writer_status':'STOPPED_AFTER_SEAL'})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'contract':ref(OUT/'contract.json'),'audit':ref(OUT/'static-audit.json'),'selected_sources':selected,'target_calls':0},ensure_ascii=False))
