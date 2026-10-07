"""Receipt-only W03 parent runner and fail-closed immutable evidence reuse.

Fresh runs are explicit (--run). Registered dispatch only verifies existing atoms.
No old receipts, pytest fixtures, registry or product files are mutated here.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import uuid
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PLAN_PATH = HERE / "expected.json"
PACKAGES = ["./internal/domain", "./internal/canonical", "./apps/control", "./adapters/evaluation", "./internal/host"]
GATES = {"W03-G01": "DEVELOPMENT", "W03-G02": "FIXTURE", "W03-G03": "FIXTURE"}
KEYS = {"W03-G01": "contracts.validate", "W03-G02": "test.domain", "W03-G03": "contracts.validate"}
SOURCE_PREFIXES = ("internal/", "adapters/", "evaluation/", "apps/control/", "migrations/", "contracts/", "spec/v2.0/", "tests/domain/", "tests/contracts/")
SOURCE_FILES = {"go.mod", "go.sum", "ops/ci/domain.py", "ops/ci/contracts.py"}

class EvidenceError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise EvidenceError(message)

def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result

def loads(raw):
    def reject_constant(value):
        raise EvidenceError("non-finite JSON number: " + value)
    def finite_float(value):
        parsed = float(value)
        require(math.isfinite(parsed), "non-finite JSON number: " + value)
        return parsed
    return json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=reject_constant, parse_float=finite_float)

def read(path):
    return loads(Path(path).read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def plan():
    p = read(PLAN_PATH)
    require(p["gates"] == GATES, "frozen gate modes changed")
    return p

def tool(p):
    locked = read(p["toolchain_path"])
    record = locked["tools"]["go"]
    actual = os.environ.get("RESEARCHOS_GO", record["path"])
    # tool_env resolves the registered tool to its locked absolute executable.
    require(Path(actual).is_absolute(), "RESEARCHOS_GO must resolve to locked absolute Go path")
    require(Path(actual).resolve() == Path(record["path"]).resolve(), "Go path differs from locked toolchain")
    require(sha(actual) == record["sha256"], "Go executable hash mismatch")
    return actual

def run_environment(p):
    allowed = ("SystemRoot", "SYSTEMROOT", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PROGRAMDATA", "ProgramFiles", "ProgramFiles(x86)")
    env = {k: os.environ[k] for k in allowed if k in os.environ}
    env.update(p["go_environment"])
    return env

def input_manifest(kind, gate, p):
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    selected = sorted(f for f in paths if f and (f in SOURCE_FILES or f.startswith(SOURCE_PREFIXES)))
    # Detect additions as well as changes; relevant untracked source is not silently ignored.
    extra = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    require(not any(f and (f in SOURCE_FILES or f.startswith(SOURCE_PREFIXES)) for f in extra), "untracked relevant source requires explicit input enrollment")
    hashes = {f: sha(ROOT / f) for f in selected}
    hashes["executor/gate_driver.py"] = sha(HERE / "gate_driver.py")
    hashes["executor/bridge.py"] = sha(HERE / "bridge.py")
    hashes["executor/expected.json"] = sha(PLAN_PATH)
    hashes["toolchain/locked.json"] = sha(p["toolchain_path"])
    hashes["toolchain/go.exe"] = sha(tool(p))
    if kind == "probe":
        hashes["executor/probe/main.go"] = sha(HERE / "probe/main.go")
        for name, expected in p["frozen_contract_hashes"].items():
            actual = sha(Path(p["frozen_contract_dir"]) / name)
            require(actual == expected, "frozen contract drift: " + name)
            hashes["frozen/v2.4/" + name] = actual
        for name, expected in p["fixture_hashes"].items():
            require(hashes[name] == expected, "frozen fixture drift: " + name)
        corpus = read(ROOT / "tests/contracts/fixtures/client_protocol_v2_fixtures.json")["fixtures"]
        actual_fixture_metadata = {"FIXTURE/" + row["name"]: {"expected_valid": row["expected_valid"], "schema_definition": row["schema_definition"]} for row in corpus}
        require(len(actual_fixture_metadata) == len(corpus) == 106 and actual_fixture_metadata == p["fixture_metadata"], "fixture metadata differs from pinned original corpus")
    expected = p["tests"][gate] if kind == "go" else p["probe_ids"][gate]
    require(expected and len(expected) == len(set(expected)), "empty or duplicate expected set")
    return {"schema": "w03-atom-input-v1", "gate": gate, "mode": GATES[gate], "kind": kind,
            "source_hashes": hashes, "expected_ids": expected, "environment": p["go_environment"],
            "test_packages": p["test_packages"][gate] if kind == "go" else {},
            "fixture_metadata": p["fixture_metadata"] if kind == "probe" and gate == "W03-G01" else {},
            "packages": PACKAGES if kind == "go" else [], "formal_product_acceptance": "NOT_RUN"}

def invocation(kind, gate, p):
    if kind == "go":
        return [tool(p), "test", "-count=1", "-json", "-run", "^(" + "|".join(p["tests"][gate]) + ")$", *PACKAGES]
    # execution/ is an intentionally separate module. Explicit source-file mode
    # compiles this receipt probe against the root module without editing either.
    return [tool(p), "run", "./" + (HERE / "probe/main.go").relative_to(ROOT).as_posix(), "--check", gate, "--spec", p["frozen_contract_dir"]]

def parse_go(raw, expected, exit_code, test_packages, packages=PACKAGES):
    require(type(exit_code) is int and exit_code == 0, "Go command exit must be integer zero")
    require(set(test_packages) == set(expected), "test/package expectation mismatch")
    expected_pairs = collections.Counter((test_packages[name], name) for name in expected)
    events = [loads(line) for line in raw.splitlines() if line.strip()]
    require(events, "empty Go output")
    require(not any(e.get("Action") in ("fail", "skip") for e in events), "Go emitted fail or skip")
    runs = collections.Counter((e.get("Package"), e["Test"]) for e in events if e.get("Action") == "run" and "Test" in e and "/" not in e["Test"])
    passes = collections.Counter((e.get("Package"), e["Test"]) for e in events if e.get("Action") == "pass" and "Test" in e and "/" not in e["Test"])
    require(runs == expected_pairs, "missing, unexpected, or duplicate top-level Go run/package")
    require(passes == expected_pairs, "missing, unexpected, or duplicate top-level Go pass/package")
    completed = [e.get("Package") for e in events if e.get("Action") == "pass" and "Test" not in e]
    require(collections.Counter(completed) == collections.Counter("researchos.local/research-os/" + x[2:] for x in packages), "missing or duplicate package completion")
    return {"top_level_test_ids": sorted(expected), "top_level_test_pairs": [{"package": package, "test": test} for package, test in sorted(passes)], "top_level_test_count": len(passes),
            "subtest_pass_count": sum(1 for e in events if e.get("Action") == "pass" and "/" in e.get("Test", ""))}

def parse_probe(raw, expected, exit_code, gate, fixture_metadata=None):
    require(type(exit_code) is int and exit_code == 0, "probe command exit must be integer zero")
    report = loads(raw)
    require(report.get("status") == "PASS" and report.get("check_id") == gate, "probe status or gate mismatch")
    require(report.get("formal_product_acceptance") == "NOT_RUN" and report.get("owned_acceptance_ids") == [], "probe acceptance boundary mismatch")
    checks = report.get("checks", [])
    require(checks and collections.Counter(c.get("id") for c in checks) == collections.Counter(expected), "empty, missing, extra, or duplicate probe check")
    require(all(c.get("passed") is True for c in checks), "probe contains failed check")
    groups = collections.Counter(c["group"] for c in checks)
    expected_groups = {"projection", "aggregate", "fixtures", "fixture_metadata"} if gate == "W03-G01" else {"types", "bindings"}
    require(set(groups) == expected_groups, "probe groups mismatch")
    if gate == "W03-G01":
        fs = [c for c in checks if c["group"] == "fixtures"]
        require(fixture_metadata and set(fixture_metadata) == {c["id"] for c in fs}, "fixture ID metadata mismatch")
        for c in fs:
            frozen = fixture_metadata[c["id"]]
            actual = c["detail"]
            require(type(actual.get("expected_valid")) is bool and type(actual.get("actual_valid")) is bool, "fixture validity must be boolean")
            require(actual["expected_valid"] is frozen["expected_valid"] and actual.get("schema_definition") == frozen["schema_definition"], "fixture labels differ from pinned corpus: " + c["id"])
            require(actual["actual_valid"] is frozen["expected_valid"], "fixture actual decision differs from pinned expectation: " + c["id"])
        require(len(fs) == 106 and sum(c["detail"]["expected_valid"] is True for c in fs) == 76 and sum(c["detail"]["expected_valid"] is False for c in fs) == 30, "fixture 76/30/106 shape mismatch")
    return {"group_counts": dict(groups), "new_check_groups": 2,
            "fixture_decisions": 106 if gate == "W03-G01" else 0, "probe_check_ids": [c["id"] for c in checks]}

def parse_atom(kind, gate, raw, manifest, exit_code):
    return parse_go(raw, manifest["expected_ids"], exit_code, manifest["test_packages"], manifest["packages"]) if kind == "go" else parse_probe(raw, manifest["expected_ids"], exit_code, gate, manifest["fixture_metadata"])

def atom_reference(directory):
    return {"path": directory.relative_to(HERE).as_posix(), "receipt_sha256": sha(directory / "receipt.json"), "manifest_sha256": sha(directory / "manifest.json")}

def checked_directory(ref):
    path = Path(ref["path"])
    require(not path.is_absolute() and ".." not in path.parts, "unsafe evidence reference")
    directory = (HERE / path).resolve()
    require(directory.is_relative_to(HERE / "runs"), "evidence reference outside runs")
    return directory

def verify_atom(ref, kind, gate, p):
    directory = checked_directory(ref)
    require(sha(directory / "receipt.json") == ref["receipt_sha256"], "receipt hash mismatch")
    require(sha(directory / "manifest.json") == ref["manifest_sha256"], "manifest hash mismatch")
    manifest, receipt = read(directory / "manifest.json"), read(directory / "receipt.json")
    require(manifest == input_manifest(kind, gate, p), "stale source, mode, expected set, or runtime environment")
    require(receipt["input_digest"] == digest(manifest), "input digest mismatch")
    require(receipt["gate"] == gate and receipt["mode"] == GATES[gate] and receipt["kind"] == kind, "receipt selector mismatch")
    require(receipt["status"] == "PASS" and type(receipt["exit_code"]) is int and receipt["exit_code"] == 0, "receipt not successful")
    require(receipt["invocation"] == invocation(kind, gate, p), "invocation mismatch")
    require(receipt["formal_product_acceptance"] == "NOT_RUN" and receipt["owned_acceptance_ids"] == [], "receipt acceptance boundary mismatch")
    require(sha(directory / "stdout.txt") == receipt["stdout_sha256"] and sha(directory / "stderr.txt") == receipt["stderr_sha256"], "raw evidence hash mismatch")
    require(receipt.get("started_at") and receipt.get("ended_at") and receipt.get("source_head") and receipt.get("cwd"), "missing execution provenance")
    parsed = parse_atom(kind, gate, (directory / "stdout.txt").read_text(encoding="utf-8"), manifest, receipt["exit_code"])
    require(parsed == receipt["parsed"], "raw/receipt parsed result mismatch")
    return parsed

def execute_atom(kind, gate, p):
    manifest = input_manifest(kind, gate, p)
    command = invocation(kind, gate, p)
    directory = HERE / "runs" / (gate + "-" + kind + "-" + uuid.uuid4().hex)
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / "manifest.json", manifest)
    started = timestamp()
    try:
        proc = subprocess.run(command, cwd=ROOT, env=run_environment(p), capture_output=True, timeout=600)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = error.stdout or b"", (error.stderr or b"") + b"\nW03 runner timeout\n", 124
    (directory / "stdout.txt").write_bytes(stdout)
    (directory / "stderr.txt").write_bytes(stderr)
    parsed, problem = {}, None
    try:
        require(input_manifest(kind, gate, p) == manifest, "source changed during execution")
        parsed = parse_atom(kind, gate, stdout.decode("utf-8"), manifest, code)
    except (EvidenceError, ValueError) as error:
        problem = str(error)
    receipt = {"schema": "w03-atom-receipt-v1", "gate": gate, "mode": GATES[gate], "kind": kind,
               "status": "FAIL" if problem else "PASS", "exit_code": code, "error": problem,
               "invocation": command, "cwd": str(ROOT), "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "started_at": started, "ended_at": timestamp(), "input_digest": digest(manifest),
               "stdout_sha256": sha(directory / "stdout.txt"), "stderr_sha256": sha(directory / "stderr.txt"),
               "parsed": parsed, "formal_product_acceptance": "NOT_RUN", "owned_acceptance_ids": []}
    write(directory / "receipt.json", receipt)
    return atom_reference(directory), receipt

def run_gate(gate, fresh=False):
    require(gate in GATES, "unknown parent gate")
    p = plan()
    require(os.environ.get("RESEARCHOS_TASK_ID", "W03") == "W03", "wrong task")
    require(os.environ.get("RESEARCHOS_CHECK_ID", gate) == gate, "wrong check")
    require(not os.environ.get("RESEARCHOS_CASE_ID"), "formal case forbidden")
    require(os.environ.get("RESEARCHOS_MEASUREMENT_MODE", GATES[gate]) == GATES[gate], "wrong measurement mode")
    index_path = HERE / ("current_" + gate + ".json")
    index = read(index_path) if index_path.exists() else {"gate": gate, "mode": GATES[gate], "atoms": {}}
    require(index["gate"] == gate and index["mode"] == GATES[gate], "index mode or gate mismatch")
    kinds = ["go", "probe"] if gate != "W03-G02" else ["go"]
    require(set(index["atoms"]) <= set(kinds), "unexpected atom kind")
    reports, problems = {}, []
    for kind in kinds:
        ref = index["atoms"].get(kind)
        if ref:
            try:
                reports[kind] = verify_atom(ref, kind, gate, p)
                continue
            except (EvidenceError, OSError, KeyError, ValueError) as error:
                if not fresh:
                    problems.append(kind + ": " + str(error))
                    continue
                # A known same-input failure is evidence, not permission to
                # spend another attempt. A changed manifest can be run once.
                directory = checked_directory(ref)
                previous_manifest = read(directory / "manifest.json")
                previous_receipt = read(directory / "receipt.json")
                if previous_manifest == input_manifest(kind, gate, p) and previous_receipt.get("status") == "FAIL":
                    problems.append(kind + ": existing same-input failure; no retry")
                    continue
        if not fresh:
            problems.append(kind + ": no verified current atom")
            continue
        ref, receipt = execute_atom(kind, gate, p)
        index["atoms"][kind] = ref
        write(index_path, index)
        if receipt["status"] == "PASS":
            reports[kind] = verify_atom(ref, kind, gate, p)
        else:
            problems.append(kind + ": " + str(receipt["error"]))
    passed = not problems and set(reports) == set(kinds)
    output = {"status": "PASS" if passed else "FAIL", "task_id": "W03", "check_id": gate, "mode": GATES[gate],
              "assertion_ids": [gate] if passed else [], "assertions": 1 if passed else 0,
              "expected_assertion_ids": [gate], "atomic_results": reports, "errors": problems,
              "evidence_index": index_path.relative_to(ROOT).as_posix(), "evidence_index_sha256": sha(index_path) if index_path.exists() else None,
              "formal_product_acceptance": "NOT_RUN", "owned_acceptance_ids": [], "associated_cases": {"A03": "NOT_RUN", "C04": "NOT_RUN", "C19": "NOT_RUN"}}
    if fresh:
        write(HERE / ("candidate_" + gate + ".json"), output)
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=GATES, required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    try:
        report = run_gate(args.check, args.run)
    except (EvidenceError, OSError, ValueError, KeyError) as error:
        report = {"status": "FAIL", "assertion_ids": [], "assertions": 0, "error": str(error)}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
