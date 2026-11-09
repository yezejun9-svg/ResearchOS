"""Finite product-CLI Mu SDK trial; execute only after a separate Root grant.

The trial uses ResearchOS CLI -> session.send -> Mu worker -> trusted broker.
It never constructs a provider HTTP request or reads a credential. Bootstrap
creates a fresh Project/Goal; execution waits for the product's own admitted
qualification Run and then performs one CLI turn. Every adverse outcome stops.
"""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.dont_write_bytecode = True

PROVIDER = "opencode-go"
MODEL = "deepseek-v4.1-flash"
BASE = "https://opencode.ai/zen/go/v1"
ENDPOINT = BASE + "/chat/completions"
CREDENTIAL_REF = "cred-opencode_go-api_key-1791292735825831100-02e9207a-d97edec4"
REVIEW_SHA = "f59c97465b93a17c7bf3fd408a642b2b4aaa9f9b23a802de4637ca85d4653d95"
MAX_PROVIDER_REQUESTS = 3
MAX_OUTPUT_TOKENS_TOTAL_REQUESTED = 8192
MAX_OUTPUT_TOKENS_PER_REQUEST = 2730  # 2730 * 3 = 8190.
MAX_WALL_SECONDS = 300
MAX_RAW_BYTES = 2 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pin_file(pin, label):
    require(isinstance(pin, dict) and set(pin) == {"path", "sha256", "bytes"}, label + " pin shape")
    path = Path(pin["path"])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), label + " file")
    raw = path.read_bytes()
    require(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"], label + " pin changed")
    return path


def pin_path(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def put_json(path, obj):
    raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)


def readonly_db(path):
    require(path.is_absolute() and path.is_file(), "isolated product DB missing")
    # URI mode=ro prevents the evidence reader from modifying business state.
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=3)


def object_by_id(db, kind, identity, project=None):
    query = "SELECT body FROM domain_objects WHERE kind=? AND id=?"
    args = [kind, identity]
    if project is not None:
        query += " AND project=?"
        args.append(project)
    rows = [json.loads(row[0]) for row in db.execute(query, args)]
    require(len(rows) == 1, kind + " exact identity missing or ambiguous")
    return rows[0]


def budget_chain(db, project, goal_id):
    goal = object_by_id(db, "Goal", goal_id, project)
    require(goal.get("status") == "ACTIVE", "goal is not ACTIVE")
    current = goal.get("budget_policy_id")
    policies = []
    seen = set()
    while current:
        require(current not in seen and len(policies) < 8, "budget ancestry cycle")
        seen.add(current)
        policy = object_by_id(db, "BudgetPolicy", current)
        require(policy.get("mode") == "UNLIMITED_AMOUNT" and policy.get("cap") is None and
                policy.get("unknown_cost_action") == "ALLOW_AND_RECORD" and
                policy.get("enforcement") == "ACCOUNTING_ONLY", "effective budget is not default unlimited/unknown-record")
        effective = datetime.fromisoformat(policy["effective_from"].replace("Z", "+00:00"))
        require(effective.tzinfo is not None and effective <= datetime.now(timezone.utc),
                "future policy revision needs an independently selected active predecessor")
        policies.append(policy)
        current = policy.get("parent_policy_id")
    require([p.get("scope_type") for p in policies] == ["GOAL", "PROJECT", "GLOBAL"], "Goal→Project→Global ancestry mismatch")
    require(policies[0].get("project_id") == project and policies[1].get("project_id") == project and
            policies[2].get("project_id") is None, "budget project binding mismatch")
    return [{"id": p["id"], "revision": p["revision"], "mode": p["mode"], "cap": None}
            for p in policies]


def effects(db, run_id):
    rows = db.execute("SELECT body FROM resource_effects WHERE run=? ORDER BY sequence", (run_id,))
    return [json.loads(row[0]) for row in rows]


def counts(rows):
    result = {"MODEL": 0, "TOOL": 0}
    for row in rows:
        cap = row.get("payload", {}).get("capability")
        if cap in result:
            result[cap] += 1
    return result


def unknown_ledgers(db, project, run_id, minimum):
    rows = [json.loads(row[0]) for row in db.execute(
        "SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=?",
        (project, run_id))]
    unknown = [row for row in rows if row.get("operation") == "UNKNOWN"]
    require(len(unknown) >= minimum, "unknown provider cost ledger absent")
    require(all(row.get("money") is None and row.get("cost_basis") == "UNKNOWN" for row in unknown),
            "UNKNOWN cost was coerced to a number")
    return [{"id": row["id"], "provider_request_id": row["provider_request_id"],
             "money": None, "cost_basis": "UNKNOWN"} for row in unknown]


