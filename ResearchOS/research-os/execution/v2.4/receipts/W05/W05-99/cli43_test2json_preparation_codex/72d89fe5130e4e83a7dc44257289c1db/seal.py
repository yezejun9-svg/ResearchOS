"""Seal preparation metadata only; no proposed module is imported or executed."""
import ast
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes()
    return {'path':str(Path(p).absolute()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
inputs=json.loads((OUT/'inputs.before.json').read_text(encoding='utf8'))
after=[pin(r['path']) for r in inputs]
if after!=inputs:raise ValueError('Input drift before seal')
for n in ['prepare.py','seal.py','runner.v7.proposed.py','windows_debug_job_tree.diagnostic.proposed.py']:
    ast.parse((OUT/n).read_text(encoding='utf8'),filename=n)
save('inputs.at-seal.json',after)
save('tool-observations.json',{'actual_tools':[
 {'chunk':'d16315','outer_exit':0,'native_exit':None,'kind':'Read original manifest'},
 {'chunk':'981e00','outer_exit':0,'native_exit':None,'kind':'Read helper event/cleanup spans'},
 {'chunk':'c8af07','outer_exit':0,'native_exit':None,'kind':'Read helper capture/process spans'},
 {'chunk':'bf7435','outer_exit':0,'native_exit':None,'kind':'Read runner and failed handoff'},
 {'chunk':'9e4f67','outer_exit':0,'native_exit':None,'kind':'Read failed review and runner'},
 {'chunk':'8fb6db','outer_exit':0,'native_exit':None,'kind':'Read known input manifest and bounded Go source inventory','output_truncated':True,'limitation':'display was unnecessarily broad; source facts use exact copied files, not truncated display'},
 {'chunk':'b7b57f','outer_exit':0,'native_exit':None,'kind':'Read Go tool and test2json source'},
 {'chunk':'6dabf6','outer_exit':0,'native_exit':None,'kind':'Create own exclusive preparation leaf'},
 {'chunk':'74c75f','outer_exit':0,'actual_python_exit':0,'kind':'Run pure source/AST constructor','invocation_ref':pin(OUT/'preparation.invocation.json'),'stdout_ref':pin(OUT/'preparation.stdout.raw'),'stderr_ref':pin(OUT/'preparation.stderr.raw')}
 ],'new_failure_origins':[],'candidate_execution':False,'runtime_native_values_not_inferred':True})
stages=['git-head','git-public-blobs','go-version','go-env','go-list','go-list-test2json','build-test2json',
        'build-cli','build-test','buildinfo-cli','buildinfo-test','buildinfo-test2json','case-00','case-01']
proposal={
 'schema':'researchos.cli43-test2json-controller-preparation.v1','author':'codex:/root/command_queue_impl',
 'status':'PREPARATION_ONLY','execution_authorized':False,'actual_root_scope_ref':None,'actual_grant_ref':None,
 'source_commit':'a510dbef4a7e08fb5c428df44c39b133f3ffa856','source_unique_paths':43,
 'inputs':inputs,'runner_ref':pin(OUT/'runner.v7.proposed.py'),
 'diagnostic_helper_ref':pin(OUT/'windows_debug_job_tree.diagnostic.proposed.py'),
 'originals_unchanged':True,'old_failed_execution_unchanged':True,'counter_reset':False,
 'cause_boundary':{'old_unknown_PID':41296,'old_generation':16,'old_rejected_image_identity':None,
   'old_leaf_started':False,'claim':'Fixed Go source supports implicit builtin-tool compilation as a possible path; this preparation does not identify the old rejected image or establish its cause.'},
 'source_evidence':[
  {'ref':inputs[3],'lines':[100,143,268,282,334,386],
   'fact':'Missing installed tool can load builtin cmd/tool, construct LinkAction and run BuiltTarget; direct explicitly built tool removes this implicit build from cases.'},
  {'ref':inputs[4],'lines':[5,29],
   'fact':'test2json accepts -t/-p then the test executable/flags. Existing -test.v is permissible lower fidelity; preserved exactly rather than changed here.'},
  {'ref':inputs[1],'lines':[298,330,346,370],
   'fact':'Actual hFile path/hash exist before the module/image rejection; the new diagnostic reuses these already observed bytes and the existing process generation/creation identity.'}],
 'exact_changes':[
  'One new controlled go-list -compiled -deps -json -work -x cmd/test2json, same fixed Go; reject any graph error, non-Goroot package, Module metadata, missing/noncanonical/uncatalogued source or ambiguous main.',
  'Fresh export/bin/test2json.exe built with -p=1 -mod=readonly -buildvcs=false -work -x, independent before/after WORK/cache observations; executable ledger pin immediately after successful build.',
  'Final full WORK/cache/importcfg/importcfg.link/archive closure includes all three builds and the new executable; go version -m for tool before the first case.',
  'Use direct pinned test2json executable for both cases with every original -t/-p/test flag and selector byte preserved; add only this fresh artifact to the finite authorized image set.',
  'New helper retains at most one rejected_load_facts entry after actual original hFile hashing, before original module/image/primary mismatch RuntimeError. Rejected facts never enter qualified modules. No new file/API reads, no authorization or cleanup change.'
 ],
 'source_closure':{'new_tool_sources':'Existing frozen selected GoRoot files only, including all present graph fields/ignored/platform source fields; no catalog auto-expansion.',
   'generated':'Full same-round GOTMP/WORK, generated testmain, importcfg/importcfg.link, every archive, fresh cache and all three executables.',
   'failure_artifact':'The tool lives outside .cli43-build, so a separate finally artifact pin records any present partial output without certifying success.',
   'old_executable_reuse':False,'new_module_downloads':False,
   'scope_inputs_requiring_new_Root_pins':['runner_ref','debug_tree_helper_ref','actual full scope hash','runtime/controller source refs','independent review refs','fresh Root registration/grant','fresh output/export/authorization/cache UUIDs'],
   'other_controls_unchanged':['launcher','authorization gate','metadata pipeline','instrumented test/source plan','public compiler image selection','source authority']},
 'ordered_native_stages':stages,'native_calls_full_success':14,'native_calls_cap':16,
 'caps':{'compiler_seconds':600,'list_seconds':240,'case_seconds':510,'test_seconds':480,'inner_soft_seconds':3300,
   'outer_seconds':3600,'cleanup_seconds':5,'compiler_total_processes':2048,'job_active_processes':16,
   'case_processes':16,'images':64,'compiler_images_max':61,'dynamic_image_slots':3,
   'case_count':2,'fixture_dispatch_per_boundary_per_case':32,'HTTP_qualification_observation_limit':128,
   'SDK_Node_model_external_paid':0},
 'time_limit_note':'The stage timeouts are individual upper bounds, not an additive promise to finish under the unchanged 3300-second soft or 3600-second outer deadline. First unexpected failure still stops; no timeout widening or retry.',
 'diagnostic_contract':{'limit':1,'fields':['event_code','image_base','pid','creation_time_100ns','path_from_actual_file_handle','before.sha256','before.bytes','process_generation','expected_pin|null','rejection_reason','qualified_module=false','diagnostic_only=true'],
   'earlier_path_or_hash_failure':'No diagnostic load fact can be manufactured before its actual hash finishes. Original error/nullable process evidence remains; no extra IO attempted.',
   'success_qualification_unchanged':True,'first_unknown_stops':True,'complete_on_failure':False},
 'future_cases':[{'selector':'^TestCLIProtocolInteractiveAuthority$/^'+leaf+'$','status':'NOT_RUN'} for leaf in ['real-existing-open-readonly','real-existing-self-send']],
 'protected':{'business_qualifier_suffix_bytes_identical':True,'all_other_runner_functions_AST_identical':True,
   'whole_original_runner_and_helper_inverse_byte_equal':True,'old_fixture_and_HTTP_assertions_unchanged':True},
 'open_gates':['Non-author source/controller review of these two new receipt candidates.',
   'Root binds actual selected compiler/runtime resources and verifies the cmd/test2json graph uses only already authorized source files; missing selected input stops without fetching.',
   'New explicit actual Root scope/CAS/sealed authority/grant, new cache/exes/output; no reuse of r327 grant or execution.',
   'All compilation, Windows debug runtime evidence, rejection diagnostics, test events, HTTP/closedDB facts and final qualification remain NOT_RUN.'],
 'actual_target_execution':0,'source_acceptance':False,'formal_increment':0,'writer_status':'STOPPED'}
save('proposal.json',proposal)
save('handoff.json',{'schema':'researchos.preparation-handoff.v1','status':'PREPARATION_ONLY_STOPPED',
 'proposal_ref':pin(OUT/'proposal.json'),'runner_ref':pin(OUT/'runner.v7.proposed.py'),
 'diagnostic_helper_ref':pin(OUT/'windows_debug_job_tree.diagnostic.proposed.py'),
 'static_audit_ref':pin(OUT/'static-audit.json'),'exact_inverse_mapping_ref':pin(OUT/'exact-transformations.json'),
 'inputs_before_ref':pin(OUT/'inputs.before.json'),'inputs_after_ref':pin(OUT/'inputs.at-seal.json'),
 'tool_observations_ref':pin(OUT/'tool-observations.json'),'non_author_failed_review_ref':inputs[2],
 'native_calls_full_success':14,'native_calls_cap':16,'actual_target_calls':0,'new_failure_origins':[],
 'source_acceptance':False,'execution_grant':False,'counter_reset':False})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','members':members,'member_count':len(members),'excluded_only_self':True})
print(json.dumps({'handoff':pin(OUT/'handoff.json'),'manifest':pin(OUT/'manifest.json'),'proposal':pin(OUT/'proposal.json'),'members':len(members)},ensure_ascii=False))
