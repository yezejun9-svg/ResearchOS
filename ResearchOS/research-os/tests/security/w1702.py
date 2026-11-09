"""W17/W17-02 only: current production authorization with synthetic input.

No LIVE result or independent acceptance is issued by this handler.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import uuid

import c22_fixture as c22

ROOT = Path(__file__).resolve().parents[2]
TESTS = ("TestW1702AuthorityTransitions", "TestProtectedReadRevalidation")
INCREMENT_IDS = {
    *[f"W1702-ROLE-{role}{suffix}" for role in ("EXECUTOR", "PLANNER") for suffix in ("", "-content")],
    *[f"W1702-{op}-{role}" for role in ("EXECUTOR", "PLANNER") for op in ("LIST", "REGISTER")],
    *[f"W1702-READ-{scenario}" for scenario in ("role-removed", "provider-unavailable", "provider-private-error")],
    "W1702-REGISTER-REVOKED", "W1702-FROZEN-BODY-CLOSED",
    *["PROTECTED-REVALIDATE-" + scenario for scenario in ("grant-revoked", "credential-revoked", "artifact-stale", "corrupt-body")],
}


def validate_increment(events: list[dict]) -> list[dict]:
    endings = [e for e in events if not e.get("Test") and e.get("Action") in ("pass", "fail")]
    c22.require(len(endings) == 1 and endings[0]["Action"] == "pass", "Increment package did not pass")
    passed = {e["Test"] for e in events if e.get("Test") and e["Action"] == "pass" and "/" not in e["Test"]}
    c22.require(passed == set(TESTS) and not any(e["Action"] in ("fail", "skip") for e in events), "Increment tests absent, failed or skipped")
    rows = []
    for line in "".join(e.get("Output", "") for e in events).splitlines():
        for prefix in ("W1702_ASSERTION ", "W11_PROTECTED_ASSERTION "):
            if line.startswith(prefix):
                rows.append(json.loads(line[len(prefix):]))
    ids = [r.get("assertion_id") for r in rows]
    c22.require(len(ids) == len(INCREMENT_IDS) and len(ids) == len(set(ids)) and set(ids) == INCREMENT_IDS,
                "Increment requires exact nonzero unique assertion inventory")
    c22.require(all(r.get("status") == "PASS" and r.get("expected") == r.get("actual") for r in rows), "Increment assertion differs")
    return rows


def source_manifest() -> dict:
    paths = subprocess.check_output([
        "git", "ls-files", "internal/domain", "internal/auth", "internal/store", "adapters", "evaluation",
        "ops/experiment_sandbox", "ops/protected_fixture", "migrations/sqlite", "spec/v2.0/contracts", "go.mod", "go.sum",
        "execution/toolchains/locked.json", "execution/project_identity.json",
    ], cwd=ROOT, text=True, encoding="utf-8").splitlines()
    paths += ["tests/security/w1702.py", "tests/security/test_w1702_handler.py", "tests/security/c22_fixture.py", "tests/security/c22_expected.json"]
    return {p: c22.digest(ROOT / p) for p in sorted(set(paths))}


def main() -> int:
    result = {"status": "FAIL", "assertions": 0, "assertion_ids": [], "receipt": None}
    out = report = None
    started = time.monotonic()
    try:
        c22.require(len(sys.argv) == 1 and os.environ.get("RESEARCHOS_TASK_ID") == "W17"
                    and os.environ.get("RESEARCHOS_CHECK_ID") == "W17-02" and not os.environ.get("RESEARCHOS_CASE_ID"),
                    "Only TASK=W17 CHECK=W17-02 without CASE or arguments is bound")
        c22.require(os.environ.get("RESEARCHOS_MEASUREMENT_MODE", "FIXTURE") == "FIXTURE"
                    and os.environ.get("RESEARCHOS_MODE", "FIXTURE") == "FIXTURE", "Only FIXTURE is supported")
        locked = c22.read(ROOT / "execution/toolchains/locked.json")["tools"]
        go = Path(os.environ.get("RESEARCHOS_GO", locked["go"]["path"]))
        c22.require(go.is_file() and c22.digest(go) == "sha256:" + locked["go"]["sha256"], "Locked Go hash differs")
        c22.require(c22.digest(Path(sys.executable)) == "sha256:" + locked["python"]["sha256"], "Locked Python hash differs")
        run = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
        out = ROOT / "execution/v2.4/receipts/W17/W17-02" / run
        out.mkdir(parents=True)
        result["receipt"] = str(out / "report.json")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        hashes = source_manifest()
        c22.save(out / "source-manifest.json", {"source_commit": head, "files": hashes,
            "tools": {"go": {"path": str(go), "sha256": c22.digest(go)},
                      "python": {"path": sys.executable, "sha256": c22.digest(Path(sys.executable))}}})
        report = {"status": "FAIL", "task_id": "W17", "check_id": "W17-02", "mode": "FIXTURE",
            "execution_status": "EXECUTION_REPORTED", "independent_acceptance": "PENDING", "source_commit": head,
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "cwd": str(ROOT),
            "platform": platform.platform(), "commands": [], "assertions": [],
            "formal_holdout_accessed": False, "LIVE_qualified": False, "BOUNDED_AUTO_granted": False,
            "resource_status": {
                "local_development": {"status": "AVAILABLE", "scope": "Synthetic Windows AppContainer and scoped loopback HTTP"},
                "C22": {"status": "FIXTURE_ONLY", "formal_resource": "NOT_OBSERVED",
                    "reason": "CanaryStore permits unrestricted same-user reads; independent verifier-owned formal data/label/detail access is not demonstrated by this fixture. Existing protected summary/import/qualification production paths are outside this probe. FrozenProvider.Read rejects control-host body export by design; that does not establish qualification service availability or absence."},
                "A11": {"status": "PARENT_LIVE_NOT_RUN", "formal_resource": "NOT_EXERCISED",
                    "reason": "This increment tests application credential/grant revocation only. Actual device pairing, UI secret masking and full LIVE_WINDOWS acceptance remain parent scope."},
                "C07": {"status": "PARENT_CASE_NOT_RUN", "formal_resource": "LOCAL_FIXTURE_AVAILABLE",
                    "reason": "Candidate self-score denial is exercised by C22. Full hard-evidence-versus-model-score case is not claimed by this card."}},
            "limitations": [
                "Different same-user agents are not independent verifier identities.",
                "HTTP is issued by the host under scoped credentials; AppContainer proves file read/write denial separately and does not issue HTTP.",
                "Guessed preview/export/log/backup routes return 404 and are NOT capability evidence. Protected content endpoint is real; actual local backup engine refuses protected artifacts.",
                "Service-log marker scan covers generated server logs and controlled provider failures only, not all possible exception paths.",
                "FrozenProvider body denial is a local method probe only; no live service probe or new body-export provider.",
                "No independent verifier read of formal labels, production declassification, full C22/A11/C07 or parent acceptance is issued."]}
        env = dict(os.environ, GOTOOLCHAIN="local", GOENV="off", RESEARCHOS_GO=str(go), RESEARCHOS_C22_EVIDENCE=str(out))
        suites = (("c22", "^" + c22.TEST + "$"), ("increment", "^(" + "|".join(TESTS) + ")$"))
        all_assertions = []
        for name, selector in suites:
            command = [str(go), "test", "./internal/domain", "-run", selector, "-count=1", "-timeout=120s", "-json"]
            stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:
                completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
            except subprocess.TimeoutExpired as error:
                (out / (name + ".stdout.jsonl")).write_bytes(error.stdout or b"")
                (out / (name + ".stderr.log")).write_bytes(error.stderr or b"")
                report["commands"].append({"argv": command, "cwd": str(ROOT), "started_at": stamp,
                    "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "exit_code": None, "timed_out": True})
                raise
            (out / (name + ".stdout.jsonl")).write_bytes(completed.stdout)
            (out / (name + ".stderr.log")).write_bytes(completed.stderr)
            report["commands"].append({"argv": command, "cwd": str(ROOT), "started_at": stamp,
                "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "exit_code": completed.returncode})
            c22.require(completed.returncode == 0, name + " Go execution failed; raw evidence preserved")
            events = [json.loads(line) for line in completed.stdout.decode("utf-8").splitlines() if line]
            if name == "c22":
                checked = c22.validate_evidence(out, events, c22.read(c22.EXPECTED))
                c22.save(out / "permission-matrix.json", checked["permission_matrix"])
                c22.save(out / "native-matrix.json", checked["native_matrix"])
                c22.save(out / "marker-scan.json", checked["scan"])
                rows = checked["assertions"]
            else:
                rows = validate_increment(events)
            all_assertions.extend(rows)
            report["assertions"] = all_assertions
        ids = [a["assertion_id"] for a in all_assertions]
        c22.require(len(ids) == 154 and len(ids) == len(set(ids)), "Combined unique inventory must contain 154 assertions")
        c22.require(hashes == source_manifest(), "Source changed during execution")
        report["status"] = result["status"] = "PASS"
        result["assertions"], result["assertion_ids"] = len(ids), ids
    except Exception as error:
        result["error"] = str(error)
        if report is not None:
            report["error"] = traceback.format_exc()
    finally:
        if out is not None and report is not None:
            report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report["elapsed_seconds"] = round(time.monotonic() - started, 3)
            report["evidence_hashes"] = {p.name: c22.digest(p) for p in sorted(out.iterdir()) if p.is_file()}
            c22.save(out / "report.json", report)
            c22.save(out / "evidence-index.json", {"files": {p.name: c22.digest(p) for p in sorted(out.iterdir()) if p.is_file()}})
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
