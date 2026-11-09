"""One-time Source-only sealer; no dispatcher, Native, Go or provider calls."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\作品集\ResearchOS\research-os")
PKG = Path(r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4")
GUARD = ROOT / "execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
HELPER = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
REVIEW = ROOT / "execution/v2.4/receipts/W09/W09-99/main_c19_native_actual_independent_review_codex/review-1a12035-v2"
S369 = ROOT / "execution/v2.4/receipts/W09/W09-99/checkpoint_r369_native_source_root/cp369-c19-20261009"
V4_REVIEW = ROOT / "execution/v2.4/receipts/W09/W09-99/main_c19_dispatcher_caller_independent_review_codex/c19v4-review-20261009"


def pin(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def save(name, data):
    path = HERE / name
    with path.open("xb") as file:
        file.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return pin(path)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assert not (HERE / "HDF.json").exists() and not (HERE / "MF.json").exists()
source = HERE / "main_c19_consumer_caller.source.py"
controls = HERE / "source_controls.py"
ast.parse(source.read_bytes())
ast.parse(controls.read_bytes())
result = json.loads((HERE / "source-controls.result.json").read_bytes())
assert result["failed"] == 0 and result["passed"] == 36 and result["synthetic_non_authoritative"] is True
candidate = load(source, "w09_c19_source_to_seal")
assert candidate.frozen_plan()["sha256"] == "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17"
assert len(candidate.selected_registry(candidate.frozen_plan())) == 2
assert len(candidate.qualified_modes()[2]) == 2
assert pin(GUARD)["sha256"] == "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(HELPER)["sha256"] == "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
helper = load(HELPER, "w09_c19_helper_to_seal")
guard_module = load(GUARD, "w09_c19_guard_to_seal")
refs = [pin(p) for p in (
    source, controls, HERE / "source-controls.result.json", HERE / "root-calling-contract.source.json",
    HERE / "source-original-observations.json", __file__,
    GUARD, HELPER, REVIEW / "HDF.json", REVIEW / "MF.json",
    REVIEW / "two-consumer-mode-interface.json", REVIEW / "actual-decision.json",
    V4_REVIEW / "HDF.json", V4_REVIEW / "MF.json", V4_REVIEW / "findings.json",
    V4_REVIEW / "source-decision.json",
    S369 / "Main-C19-actual-handoff.root.json", S369 / "Main-C19-single-native-request.actual.root.json",
    PKG / "contracts/execution.plan.json", ROOT / "execution/command_dispatcher/dispatch.py",
    ROOT / "ops/ci/w09_formal_router.py", ROOT / "ops/ci/w09_evidence_closure.py",
    ROOT / "execution/toolchains/locked.json", ROOT / "execution/project_identity.json",
    ROOT / "execution/v2.4/checkpoint.json", ROOT / "execution/v2.4/path_ownership.json",
    ROOT / "execution/v2.4/step_state.json", ROOT / "execution/v2.4/commands.json",
    ROOT / "execution/v2.4/current_spec.json",
    Path(sys.executable))]
interface = json.loads((REVIEW / "two-consumer-mode-interface.json").read_bytes())
for row in interface["modes"]:
    refs += [pin(row["independent_review_ref"]["path"]), pin(row["mode_decision_ref"]["path"])]
refs += [pin(ROOT / interface["native_report_ref"]), pin(ROOT / interface["native_tool_run_ref"])]
refs += [pin(p) for p in helper.runtime_resource_paths()]
for module in list(sys.modules.values()):
    for field in ("__file__", "__cached__"):
        path = getattr(module, field, None)
        if path and Path(path).is_file(): refs.append(pin(path))
dedup = {}
for ref in refs:
    key = ref["path"].casefold()
    assert key not in dedup or dedup[key] == ref
    dedup[key] = ref
refs = list(dedup.values())
vector_ref = save("source-input-pins.json", {
    "schema": "researchos.w09-c19-two-consumer-source-inputs.v1",
    "source_only": True, "refs": refs, "count": len(refs),
    "native_historical_cp": 369, "consumer_future_cp": 370,
    "formal_case_accepted_delta": 0})
guard = guard_module.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
try:
    guard.acquire([*refs, vector_ref])
finally:
    cleanup = guard.close()
assert cleanup["closed"] is True and cleanup["retained_handles_count"] == 0
assert cleanup["errors"] == [] and cleanup["verification"] == "PASSED"
cleanup_ref = save("source-guard.cleanup.json", cleanup)
mf = {"schema": "researchos.w09-c19-two-consumer-source-manifest.v1",
      "caller_source_ref": pin(source), "contract_ref": pin(HERE / "root-calling-contract.source.json"),
      "controls_source_ref": pin(controls), "controls_result_ref": pin(HERE / "source-controls.result.json"),
      "original_observations_ref": pin(HERE / "source-original-observations.json"),
      "v4_independent_request_changes_ref": pin(V4_REVIEW / "HDF.json"),
      "input_vector_ref": vector_ref, "source_guard_cleanup_ref": cleanup_ref,
      "sealer_ref": pin(__file__), "ref_count": len(refs) + 1,
      "source_guard_closed": True, "source_guard_retained_handles": 0,
      "actual_consumers_run": False, "formal_acceptance": False,
      "formal_case_accepted_delta": 0, "parent_acceptance": False,
      "inverse": "New receipt namespace only; remove exact new bytes to invert. No Main or Canon before bytes changed."}
mf_ref = save("MF.json", mf)
hdf = {"schema": "researchos.w09-c19-two-consumer-caller-source-handoff.v1",
       "status": "SOURCE_ONLY_PENDING_ROOT_REGISTRATION",
       "actor": "codex:/root/w09_formal_profile_source_impl",
       "caller_source_ref": pin(source), "manifest_ref": mf_ref,
       "root_contract_ref": mf["contract_ref"],
       "source_controls_ref": mf["controls_result_ref"],
       "original_observations_ref": mf["original_observations_ref"],
       "v4_review_ref": mf["v4_independent_request_changes_ref"],
       "source_guard_cleanup_ref": cleanup_ref,
       "native_qualified_hdf_ref": pin(REVIEW / "HDF.json"),
       "native_handoff_ref": pin(S369 / "Main-C19-actual-handoff.root.json"),
       "frozen_plan_ref": pin(PKG / "contracts/execution.plan.json"),
       "source_review": "OPEN_INDEPENDENT_REVIEW_REQUIRED",
       "CP370_registration": "NOT_YET_REGISTERED",
       "actual_consumer_executed": False, "native_producer_rerun": False,
       "registry_writes": False, "canonical_writes": False,
       "formal_dispatcher_actual_grant": False,
       "formal_acceptance": False, "formal_case_accepted_delta": 0, "parent_acceptance": False,
       "stop": "FINAL_SOURCE_ONLY"}
hdf_ref = save("HDF.json", hdf)
print(json.dumps({"HDF": hdf_ref, "MF": mf_ref, "guard_ref_count": len(refs)+1,
                  "guard_closed": True, "formal_case_accepted_delta": 0}, ensure_ascii=False))
