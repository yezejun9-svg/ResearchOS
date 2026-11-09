"""Finite product-CLI Mu SDK trial; execute only after a separate Root grant.

The trial uses ResearchOS CLI -> session.send -> Mu worker -> trusted broker.
It never constructs a provider HTTP request or reads a credential. Bootstrap
creates a fresh Project/Goal; execution waits for the product's own admitted
qualification Run and then performs one CLI turn. Every adverse outcome stops.
"""

import hashlib
import ctypes
import json
import os
from pathlib import Path
import sqlite3
import stat
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
SOURCE_COMMIT = "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7"
ROOT = Path("D:/作品集/ResearchOS/research-os")
PHASE_BASIS_KEYS = (
    "schema", "source_commit", "phase", "run_uuid",
    "maximum_provider_requests", "qualification_requests", "ordinary_requests",
    "requested_output_tokens_total", "total_wall_seconds",
    "cli_binary", "intake_review", "public_route_manifest", "runtime_profile",
    "cancel_fixture_receipt", "bootstrap_receipt", "credential_revision",
    "data_root", "workspace", "repository_root", "discovery_file",
    "cli_config_file", "outcome_dir", "once_path", "root_registration_started_at_utc",
    "project_id", "goal_id", "runtime_id", "qualification_task_id",
    "qualification_run_id", "qualification_epoch", "qualification_owner_root",
    "qualification_profile_hash", "profile_entity_ref", "config_revision",
    "prompt", "workspace_witness", "goal_objective",
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def json_file(path):
    def unique(items):
        out = {}
        for key, value in items:
            require(key not in out, "duplicate JSON key")
            out[key] = value
        return out
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique)


def pin_file(pin, label):
    require(isinstance(pin, dict) and set(pin) == {"path", "sha256", "bytes"}, label + " pin shape")
    path = Path(pin["path"])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), label + " file")
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        require(not ancestor.is_symlink() and not getattr(ancestor, "is_junction", lambda: False)() and
                not getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400), label + " reparse ancestor")
    require(str(path.resolve(strict=True)).casefold() == str(path).casefold() and
            stat.S_ISREG(path.lstat().st_mode), label + " alias or nonregular")
    raw = path.read_bytes()
    require(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"], label + " pin changed")
    return path


def canonical_dir(raw, label):
    require(isinstance(raw, str) and Path(raw).is_absolute(), label + " absolute")
    path = Path(raw)
    require(path.is_dir(), label + " existing directory")
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        require(not ancestor.is_symlink() and not getattr(ancestor, "is_junction", lambda: False)() and
                not getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400), label + " reparse ancestor")
    require(str(path.resolve(strict=True)).casefold() == str(path).casefold(), label + " alias")
    return path


def parse_pinned_json(pin, label):
    path = pin_file(pin, label)
    def unique(items):
        out = {}
        for key, value in items:
            require(key not in out, label + " duplicate JSON key")
            out[key] = value
        return out
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def os_job_membership():
    require(os.name == "nt", "Windows Job required")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    assigned = ctypes.c_int()
    ok = kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(assigned))
    require(ok != 0 and assigned.value != 0, "runner process outside Windows Job")


def phase_basis(doc, mode):
    """Closed consumed-input projection; excludes only later Root authority refs."""
    require(all(key in doc for key in PHASE_BASIS_KEYS), "PHASE_BASIS_FIELD_MISSING")
    cli = str(Path(doc["cli_binary"]["path"]))
    if mode == "bootstrap":
        commands = {
            "cli-init": [cli, "init", doc["workspace"]],
            "cli-goal": [cli, "goal", doc["goal_objective"], "--project",
                         "<CLI_INIT_PROJECT_ID>"],
        }
    else:
        commands = {
            "cli-config": [cli, "config", "set-model", "--model", PROVIDER + "/" + MODEL,
                           "--base-url", BASE, "--config-revision",
                           str(doc["config_revision"]), "--credential-ref",
                           CREDENTIAL_REF, "--default"],
            "cli-run": [cli, "run", doc["prompt"], "--project", doc["project_id"],
                        "--output", "jsonl"],
        }
    return {"schema": "researchos.mu-sdk-trial-phase-basis.v1",
            "phase": mode, "run_uuid": doc["run_uuid"],
            "source_ref": pin_path(Path(__file__).resolve()),
            "consumed_input": {key: doc[key] for key in PHASE_BASIS_KEYS},
            "child_argv": commands, "cwd": str(Path(doc["repository_root"])),
            "child_environment": cli_environment(doc)}


def authorized_child(doc, label, argv, cwd, env):
    frozen = parse_pinned_json(doc["input_basis_ref"], "input_basis_ref")
    require(frozen == phase_basis(doc, doc["phase"]) and
            frozen == doc.get("_sealed_phase_basis"), "PHASE_BASIS_CHANGED_BEFORE_CHILD")
    expected = frozen["child_argv"].get(label)
    require(expected is not None, "UNAUTHORIZED_CHILD_LABEL")
    if label == "cli-goal":
        project = doc.get("_init_project_id")
        require(isinstance(project, str) and project, "CLI_INIT_PROJECT_ID_MISSING")
        expected = [project if value == "<CLI_INIT_PROJECT_ID>" else value for value in expected]
    require(argv == expected and str(cwd) == frozen["cwd"] and
            env == frozen["child_environment"], "CHILD_ARGV_CWD_ENV_CHANGED")


