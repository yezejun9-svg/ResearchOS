import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent
B = Q.parent.parent
R = B.parent.parent.parent.parent.parent
KEY = "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"

def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def verify(value):
    actual = ref(value["path"])
    assert (actual["sha256"], actual["bytes"]) == (value["sha256"], value["bytes"]), "pinned input differs"
    return actual

def write(name, value):
    path = Q / name
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        assert stream.write(raw) == len(raw)
    return ref(path)

def main():
    inspection = json.loads((Q/"inspection.json").read_text(encoding="utf-8"))
    static = json.loads((Q/"static-evidence.json").read_text(encoding="utf-8"))
    for key in ("CTL2_HDF_ref", "CTL2_MF_ref", "base_controller_ref", "EnvSource_HDF_ref", "EnvSource_MF_ref"):
        verify(inspection[key])
    for value in inspection["CTL2_member_refs_verified"]:
        verify(value)
    for pair in inspection["snapshots"]:
        verify(pair["source_ref"])
        verify(pair["snapshot_ref"])
    for key in ("base_ref", "candidate_ref", "patch_ref", "observer_snapshot_ref", "API_snapshot_ref"):
        verify(static[key])
    source = (Q/"root_native_migration_controller.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    nodes = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    def node_ref(name):
        node = nodes[name]
        return {"source_ref": static["candidate_ref"], "name": name, "line": node.lineno, "end_line": node.end_lineno}
    selected = ("canonical_path", "require_ref", "from_raw_pin", "load_public_module",
                "_plain_guard_refs", "_closed_native", "_require_isolated_temp_environment",
                "context", "serve", "sign_reviewed", "publish_signed", "release_fixture")
    excerpts = []
    lines = source.splitlines()
    for name in selected:
        n = nodes[name]
        excerpts.append(dict(node_ref(name), lines=[
            {"line": index+1, "text": lines[index]}
            for index in range(n.lineno-1, n.end_lineno)]))
    excerpt_ref = write("source-call-chain-excerpts.json", {
        "schema": "researchos.source-call-chain-excerpts.v1", "authority": "NONE",
        "source_executed": False, "excerpts": excerpts})

    history = Q/"inputs"/"history"
    history.mkdir(parents=True, exist_ok=False)
    correction = B/"integration_codex"/"root-metadata-diagnostic-843-filetime-precision"/"failure-origin.843.json"
    invocation = B/"integration_codex"/"native-ttl-controller-config-v2-root-4a61fbed032643e4"/"controller-runtime"/"test.invocation.json"
    correction_raw = correction.read_bytes()
    invocation_raw = invocation.read_bytes()
    invocation_ref = ref(invocation)
    assert invocation_ref["sha256"] == "fd21fe7c64be206de278857408da2d04d0bfd1769894b0821af8fee64ff87a7c"
    assert invocation_ref["bytes"] == 3722
    decoded_correction = json.loads(correction_raw.decode("utf-8"))
    decoded_invocation = json.loads(invocation_raw.decode("utf-8"))
    assert decoded_correction["ordinal"] == 843
    exact_go_time = decoded_invocation["result"]["creation_time_100ns"]
    assert type(exact_go_time) is int and str(exact_go_time) == "134359787460741284"
    assert decoded_correction["observed_harness_creation_time_decimal"] == str(exact_go_time)
    for name, raw in (("failure-origin.843.json", correction_raw), ("test.invocation.json", invocation_raw)):
        with (history/name).open("xb") as stream:
            assert stream.write(raw) == len(raw)
    history_ref = write("filetime-history-qualification.json", {
        "schema": "researchos.exact-filetime-history-qualification.v1", "authority": "NONE",
        "original835_ref_as_stated_by_Root843": decoded_correction["original_origin835_ref"],
        "original835_unchanged_not_rewritten": True, "failure_counter_reset": False,
        "Root843_source_ref": ref(correction), "Root843_snapshot_ref": ref(history/"failure-origin.843.json"),
        "held_native_invocation_source_ref": invocation_ref,
        "held_native_invocation_snapshot_ref": ref(history/"test.invocation.json"),
        "recorded835_go_FILETIME_decimal_inaccurate": decoded_correction["recorded_harness_creation_time_decimal"],
        "held_native_go_FILETIME_decimal": str(exact_go_time),
        "rehearsal_FILETIME_decimal_Root_reported_actual": "134359787476336016",
        "rehearsal_value_provenance": "Root CTL3 task text; child invocation not opened by this Source author",
        "exact_integer_parser": "Python json int, converted to decimal string",
        "JavaScript_Number_used_for_64bit_observation": False,
        "new_native_invocation_performed": False})

    expected = []
    def boundary(name, expected_outcome, gate, condition, required_input):
        expected.append({"case": name, "expected": expected_outcome, "actual": "NOT_RUN",
            "scope": "source-only synthetic public environment boundary",
            "gate_ref": node_ref(gate), "condition": condition, "Root_actual_input": required_input})
    boundary("fresh-existing-local-directory", "environment guard permits; full context still needs every pin",
             "_require_isolated_temp_environment",
             "One absolute canonical existing fresh directory below this repository .local, not trial/system; proof == TEMP == TMP literal",
             "Root creates fresh isolated local temp directory, uses exact same absolute value for all three env keys")
    boundary("proof-absent-legacy-environment", "new guard not called; prior context behavior preserved",
             "context", "Proof key absent", "Original fixed public environment and all prior pinned context resources")
    boundary("unknown-extra-environment-key", "REJECT", "context",
             "Environment keys are not subset of ENV_KEYS", "Synthetic unknown public key plus otherwise valid fixed cfg")
    boundary("non-string-or-NUL-value", "REJECT", "context",
             "Any environment value not string or contains NUL", "Synthetic invalid value; no secret required")
    boundary("required-Windows-or-temp-key-missing", "REJECT", "context",
             "SystemRoot/WINDIR/TEMP/TMP missing", "Remove exactly one required public key from fixed synthetic cfg")
    boundary("empty-or-whitespace-proof", "REJECT", "_require_isolated_temp_environment",
             "Empty or whitespace proof root", "Set proof/TEMP/TMP to same empty or whitespace string")
    boundary("TEMP-or-TMP-binding-differs", "REJECT", "_require_isolated_temp_environment",
             "TEMP != proof or TMP != proof literal", "One different existing synthetic local directory, including differing alias spelling")
    boundary("relative-root", "REJECT", "_require_isolated_temp_environment",
             "Normalized declared proof path not absolute", "Same relative value for proof/TEMP/TMP")
    boundary("repository-local-root-itself", "REJECT", "_require_isolated_temp_environment",
             "Proof equals repository .local", "Same exact R/.local value for proof/TEMP/TMP")
    boundary("outside-local-or-different-volume", "REJECT", "_require_isolated_temp_environment",
             "Proof is outside fixed repository local directory", "Use separate non-private synthetic absolute path; no original DB needed")
    boundary("missing-directory-or-regular-file", "REJECT", "_require_isolated_temp_environment",
             "Root path is not an existing directory", "New synthetic missing path or synthetic file below .local")
    boundary("trial-root-or-descendant", "REJECT before resolving/statting proof root",
             "_require_isolated_temp_environment",
             "Declared path equals or is below original trial namespace",
             "Lexical original trial name only; do not create or read any trial DB/private file")
    boundary("trial-containing-ancestor", "REJECT before resolving/statting proof root",
             "_require_isolated_temp_environment", "Declared proof is an ancestor of original trial namespace",
             "R/.local is already rejected; lexical ancestor boundary without contents reads")
    boundary("symlink-junction-alias-or-noncanonical-path", "REJECT", "canonical_path",
             "Path.resolve casefold differs from supplied path casefold; .local itself must also be canonical",
             "New synthetic controlled directory alias only; do not mutate original project resources")
    boundary("physical-trial-overlap", "REJECT", "_require_isolated_temp_environment",
             "Physical root overlaps fixed physical trial namespace",
             "NoSnapshot boundary expectation only; current canonical gate rejects noncanonical aliases first")
    boundary("system-directory-or-ancestor-overlap", "REJECT", "_require_isolated_temp_environment",
             "Proof overlaps canonical SystemRoot/WINDIR in either direction; directory values must exist",
             "Synthetic public directory metadata under isolated local root; actual system directory outside .local is rejected earlier")
    boundary_ref = write("boundary-matrix.json", {
        "schema": "researchos.controller-temp-env-expected-boundaries.v1",
        "authority": "NONE", "formal_acceptance": False, "pure_context_called": False,
        "helper_called": False, "source_only_static_expectations": True, "cases": expected})

    required = ["Schema", "ControllerDirectory", "ControllerSource", "HarnessConfig", "TestProgram",
        "ObservedOwnedHelper", "OriginalOwnedHelper", "SourceReadGuard", "CompilerInventory",
        "BuildInvocation", "FrozenInputs", "Environment"]
    eight = ["ControllerSource", "HarnessConfig", "TestProgram", "ObservedOwnedHelper",
        "OriginalOwnedHelper", "SourceReadGuard", "CompilerInventory", "BuildInvocation"]
    seven = ["RootProgram", "ControlProgram", "BackupProgram", "EnrollmentProgram", "PythonProgram",
        "BrokerSource", "PrivateStdinHelper"]
    context_segment = ast.get_source_segment(source, nodes["context"])
    assert all('"'+key+'"' in context_segment for key in required + eight + seven)
    mappings = [
        {"input": "config_ref", "requirement": "Exact public {path,sha256,bytes}; prefix sha256:, canonical absolute path, actual UTF8 JSON bytes, duplicate members rejected; no private file reference",
         "producer": "Root fresh public fixed cfg, after independent CTL3 review", "status": "PENDING_ROOT"},
        {"input": "ControllerSource", "requirement": "Exact byte pin of this candidate (or byte-identical Root fresh copy); runtime path equals __file__; exact same ref in FrozenInputs",
         "available_source_ref": static["candidate_ref"], "status": "SOURCE_AVAILABLE_ACTUAL_PENDING"},
        {"input": "ObservedOwnedHelper", "requirement": "CTL2 observer bytes preserved; Root fresh runtime public path pinned and frozen",
         "available_source_snapshot_ref": static["observer_snapshot_ref"], "status": "SOURCE_AVAILABLE_ACTUAL_PENDING"},
        {"input": "OriginalOwnedHelper and SourceReadGuard",
         "requirement": "Root actual approved public modules pinned; exact refs in FrozenInputs; do not assume runtimeResource paths from old receipts",
         "status": "ROOT_FRESH_PUBLIC_RESOURCE_REFS_REQUIRED"},
        {"input": "HarnessConfig", "requirement": "Exact synthetic-native-migration-config.v1 and one of existing 9 Cases; every seven RawPin verified and exactly frozen; PythonProgram == fixed sys.executable",
         "status": "ROOT_FRESH_CONFIG_REQUIRED"},
        {"input": "seven RawPin members", "members": seven,
         "requirement": "Each exact {role,path,sha256,bytes}; Root/Control programs exist and share same fresh parent; no private issuer/ExecuteClaim contents in Source packet",
         "status": "ROOT_FRESH_PUBLIC_PINS_REQUIRED"},
        {"input": "TestProgram, BuildInvocation, CompilerInventory",
         "requirement": "Root fresh accepted EnvSource composition compile; exactly one -o and -c and native recovery tag; cwd == HarnessConfig.BuildRoot; selected test binary path exact; actual_native_exit == 0 and full native Job/handles closure",
         "native_broker_source_HDF_ref": inspection["EnvSource_HDF_ref"],
         "native_broker_source_MF_ref": inspection["EnvSource_MF_ref"],
         "status": "ROOT_FRESH_COMPILATION_AND_INDEPENDENT_REVIEW_REQUIRED"},
        {"input": "CompilerInventory.build_inputs/product_inventory",
         "requirement": "All actual test+embed+product input pins frozen; build_tag exactly researchos_native_recovery_harness, includes_actual_test_and_embed_inputs True; sha256 prefix normalized by unchanged gate",
         "status": "ROOT_ACTUAL_COMPLETE_INVENTORY_REQUIRED"},
        {"input": "FrozenInputs", "requirement": "Nonempty, path-unique public refs; all eight refs and seven RawPins and compiler/product inputs and every OriginalOwnedHelper.runtime_resource_paths member exact; guard retains whole closure",
         "status": "ROOT_FRESH_FULL_CLOSURE_REQUIRED"},
        {"input": "ControllerDirectory/HarnessConfig.OutputDirectory/HarnessConfig.BuildRoot",
         "requirement": "Canonical Root fresh directories; controller/output disjoint in both ancestor directions; build matches actual compiler invocation",
         "status": "ROOT_FRESH_DIRECTORY_REFS_REQUIRED"},
        {"input": "Environment", "requirement": "Only old reviewed keys + this one proof key, all string no NUL; exact fixed proofRoot == TEMP == TMP; proof existing canonical child below fixed R/.local, no trial/system overlap; never os.environ inheritance",
         "status": "ROOT_FRESH_PUBLIC_ENVIRONMENT_REQUIRED"},
        {"input": "context entry only", "requirement": "Root may call context with full valid public resource closure and record exact input/stdout/stderr/actual exit; this author did not import controller/module or call context/helper",
         "status": "NOT_RUN"},
        {"input": "later native launch/sign/release", "requirement": "Separate existing Root grant/private stdin owner binding, per payload manual approval/sign, specific release and full Job closure. Pure context cannot authorize native/accept formal case.",
         "status": "NOT_RUN"}]
    prerequisites_ref = write("root-public-context-prerequisites.json", {
        "schema": "researchos.controller-temp-env-root-context-prerequisites.v1",
        "authority": "NONE", "formal_acceptance": False,
        "fixed_config_schema_unchanged": "researchos.root-native-migration-controller.v1",
        "exact_config_fields": required, "eight_public_ref_fields": eight,
        "seven_harness_RawPin_fields": seven, "mappings": mappings,
        "context_source_ref": node_ref("context"), "full_Sourceguard_closure_claim": "Required for Root actual; not fabricated/passed by Source author",
        "contents_of_original_trial_or_private_files_read": False})
    result = {"history_ref": history_ref, "boundary_ref": boundary_ref,
              "Root_prerequisites_ref": prerequisites_ref, "source_excerpts_ref": excerpt_ref}
    write("metadata-summary.json", {"authority": "NONE", "outputs": result, "new_mechanical_errors": 0,
        "all_current_source_pins_verified": True, "marked_python_exit_expected_after_success": 0,
        "controller_or_observer_imported": False, "Go_SQL_native_sign_crypto_model_execution": None})
    print(json.dumps({"authority": "NONE", "boundary_case_count": len(expected),
        "public_cfg_field_count": len(required), "all_boundaries_actual": "NOT_RUN",
        "outputs": result}, ensure_ascii=False))

code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    code = 1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
