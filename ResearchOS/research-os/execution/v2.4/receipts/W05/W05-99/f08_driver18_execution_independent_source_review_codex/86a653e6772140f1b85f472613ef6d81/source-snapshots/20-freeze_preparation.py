"""Pure IO/hash/AST only. Does not import any proposed controller or helper."""
import ast
import hashlib
import json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99'
F=BASE/'f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0'
A=BASE/'f08_sqlite_driver18_validation_preparation_codex/a84ef66a214346e4891e569c55bc6d9b'
REV=BASE/'f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af'
U=BASE/'cli43_compiler_parallelism_preparation_codex/8ac0acd36c6047beaab455730692d078/runner.v6.proposed.py'
H=ROOT/'execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0/windows_debug_job_tree.py'
N=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
def pin(p):
    raw=Path(p).read_bytes();return {'path':str(Path(p).absolute()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def need(v,msg):
    if not v:raise ValueError(msg)
names={'fork_handoff_ref':F/'handoff.json','consumer_contract_ref':F/'consumer-and-driver-validation.contract.proposed.json',
 'fork_lock_ref':F/'fork.file-lock.json','original_lock_ref':F/'module.before.json',
 'test_source_ref':A/'innocuous_test.go.proposed.txt','surface_ref':A/'consumer_surface.go.proposed.txt',
 'producer_ref':A/'i16_fixture_main.go.proposed.txt','probe_ref':A/'i16_old_probe_main.go.proposed.txt',
 'consumer_mod_ref':A/'consumer.go.mod.proposed.txt','old_mod_ref':A/'old_probe.go.mod.proposed.txt',
 'sum_ref':A/'consumer.go.sum.proposed.txt','source_handoff_ref':A/'handoff.json',
 'non_author_handoff_ref':REV/'handoff.json','non_author_review_ref':REV/'REVIEW.md',
 'original_regression_ref':F/'module/modernc_sqlite_v1_60_1_researchos_innocuous/func_test.go',
 'fork_mod_ref':F/'module/modernc_sqlite_v1_60_1_researchos_innocuous/go.mod',
 'fork_sum_ref':F/'module/modernc_sqlite_v1_60_1_researchos_innocuous/go.sum'}
fixed={k:pin(v) for k,v in names.items()}
need(fixed['consumer_contract_ref']['sha256']=='bfad5ca07ab7a878e34a1df000d58e96eb74c2411dec9e773dc6b3d80adcf2e6','consumer contract')
need(fixed['test_source_ref']['sha256']=='5df920564f6213954e9202895a69001f42debb056ac264b652e0afe743171e50','test source')
need(fixed['original_regression_ref']['sha256']=='85e63e33c8d22d89e426dd33dff7bfece1f472b4796cd067718d9a6d22fb4e54','full original I18')
utility=pin(U);debug=pin(H);normal=pin(N)
need(utility['sha256']=='333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea','utility')
need(debug['sha256']=='8368debd47b8a1df7e4b8c6f11d28abdd7df49d8683ac755134d3877ca818e27','debug helper')
need(normal['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad','owned helper')
inputs=list(fixed.values())+[utility,debug,normal]
save('inputs.before.json',inputs);save('fixed-inputs.json',fixed)
for i,p in enumerate(names.values()):
    if p.stat().st_size<100000:
        with (OUT/(str(i)+'-'+p.name+'.input.txt')).open('xb') as f:f.write(p.read_bytes())
controllers=['driver18_controller.proposed.py','launch.proposed.py']
trees={n:ast.parse((OUT/n).read_text(encoding='utf8'),filename=n) for n in controllers}
ast.parse(Path(__file__).read_text(encoding='utf8'),filename='freeze_preparation.py')
caps={'native_calls':32,'compiler_seconds':600,'test_seconds':750,'inner_seconds':3300,'outer_seconds':3600,
 'cleanup_seconds':5,'images':64,'compiler_processes':2048,'job_active_processes':16,'fixture_HTTP':0,'SDK_Node_model_external_paid':0}
scope={'schema':'researchos.driver18-root-finite-scope.proposed.v1','preparation_only':True,'actual_Root_registration':None,
 'actual_origin_cut':None,'actual_non_author_controller_review_ref':None,'authority_validator_ref':None,
 'resource_catalog_ref':None,'prepared_ref':None,'mode':None,'ordered_cases':None,'public_environment':None,
 'work_root':None,'prepare_output_root':None,'execute_output_root':None,'prepare_launcher_output_root':None,
 'execute_launcher_output_root':None,'fixed_inputs_ref':pin(OUT/'fixed-inputs.json'),
 'controller_ref':pin(OUT/controllers[0]),'launcher_ref':pin(OUT/controllers[1]),'utility_ref':utility,
 'owned_helper_ref':normal,'debug_helper_ref':debug,'caps':caps,'source_acceptance':False}
save('scope.UNBOUND.proposed.json',scope)
ops=['go-version','graph-fork','graph-consumer','graph-old','build-fork-test','build-consumer-surface','build-i16-producer','build-i16-old',
 'buildinfo-test','buildinfo-producer','buildinfo-old']+['case-I'+str(i).zfill(2) for i in range(1,16)]+['I16-produce','I16-old-probe','case-I16','case-I18']
need(len(ops)==30,'native total')
save('finite-operation-roster.json',{'partial17_native_calls':len(ops),'native_cap':32,'ordered_calls':ops,
 'future_full18_arithmetic_only':31,'full18_current_controller_supported':False,
 'reason':'Real reviewed callback/name/vector adapter absent. A future full18 mode needs separately reviewed source binding; current executable mode only explicit partial17.',
 'prepare_phase_Go_calls':0,'all18':'NOT_RUN','I17':'FATAL_OPEN_OR_EXPLICIT_NOT_AUTHORIZED','caps':caps,
 'budget_authority':'Root new task message explicitly chose these proposed caps; original consumer contract had no numeric execution lease.'})
save('resource-and-authority-contract.json',{
 'status':'UNBOUND_NOT_EXECUTABLE','resource_catalog_ref':None,'actual_dependency_graph':None,'fresh_compiler_executables':None,
 'resource_catalog_shape':{'files':'exact absolute path/sha256/bytes list: actual Python __file__ + __cached__ + loaded OS point-in-time files, controls, fixed Go compiler tools, full GoRoot sources and every selected offline transitive dependency input',
 'python':'exact path/sha/bytes','go':'exact pinned Go1.27.1 path/sha/bytes','GOROOT':'actual fixed path',
 'compiler_images':'finite pinned images, max61 static plus 3 new exe; unknown immediately rejects',
 'offline_modcache_copies':'list {relative_path,ref}; all refs must be in files; no overwrite. Root must include download .mod/.info/.ziphash and required public dependency source files; no network fallback.'},
 'source_module_prefixes':{'fork':1899,'pristine_old':1899,'only_existing_fork_driver_change':'sqlite.go',
 'own_copy_delta':'one new driver18_innocuous_test.go in copied fork; all original func_test.go bytes preserved',
 'consumer_replace':'modernc.org/sqlite v1.60.1 => ../fork','old_probe_replace':'NONE; actual module must be v1.60.1 at new isolated modcache'},
 'direct_dependencies_from_actual_go_mod':{'github.com/google/pprof':'v0.0.0-20260802141513-ef3492d7dac3','golang.org/x/sys':'v0.48.0','modernc.org/fileutil':'v1.4.0','modernc.org/libc':'v1.77.1','modernc.org/mathutil':'v1.7.1'},
 'indirect_dependencies_from_actual_go_mod':{'github.com/dustin/go-humanize':'v1.0.1','github.com/google/uuid':'v1.6.0','github.com/mattn/go-isatty':'v0.0.24','github.com/ncruces/go-strftime':'v1.0.0','github.com/remyoudompheng/bigfft':'v0.0.0-20230129092748-24d4a6f8daec','modernc.org/memory':'v1.12.1'},
 'dependency_closure_limit':'Declared versions are source facts, not evidence all transitive files are locally present or actual selected. Root must inventory offline copies; actual Go graph refuses an uncatalogued file. No dependency installs or downloads in this preparation.',
 'root_gate_interface':'validate_grant(scope_path, scope_sha, grant_path, grant_sha) returns scope, phase, actor=codex:/root, actual_registration_completed=true, authorization_input_refs',
 'root_gate_required_checks':['Actual explicit phase grant and once-only fresh leaf scope, original Root registration native result and sealed audit/manifest membership.',
 'All four immutable canonical copies and exact CP/OW/failure tuple bound to actual CAS intent desired; no inferred live tuple and no self-attested authorized boolean.',
 'Actual independent controller review binds complete scope/launcher/controller/helper/utility hashes and partial17 decision; excludes candidate author.',
 'All consumed immutable chain refs returned for ledger freeze; source resources/build dependencies and actual prepared.json/hash/prepare completion/manifest bound by execute grant.',
 'Unique prepare then unique execute grants; prepare success is not execution authorization; no stale UUID/cache/binary reuse or retry.',
 'Actual Python flags -I -S -X utf8 and OS/module raw inputs; point-in-time inventory is not whole-life Python provenance.'],
 'gate_implementation':'OPEN: reuse Root reviewed metadata/authority binding machinery through a separately reviewed driver18-specific adapter. This package does not implement a permissive generic grant or mint grants.',
 'canonical_writes':0,'source_adoption':False,'SQL24_permission':False})
save('I16-provenance-contract.json',{'status':'NOT_RUN','phases':[
 {'id':1,'program':'fresh fork-linked producer','evidence':'actual graph selected fork dir/qualified replace, build WORK/archive/buildinfo/exe, owned native/creation/job closure; report phase_only_not_case_pass; original closed DB no sidecars, exclusive closed copy+SHA'},
 {'id':2,'program':'fresh pristine-driver probe in separate process/module, no replace/no UDF registration',
  'evidence':'actual selected original v1.60.1 Dir+Module, separate exe buildinfo/job/native; report file byte/object agrees with actual captured stdout; original program checks exact schema, missing function cause code1, before/after count1; closed file byte equality before/after old stage mandatory; reject any drift, not normalize it'},
 {'id':3,'program':'fresh fork testexe exact TestDriverI16','evidence':'original source confirms count1/x7, actual insert9/count2; actual test PASS and native/job proof plus closed sidecars absence and final separate copy required'}],
 'no_ABI_coexistence':True,'no_unmanaged_test_children':True,'report_alone_not_authority':True,
 'separate_full_SQL_schema_column_typeof_rowid_scan':False,
 'limit':'Closed pre/post identical bytes prove original schema/rows unchanged during old phase. This does not claim an independently executed SQL inventory. If reviewers require that distinct observation, add separately authorized source/inspector; do not assert it exists.',
 'I18_original_body_ref':fixed['original_regression_ref'],'I18_original_timing':'two original1000x200ms loops approx400 seconds plus original remaining work; all untouched; Root chose750 seconds per test, within3300/3600 overall',
 'I17':'No actual binding. Full18 request fails before cases; explicit independently authorized partial17 omits selector and reports OPEN_NOT_AUTHORIZED, never SKIP or all18 PASS.'})
save('static-checks.json',{'Python_AST_files':3,'candidate_import_or_execution':False,
 'actual_Go_gofmt_SQL_Node_SDK_HTTP_model_DLL':0,'go_candidate_bytes_unchanged':True,
 'original_test_body_preserved':True,'source_overlays_only_future_fresh_copy':True,
 'forward_inverse_method':'All eight future source mapping operations copy exact verified bytes without text rewriting. Deleting only the added test yields exact1899 original fork prefix; consumers keep original go.mod/sum/test bytes. This preparation does not materialize the copy or claim runtime proof.',
 'new_controller':'new glue around pinned333 utility functions and pinned6a4/8368; those entire source files are referenced unchanged, not edited',
 'fixed_native_graph_calls':30,'cap':32,'I17_is_open':True,'all_actual_case_states':'NOT_RUN'})
after=[pin(r['path']) for r in inputs];need(after==inputs,'input drift');save('inputs.after.json',after)
print(json.dumps({'scope':pin(OUT/'scope.UNBOUND.proposed.json'),'controller':pin(OUT/controllers[0]),'launcher':pin(OUT/controllers[1]),'input_count':len(inputs),'drift':0},ensure_ascii=False))