def authority_binding(doc, mode):
    """Check actual Root chain before an output directory, one-time mark or child exists."""
    names = ("root_registration", "root_review", "root_grant", "owner_lease",
             "root_checkpoint", "outer_job_contract", "job_probe_receipt",
             "controller_source", "controller_review")
    pinned = {name: parse_pinned_json(doc[name], name) if name != "controller_source"
              else pin_file(doc[name], name) for name in names}
    reg, review, grant = (pinned[k] for k in ("root_registration", "root_review", "root_grant"))
    lease, cp = pinned["owner_lease"], pinned["root_checkpoint"]
    job, probe = pinned["outer_job_contract"], pinned["job_probe_receipt"]
    controller = pinned["controller_review"]
    uuid = doc.get("run_uuid")
    require(isinstance(uuid, str) and len(uuid) == 32 and
            all(c in "0123456789abcdef" for c in uuid) and doc.get("phase") == mode,
            "fresh Root UUID or phase missing")
    limits = {"maximum_provider_requests": 3, "requested_output_tokens_total": 8192,
              "total_wall_seconds": 300}
    source_pin = pin_path(Path(__file__).resolve())
    basis = parse_pinned_json(doc["input_basis_ref"], "input_basis_ref")
    require(basis == phase_basis(doc, mode), "IMMUTABLE_PHASE_BASIS_CHANGED")
    require(reg.get("schema") == "researchos.mu-sdk-trial-root-registration.v1" and
            reg.get("actor_id") == "codex:/root" and reg.get("run_uuid") == uuid and
            reg.get("phase") == mode and reg.get("source_commit") == SOURCE_COMMIT and
            reg.get("source_ref") == source_pin and reg.get("limits") == limits and
            reg.get("input_basis_ref") == doc["input_basis_ref"] and
            reg.get("data_root") == doc["data_root"] and
            reg.get("workspace") == doc["workspace"] and
            reg.get("repository_root") == doc["repository_root"] and
            reg.get("once_path") == doc["once_path"] and
            reg.get("started_at_utc") == doc.get("root_registration_started_at_utc") and
            reg.get("qualification_task_id") == doc.get("qualification_task_id") and
            reg.get("qualification_run_id") == doc.get("qualification_run_id") and
            reg.get("qualification_epoch") == doc.get("qualification_epoch") and
            reg.get("runtime_id") == doc.get("runtime_id") and
            reg.get("profile_entity_ref") == doc.get("profile_entity_ref") and
            reg.get("qualification_profile_hash") == doc.get("qualification_profile_hash") and
            reg.get("public_route_manifest_ref") == doc.get("public_route_manifest") and
            reg.get("runtime_profile_ref") == doc.get("runtime_profile"),
            "Root registration changed or is a generic JSON claim")
    require(review.get("schema") == "researchos.mu-sdk-trial-nonauthor-review.v1" and
            review.get("decision") == "SOURCE_AND_SCOPE_REVIEWED" and
            review.get("actor_id") not in (None, "", "codex:/root", reg.get("owner")) and
            review.get("run_uuid") == uuid and
            review.get("registration_ref") == doc["root_registration"] and
            review.get("source_ref") == source_pin and
            review.get("input_basis_ref") == doc["input_basis_ref"] and
            review.get("runtime_profile_ref") == doc.get("runtime_profile") and
            review.get("public_route_manifest_ref") == doc.get("public_route_manifest"),
            "non-author source/scope review absent")
    require(grant.get("schema") == "researchos.mu-sdk-trial-root-grant.v1" and
            grant.get("actor_id") == "codex:/root" and
            grant.get("decision") == "ALLOW_ISOLATED_MU_SDK_TRIAL" and
            grant.get("run_uuid") == uuid and grant.get("phase") == mode and
            grant.get("registration_ref") == doc["root_registration"] and
            grant.get("review_ref") == doc["root_review"] and
            grant.get("source_ref") == source_pin and grant.get("limits") == limits and
            grant.get("input_basis_ref") == doc["input_basis_ref"] and
            grant.get("once_path") == doc["once_path"] and
            grant.get("data_root") == doc["data_root"] and
            grant.get("workspace") == doc["workspace"] and
            grant.get("repository_root") == doc["repository_root"] and
            grant.get("qualification_run_id") == doc.get("qualification_run_id") and
            grant.get("runtime_id") == doc.get("runtime_id") and
            grant.get("profile_entity_ref") == doc.get("profile_entity_ref") and
            grant.get("outer_job_ref") == doc["outer_job_contract"] and
            grant.get("controller_review_ref") == doc["controller_review"] and
            grant.get("runtime_profile_ref") == doc.get("runtime_profile") and
            grant.get("public_route_manifest_ref") == doc.get("public_route_manifest"),
            "Root grant does not authorize this exact one-time phase")
    require(lease.get("schema") == "researchos.mu-sdk-trial-owner-lease.v1" and
            lease.get("state") == "ACTIVE" and lease.get("run_uuid") == uuid and
            lease.get("owner") == reg.get("owner") and
            lease.get("data_root") == doc["data_root"] and
            datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00")) >
            datetime.now(timezone.utc), "current Root owner lease absent")
    wip = cp.get("work_in_progress", {})
    require(cp.get("head") == SOURCE_COMMIT and
            doc["root_checkpoint"]["path"] == str(Path(doc["repository_root"]) /
                                                  "execution/v2.4/checkpoint.json") and
            wip.get("mu_sdk_active_run_uuid") == uuid and
            wip.get("mu_sdk_registration_ref") == doc["root_registration"] and
            wip.get("mu_sdk_owner_lease_ref") == doc["owner_lease"],
            "current checkpoint did not grant this trial lease")
    require(job.get("schema") == "researchos.mu-sdk-trial-outer-job.v1" and
            job.get("run_uuid") == uuid and job.get("runner_pid") == os.getpid() and
            job.get("kill_on_close") is True and job.get("owns_child_tree") is True and
            job.get("wall_seconds") == 300 and
            job.get("controller_source_ref") == doc["controller_source"],
            "actual current Windows Job evidence missing")
    heartbeat_path = Path(job.get("heartbeat_path", ""))
    require(heartbeat_path.is_absolute() and
            canonical_dir(str(heartbeat_path.parent), "Job heartbeat parent") ==
            canonical_dir(doc["data_root"], "isolated data root") / "trial-control",
            "Job heartbeat outside isolated control root")
    heartbeat = json_file(heartbeat_path)
    require(heartbeat.get("schema") == "researchos.mu-sdk-trial-job-heartbeat.v1" and
            heartbeat.get("run_uuid") == uuid and heartbeat.get("runner_pid") == os.getpid() and
            heartbeat.get("active") is True and
            type(heartbeat.get("monotonic_tick")) in (int, float) and
            0 <= time.monotonic() - heartbeat["monotonic_tick"] <= 5,
            "actual outer Job lifecycle heartbeat stale")
    require(probe.get("schema") == "researchos.mu-sdk-trial-os-job-probe.v1" and
            probe.get("run_uuid") == uuid and probe.get("runner_pid") == os.getpid() and
            probe.get("member_of_expected_job") is True and
            probe.get("outer_job_ref") == doc["outer_job_contract"],
            "same-PID controller Job probe absent")
    require(controller.get("schema") == "researchos.mu-sdk-trial-controller-review.v1" and
            controller.get("decision") == "ACTUAL_JOB_LIFECYCLE_REVIEWED" and
            controller.get("actor_id") not in (None, "", "codex:/root", reg.get("owner")) and
            controller.get("run_uuid") == uuid and
            controller.get("controller_source_ref") == doc["controller_source"] and
            controller.get("outer_job_ref") == doc["outer_job_contract"] and
            controller.get("job_probe_ref") == doc["job_probe_receipt"] and
            controller.get("heartbeat_path") == str(heartbeat_path),
            "independent controller evidence absent")
    deadline = reg.get("absolute_deadline_monotonic")
    started = reg.get("started_monotonic")
    require(type(started) in (int, float) and type(deadline) in (int, float) and
            0 < deadline - started <= 300 and
            deadline == grant.get("absolute_deadline_monotonic") == job.get("absolute_deadline_monotonic") and
            0 < deadline - time.monotonic() <= 300, "absolute Root deadline changed or exhausted")
    os_job_membership()
    once = Path(doc["once_path"])
    data = canonical_dir(doc["data_root"], "isolated product root")
    require(once.is_absolute() and once.parent == data / "trial-once" and
            once.name == uuid + ".json" and once.parent.is_dir() and not once.exists(),
            "Root one-time grant already consumed or foreign")
    doc["_sealed_phase_basis"] = basis
    return deadline


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


