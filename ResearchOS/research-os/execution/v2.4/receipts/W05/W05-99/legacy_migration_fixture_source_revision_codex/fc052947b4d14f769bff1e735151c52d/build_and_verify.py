import sys
sys.dont_write_bytecode = True
import ast
import collections
import difflib
import hashlib
import json
import re
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent
OLD = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9")
REVIEW = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_independent_review_codex/4ec609adce7346a9b8fe61e898a8a15e")
TARGET = "TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction"
def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def verify(item):
    actual = ref(item["path"])
    assert actual["sha256"] == item["sha256"] and actual["bytes"] == item["bytes"], "pin mismatch: " + item["path"]
def write(name, value):
    p = Q / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
def main():
    inputs = json.loads((Q / "input-pins.json").read_text(encoding="utf-8"))
    for row in inputs["snapshots"]:
        verify(row["source_ref"])
        verify(row["snapshot_ref"])
    mf = json.loads((REVIEW / "MF.json").read_text(encoding="utf-8"))
    utility_ref = next(x for x in mf["members"] if x["relative_path"] == "review.py")
    verify(utility_ref)
    utility_source = Path(utility_ref["path"]).read_text(encoding="utf-8")
    tree = ast.parse(utility_source)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"masked", "funcs", "assertions"}]
    assert {n.name for n in selected} == {"masked", "funcs", "assertions"}
    scope = {"re": re, "collections": collections}
    for n in selected:
        exec(compile(ast.Module(body=[n], type_ignores=[]), utility_ref["path"], "exec"), scope)
    funcs = scope["funcs"]
    assertions = scope["assertions"]
    masked = scope["masked"]

    snapshot_root = Q / "inputs/previous-source/candidate-root"
    old_file = snapshot_root / "internal/domain/client_session_bootstrap_test.go"
    old_raw = old_file.read_bytes()
    old_text = old_raw.decode("utf-8")
    old_body = funcs(old_text)[TARGET]
    before = "\tf := setup(t)\n\tctx := context.Background()\n\tif err := useLegacyTranscriptFixture(t, f); err != nil {"
    after = "\tctx := context.Background()\n\tdb, err := legacyTranscriptFixtureDatabase(t)\n\tif err != nil {"
    assert old_body.count(before) == 1
    new_body = old_body.replace(before, after, 1)
    assert new_body.count("f.db.Begin()") == 1
    assert new_body.count("f.db.QueryRow(") == 1
    new_body = new_body.replace("f.db.Begin()", "db.Begin()", 1)
    new_body = new_body.replace("f.db.QueryRow(", "db.QueryRow(", 1)
    assert "f." not in masked(new_body)
    assert "useLegacyTranscriptFixture" not in new_body
    assert old_text.count(old_body) == 1
    new_text = old_text.replace(old_body, new_body, 1)
    inverse_body = new_body.replace(after, before, 1).replace("db.Begin()", "f.db.Begin()", 1).replace("db.QueryRow(", "f.db.QueryRow(", 1)
    assert inverse_body == old_body
    assert new_text.replace(new_body, old_body, 1).encode("utf-8") == old_raw

    candidate_root = Q / "candidate-root"
    candidate_root.mkdir(exist_ok=False)
    old_candidates = json.loads((Q / "inputs/previous-source/construction.json").read_text(encoding="utf-8"))["member_refs"]
    candidates = []
    equal_other_members = []
    for item in old_candidates:
        source = Path(item["path"])
        verify(item)
        relative = source.relative_to(OLD / "candidate-root")
        target = candidate_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = new_text.encode("utf-8") if relative.as_posix() == "internal/domain/client_session_bootstrap_test.go" else source.read_bytes()
        with target.open("xb") as f:
            f.write(raw)
        candidates.append(ref(target))
        if relative.as_posix() != "internal/domain/client_session_bootstrap_test.go":
            assert target.read_bytes() == source.read_bytes()
            equal_other_members.append({"relative_path": relative.as_posix(), "previous_ref": item, "candidate_ref": ref(target)})

    source_pins = json.loads((Q / "inputs/previous-source/source-pins.json").read_text(encoding="utf-8"))
    for item in source_pins["base_refs"] + source_pins["production_and_contract_refs"]:
        verify(item)
    comparisons = []
    original_names = []
    unrelated_equal = []
    for base in source_pins["base_refs"]:
        source = Path(base["path"]).read_text(encoding="utf-8")
        candidate = (candidate_root / "internal/domain" / Path(base["path"]).name).read_text(encoding="utf-8")
        af, bf = funcs(source), funcs(candidate)
        aa, ba = assertions(source), assertions(candidate)
        assert set(af) <= set(bf)
        assert not (aa - ba)
        equal = [name for name in af if af[name] == bf[name]]
        unrelated_equal.extend(equal)
        original_names.extend(af)
        comparisons.append({"base_ref": base, "candidate_ref": ref(candidate_root / "internal/domain" / Path(base["path"]).name),
                            "original_Test_names": list(af), "candidate_Test_names": list(bf),
                            "original_assertion_call_count": aa.total(), "candidate_assertion_call_count": ba.total(),
                            "missing_original_assertions": list((aa-ba).elements()),
                            "original_equal_bodies": equal})
    assert len(original_names) == 12
    assert sum(c["original_assertion_call_count"] for c in comparisons) == 126
    assert len(unrelated_equal) == 9
    old_funcs, new_funcs = funcs(old_text), funcs(new_text)
    assert set(old_funcs) == set(new_funcs)
    assert all(old_funcs[name] == new_funcs[name] for name in old_funcs if name != TARGET)
    assert assertions(old_body) == assertions(new_body)
    assert assertions(old_text) == assertions(new_text)
    assert len(equal_other_members) == 3

    helper = (candidate_root / "internal/domain/legacy_migration_fixture_test.go").read_text(encoding="utf-8")
    ddl = (candidate_root / "internal/domain/testdata/pretranscript-3225a31f.sql").read_bytes()
    assert hashlib.sha256(ddl).hexdigest() == "3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a"
    assert hashlib.sha1(b"blob " + str(len(ddl)).encode("ascii") + b"\0" + ddl).hexdigest() == "9efc768f8f4cfb6ac31e1f88a78ad095877328af"
    migrations = json.loads((Q / "inputs/previous-source/migration-resources.json").read_text(encoding="utf-8"))
    migration_checks = []
    for item in migrations["migration_sources"]:
        verify(item["actual_source_ref"])
        raw = Path(item["actual_source_ref"]["path"]).read_bytes()
        actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        assert actual_blob == item["git_blob"]
        migration_checks.append({"version": item["version"], "git_path": item["git_path"], "git_blob": actual_blob,
                                 "actual_source_ref": item["actual_source_ref"]})
    assert [x["version"] for x in migration_checks] == list(range(1, 21))
    def balanced(source):
        stack = []
        pairs = {")": "(", "]": "[", "}": "{"}
        for c in masked(source):
            if c in "([{":
                stack.append(c)
            elif c in ")]}":
                assert stack and stack.pop() == pairs[c]
        return not stack
    for p in candidate_root.rglob("*.go"):
        assert balanced(p.read_text(encoding="utf-8"))

    fence_ref = next(x for x in source_pins["production_and_contract_refs"] if Path(x["path"]).name == "client_session_fence.go")
    fence = Path(fence_ref["path"]).read_text(encoding="utf-8")
    assert "if restored {" in fence
    assert "if present == 0 {" in fence
    assert "ALTER TABLE client_sessions ADD COLUMN transcript_artifact_id TEXT" in fence
    assert "CREATE TRIGGER IF NOT EXISTS client_session_epoch_no_regression" in fence
    assert "CREATE TRIGGER IF NOT EXISTS client_session_require_fresh" in fence
    assert "t.Cleanup(func() { _ = db.Close() })" in helper
    assert "applyLegacyFixtureMigrationRange(context.Background(), db, 2, 20)" in helper
    assert "return db, nil" in helper
    checks = {
        "schema_only_database_no_Project_copy": "legacyTranscriptFixtureDatabase(t)" in new_body and "setup(t)" not in new_body,
        "same_db_begin_and_postrollback_query": "tx, err := db.Begin()" in new_body and "db.QueryRow(" in new_body,
        "explicit_and_deferred_tx_rollback_kept": "defer tx.Rollback()" in new_body and "if err = tx.Rollback(); err != nil {" in new_body,
        "original_transaction_install_and_column_checks_kept": "installClientSessionFence(ctx, tx, false)" in new_body and "count != 1" in new_body and "count != 0" in new_body,
        "helper_registers_local_db_close_cleanup": True,
        "historical1_to20_then_pinned_oldDDL_unchanged": True,
        "fence_restored_false_skips_Run_barrier_seed": True,
        "empty_session_fixture_requires_no_Project_Run_inserts": "INSERT" not in new_body,
        "production_fence_epoch_triggers_retained": True,
        "rejection_gate_and_source_pin_errors_retained": True,
        "runtime_reachability_proven": False,
        "static_reachability_precondition_conflict_removed": True,
    }
    assert all(value for key, value in checks.items() if key != "runtime_reachability_proven")
    diff = "".join(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True),
                  fromfile="previous-source/candidate-root/internal/domain/client_session_bootstrap_test.go",
                  tofile="v2/candidate-root/internal/domain/client_session_bootstrap_test.go"))
    diff_path = Q / "diffs/LEGACY-ROLLBACK-001.diff"
    diff_path.parent.mkdir(exist_ok=False)
    with diff_path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(diff)
    result = {
        "authority": "NONE", "formal_acceptance": False, "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW",
        "finding": "LEGACY-ROLLBACK-001", "candidate_refs": candidates, "minimal_diff_ref": ref(diff_path),
        "exact_inverse_restores_previous_Source_bytes": True,
        "changed_original_Test_body_only": TARGET,
        "all_other_previous_Test_bodies_byte_equal": True,
        "other_three_candidate_members_byte_equal": equal_other_members,
        "original_12_names_126_assertions_9_unrelated_bodies": True,
        "assertions_old_body_and_new_body_equal": True,
        "comparisons": comparisons,
        "migration_checks": migration_checks,
        "DDL_git_blob": "9efc768f8f4cfb6ac31e1f88a78ad095877328af",
        "historical_commit": "3225a31fd25969c6a5e071a2fc686cb4a835e162",
        "call_chain_checks": checks,
        "production_fence_ref": fence_ref,
        "review_static_utility_ref": utility_ref,
        "ordinary": "BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE",
        "Go_AST_Go_gofmt_compiler_SQL_native_model_execution": None,
        "mechanical_failures_this_v2": 0,
        "prior_833_826_and_FULL_not_reset": True,
    }
    write("static-verification.json", result)
    write("source-pins.json", {"authority": "NONE", "previous_HDF_ref": inputs["previous_HDF_ref"],
         "previous_MF_ref": inputs["previous_MF_ref"], "review_HDF_ref": inputs["review_HDF_ref"],
         "review_MF_ref": inputs["review_MF_ref"], "candidate_refs": candidates,
         "base_refs": source_pins["base_refs"], "production_and_contract_refs": source_pins["production_and_contract_refs"],
         "other_three_candidates_equal_previous": equal_other_members,
         "history_resource_refs": [ref(Q / "inputs/previous-source/migration-resources.json"), ref(Q / "inputs/previous-source/historical20-resource-entry.json")],
         "prior_833_origin_ref": ref(Q / "inputs/previous-source/failure-origin.833.json")})
    print(json.dumps({"authority": "NONE", "status": result["status"], "candidate_refs": candidates,
          "minimal_diff": diff, "call_chain_checks": checks, "original_names": len(original_names),
          "original_assertions": 126, "unrelated_equal_bodies": len(unrelated_equal),
          "all_other_candidate_members_byte_equal": True, "ordinary": result["ordinary"],
          "static_verification_ref": ref(Q / "static-verification.json")}, ensure_ascii=False))
exit_code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    exit_code = 1
finally:
    print("ROOT_PYTHON_EXIT=" + str(exit_code))
sys.exit(exit_code)

