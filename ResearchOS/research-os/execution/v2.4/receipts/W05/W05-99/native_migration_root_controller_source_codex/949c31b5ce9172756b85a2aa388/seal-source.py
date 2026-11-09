"""Final metadata and AST inspection only. Never import controller modules."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parent.parent
H=B/"native_migration_harness_error_revision_codex/e57c696eaf418862f0eb721ec8c8"
F=B/"native_orchestration_read_failure_codex/805-2f8d31a9ad003"
N=B/"prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65/candidate-root"
C=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
HC=B/"integration_codex/native-migration-positive-root-73df768bc70b4f64/native-harness.public.config.json"
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(n,o):
 with (P/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(o,f,ensure_ascii=True,indent=2)
controller=P/"root_native_migration_controller.py"
observer=P/"windows_owned_observed.py"
code=controller.read_text(encoding="utf-8")
tree=ast.parse(code,filename=str(controller))
ast.parse(observer.read_text(encoding="utf-8"),filename=str(observer))
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
api=["serve","poll","snapshot","sign_reviewed","publish_signed","release_fixture","stop"]
assert all(name in functions for name in api)
serve_calls={n.func.id for n in ast.walk(functions["serve"]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
assert "sign_reviewed" not in serve_calls and "publish_signed" not in serve_calls and "release_fixture" not in serve_calls
assert "issuer_dpapi_path_runtime" not in ast.get_source_segment(code,functions["serve"])
assert "issuer_dpapi_path_runtime" not in ast.get_source_segment(code,functions["context"])
checks={
 "controller_and_observer_ast_parse":True,
 "serve_has_no_sign_or_approval_api_calls":True,
 "private_issuer_only_sign_runtime_api":True,
 "fixed_package_cwd":'str(c["build"]/"internal/domain")' in code,
 "fixed_test_program_and_flags":'"-test.run=^TestNativeMigrationAuthorityHarness$"' in code,
 "root_config_and_actual_build_output_binding":'build_argv.index("-o")+1' in code,
 "compiler_inventory_members_required_frozen":'inventory["build_inputs"] + inventory["product_inventory"]' in code,
 "same_held_job_observation_across_approval":'owned Job changed across review pause' in code,
 "signed_and_publish_are_separate_actions":"SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD" in code and "PUBLISH_REVIEWED_SIGNED_DOCUMENT" in code,
 "grant_absolute_240_second_bound":"<= 240" in code,
 "private_signer_stdout_stderr_nul":'open(os.devnull,"wb")' in code,
 "retained_fixture_requires_root_inspection":"RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION" in code,
 "no_sql_module_or_subprocess_shell":all(not(isinstance(n,ast.Import) and any(a.name in ("sqlite3","subprocess") for a in n.names)) for n in tree.body),
 "new_namespace_only":True,
}
assert all(checks.values())
inputs=[]
for p in [H/"HDF.json",H/"MF.json",H/"CONTRACT.md",H/"root_only_native_broker.py",
 H/"candidate-root/internal/domain/native_migration_authority_harness_windows_test.go",
 H/"candidate-root/internal/domain/native_migration_error_match_windows_test.go",
 B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py",
 B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py",
 B/"native_private_stdin_helper_revision_codex/320740c9ef7c4dbaa6cae48633aa8e60/windows_owned_private_stdin.py",
 N/"ops/supervisor/recovery_enrollment/main_windows.go",
 N/"internal/recoveryauthority/enrollment_windows.go",
 N/"internal/recoveryauthority/migration.go",N/"internal/recoveryauthority/types.go",
 C/"validation.closed.json",C/"tagged-test-binary-compile.invocation.json",
 C/"actual-tagged-compiler-input-inventory.json",HC,F/"HDF.json",F/"MF.json",F/"failure-origin.805.json"]:
 inputs.append(ref(p))
assert ref(H/"HDF.json")["sha256"]=="e8886cf85b95a84bade493e12691f995a631c179460726d29beba8e5c2a9b92e"
assert ref(HC)["sha256"]=="ef404512f197dda8223526af9f301fa922b54a84416e43094f79202e70f9fd32"
new("public-input-pins.json",{"schema":"researchos.native-controller-public-input-pins.v1","inputs":inputs,
 "existing_93_harness_base_inventory_reexecuted":False,"upcoming_fixture_or_private_paths_read":False})
new("static-evidence.json",{"schema":"researchos.native-controller-static-evidence.v1","checks":checks,
 "ast_only":True,"controller_imported_or_executed":False,"native_or_go_or_sql_run":False,
 "private_read_or_signing":False,"provider_requests":0,"failure805_distinct_preserved":True})
new("root-controller-api.json",{"schema":"researchos.root-native-controller-api.v1",
 "api":{name:[arg.arg for arg in functions[name].args.args] for name in api},
 "public_ref_shape":{"path":"absolute canonical public path","sha256":"sha256:<64hex>","bytes":"integer"},
 "issuer_dpapi_path":"runtime sign_reviewed argument only; never configured, saved or printed",
 "state_sequence":["serve-start","release snapshot","Root sign approval","sign_reviewed",
  "Root signed-document review approval","publish_signed","grant snapshot","Root sign approval",
  "sign_reviewed","Root signed-document review approval","publish_signed",
  "fixture-retained snapshot","Root actual fixture inspection","release_fixture","owned Job and guard closure"],
 "automatic_signing":False,"automatic_approval":False,"nine_case_loop":False})
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
new("MF.json",{"schema":"researchos.native-root-controller-source-manifest.v1","members":members})
hdf={"schema":"researchos.native-root-controller-source-handoff.v1",
 "status":"SOURCE_IMPLEMENTED_PENDING_ROOT_INDEPENDENT_REVIEW_AND_ACTUAL_EXECUTION",
 "sourceStatus":"EXECUTION_REPORTED","formal":False,"production_ready":False,"execution_authority":False,
 "actor_id":"codex:/root/command_queue_impl","source_root":str(P),
 "source_refs":{"root_native_migration_controller.py":ref(controller),"windows_owned_observed.py":ref(observer)},
 "manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),
 "contract_ref":ref(P/"CONTRACT.md"),"controller_api_ref":ref(P/"root-controller-api.json"),
 "static_evidence_ref":ref(P/"static-evidence.json"),"public_input_pins_ref":ref(P/"public-input-pins.json"),
 "helper_delta_ref":ref(P/"owned-observer.patch"),"helper_inverse_evidence_ref":ref(P/"observer-static.json"),
 "original_tool_io_ref":ref(P/"original-tool-io.json"),"harness_handoff_ref":ref(H/"HDF.json"),
 "failure805_handoff_ref":ref(F/"HDF.json"),"failure805_origin_ref":ref(F/"failure-origin.805.json"),
 "mechanical_failures":[{"ordinal":805,"actualOuter":1,"actualPython":None,"native":None,"distinct_from_800":True}],
 "source_author_errors_after_805":0,
 "source_author_actions":{"go_or_build_or_gofmt":False,"native_or_sql":False,"signing":False,
  "private_key_or_private_resource_read":False,"provider_requests":0,"Main_T3_T4_T5_canonical_writes":False},
 "actual_controller_lifetime_tests_run":False,"no_new_schema_fixture":True,
 "root_required_next":["independent Source and minimal owned-helper delta review",
  "actual observe/cancel/timeout Job closure validation before Owner-bearing harness",
  "freeze public configuration, build/compiler inputs and actual loaded Python/native modules",
  "drive one fresh case at a time with concrete review/sign/publish/inspection/release approvals",
  "independently verify full native results and retained DB invariants"],
 "private_boundary":"issuer path API runtime only, genuine native CLI consumes DPAPI; native signer stdio goes NUL, no saved private argv",
 "no_automatic_approval_or_signing":True,"native_acceptance":"PENDING_ROOT"}
new("HDF.json",hdf)
for n,r in members.items():assert ref(P/n)==r
for r in inputs:
 actual=ref(Path(r["path"]));assert actual["sha256"]==r["sha256"] and actual["bytes"]==r["bytes"]
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"source_refs":hdf["source_refs"],
                 "members":len(members),"public_inputs":len(inputs),"ast_only":True},ensure_ascii=True))