def go_hash(value):
    # The checked qualification vectors use JSON strings, integers and maps.
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def exact_ref(ref, obj, kind):
    expected = {"entity_type": kind, "id": obj["id"], "revision": obj["revision"],
                "content_hash": obj.get("content_hash") if kind == "Artifact" else
                obj.get("receipt_hash")}
    require(ref == expected, kind + " EntityRef id/revision/content_hash changed")


def object_by_ref(db, project, ref, kind):
    require(isinstance(ref, dict) and ref.get("entity_type") == kind and
            type(ref.get("revision")) is int and ref["revision"] > 0 and
            isinstance(ref.get("id"), str), kind + " EntityRef shape changed")
    rows = list(db.execute(
        "SELECT body FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=?",
        (project, kind, ref["id"], ref["revision"])))
    require(len(rows) == 1, kind + " EntityRef original version absent")
    obj = json.loads(rows[0][0])
    exact_ref(ref, obj, kind)
    return obj


def exact_artifact_ref(db, project, identity):
    artifact = object_by_id(db, "Artifact", identity, project)
    return {"entity_type": "Artifact", "id": artifact["id"],
            "revision": artifact["revision"], "content_hash": artifact["content_hash"]}


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


def effects(db, project, run_id):
    rows = db.execute("SELECT rowid,effect_key,sequence,body FROM resource_effects WHERE project=? AND run=? ORDER BY rowid",
                      (project, run_id))
    first, latest = {}, {}
    for rowid, key, sequence, body in rows:
        first.setdefault(key, rowid)
        if key not in latest or sequence > latest[key][0]:
            observed = json.loads(body)
            require(observed.get("effect_key", key) == key, "effect key differs from its durable row")
            observed["effect_key"] = key
            latest[key] = (sequence, observed)
    return [latest[key][1] for key in sorted(first, key=first.get)]


