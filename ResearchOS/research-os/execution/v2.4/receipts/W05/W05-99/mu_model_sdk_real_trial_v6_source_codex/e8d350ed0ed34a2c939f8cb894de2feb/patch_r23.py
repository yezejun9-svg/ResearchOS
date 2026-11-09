"""Source-only draft bootstrap and fresh ordinary Goal binding; no execution."""
import ast
import hashlib
import json
import pathlib
import sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path("D:/作品集/ResearchOS/research-os")
HERE = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb"
source = (HERE / "mu_sdk_trial.v6.latest_state.proposed.py").read_text(encoding="utf-8")
replacements = []


def plan(label, before, after):
    replacements.append((label, before, after))


draft_helper = '''def verified_cli_draft_goal_transition(doc, old, parsed, post_raw):
    """Project-level --draft creates one Session and Goal without a Task/Run."""
    require(len(parsed) == 1 and isinstance(parsed[0], dict),
            "CLI_DRAFT_STREAM_NOT_SINGLE_SUMMARY")
    row = parsed[0]
    require(row.get("command") == "goal" and row.get("status") == "GOAL_DRAFT_CREATED" and
            type(row.get("exit_code")) is int and row["exit_code"] == 0 and
            "context_save_error" not in row and "last_verified_session_snapshot" not in row and
            row.get("execution") == {"status": "NOT_STARTED", "independent_acceptance": "NOT_EVALUATED"},
            "CLI_DRAFT_NOT_A_NO_EXECUTION_RESULT")
    ops = row.get("operations")
    require(isinstance(ops, list) and len(ops) == 1 and isinstance(ops[0], dict) and
            ops[0].get("method") == "goal.start" and ops[0].get("status") == "COMPLETED" and
            type(ops[0].get("exit_code")) is int and ops[0]["exit_code"] == 0,
            "CLI_DRAFT_OPERATION_NOT_GOAL_START")
    result = ops[0].get("result")
    require(isinstance(result, dict) and isinstance(result.get("snapshot"), dict),
            "CLI_DRAFT_TYPED_RESULT_ABSENT")
    snap = result["snapshot"]
    writer = snap.get("writer")
    saved = row.get("saved_context")
    require(isinstance(writer, dict) and isinstance(saved, dict) and
            set(saved) == {"project_id", "session_id", "session_revision",
                           "writer_epoch", "updated_by"} and
            isinstance(result.get("goal_id"), str) and result["goal_id"] and
            result.get("goal_status") == snap.get("goal_status") == "DRAFT" and
            result["goal_id"] == snap.get("goal_id") == row.get("goal", {}).get("goal_id") and
            result.get("goal_revision") == row.get("goal", {}).get("goal_revision") and
            type(saved.get("session_revision")) is int and saved["session_revision"] >= 1 and
            type(saved.get("writer_epoch")) is int and saved["writer_epoch"] >= 1 and
            saved["project_id"] == old.get("project_id") == doc.get("_init_project_id") == snap.get("project_id") and
            saved["session_id"] == row.get("session_id") == snap.get("session_id") and
            old.get("session_id") == "" and saved["session_revision"] == snap.get("revision") and
            saved["writer_epoch"] == writer.get("epoch") and
            saved["updated_by"] == row.get("client_id") == writer.get("client_id"),
            "CLI_DRAFT_CONTEXT_OR_GOAL_MISMATCH")
    expected = dict(old)
    expected.update(saved)
    require(strict_consumed_json(post_raw, "CLI draft postimage") == expected,
            "CLI_DRAFT_CONFIG_POSTIMAGE_NOT_DERIVED")
    return {"goal_id": result["goal_id"], "goal_status": "DRAFT",
            "session_id": saved["session_id"], "saved_context": saved,
            "provider_requests_from_goal_command": 0}


'''
plan("draft helper", "def after_child_consumed_states(",
     draft_helper + "def after_child_consumed_states(")
