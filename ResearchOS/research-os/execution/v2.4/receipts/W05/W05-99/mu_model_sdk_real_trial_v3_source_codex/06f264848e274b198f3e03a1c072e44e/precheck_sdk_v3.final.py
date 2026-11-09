"""Pure IO, AST-extracted helper checks; no candidate import or product child."""
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import types

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "mu_sdk_trial.v3.proposed.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
compile(tree, str(SOURCE), "exec", dont_inherit=True)
funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
names = ("require", "go_hash", "exact_ref", "object_by_id", "object_by_ref",
         "exact_artifact_ref", "effects", "counts", "model_ledgers",
         "phase_basis", "authorized_child", "exact_qualification",
         "guard_deadline", "command_once")
assert all(name in funcs for name in names)
module = ast.fix_missing_locations(ast.Module(body=[funcs[name] for name in names],
                                              type_ignores=[]))
ns = {"__file__": str(SOURCE), "hashlib": hashlib, "json": json, "Path": Path,
      "time": time, "datetime": datetime, "timezone": timezone,
      "subprocess": subprocess, "PROVIDER": "opencode-go",
      "MODEL": "deepseek-v4.1-flash", "BASE": "https://opencode.ai/zen/go/v1",
      "CREDENTIAL_REF": "protected-ref", "MAX_RAW_BYTES": 2 * 1024 * 1024,
      "pin_path": lambda path: {"path": "source", "sha256": "a" * 64, "bytes": 1},
      "cli_environment": lambda doc: {"PATH": "p", "RESEARCHOS_CLI_CONFIG": doc["cli_config_file"],
                                      "RESEARCHOS_CLI_DISCOVERY": doc["discovery_file"]}}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
        target.id == "PHASE_BASIS_KEYS" for target in node.targets):
        ns["PHASE_BASIS_KEYS"] = ast.literal_eval(node.value)
exec(compile(module, str(SOURCE), "exec", dont_inherit=True), ns)

def reject(call, marker=None):
    try:
        call()
    except ValueError as exc:
        if marker:
            assert marker in str(exc), (marker, str(exc))
    else:
        raise AssertionError("negative case unexpectedly accepted")

doc = {key: None for key in ns["PHASE_BASIS_KEYS"]}
doc.update({"schema": "researchos.mu-sdk-trial.executable-input.v1", "source_commit": "x",
            "phase": "execute", "run_uuid": "a" * 32,
            "cli_binary": {"path": "D:/cli.exe", "sha256": "0" * 64, "bytes": 100},
            "cli_config_file": "D:/new-config.json", "discovery_file": "D:/new-discovery.json",
            "repository_root": "D:/repo", "prompt": "read evidence.txt",
            "project_id": "p", "goal_id": "g", "config_revision": 1})
frozen = ns["phase_basis"](doc, "execute")
ns["parse_pinned_json"] = lambda pin, label: frozen
doc["input_basis_ref"] = "basis"
doc["_sealed_phase_basis"] = frozen
config = frozen["child_argv"]["cli-config"]
ns["authorized_child"](doc, "cli-config", config, Path(doc["repository_root"]),
                       frozen["child_environment"])
for key, change in (("cli_binary", {"path": "D:/other.exe", "sha256": "1" * 64, "bytes": 100}),
                    ("cli_config_file", "D:/other-config.json"),
                    ("discovery_file", "D:/other-discovery.json"),
                    ("goal_id", "foreign-goal"), ("prompt", "different prompt"),
                    ("workspace_witness", "foreign-witness"),
                    ("cancel_fixture_receipt", {"path": "foreign", "sha256": "1" * 64, "bytes": 1}),
                    ("bootstrap_receipt", {"path": "foreign", "sha256": "1" * 64, "bytes": 1})):
    changed = {**doc, key: change}
    reject(lambda changed=changed: ns["authorized_child"](
        changed, "cli-config", config, Path(changed["repository_root"]),
        frozen["child_environment"]), "PHASE_BASIS_CHANGED_BEFORE_CHILD")
reject(lambda: ns["authorized_child"](doc, "cli-config", config + ["--extra"],
                                      Path(doc["repository_root"]), frozen["child_environment"]),
       "CHILD_ARGV_CWD_ENV_CHANGED")
