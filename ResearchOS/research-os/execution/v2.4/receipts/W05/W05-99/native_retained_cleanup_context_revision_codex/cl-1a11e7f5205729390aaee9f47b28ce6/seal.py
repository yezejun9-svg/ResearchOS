import ast,json,hashlib
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (N/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(N/n)
stat=json.loads((N/"static-preservation.json").read_bytes())
r=json.loads((N/"source-replacements.json").read_bytes())
candidate=Path(stat["candidate_ref"]["path"]).read_bytes()
base=(N/"base-root/internal/domain/native_migration_authority_harness_windows_test.go").read_bytes()
text=candidate.decode()
assert text.endswith(r["appended_helper_and_tests"])
inverse=text[:-len(r["appended_helper_and_tests"])]
assert inverse.count(r["replacement_block"])==1
inverse=inverse.replace(r["replacement_block"],r["original_block"],1)
assert inverse.encode()==base
assert pin(stat["candidate_ref"]["path"])==stat["candidate_ref"]
for ref in json.loads((N/"sourceguard.final.json").read_bytes())["refs"]:assert pin(ref["path"])==ref
ast.parse((N/"construct-source.py").read_bytes())
prov=save("provenance.json",dict(base_ref=stat["base_ref"],candidate_ref=stat["candidate_ref"],delta=["replace only registered cleanup block context source","append one explicit detached bounded context helper and four pure-Go subtests"],exact_inverse_bytes=True,old_imports_and_entire_remaining_bytes_preserved=True,source_assertion_calls_preserved=90,cases_preserved=stat["nine_cases"],old_Main_Source_writes=False,Go_AST_gofmt_compile_test_executed=False,Root_selected_cleanup_minutes=4,main_execution_minutes=20,current_Go_timeout_minutes=25,current_owned_job_timeout_minutes=30,grant_minutes=4))
members={p.relative_to(N).as_posix():pin(p) for p in N.rglob("*") if p.is_file() and p.name not in ("HDF.json","MF.json")}
mf=save("MF.json",dict(schema="researchos.native-retained-cleanup-context-manifest.v1",members=members,authority="NONE",formal_acceptance=False))
hdf=save("HDF.json",dict(schema="researchos.native-retained-cleanup-context-handoff.v1",status="SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ACTUAL",actor="codex:/root/command_queue_impl",manifest_ref=mf,manifest_member_count=len(members),candidate_ref=stat["candidate_ref"],base_ref=stat["base_ref"],production_files=0,candidate_files=1,report_ref=pin(N/"report.md"),provenance_ref=prov,static_ref=pin(N/"static-preservation.json"),source_guard_ref=pin(N/"sourceguard.final.json"),cleanup_minutes=4,main20min_and_grant4min_unchanged=True,current_Go25min_owned30min_unchanged=True,nine_original_cases_preserved=True,all90_original_assertion_calls_preserved=True,new_pure_Go_Test="TestNativeHarnessCleanupReviewContext",new_subtests=stat["new_pure_subtests"],Root_explicit_fixture_release_still_required=True,new_actual_Go_SQL_native_model_Git=False,mechanical_failures=[dict(ordinal=899,outer_exit=1,SourcePython_exit=1,native_exit=None,origin_ref=pin(N/"failure-origin.899.json"),failed_source_ref=pin(N/"construct-source.failed.899.py"))],failure_counter_reset=False,Main_canonical_old_Source_writes=False,self_approved=False,formal_acceptance=False,STOP=True))
for ref in members.values():assert pin(ref["path"])==ref
print(json.dumps(dict(HDF=hdf,MF=mf,members=len(members),candidate=stat["candidate_ref"],status="SOURCE_ONLY_SEALED_STOP",new_native_exit=None)))

