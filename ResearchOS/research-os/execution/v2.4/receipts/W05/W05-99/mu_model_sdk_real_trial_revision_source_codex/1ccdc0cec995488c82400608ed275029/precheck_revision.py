"""Pure in-memory negative checks on selected AST functions; no candidate import."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "mu_sdk_trial.v2.proposed.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
compile(tree, str(SOURCE), "exec", dont_inherit=True)
funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
needed = ("require", "authority_binding", "exact_qualification", "guard_deadline",
          "command_once", "validate_input", "complete_sse")
assert all(name in funcs for name in needed)
module = ast.fix_missing_locations(ast.Module(body=[funcs[name] for name in needed], type_ignores=[]))
PIN = {"path": "SOURCE", "sha256": "a" * 64, "bytes": 1}
REG = "reg"
REV = "rev"
GRANT = "grant"
uuid = "a" * 32
source_commit = "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7"
limits = {"maximum_provider_requests": 3, "requested_output_tokens_total": 8192,
          "total_wall_seconds": 300}
doc = {"run_uuid": uuid, "phase": "bootstrap", "data_root": "D:/isolated",
       "workspace": "D:/witness", "repository_root": "D:/repo",
       "once_path": "D:/isolated/trial-once/" + uuid + ".json",
       "root_registration_started_at_utc": "2026-10-08T00:00:00Z",
       "qualification_task_id": None, "qualification_run_id": None,
       "qualification_epoch": None, "runtime_id": None,
       "profile_entity_ref": None, "qualification_profile_hash": None,
       "public_route_manifest": None, "runtime_profile": None,
       "root_registration": REG, "root_review": REV, "root_grant": GRANT,
       "owner_lease": "lease", "root_checkpoint": "checkpoint",
       "outer_job_contract": "job", "job_probe_receipt": "probe",
       "controller_source": "controller_source", "controller_review": "controller_review"}
reg = {"schema": "researchos.mu-sdk-trial-root-registration.v1", "actor_id": "codex:/root",
       "run_uuid": uuid, "phase": "bootstrap", "source_commit": source_commit,
       "source_ref": PIN, "limits": limits, "data_root": doc["data_root"],
       "workspace": doc["workspace"], "repository_root": doc["repository_root"],
       "once_path": doc["once_path"], "started_at_utc": doc["root_registration_started_at_utc"],
       "qualification_task_id": None, "qualification_run_id": None,
       "qualification_epoch": None, "runtime_id": None,
       "profile_entity_ref": None, "qualification_profile_hash": None,
       "public_route_manifest_ref": None, "runtime_profile_ref": None, "owner": "root"}
review = {"schema": "researchos.mu-sdk-trial-nonauthor-review.v1",
          "decision": "SOURCE_AND_SCOPE_REVIEWED", "actor_id": "different-reviewer",
          "run_uuid": uuid, "registration_ref": REG, "source_ref": PIN,
          "runtime_profile_ref": None, "public_route_manifest_ref": None}
grant = {"schema": "researchos.mu-sdk-trial-root-grant.v1", "actor_id": "codex:/root",
         "decision": "DENY", "run_uuid": uuid, "phase": "bootstrap",
         "registration_ref": REG, "review_ref": REV, "source_ref": PIN,
         "limits": limits, "once_path": doc["once_path"],
         "data_root": doc["data_root"], "workspace": doc["workspace"],
         "repository_root": doc["repository_root"],
         "qualification_run_id": None, "runtime_id": None, "profile_entity_ref": None,
         "outer_job_ref": "job", "controller_review_ref": "controller_review",
         "runtime_profile_ref": None, "public_route_manifest_ref": None}
fake_refs = {REG: reg, REV: review, GRANT: grant, "lease": {}, "checkpoint": {},
             "job": {}, "probe": {}, "controller_review": {}}
ns = {"__file__": str(SOURCE), "Path": Path, "os": os, "time": time, "json": json,
      "datetime": datetime, "timezone": timezone,
      "SOURCE_COMMIT": source_commit, "ROOT": Path("D:/repo"),
      "MAX_PROVIDER_REQUESTS": 3, "MAX_WALL_SECONDS": 300,
      "MAX_OUTPUT_TOKENS_TOTAL_REQUESTED": 8192,
      "MAX_OUTPUT_TOKENS_PER_REQUEST": 2730,
      "PROVIDER": "opencode-go", "BASE": "https://opencode.ai/zen/go/v1",
      "MODEL": "deepseek-v4.1-flash", "CREDENTIAL_REF": "cred-ref",
      "REVIEW_SHA": "b" * 64,
      "parse_pinned_json": lambda ref, label: fake_refs[ref],
      "pin_file": lambda ref, label: PIN,
      "pin_path": lambda path: PIN,
      "os_job_membership": lambda: (_ for _ in ()).throw(AssertionError("Job query reached after fake grant")),
      "canonical_dir": lambda raw, label: Path(raw),
      "json_file": lambda path: {},
      "validate_public_route": lambda doc: None}
exec(compile(module, str(SOURCE), "exec", dont_inherit=True), ns)

def must_reject(call, expected):
    try:
        call()
    except ValueError as exc:
        assert expected in str(exc), (expected, str(exc))
    else:
        raise AssertionError("negative case unexpectedly accepted: " + expected)

must_reject(lambda: ns["authority_binding"](doc, "bootstrap"), "Root grant")

class StaleMarkerDB:
    def execute(self, statement, args):
        assert "runtime_qualification_runs" in statement
        return [("old-task", "old-run", "old-runtime", 1, "plan", "profile", "owner")]

stale = {"project_id": "p", "runtime_id": "new-runtime",
         "qualification_run_id": "new-run", "qualification_task_id": "new-task",
         "qualification_epoch": 2}
must_reject(lambda: ns["exact_qualification"](StaleMarkerDB(), stale),
            "trusted current qualification run marker")
must_reject(lambda: ns["guard_deadline"](time.monotonic() - 1, "Popen"),
            "absolute Root deadline exhausted")
must_reject(lambda: ns["command_once"]([], None, None, None, "exhausted", time.monotonic() - 1),
            "absolute Root deadline lacks launch/evidence reserve")
assert ns["complete_sse"](b'data: {"ok":true}\n\ndata: [DONE]\n\n')
assert not ns["complete_sse"](b'data: {"content":"[DONE]"}\n\n')

intake = {"decision": "RESOURCE_ACCESS_VERIFIED_UNQUALIFIED_RUNTIME",
          "resource": {"provider_id": ns["PROVIDER"], "base_url": ns["BASE"],
                       "model_id": ns["MODEL"], "credential_ref_only": ns["CREDENTIAL_REF"],
                       "private_root_ref_only": "D:/old-resource"}}
ns["json_file"] = lambda path: intake
shape = {**doc, "schema": "researchos.mu-sdk-trial.executable-input.v1",
         "source_commit": source_commit, "maximum_provider_requests": 3,
         "total_wall_seconds": 300, "requested_output_tokens_total": 8192,
         "qualification_requests": 1, "ordinary_requests": 2,
         "cli_binary": PIN, "intake_review": {"path": "INTAKE", "sha256": ns["REVIEW_SHA"], "bytes": 1},
         "discovery_file": "D:/isolated/discovery.json",
         "cli_config_file": "D:/isolated/cli.json",
         "prompt": "read evidence.txt", "workspace_witness": "witness"}
ns["ROOT"] = Path("D:/repo")
ns["__file__"] = "D:/repo/execution/source.py"
must_reject(lambda: ns["validate_input"]({**shape, "data_root": "D:/old-resource"}, "bootstrap"),
            "disjoint from the entire old product resource root")
must_reject(lambda: ns["validate_input"]({**shape, "data_root": "D:/old-resource/new"}, "bootstrap"),
            "disjoint from the entire old product resource root")

control = (HERE / "apps_control_main.v2.proposed.go").read_text(encoding="utf-8")
host = (HERE / "internal_host_host.v2.proposed.go").read_text(encoding="utf-8")
vault = (HERE / "internal_host_vault.v2.proposed.go").read_text(encoding="utf-8")
assert control.index("hostboundary.ValidateTrialVaultIsolation(dataDir, *trialVault)") < control.index("rt.AcquireDataRootLease(dataDir)") < control.index("store.Open(")
assert host.index("ValidateTrialVaultIsolation(filepath.Dir(cfg.Dir), cfg.ReadOnlyModelVaultDir)") < host.index("os.MkdirAll(cfg.Dir")
assert "os.SameFile" in vault and "filepath.EvalSymlinks" in vault
results = {"schema": "researchos.mu-sdk-trial-v2-pure-negative-precheck.v1",
           "candidate_imported": False, "product_or_child_started": False,
           "mutable_product_writes": 0, "provider_requests": 0,
           "negative_cases": ["fake Root grant rejected before Job check/output/Popen",
                              "old qualification marker rejected before profile/effect reuse",
                              "expired absolute deadline rejected before Popen",
                              "same protected data root rejected",
                              "descendant protected data root rejected",
                              "Go control/host guard statically precedes lease/mkdir/Open",
                              "Go isolation uses EvalSymlinks and SameFile"],
           "Go_runtime_negative_cases": "NOT_RUN_SOURCE_ONLY"}
with (HERE / "precheck-results.seal.json").open("xb") as out:
    out.write((json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
print(json.dumps(results, ensure_ascii=False))