source_text = SOURCE.read_text(encoding="utf-8")
assert source_text.count('get("input_basis_ref") == doc["input_basis_ref"]') == 3
assert source_text.index("basis == phase_basis(doc, mode)") < source_text.index("reg.get(\"schema\")")
assert "doc[\"_sealed_phase_basis\"] = basis" in source_text

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def fixture():
    project, run_id, task_id, runtime_id = "project", "run", "task", "runtime"
    technical_fields = {"adapter": "mu", "adapter_revision": "1",
                        "capabilities": ["MODEL", "TOOL"], "platform": "windows",
                        "measurement_mode": "LIVE", "credential_ref": "sealed"}
    technical = ns["go_hash"]([technical_fields[key] for key in
                               ("adapter", "adapter_revision", "capabilities", "platform",
                                "measurement_mode", "credential_ref")])
    profile = {"runtime_id": runtime_id, "technical_hash": technical}
    profile_raw = encode(profile).encode()
    profile_hash = "sha256:" + hashlib.sha256(profile_raw).hexdigest()
    profile_art = {"id": "profile-art", "revision": 1, "content_hash": profile_hash,
                   "storage_key": "profile-key", "byte_size": len(profile_raw)}
    profile_ref = {"entity_type": "Artifact", "id": profile_art["id"],
                   "revision": 1, "content_hash": profile_hash}
    accepted_output = {"id": "output", "revision": 1, "content_hash": "sha256:" + "2" * 64}
    output_ref = {"entity_type": "Artifact", "id": "output", "revision": 1,
                  "content_hash": accepted_output["content_hash"]}
    observation = {"state": "SETTLED", "children_stopped": True, "queue_empty": True,
                   "protocol": {"settled": True}, "spec": {"run_id": run_id,
                   "task_id": task_id, "epoch": 4, "profile_hash": ns["go_hash"](profile_ref),
                   "technical_hash": technical}}
    log_raw = encode(observation).encode()
    log_hash = "sha256:" + hashlib.sha256(log_raw).hexdigest()
    log_art = {"id": "log", "revision": 1, "content_hash": log_hash,
               "storage_key": "log-key", "byte_size": len(log_raw)}
    log_ref = {"entity_type": "Artifact", "id": "log", "revision": 1, "content_hash": log_hash}
    task = {"id": task_id, "revision": 3, "project_id": project,
            "task_type": "runtime_qualification", "status": "ACCEPTED",
            "active_run_id": run_id, "acceptance_id": "accepted",
            "input_refs": [profile_ref], "output_artifact_ids": ["output"],
            "acceptance_contract": {"contract_hash": "sha256:" + "3" * 64},
            "context_bundle_id": "context"}
    task_snapshot = {**task, "revision": 2, "status": "EXECUTION_REPORTED"}
    task_ref = {"entity_type": "Task", "id": task_id, "revision": 2, "content_hash": None}
    run = {"id": run_id, "task_id": task_id, "runtime_id": runtime_id,
           "status": "SETTLED", "children_stopped": True, "queue_empty": True,
           "lease_epoch": 4, "context_bundle_id": "context",
           "result_artifact_ids": ["output"], "executor_principal_id": "executor",
           "created_at": "2026-10-08T01:00:00Z"}
    accepted = {"id": "accepted", "revision": 1, "project_id": project,
                "subject_ref": task_ref, "verdict": "PASS", "run_id": run_id,
                "contract_hash": task["acceptance_contract"]["contract_hash"],
                "input_refs": task["input_refs"], "artifact_refs": [output_ref],
                "executor_principal_ids": ["executor"],
                "verifier_principal_id": "independent",
                "measurement_mode": "LIVE",
                "created_at": datetime.now(timezone.utc).isoformat()}
    accepted["receipt_hash"] = ns["go_hash"](accepted)
    runtime = {"id": runtime_id, "status": "AVAILABLE",
               "qualification_ids": ["accepted"], **technical_fields}
    plan = {"runtime_id": runtime_id, "profile_ref": profile_ref,
            "max_validity_seconds": 3600}
    marker = (task_id, run_id, runtime_id, 4, ns["go_hash"](plan),
              ns["go_hash"](profile_ref), task["acceptance_contract"]["contract_hash"],
              ns["go_hash"](task["input_refs"]), "context", "root-owner")
    doc = {"project_id": project, "runtime_id": runtime_id, "qualification_run_id": run_id,
           "qualification_task_id": task_id, "qualification_epoch": 4,
           "root_registration_started_at_utc": "2026-10-08T00:00:00Z",
           "qualification_owner_root": "root-owner",
           "qualification_profile_hash": marker[5], "profile_entity_ref": profile_ref,
           "runtime_profile": {"path": "none", "sha256": hashlib.sha256(profile_raw).hexdigest(),
                               "bytes": len(profile_raw)}}
    class DB:
        def __init__(self):
            self.docs = {("Task", task_id): task, ("Run", run_id): run,
                         ("RuntimeRegistration", runtime_id): runtime,
                         ("AcceptanceReceipt", "accepted"): accepted,
                         ("Artifact", "profile-art"): profile_art,
                         ("Artifact", "log"): log_art, ("Artifact", "output"): accepted_output}
            self.versions = {("Task", task_id, 2): task_snapshot,
                             ("Artifact", "profile-art", 1): profile_art,
                             ("Artifact", "log", 1): log_art}
            self.marker = marker
            self.observation = observation
            self.log_raw = log_raw
        def execute(self, sql, args):
            if "runtime_qualification_runs" in sql: return [self.marker] if args == (project, run_id) else []
            if "FROM domain_objects WHERE kind=?" in sql:
                obj = self.docs.get((args[0], args[1]))
                return [(encode(obj),)] if obj and (len(args) == 2 or args[2] == project) else []
            if "FROM domain_versions" in sql:
                obj = self.versions.get((args[1], args[2], args[3]))
                return [(encode(obj),)] if obj and args[0] == project else []
            if "runtime_qualification_plans" in sql:
                return [(encode(plan), marker[4], "root-owner")]
            if "runtime_bindings" in sql:
                return [(encode(profile_ref), marker[5], technical)]
            if "runtime_qualification_approvals" in sql:
                return [(run_id, encode(log_ref), ns["go_hash"](["accepted"]))]
            if "FROM artifact_uses" in sql: return [("log-key",)] if args == (project, "log", run_id, 4) else []
            if "runtime_observations" in sql:
                return [(encode(self.observation), ns["go_hash"](self.observation))]
            if "FROM uploaded_content" in sql:
                return [(profile_raw if args[1] == "profile-key" else self.log_raw,)]
            if "FROM resource_effects" in sql:
                return [(1, "effect-1", 2, encode({"state": "CONFIRMED",
                         "payload": {"capability": "MODEL"}}))]
            if "BudgetLedgerEntry" in sql:
                return [(encode({"id": "unknown-1", "run_id": run_id,
                         "provider_request_id": "effect-1", "operation": "UNKNOWN",
                         "money": None, "cost_basis": "UNKNOWN"}),)]
            raise AssertionError("unexpected readonly query: " + sql)
    return DB(), doc

