from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

repo = Path(r"D:/作品集/ResearchOS/research-os")
worktree = Path(__file__).resolve().parents[6]
receipt = Path(__file__).parent
if not (worktree / "go.mod").is_file():
    raise SystemExit("worktree root check failed")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lock = repo / "execution/toolchains/locked.json"
go = json.loads(lock.read_text(encoding="utf-8"))["tools"]["go"]
if sha(go["path"]) != go["sha256"]:
    raise SystemExit("locked Go hash mismatch")
selector = sys.argv[1] if len(sys.argv) > 1 else "^TestW05CLIRealLocalGoal"
tag = sys.argv[2] if len(sys.argv) > 2 else "selected"
run = receipt / tag
run.mkdir(exist_ok=True)
paths = subprocess.check_output(
    ["git", "ls-files", "apps/cli", "internal", "migrations", "spec/v2.0/contracts", "go.mod", "go.sum"],
    cwd=worktree, text=True, encoding="utf-8"
).splitlines()
paths = sorted(set(paths) | {"apps/cli/cli_stream_test.go"})

def manifest():
    files = []
    missing = []
    for relative in paths:
        path = worktree / relative
        if not path.is_file():
            missing.append(relative)
            continue
        files.append({"path": relative.replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha(path)})
    return {"files": files, "missing": missing, "tracked_path_count": len(paths)}

before = manifest()
save(run / "source-before.json", before)
argv = [go["path"], "test", "-json", "-count=1", "./apps/cli", "-run", selector, "-timeout", "120s"]
env = dict(os.environ)
env.update({
    "GOROOT": str(repo / ".local/tools/go1.27.1/go"),
    "GOPATH": str(repo / ".local/gopath"),
    "GOCACHE": str(repo / ".local/gocache"),
    "RESEARCHOS_GO": go["path"],
    "GOTOOLCHAIN": "local", "GOENV": "off", "GOPROXY": "off",
})
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
inputs = {
    "schema": "researchos.w05.goal-composition-run-input.v1",
    "scope": "REAL_LOCAL_BINDING_FIXTURE_TEST_ONLY",
    "argv": argv, "cwd": str(worktree),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip(),
    "source_before_sha256": sha(run / "source-before.json"),
    "tool_lock_sha256": sha(lock), "go_exe_sha256": sha(go["path"]),
    "runner_sha256": sha(__file__),
    "fixed_environment": {key: env[key] for key in ["GOROOT", "GOPATH", "GOCACHE", "RESEARCHOS_GO", "GOTOOLCHAIN", "GOENV", "GOPROXY"]},
    "started_at": started, "provider_calls": 0,
}
save(run / "inputs.json", inputs)
with (run / "stdout.jsonl").open("wb") as stdout, (run / "stderr.raw").open("wb") as stderr:
    try:
        completed = subprocess.run(argv, cwd=worktree, env=env, stdout=stdout, stderr=stderr, timeout=150)
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
after = manifest()
save(run / "source-after.json", after)
events = []
invalid_lines = []
for line_number, line in enumerate((run / "stdout.jsonl").read_bytes().splitlines(), 1):
    try:
        events.append(json.loads(line))
    except (ValueError, UnicodeDecodeError):
        invalid_lines.append(line_number)
passes = [row.get("Test") for row in events if row.get("Action") == "pass" and row.get("Test")]
fails = [row.get("Test") for row in events if row.get("Action") == "fail" and row.get("Test")]
skips = [row.get("Test") for row in events if row.get("Action") == "skip" and row.get("Test")]
package_pass = any(row.get("Action") == "pass" and not row.get("Test") for row in events)
result = {
    "schema": "researchos.w05.goal-composition-run-result.v1",
    "argv": argv, "integer_exit_code": int(exit_code),
    "started_at": started, "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "inputs_sha256": sha(run / "inputs.json"), "stdout_sha256": sha(run / "stdout.jsonl"),
    "stderr_sha256": sha(run / "stderr.raw"),
    "source_before_sha256": sha(run / "source-before.json"),
    "source_after_sha256": sha(run / "source-after.json"),
    "source_changed_during_run": before != after,
    "invalid_jsonl_lines": invalid_lines,
    "test_pass": passes, "test_fail": fails, "test_skip": skips,
    "package_pass": package_pass, "provider_calls": 0, "formal_case_count_delta": 0,
    "pass": exit_code == 0 and not invalid_lines and not fails and not skips and bool(passes) and package_pass and before == after,
}
save(run / "result.json", result)
print(json.dumps({"run": str(run), "pass": result["pass"], "exit": exit_code, "passes": len(passes), "fails": fails, "skips": skips, "invalid_lines": invalid_lines}, ensure_ascii=False))
if not result["pass"]:
    print((run / "stderr.raw").read_text(encoding="utf-8", errors="replace")[-5000:])
    print("".join(row.get("Output", "") for row in events)[-8000:])
sys.exit(0 if result["pass"] else 1)
