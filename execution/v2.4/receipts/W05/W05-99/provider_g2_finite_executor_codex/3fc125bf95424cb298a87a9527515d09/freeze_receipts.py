from pathlib import Path
import hashlib,json,subprocess,datetime
N=Path(__file__).resolve().parent;W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
F=N/'final-audit-97b53059b7284a5294781a90f7ab64a1'
B=N/'build-e98a85f6a8fe4e69a1b2939a55ec68ef';R=N/'run-c62cac438c834dc794a35231bd688818'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(W)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,v):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert commit=='8d0921b7c42ecd40300c58192d54af1064947aed'
paths=subprocess.check_output(['git','diff','--name-only','6fb5263681c17f0e50920c354dc07ed440a23714',commit],text=True).splitlines()
assert sorted(paths)==sorted(['internal/domain/runtime_provider_binding_windows_test.go','internal/domain/runtime_coordinator_windows_test.go'])
sources=[]
for rel in paths:
 blob=subprocess.check_output(['git','show',commit+':'+rel]);p=W/rel;assert blob==p.read_bytes()
 sources.append(dict(ref(p),git_blob_id=subprocess.check_output(['git','rev-parse',commit+':'+rel],text=True).strip()))
save(F/'committed-source.json',{'commit':commit,'base':'6fb5263681c17f0e50920c354dc07ed440a23714','source':sources,'current_source_writer':'STOPPED'})
stages=[]
for p in R.rglob('native-stages-and-fault.json'):stages.append({'ref':ref(p),'actual':json.loads(p.read_text(encoding='utf-8'))})
save(F/'actual-native-stage-index.json',stages)
save(F/'handoff.json',{
 'schema':'researchos.w05.provider-g2-finite-handoff.v1','status':'EXECUTION_REPORTED_PENDING_NONAUTHOR_REVIEW','executor':'codex:/root/sources_parent_impl',
 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':commit,'base_commit':'6fb5263681c17f0e50920c354dc07ed440a23714','current_source_writer':'STOPPED',
 'scope':ref(N/'scope.original.json'),'source':ref(F/'committed-source.json'),'case_matrix':ref(F/'case-matrix.json'),'audit':ref(F/'audit-summary.json'),
 'closed_databases':ref(F/'closed-db-audit.json'),'actual_http_counts':ref(F/'actual-http-counts.json'),'native_stage_index':ref(F/'actual-native-stage-index.json'),'protected_functions':ref(F/'protected-functions.json'),
 'failures':ref(F/'failure-origins.json'),'build':ref(B/'build-result.json'),'build_argv':ref(B/'test-build.invocation.json'),'build_raw':ref(B/'test-build.stderr'),
 'source_compiler_sdk_inputs_before':ref(B/'inputs.before.json'),'source_compiler_sdk_inputs_after':ref(B/'inputs.after.json'),'compiler_generated':ref(B/'generated.json'),'compiler_archives':ref(B/'archives.before.json'),
 'testexe':ref(B/'domain.g2.test.exe'),'run':ref(R/'handoff.json'),'run_inputs_before':ref(R/'inputs.before.json'),'component_after_native_before':ref(R/'component.after.native.before.json'),'run_inputs_after':ref(R/'inputs.after.json'),
 'counts':{'exact_component_leaf':18,'exact_native_leaf':11,'native_exit_zero':29,'leaf_pass':29,'leaf_fail':0,'skip':0,'model_loopback_http':4,'external_http':0,'paid':0,'fixture_sqlite_snapshots':13,'pure_tool_nonzero_origins':3},
 'limits':['No qualification or whole-provider acceptance','No G1/G3/G4/G5/G6 or held history tests executed','Native quarantine preserves UNKNOWN and UPPER_BOUND reservation; does not assert zero ACTUAL cost','SDK bundle is the already locked readonly 497e111b artifact, not rebuilt or modified','Original protected contextFixture bootstrap request count remains explicitly NOT_INSTRUMENTED; subsequent setup/local API/readiness/MODEL actual counters are separate','Initial build d486 remains development-only; acceptance evidence uses e98 and one 29-leaf cohort c62 only'],
 'formal_acceptance_delta':0
})
files=[ref(p) for p in sorted(N.rglob('*')) if p.is_file() and p not in [F/'manifest.json',F/'index.json']]
save(F/'manifest.json',{'root':str(N.relative_to(W)).replace('\\','/'),'entries':files,'listed_count':len(files),'excludes':['manifest.json','index.json']})
save(F/'index.json',{'handoff':ref(F/'handoff.json'),'manifest':ref(F/'manifest.json'),'listed_count':len(files),'source_commit':commit,'self_signed_acceptance':False})
print(json.dumps(json.loads((F/'index.json').read_text(encoding='utf-8')),ensure_ascii=False))
