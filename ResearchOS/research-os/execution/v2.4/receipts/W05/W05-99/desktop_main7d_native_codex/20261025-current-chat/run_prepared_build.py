"""Run the pre-registered native build once and retain byte-exact process streams."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
recipe_path = HERE / "build-invocation.pre.json"
recipe = json.loads(recipe_path.read_bytes())
cwd = Path(recipe["cwd"])
argv = recipe["argv"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if sha256(Path(recipe["scope_ref"])) != recipe["scope_sha256"]:
    raise SystemExit("scope hash mismatch")
if subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip() != recipe["expected_head"]:
    raise SystemExit("worktree HEAD mismatch")
if subprocess.run(["git", "show", "-s", "--format=%T", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip() != recipe["expected_tree"]:
    raise SystemExit("worktree tree mismatch")
if subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=cwd, capture_output=True, text=True, check=True).stdout:
    raise SystemExit("tracked worktree dirty")
output = Path(argv[argv.index("--output") + 1])
internal_receipts = Path(argv[argv.index("--receipts") + 1])
if output.exists() or internal_receipts.exists():
    raise SystemExit("new output or internal receipts already exist")
temp = Path(recipe["env_overrides"]["TEMP"])
temp.mkdir(parents=True, exist_ok=False)
env = os.environ.copy()
env.update(recipe["env_overrides"])
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (HERE / "builder.stdout.raw").open("xb") as stdout, (HERE / "builder.stderr.raw").open("xb") as stderr:
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL)
    code = proc.wait()
end = datetime.datetime.now(datetime.timezone.utc).isoformat()
(HERE / "builder.native-exit.txt").write_text(f"{code}\n", encoding="ascii", newline="\n")
(HERE / "builder-process.json").write_text(json.dumps({
    "started_at": start,
    "ended_at": end,
    "pid": proc.pid,
    "native_exit": code,
    "recipe_sha256": sha256(recipe_path),
    "stdout_sha256": sha256(HERE / "builder.stdout.raw"),
    "stderr_sha256": sha256(HERE / "builder.stderr.raw"),
    "output": str(output),
    "internal_receipts": str(internal_receipts),
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"native_exit={code} pid={proc.pid} output={output} internal_receipts={internal_receipts}")
sys.exit(code)
