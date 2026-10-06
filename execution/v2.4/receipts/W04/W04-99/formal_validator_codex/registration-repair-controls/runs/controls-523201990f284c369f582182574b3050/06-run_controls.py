"""Archive one real locked-Python execution of the ten new synthetic controls."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[5]
SCOPE = "SYNTHETIC_REGISTRATION_REPAIR_CONTROLS_NOT_PRODUCT_EVIDENCE"
FROZEN = {
    BASE / "validate.py": "008759e428d993da3a277cb915818ebcac67fd4b73027d732413271d6e81cb96",
    REPO / "execution/v2.4/formal_case_index.py": "26ade1e6c23e43d4ca5f26bd39313aa5fdf747350a872bf7bf8de71edda4a776",
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def ref(path): return {"path": path.relative_to(REPO).as_posix(), "sha256": sha(path)}
def write(path, value):
    with path.open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

def main():
    for path, digest in FROZEN.items():
        if sha(path) != digest: raise ValueError("root-frozen reader changed: " + str(path))
    locked_path = REPO / "execution/toolchains/locked.json"
    locked = json.loads(locked_path.read_text(encoding="utf-8"))["tools"]["python"]
    if Path(sys.executable).resolve() != Path(locked["path"]).resolve() or sha(Path(sys.executable)) != locked["sha256"]:
        raise ValueError("requires actual locked Python")
    paths = [*FROZEN, BASE / "test_validate.py", BASE / "README.md", HERE / "README.md",
             HERE / "test_registration_repair.py", HERE / "run_controls.py", locked_path]
    paths.extend(REPO / ".local/worktrees/v24-continuation/spec/v2.4/contracts" / name
                 for name in ("acceptance.json", "tasks.json", "execution.plan.json"))
    hashes = {str(path.relative_to(REPO)): sha(path) for path in paths}
    input_digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    runs = HERE / "runs"; runs.mkdir(exist_ok=True)
    for previous in runs.glob("*/receipt.json"):
        old = json.loads(previous.read_text(encoding="utf-8"))
        if old["input_digest"] == input_digest and old["exit_code"] != 0:
            raise ValueError("unchanged failed control input cannot be rerun")
    run = runs / ("controls-" + uuid.uuid4().hex); run.mkdir()
    snapshots = []
    for number, path in enumerate(paths):
        destination = run / (str(number).zfill(2) + "-" + path.name)
        destination.write_bytes(path.read_bytes())
        snapshots.append({"original_ref": ref(path), "snapshot_ref": ref(destination)})
    write(run / "source_snapshot.json", {"scope": SCOPE, "sources": snapshots})
    argv = [locked["path"], "-B", "-X", "utf8", str(HERE / "test_registration_repair.py")]
    env = {key: value for key, value in os.environ.items() if key.upper() in
           ("SYSTEMROOT", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PROGRAMDATA", "PATH")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = now()
    result = subprocess.run(argv, cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (run / "stdout.txt").write_bytes(result.stdout); (run / "stderr.txt").write_bytes(result.stderr)
    unchanged = all(sha(path) == hashes[str(path.relative_to(REPO))] for path in paths)
    observations = [json.loads(line.split(" ", 1)[1]) for line in result.stdout.decode("utf-8").splitlines()
                    if line.startswith("REGISTRATION_REPAIR_CONTROL ")]
    expected = {(r, s) for r in ("local", "public") for s in
                ("dispatcher_not_in_product_vector", "wrong_native_hash", "changed_current_bytes", "post_read_change", "child_input_unpinned")}
    observed = {(row["reader"], row["scenario"]) for row in observations if row["status"] == "PASS"}
    complete = len(observations) == 10 and observed == expected
    receipt = {"schema": "researchos.registration-repair-controls.v1", "scope": SCOPE,
               "status": "PASS" if result.returncode == 0 and unchanged and complete else "FAIL",
               "actual_argv": argv, "cwd": str(HERE), "environment_variable_names": sorted(env),
               "started_at": start, "ended_at": now(), "exit_code": result.returncode,
               "locked_python": locked, "toolchain_ref": ref(locked_path), "input_digest": input_digest,
               "source_hashes": hashes, "source_snapshot_ref": ref(run / "source_snapshot.json"),
               "source_unchanged_during_run": unchanged, "control_roster_complete": complete,
               "control_count": len(observations), "stdout": ref(run / "stdout.txt"), "stderr": ref(run / "stderr.txt"),
               "formal_case_count_delta": 0, "product_commands_executed": 0,
               "prior_controls_reclaimed": False}
    write(run / "receipt.json", receipt)
    scratch = HERE / ".synthetic-work"
    if scratch.exists() and scratch.resolve().parent == HERE.resolve() and not any(scratch.iterdir()): scratch.rmdir()
    print(json.dumps({"status": receipt["status"], "scope": SCOPE, "control_count": len(observations),
                      "receipt": ref(run / "receipt.json")}, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS" else 1

if __name__ == "__main__": sys.exit(main())