def validate_public_route(doc):
    require(doc.get("schema") == "researchos.mu-sdk-trial.public-route.v1", "route manifest schema")
    require((doc.get("provider_id"), doc.get("model_id"), doc.get("base_url"),
             doc.get("endpoint"), doc.get("credential_ref")) ==
            (PROVIDER, MODEL, BASE, ENDPOINT, CREDENTIAL_REF), "sealed provider route metadata changed")
    require(doc.get("measurement_mode") == "LIVE" and doc.get("bearer_token_present") is False,
            "route must be LIVE and protected-reference-only")
    require(doc.get("qualification_model_calls") == 1 and doc.get("ordinary_model_calls") == 2,
            "frozen route must allow exactly one qualification and two ordinary calls")
    require(doc.get("max_output_tokens") <= MAX_OUTPUT_TOKENS_PER_REQUEST,
            "three responses can exceed aggregate requested-token limit")
    require(doc.get("max_cost") is None and doc.get("model_upper_bound") is None,
            "this unlimited/UNKNOWN route must not invent a price")
    require(doc.get("function_tool_names") == ["read"] and doc.get("tool_upper_bound") ==
            {"amount": "0", "currency": "USD"}, "read tool route differs from frozen zero-money permission")


def validate_input(doc, mode):
    require(doc.get("schema") == "researchos.mu-sdk-trial.executable-input.v1", "input schema")
    require(doc.get("source_commit") == "e2ee22a0", "source commit changed")
    require(doc.get("maximum_provider_requests") == MAX_PROVIDER_REQUESTS and
            doc.get("total_wall_seconds") == MAX_WALL_SECONDS and
            doc.get("requested_output_tokens_total") == MAX_OUTPUT_TOKENS_TOTAL_REQUESTED,
            "finite scope changed")
    require(doc.get("qualification_requests") == 1 and doc.get("ordinary_requests") == 2,
            "request partition changed")
    for name in ("root_registration", "root_grant", "cli_binary", "intake_review"):
        pin_file(doc[name], name)
    require(doc["intake_review"]["sha256"] == REVIEW_SHA, "resource intake authority changed")
    review = json_file(doc["intake_review"]["path"])
    require(review.get("decision") == "RESOURCE_ACCESS_VERIFIED_UNQUALIFIED_RUNTIME", "intake decision changed")
    resource = review["resource"]
    require((resource["provider_id"], resource["base_url"], resource["model_id"],
             resource["credential_ref_only"]) == (PROVIDER, BASE, MODEL, CREDENTIAL_REF),
            "intake resource tuple changed")
    if mode == "execute":
        for name in ("public_route_manifest", "runtime_profile", "cancel_fixture_receipt",
                     "bootstrap_receipt", "outer_job_contract"):
            pin_file(doc[name], name)
        validate_public_route(json_file(doc["public_route_manifest"]["path"]))
        profile = json_file(doc["runtime_profile"]["path"])
        model = profile.get("model_config", {})
        require(profile.get("backend") == "mu-sdk-broker-v1" and profile.get("model") == MODEL,
                "Mu profile identity changed")
        require((model.get("api"), model.get("provider"), model.get("model"), model.get("endpoint")) ==
                ("openai-completions", PROVIDER, MODEL, ENDPOINT), "frozen SDK route changed")
        require(model.get("max_calls") == 2 and 1 <= model.get("max_output_tokens", 0) <=
                MAX_OUTPUT_TOKENS_PER_REQUEST and profile.get("model_qualification", {}).get("max_calls") == 1,
                "qualification/ordinary model limits changed")
        require(profile.get("max_cost", "ABSENT") is None, "explicit unknown qualification max_cost required")
        require(profile.get("timeout_seconds", 9999) <= MAX_WALL_SECONDS, "profile timeout exceeds scope")
        names = [tool.get("function", {}).get("name") for tool in model.get("tools", [])]
        require(names == ["read"], "only bounded read tool is in this trial")
        policy = profile.get("tool_policy", {})
        require(policy.get("max_calls") == 1 and policy.get("read_paths") == ["evidence.txt"] and
                policy.get("write_paths") == {} and policy.get("max_read_bytes") == 4096 and
                policy.get("max_write_bytes") == 4096,
                "frozen read-only workspace tool policy changed")
        routes = profile.get("effect_routes", [])
        require(len(routes) == 2 and {route.get("capability") for route in routes} == {"MODEL", "TOOL"},
                "frozen MODEL and TOOL effect routes required")
        model_route = next(route for route in routes if route["capability"] == "MODEL")
        tool_route = next(route for route in routes if route["capability"] == "TOOL")
        require(model_route.get("upper_bound") is None and
                tool_route.get("upper_bound") == {"amount": "0", "currency": "USD"},
                "unlimited MODEL and zero-cost TOOL route changed")
        require(model_route.get("id") == model.get("route") == profile.get("model_qualification", {}).get("route") and
                tool_route.get("id") == model.get("route") and
                model_route.get("credential_revision") == doc.get("credential_revision"),
                "MODEL/TOOL route or protected credential revision changed")
        bootstrap = json_file(doc["bootstrap_receipt"]["path"])
        require(bootstrap.get("stage") == "BOOTSTRAP_ONLY" and
                bootstrap.get("project_id") == doc.get("project_id") and
                bootstrap.get("goal_id") == doc.get("goal_id") and
                bootstrap.get("provider_requests") == 0, "bootstrap identity changed")
        job = json_file(doc["outer_job_contract"]["path"])
        require(job.get("kill_on_close") is True and job.get("wall_seconds") <= MAX_WALL_SECONDS and
                job.get("owns_child_tree") is True, "bounded Windows Job ownership missing")
        cancel = json_file(doc["cancel_fixture_receipt"]["path"])
        require(cancel.get("case_id") == "TestRuntimeMuTypedCancelStopsTransport" and
                cancel.get("source_commit") == "e2ee22a0" and cancel.get("native_exit") == 0 and
                cancel.get("external_provider_requests") == 0 and
                cancel.get("original_io_refs"), "current local cancel fixture evidence absent")
    require(Path(doc["data_root"]).is_absolute() and Path(doc["workspace"]).is_absolute(),
            "absolute isolated data/workspace roots required")
    require(Path(doc["data_root"]).resolve() != Path(resource["private_root_ref_only"]).resolve(),
            "trial must not use the intake product DB as its own DB")
    require(Path(doc["discovery_file"]).is_absolute() and Path(doc["cli_config_file"]).is_absolute(),
            "isolated discovery/config paths required")
    require(isinstance(doc.get("scope_started_unix"), (int, float)) and
            0 <= time.time() - doc["scope_started_unix"] < MAX_WALL_SECONDS,
            "fresh finite scope clock required")
    require(len(doc.get("prompt", "").encode("utf-8")) <= 4096 and
            "evidence.txt" in doc.get("prompt", ""), "bounded read witness prompt required")
    require(doc.get("workspace_witness") and len(doc["workspace_witness"]) <= 128,
            "bounded workspace witness required")
    return True