db, qdoc = fixture()
models, ledgers = ns["exact_qualification"](db, qdoc)
assert len(models) == len(ledgers) == 1 and ledgers[0]["money"] is None
reject(lambda: ns["exact_qualification"](db, {**qdoc, "project_id": "foreign"}),
       "trusted current qualification run marker")
reject(lambda: ns["exact_qualification"](db, {**qdoc, "profile_entity_ref": {"id": "old"}}),
       "qualified runtime does not contain")
db.observation = {**db.observation, "spec": {**db.observation["spec"], "run_id": "old-run"}}
reject(lambda: ns["exact_qualification"](db, qdoc), "approved log bytes differ")

class Child:
    def poll(self): return 1
    def wait(self, timeout=None): return 1
    def kill(self): pass
starts = []
ns["subprocess"] = types.SimpleNamespace(
    DEVNULL=-1, Popen=lambda *args, **kwargs: (starts.append(1) or Child()),
    TimeoutExpired=subprocess.TimeoutExpired)
ns["authorized_child"] = lambda *args: None
ns["os_job_membership"] = lambda: None
receipts = []
ns["put_json"] = lambda path, receipt: receipts.append(receipt)
ns["pin_path"] = lambda path: (_ for _ in ()).throw(OSError("raw hash failed"))
with tempfile.TemporaryDirectory(prefix="sdk-v3-check-", dir=HERE) as temp:
    root = Path(temp).resolve(strict=True)
    assert HERE in root.parents
    reject(lambda: ns["command_once"]({}, ["fake"], root, {}, root, "one",
                                      time.monotonic() + 5), "original raw/exit")
    assert len(starts) == 1 and receipts[0]["actual_exit"] == 1
    assert receipts[0]["first_cause"] == "CHILD_NONZERO_EXIT:1"
    assert receipts[0]["secondary_failures"] and "raw hash failed" in receipts[0]["secondary_failures"][0]
    reject(lambda: ns["command_once"]({}, ["fake"], root, {}, root, "expired",
                                      time.monotonic() - 1), "launch/evidence reserve")
    assert len(starts) == 1
control = (HERE / "apps_control_main.v3.proposed.go").read_text(encoding="utf-8")
host = (HERE / "internal_host_host.v3.proposed.go").read_text(encoding="utf-8")
vault = (HERE / "internal_host_vault.v3.proposed.go").read_text(encoding="utf-8")
assert control.index("ValidateTrialStorageLayout(dataDir") < control.index("rt.AcquireDataRootLease(dataDir)") < control.index("store.Open(")
assert host.index("ValidateTrialStorageLayout(filepath.Dir(cfg.Dir)") < host.index("os.MkdirAll(cfg.Dir")
assert host.index("os.MkdirAll(cfg.Dir") < host.index("privateDir(cfg.Dir)")
assert "os.Lstat(path)" in vault and "filepath.EvalSymlinks(path)" in vault
result = {"schema": "researchos.mu-sdk-trial-v3-pure-precheck.v1",
          "candidate_imported": False, "go_cli_sdk_provider_executions": 0,
          "positive": ["phase basis and exact child argv/cwd/env", "current EntityRef.id profile plus separate accepted receipt/log Artifact and UNKNOWN ledger"],
          "negative": ["CLI/config/discovery/Goal/prompt/witness/evidence basis drift",
                       "foreign project/old profile/swapped log observation",
                       "native exit1 remains first after raw hash failure",
                       "expired deadline prevents Popen",
                       "Go trial host/DB leaf checks precede lease/Open/mkdir/privateDir"],
          "actual_windows_junction_test": "NOT_RUN_SOURCE_ONLY"}
with (HERE / "precheck.v3.final.json").open("xb") as out:
    out.write((json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
print(json.dumps(result, ensure_ascii=False))
