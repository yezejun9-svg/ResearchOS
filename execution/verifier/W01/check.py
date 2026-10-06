"""Read-only W01 evidence checks; output stays in the verifier directory."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = "7a877ee9-c215-4fa2-9aeb-8623d55abd80"
BASE = ROOT / "execution/receipts/W01" / RUN
SANDBOX = ROOT / ".local/worktrees/core-qualification"
def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(argv, cwd=ROOT):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    return {"argv": list(map(str, argv)), "cwd": str(cwd), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

receipt = read(BASE / "receipt.json")
manifest = read(BASE / "artifact-manifest.json")
assert len(manifest) == 83
assert sha(BASE / "artifact-manifest.json") == receipt["artifact_manifest_hash"]
for row in manifest:
    assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
expected = receipt["receipt_hash"]
receipt["receipt_hash"] = None
assert hashlib.sha256(json.dumps(receipt, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == expected
assert sha(ROOT / "spec/v2.0/PACKAGE_MANIFEST.json") == receipt["input_manifest_hash"]
assert sha(ROOT / "execution/route.json") == receipt["route_revision"]
identity = read(ROOT / "execution/project_identity.json")
assert receipt["project_id"] == identity["project_id"]
assert receipt["executor_identity"] != "codex:/root/route_verifier"
checks = [run([sys.executable, "-X", "utf8", "qualification/core/verify_evidence.py"])]
assert checks[-1]["exit_code"] == 0
commands = list((ROOT / "qualification/core/evidence").glob("*/command.json"))
assert len(commands) == 24
for path in commands:
    command = read(path)
    for stream in ("stdout", "stderr"):
        assert sha(path.parent / (stream + ".txt")) == command[stream + "_sha256"]
source = SANDBOX / ".local/paperclip"
checks.append(run(["git", "rev-parse", "HEAD"], source))
assert checks[-1]["stdout"].strip() == "d554c4789ed3930f8a53ac9fdf6503b3187097da"
checks.append(run(["git", "status", "--short"], source))
assert checks[-1]["exit_code"] == 0 and not checks[-1]["stdout"].strip()
excerpts = read(ROOT / "qualification/core/source-excerpts.json")["files"]
for entry in excerpts:
    assert sha(source / entry["path"]) == entry["sha256"]
    lines = (source / entry["path"]).read_text(encoding="utf-8").splitlines()
    for part in entry["ranges"]:
        assert "\n".join(lines[part["start_line"]-1:part["end_line"]]) == part["text"]
probe = read(ROOT / "qualification/core/evidence/policy-probe/command.json")
assert sha(SANDBOX / "qualification/core/probe-policy.ts") == sha(ROOT / "qualification/core/probe-policy.ts")
checks.append(run(probe["argv"], Path(probe["cwd"])))
assert checks[-1]["exit_code"] == 0
observed = json.loads(checks[-1]["stdout"])
assert observed["normal_completion"]["status"] == "PASS"
assert observed["policy_clear"]["status"] == "FAIL"
assert observed["policy_clear"]["actual_patch"] == {}
checks.append(run(["git", "diff", "--name-only", receipt["base_revision"], "--", "spec/v2.0"]))
assert checks[-1]["exit_code"] == 0 and not checks[-1]["stdout"].strip()
head = run(["git", "rev-parse", "HEAD"])["stdout"].strip()
result = {"status": "PASS", "scope": "W01_ROUTE_EVIDENCE_ONLY", "verified_at": datetime.now(timezone.utc).isoformat(), "reviewed_git_head": head, "artifact_rows": len(manifest), "command_records": len(commands), "source_files_checked": len(excerpts), "product_acceptance": "NOT_RUN", "checks": checks}
(OUT / "checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k != "checks"}, ensure_ascii=False))
