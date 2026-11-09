"""Independent isolated metadata fragments. Never executes recovery main or gate."""
import ast
import contextlib
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
SOURCE = ROOT / "execution/v2.4/receipts/W05/W05-99/scope7_grant_recovery_source_preparation_codex/8821517157754457be7645afa51c5177/scope7_grant_recover.v2.proposed.py"
OUT = Path(__file__).parent
raw = SOURCE.read_bytes()
assert len(raw) == 23698 and hashlib.sha256(raw).hexdigest() == "1004e4d42ac9a32e79e7188e3a91070d7fe7b0fbb3dfdc4481743199310ca7ea"
tree = ast.parse(raw, str(SOURCE))
checks = []
def ok(name, value):
    assert value, name
    checks.append({"name": name, "result": "PASS"})
def reject(name, action):
    try:
        action()
    except RuntimeError as exc:
        checks.append({"name": name, "result": "REJECT_EXPECTED", "reason": str(exc)})
    else:
        raise AssertionError(name + ": accepted")
# Execute only the original entrypoint dispatch with a stub main, never actual main.
entry = next(n for n in tree.body if isinstance(n, ast.If) and ast.unparse(n.test) == "__name__ == '__main__'")
entrycode = compile(ast.Module(body=[entry], type_ignores=[]), "<entrypoint-only>", "exec")
def dispatch(f):
    stdout, stderr = io.StringIO(), io.StringIO()
    env = {"__name__": "__main__", "main": f, "json": json, "sys": sys}
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            exec(entrycode, env)
        except SystemExit as exc:
            return exc.code, stdout.getvalue(), stderr.getvalue()
    raise AssertionError("entrypoint did not exit")
success = dispatch(lambda: 0)
ok("R1 success exits zero without false incomplete message", success == (0, "", ""))
def failing_stub():
    raise RuntimeError("SYNTHETIC_METADATA_FAILURE")
failure = dispatch(failing_stub)
ok("R1 failure exits one and preserves cause", failure[0] == 1 and "SYNTHETIC_METADATA_FAILURE" in failure[2] and "RECOVERY_INCOMPLETE" in failure[2])
# Load only standard imports, literal globals, and read-only helper definitions.
allowed = {"need", "path", "raw_at", "strict", "reference", "files_in", "process_empty"}
nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)) or isinstance(n, ast.FunctionDef) and n.name in allowed]
space = {"__file__": str(SOURCE), "__name__": "independent_readonly_fragments"}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "<readonly-helpers-only>", "exec"), space)
validate = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_existing")
start = next(i for i,n in enumerate(validate.body) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "disk" for t in n.targets))
stop = next(i for i,n in enumerate(validate.body) if ast.unparse(n).startswith("need(diagnostic["))
freeze = compile(ast.Module(body=validate.body[start:stop], type_ignores=[]), "<fixed-inventory-fragment>", "exec")
space["boundary"] = json.loads(space["BOUNDARY_REVIEW"].read_bytes())
exec(freeze, space)
ok("R2 actual immutable inventory binds PF32 and AUTH34", len(space["frozen_pf"]) == 32 and len(space["frozen_auth"]) == 34)
pf, auth = space["PF"], space["AUTH"]
target_name = "admission.head.invocation.json"
original = Path.read_bytes
changed = json.loads(original(pf / target_name))
changed["synthetic_review_mutation"] = True
changed_bytes = json.dumps(changed).encode()
copy_map = json.loads(original(auth / "preflight-copy-map.json"))
for row in copy_map["entries"]:
    if Path(row["original_ref"]["path"]).name == target_name:
        for key in ("original_ref", "copy_ref"):
            row[key]["sha256"] = hashlib.sha256(changed_bytes).hexdigest()
            row[key]["bytes"] = len(changed_bytes)
virtual = {pf / target_name: changed_bytes, auth / target_name: changed_bytes,
           auth / "preflight-copy-map.json": json.dumps(copy_map).encode()}
def simulated_bytes(p):
    return virtual[p] if p in virtual else original(p)
space["READS"] = {}
with patch.object(Path, "read_bytes", simulated_bytes):
    reject("R2 changed original plus identical copy plus revised map rejected", lambda: exec(freeze, space))
# Evaluate exact post-gate root guard with synthetic root presence; no root created.
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
root_guard = next(n for n in main.body if "execution leaf appeared during read-only gate" in ast.unparse(n))
guard = compile(ast.Module(body=[root_guard], type_ignores=[]), "<postgate-roots-only>", "exec")
scope = json.loads(space["SCOPE"].read_bytes())
space["gate_result"] = {"scope": scope}
space["path"] = lambda value, existing=True: Path(value)
for key in ("output_root", "outer_output_root", "export_root"):
    appeared = Path(scope[key])
    with patch.object(os.path, "lexists", lambda p: Path(p) == appeared):
        reject("R3 newly occupied " + key + " rejected", lambda: exec(guard, space))
fresh = {"schema": "researchos.root-process-empty-observation.v1", "actor": "codex:/root",
         "run_uuid": space["UID"], "method": "Win32_Process", "matching_processes": [],
         "native_probe_exit": 0, "command_filter_contains": space["UID"],
         "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
space["process_empty"](fresh)
ok("R3 fresh synthetic observation accepted", True)
fresh["observed_at"] = "2000-01-01T00:00:00+00:00"
reject("R3 stale post-gate observation rejected", lambda: space["process_empty"](fresh))
# Independently hash all Source-package files. Selected producer manifest is not full inventory.
def pin(p):
    data = p.read_bytes()
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
members = json.loads((SOURCE.parent / "manifest.json").read_bytes())["members"]
for ref in members:
    assert pin(ROOT / ref["path"]) == ref
all_refs = [pin(p) for p in sorted(SOURCE.parent.iterdir()) if p.is_file()]
ok("producer manifest eleven pinned members match disk", len(members) == 11)
ok("complete independent source inventory has fourteen files", len(all_refs) == 14)
report = {"schema": "researchos.scope7-independent-fragment-controls.v1", "source_ref": pin(SOURCE),
          "checks": checks, "count": len(checks), "failures": [], "source_package_all_files": all_refs,
          "producer_manifest_selected_members": 11, "producer_manifest_not_full_directory": True,
          "candidate_main_calls": 0, "grant_gate_calls": 0, "product_calls": 0,
          "canonical_writes": 0, "grant_tail_writes": 0,
          "synthetic_controls_are_not_process_observations": True}
with (OUT / "independent-controls.json").open("xb") as f:
    f.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
print(json.dumps({"checks": len(checks), "failures": 0, "report_ref": pin(OUT / "independent-controls.json"),
                  "candidate_main_calls": 0, "grant_gate_calls": 0}))