def cli_environment(doc):
    allowed = ("SystemRoot", "WINDIR", "PATH", "USERPROFILE", "LOCALAPPDATA",
               "APPDATA", "TEMP", "TMP")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env["RESEARCHOS_CLI_DISCOVERY"] = doc["discovery_file"]
    env["RESEARCHOS_CLI_CONFIG"] = doc["cli_config_file"]
    return env


def command_once(argv, cwd, env, directory, label, deadline):
    stdout = directory / (label + ".stdout.raw")
    stderr = directory / (label + ".stderr.raw")
    started = time.time()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err,
                                 stdin=subprocess.DEVNULL, creationflags=0)
        reason = None
        while child.poll() is None:
            if time.time() >= deadline:
                reason = "DEADLINE"
            elif stdout.stat().st_size > MAX_RAW_BYTES or stderr.stat().st_size > MAX_RAW_BYTES:
                reason = "OUTPUT_OVERFLOW"
            if reason:
                child.kill()
                break
            time.sleep(0.05)
        try:
            actual_exit = child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            actual_exit = child.wait(timeout=2)
            reason = reason or "CHILD_DID_NOT_DRAIN"
    receipt = {"argv": argv, "cwd": str(cwd), "started_unix": started,
               "ended_unix": time.time(), "actual_exit": actual_exit,
               "first_cause": reason, "stdout_ref": pin_path(stdout), "stderr_ref": pin_path(stderr)}
    put_json(directory / (label + ".invocation.json"), receipt)
    require(reason is None and actual_exit == 0, label + " failed; original raw is sealed")
    require(stdout.stat().st_size <= MAX_RAW_BYTES and stderr.stat().st_size <= MAX_RAW_BYTES,
            label + " raw output exceeded limit")
    parsed = []
    for line in stdout.read_text(encoding="utf-8", errors="strict").splitlines():
        parsed.append(json.loads(line))
    require(parsed and all(isinstance(row, dict) for row in parsed), label + " JSONL missing")
    return receipt, parsed


