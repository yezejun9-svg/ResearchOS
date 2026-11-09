"""Independent source/AST/byte audit only; no product/native/provider execution."""
import ast
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
BASE = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_independent_source_review_codex/ef4206a717d4407bac66097b27e3a7a5")
SOURCE = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(Path(path)).replace("\\", "/"), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def doc(path):
    return json.loads(Path(path).read_bytes())
def verify(ref):
    actual = pin(ref["path"])
    return {"expected": ref, "actual": actual, "matches": actual["sha256"] == ref["sha256"] and actual["bytes"] == ref["bytes"]}
hdf = doc(SOURCE / "handoff.json")
mf = doc(SOURCE / "manifest.json")
iv = doc(SOURCE / "source-inverse.json")
members = [verify(ref) for ref in mf["members"]]
externals = [verify(ref) for ref in [iv["basis_ref"], hdf["review_ref"], hdf["cli_producer_ref"], *hdf["go_refs"]]]
old = Path(iv["basis_ref"]["path"]).read_text(encoding="utf-8")
new = Path(hdf["candidate_ref"]["path"]).read_text(encoding="utf-8")
def regenerated(ref, left, right):
    raw = Path(ref["path"]).read_bytes()
    lines = raw.decode("utf-8").splitlines(keepends=True)
    generated = "".join(difflib.unified_diff(left.splitlines(keepends=True), right.splitlines(keepends=True),
                     fromfile=lines[0][4:].rstrip("\r\n"), tofile=lines[1][4:].rstrip("\r\n"))).encode("utf-8")
    return {"ref": ref, "exact_regeneration": generated == raw}
old_tree, new_tree = ast.parse(old), ast.parse(new)
def definitions(tree, text):
    lines = text.splitlines(keepends=True)
    return {n.name: (ast.dump(n, include_attributes=False), "".join(lines[n.lineno-1:n.end_lineno]))
            for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
old_defs, new_defs = definitions(old_tree, old), definitions(new_tree, new)
unchanged = [name for name in old_defs if name in new_defs and old_defs[name] == new_defs[name]]
changed = [name for name in old_defs if name in new_defs and old_defs[name] != new_defs[name]]
added = [name for name in new_defs if name not in old_defs]
nd = list(difflib.ndiff(old.splitlines(keepends=True), new.splitlines(keepends=True)))
inverse = {"forward": regenerated(iv["forward_diff_ref"], old, new),
           "reverse": regenerated(iv["reverse_diff_ref"], new, old),
           "ndiff_restore_old_exact": "".join(difflib.restore(nd, 1)) == old,
           "ndiff_restore_new_exact": "".join(difflib.restore(nd, 2)) == new,
           "unchanged_definitions_byte_ast": unchanged, "changed": changed, "added": added}
terminal = (SOURCE / "mu_sdk_trial.v6.terminal.proposed.py").read_text(encoding="utf-8")
terminal_defs = definitions(ast.parse(terminal), terminal)
stream_names = ["original_cli_summary_stream", "verified_cli_context_transition", "strict_consumed_json"]
stream_controls_basis = {name: new_defs[name] == terminal_defs[name] for name in stream_names}
copies = []
for original in [hdf["cli_producer_ref"], *hdf["go_refs"]]:
    matching = [r for r in mf["members"] if r["sha256"] == original["sha256"] and r["bytes"] == original["bytes"]]
    copies.append({"original_ref": original, "copies": matching,
                   "actual_copy_bytes_equal": bool(matching) and all(Path(r["path"]).read_bytes() == Path(original["path"]).read_bytes() for r in matching)})
# Execute only seven named data validators plus require; no candidate module or entry point.
pure_names = {"require", "strict_consumed_json", "original_cli_summary_stream",
              "verified_cli_context_transition", "object_by_id", "budget_chain", "verify_ordinary_goal_graph"}
nodes = [n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name in pure_names]
space = {"json": json, "datetime": datetime, "timezone": timezone}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "<independent-selected-pure-data-functions>", "exec"), space)
test_text = (SOURCE / "precheck_terminal.py").read_text(encoding="utf-8")
test_tree = ast.parse(test_text)
old_node = next(n for n in test_tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "old" for t in n.targets))
old_context = ast.literal_eval(old_node.value)
old_context["session_id"] = "session-A"
fixture_node = next(n for n in test_tree.body if isinstance(n, ast.FunctionDef) and n.name == "fixture")
fixture_space = {"json": json, "old": old_context}
exec(compile(ast.Module(body=[fixture_node], type_ignores=[]), "<read-only-fixture-data-builder>", "exec"), fixture_space)
stream, post = fixture_space["fixture"]("cli-run", 4)
summary = stream[-1]
summary["operations"][0]["method"] = "session.get"
summary["operations"][0]["result"]["snapshot"]["goal_id"] = "draft-goal"
summary["operations"][-1]["result"]["snapshot"]["goal_id"] = "goal-A"
summary["last_verified_session_snapshot"].update(goal_id="goal-A", active_run_id="run-A")
summary["execution"]["task_id"] = "task-A"
stream[-2]["event"]["payload"]["artifact_ref"].update(entity_type="Artifact", revision=1, content_hash="sha256:"+"a"*64)
def observes(fn):
    try:
        value = fn()
        return {"accepted": True, "exception": None, "returned_type": type(value).__name__}
    except (ValueError, KeyError, TypeError, AssertionError) as error:
        return {"accepted": False, "exception": type(error).__name__ + ":" + str(error)}
