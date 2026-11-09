from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent

def ref(p):
    raw=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def emit(name,value):
    p=OUT/name;p.write_bytes(json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')+b'\n');return ref(p)
def read(name):return json.loads((OUT/name).read_bytes())

audit=read('static-byte-audit.json')
assert audit['status']=='STATIC_CHECKED_SOURCE_PREPARATION_ONLY'
assert audit['pretransition_frame_count']==100 and audit['vector_count']==109
before=read('inputs.before.json');after=[]
for r in before:
    current=ref(Path(r['path']));assert current==r;after.append(current)
assert after==read('inputs.after.json')

source_input=next(r for r in before if r['path'].endswith('/01-client_cancel_finalization.v3.go.proposed.txt'))
producer_input=next(r for r in before if r['path'].endswith('/02-client_cancel_finalization_test.v3.go.proposed.txt'))
driver_input=next(r for r in before if r['path'].endswith('/00-innocuous_test.go.proposed.txt'))
mapping_input=next(r for r in before if r['path'].endswith('/mapping.json'))
fork_input=next(r for r in before if r['path'].endswith('/modernc_sqlite_v1_60_1_researchos_innocuous/sqlite.go'))
group=emit('source-group.json',{
 'schema':'researchos.f08.i17.binding-source-group.v1',
 'status':'PROPOSED_NOT_ADOPTED_NOT_RUN',
 'production_callback':{'before':source_input,'after':source_input,'whole_bytes_unchanged':True,'target':'internal/domain/client_cancel_finalization.go'},
 'producer_tests':{'before':producer_input,'after':ref(OUT/'client_cancel_finalization_test.v4.go.proposed.txt'),'target':'internal/domain/client_cancel_finalization_test.go'},
 'domain_harness':{'before':'ABSENT','after':ref(OUT/'client_cancel_finalization_i17_integration_test.go.proposed.txt'),'target':'internal/domain/client_cancel_finalization_i17_integration_test.go'},
 'driver_test_contract':{'before':driver_input,'after':ref(OUT/'innocuous_test.go.proposed.txt'),'target':'Root separately owned future fork innocuous_test.go','original_controller':'UNCHANGED','I17_original_adapter':'still nil FATAL_OPEN'},
 'driver_source':{'before':fork_input,'after':fork_input,'whole_bytes_unchanged':True},
 'raw_vectors':ref(OUT/'vector-manifest.json'),
 'raw_sequences':ref(OUT/'raw-sequences.json'),
 'raw_provenance':ref(OUT/'fixture-provenance.json'),
 'raw_digest_controls':ref(OUT/'raw-digest-controls.json'),
 'original_DDL34':ref(OUT/'v5-candidate.sql.unchanged.txt'),
 'target_path_mutations_here':False,
 'public_exports_added':False,'circular_import_added':False,'fake_or_all_error_callbacks_added':False,
 'requires_independent_current_source_review':True})
selector=emit('future-selectors.json',{
 'schema':'researchos.f08.i17.future-selectors.v1','status':'ALL_NOT_RUN_UNBOUND',
 'module':'researchos.local/research-os','target_package':'internal/domain','root_worktree':None,
 'selectors':[
  {'selector':'TestF08I17ProducerFreeze','purpose':'genuine Go data producer exact bytes equal independent frozen frames; before SUT','process':'fresh Root-owned controlled Go process','actual_go_module_closure':None},
  {'selector':'TestF08I17DomainBindings','purpose':'private actual factory plus genuine init real3 registrations with trusted_schemaOFF and callback error contract','process':'separate fresh Root-owned controlled Go process after producer equality','actual_go_module_closure':None},
  {'selector':'TestDriverI17','module':'modernc.org/sqlite','status':'FATAL_OPEN_UNBOUND_PRIVATE_PACKAGE_ADAPTER','old_partial_controller':'unchanged; needs Root approved route split'},
  {'selector':None,'status':'FATAL_OPEN_NOT_IMPLEMENTED','purpose':'actual v5 34source view/trigger same-transaction capture and storage types before cast; no invented alias'}],
 'resource_environment':'F08_I17_RESOURCE_APPROVAL','resource_schema':'researchos.f08.i17.root-resource.v1','unconfigured_resource':ref(OUT/'root-resource.proposed.json'),
 'external_owner_lease_go_mod_replace_Job_and_close_proofs_required':True})
remaining=[
 'Independent current source/vector approval and genuine Go producer byte comparison',
 'Actual fresh driver/source/module/transitive compile and dynamic purity closure',
 'Actual v5 source view order, typeof-before-CAST, native exact raw pertransition captures',
 'Actual same-transaction DDL parent/member/pin/solejournal/control closure and SQL24/22-23 migration rollback',
 'Initial auth_principals/auth_grants/current ownerRoot/executor/effective-clock/profile authority',
 'Mode3 authentic caller contract',
 'Later-epoch saved operation producer binding',
 'Ordinary native/SDK final authority and complete historical/backup proofs',
 'Legal >1MiB complete solejournal completion/replay']
scope=emit('scope-and-open.json',{
 'schema':'researchos.f08.i17.binding-scope.v1','I17_status':'FATAL_OPEN_FULL_BINDING_NOT_PROVEN',
 'static_issues':{'I17-M01':'error expectation prepared; future actual SQLite primary1 verification remains','I17-M02':'domain-owned private factory/real registration harness prepared; module/resource route unbound','I17-M03':'independent raw source-data reconstruction and freeze-before-SUT candidates prepared; native producer equality/native DDL capture pending'},
 'remaining_FATAL_OPEN':remaining,
 'source_acceptance':False,'formal_acceptance':False,'three_callbacks_complete':False,'SQL24_adoption_allowed':False,
 'formal_increment':0,'candidate_execution_count':0,'model_HTTP_SDK_native_driver_SQL_Go_calls':0,
 'all_expected_good_values':'SOURCE_INFERENCE_NOT_RUN','SQLitePrimaryError1':'SOURCE_INFERENCE_NOT_RUN',
 'mutations':{'owned_receipt_only':True,'Main':False,'canonical':False,'cache_module':False,'old_sealed_receipts':False,'old_partial17_controller':False,'failure_counters':False},
 'old_fd09_cleanup':'autoreview rejection and files preserved; no delete attempted',
 'new_failure_origins':[ref(OUT/'original-parser-failure.json')],
 'old_mapping_origins':'preserved via selected mapping handoff; not recounted or retried',
 'actual_native_observations':[ref(OUT/'prepare.native-observation.json'),ref(OUT/'audit.native-observation.json')],
 'original_tool_observations':[ref(OUT/'original-tool-observations.json'),ref(OUT/'supplement-tool-observations.json')]})
emit('ownership.closed.json',{'schema':'researchos.source-preparation.ownership-close.v1','lease_id':OUT.name,'actor':'codex:/root/f08_i17_binding_impl','writer_status':'STOPPED_AFTER_SEAL','owned_root':OUT.as_posix(),'outside_namespace_mutations':False,'source_adoption':False,'formal_acceptance':False})
handoff=emit('handoff.json',{
 'schema':'researchos.f08.i17.binding-revision-preparation.handoff.v1','actor':'codex:/root/f08_i17_binding_impl',
 'writer_status':'STOPPED_AFTER_SEAL','status':'SEALED_SOURCE_PREPARATION_NOT_ADOPTED_NOT_RUN',
 'self_acceptance':False,'independent_non_author_review':'REQUIRED_NOT_YET_DONE',
 'mapping_input':mapping_input,'source_group_ref':group,'selector_ref':selector,'scope_open_ref':scope,
 'changes_ref':ref(OUT/'changes.json'),'new_harness_change':audit['new_harness_change'],
 'static_byte_audit_ref':ref(OUT/'static-byte-audit.json'),'raw_vectors_ref':ref(OUT/'vector-manifest.json'),
 'raw_sequences_ref':ref(OUT/'raw-sequences.json'),'provenance_ref':ref(OUT/'fixture-provenance.json'),
 'vector_count':109,'pretransition_frames':100,'sequence_frames':[24,24,26,26],
 'v3_Test_bodies_unchanged':28,'other_driver_Test_bodies_unchanged':17,
 'whole_forward_inverse_bytes_exact':True,'original_DDL34_unchanged':True,
 'inputs_before_ref':ref(OUT/'inputs.before.json'),'inputs_after_ref':ref(OUT/'inputs.after.json'),'input_count':46,
 'actual_python_preparation_exit':read('prepare.native-observation.json')['native_exit'],
 'actual_python_static_audit_exit':read('audit.native-observation.json')['native_exit'],
 'Go_AST_compile_gofmt_SQL_native_SDK_HTTP_model_runs':0,
 'new_parser_origin_outer_exit':1,'new_parser_origin_native_exit':None,'new_failure_origins':[ref(OUT/'original-parser-failure.json')],
 'I17_full_binding':'FATAL_OPEN','remaining_FATAL_OPEN':remaining,
 'source_acceptance':False,'driver_adopted':False,'SQL24_adoption_allowed':False,'formal_increment':0,
 'Main_cache_canonical_module_old_receipt_counter_writes':0,
 'root_next':'Independent read-only source/vector review, then separately Root-owned source/resource lease and actual producer/Go/SQL verification; original partial17 controller unchanged',
 'manifest':'manifest.json self-excluded; exact SHA/bytes emitted by actual final terminal tool result',
 'seal_actual_native_exit':None,'seal_actual_exit_authority':'external terminal result only'})
assert read('prepare.native-observation.json')['native_exit']==0 and read('audit.native-observation.json')['native_exit']==0
files=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
manifest=emit('manifest.json',{'schema':'researchos.whole-namespace-manifest.v1','root':OUT.as_posix(),'self_excluded':'manifest.json','file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'members':files})
for r in files:assert ref(Path(r['path']))==r
print(json.dumps({'status':'SEALED_SOURCE_PREPARATION_NOT_RUN','manifest':manifest,'handoff':handoff,'static_audit':ref(OUT/'static-byte-audit.json'),'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'writer':'STOPPED'},ensure_ascii=False))