def counts(rows):
    result = {"MODEL": 0, "TOOL": 0}
    for row in rows:
        cap = row.get("payload", {}).get("capability")
        if cap in result:
            result[cap] += 1
    return result


def model_ledgers(db, project, run_id, model_effects):
    rows = [json.loads(row[0]) for row in db.execute(
        "SELECT body FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=?",
        (project, run_id))]
    effect_keys = [row.get("effect_key") for row in model_effects]
    require(len(effect_keys) == len(set(effect_keys)) and all(effect_keys), "model effect keys not unique")
    unknown = [row for row in rows if row.get("provider_request_id") in effect_keys]
    require(len(unknown) == len(effect_keys) and
            {row.get("provider_request_id") for row in unknown} == set(effect_keys) and
            all(row.get("operation") == "UNKNOWN" for row in unknown),
            "one UNKNOWN ledger per exact MODEL effect required")
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
    require(doc.get("source_commit") == SOURCE_COMMIT, "source commit changed")
    require(doc.get("maximum_provider_requests") == MAX_PROVIDER_REQUESTS and
            doc.get("total_wall_seconds") == MAX_WALL_SECONDS and
            doc.get("requested_output_tokens_total") == MAX_OUTPUT_TOKENS_TOTAL_REQUESTED,
            "finite scope changed")
    require(doc.get("qualification_requests") == 1 and doc.get("ordinary_requests") == 2,
            "request partition changed")
    require(doc.get("phase") == mode and
            canonical_dir(doc["repository_root"], "repository root") == ROOT and
            ROOT in Path(__file__).resolve().parents,
            "trial script is not running from the pinned repository root")
    for name in ("cli_binary", "intake_review"):
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
                     "bootstrap_receipt"):
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
        cancel = json_file(doc["cancel_fixture_receipt"]["path"])
        require(cancel.get("case_id") == "TestRuntimeMuTypedCancelStopsTransport" and
                cancel.get("source_commit") == SOURCE_COMMIT and cancel.get("native_exit") == 0 and
                cancel.get("external_provider_requests") == 0 and
                cancel.get("original_io_refs"), "current local cancel fixture evidence absent")
    data_root = canonical_dir(doc["data_root"], "isolated product root")
    private_root = canonical_dir(resource["private_root_ref_only"], "old protected resource root")
    require(data_root != private_root and data_root not in private_root.parents and
            private_root not in data_root.parents and Path(doc["workspace"]).is_absolute(),
            "trial data root must be disjoint from the entire old product resource root")
    require(Path(doc["discovery_file"]).is_absolute() and Path(doc["cli_config_file"]).is_absolute(),
            "isolated discovery/config paths required")
    require(len(doc.get("prompt", "").encode("utf-8")) <= 4096 and
            "evidence.txt" in doc.get("prompt", ""), "bounded read witness prompt required")
    require(doc.get("workspace_witness") and len(doc["workspace_witness"]) <= 128,
            "bounded workspace witness required")
    return authority_binding(doc, mode)


def cli_environment(doc):
    allowed = ("SystemRoot", "WINDIR", "PATH", "USERPROFILE", "LOCALAPPDATA",
               "APPDATA", "TEMP", "TMP")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env["RESEARCHOS_CLI_DISCOVERY"] = doc["discovery_file"]
    env["RESEARCHOS_CLI_CONFIG"] = doc["cli_config_file"]
    return env


def guard_deadline(deadline, phase):
    require(time.monotonic() < deadline, "absolute Root deadline exhausted before " + phase)


def consume_once(doc, deadline):
    guard_deadline(deadline, "one-time grant consumption")
    marker = {"schema": "researchos.mu-sdk-trial-once-consumption.v1",
              "run_uuid": doc["run_uuid"], "grant_ref": doc["root_grant"],
              "phase": doc["phase"], "consumed_monotonic": time.monotonic(),
              "automatic_retry": False, "counter_reset": False}
    put_json(Path(doc["once_path"]), marker)
    guard_deadline(deadline, "one-time grant consumption completion")


