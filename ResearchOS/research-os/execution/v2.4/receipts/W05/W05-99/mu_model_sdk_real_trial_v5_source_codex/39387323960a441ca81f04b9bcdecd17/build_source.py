"""Pure byte-level v5 source proposal builder. Never imports or runs candidates."""
import ast
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("D:/作品集/ResearchOS/research-os")
HERE = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17"
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v4_source_codex/87c5a05ce5054e3c9ffa2f62ba898c57"


def ref(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write(name, raw):
    path = HERE / name
    with path.open("xb") as stream:
        stream.write(raw)
    assert path.read_bytes() == raw
    return ref(path)


def replace_once(source, old, new, label):
    assert source.count(old) == 1, (label, source.count(old))
    return source.replace(old, new)


v4 = (OLD / "mu_sdk_trial.v4.proposed.py").read_text(encoding="utf-8")
helper = '''def verified_cli_context_transition(label, old, parsed, post_raw):
    """One original CLI JSONL record + final validated snapshot + saved bytes."""
    require(label in ("cli-goal", "cli-run") and isinstance(old, dict),
            "CONTEXT_PREIMAGE_INVALID")
    name = "goal" if label == "cli-goal" else "run"
    rows = [row for row in parsed if row.get("command") == name]
    require(len(rows) == len(parsed) == 1, "CLI_CONTEXT_JSONL_NOT_UNIQUE")
    row = rows[0]
    require(row.get("exit_code") == 0 and "context_save_error" not in row,
            "CLI_CONTEXT_SAVE_NOT_SUCCESSFUL")
    ops = row.get("operations")
    require(isinstance(ops, list), "CLI_CONTEXT_OPERATIONS_ABSENT")
    methods = [op.get("method") if isinstance(op, dict) else None for op in ops]
    expected_methods = ((["goal.start"], ["session.get", "goal.start"])
                        if label == "cli-goal" else
                        (["session.create", "session.send"],
                         ["session.get", "session.send"]))
    require(methods in expected_methods and all(
        op.get("status") == "COMPLETED" and type(op.get("exit_code")) is int
        and op["exit_code"] == 0 for op in ops),
        "CLI_CONTEXT_OPERATION_SEQUENCE_CHANGED")
    final_result = ops[-1].get("result")
    require(isinstance(final_result, dict), "CLI_CONTEXT_OPERATION_RESULT_ABSENT")
    admitted = final_result.get("snapshot", final_result)
    final = row.get("last_verified_session_snapshot")
    saved = row.get("saved_context")
    require(isinstance(admitted, dict) and isinstance(final, dict) and
            isinstance(saved, dict) and set(saved) == {
                "project_id", "session_id", "session_revision", "writer_epoch", "updated_by"},
            "CLI_CONTEXT_WITNESSES_ABSENT")
    writer = final.get("writer")
    require(isinstance(writer, dict) and type(saved["session_revision"]) is int and
            type(saved["writer_epoch"]) is int and
            saved["session_revision"] >= 1 and saved["writer_epoch"] >= 1 and
            type(final.get("revision")) is int and type(writer.get("epoch")) is int,
            "CLI_CONTEXT_WRITER_INVALID")
    require(saved["project_id"] == old.get("project_id") == admitted.get("project_id")
            == final.get("project_id") and
            saved["session_id"] == row.get("session_id") == admitted.get("session_id")
            == final.get("session_id") and
            (old.get("session_id") in ("", saved["session_id"])) and
            isinstance(saved["session_id"], str) and saved["session_id"] and
            saved["session_revision"] == final["revision"] and
            saved["session_revision"] >= admitted.get("revision", 0) and
            saved["writer_epoch"] == writer["epoch"] and
            saved["updated_by"] == row.get("client_id") == writer.get("client_id") and
            admitted.get("writer", {}).get("client_id") == saved["updated_by"],
            "CLI_CONTEXT_ORIGINAL_RESPONSE_MISMATCH")
    require(label != "cli-run" or (methods[0] != "session.create" or
            old.get("session_id") == ""), "CLI_RUN_CREATE_NOT_FRESH")
    expected = dict(old)
    expected.update(saved)
    post = strict_consumed_json(post_raw, "CLI context postimage")
    require(post == expected, "CLI_CONTEXT_POSTIMAGE_NOT_DERIVED")
    return {"original_jsonl_command": name, "admission_method": methods[-1],
            "saved_context": saved, "final_snapshot_revision": final["revision"],
            "postimage_fields": sorted(expected)}


'''
assert v4.count("def after_child_consumed_states(") == 1
v5 = v4.replace("def after_child_consumed_states(", helper + "def after_child_consumed_states(", 1)
v5 = replace_once(v5,
'''    else:
        require(label in ("cli-goal", "cli-run") and config[0] == prior,
                "UNAUTHORIZED_CONFIG_TRANSITION")
    doc["_expected_config_state"] = config[0]
    return ({"discovery_state": discovery[0], "config_before_state": prior,
             "config_after_state": config[0], "transition_label": label},
''',
'''    else:
        require(label in ("cli-goal", "cli-run") and prior["exists"] and
                isinstance(old, dict) and config[0]["exists"],
                "CLI_CONTEXT_PREIMAGE_CHANGED")
        if config[0] != prior:
            context_evidence = verified_cli_context_transition(label, old, parsed, config[1])
        else:
            context_evidence = {"unchanged_original_bytes": True}
    doc["_expected_config_state"] = config[0]
    transition = {"discovery_state": discovery[0], "config_before_state": prior,
                  "config_after_state": config[0], "transition_label": label}
    if label in ("cli-goal", "cli-run"):
        transition["context_evidence"] = context_evidence
    return (transition,
''', "finite context transition")
v5 = replace_once(v5, 'if label in ("cli-init", "cli-config"):\n                if before_config_raw is not None:',
                  'if label in ("cli-init", "cli-config", "cli-goal", "cli-run"):\n                if before_config_raw is not None:',
                  "raw before/after export")
runner_ref = write("mu_sdk_trial.v5.proposed.py", v5.encode("utf-8"))

main_cli = (ROOT / "apps/cli/cli_stream.go").read_text(encoding="utf-8")
cli = replace_once(main_cli, "\ttransportUnreachable bool\n", "\ttransportUnreachable bool\n\tlastVerifiedSessionSnapshot map[string]any\n", "last snapshot field")
cli = replace_once(cli,
'''\tif snap["project_id"] != f.c.projectID || snap["session_id"] != f.c.sessionID || snap["protocol_version"] != clientProtocol {
\t\treturn nil, "SNAPSHOT_SCOPE_MISMATCH", exitNotImplemented
\t}
\treturn snap, "", 0
''',
'''\tif snap["project_id"] != f.c.projectID || snap["session_id"] != f.c.sessionID || snap["protocol_version"] != clientProtocol {
\t\treturn nil, "SNAPSHOT_SCOPE_MISMATCH", exitNotImplemented
\t}
\tf.lastVerifiedSessionSnapshot = snap
\treturn snap, "", 0
''', "verified session snapshot")
cli = replace_once(cli,
'''\tout["session_id"], out["reason"], out["detail"] = c.sessionID, reason, detail
\treturn out, code
''',
'''\tout["session_id"], out["reason"], out["detail"] = c.sessionID, reason, detail
\tif f.lastVerifiedSessionSnapshot != nil && !readOnly {
\t\tout["last_verified_session_snapshot"] = f.lastVerifiedSessionSnapshot
\t}
\treturn out, code
''', "original final snapshot in JSONL")
cli = replace_once(cli,
'''\tif err := saveCLIContext(c, cfg); err != nil {
\t\tdiag("session context could not be saved: %s", err)
\t\tout["context_save_error"] = "CONFIG_WRITE_FAILED"
\t\tif code == 0 {
\t\t\tcode = exitFailed
\t\t\tout["status"], out["exit_code"] = "REJECTED", code
\t\t}
\t}
\toutJSON(out)
''',
'''\tif err := saveCLIContext(c, cfg); err != nil {
\t\tdiag("session context could not be saved: %s", err)
\t\tout["context_save_error"] = "CONFIG_WRITE_FAILED"
\t\tif code == 0 {
\t\t\tcode = exitFailed
\t\t\tout["status"], out["exit_code"] = "REJECTED", code
\t\t}
\t} else if c.sessionID != "" && c.projectID != "" && c.revision >= 1 {
\t\t// Original JSONL reports the exact persisted context after a successful save.
\t\tout["saved_context"] = map[string]any{
\t\t\t"project_id": cfg.ProjectID, "session_id": cfg.SessionID,
\t\t\t"session_revision": cfg.Revision, "writer_epoch": cfg.WriterEpoch,
\t\t\t"updated_by": cfg.UpdatedBy,
\t\t}
\t}
\toutJSON(out)
''', "persisted writer receipt")
cli_ref = write("cli_stream.context_receipt.v5.proposed.go", cli.encode("utf-8"))

go_refs = []
for name in ("internal_host_vault.v4.proposed.go", "internal_host_host.v4.proposed.go",
             "apps_control_main.v4.proposed.go", "runtime_qualification.unlimited.v5.proposed.go"):
    original = OLD / name
    target = name.replace(".v4.proposed.go", ".v5.proposed.go")
    go_refs.append({"prior": ref(original), "candidate": write(target, original.read_bytes())})
template_ref = write("input.v5.template.json", (OLD / "input.v4.template.json").read_bytes())
assert ast.parse(v5)
assert len(go_refs) == 4 and all(x["prior"]["sha256"] == x["candidate"]["sha256"] for x in go_refs)
inverse = {"schema": "researchos.mu-sdk-v5-source-inverse.v1", "baseline_runner": ref(OLD / "mu_sdk_trial.v4.proposed.py"),
           "candidate_runner": runner_ref, "current_main_cli": ref(ROOT / "apps/cli/cli_stream.go"),
           "candidate_cli": cli_ref, "go_byte_identical": go_refs,
           "runner_changed_functions": ["verified_cli_context_transition", "after_child_consumed_states", "command_once"],
           "cli_changed_functions": ["cliFlow.snapshot", "runCLIVerb", "cliFlowSummary"],
           "cli_added_field": "cliFlow.lastVerifiedSessionSnapshot",
           "inverse": "Restore exact baseline_runner and current_main_cli bytes; four Go candidate byte pins equal prior; template byte-identical."}
inverse_ref = write("source-inverse.json", (json.dumps(inverse, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
result = {"runner_ref": runner_ref, "cli_ref": cli_ref, "go_refs": go_refs,
          "template_ref": template_ref, "inverse_ref": inverse_ref}
write("build-result.json", (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"built": True, "runner_sha": runner_ref["sha256"], "cli_sha": cli_ref["sha256"], "go_equal": True}, ensure_ascii=False))
