"""Read-only Source qualification controls. Synthetic inputs never grant Root authority."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "register_cp370.source.py"
OLD = HERE.parent / "cp370proposal-20261009"
REVIEW = HERE.parent.parent / "cp370_prepared_definition_independent_review_codex/preparedr-01a12072"
CALLER = HERE.parent.parent / "w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v6"
CALLER_REVIEW = HERE.parent.parent / "main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009"
ROOT_INPUT = HERE.parent.parent / "checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009"
QUAL = ROOT_INPUT / "original-diagnostic-qualifications.seed.live996.root.json"
SEED_WITNESS = ROOT_INPUT / "seed.actual-observation-witness.live996.root.json"


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    path = HERE / name
    with path.open("xb") as out: out.write(raw)
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def main():
    ns = runpy.run_path(str(SOURCE), run_name="cp370_v2_synthetic_controls")
    outcomes = []
    def pass_case(name): outcomes.append({"name": name, "result": "PASS", "SyntheticNonAuthoritative": True})
    def reject(name, callback, code):
        try: callback()
        except ValueError as error:
            if str(error) != code: raise AssertionError((name, str(error), code)) from error
            pass_case(name + ":" + code)
        else: raise AssertionError("BAD_INPUT_ACCEPTED:" + name)

    before, cp, ow = ns["check_before_pair"]()
    assert cp["revision"] == 369 and ow["revision"] == 173
    pass_case("actual_before_canonical_four_byte_pins_read_only")
    assert ns["pin"](OLD / "register_cp370.source.py")["sha256"] == (
        "981ac827ca2c2eca27815580c3c2bbb5d958feba7e78d135b18049ea95f1d793")
    assert ns["pin"](REVIEW / "findings.final.json")["sha256"] == (
        "02357c4d4c933e2e6c6cba5530463ea39d967f99c19a4ea04e620e612b329b37")
    pass_case("prior_sealed_source_and_five_findings_exact")

    caller = ns["ensure_caller_source"](ns["pin"](CALLER / "HDF.json"),
                                         ns["pin"](CALLER / "MF.json"))
    review_manifest = json.loads((CALLER_REVIEW / "MF.json").read_bytes())
    decision_ref = ns["pin"](CALLER_REVIEW / "source-decision.json")
    ns["validate_review_members"](review_manifest, decision_ref, caller)
    pass_case("real_v6_review_manifest_member_and_source_bindings")
    for label, changed in (("empty_review_members", dict(review_manifest, members=[])),
                           ("wrong_source_hdf", dict(review_manifest, source_hdf_ref=caller[1])),
                           ("wrong_source_mf", dict(review_manifest, source_mf_ref=caller[0]))):
        reject(label, lambda changed=changed: ns["validate_review_members"](
            changed, decision_ref, caller), "REVIEW_MANIFEST_NOT_BOUND")
    ns["validate_reviewer_actor"]("codex:/root/native_temp_independent_review")
    pass_case("exact_designated_non_author_actor")
    for actor in ("/root", "", False, ["codex:/root/native_temp_independent_review"],
                  "codex:/root", "codex:/root/w09_formal_profile_source_impl"):
        reject("fake_or_alias_reviewer_" + type(actor).__name__,
               lambda actor=actor: ns["validate_reviewer_actor"](actor),
               "REVIEWER_NOT_CANONICAL_NONAUTHOR")

    qualification = json.loads(QUAL.read_bytes())
    assert ns["pin"](QUAL)["sha256"] == (
        "29ccebbd4fa089e2bb579b8cbbfe7253b14d5b2364f1c5f26895e7cbbe91f81d")
    original_pending = json.loads(Path(qualification["source_pending_ref"]["path"]).read_bytes())["pending"]
    pending = [{key: row[key] for key in ("ordinal", "origin_ref", "description")}
               for row in original_pending]
    seed = {"schema": "researchos.root-cp370-source-live-context.v2",
            "issued_by": "codex:/root", "root_thread_id": ns["ROOT_THREAD_ID"],
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_cutoff": qualification["source_cutoff"],
            "next_original_failure_ordinal": qualification["next_original_failure_ordinal"],
            "pending": pending, "qualification_ref": ns["pin"](QUAL),
            "seed_witness_ref": ns["pin"](SEED_WITNESS)}
    qualified = ns["validate_qualification"](qualification, seed)
    assert len(qualified) == 30 and qualified[966]["actual_outer_exit"] == 0
    assert qualified[967]["actual_outer_exit"] == 1
    assert qualified[967]["actual_native_exit"] is None
    assert qualified[987]["actual_outer_exit"] is None
    pass_case("actual_root_qualification_30_rows_read_only_no_authority_grant")
    ns["validate_live"](seed, "source")
    pass_case("actual_root_seed_host_three_original_audit_ranges_read_only")
    witness, witness_refs = ns["validate_root_witness"](seed["seed_witness_ref"], seed, "SEED")
    assert witness["registrar_review_refs"] == [] and len(witness_refs) == 4
    pass_case("actual_seed_witness_carries_zero_registrar_review_refs")
    assert qualified[971]["origin_ref"] == qualified[972]["origin_ref"]
    assert qualified[971]["origin_selector"] != qualified[972]["origin_selector"]
    pass_case("shared_original_file_distinct_selectors_legal")
    for name, mutate, code in (
        ("bool_outer_exit", lambda q: q["rows"][0].__setitem__("actual_outer_exit", False),
         "QUALIFICATION_EXIT_TYPED"),
        ("float_native_exit", lambda q: q["rows"][1].__setitem__("actual_native_exit", 0.0),
         "QUALIFICATION_EXIT_TYPED"),
        ("wrong_original_selector", lambda q: q["rows"][0]["exit_qualification"].__setitem__(
            "source_capture_selector", "other"), "ORIGINAL_EXIT_QUALIFICATION_NOT_BOUND"),
        ("counter_reset", lambda q: q.__setitem__("counter_reset", True),
         "QUALIFICATION_ROOT_AND_CUTOFF"),
        ("fake_origin_ref", lambda q: q["rows"][0].__setitem__("origin_ref", q["rows"][1]["origin_ref"]),
         "QUALIFICATION_INVOCATION_IDENTITY"),
    ):
        candidate = copy.deepcopy(qualification)
        mutate(candidate)
        reject(name, lambda candidate=candidate: ns["validate_qualification"](candidate, seed), code)
    pair = [copy.deepcopy(qualified[971]), copy.deepcopy(qualified[972])]
    pair[1]["origin_selector"] = pair[0]["origin_selector"]
    reject("same_origin_same_selector_rejected_independently",
           lambda: ns["validate_invocation_identities"](pair),
           "ORIGINAL_INVOCATION_REUSED")
    changed_source_selector = copy.deepcopy(qualification)
    changed_source_selector["rows"][972-966]["origin_selector"] = qualified[971]["origin_selector"]
    reject("sealed_original_selector_cannot_be_rewritten",
           lambda: ns["validate_qualification"](changed_source_selector, seed),
           "PRIOR_ORIGINAL_EXIT_OR_SELECTOR_CHANGED")
    bad_live = copy.deepcopy(seed)
    bad_live["pending"][0]["actual_outer_exit"] = 0
    reject("source_live_cannot_self_assert_numeric_exit",
           lambda: ns["validate_live"](bad_live, "source"), "LIVE_ROW_TYPED")
    fresh_q = copy.deepcopy(qualified)
    fresh_q[967]["actual_outer_exit"] = 0
    reject("failed_outer_one_cannot_turn_zero_after_seal",
           lambda: ns["validate_qualification_continuity"](seed, qualified, seed, fresh_q),
           "SOURCE_ORIGINALS_CHANGED_AFTER_SEAL")
    fresh_q = copy.deepcopy(qualified)
    fresh_q[987]["actual_outer_exit"] = 0
    reject("unknown_outer_null_cannot_turn_zero_after_seal",
           lambda: ns["validate_qualification_continuity"](seed, qualified, seed, fresh_q),
           "SOURCE_ORIGINALS_CHANGED_AFTER_SEAL")

    ns["validate_postseal_times"]("2026-10-09T12:00:00Z", "2026-10-09T12:10:00Z",
                                  "2026-10-09T12:11:00Z", "2026-10-09T12:12:00Z")
    pass_case("synthetic_postreview_witness_fresh_order_only")
    for name, values in (("witness_before_review", ("12:00", "12:10", "12:09", "12:12")),
                         ("early_context_reused", ("12:00", "12:10", "12:11", "12:00"))):
        values = tuple("2026-10-09T" + value + ":00Z" for value in values)
        reject(name, lambda values=values: ns["validate_postseal_times"](*values),
               "POSTSEAL_WITNESS_TIME_ORDER")
    reject("null_fresh_time", lambda: ns["validate_postseal_times"](
        "2026-10-09T12:00:00Z", "2026-10-09T12:10:00Z",
        "2026-10-09T12:11:00Z", None), "UTC_TIME_TYPE")

    boundary = ns["ROOT_OUTPUT_BOUNDARY"]
    child = boundary / "synthetic-root-caller-output"
    assert ns["canonical_output_root"](str(child)) == str(child.resolve())
    pass_case("strict_canonical_output_child")
    for label, path in (("receipt_boundary", boundary),
                        ("dotdot_boundary_alias", boundary / "SYNTHETIC_NOT_CREATED" / ".."),
                        ("outside_boundary", boundary.parent),
                        ("relative_path", Path("relative"))):
        reject(label, lambda path=path: ns["canonical_output_root"](str(path)),
               "OUTPUT_ROOT_SCOPE")

    sources = [*before, ns["pin"](SOURCE), ns["pin"](__file__), *witness_refs,
               ns["pin"](HERE / "ROOT_BUILDER_CONTRACT.source.md"), ns["pin"](QUAL),
               ns["pin"](qualification["source_pending_ref"]["path"]),
               ns["pin"](CALLER / "HDF.json"), ns["pin"](CALLER / "MF.json"),
               ns["pin"](CALLER_REVIEW / "HDF.json"), ns["pin"](CALLER_REVIEW / "MF.json"),
               ns["pin"](CALLER_REVIEW / "source-decision.json"),
               ns["pin"](REVIEW / "HDF.json"), ns["pin"](REVIEW / "MF.json"),
               ns["pin"](REVIEW / "findings.final.json"),
               *[ns["pin"](p) for p in (ns["BASE"], ns["GP"], ns["TP"], sys.executable)]]
    sources.extend(row["origin_ref"] for row in pending)
    guard, count = ns["held_guard"](sources, exclude_pair=False)
    cleanup = guard.close()
    assert cleanup["verification"] == "PASSED" and cleanup["closed"] is True
    assert cleanup["retained_handles_count"] == 0 and cleanup["errors"] == []
    cleanup_ref = save("source-guard.cleanup.controls.json", cleanup)
    result = {"schema": "researchos.w09-cp370-registrar-v2-source-controls.v1",
              "SyntheticNonAuthoritative": True, "actual_registrar_run": False,
              "RootScopeCreated": False, "CanonWritten": False,
              "source_controls_passed": len(outcomes), "source_controls_failed": 0,
              "controls": outcomes, "guard_refs": count,
              "guard_closed": True, "guard_retained_handles": 0,
              "guard_cleanup_ref": cleanup_ref,
              "formal_acceptance": False, "parent_acceptance": False,
              "formal_case_accepted_delta": 0}
    print(json.dumps(save("source-controls.result.json", result), ensure_ascii=False))


if __name__ == "__main__": main()
