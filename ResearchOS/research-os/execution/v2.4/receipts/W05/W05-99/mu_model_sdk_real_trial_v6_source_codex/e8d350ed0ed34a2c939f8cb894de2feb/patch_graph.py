"""Exclusive source-only extraction; does not import or run product code."""
import ast
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb')
source = (HERE / 'mu_sdk_trial.v6.r23.proposed.py').read_text(encoding='utf-8')
target = HERE / 'mu_sdk_trial.v6.graph.proposed.py'

helper = '''def verify_ordinary_goal_graph(db, doc, before, original_summary, prior_snapshot,
                               admitted, draft_policies):
    """Tie the original CLI admission and host report to exact new domain rows."""
    execution = original_summary["execution"]
    host = execution.get("host_execution")
    require(isinstance(host, dict), "original host report absent")
    project = doc["project_id"]
    after = {kind: {row[0] for row in db.execute(
        "SELECT id FROM domain_objects WHERE project=? AND kind=?", (project, kind))}
             for kind in ("Goal", "Task", "Run")}
    created = {kind: after[kind] - before[kind] for kind in before}
    require(all(len(created[kind]) == 1 for kind in ("Goal", "Task", "Run")),
            "ordinary turn must add exactly one Goal, Task and Run")
    new_goal_id = next(iter(created["Goal"]))
    task_id = next(iter(created["Task"]))
    run_id = next(iter(created["Run"]))
    run = object_by_id(db, "Run", run_id, project)
    task = object_by_id(db, "Task", task_id, project)
    goal = object_by_id(db, "Goal", new_goal_id, project)
    require(prior_snapshot.get("goal_id") == doc["goal_id"] and
            new_goal_id != doc["goal_id"] and
            new_goal_id == execution.get("goal_id") == admitted.get("goal_id") and
            task_id == execution.get("task_id") == run.get("task_id") and
            run_id == execution.get("run_id") == task.get("active_run_id") and
            task.get("goal_id") == new_goal_id and goal.get("status") == "ACTIVE" and
            run.get("runtime_id") == doc["runtime_id"] and
            task.get("status") == "EXECUTION_REPORTED" and
            run.get("status") == host.get("status") == "SETTLED" and
            run.get("revision") == host.get("revision") and
            run.get("children_stopped") is host.get("children_stopped") is True and
            run.get("queue_empty") is host.get("queue_empty") is True and
            run.get("runtime_settled_at") == host.get("runtime_settled_at") and
            run.get("execution_report") == host.get("execution_report") and
            run.get("exit_code") == execution.get("exit_code") == 0,
            "ordinary original response and new Goal/Task/Run graph differ")
    ids = host.get("result_artifact_ids")
    require(isinstance(ids, list) and ids and
            len(ids) == len(set(ids)) and
            all(isinstance(identity, str) and identity for identity in ids) and
            run.get("result_artifact_ids") == ids and
            task.get("output_artifact_ids") == ids,
            "host artifact IDs differ from Run or Task")
    for identity in ids:
        artifact = object_by_id(db, "Artifact", identity, project)
        require(artifact.get("id") == identity,
                "original host artifact absent from this project")
    policies = budget_chain(db, project, new_goal_id, "ACTIVE")
    require([p["id"] for p in policies[1:]] ==
            [p["id"] for p in draft_policies[1:]] and
            policies[0]["id"] != draft_policies[0]["id"],
            "new Goal budget ancestry differs from frozen parent chain")
    return new_goal_id, task_id, run_id, policies


'''

old = '''        after = {kind: {row[0] for row in db.execute(
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
'''
new = '''        new_goal_id, task_id, run_id, policies = verify_ordinary_goal_graph(
            db, doc, before, original_summary, prior_snapshot, admitted, draft_policies)
'''
assert source.count('def effects(db, project, run_id):') == 1
assert source.count(old) == 1
changed = source.replace('def effects(db, project, run_id):', helper + 'def effects(db, project, run_id):', 1).replace(old, new, 1)
ast.parse(changed)
with target.open('xb') as out:
    out.write(changed.encode('utf-8'))
print({'source_sha256': hashlib.sha256(changed.encode('utf-8')).hexdigest(),
       'bytes': len(changed.encode('utf-8')), 'inverse_exact': changed.replace(new, old, 1).replace(helper, '', 1) == source})
