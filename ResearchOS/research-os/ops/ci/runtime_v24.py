"""Fail-closed v2.4 runtime LIVE routing preflight; not a formal runtime driver.

No provider, native process, external command, or caller-supplied result is run/read.
The dispatcher captures this report. Zero assertions pass until a real driver exists.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

SPEC_PINS = {
    "PACKAGE_MANIFEST.json": "4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964",
    "contracts/execution.plan.json": "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17",
    "contracts/tasks.json": "37e1bc901a8843b91ae750c90164ef58560bccc50fa011908b5f3c30809cb8d4",
    "contracts/acceptance.json": "ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66",
}
LIVE_CHECK_MODES = {
    "W05-G02": "LIVE_WINDOWS_AND_SERVICE",
    "W05-H08": "LIVE_WINDOWS", "W05-P01": "LIVE_WINDOWS", "W05-U02": "LIVE_WINDOWS",
}
A04_IDS = [f"A04-{i:02d}" for i in range(1, 7)]
GAP = "The current Mu runtime has no v2.4 formal LIVE driver for this selector. Native/provider execution and independent acceptance were not run."

class PreflightError(ValueError):
    def __init__(self, code, reason):
        super().__init__(reason)
        self.code = code

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise PreflightError("INVALID_ARGUMENT", message)

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def _json(raw):
    return json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON: {value}")))

def _one(rows, predicate, label):
    found = [row for row in rows if predicate(row)]
    if len(found) != 1:
        raise PreflightError("SPEC_CONTRACT_MISMATCH", f"expected one {label}")
    return found[0]

def load_spec(root_value):
    if not root_value or not Path(root_value).is_absolute():
        raise PreflightError("SPEC_RESOURCE_MISSING", "RESEARCHOS_V24_SPEC_ROOT must be the registry-bound absolute frozen v2.4 root; no fallback is allowed")
    root = Path(root_value)
    docs = {}
    for relative, expected in SPEC_PINS.items():
        try:
            raw = (root / relative).read_bytes()
        except OSError as error:
            raise PreflightError("SPEC_RESOURCE_MISSING", f"cannot read frozen {relative}: {error.strerror}") from error
        if hashlib.sha256(raw).hexdigest() != expected:
            raise PreflightError("SPEC_HASH_MISMATCH", f"frozen hash mismatch: {relative}")
        try:
            docs[relative] = _json(raw)
        except (ValueError, UnicodeError) as error:
            raise PreflightError("SPEC_CONTRACT_MISMATCH", f"invalid frozen JSON: {relative}") from error
    manifest = docs["PACKAGE_MANIFEST.json"]
    if manifest.get("package_id") != "researchos-implementation-spec" or manifest.get("package_version") != "2.4.0":
        raise PreflightError("SPEC_CONTRACT_MISMATCH", "expected ResearchOS specification 2.4.0")
    for relative in SPEC_PINS:
        if relative == "PACKAGE_MANIFEST.json":
            continue
        entry = _one(manifest["files"], lambda row: row.get("path") == relative, relative+" manifest entry")
        if entry.get("sha256") != SPEC_PINS[relative] or entry.get("size_bytes") != (root / relative).stat().st_size:
            raise PreflightError("SPEC_CONTRACT_MISMATCH", f"manifest binding mismatch: {relative}")
    return docs

def frozen_selection(docs, task_id, check_id, case_id):
    tasks = docs["contracts/tasks.json"]
    task = _one(tasks["tasks"], lambda row: row.get("task_id") == task_id, "W05 task")
    selection = tasks["verification_command_selection"]
    if check_id:
        gate = _one(task["task_gate_checks"], lambda row: row.get("check_id") == check_id, "runtime check")
        binding = _one(selection["parent_check_bindings"], lambda row: row.get("key") == "test.runtime" and row.get("task_id") == task_id and row.get("check_id") == check_id and not row.get("case_id"), "runtime check binding")
        if gate.get("mode") != LIVE_CHECK_MODES[check_id] or binding.get("expected_assertion_ids") != [check_id] or binding.get("key") != "test.runtime":
            raise PreflightError("SPEC_CONTRACT_MISMATCH", "runtime check mode/assertion binding mismatch")
        return gate["mode"], [{"id": check_id, "check": gate["check"], "expected": gate["expected"]}]
    case = _one(docs["contracts/acceptance.json"]["cases"], lambda row: row.get("id") == case_id, "A04 case")
    binding = _one(selection["formal_case_bindings"], lambda row: row.get("key") == "test.runtime" and row.get("task_id") == task_id and row.get("case_id") == case_id and not row.get("check_id"), "A04 formal binding")
    if (case.get("mode") != "LIVE_WINDOWS" or case.get("final_owner_task") != "W05" or case.get("command_keys") != ["test.runtime"] or [row.get("id") for row in case["assertions"]] != A04_IDS
            or binding.get("expected_assertion_ids") != A04_IDS or binding.get("key") != "test.runtime"
            or case_id not in task["owned_acceptance_ids"]):
        raise PreflightError("SPEC_CONTRACT_MISMATCH", "A04 requires exactly its six frozen LIVE assertions")
    return case["mode"], case["assertions"]

def preflight(argv=None, environ=None):
    env = os.environ if environ is None else environ
    report = {"command": "test.runtime", "driver": "v24-live-gap-preflight", "status": "BLOCKED",
              "measurement_mode": "NOT_RUN", "passed": False, "assertion_ids": [], "passed_assertion_ids": [],
              "assertions": [], "expected_assertion_ids": [], "passed_count": 0,
              "native_executed": False, "provider_executed": False, "independent_acceptance": "NOT_RUN"}
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--mode", required=True)
        args = parser.parse_args(argv)
        task, check, case = (env.get(name, "") for name in ("RESEARCHOS_TASK_ID", "RESEARCHOS_CHECK_ID", "RESEARCHOS_CASE_ID"))
        report.update(task_id=task, check_id=check, case_id=case, requested_mode=args.mode)
        if task != "W05" or (bool(check) == bool(case)) or (check and check not in LIVE_CHECK_MODES) or (case and case != "A04"):
            raise PreflightError("INVALID_SELECTOR", "require exact W05 plus one of G02/H08/P01/U02 or case A04; mixed/unknown selectors are rejected")
        if args.mode != "live":
            raise PreflightError("INVALID_MODE", "v2.4 LIVE requirements cannot run or pass in fixture mode")
        docs = load_spec(env.get("RESEARCHOS_V24_SPEC_ROOT", ""))
        required_mode, assertions = frozen_selection(docs, task, check, case)
        report.update(required_mode=required_mode, spec_version="2.4.0", spec_root=str(Path(env["RESEARCHOS_V24_SPEC_ROOT"]).resolve()), spec_sha256=dict(SPEC_PINS),
                      expected_assertion_ids=[row["id"] for row in assertions],
                      assertions=[{"assertion_id": row["id"], "check": row["check"], "expected": row["expected"], "status": "NOT_RUN", "reason": GAP} for row in assertions],
                      reason_code="IMPLEMENTATION_GAP", reason=GAP)
        return report, 1
    except PreflightError as error:
        report.update(reason_code=error.code, reason=str(error))
        return report, 2
    except (KeyError, TypeError, ValueError, OSError) as error:
        report.update(reason_code="SPEC_CONTRACT_MISMATCH", reason=f"invalid frozen contract structure: {type(error).__name__}")
        return report, 2

def main():
    report, code = preflight()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return code

if __name__ == "__main__":
    sys.exit(main())
