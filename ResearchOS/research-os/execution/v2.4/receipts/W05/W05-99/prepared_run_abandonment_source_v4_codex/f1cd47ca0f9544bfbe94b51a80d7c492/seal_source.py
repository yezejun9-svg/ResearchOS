import pathlib,json,hashlib
O=pathlib.Path(__file__).parent
def ref(p):
 p=pathlib.Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(n,d):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
base=json.loads((O/'base-refs.json').read_text(encoding='utf-8'))
static=json.loads((O/'source-static-evidence.json').read_text(encoding='utf-8'))
for x in base['input_refs']:
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
for rel,x in base['source_refs'].items():
 a=ref(O/rel);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name not in ('HDF.json','MF.json'))
members={str(p.relative_to(O)).replace('\\','/'):base['source_refs'].get(str(p.relative_to(O)).replace('\\','/'),ref(p)) for p in files}
total=len(members)+2
put('MF.json',dict(schema='researchos.prepared-run-abandonment-source-manifest.v4',sourceStatus='EXECUTION_REPORTED',revision_root=str(O),expected_write_root=str(O.parent.parent),source_dir=str(O/'candidate-root'),source_file_count=6,member_count=len(members),total_file_count_in_revision=total,members=members,metadata_files_excluded_from_members=['HDF.json','MF.json'],source_refs=base['source_refs'],previous_HDF_ref=base['previous_HDF_ref'],previous_MF_ref=base['previous_MF_ref'],base_refs_ref=ref(O/'base-refs.json'),main_base_refs=base['main_base_refs'],input_refs=base['input_refs'],input_drift=0,productionAuthority='UNSATISFIED',goVerification='NOT_RUN_BY_SOURCE_AUTHOR',productionMigration='UNAUTHORIZED'))
put('HDF.json',dict(schema='researchos.prepared-run-abandonment-handoff.v4',sourceStatus='EXECUTION_REPORTED',decision='SOURCE_FIXTURE_FIX_ONLY_ROOT_ACTUAL_TESTS_REQUIRED',submission_scope='W05/W05-99',expected_write_root=str(O.parent.parent),revision_root=str(O),source_dir=str(O/'candidate-root'),source_file_count=6,manifest_member_count=len(members),total_file_count_in_revision=total,manifest_ref=ref(O/'MF.json'),source_refs=base['source_refs'],base_refs_ref=ref(O/'base-refs.json'),previous_HDF_ref=base['previous_HDF_ref'],previous_MF_ref=base['previous_MF_ref'],diff_ref=ref(O/'source-diff.patch'),v3_delta_ref=ref(O/'v3-to-v4.diff.patch'),static_evidence_ref=ref(O/'source-static-evidence.json'),original_tool_io_ref=ref(O/'original-construction-tool-io.json'),changed_sources=static['changed_sources'],byte_identical_v3_sources=static['byte_identical_v3_sources'],fixture_fix='Removed preparedChangeManifest SQL mutation blocked by immutable manifest trigger. Five cases now clone the real persisted typed manifest in memory and call the actual profile checker after clean LIVE unknown-cost baseline.',checker_only_case_names=static['checker_only_case_names'],checker_only_cases=5,retained_top_level_upload_and_marker_cases=7,checker_cases_are_not_top_level_API_coverage=True,existing_success_idempotency_authority_footprint_tests_unchanged=True,production_guards_and_triggers_unchanged=True,productionAuthority='UNSATISFIED',trusted_private_authority_factory='OPEN',default_nil_authority='DENY',migration0024='UNCHANGED_FRESH_ONLY_POPULATED_DB_UPGRADE_NOT_AUTHORIZED',goVerification='NOT_RUN_BY_SOURCE_AUTHOR',Source_native_SQL_provider_execution='NOT_RUN',original_trial_provider_requests=None,original_once_consumed=True,original_clock_reset=False,automatic_retry=False,new_failures=[],prior_failures_preserved=True,formal_acceptance=False,input_drift=0,stopped=True))
assert len([p for p in O.rglob('*') if p.is_file()])==total
for x in members.values():
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
print(json.dumps(dict(HDF=ref(O/'HDF.json'),MF=ref(O/'MF.json'),test_source=ref(O/'candidate-root/internal/domain/prepared_run_abandonment_windows_test.go'),member_count=len(members),total_file_count=total,input_drift=0,new_failures=[])))