plan("draft routing", '''        context_evidence = verified_cli_context_transition(label, old, parsed, config[1])
''', '''        context_evidence = (verified_cli_draft_goal_transition(doc, old, parsed, config[1])
                            if label == "cli-goal" else
                            verified_cli_context_transition(label, old, parsed, config[1]))
''')
plan("bootstrap argv", '''"<CLI_INIT_PROJECT_ID>"],
''', '''"<CLI_INIT_PROJECT_ID>", "--draft"],
''')
plan("bootstrap invocation", '''[cli, "goal", doc["goal_objective"], "--project", project_ids[0]],
''', '''[cli, "goal", doc["goal_objective"], "--project", project_ids[0], "--draft"],
''')
plan("goal budget status", '''def budget_chain(db, project, goal_id):
    goal = object_by_id(db, "Goal", goal_id, project)
    require(goal.get("status") == "ACTIVE", "goal is not ACTIVE")
''', '''def budget_chain(db, project, goal_id, expected_status="ACTIVE"):
    goal = object_by_id(db, "Goal", goal_id, project)
    require(expected_status in ("ACTIVE", "DRAFT") and
            goal.get("status") == expected_status,
            "goal status differs from the authorized phase")
''')
plan("bootstrap budget", '''policies = budget_chain(db, project_ids[0], goals[0]["id"])
''', '''policies = budget_chain(db, project_ids[0], goals[0]["id"], "DRAFT")
''')
plan("execute historical draft budget", '''                budget_chain(db, doc["project_id"], doc["goal_id"])
''', '''                budget_chain(db, doc["project_id"], doc["goal_id"], "DRAFT")
''')
plan("execute draft policy and before IDs", '''        policies = budget_chain(db, doc["project_id"], doc["goal_id"])
        before = {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind='Run'", (doc["project_id"],))}
''', '''        draft_policies = budget_chain(db, doc["project_id"], doc["goal_id"], "DRAFT")
        before = {kind: {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind=?", (doc["project_id"], kind))}
                  for kind in ("Goal", "Task", "Run")}
''')
plan("run original parsed receipt", '''    command_once(doc, [cli, "run", doc["prompt"], "--project", doc["project_id"], "--output", "jsonl"],
                 cwd, env, output, "cli-run", deadline)
''', '''    run_invocation, run_rows = command_once(
        doc, [cli, "run", doc["prompt"], "--project", doc["project_id"], "--output", "jsonl"],
        cwd, env, output, "cli-run", deadline)
    original_summary = run_rows[-1]
    original_execution = original_summary["execution"]
    prior_snapshot = original_summary["operations"][0]["result"]
    prior_snapshot = prior_snapshot.get("snapshot", prior_snapshot)
    admitted = original_summary["operations"][-1]["result"]
    admitted = admitted.get("snapshot", admitted)
    require(original_summary["operations"][0]["method"] == "session.get" and
            prior_snapshot.get("goal_id") == doc["goal_id"] and
            admitted.get("goal_id") == original_execution.get("goal_id") and
            admitted["goal_id"] != doc["goal_id"],
            "ordinary admission did not create a new Goal from the draft Session")
''')
plan("run DB identity and new budget", '''        after = {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind='Run'", (doc["project_id"],))}
        created = after - before
        require(len(created) == 1, "exactly one ordinary Run required")
        run_id = next(iter(created))
        run = object_by_id(db, "Run", run_id, doc["project_id"])
        task = object_by_id(db, "Task", run["task_id"], doc["project_id"])
        require(run.get("runtime_id") == doc["runtime_id"] and
                task.get("goal_id") == doc["goal_id"] and task.get("status") == "EXECUTION_REPORTED",
                "ordinary turn did not settle under the pinned Goal")
''', '''        after = {kind: {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind=?", (doc["project_id"], kind))}
                 for kind in ("Goal", "Task", "Run")}
        created = {kind: after[kind] - before[kind] for kind in before}
        require(all(len(created[kind]) == 1 for kind in ("Goal", "Task", "Run")),
                "ordinary turn must add exactly one Goal, Task and Run")
        new_goal_id = next(iter(created["Goal"]))
        task_id = next(iter(created["Task"]))
        run_id = next(iter(created["Run"]))
        run = object_by_id(db, "Run", run_id, doc["project_id"])
        task = object_by_id(db, "Task", task_id, doc["project_id"])
        goal = object_by_id(db, "Goal", new_goal_id, doc["project_id"])
        require(new_goal_id != doc["goal_id"] and
                new_goal_id == original_execution.get("goal_id") == admitted.get("goal_id") and
                task_id == original_execution.get("task_id") == run.get("task_id") and
                run_id == original_execution.get("run_id") == task.get("active_run_id") and
                task.get("goal_id") == new_goal_id and goal.get("status") == "ACTIVE" and
                run.get("runtime_id") == doc["runtime_id"] and
                task.get("status") == "EXECUTION_REPORTED",
                "ordinary original response and new Goal/Task/Run graph differ")
        policies = budget_chain(db, doc["project_id"], new_goal_id, "ACTIVE")
        require([p["id"] for p in policies[1:]] == [p["id"] for p in draft_policies[1:]] and
                policies[0]["id"] != draft_policies[0]["id"],
                "new Goal budget ancestry differs from frozen parent chain")
''')
plan("trial output new goal", '''             "goal_id": doc["goal_id"], "qualification_run_id": doc["qualification_run_id"],
''', '''             "bootstrap_draft_goal_id": doc["goal_id"], "ordinary_goal_id": new_goal_id,
             "ordinary_task_id": task_id, "qualification_run_id": doc["qualification_run_id"],
''')
plan("trial output original graph", '''             "ordinary_ledgers": ordinary_ledgers, "original_fact_refs": originals,
''', '''             "ordinary_ledgers": ordinary_ledgers, "original_fact_refs": originals,
             "draft_policies": draft_policies, "ordinary_invocation_ref": pin_path(output / "cli-run.invocation.json"),
''')
plan("qualification active budget", '''    task = object_by_id(db, "Task", task_id, project)
    run = object_by_id(db, "Run", run_id, project)
    runtime = object_by_id(db, "RuntimeRegistration", runtime_id, project)
''', '''    task = object_by_id(db, "Task", task_id, project)
    run = object_by_id(db, "Run", run_id, project)
    runtime = object_by_id(db, "RuntimeRegistration", runtime_id, project)
    qualification_policies = budget_chain(db, project, task["goal_id"], "ACTIVE")
    require(task["goal_id"] != doc["goal_id"],
            "qualification cannot borrow the bootstrap DRAFT Goal")
''')
plan("qualification ledger policy", '''    return model_rows, model_ledgers(db, project, run_id, model_rows)
''', '''    return model_rows, model_ledgers(db, project, run_id, model_rows,
                                     qualification_policies[0]["id"])
''')
plan("ledger exact policy parameter", '''def model_ledgers(db, project, run_id, model_effects):
''', '''def model_ledgers(db, project, run_id, model_effects, expected_policy_id):
''')
plan("ledger exact policy check", '''    require(all(row.get("money") is None and row.get("cost_basis") == "UNKNOWN" for row in unknown),
            "UNKNOWN cost was coerced to a number")
''', '''    require(all(row.get("money") is None and row.get("cost_basis") == "UNKNOWN" and
                row.get("policy_id") == expected_policy_id for row in unknown),
            "UNKNOWN cost or new Goal policy was misattributed")
''')
plan("ordinary ledger policy", '''ordinary_ledgers = model_ledgers(db, doc["project_id"], run_id, ordinary_models)
''', '''ordinary_ledgers = model_ledgers(db, doc["project_id"], run_id, ordinary_models,
                                         policies[0]["id"])
''')
plan("bootstrap exact no effects", '''            require(len(goals) == 1, "exactly one new Goal required")
''', '''            require(len(goals) == 1 and goals[0].get("status") == "DRAFT",
                    "exactly one DRAFT Goal required")
            require(all(db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?",
                                   (project_ids[0], kind)).fetchone()[0] == 0
                        for kind in ("Task", "Run", "BudgetLedgerEntry")) and
                    db.execute("SELECT count(*) FROM resource_effects WHERE project=?",
                               (project_ids[0],)).fetchone()[0] == 0,
                    "draft bootstrap started work or charged a provider")
            summary = goal_rows[-1]
            require(len(goal_rows) == 1 and
                    summary["goal"]["goal_id"] == goals[0]["id"] and
                    summary["execution"]["status"] == "NOT_STARTED",
                    "DRAFT Goal DB row differs from original CLI response")
''')

counts = {label: source.count(before) for label, before, _ in replacements}
print(json.dumps({"replacement_anchor_counts": counts}, ensure_ascii=False))
if any(count != 1 for count in counts.values()):
    print("NO_SOURCE_WRITTEN_AMBIGUOUS_ANCHOR")
    sys.exit(0)
for label, before, after in replacements:
    source = source.replace(before, after, 1)
ast.parse(source)
target = HERE / "mu_sdk_trial.v6.r23.proposed.py"
with target.open("xb") as stream:
    stream.write(source.encode("utf-8"))
raw = target.read_bytes()
print(json.dumps({"source_written": True, "sha256": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw)}, ensure_ascii=False))
