"""Synthetic real-shape pure IO controls; no candidate import, child or network."""
import ast
import copy
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17")
source = (HERE / "mu_sdk_trial.v5.proposed.py").read_text(encoding="utf-8")
tree = ast.parse(source)
names = {"verified_cli_context_transition", "after_child_consumed_states", "strict_consumed_json"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names


def require(ok, message):
    if not ok:
        raise ValueError(message)


scope = {"require": require, "json": json}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "<pure-io-functions-only>", "exec"), scope)
verify = scope["verified_cli_context_transition"]
after = scope["after_child_consumed_states"]
old = {"config_revision": 1, "model": "opencode-go/deepseek-v4.1-flash",
       "settled_run_id": "", "workspace_ref": "workspace-A", "project_id": "project-A",
       "session_id": "", "session_revision": 0, "writer_epoch": 0, "updated_by": ""}


def fixture(label):
    name = "goal" if label == "cli-goal" else "run"
    epoch = 3 if label == "cli-goal" else 2
    first_rev, final_rev = (2, 3) if label == "cli-goal" else (3, 4)
    writer = {"client_id": "cli-owner-A", "epoch": epoch, "expires_at": "2030-01-01T00:00:00Z"}
    admitted = {"project_id": "project-A", "session_id": "session-A",
                "revision": first_rev, "writer": writer}
    final = dict(admitted, revision=final_rev)
    saved = {"project_id": "project-A", "session_id": "session-A",
             "session_revision": final_rev, "writer_epoch": epoch, "updated_by": "cli-owner-A"}
    if name == "goal":
        operations = [{"method": "goal.start", "status": "COMPLETED", "exit_code": 0,
                       "result": {"snapshot": admitted, "goal_id": "goal-A"}}]
    else:
        created = dict(admitted, revision=1)
        operations = [{"method": "session.create", "status": "COMPLETED", "exit_code": 0,
                       "result": {"snapshot": created}},
                      {"method": "session.send", "status": "COMPLETED", "exit_code": 0,
                       "result": {"snapshot": admitted, "message_id": "message-A"}}]
    row = {"command": name, "status": "COMPLETED", "exit_code": 0,
           "client_id": "cli-owner-A", "session_id": "session-A",
           "operations": operations, "last_verified_session_snapshot": final,
           "saved_context": saved}
    post = dict(old, **saved)
    return row, post


checks = []
for label in ("cli-goal", "cli-run"):
    row, post = fixture(label)
    raw = (json.dumps(post, separators=(",", ":")) + "\n").encode()
    evidence = verify(label, old, [row], raw)
    assert evidence["saved_context"] == row["saved_context"]
    checks.append(label + "_legitimate_context_positive")
    for mutation, change in (
        ("external_project", lambda r, p: p.__setitem__("project_id", "project-foreign")),
        ("changed_workspace", lambda r, p: p.__setitem__("workspace_ref", "workspace-foreign")),
        ("changed_model", lambda r, p: p.__setitem__("model", "other-model")),
        ("changed_config_revision", lambda r, p: p.__setitem__("config_revision", 2)),
        ("changed_session", lambda r, p: p.__setitem__("session_id", "session-foreign")),
        ("changed_saved_revision", lambda r, p: r["saved_context"].__setitem__("session_revision", 99)),
        ("changed_writer_epoch", lambda r, p: r["saved_context"].__setitem__("writer_epoch", 99)),
        ("foreign_writer", lambda r, p: r["last_verified_session_snapshot"]["writer"].__setitem__("client_id", "foreign")),
        ("missing_final_snapshot", lambda r, p: r.pop("last_verified_session_snapshot")),
        ("failed_save", lambda r, p: r.__setitem__("context_save_error", "CONFIG_WRITE_FAILED")),
        ("admission_scope", lambda r, p: r["operations"][-1]["result"]["snapshot"].__setitem__("project_id", "foreign")),
    ):
        bad_row, bad_post = copy.deepcopy(row), copy.deepcopy(post)
        change(bad_row, bad_post)
        try:
            verify(label, old, [bad_row], json.dumps(bad_post).encode())
        except (ValueError, TypeError, KeyError):
            checks.append(label + "_" + mutation + "_rejected")
        else:
            raise AssertionError(label + "_" + mutation + "_accepted")

# Exact-byte no-write branch remains the original v4 behavior.
old_raw = json.dumps(old, separators=(",", ":")).encode()
prior = {"path": "C:/isolated/config.json", "exists": True,
         "sha256": hashlib.sha256(old_raw).hexdigest(), "bytes": len(old_raw)}
discovery = ({"path": "C:/isolated/discovery.json", "exists": True,
              "sha256": "pinned", "bytes": 1}, b"x")
current = [(prior, old_raw)]
scope["current_consumed_states"] = lambda doc: (discovery, current[0])
doc = {"initial_discovery_state": discovery[0], "_expected_config_state": prior,
       "_pre_child_config_json": old, "_pre_child_config_raw": old_raw}
transition, before, post = after(doc, "cli-run", [])
assert transition["context_evidence"] == {"unchanged_original_bytes": True}
assert before == post == old_raw
checks.append("unchanged_context_exact_bytes_positive")

cli = (HERE / "cli_stream.context_receipt.v5.proposed.go").read_text(encoding="utf-8")
assert cli.count('out["saved_context"] = map[string]any{') == 1
assert cli.count('out["last_verified_session_snapshot"] = f.lastVerifiedSessionSnapshot') == 1
assert cli.count('f.lastVerifiedSessionSnapshot = snap') == 1
checks.append("cli_receipt_static_exact_sites")
with (HERE / "precheck.v5.json").open("xb") as stream:
    stream.write((json.dumps({"schema": "researchos.mu-sdk-v5-pure-io-precheck.v1",
                              "all_passed": True, "checks": checks,
                              "actual_cli_executions": 0, "actual_model_requests": 0,
                              "synthetic_fixture_not_qualification": True},
                             ensure_ascii=False, indent=2) + "\n").encode())
print(json.dumps({"all_passed": True, "checks": len(checks)}, ensure_ascii=False))
