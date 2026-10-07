import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(r"D:\作品集\ResearchOS\research-os")
out = Path(__file__).resolve().parent
plan = root / ".local/worktrees/v24-continuation/spec/v2.4/contracts/execution.plan.json"
state = root / "execution/v2.4/step_state.json"
sys.path.insert(0, str(root / "execution/v2.4"))
from formal_case_index import derive_formal_cases


def save(name, value):
    with (out / name).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


start = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = derive_formal_cases(root, state, plan)
save("formal-index.json", result)
save("formal-index.invocation.json", {"kind": "ACTUAL_READ_ONLY_DERIVE_CALL", "function": "formal_case_index.derive_formal_cases", "repo": str(root), "state": str(state), "plan": str(plan), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "derived_integrity": result["integrity"], "formal_cases_accepted": result["formal_cases_accepted"], "accepted_case_ids": result["accepted_case_ids"], "product_gate_executed": False})
argv = [sys.executable, "-B", "-X", "utf8", str(plan.parent.parent / "tools/task_packet.py"), "show", "W05-99", "--state", str(state)]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
proc = subprocess.run(argv, cwd=root, capture_output=True)
for name, raw in [("task-packet.stdout.raw", proc.stdout), ("task-packet.stderr.raw", proc.stderr)]:
    with (out / name).open("xb") as stream:
        stream.write(raw)
save("task-packet.invocation.json", {"argv": argv, "cwd": str(root), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": proc.returncode, "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
cp = json.loads((root / "execution/v2.4/checkpoint.json").read_bytes())
print(json.dumps({"current_formal_cases_accepted": result["formal_cases_accepted"], "accepted_case_ids": result["accepted_case_ids"], "derive_integrity": result["integrity"], "task_packet_actual_exit": proc.returncode, "checkpoint_keys": list(cp), "formal_increment": 0}))
sys.exit(proc.returncode)
