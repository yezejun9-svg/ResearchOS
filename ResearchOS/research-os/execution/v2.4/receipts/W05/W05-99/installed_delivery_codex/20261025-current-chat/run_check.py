"""Create-once raw command evidence for CP558 isolated tests and builder."""
import json
import os
from pathlib import Path
import subprocess
import sys

if len(sys.argv) < 4 or sys.argv[3] != "--":
    raise SystemExit("usage: run_check.py receipt-root name -- command...")
root = Path(sys.argv[1]).resolve()
name = sys.argv[2]
argv = sys.argv[4:]
target = root / name
target.mkdir(parents=True, exist_ok=False)
cwd = Path("D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-installed-delivery-20261025")
env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("RESEARCHOS_", "ROS_DESKTOP_", "NODE_", "ELECTRON_"))}
env.update({"PYTHONDONTWRITEBYTECODE": "1", "GOMODCACHE": "D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod",
            "GOCACHE": "C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-maintenance-c57-20261025/go-cache"})
(target / "recipe.json").write_text(json.dumps({"cwd": str(cwd), "argv": argv,
    "environment_policy": "RESEARCHOS_ ROS_DESKTOP_ NODE_ ELECTRON_ cleared; Python pycache disabled",
    "go_module_cache": env["GOMODCACHE"], "go_cache": env["GOCACHE"]}, indent=2), encoding="utf8")
with (target / "stdout.raw").open("xb") as stdout, (target / "stderr.raw").open("xb") as stderr:
    result = subprocess.run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, check=False)
(target / "exit.json").write_text(json.dumps({"native_exit": result.returncode}) + "\n", encoding="utf8")
print(json.dumps({"name": name, "exit": result.returncode, "receipt": str(target)}))
raise SystemExit(result.returncode)
