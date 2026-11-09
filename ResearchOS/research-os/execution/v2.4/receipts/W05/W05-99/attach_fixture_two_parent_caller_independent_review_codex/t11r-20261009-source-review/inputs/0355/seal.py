import sys
sys.dont_write_bytecode = True
import hashlib
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path

Q = Path(__file__).resolve().parent
def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def verify(item):
    actual = ref(item["path"])
    assert actual["sha256"] == item["sha256"] and actual["bytes"] == item["bytes"], "pin mismatch: " + item["path"]
def load(name):
    return json.loads((Q / name).read_text(encoding="utf-8"))
def write(name, value):
    with (Q / name).open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
def func_excerpt(path, name):
    source = Path(path).read_text(encoding="utf-8")
    lines = source.splitlines()
    starts = [n for n, line in enumerate(lines) if re.match(r"^func\s+" + re.escape(name) + r"\s*\(", line)]
    assert len(starts) == 1
    start = starts[0]
    following = [n for n in range(start + 1, len(lines)) if lines[n].startswith("func ")]
    end = following[0] if following else len(lines)
    return {"source_ref": ref(path), "function": name, "start_line": start + 1, "end_line": end,
            "lines": [{"line": n + 1, "text": lines[n]} for n in range(start, end)]}
def main():
    sp = load("source-pins.json")
    st = load("static-verification.json")
    ip = load("input-pins.json")
    for item in sp["candidate_refs"] + sp["base_refs"] + sp["production_and_contract_refs"]:
        verify(item)
    for row in ip["snapshots"]:
        verify(row["source_ref"])
        verify(row["snapshot_ref"])
    for key in ["previous_HDF_ref", "previous_MF_ref", "review_HDF_ref", "review_MF_ref"]:
        verify(sp[key])
    previous_mf = json.loads(Path(sp["previous_MF_ref"]["path"]).read_text(encoding="utf-8"))
    review_mf = json.loads(Path(sp["review_MF_ref"]["path"]).read_text(encoding="utf-8"))
    for member in previous_mf["members"] + review_mf["members"]:
        verify(member)
    assert st["exact_inverse_restores_previous_Source_bytes"]
    assert st["original_12_names_126_assertions_9_unrelated_bodies"]
    assert st["assertions_old_body_and_new_body_equal"]
    assert len(st["other_three_candidate_members_byte_equal"]) == 3
    for row in st["other_three_candidate_members_byte_equal"]:
        verify(row["previous_ref"])
        verify(row["candidate_ref"])
        assert Path(row["previous_ref"]["path"]).read_bytes() == Path(row["candidate_ref"]["path"]).read_bytes()
    for row in st["migration_checks"]:
        verify(row["actual_source_ref"])
        raw = Path(row["actual_source_ref"]["path"]).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() == row["git_blob"]
    candidate = Q / "candidate-root/internal/domain/client_session_bootstrap_test.go"
    helper = Q / "candidate-root/internal/domain/legacy_migration_fixture_test.go"
    fence = next(x for x in sp["production_and_contract_refs"] if Path(x["path"]).name == "client_session_fence.go")
    sqlite = next(x for x in sp["production_and_contract_refs"] if Path(x["path"]).name == "sqlite.go")
    deps = Q / "inputs/dependencies"
    excerpts = [
        func_excerpt(candidate, "TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction"),
        func_excerpt(helper, "legacyTranscriptFixtureDatabase"),
        func_excerpt(helper, "useLegacyTranscriptFixture"),
        func_excerpt(helper, "applyLegacyFixtureMigration"),
        func_excerpt(fence["path"], "installClientSessionFence"),
        func_excerpt(sqlite["path"], "Open"),
        func_excerpt(sqlite["path"], "Bootstrap"),
        func_excerpt(deps / "domain_test.go", "setupWithConstructor"),
        func_excerpt(deps / "context_test.go", "contextFixtureFrom"),
    ]
    write("call-chain-excerpts.json", {"authority": "NONE", "static_only": True,
          "runtime_reachability_proven": False, "checks": st["call_chain_checks"], "excerpts": excerpts})
    original = load("inputs/previous-source/verification.json")
    previous_hdf = load("inputs/previous-source/HANDOFF.json")
    failure833 = load("inputs/previous-source/failure-origin.833.json")
    assert failure833["ordinal"] == 833 and failure833["actual_Python_exit"] == 1
    assert failure833["actual_native_exit"] is None
    assert previous_hdf["failures"]["assigned_ordinal"] == 833
    review_findings = load("inputs/review/findings.json")
    assert review_findings["verdict"] == "REQUEST_CHANGES"
    assert [x["id"] for x in review_findings["important"]] == ["LEGACY-ROLLBACK-001"]
    verify(original["original_FULL_raw_ref"])
    write("failure-and-review-history.json", {
        "authority": "NONE",
        "previous_failure833_snapshot_ref": ref(Q / "inputs/previous-source/failure-origin.833.json"),
        "previous_source_reported_833": True,
        "previous_failure833_actual_Python_outer_exit": 1,
        "previous_failure833_native_exit": None,
        "earlier826_and_all_history_not_reset": True,
        "independent_REQUEST_CHANGES_ref": ref(Q / "inputs/review/findings.json"),
        "finding_fixed_in_Source_candidate_only": "LEGACY-ROLLBACK-001",
        "finding_acceptance_pending_independent_review": True,
        "original_FULL_raw_ref": original["original_FULL_raw_ref"],
        "original_failed_nodes_preserved": original["original_failed_nodes_preserved"],
        "FULL1261_PASS_25_FAIL_4_SKIP_not_reclassified": True,
        "new_v2_mechanical_errors": 0,
        "no_failure_count_reset": True,
    })
    handoff = {
        "schema": "researchos.source-revision-handoff.v1",
        "created_at": datetime.now(timezone.utc).isoformat(), "namespace": str(Q),
        "authority": "NONE", "formal_acceptance": False,
        "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW",
        "finding": "LEGACY-ROLLBACK-001",
        "revision": "v2: schema-only rollback database binding",
        "previous_source_HDF_ref": sp["previous_HDF_ref"],
        "previous_source_MF_ref": sp["previous_MF_ref"],
        "independent_request_changes_HDF_ref": sp["review_HDF_ref"],
        "independent_request_changes_MF_ref": sp["review_MF_ref"],
        "candidate_refs": sp["candidate_refs"],
        "base_refs": sp["base_refs"],
        "minimal_diff_ref": st["minimal_diff_ref"],
        "report_ref": ref(Q / "report.md"),
        "source_pins_ref": ref(Q / "source-pins.json"),
        "input_pins_ref": ref(Q / "input-pins.json"),
        "static_verification_ref": ref(Q / "static-verification.json"),
        "call_chain_excerpts_ref": ref(Q / "call-chain-excerpts.json"),
        "failure_and_review_history_ref": ref(Q / "failure-and-review-history.json"),
        "original_tool_io_ref": ref(Q / "tool-io.json"),
        "unchanged_other_three_candidates": st["other_three_candidate_members_byte_equal"],
        "static_preservation": {"original_Test_names": 12, "original_assertion_calls": 126,
                               "original_unrelated_bodies_byte_equal": 9,
                               "previous_all_Test_names_unchanged": True,
                               "all_other_previous_Test_bodies_unchanged": True,
                               "exact_inverse_reproduces_previous_Source_bytes": True,
                               "no_Go_AST_or_runtime_proof": True},
        "call_chain_static_checks": st["call_chain_checks"],
        "historical_resources": {"commit": st["historical_commit"], "DDL_blob": st["DDL_git_blob"],
                                "numbered_sql_count": 20, "numbered_migration_source_changes": 0,
                                "historical_DDL_changes": 0, "release_authority_created": False,
                                "history_resource_refs": sp["history_resource_refs"]},
        "ordinary": "BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE",
        "component_acceptance": "NOT_RUN; synthetic fixtures; Root independent actual required",
        "execution": {"fixed_Python_flags": "-I -S -B -X utf8",
                      "metadata_read_and_build_actual_exit": 0,
                      "ROOT_PYTHON_EXIT_sentinels": "0",
                      "seal_current_invocation_exit_pending_postseal_IO": True,
                      "Go_AST": None, "Go": None, "gofmt": None, "compiler": None,
                      "SQL": None, "native_product": None, "model": None,
                      "private_credentials": None},
        "write_scope": {"unique_v2_namespace_only": True, "changed_existing_test_files": 1,
                        "production": 0, "Main": 0, "T5": 0, "T6": 0, "canonical": 0,
                        "old_source_package": 0, "old_independent_review_package": 0,
                        "baseline_lock_held": False},
        "failure_history": {"mechanical_errors_new_v2": 0, "prior833_preserved": True,
                            "prior826_and_FULL_preserved": True, "counts_reset": False,
                            "Root_newer_global_835_to838_not_affected_by_this_Source_branch": True},
        "next_actor": "Independent reviewer for this new v2; Root fresh guarded compile/component actual after review",
        "manifest_exclusions": {"MF.json": "self fingerprint",
                                "postseal-tool-io.json": "later seal/write invocation result, separately pinned for Root"},
    }
    write("HDF.json", handoff)
    members = []
    for p in sorted(Q.rglob("*")):
        if p.is_file() and p.name not in {"MF.json", "postseal-tool-io.json"}:
            members.append({"relative_path": p.relative_to(Q).as_posix(), **ref(p)})
    write("MF.json", {"schema": "researchos.source-revision-manifest.v1", "authority": "NONE",
          "formal_acceptance": False, "status": handoff["status"], "members": members,
          "exclusions": handoff["manifest_exclusions"]})
    for member in members:
        verify(member)
    print(json.dumps({"authority": "NONE", "formal_acceptance": False, "status": handoff["status"],
           "refs": {name: ref(Q / name) for name in [
               "HDF.json", "MF.json", "report.md", "source-pins.json", "static-verification.json",
               "call-chain-excerpts.json", "failure-and-review-history.json", "tool-io.json"]},
           "candidate_refs": sp["candidate_refs"], "minimal_diff_ref": st["minimal_diff_ref"],
           "member_count": len(members), "ordinary": "BLOCKED", "new_mechanical_errors": 0,
           "prior833_826_and_REQUEST_CHANGES_preserved": True}, ensure_ascii=False))
exit_code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    exit_code = 1
finally:
    print("ROOT_PYTHON_EXIT=" + str(exit_code))
sys.exit(exit_code)

