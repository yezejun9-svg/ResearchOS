"""One-shot Source preparation check. Never builds or activates a Root scope."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "register_cp370.source.py"


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path = HERE / name
    with path.open("xb") as out:
        out.write(raw)
        out.flush()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def main():
    ast.parse(SOURCE.read_bytes(), str(SOURCE))
    ns = runpy.run_path(str(SOURCE), run_name="registrar_source_prepared_only")
    before, cp, ow = ns["check_before_pair"]()
    checks = []
    pending = []
    for row in cp["work_in_progress"]["later_diagnostics_observed_after_cutoff"]:
        pending.append(dict(row, actual_outer_exit=None, actual_python_exit=None,
                            actual_native_exit=None))
    live = dict(schema="researchos.root-postseal-live-diagnostic-context.v1",
                issued_by="codex:/root", created_utc="SYNTHETIC_NONAUTHORITATIVE",
                source_cutoff={"highest_ordinal": 965, "next_failure_ordinal": 966},
                next_original_failure_ordinal=970, pending=pending)
    ns["validate_live"](live)
    checks.append("synthetic_in_memory_live_shape_positive_only")
    cases = {
        "bool_exit": lambda d: d["pending"][0].__setitem__("actual_outer_exit", False),
        "float_exit": lambda d: d["pending"][0].__setitem__("actual_python_exit", 0.0),
        "bool_next": lambda d: d.__setitem__("next_original_failure_ordinal", True),
        "null_pending": lambda d: d.__setitem__("pending", None),
        "missing_ordinal": lambda d: d["pending"].pop(1),
        "duplicate_ordinal": lambda d: d["pending"][1].__setitem__("ordinal", 966),
        "changed_origin_hash": lambda d: d["pending"][0]["origin_ref"].__setitem__(
            "sha256", "0" * 64),
        "extra_live_field": lambda d: d.__setitem__("formal_acceptance", True),
        "reset_to_966": lambda d: d.__setitem__("next_original_failure_ordinal", 966),
    }
    for name, mutate in cases.items():
        candidate = copy.deepcopy(live)
        mutate(candidate)
        try: ns["validate_live"](candidate)
        except (ValueError, TypeError, KeyError): checks.append("reject_" + name)
        else: raise AssertionError("SYNTHETIC_NEGATIVE_NOT_REJECTED:" + name)
    for name, ref in (("bool_bytes", {"path": str(SOURCE), "sha256": ns["pin"](SOURCE)["sha256"], "bytes": True}),
                      ("extra_ref_field", dict(ns["pin"](SOURCE), grant=True))):
        try: ns["exact_ref"](ref)
        except (ValueError, TypeError): checks.append("reject_" + name)
        else: raise AssertionError("SYNTHETIC_REF_NOT_REJECTED:" + name)
    held = [*before, ns["pin"](SOURCE), ns["pin"](__file__),
            ns["pin"](HERE / "ROOT_BUILDER_CONTRACT.source.md"),
            *[ns["pin"](path) for path in (ns["BASE"], ns["GP"], ns["TP"], sys.executable)]]
    guard, count = ns["held_guard"](held, exclude_pair=False)
    cleanup = guard.close()
    assert cleanup["verification"] == "PASSED" and cleanup["closed"] is True
    assert cleanup["retained_handles_count"] == 0 and cleanup["errors"] == []
    cleanup_ref = save("source-guard.cleanup.prepared.json", cleanup)
    result = dict(schema="researchos.w09-cp370-registrar-source-prepared-check.v1",
                  status="SOURCE_PREPARED_REVIEW_INPUTS_MISSING",
                  synthetic_controls_non_authoritative=checks,
                  synthetic_control_count=len(checks),
                  source_guard_ref_count=count, source_guard_closed=True,
                  source_guard_retained_handles=0, source_guard_cleanup_ref=cleanup_ref,
                  current_before_canonical_refs=before,
                  registrar_source_ref=ns["pin"](SOURCE),
                  root_builder_contract_ref=ns["pin"](HERE / "ROOT_BUILDER_CONTRACT.source.md"),
                  verify_script_ref=ns["pin"](__file__),
                  final_caller_independent_review="MISSING",
                  Scope="NOT_GENERATED", registration_facts="NOT_GENERATED",
                  Canon="UNCHANGED", actual_dispatchers_run=False,
                  formal_acceptance=False, parent_acceptance=False,
                  formal_case_accepted_delta=0)
    print(json.dumps(save("source-prepared-verification.json", result), ensure_ascii=False))


if __name__ == "__main__": main()