def command_once(doc, argv, cwd, env, directory, label, deadline):
    # Reserve time for raw closure before spawning; the Root Job owns the hard kill.
    require(deadline - time.monotonic() > 1.0, "absolute Root deadline lacks launch/evidence reserve")
    authorized_child(doc, label, argv, cwd, env)
    os_job_membership()
    stdout = directory / (label + ".stdout.raw")
    stderr = directory / (label + ".stderr.raw")
    started, child, actual_exit, first_cause = time.monotonic(), None, None, None
    secondary = []
    try:
        with stdout.open("xb") as out, stderr.open("xb") as err:
            try:
                require(deadline - time.monotonic() > 1.0,
                        "absolute Root deadline lacks Popen/evidence reserve")
                child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err,
                                         stdin=subprocess.DEVNULL, creationflags=0)
                while child.poll() is None:
                    if time.monotonic() >= deadline - 0.5:
                        first_cause = "DEADLINE_WITH_EVIDENCE_RESERVE"
                    elif stdout.stat().st_size > MAX_RAW_BYTES or stderr.stat().st_size > MAX_RAW_BYTES:
                        first_cause = "OUTPUT_OVERFLOW"
                    if first_cause:
                        child.kill()
                        break
                    time.sleep(min(0.05, max(0.0, deadline - 0.5 - time.monotonic())))
                remaining = max(0.0, deadline - time.monotonic())
                actual_exit = child.wait(timeout=remaining) if remaining else child.poll()
                if actual_exit is None:
                    first_cause = first_cause or "CHILD_LIFECYCLE_INCOMPLETE"
            except BaseException as exc:
                first_cause = first_cause or type(exc).__name__ + ":" + str(exc)
                if child is not None and child.poll() is None:
                    try:
                        child.kill()
                        actual_exit = child.poll()
                    except BaseException as cleanup_exc:
                        secondary.append(type(cleanup_exc).__name__ + ":" + str(cleanup_exc))
    except BaseException as exc:
        first_cause = first_cause or type(exc).__name__ + ":" + str(exc)
    # Native exit is known now. Freeze it before any later raw hash/parse error.
    if actual_exit is not None and actual_exit != 0 and first_cause is None:
        first_cause = "CHILD_NONZERO_EXIT:" + str(actual_exit)
    raw_refs = {}
    for name, path in (("stdout_ref", stdout), ("stderr_ref", stderr)):
        try:
            raw_refs[name] = pin_path(path) if path.is_file() else None
        except BaseException as exc:
            raw_refs[name] = None
            secondary.append(name + ":" + type(exc).__name__ + ":" + str(exc))
    parsed = None
    if first_cause is None and not secondary:
        try:
            guard_deadline(deadline, label + " parsing")
            require(actual_exit == 0, "CHILD_NONZERO_EXIT")
            require(stdout.stat().st_size <= MAX_RAW_BYTES and stderr.stat().st_size <= MAX_RAW_BYTES,
                    "OUTPUT_OVERFLOW")
            parsed = [json.loads(line) for line in stdout.read_text(encoding="utf-8", errors="strict").splitlines()]
            require(parsed and all(isinstance(row, dict) for row in parsed), "JSONL_MISSING")
        except BaseException as exc:
            first_cause = type(exc).__name__ + ":" + str(exc)
    if first_cause is None and secondary:
        first_cause = secondary[0]
    receipt = {"argv": argv, "cwd": str(cwd), "started_monotonic": started,
               "ended_monotonic": time.monotonic(), "actual_exit": actual_exit,
               "first_cause": first_cause, "secondary_failures": secondary, **raw_refs}
    put_json(directory / (label + ".invocation.json"), receipt)
    guard_deadline(deadline, label + " evidence completion")
    require(first_cause is None and actual_exit == 0 and not secondary and parsed is not None,
            label + " failed; original raw/exit receipt is sealed")
    return receipt, parsed


