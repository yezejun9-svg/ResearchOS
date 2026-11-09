import sys
sys.dont_write_bytecode = True
import ast
import difflib
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent
KEY = "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"

def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def verify(value):
    actual = ref(value["path"])
    assert (actual["sha256"], actual["bytes"]) == (value["sha256"], value["bytes"]), "pinned input differs"
    return actual

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(name, value):
    path = Q/name
    raw = (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
    with path.open("xb") as stream:
        assert stream.write(raw) == len(raw)
    return ref(path)

def verified_manifest(root, manifest_ref):
    verify(manifest_ref)
    manifest = read_json(manifest_ref["path"])
    members = manifest["members"]
    verified = []
    names = set()
    for member in members:
        relative = member.get("relative_path", member.get("relative_name"))
        assert isinstance(relative, str) and relative and relative not in names, "unique relative member required"
        part = Path(relative)
        assert not part.is_absolute() and ".." not in part.parts, "member must stay below Source packet"
        names.add(relative)
        actual = ref(root/part)
        assert (actual["sha256"], actual["bytes"]) == (member["sha256"], member["bytes"]), "manifest member differs"
        verified.append(dict(actual, relative_path=relative))
    return verified

def main():
    inspection = read_json(Q/"inspection.json")
    static = read_json(Q/"static-evidence.json")
    metadata = read_json(Q/"metadata-summary.json")
    for field in ("CTL2_HDF_ref", "CTL2_MF_ref", "base_controller_ref", "EnvSource_HDF_ref", "EnvSource_MF_ref"):
        verify(inspection[field])
    for value in inspection["CTL2_member_refs_verified"]:
        verify(value)
    for pair in inspection["snapshots"]:
        verify(pair["source_ref"])
        verify(pair["snapshot_ref"])
    for value in metadata["outputs"].values():
        verify(value)
    for field in ("base_ref", "candidate_ref", "patch_ref", "observer_snapshot_ref", "API_snapshot_ref"):
        verify(static[field])
    assert static["candidate_ref"]["sha256"] == "a1f53e223f47c5d8ecdb7edc5f94fec0bcc36beae9774d16ad9d0002b6ef638a"
    assert static["candidate_ref"]["bytes"] == 42696
    assert static["base_ref"]["sha256"] == "14cba01f91b7d9f322243c0df041a29337c422f72ea96214337047522dec8c83"
    assert static["base_ref"]["bytes"] == 40404
    env_root = Path(inspection["EnvSource_MF_ref"]["path"]).parent
    env_members = verified_manifest(env_root, inspection["EnvSource_MF_ref"])
    base_raw = Path(static["base_ref"]["path"]).read_bytes()
    candidate_raw = (Q/"root_native_migration_controller.py").read_bytes()
    before_lines = base_raw.decode("utf-8").splitlines(keepends=True)
    after_lines = candidate_raw.decode("utf-8").splitlines(keepends=True)
    edits = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before_lines, after_lines, autojunk=False).get_opcodes():
        if tag != "equal":
            edits.append({"operation": tag, "base_start_line_zero_based": i1, "base_end_line_exclusive": i2,
                "candidate_start_line_zero_based": j1, "candidate_end_line_exclusive": j2,
                "base_text": "".join(before_lines[i1:i2]), "candidate_text": "".join(after_lines[j1:j2])})
    restored = list(after_lines)
    for edit in reversed(edits):
        restored[edit["candidate_start_line_zero_based"]:edit["candidate_end_line_exclusive"]] = edit["base_text"].splitlines(keepends=True)
    assert "".join(restored).encode("utf-8") == base_raw, "exact inverse must restore complete base bytes"
    inverse_ref = write("controller-inverse-edits.json", {"schema": "researchos.controller-exact-inverse.v1",
        "authority": "NONE", "base_ref": static["base_ref"], "candidate_ref": static["candidate_ref"],
        "exact_inverse_byte_equal": True, "line_region_count": len(edits), "edits": edits})
    before = ast.parse(base_raw.decode("utf-8"))
    after = ast.parse(candidate_raw.decode("utf-8"))
    compile(after, "root_native_migration_controller.py", "exec")
    bdefs = {n.name:n for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    adefs = {n.name:n for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    unchanged = static["all_other_top_level_functions_classes_raw_and_AST_equal"]
    assert len(unchanged) == 30
    assert set(adefs) == set(bdefs) | {"_require_isolated_temp_environment"}
    for name in unchanged:
        assert ast.dump(bdefs[name], include_attributes=False) == ast.dump(adefs[name], include_attributes=False)
        assert ast.get_source_segment(base_raw.decode("utf-8"),bdefs[name]) == ast.get_source_segment(candidate_raw.decode("utf-8"),adefs[name])
    assert static["only_new_ENV_KEY"] == KEY
    assert set(static["new_ENV_KEYS"]) - set(static["old_ENV_KEYS"]) == {KEY}
    assert not set(static["old_ENV_KEYS"]) - set(static["new_ENV_KEYS"])
    matrix = read_json(Q/"boundary-matrix.json")
    assert len(matrix["cases"]) == 16 and all(c["actual"] == "NOT_RUN" for c in matrix["cases"])
    prerequisites = read_json(Q/"root-public-context-prerequisites.json")
    assert len(prerequisites["exact_config_fields"]) == 12
    assert len(prerequisites["eight_public_ref_fields"]) == 8
    assert len(prerequisites["seven_harness_RawPin_fields"]) == 7
    original_io = read_json(Q/"original-tool-io.json")
    assert original_io["authority"] == "NONE" and original_io["calls"], "complete original IO required before seal"
    closure_ref = write("source-guard-closure.json", {
        "schema": "researchos.controller-source-static-guard-closure.v1", "authority": "NONE",
        "scope": "Source packet and public snapshots only; actual Root retained native Source guard not run",
        "candidate_ref": static["candidate_ref"], "base_ref": static["base_ref"],
        "CTL2_HDF_ref": inspection["CTL2_HDF_ref"], "CTL2_MF_ref": inspection["CTL2_MF_ref"],
        "all_CTL2_13_member_refs_reverified": inspection["CTL2_member_refs_verified"],
        "EnvSource_HDF_ref": inspection["EnvSource_HDF_ref"], "EnvSource_MF_ref": inspection["EnvSource_MF_ref"],
        "all_EnvSource_member_refs_reverified": env_members,
        "all_copied_input_source_and_snapshot_refs_reverified": inspection["snapshots"],
        "Root_actual_retained_guard_entire_context_FrozenInputs": "PENDING_ROOT_FRESH_ACTUAL",
        "Root_required_actual_mapping_ref": ref(Q/"root-public-context-prerequisites.json"),
        "prior_failure_835_841_843_and_all_history_unchanged": True,
        "new_mechanical_errors": 0, "Main_T5_T6_T7_canonical_oldSource_writes": 0,
        "controller_observer_imported_or_context_helper_called": False})
    hdf = {
        "schema": "researchos.native-controller-temp-env-source-handoff.v1", "authority": "NONE",
        "formal_acceptance": False, "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_FRESH_ACTUAL",
        "packet_root": str(Q), "candidate_ref": static["candidate_ref"],
        "CTL2_base_ref": static["base_ref"], "CTL2_HDF_ref": inspection["CTL2_HDF_ref"],
        "CTL2_MF_ref": inspection["CTL2_MF_ref"], "native_broker_Source_HDF_ref": inspection["EnvSource_HDF_ref"],
        "native_broker_Source_MF_ref": inspection["EnvSource_MF_ref"],
        "delta_ref": ref(Q/"controller-temp-env.patch"), "exact_inverse_ref": inverse_ref,
        "static_evidence_ref": ref(Q/"static-evidence.json"), "Source_guard_closure_ref": closure_ref,
        "contract_ref": ref(Q/"CONTRACT.md"), "boundary_matrix_ref": ref(Q/"boundary-matrix.json"),
        "Root_public_context_prerequisites_ref": ref(Q/"root-public-context-prerequisites.json"),
        "source_call_chain_excerpts_ref": ref(Q/"source-call-chain-excerpts.json"),
        "exact_uint64_failure_history_ref": ref(Q/"filetime-history-qualification.json"),
        "original_tool_IO_ref": ref(Q/"original-tool-io.json"),
        "new_public_key_only": KEY, "exact_literal_binding": "proofRoot == TEMP == TMP",
        "Root_fresh_temp_root": "absolute existing canonical child of fixed R/.local; trial/system overlap prohibited",
        "Schema_other_ENVkeys_source_identity_all_provenance_atomic_Sign_Job_release_TTL_gates_unchanged": True,
        "unchanged_other_top_level_raw_and_AST_definition_count": 30, "exact_inverse_byte_equal": True,
        "boundary_expected_count": 16, "boundary_actual": "NOT_RUN",
        "pure_context_helper_controller_observer_execution": False, "Go_native_SQL_sign_crypto_model_execution": None,
        "Main_T5_T6_T7_canonical_old_Source_writes": 0,
        "new_mechanical_errors": 0, "historical_failures_and_counter_not_reset": True,
        "Root_next_action": "non-author independent Source review, fresh full public context guard validation and actual compilation/native positive under existing Root authority",
        "MF_exclusions_exact_relative_paths": ["MF.json", "postseal-tool-io.json"],
        "postseal_IO": "written separately after actual seal result, never self-authoritative"
    }
    hdf_ref = write("HDF.json", hdf)
    members = []
    exclusions = set(hdf["MF_exclusions_exact_relative_paths"])
    for path in sorted(Q.rglob("*"), key=lambda p: p.relative_to(Q).as_posix()):
        if path.is_file():
            relative = path.relative_to(Q).as_posix()
            if relative not in exclusions:
                members.append(dict(ref(path), relative_path=relative))
    assert any(m["relative_path"] == "inputs/CTL2/MF.json" for m in members)
    assert any(m["relative_path"] == "inputs/EnvSource/MF.json" for m in members)
    mf_ref = write("MF.json", {
        "schema": "researchos.native-controller-temp-env-source-manifest.v1",
        "authority": "NONE", "formal_acceptance": False, "status": hdf["status"],
        "packet_root": str(Q), "HDF_ref": hdf_ref, "members": members,
        "exclusions_exact_relative_paths": sorted(exclusions)})
    for value in members:
        verify(value)
    print(json.dumps({"authority": "NONE", "formal_acceptance": False,
        "HDF_ref": hdf_ref, "MF_ref": mf_ref, "candidate_ref": static["candidate_ref"],
        "contract_ref": hdf["contract_ref"], "static_ref": hdf["static_evidence_ref"],
        "delta_ref": hdf["delta_ref"], "inverse_ref": inverse_ref,
        "Source_guard_closure_ref": closure_ref, "member_count": len(members),
        "exact_inverse_byte_equal": True, "unchanged_other_definition_count": 30,
        "new_mechanical_errors": 0, "Root_actual": "NOT_RUN", "stop_after_seal": True}, ensure_ascii=False))

code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    code = 1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