controls = {"positive_stream_with_actual_terminal_targets": observes(lambda: space["verified_cli_context_transition"]("cli-run", old_context, stream, post))}
for key, value in [("goal_id", "foreign-goal"), ("active_run_id", "foreign-run")]:
    bad = copy.deepcopy(stream); bad[-1]["last_verified_session_snapshot"][key] = value
    controls["foreign_final_"+key] = observes(lambda bad=bad: space["verified_cli_context_transition"]("cli-run", old_context, bad, post))
for key, value in [("entity_type", "Task"), ("revision", False), ("content_hash", "wrong-hash")]:
    bad = copy.deepcopy(stream); bad[-2]["event"]["payload"]["artifact_ref"][key] = value
    controls["invalid_available_artifact_ref_"+key] = observes(lambda bad=bad: space["original_cli_summary_stream"]("cli-run", bad))
graph_text = (SOURCE / "precheck_graph.py").read_text(encoding="utf-8")
graph_tree = ast.parse(graph_text)
graph_pure = [n for n in graph_tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ("policy", "FakeDB")]
fixture_graph = {"json": json}
exec(compile(ast.Module(body=graph_pure, type_ignores=[]), "<read-only-memory-rows>", "exec"), fixture_graph)
for n in graph_tree.body:
    if isinstance(n, ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("objects", "host", "summary", "doc", "before"):
        exec(compile(ast.Module(body=[n], type_ignores=[]), "<read-only-fixture-values>", "exec"), fixture_graph)
rows = copy.deepcopy(fixture_graph["objects"])
DB = fixture_graph["FakeDB"]
draft = space["budget_chain"](DB(rows), "P", "G0", "DRAFT")
def graph_case(current_rows):
    return space["verify_ordinary_goal_graph"](DB(current_rows), fixture_graph["doc"], fixture_graph["before"],
                  fixture_graph["summary"], {"goal_id":"G0"}, {"goal_id":"G1"}, draft)
controls["artifact_row_only_id"] = observes(lambda: graph_case(rows))
rows_full = copy.deepcopy(rows)
rows_full[("Artifact", "A1")].update(revision=1, content_hash="sha256:"+"a"*64, storage_key="run-A-output", byte_size=1)
controls["artifact_row_with_version"] = observes(lambda: graph_case(rows_full))
for key,value in [("revision",99),("content_hash","sha256:"+"b"*64)]:
    bad = copy.deepcopy(rows_full); bad[("Artifact","A1")][key] = value
    controls["artifact_db_"+key+"_different_from_original_event"] = observes(lambda bad=bad: graph_case(bad))
audit = {"schema":"researchos.mu-sdk-v6-independent-source-audit.v1",
         "actor_id":"codex:/root/f08_whole_scope_review",
         "manifest_ref":pin(SOURCE/"manifest.json"), "handoff_ref":pin(SOURCE/"handoff.json"),
         "source_ref":hdf["candidate_ref"], "all_members":members,
         "members_count":len(members), "members_all_exact":all(r["matches"] for r in members),
         "external_refs":externals, "external_refs_all_exact":all(r["matches"] for r in externals),
         "whole_inverse":inverse, "cli_and_four_go_exact_copies":copies,
         "selected_stream_same_as_author_27_control_basis":stream_controls_basis,
         "independent_pure_data_observations":controls,
         "pure_data_observations_are_not_product_execution":True,
         "candidate_entry_point_imports":0, "actual_cli_go_sdk_provider_calls":0,
         "canonical_writes":0,"source_acceptance_delta":0,"formal_case_accepted_delta":0}
with (BASE/"audit.json").open("xb") as f:
    f.write((json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
print(json.dumps({"audit_ref":pin(BASE/"audit.json"),"all_members":len(members),"members_exact":audit["members_all_exact"],
                  "external_exact":audit["external_refs_all_exact"],"inverse":{k:v for k,v in inverse.items() if k not in ("unchanged_definitions_byte_ast",)},
                  "unchanged_definitions":len(unchanged),"controls":controls},ensure_ascii=False))