def exact_qualification(db, doc):
    project, runtime_id, run_id = doc["project_id"], doc["runtime_id"], doc["qualification_run_id"]
    task_id = doc["qualification_task_id"]
    markers = list(db.execute(
        "SELECT task,run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root FROM runtime_qualification_runs WHERE project=? AND run=?",
        (project, run_id)))
    require(len(markers) == 1 and markers[0][:4] ==
            (task_id, run_id, runtime_id, doc["qualification_epoch"]),
            "trusted current qualification run marker absent or stale")
    task = object_by_id(db, "Task", task_id, project)
    run = object_by_id(db, "Run", run_id, project)
    runtime = object_by_id(db, "RuntimeRegistration", runtime_id, project)
    marker = markers[0]
    require(task.get("task_type") == "runtime_qualification" and task.get("status") == "ACCEPTED" and
            task.get("active_run_id") == run_id and
            run.get("task_id") == task_id and run.get("runtime_id") == runtime_id and
            run.get("status") == "SETTLED" and run.get("children_stopped") is True and
            run.get("queue_empty") is True and
            run.get("lease_epoch") == marker[3] and runtime.get("status") == "AVAILABLE" and
            runtime.get("measurement_mode") == "LIVE", "qualification Task/Run/runtime state mismatch")
    require(run.get("created_at", "") >= doc["root_registration_started_at_utc"],
            "qualification was created before this Root trial")
    plans = list(db.execute("SELECT plan,plan_hash,author_root FROM runtime_qualification_plans WHERE project=? AND task=? AND runtime=?",
                            (project, task_id, runtime_id)))
    bindings = list(db.execute("SELECT profile_ref,profile_hash,technical_hash FROM runtime_bindings WHERE project=? AND runtime=?",
                               (project, runtime_id)))
    require(len(plans) == len(bindings) == 1 and plans[0][1] == marker[4] and
            plans[0][2] == marker[9] == doc["qualification_owner_root"] and
            bindings[0][1] == marker[5] == doc["qualification_profile_hash"] and
            marker[6] == task.get("acceptance_contract", {}).get("contract_hash") and
            marker[7] == go_hash(task.get("input_refs")) and
            marker[8] == task.get("context_bundle_id") == run.get("context_bundle_id"),
            "current frozen plan/profile binding changed")
    plan = json.loads(plans[0][0])
    profile_ref = json.loads(bindings[0][0])
    require(go_hash(plan) == marker[4] and go_hash(profile_ref) == marker[5] and
            plan.get("runtime_id") == runtime_id and plan.get("profile_ref") == profile_ref and
            profile_ref == doc["profile_entity_ref"] and
            profile_ref in task.get("input_refs", []) and
            task.get("acceptance_id") in runtime.get("qualification_ids", []) and
            len(runtime.get("qualification_ids", [])) == 1,
            "qualified runtime does not contain this accepted profile receipt")
    acceptance = object_by_id(db, "AcceptanceReceipt", task["acceptance_id"], project)
    subject = object_by_ref(db, project, acceptance["subject_ref"], "Task")
    accepted_hash = go_hash({key: value for key, value in acceptance.items()
                             if key != "receipt_hash"})
    created = datetime.fromisoformat(acceptance["created_at"].replace("Z", "+00:00"))
    valid = plan.get("max_validity_seconds")
    require(acceptance.get("verdict") == "PASS" and
            acceptance.get("receipt_hash") == accepted_hash and
            acceptance.get("run_id") == run_id and
            acceptance.get("measurement_mode") == "LIVE" and
            acceptance.get("contract_hash") == marker[6] and
            acceptance.get("input_refs") == task.get("input_refs") and
            acceptance.get("executor_principal_ids") == [run.get("executor_principal_id")] and
            acceptance.get("verifier_principal_id") not in (None, "", run.get("executor_principal_id")) and
            subject.get("task_type") == "runtime_qualification" and
            subject.get("status") == "EXECUTION_REPORTED" and
            type(valid) is int and valid > 0 and
            0 <= (datetime.now(timezone.utc) - created).total_seconds() < valid,
            "independent current acceptance receipt changed or expired")
    approvals = list(db.execute("SELECT run,receipt_ref,qualification_hash FROM runtime_qualification_approvals WHERE project=? AND runtime=? ORDER BY revision DESC LIMIT 1",
                                (project, runtime_id)))
    require(len(approvals) == 1 and approvals[0][0] == run_id and
            approvals[0][2] == go_hash(runtime["qualification_ids"]),
            "current approval belongs to another qualification vector")
    log_ref = json.loads(approvals[0][1])
    log_artifact = object_by_ref(db, project, log_ref, "Artifact")
    output_ids = task.get("output_artifact_ids", [])
    require(output_ids and output_ids == run.get("result_artifact_ids") and
            acceptance.get("artifact_refs") ==
            [exact_artifact_ref(db, project, item) for item in output_ids],
            "independently accepted Run output vector changed")
    uses = list(db.execute(
        "SELECT storage_key FROM artifact_uses WHERE project=? AND artifact=? AND run=? AND epoch=?",
        (project, log_ref["id"], run_id, marker[3])))
    require(len(uses) == 1 and uses[0][0] == log_artifact["storage_key"],
            "approved log Artifact does not belong to this Run epoch")
    observations = list(db.execute(
        "SELECT body,receipt_hash FROM runtime_observations WHERE project=? AND run=? AND epoch=? ORDER BY observed_at DESC LIMIT 1",
        (project, run_id, marker[3])))
    raw_log = list(db.execute(
        "SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1",
        (project, log_artifact["storage_key"])))
    require(len(observations) == len(raw_log) == 1 and
            len(raw_log[0][0]) == log_artifact["byte_size"] and
            "sha256:" + hashlib.sha256(raw_log[0][0]).hexdigest() ==
            log_artifact["content_hash"] == log_ref["content_hash"] and
            json.loads(raw_log[0][0]) == json.loads(observations[0][0]) and
            go_hash(json.loads(observations[0][0])) == observations[0][1],
            "approved log bytes differ from trusted Run observation")
    observation = json.loads(observations[0][0])
    spec, protocol = observation.get("spec", {}), observation.get("protocol", {})
    require(observation.get("state") == "SETTLED" and
            observation.get("children_stopped") is True and
            observation.get("queue_empty") is True and
            protocol.get("settled") is True and
            spec.get("run_id") == run_id and spec.get("task_id") == task_id and
            spec.get("epoch") == marker[3] and spec.get("profile_hash") == marker[5] and
            spec.get("technical_hash") == bindings[0][2],
            "trusted native observation is not this qualification")
    artifact = object_by_ref(db, project, profile_ref, "Artifact")
    raw_profile = list(db.execute("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1",
                                  (project, artifact["storage_key"])))
    technical = go_hash([runtime.get(key) for key in
                         ("adapter", "adapter_revision", "capabilities", "platform",
                          "measurement_mode", "credential_ref")])
    require(len(raw_profile) == 1 and
            len(raw_profile[0][0]) == doc["runtime_profile"]["bytes"] and
            hashlib.sha256(raw_profile[0][0]).hexdigest() ==
            doc["runtime_profile"]["sha256"] and
            "sha256:" + hashlib.sha256(raw_profile[0][0]).hexdigest() == artifact["content_hash"] ==
            profile_ref["content_hash"] and
            technical == bindings[0][2] and
            json.loads(raw_profile[0][0]).get("runtime_id") == runtime_id and
            json.loads(raw_profile[0][0]).get("technical_hash") == technical,
            "sealed profile original bytes or technical identity mismatch")
    model_rows = [row for row in effects(db, project, run_id) if row.get("payload", {}).get("capability") == "MODEL"]
    require(counts(effects(db, project, run_id)) == {"MODEL": 1, "TOOL": 0} and
            len(model_rows) == 1 and model_rows[0].get("state") == "CONFIRMED",
            "qualification MODEL effect not exact and confirmed")
    return model_rows, model_ledgers(db, project, run_id, model_rows)


