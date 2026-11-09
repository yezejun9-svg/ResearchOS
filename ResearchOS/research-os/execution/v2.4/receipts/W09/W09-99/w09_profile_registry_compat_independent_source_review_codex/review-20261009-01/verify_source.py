"""Independent finite Source review. No current CP/OW open and no product run."""
import ast
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import types

O = Path(__file__).resolve().parent
R = O.parents[6]
Q = R / "execution/v2.4/receipts/W09/W09-99/w09_profile_registry_compat_source_codex/adfab031c6ab45ea947f1994b65b43f5"
S = R / "execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009"
G = R / "execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
GUARD_SHA = "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
checks = []


def pin(path):
    p = Path(path); raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def exact(ref):
    observed = pin(ref["path"])
    assert set(ref) == {"path", "sha256", "bytes"} and observed["sha256"] == ref["sha256"] and observed["bytes"] == ref["bytes"], ref
    return observed


def read(path): return json.loads(Path(path).read_bytes())


def save(name, value):
    with (O / name).open("xb") as stream: stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    return pin(O / name)


def check(name, ok):
    assert ok, name
    checks.append(dict(name=name, status="PASS_SOURCE_ONLY"))


hdf_ref = dict(path=str(Q / "HDF.json"), sha256="6e4153cce0bf202d744014f49122beb623588690f2d940c687228ec3c5ad4920", bytes=6729)
exact(hdf_ref); hdf = read(hdf_ref["path"]); exact(hdf["manifest_ref"]); mf = read(hdf["manifest_ref"]["path"])
public = read(hdf["public_Source_pins_ref"]["path"])["refs"]
historical = [pin(S / ("historical.cp370." + name + ".json")) for name in ("checkpoint", "path_ownership", "step_state", "commands")]
refs = [hdf_ref, hdf["manifest_ref"], *mf["members"], *public, *historical, pin(G)]
unique = {str(Path(ref["path"]).resolve()).casefold(): exact(ref) for ref in refs}
for name in ("checkpoint", "path_ownership"):
    assert str(R / ("execution/v2.4/" + name + ".json")).casefold() not in unique
