"""Current W01 parent gates. No inference, acceptance writes, or route reselection.

Receipts are exclusive-create, per invocation. Historical qualification bytes are
inputs only. LIVE_WINDOWS describes the host, while all scenario data is FIXTURE.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PIN = HERE / "parent_inputs.json"
SELECTORS = ("W01-G01", "W01-G02", "W01-G03", "W01-G04")
MODES = dict(zip(SELECTORS, ("DEVELOPMENT", "FIXTURE", "LIVE_WINDOWS", "DEVELOPMENT")))
W18 = "execution/v2.4/receipts/W18/W18-02/gui-20261006-031719-41175c"
TESTS = (
    "TestW0602SessionSingleWriterHandoff",
    "TestClientCancelChangesCanonicalRun",
    "TestClientResumeNeverRestartsPreviousRun",
    "TestClientSameWriterRenewsExpiredLease",
    "TestRuntimeMuTypedCancelStopsTransport",
    "TestW14SessionProjectionRecoveryAfterReportCommit",
    "TestW06Step4NegativesPartA",
)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def strict_results(rows, required):
    """Reject missing/duplicate/false/string truthiness, including zero assertions."""
    if not isinstance(rows, list) or not rows or not required:
        return False
    if any(not isinstance(row, dict) for row in rows):
        return False
    ids = [row.get("id") for row in rows]
    return (all(isinstance(key, str) and key for key in ids) and
            len(ids) == len(set(ids)) and set(required) <= set(ids) and
            all(row.get("ok") is True for row in rows))


def source_delta(expected, current, allowed_additions):
    changed = [key for key, value in expected.items() if current.get(key) != value]
    extra = {key: value for key, value in current.items() if key not in expected}
    unapproved = [key for key, value in extra.items() if allowed_additions.get(key) != value]
    return {"ok": not changed and not unapproved, "changed_or_missing": changed,
            "unapproved_additions": unapproved, "bounded_additions": extra}


def parse_go(stdout, required):
    rows, seen, bad, assertions, output_by_test = [], set(), [], [], {}
    for line in stdout.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            bad.append("non_json_go_output")
            continue
        rows.append(row)
        name, action = row.get("Test"), row.get("Action")
        if name in required and action == "pass":
            if name in seen:
                bad.append("duplicate_test_pass:" + name)
            seen.add(name)
        if action in {"skip", "fail"}:
            bad.append(action + ":" + str(name))
        output_by_test[name] = output_by_test.get(name, "") + row.get("Output", "")
    # go test -json splits long writes into multiple Output events. Reassemble
    # each test stream before parsing complete newline-delimited assertions.
    for output in output_by_test.values():
        for line in output.splitlines():
            if line.startswith("W06_ASSERTION "):
                try:
                    value = json.loads(line.removeprefix("W06_ASSERTION "))
                except ValueError:
                    bad.append("malformed_named_assertion")
                    continue
                assertions.append(value)
                if value.get("status") != "PASS":
                    bad.append("failed_named_assertion")
    bad += ["missing_test:" + name for name in required if name not in seen]
    if not any(row.get("Action") == "pass" and "Test" not in row for row in rows):
        bad.append("missing_package_pass")
    return {"ok": not bad, "tests": sorted(seen), "failures": bad, "assertions": assertions}


class Gate:
    def __init__(self, selector):
        self.selector = selector
        self.run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12]
        self.out = REPO / "execution/v2.4/receipts/W01/W01-99" / self.run_id
        self.out.mkdir(parents=True, exist_ok=False)
        self.pin = read(PIN)
        self.main = Path(self.pin["resource_root"])
        self.checks, self.inputs, self.commands = [], {}, []
        self.local = REPO / ".local/w0199" / self.run_id
        self.local.mkdir(parents=True, exist_ok=False)

    def check(self, key, ok, detail):
        self.checks.append({"id": key, "ok": ok is True, "detail": detail})

    def input(self, rel, expected=None, root=None):
        path = (root or REPO) / rel
        actual = digest(path)
        self.inputs[str(path)] = actual
        if expected is not None and actual != expected:
            raise ValueError("INPUT_HASH_DRIFT: " + rel)
        return path

    def pinned(self, rel):
        return self.input(rel, self.pin["files"][rel])

    def data(self, rel):
        return read(self.pinned(rel))

    def cmd(self, label, argv, cwd=REPO, env=None, timeout=240):
        start = dt.datetime.now(dt.timezone.utc).isoformat()
        kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        try:
            result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True,
                                    timeout=timeout, encoding="utf-8", errors="replace", **kwargs)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            code = 124
            stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
            stderr = "TIMEOUT " + str(timeout) + "\n" + (exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else exc.stderr or "")
        for suffix, value in (("stdout", stdout), ("stderr", stderr)):
            with (self.out / (label + "." + suffix + ".txt")).open("x", encoding="utf-8") as stream:
                stream.write(value)
        record = {"label": label, "argv": list(map(str, argv)), "cwd": str(cwd), "exit_code": code,
                  "started_at": start, "ended_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        save(self.out / (label + ".command.json"), record)
        self.commands.append(record)
        return code, stdout, stderr

    def tool(self, name):
        entry = self.pin["tools"][name]
        path = Path(entry["path"])
        if digest(path) != entry["sha256"]:
            raise ValueError("TOOL_HASH_DRIFT:" + name)
        self.inputs[str(path)] = entry["sha256"]
        return path

    def env(self):
        # A fixture never receives provider credentials from the caller's environment.
        result = {key: value for key, value in os.environ.items()
                  if not key.startswith(("RESEARCHOS_", "ROS_", "OPENAI_", "ANTHROPIC_", "DEEPSEEK_"))
                  and not key.endswith(("API_KEY", "ACCESS_TOKEN"))}
        result.update(GOTOOLCHAIN="local", GOENV="off", GOPATH=str(self.main / ".local/gopath"),
                      GOCACHE=str(self.main / ".local/gocache"),
                      PATH=str(self.tool("node").parent) + os.pathsep + result.get("PATH", ""))
        return result

    def source_snapshot(self):
        paths = subprocess.check_output(["git", "ls-files", "apps/cli", "apps/control", "apps/desktop/main",
                 "apps/desktop/preload", "apps/web/src", "internal", "adapters", "migrations", "contracts", "go.mod", "go.sum"],
                 cwd=REPO, encoding="utf-8").splitlines()
        return {path: digest(REPO / path) for path in paths}

    def inherited_dual_end(self):
        prefix = self.pin.get("current_sample", W18)
        result = self.data(prefix + "/result.json")
        meta = self.data(prefix + "/fixture-metadata.json")
        native = self.data(prefix + "/native-session.json")
        resumed = self.data(prefix + "/native-resumed-writer.json")["snapshot"]
        cli = json.loads(self.pinned(prefix + "/cli-status.stdout.txt").read_text(encoding="utf-8"))
        source = self.data(prefix + "/source-hashes.json")
        drift = [path for path, value in source.items() if digest(REPO / path) != value]
        current = self.source_snapshot()
        delta = source_delta(source, current, self.pin.get("allowed_additive_sources", {})) if prefix != W18 else {"ok": not drift}
        self.inputs.update({str(REPO / path): value for path, value in current.items()})
        self.inputs.update({str(REPO / path): digest(REPO / path) for path in source})
        # Raw files and commands all stay byte-bound to the independent slice review.
        for path in self.pin["files"]:
            if path.startswith(prefix + "/"):
                self.pinned(path)
        review = self.data("execution/v2.4/receipts/W18/W18-02/independent_review_final_codex.json")
        self.check("dual_end_source_current", not drift and delta["ok"], {"source_count": len(source), "drift": drift, "integration_delta": delta})
        self.check("dual_end_reviewed_method", review["verdict"] == "ACCEPT_W18-02_IMPLEMENTATION_SLICE",
                   {"method": "Existing independently reviewed fixture/CDP method; current sample still requires independent W01 review",
                    "current_sample": prefix, "historical_w18_source_drift": self.pin.get("historical_w18_source_drift", [])})
        rows = [{"id": k, "ok": v} for k, v in result["cli_checks"].items()] + [
                {"id": "gui_" + k, "ok": v} for k, v in result["gui_checks"].items()]
        required = self.pin["dual_end_assertions"]
        self.check("dual_end_exact_assertions", strict_results(rows, required) and set(required) == {r["id"] for r in rows},
                   {"required": required, "actual": rows, "mode": result["mode"]})
        session = next(row["result"] for row in cli["operations"] if row["method"] == "session.get")
        self.check("dual_end_raw_same_identity", all(session[key] == native[key] == resumed[key] == meta[key]
                   for key in ("project_id", "session_id", "goal_id")) and
                   cli["continuation"]["next_step"]["task_id"] == meta["task_id"] and
                   session["core_build_id"] == resumed["core_build_id"] == meta["core_build_id"],
                   {"session_id": meta["session_id"], "goal_id": meta["goal_id"], "task_id": meta["task_id"],
                    "core_build_id": meta["core_build_id"], "evidence_mode": "FIXTURE"})
        self.check("dual_end_not_provider_acceptance", result["mode"] == "FIXTURE" and
                   result["provider_calls_by_harness"] == 0 and result["formal_cases_accepted"] == [],
                   "Actual CLI and Electron processes on Windows, constructed data, zero provider calls")

    def g01(self):
        inventory = self.data("execution/v2.4/inventory.json")
        candidate = self.data("execution/v2.4/source_candidates.json")
        review = self.data("execution/v2.4/receipts/W00/W00-01/independent_review.json")
        self.check("local_inventory_before_candidate", dt.datetime.fromisoformat(inventory["created_at"]) <
                   dt.datetime.fromisoformat(candidate["created_at"]),
                   {"inventory": inventory["created_at"], "candidate": candidate["created_at"]})
        self.check("inventory_authorized_and_independent", review["verdict"] == "ACCEPT" and
                   inventory["authorization"] == self.pin["inventory_authorization"], inventory["authorization"])
        tools = inventory["tools"]
        statuses = {key: tools[key]["status"] for key in self.pin["inventory_statuses"]}
        self.check("not_checked_never_not_found", statuses == self.pin["inventory_statuses"], statuses)
        manifest = read(self.input(self.pin["spec_manifest"], self.pin["spec_manifest_sha256"], self.main))
        mismatches = []
        for row in manifest["files"]:
            path = "third_party/mu/" + row["path"]
            actual = digest(self.input(path))
            if actual != row["sha256"]:
                mismatches.append(path)
        self.check("fixed_source_manifest_reused", len(manifest["files"]) == 12 and not mismatches and
                   candidate["primary_candidate"]["commit"] == self.pin["mu_commit"],
                   {"files": len(manifest["files"]), "mismatches": mismatches})
        self.check("fallback_honestly_unchecked", candidate["fallback_candidate"]["status"] == "NOT_TOUCHED",
                   candidate["fallback_candidate"])
        tightened = self.data("execution/v2.4/receipts/W01/W01-01/W01-01_evidence_tightened.json")
        self.check("tightened_source_review", tightened["status"] == "PASS", "Exact accepted tightened source evidence, not broad keyword proxy")

    def g02(self):
        self.inherited_dual_end()
        before = self.source_snapshot()
        save(self.out / "product-sources-before.json", before)
        inherited = self.pin.get("current_counterexamples")
        if inherited:
            previous = self.data(inherited + "/product-sources-before.json")
            delta = source_delta(previous, before, self.pin.get("allowed_additive_sources", {}))
            self.check("counterexample_inputs_still_current", delta["ok"], {"basis": "Original successful seven-test invocation; parser failure did not alter raw execution", "integration_delta": delta})
            command = self.data(inherited + "/qualification-counterexamples.command.json")
            raw = self.pinned(inherited + "/qualification-counterexamples.stdout.txt").read_text(encoding="utf-8")
            self.pinned(inherited + "/qualification-counterexamples.stderr.txt")
            code = command["exit_code"]
            self.check("counterexample_exact_command", command["argv"] == [str(self.tool("go")), "test", "./internal/domain",
                       "-run", "^(" + "|".join(TESTS) + ")$", "-count=1", "-json", "-timeout=180s"], command)
            self.tool("mu_worker")
        else:
            env = self.env()
            env["RESEARCHOS_MU_BUNDLE"] = str(self.tool("mu_worker"))
            code, raw, _ = self.cmd("qualification-counterexamples", [self.tool("go"), "test", "./internal/domain",
                        "-run", "^(" + "|".join(TESTS) + ")$", "-count=1", "-json", "-timeout=180s"], env=env)
        parsed = parse_go(raw, TESTS)
        save(self.out / "go-assertion-inventory.json", parsed)
        self.check("current_product_counterexamples", code == 0 and parsed["ok"], parsed)
        ids = {row["assertion_id"] for row in parsed["assertions"] if row.get("status") == "PASS"}
        required = self.pin["required_go_assertions"]
        self.check("named_negative_coverage", set(required) <= ids, {"required": required, "observed": sorted(ids)})
        self.check("real_worker_cancelled_no_retry", "MU_CANCEL inflight_HTTP_stopped=true sandbox_stopped=true provider_calls=1" in raw,
                   "Local httptest server only; real locked Mu worker process. HTTP stopped, sandbox stopped, no retry")
        after = self.source_snapshot()
        save(self.out / "product-sources-after.json", after)
        self.check("product_sources_stable", before == after, "All tracked build inputs remained byte-identical")
        self.inputs.update({str(REPO / path): value for path, value in before.items()})

    def g03(self):
        self.check("actual_windows", os.name == "nt", sys.platform)
        if os.name != "nt":
            return
        if self.pin.get("current_sample"):
            self.inherited_dual_end()
            prefix = self.pin["current_sample"]
            original = self.data(prefix + "/receipt.json")
            required = ["qualification_sample_installed_exactly", "go-version", "node-version", "cli-version",
                        "installed_cli_same_host", "installed_desktop_started_actual_native", "qualification_host_client_versions",
                        "installed_actual_dual_end_current", "build_inputs_stable"]
            rows = [r for r in original["checks"] if r["id"] in required]
            self.check("installed_observations_current", strict_results(rows, required), rows)
            assembled = self.data(prefix + "/assembly-files.json")
            installed = self.data(prefix + "/installed-files.json")
            self.check("installed_all_bytes_identical", assembled == installed and len(installed) > 0,
                       {"files": len(installed), "manifest": prefix + "/installed-files.json"})
            supplemental = self.data(self.pin["cleanup_resolution"])
            self.check("temporary_cleanup_resolved", supplemental["status"] == "PASS" and
                       supplemental["original_run_id"] == original["run_id"] and
                       not Path(supplemental["sample_directory"]).exists(), supplemental)
            for path, value in supplemental["additional_build_source_hashes"].items():
                self.input(path, value)
            self.check("additional_build_sources_current", bool(supplemental["additional_build_source_hashes"]),
                       "Supplementary source measurement against unchanged baseline; original raw GUI evidence not rewritten")
            return
        from windows_sample import run_sample
        run_sample(self)

    def g04(self):
        route = self.data("execution/v2.4/route.json")
        reuse = self.data("execution/v2.4/reuse_decisions.json")
        adr = self.pinned("docs/adr/ADR-next-v24-route.md")
        review = self.data("execution/v2.4/receipts/W01/W01-03/independent_review.json")
        obligations = self.data("execution/v2.4/receipts/W01/W01-02/carry_forward_obligations.json")
        self.check("route_exact_and_independently_reviewed", route["selected_route"] == "MU_FORK" and
                   route["provisional"] == "NO" and route["product_acceptance"] == "NOT_RUN" and
                   route["adr_sha256"] == digest(adr) and review["verdict"] == "ACCEPT",
                   "Pinned final route/reuse/ADR and independent review remain unchanged; no repair reset or reselection")
        gaps = {name: value for name, value in reuse["per_capability"].items() if value["decision"] == "CUSTOM_GAP"}
        self.check("every_custom_gap_exact_reviewed_scope", gaps == self.pin["custom_gaps"], gaps)
        self.check("carry_forward_all_retained", obligations["carry_forward"] == self.pin["carry_forward"] and
                   route["carry_forward_ref"] == "execution/v2.4/receipts/W01/W01-02/carry_forward_obligations.json",
                   {"obligations": obligations["carry_forward"], "disposition": "retained; not all discharged by W01"})
        self.check("no_qm_failure_fullstack_fallback", reuse["per_capability"]["qoder_remote_adapter"]["decision"] == "OPTIONAL_EXTENSION_NOT_SELECTED"
                   and route["fallback"]["status"] == "NOT_TRIGGERED" and route["jev"]["status"] == "NOT_RUN",
                   {"qoder": reuse["per_capability"]["qoder_remote_adapter"], "fallback": route["fallback"], "jev": route["jev"]})
        self.pinned("execution/route.json")
        self.check("historical_route_preserved", True, "Historical THIN_CORE bytes checked; no authority inheritance")

    def run(self):
        try:
            self.input("qualification/v2.4/qualify.py")
            self.input("qualification/v2.4/parent_gates.py")
            self.input("qualification/v2.4/windows_sample.py")
            self.input("qualification/v2.4/dispatch_parent.py")
            self.input("qualification/v2.4/test_parent_gates.py")
            self.input("qualification/v2.4/parent_inputs.json")
            for path in self.pin.get("integration_review_files", []):
                self.pinned(path)
            self.input(self.pin["frozen_tasks"], self.pin["frozen_tasks_sha256"], self.main)
            getattr(self, "g" + self.selector[-2:])()
        except Exception as exc:
            self.check("execution_or_input_gap", False, {"type": type(exc).__name__, "message": str(exc)})
        changed = [path for path, value in self.inputs.items() if not Path(path).is_file() or digest(path) != value]
        self.check("all_inputs_stable", not changed, changed)
        required = {
            "W01-G01": ["local_inventory_before_candidate", "inventory_authorized_and_independent", "not_checked_never_not_found", "fixed_source_manifest_reused", "fallback_honestly_unchecked", "tightened_source_review"],
            "W01-G02": ["dual_end_source_current", "dual_end_reviewed_method", "dual_end_exact_assertions", "dual_end_raw_same_identity", "dual_end_not_provider_acceptance", "current_product_counterexamples", "named_negative_coverage", "real_worker_cancelled_no_retry", "product_sources_stable"],
            "W01-G03": (["dual_end_source_current", "dual_end_exact_assertions", "dual_end_raw_same_identity", "installed_observations_current", "installed_all_bytes_identical", "temporary_cleanup_resolved", "additional_build_sources_current"]
                        if self.pin.get("current_sample") else ["qualification_sample_installed_exactly", "installed_cli_same_host", "installed_desktop_started_actual_native", "qualification_host_client_versions", "installed_actual_dual_end_current", "build_inputs_stable"]),
            "W01-G04": ["route_exact_and_independently_reviewed", "every_custom_gap_exact_reviewed_scope", "carry_forward_all_retained", "no_qm_failure_fullstack_fallback", "historical_route_preserved"],
        }[self.selector] + ["all_inputs_stable"]
        ok = strict_results(self.checks, required)
        status = "PASS" if ok else "BLOCKED"
        record = {"schema": "researchos.w01.parent-gate.v1", "check_id": self.selector,
                  "invocation": {"argv": [sys.executable] + sys.argv, "cwd": str(Path.cwd()),
                                 "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, encoding="utf-8").strip(),
                                 "python_version": sys.version, "platform": sys.platform},
                  "run_id": self.run_id, "mode": MODES[self.selector], "scenario_mode": "FIXTURE" if self.selector in SELECTORS[1:3] else "DEVELOPMENT",
                  "status": status, "exit_code": 0 if ok else 4, "assertion_ids": [self.selector],
                  "required_check_ids": required,
                  "assertions": [{"id": self.selector, "ok": ok}], "checks": self.checks,
                  "source_inputs_sha256": self.inputs, "commands": self.commands,
                  "owned_acceptance_ids": [], "formal_cases_accepted": [], "whole_card_accepted": False,
                  "independent_review": "REQUIRED_SEPARATELY", "new_provider_calls": 0,
                  "limitations": ["LIVE_WINDOWS is a real Windows process qualification with constructed fixture data, not LIVE provider acceptance.",
                                  "Current immutable qualification sample is reused only after all recorded product source hashes match; historical W18 source drift remains disclosed.",
                                  "Portable sample install/startup is not a production installer, NVDA test, or W13 full-card acceptance.",
                                  "Old W01 hardcoded worker-version assertion is not inherited; actual versions and pinned bundle hashes are recorded."]}
        save(self.out / "receipt.json", record)
        save(self.out / "manifest.json", {path.name: digest(path) for path in sorted(self.out.iterdir()) if path.is_file()})
        if self.local.is_dir() and not any(self.local.iterdir()):
            self.local.rmdir()
        print(json.dumps({"check_id": self.selector, "status": status, "mode": MODES[self.selector],
                          "assertion_ids": [self.selector], "assertions": 1, "scope": "W01_PARENT_QUALIFICATION_ONLY",
                          "receipt": str(self.out / "receipt.json"),
                          "failures": [row["id"] for row in self.checks if not row["ok"]]}, ensure_ascii=False))
        return record["exit_code"]


def run(selector):
    if selector not in SELECTORS:
        print(json.dumps({"status": "NOT_IMPLEMENTED", "check_id": selector}))
        return 2
    return Gate(selector).run()