def wait_qualification(db, doc, deadline):
    while time.monotonic() < deadline:
        try:
            return exact_qualification(db, doc)
        except ValueError:
            time.sleep(min(0.2, max(0.0, deadline - time.monotonic())))
    raise ValueError("exact current qualification not accepted before Root deadline")


def complete_sse(raw):
    """Mirror the frozen runtime_model.go terminal-event contract on original bytes."""
    try:
        source = raw.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError:
        return False
    if not source.endswith("\n\n"):
        return False
    complete = seen_data = False
    for event in source.split("\n\n"):
        data = []
        for line in event.split("\n"):
            if line.startswith("data:"):
                data.append(line[5:].removeprefix(" "))
        if not data:
            continue
        if complete:
            return False
        payload = "\n".join(data)
        if payload == "[DONE]":
            complete = True
            continue
        try:
            observed = json.loads(payload)
        except (ValueError, TypeError):
            return False
        if not isinstance(observed, dict):
            return False
        seen_data = True
    return complete and seen_data


def fact_refs(data_root, db, project, model_effects_by_run, deadline):
    refs = []
    for run_id, expected_rows in model_effects_by_run.items():
        guard_deadline(deadline, "original MODEL fact reading")
        rows = list(db.execute("SELECT journal_locator FROM runtime_dispatches WHERE project=? AND run=?", (project, run_id)))
        require(len(rows) == 1, "one dispatch directory per run required")
        locator = rows[0][0]
        require(isinstance(locator, str) and locator == Path(locator).name, "unsafe dispatch locator")
        directory = data_root / "runtime-dispatches" / locator
        require(directory.is_dir(), "dispatch original directory missing")
        observed_keys = []
        for path in sorted(directory.glob("effect-*.json")):
            guard_deadline(deadline, "original MODEL fact hashing")
            raw = path.read_bytes()
            require(len(raw) <= 3 * MAX_RAW_BYTES, "effect fact oversized")
            fact = json.loads(raw)
            if fact.get("receipt", {}).get("model_transport"):
                body = fact.get("receipt", {}).get("payload", {}).get("body")
                require(isinstance(body, str) and complete_sse(body.encode("utf-8")) and
                        fact.get("provider_response_hash") ==
                        fact.get("receipt", {}).get("receipt_id") ==
                        "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
                        "complete SSE response fact missing or changed")
                require(fact.get("project_id") == project and fact.get("run_id") == run_id and
                        fact.get("effect_key") in {r["effect_key"] for r in expected_rows},
                        "MODEL fact does not belong to the current effect")
                observed_keys.append(fact["effect_key"])
            refs.append(pin_path(path))
        require(len(observed_keys) == len(expected_rows) and
                set(observed_keys) == {r["effect_key"] for r in expected_rows},
                "one original SSE fact per exact MODEL effect required")
        for name in ("stdout.raw", "stderr.raw"):
            path = directory / name
            if path.is_file():
                refs.append(pin_path(path))
    require(refs, "original broker/SDK facts absent")
    guard_deadline(deadline, "original evidence closure")
    return refs