check("SOURCE_HDF_MF_68_ALL_EXACT", len(mf["members"]) == 68)
check("HISTORICAL_CP370_OW174_CM39_ARCHIVES", [read(ref["path"]).get("revision") for ref in historical] == [370, 174, None, 39])
check("PUBLIC_CURRENT_SOURCE_PINS_ALL_EXACT", len(public) == 32)
check("SOURCE_AUTHOR_INDEPENDENT", hdf["Source_author"] == "codex:/root/backup_regression_resources")
raw = G.read_bytes(); assert hashlib.sha256(raw).hexdigest() == GUARD_SHA
guard_module = types.ModuleType("w09_review_guard"); exec(compile(raw, str(G), "exec"), guard_module.__dict__)
guard = guard_module.SourceReadGuard(per_file_cap=16 * 1024 * 1024, total_cap=64 * 1024 * 1024)
cleanup = None
try:
    guard.acquire(list(unique.values()))
    index_raw = (Q / "formal_case_index.after.py").read_bytes()
    index_before = (Q / "formal_case_index.before.py").read_bytes()
    profile_raw = Path(hdf["candidate_profile_ref"]["path"]).read_bytes()
    profile_before = (Q / "inputs/formal_profile_w09.before.py").read_bytes()
    check("INDEX_FULL71844_AND_W04W07_PREFIX51719_BYTE_IDENTICAL", len(index_raw) == 71844 and index_raw == index_before == (R / "execution/v2.4/formal_case_index.py").read_bytes() and hashlib.sha256(index_raw[:51719]).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1")
    check("MAIN_PROFILE_UNCHANGED_BASE_PIN", profile_before == (R / "execution/v2.4/formal_profile_w09.py").read_bytes())
    inverse = read(hdf["exact_inverse_ref"]["path"])
    restored = profile_raw.decode("utf-8")
    for patch in reversed(inverse["patches"]):
        assert restored.count(patch["after"]) == 1
        restored = restored.replace(patch["after"], patch["before"], 1)
    check("ALL_PROFILE_PATCHES_INVERSE_EXACT_RAW_BYTES", restored.encode() == profile_before)
    check("PER_FILE_CRLF_LF_COUNTS_PRESERVED_WITHOUT_NORMALIZATION", (index_raw.count(b"\r\n"), index_raw.count(b"\n")) == (index_before.count(b"\r\n"), index_before.count(b"\n")) and restored.encode().count(b"\r\n") == profile_before.count(b"\r\n") and restored.encode().count(b"\n") == profile_before.count(b"\n"))
    profile = {"__name__": "independent_source_profile"}; index = {"__name__": "independent_source_index"}
    exec(compile(profile_raw, str(hdf["candidate_profile_ref"]["path"]), "exec"), profile)
    exec(compile(index_raw, "read_only_source_index", "exec"), index)
    api = index["_profile_api"]()
    old_ast = {x.name: ast.dump(x, include_attributes=False) for x in ast.parse(profile_before).body if isinstance(x, ast.FunctionDef)}
    new_ast = {x.name: ast.dump(x, include_attributes=False) for x in ast.parse(profile_raw).body if isinstance(x, ast.FunctionDef)}
    changed = sorted(name for name, value in old_ast.items() if new_ast.get(name) != value)
    check("ONLY_FOUR_ORIGINAL_FUNCTIONS_CHANGED", changed == ["_dispatches", "_independent", "_native", "verify_owner"])
    check("ROOT_ORIGINAL_AND_CAPTURE_REGISTRY_UNCHANGED", old_ast["_root_original"] == new_ast["_root_original"] and old_ast["_capture_registry"] == new_ast["_capture_registry"])
    commands = read(hdf["candidate_CM40_ref"]["path"]); archive = read(Q / "inputs/commands.CM39.actual-archive.json")
    check("CM40_STRICT_32_COMMANDS_FOUR_ROUTE_DELTA", commands["revision"] == 40 and len(commands["commands"]) == 32 and commands["commands"] == profile["_cm40_commands"](archive) and {key for key in commands["commands"] if commands["commands"][key] != archive["commands"][key]} == {"test.retrieval", "test.security"})
    metadata = {"revision", "revision_note", "updated_at", "updated_by", "commands"}
    check("REGISTRY_UNRELATED_METADATA_ZERO_DELTA", set(commands) == set(archive) and all(commands[k] == v for k, v in archive.items() if k not in metadata))
    check("REGISTRATION_TIMESTAMP_EXPLICITLY_UNISSUED", commands["updated_at"] == "PENDING_ROOT_ACTUAL_ISSUANCE")
    # Re-run the exact supplied finite suite in this owned review namespace.
    # Copies are bounded Source inputs, never Main or runtime inventories.
    relative_files = ["formal_case_index.before.py", "formal_case_index.after.py", "formal_profile_w09.after.py", "source_controls_v4.py", "source_controls_v5.py", "commands.after.json", "candidate-root/execution/v2.4/formal_profile_w09.py", "inputs/commands.CM39.actual-archive.json", "inputs/C19-0-dispatcher_receipt_ref.json", "inputs/C19-1-dispatcher_receipt_ref.json"]
    copied = []
    for relative in relative_files:
        destination = O / relative; destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream: stream.write((Q / relative).read_bytes())
        copied.append(dict(source=pin(Q / relative), reviewed_copy=pin(destination)))
    suite = {"__name__": "independent_v5_suite", "__file__": str(O / "source_controls_v5.py")}
    exec(compile((O / "source_controls_v5.py").read_bytes(), str(O / "source_controls_v5.py"), "exec"), suite)
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured): suite["main"]()
    save("finite-suite.stdout.json", dict(text=captured.getvalue(), synthetic_only=True))
    finite = read(O / "source-controls-v5.result.json")
    check("INDEPENDENT_RERUN_46_AND57_SOURCE_CONTROLS", finite["inherited_v4_count"] == 46 and finite["new_control_count"] == 57 and finite["formal_acceptance"] is False)
    # Additional independent mutations are recorded as expected rejection, not execution.
    temp_parent = O / "extra-synthetic-temp"; temp_parent.mkdir()
    def negative(name, mutation, code):
        with tempfile.TemporaryDirectory(dir=temp_parent) as path:
            fixture = suite["RoleFixture"](path); mutation(fixture); fixture.install()
            try: fixture.validate()
            except index["InvalidEvidence"]:
                raise AssertionError("wrong namespace exception handling")
            except suite["index"]["InvalidEvidence"] as exc: check(name, exc.code == code)
            else: raise AssertionError(name + " accepted")
    negative("ROLE_REGISTRY_WRITER_NOT_ROOT_REJECTED", lambda f: f.registry.update(writer_actor="source-author"), "ROLE_AUTHORITY_OPEN")
    negative("ROOT_OBSERVER_RELABEL_REJECTED", lambda f: f.registry["roles"].update(root_observer=f.auth), "INDEPENDENT_ACTOR")
    negative("MISSING_SIXTH_ROUTE_REJECTED", lambda f: f.registry["route_execution_refs"].pop(), "ROLE_PROVENANCE")
    negative("ASSEMBLER_AS_VERIFIER_REJECTED", lambda f: f.registry["roles"].update(assembler=f.review), "INDEPENDENT_ACTOR")
    temp_parent.rmdir()
    # Verify exact current source for every old receipt input other than CM39.
    receipt_evidence = []
    for key, ref in profile["LEGACY_C19_RECEIPTS"].items():
        actual = pin(R / ref["path"]); check("EXACT_OLD_C19_" + key, actual["sha256"] == ref["sha256"] and actual["bytes"] == ref["bytes"])
        receipt = read(R / ref["path"])
        versions = receipt["input_versions"]
        check("ALL_CURRENT_SOURCE_INPUTS_" + key, all(pin(R / x["path"])["sha256"] == x["sha256"] for x in versions if x["path"] != "execution/v2.4/commands.json"))
        receipt_evidence.append(dict(command_key=key, receipt_ref=actual, original_selector=receipt["selectors"], current_Source_checked=len(versions)))
    check("SOURCE_AND_PUBLIC_PINS_STILL_EXACT", all(exact(ref) for ref in unique.values()))
