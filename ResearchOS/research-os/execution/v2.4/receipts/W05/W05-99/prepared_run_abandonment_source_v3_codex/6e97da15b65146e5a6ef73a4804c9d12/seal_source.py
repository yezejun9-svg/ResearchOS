import pathlib,json,hashlib,difflib,re
O=pathlib.Path(__file__).parent
R=pathlib.Path(r"D:/作品集/ResearchOS/research-os")
def ref(p):
 p=pathlib.Path(p);raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def put(name,d,new=False):
 with (O/name).open('x' if new else 'w',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
base=json.loads((O/'base-refs.json').read_text(encoding='utf-8'))
for x in base['input_refs']+base['main_base_refs']:
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
supports=['internal/domain/runtime_qualification.go','internal/domain/runtime_coordinator_windows_test.go','internal/domain/runtime_dispatch.go','internal/domain/context_test.go','internal/domain/runtime_test.go','internal/domain/operations.go','internal/domain/budget_scopes.go','internal/domain/retrieval.go','migrations/sqlite/0002_domain.sql','migrations/sqlite/0005_runtime.sql','migrations/sqlite/0016_runtime_qualification.sql','execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_v5_codex/17e94063a8244fdfa69aefdbdf895cf6/staged-root-3896725ace2b4b2783334c313d548c4f/prepare.go']
supportRefs=[ref(R/p) for p in supports]
base['supporting_source_refs']=supportRefs
put('base-refs.json',base)
full=[];delta=[];sources={};unchanged=[];changed=[]
for rel in base['source_paths']:
 p=O/rel;prev=base['base_member_mapping'][rel];original=pathlib.Path(prev['path'])
 before=original.read_text(encoding='utf-8').splitlines(keepends=True);after=p.read_text(encoding='utf-8').splitlines(keepends=True)
 (unchanged if p.read_bytes()==original.read_bytes() else changed).append(rel)
 delta.extend(difflib.unified_diff(before,after,fromfile='v2/'+rel,tofile='v3/'+rel))
 target=pathlib.PurePosixPath(rel).relative_to('candidate-root')
 old=(R/target).read_text(encoding='utf-8').splitlines(keepends=True) if prev.get('base_sha256') else []
 full.extend(difflib.unified_diff(old,after,fromfile='a/'+str(target) if old else '/dev/null',tofile='b/'+str(target)))
 sources[rel]=dict(**ref(p),base_sha256=prev.get('base_sha256'),previous_ref={k:prev[k] for k in ['path','bytes','sha256']})
(O/'source-diff.patch').write_text(''.join(full),encoding='utf-8',newline='\n')
(O/'v2-to-v3.diff.patch').write_text(''.join(delta),encoding='utf-8',newline='\n')
assert len(sources)==6 and len(changed)==2 and len(unchanged)==4
source=(O/'candidate-root/internal/domain/prepared_run_abandonment.go').read_text(encoding='utf-8')
test=(O/'candidate-root/internal/domain/prepared_run_abandonment_windows_test.go').read_text(encoding='utf-8')
assert source.count('SELECT count(*) FROM')>=12
assert test.count('preparedDatabaseSnapshot(t,r)')>=6 and 'fault.Status!=status' in test and 'fault.Code!=code' in test
assert 'if s.preparedAbandonmentAuthority == nil' in source
assert 'DELETE FROM domain_objects' not in test and 'DELETE FROM uploaded_content' not in test
assert 'coordinatorFixture(t)' not in test and 'preparedAssertCleanProfile(t, r, evidence)' in test
e=json.loads((O/'source-static-evidence.json').read_text(encoding='utf-8'))
e.update(final_source_refs=sources,exact_fault_status_code_message_in_all_negative_groups=True,full_logical_fixture_DB_snapshot_before_after_rejection=True,static_checks_after_final_source_edits=True,source_construction_only=True)
put('source-static-evidence.json',e)
for x in base['input_refs']+base['main_base_refs']+supportRefs:
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name not in ('HDF.json','MF.json'))
members={str(p.relative_to(O)).replace('\\','/'):sources.get(str(p.relative_to(O)).replace('\\','/'),ref(p)) for p in files}
count=len(files)+2
mf=dict(schema='researchos.prepared-run-abandonment-source-manifest.v3',sourceStatus='EXECUTION_REPORTED',expected_write_root=str(O.parent.parent),revision_root=str(O),source_dir=str(O/'candidate-root'),source_file_count=6,member_count=len(members),total_file_count_in_revision=count,members=members,metadata_files_excluded_from_members=['HDF.json','MF.json'],metadata_exclusion_reason='No self-hash cycle; exact HDF/MF pins returned after sealing.',base_refs_ref=ref(O/'base-refs.json'),input_refs=base['input_refs'],main_base_refs=base['main_base_refs'],supporting_source_refs=supportRefs,input_drift=0,productionAuthority='UNSATISFIED',productionMigration='UNAUTHORIZED',goVerification='NOT_RUN_BY_SOURCE_AUTHOR')
put('MF.json',mf,True)
h=dict(schema='researchos.prepared-run-abandonment-handoff.v3',sourceStatus='EXECUTION_REPORTED',decision='SOURCE_CANDIDATE_ONLY_ROOT_ACTUAL_TESTS_REQUIRED',submission_scope='W05/W05-99',expected_write_root=str(O.parent.parent),revision_root=str(O),source_dir=str(O/'candidate-root'),source_file_count=6,manifest_member_count=len(members),total_file_count_in_revision=count,manifest_ref=ref(O/'MF.json'),source_refs=sources,base_refs_ref=ref(O/'base-refs.json'),diff_ref=ref(O/'source-diff.patch'),v2_delta_ref=ref(O/'v2-to-v3.diff.patch'),static_evidence_ref=ref(O/'source-static-evidence.json'),failure756_ref=ref(O/'failure-origin.756.json'),changed_sources=changed,unchanged_sources=unchanged,fix='Permit only exact immutable qualification-bound sealed pre-Run executor profile storage key; every other executor upload and every existing Run footprint remains rejected.',fixture='Production upload/seal/plan/BeginRuntimeQualification using LIVE unknown-cost admission; real immutable marker, no ledger deletion, eligible baseline before injection, exact Fault status/code/message and full logical DB rollback snapshot for negative cases.',v2_failure755_interpretation='Generic footprint refusal observed; old FIXTURE coordinator fixture creates a real reservation and Owner profile, so actual failure does not isolate executor-upload guard. R01 is a separately established static defect.',productionAuthority='UNSATISFIED',trusted_private_authority_factory='OPEN',default_nil_authority='DENY',migration0024='UNCHANGED_FRESH_ONLY_POPULATED_DB_UPGRADE_NOT_AUTHORIZED',goVerification='NOT_RUN_BY_SOURCE_AUTHOR',format_compile_tests_native_provider_SQL='NOT_RUN',original_trial_provider_requests=None,original_once_consumed=True,original_clock_reset=False,automatic_retry=False,new_failures=[756],formal_acceptance=False,input_drift=0,stopped=True)
put('HDF.json',h,True)
assert len([p for p in O.rglob('*') if p.is_file()])==count
for x in members.values():
 a=ref(x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes']
print(json.dumps(dict(HDF=ref(O/'HDF.json'),MF=ref(O/'MF.json'),source_refs=sources,member_count=len(members),total_file_count=count,input_drift=0,failure756_ref=ref(O/'failure-origin.756.json'))))