def wait_qualification(db, project, runtime_id, run_id, deadline):
    while time.time() < deadline:
        reg = object_by_id(db, "RuntimeRegistration", runtime_id, project)
        model_rows = [r for r in effects(db, run_id) if r.get("payload", {}).get("capability") == "MODEL"]
        if reg.get("status") == "AVAILABLE" and len(model_rows) == 1:
            require(model_rows[0].get("state") == "CONFIRMED" and
                    counts(effects(db, run_id)) == {"MODEL": 1, "TOOL": 0},
                    "qualification used wrong effect count or state")
            return model_rows
        time.sleep(0.2)
    raise ValueError("qualification not AVAILABLE within the same 300s scope")


def fact_refs(data_root, db, run_ids):
    refs = []
    for run_id in run_ids:
        rows = list(db.execute("SELECT journal_locator FROM runtime_dispatches WHERE run=?", (run_id,)))
        require(len(rows) == 1, "one dispatch directory per run required")
        locator = rows[0][0]
        require(isinstance(locator, str) and locator == Path(locator).name, "unsafe dispatch locator")
        directory = data_root / "runtime-dispatches" / locator
        require(directory.is_dir(), "dispatch original directory missing")
        for path in sorted(directory.glob("effect-*.json")):
            raw = path.read_bytes()
            require(len(raw) <= 3 * MAX_RAW_BYTES, "effect fact oversized")
            fact = json.loads(raw)
            if fact.get("receipt", {}).get("model_transport"):
                body = fact.get("receipt", {}).get("payload", {}).get("body")
                require(isinstance(body, str) and "data: [DONE]" in body and
                        fact.get("provider_response_hash") == "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
                        "complete SSE response fact missing or changed")
            refs.append(pin_path(path))
        for name in ("stdout.raw", "stderr.raw"):
            path = directory / name
            if path.is_file():
                refs.append(pin_path(path))
    require(refs, "original broker/SDK facts absent")
    return refs


