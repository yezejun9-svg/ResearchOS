import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=P.parent.parent/"native_migration_fixture_harness_source_codex/7050b5e73f7b3f54cb8fa9dc18"
def ref(x):
 b=x.read_bytes();return {"path":str(x),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(name,obj):
 with (P/name).open("x",encoding="utf-8",newline="\n") as stream:json.dump(obj,stream,ensure_ascii=True,indent=2)
old=json.loads((OLD/"HDF.json").read_text(encoding="utf-8"))
assert ref(OLD/"HDF.json")["sha256"]=="bea28f1679be60a36ff12170d919f8f441ec1deb748628125e21d40d75e4e9c5"
members={x.relative_to(P).as_posix():ref(x) for x in sorted(P.rglob("*")) if x.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
new("MF.json",{"schema":"researchos.native-migration-error-revision-manifest.v1","members":members})
source_names=["candidate-root/internal/domain/native_migration_authority_harness_windows_test.go",
 "candidate-root/internal/domain/native_migration_error_match_windows_test.go","root_only_native_broker.py"]
hdf=dict(old)
hdf.update({"schema":"researchos.native-migration-error-revision-handoff.v1",
 "status":"MINIMAL_ERROR_MATCH_SOURCE_REVISION_PENDING_ROOT_GO_TESTS_AND_INDEPENDENT_REVIEW",
 "source_root":str(P),"source_file_count":3,"source_refs":{name:ref(P/name) for name in source_names},
 "manifest_member_count":len(members),"manifest_ref":ref(P/"MF.json"),
 "contract_ref":ref(P/"CONTRACT.md"),"base_pins_ref":ref(P/"base-pins.json"),
 "program_provenance_ref":ref(P/"program-provenance.json"),
 "static_evidence_ref":ref(P/"static-evidence.json"),"original_tool_io_ref":ref(P/"original-tool-io.json"),
 "original_handoff_ref":ref(OLD/"HDF.json"),"original_manifest_ref":ref(OLD/"MF.json"),
 "original_static_evidence_ref":ref(OLD/"static-evidence.json"),
 "original_failure798_ref":old["failure_origin_ref"],
 "finding_ref":ref(P/"finding-origin.json"),"revision_patch_ref":ref(P/"revision.patch"),
 "revision_input_pins_ref":ref(P/"revision-input-pins.json"),"guard_cases_ref":ref(P/"guard-cases.json"),
 "new_mechanical_failures":[],
 "exact_delta":{"original_go_file":"one helper plus two complete-match call replacements and complete wrong-owner Fault.Error expectation",
  "new_go_unit_file":"24 narrow matcher cases under windows && researchos_native_recovery_harness",
  "python_broker":"byte-identical","contract":"one expected-message correction plus exact-match amendment",
  "all_nine_native_cases_and_other_assertions":"byte-identical after inversion of enumerated edits"},
 "inherited_base_pins":{"count":93,"index_byte_identical":True,"full_inventory_reexecuted":False},
 "runtime_unit_test_status":"NOT_RUN_SOURCE_AUTHOR_PROHIBITED_GO_EXECUTION",
 "required_root_checks":["independent exact revision delta and production log format review",
  "run guarded pure TestNativeHarnessExpectedError (24 cases) with actual Root Go harness",
  "existing nine native migration cases after independent signing and Owner pipe review",
  "retained full row/schema and actual Job/guard verification"],
 "source_author_actions":{"go_or_gofmt":False,"native_programs":False,"sql":False,
  "private_resource_reads":False,"signing":False,"provider_requests":0,"main_or_canonical_writes":False}})
new("HDF.json",hdf)
for name,item in members.items():assert ref(P/name)==item
assert ref(OLD/"HDF.json")["sha256"]=="bea28f1679be60a36ff12170d919f8f441ec1deb748628125e21d40d75e4e9c5"
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"source_refs":hdf["source_refs"],
                 "members":len(members),"go_unit_cases":24,"go_native_sql_run":False},ensure_ascii=True))