finally:
    cleanup = guard.close(); save("review-source-guard.final.closed.json", cleanup)
    assert cleanup.get("closed") is True and cleanup.get("retained_handles_count") == 0 and cleanup.get("verification") == "PASSED" and not cleanup.get("errors"), cleanup
save("independent-source-checks.json", dict(schema="researchos.w09-profile-v5-independent-checks.v1", actor_id="codex:/root/native_temp_independent_review", role="INDEPENDENT_NON_AUTHOR", source_hdf_ref=hdf_ref, source_mf_ref=hdf["manifest_ref"], checks=checks, historical_baseline_refs=historical, current_CP_OW_opened=False, source_copies=copied, old_C19_evidence=receipt_evidence, source_guard_ref=pin(O / "review-source-guard.final.closed.json"), source_guard_closed=True, retained_handles=0, formal_acceptance=False, parent_acceptance=False, actual_role_issuance=False, Go_Native_dispatcher_model_SQLite="NOTRUN"))
print(json.dumps(dict(status="PASS_SOURCE_ONLY", independent_checks=len(checks), inherited_finite_controls=46, new_finite_controls=57, source_guard_closed=True, retained_handles=0, current_CP_OW_opened=False, review_ref=pin(O / "independent-source-checks.json")), ensure_ascii=False))