def main():
    allowed = ("precheck-bootstrap", "bootstrap", "precheck-execute", "execute")
    require(len(sys.argv) == 3 and sys.argv[1] in allowed,
            "usage: mu_sdk_trial.proposed.py precheck-bootstrap|bootstrap|precheck-execute|execute INPUT.json")
    command, input_path = sys.argv[1], Path(sys.argv[2])
    mode = "bootstrap" if command.endswith("bootstrap") else "execute"
    require(input_path.is_absolute(), "absolute input required")
    doc = json_file(input_path)
    validate_input(doc, mode)
    if command.startswith("precheck-"):
        db_path = Path(doc["data_root"]) / "researchos.sqlite"
        with readonly_db(db_path) as db:
            if mode == "bootstrap":
                require(db.execute("SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile'").fetchone()[0] == 0,
                        "isolated bootstrap DB already has a project")
            else:
                budget_chain(db, doc["project_id"], doc["goal_id"])
        print(json.dumps({"status": "SOURCE_PRECHECK_PASSED", "phase": mode,
                          "provider_requests": 0, "qualification": None}, sort_keys=True))
        return
    output = Path(doc["outcome_dir"])
    require(output.is_absolute() and not output.exists() and output.parent.is_dir(),
            "fresh absolute outcome directory required")
    output.mkdir(mode=0o700)
    deadline = doc["scope_started_unix"] + MAX_WALL_SECONDS
    cli = str(pin_file(doc["cli_binary"], "cli_binary"))
    cwd = Path(doc["repository_root"])
    require(cwd.is_absolute() and cwd.is_dir(), "repository cwd unavailable")
    env = cli_environment(doc)
    data_root = Path(doc["data_root"])
    db_path = data_root / "researchos.sqlite"
    if mode == "bootstrap":
        with readonly_db(db_path) as db:
            count = db.execute("SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile'").fetchone()[0]
            require(count == 0, "bootstrap requires an empty isolated product DB")
        init, init_rows = command_once([cli, "init", doc["workspace"]], cwd, env, output, "cli-init", deadline)
        project_ids = [row.get("project_id") for row in init_rows if row.get("project_id")]
        require(len(set(project_ids)) == 1, "CLI init project identity missing")
        goal, goal_rows = command_once([cli, "goal", doc["goal_objective"], "--project", project_ids[0]],
                                       cwd, env, output, "cli-goal", deadline)
        with readonly_db(db_path) as db:
            goals = [json.loads(row[0]) for row in db.execute(
                "SELECT body FROM domain_objects WHERE project=? AND kind='Goal'", (project_ids[0],))]
            require(len(goals) == 1, "exactly one new Goal required")
            policies = budget_chain(db, project_ids[0], goals[0]["id"])
        put_json(output / "bootstrap.result.json", {"stage": "BOOTSTRAP_ONLY", "project_id": project_ids[0],
                 "goal_id": goals[0]["id"], "policies": policies, "cli_init_ref": pin_path(output / "cli-init.invocation.json"),
                 "cli_goal_ref": pin_path(output / "cli-goal.invocation.json"), "provider_requests": 0,
                 "qualification": None, "formal_acceptance": None})
        return

    with readonly_db(db_path) as db:
        policies = budget_chain(db, doc["project_id"], doc["goal_id"])
        before = {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind='Run'", (doc["project_id"],))}
        wait_qualification(db, doc["project_id"], doc["runtime_id"],
                           doc["qualification_run_id"], deadline)
        qualification_ledgers = unknown_ledgers(db, doc["project_id"], doc["qualification_run_id"], 1)
    config_argv = [cli, "config", "set-model", "--model", PROVIDER + "/" + MODEL,
                   "--base-url", BASE, "--config-revision", str(doc["config_revision"]),
                   "--credential-ref", CREDENTIAL_REF, "--default"]
    command_once(config_argv, cwd, env, output, "cli-config", deadline)
    command_once([cli, "run", doc["prompt"], "--project", doc["project_id"], "--output", "jsonl"],
                 cwd, env, output, "cli-run", deadline)
    with readonly_db(db_path) as db:
        after = {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind='Run'", (doc["project_id"],))}
        created = after - before
        require(len(created) == 1, "exactly one ordinary Run required")
        run_id = next(iter(created))
        run = object_by_id(db, "Run", run_id, doc["project_id"])
        task = object_by_id(db, "Task", run["task_id"], doc["project_id"])
        require(task.get("goal_id") == doc["goal_id"] and task.get("status") == "EXECUTION_REPORTED",
                "ordinary turn did not settle under the pinned Goal")
        ordinary = effects(db, run_id)
        require(counts(ordinary) == {"MODEL": 2, "TOOL": 1} and
                all(row.get("state") == "CONFIRMED" for row in ordinary),
                "MODEL→TOOL→MODEL did not complete exactly once")
        require(doc["workspace_witness"] in json.dumps(ordinary, ensure_ascii=False),
                "real workspace read witness absent from tool effect")
        ordinary_ledgers = unknown_ledgers(db, doc["project_id"], run_id, 2)
        originals = fact_refs(data_root, db, [doc["qualification_run_id"], run_id])
    put_json(output / "trial.result.json", {"schema": "researchos.mu-sdk-trial.observation.v1",
             "stage": "OBSERVED_NOT_INDEPENDENTLY_ACCEPTED", "project_id": doc["project_id"],
             "goal_id": doc["goal_id"], "qualification_run_id": doc["qualification_run_id"],
             "ordinary_run_id": run_id, "provider_requests": 3, "model_effects": 3,
             "tool_effects": 1, "requested_output_tokens_ceiling": MAX_OUTPUT_TOKENS_PER_REQUEST * 3,
             "actual_billed_tokens": None, "actual_cost": None, "cost_basis": "UNKNOWN",
             "policies": policies, "qualification_ledgers": qualification_ledgers,
             "ordinary_ledgers": ordinary_ledgers, "original_fact_refs": originals,
             "cancel_fixture_ref": doc["cancel_fixture_receipt"], "formal_acceptance": None})


if __name__ == "__main__":
    main()