def main():
    allowed = ("precheck-bootstrap", "bootstrap", "precheck-execute", "execute")
    require(len(sys.argv) == 3 and sys.argv[1] in allowed,
            "usage: mu_sdk_trial.proposed.py precheck-bootstrap|bootstrap|precheck-execute|execute INPUT.json")
    command, input_path = sys.argv[1], Path(sys.argv[2])
    mode = "bootstrap" if command.endswith("bootstrap") else "execute"
    require(input_path.is_absolute(), "absolute input required")
    doc = json_file(input_path)
    deadline = validate_input(doc, mode)
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
    guard_deadline(deadline, "one-time phase start")
    output = Path(doc["outcome_dir"])
    require(output.is_absolute() and not output.exists() and output.parent.is_dir(),
            "fresh absolute outcome directory required")
    consume_once(doc, deadline)
    output.mkdir(mode=0o700)
    guard_deadline(deadline, "output preparation")
    cli = str(pin_file(doc["cli_binary"], "cli_binary"))
    cwd = Path(doc["repository_root"])
    require(cwd.is_absolute() and cwd.is_dir(), "repository cwd unavailable")
    env = cli_environment(doc)
    data_root = Path(doc["data_root"])
    db_path = data_root / "researchos.sqlite"
    if mode == "bootstrap":
        guard_deadline(deadline, "bootstrap DB read")
        with readonly_db(db_path) as db:
            count = db.execute("SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile'").fetchone()[0]
            require(count == 0, "bootstrap requires an empty isolated product DB")
        init, init_rows = command_once(doc, [cli, "init", doc["workspace"]], cwd, env, output, "cli-init", deadline)
        project_ids = [row.get("project_id") for row in init_rows if row.get("project_id")]
        require(len(set(project_ids)) == 1, "CLI init project identity missing")
        doc["_init_project_id"] = project_ids[0]
        goal, goal_rows = command_once(doc, [cli, "goal", doc["goal_objective"], "--project", project_ids[0]],
                                       cwd, env, output, "cli-goal", deadline)
        with readonly_db(db_path) as db:
            goals = [json.loads(row[0]) for row in db.execute(
                "SELECT body FROM domain_objects WHERE project=? AND kind='Goal'", (project_ids[0],))]
            require(len(goals) == 1, "exactly one new Goal required")
            policies = budget_chain(db, project_ids[0], goals[0]["id"])
        guard_deadline(deadline, "bootstrap receipt")
        put_json(output / "bootstrap.result.json", {"stage": "BOOTSTRAP_ONLY", "project_id": project_ids[0],
                 "goal_id": goals[0]["id"], "policies": policies, "cli_init_ref": pin_path(output / "cli-init.invocation.json"),
                 "cli_goal_ref": pin_path(output / "cli-goal.invocation.json"), "provider_requests": 0,
                 "qualification": None, "formal_acceptance": None})
        return

    guard_deadline(deadline, "qualification DB read")
    with readonly_db(db_path) as db:
        policies = budget_chain(db, doc["project_id"], doc["goal_id"])
        before = {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind='Run'", (doc["project_id"],))}
        qualification_models, qualification_ledgers = wait_qualification(db, doc, deadline)
    config_argv = [cli, "config", "set-model", "--model", PROVIDER + "/" + MODEL,
                   "--base-url", BASE, "--config-revision", str(doc["config_revision"]),
                   "--credential-ref", CREDENTIAL_REF, "--default"]
    command_once(doc, config_argv, cwd, env, output, "cli-config", deadline)
    command_once(doc, [cli, "run", doc["prompt"], "--project", doc["project_id"], "--output", "jsonl"],
                 cwd, env, output, "cli-run", deadline)
    guard_deadline(deadline, "ordinary Run DB read")
    with readonly_db(db_path) as db:
        after = {row[0] for row in db.execute(
            "SELECT id FROM domain_objects WHERE project=? AND kind='Run'", (doc["project_id"],))}
        created = after - before
        require(len(created) == 1, "exactly one ordinary Run required")
        run_id = next(iter(created))
        run = object_by_id(db, "Run", run_id, doc["project_id"])
        task = object_by_id(db, "Task", run["task_id"], doc["project_id"])
        require(run.get("runtime_id") == doc["runtime_id"] and
                task.get("goal_id") == doc["goal_id"] and task.get("status") == "EXECUTION_REPORTED",
                "ordinary turn did not settle under the pinned Goal")
        ordinary = effects(db, doc["project_id"], run_id)
        require([row.get("payload", {}).get("capability") for row in ordinary] ==
                ["MODEL", "TOOL", "MODEL"] and
                counts(ordinary) == {"MODEL": 2, "TOOL": 1} and
                all(row.get("state") == "CONFIRMED" for row in ordinary),
                "MODEL→TOOL→MODEL did not complete exactly once")
        require(doc["workspace_witness"] in json.dumps(ordinary, ensure_ascii=False),
                "real workspace read witness absent from tool effect")
        ordinary_models = [row for row in ordinary if row.get("payload", {}).get("capability") == "MODEL"]
        ordinary_ledgers = model_ledgers(db, doc["project_id"], run_id, ordinary_models)
        originals = fact_refs(data_root, db, doc["project_id"],
                              {doc["qualification_run_id"]: qualification_models, run_id: ordinary_models},
                              deadline)
    guard_deadline(deadline, "final trial observation")
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
