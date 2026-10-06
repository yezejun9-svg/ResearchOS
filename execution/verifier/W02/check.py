"""Independent W02 construction checks; all local output stays beside this file."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import os
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = "c38171c1-d535-4f89-8fc4-5898890232ec"
BASE = ROOT / "execution/receipts/W02" / RUN
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def run(argv, cwd, env, timeout=90):
    started = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    return {"argv": argv, "cwd": str(cwd), "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

receipt = read(BASE / "receipt.json")
manifest = read(BASE / "artifacts.json")
assert len(manifest) == 49
assert sha(BASE / "artifacts.json") == receipt["artifact_manifest_hash"]
for row in manifest:
    assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
expected_hash = receipt.pop("receipt_hash")
def restricted_jcs(value):
    if isinstance(value, dict):
        assert all(key.isascii() for key in value)
        for item in value.values(): restricted_jcs(item)
    elif isinstance(value, list):
        for item in value: restricted_jcs(item)
    elif isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, int):
        assert abs(value) <= 9007199254740991
    else:
        assert value is None
restricted_jcs(receipt)
actual_hash = "sha256:" + hashlib.sha256(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
assert actual_hash == expected_hash
registry = read(ROOT / "execution/commands.json")
locked = read(ROOT / "execution/toolchains/locked.json")
registration_hash = sha(ROOT / "execution/commands.json")
index = read(ROOT / "execution/command_verifications.json")
assert index["registered_command_revision"] == registration_hash
counts = {}
for row in receipt["verification_results"]:
    invocation = read(ROOT / row["actual_invocation_reference"])
    assert invocation["status"] == "PASS" and invocation["exit_code"] == 0
    assert invocation["registered_command_revision"] == registration_hash
    assert invocation["dispatcher_sha256"] == sha(ROOT / "execution/command_dispatcher/dispatch.py")
    assert invocation["toolchain_revision"] == sha(ROOT / "execution/toolchains/locked.json")
    for stream in ("stdout", "stderr"):
        evidence = invocation[stream]
        assert sha(ROOT / evidence["path"]) == evidence["sha256"]
    for item in invocation["input_versions"]:
        assert sha(ROOT / item["path"]) == item["sha256"]
    assert row["assertion_ids"] == invocation["assertion_ids"]
    indexed = index["commands"][row["command_key"]]
    assert sha(ROOT / indexed["receipt"]) == indexed["sha256"]
    counts[row["command_key"]] = len(invocation["assertion_ids"])
assert counts == {"build.check": 9, "contracts.validate": 3, "package.validate": 8, "environment.verify": 6, "dispatcher.check": 21, "core.qualify": 1}
tasks = read(ROOT / "spec/v2.0/contracts/tasks.json")
assert set(tasks["verification_command_plan"]) <= set(registry["commands"])
assert len(read(ROOT / "execution/acceptance_status.json")["cases"]) == 42
assert all(row["status"] == "NOT_RUN" for row in read(ROOT / "execution/acceptance_status.json")["cases"].values())
assert sha(ROOT / "execution/route.json") == receipt["route_revision"]
assert read(ROOT / "execution/route.json")["selected_route"] == "THIN_CORE"
for tool in locked["tools"].values(): assert sha(Path(tool["path"])) == tool["sha256"]
entry = registry["commands"]["build.check"]
env = {name: os.environ[name] for name in entry["allowed_env"] if name in os.environ}
env.update(entry["fixed_env"])
env.update({name: locked["tools"][tool]["path"] for name, tool in entry["tool_env"].items()})
env["PYTHONDONTWRITEBYTECODE"] = "1"
python = locked["tools"]["python"]["path"]
git = locked["tools"]["git"]["path"]
head = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
archive = subprocess.check_output([git, "archive", "--format=zip", head], cwd=ROOT)
results = []
with tempfile.TemporaryDirectory(prefix="v-", dir=OUT) as temp:
    clean = Path(temp)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle: bundle.extractall(clean)
    assert not (clean / "apps/web/node_modules").exists()
    assert not (clean / ".local/bin").exists()
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(run, [python, "-X", "utf8", "ops/ci/build.py"], clean, env, 120), pool.submit(run, [python, "-X", "utf8", "tests/bootstrap/test_dispatcher.py"], ROOT, env, 60)]
        results.extend(job.result() for job in jobs)
    results.append(run([python, "-X", "utf8", "ops/ci/contracts.py"], clean, env))
    for result in results:
        assert result["exit_code"] == 0, result
        report = json.loads(result["stdout"])
        assert report["status"] == "PASS" and report["assertions"] > 0
    assert [json.loads(result["stdout"])["assertions"] for result in results] == [9, 21, 3]
for row in manifest: assert sha(ROOT / row["path"]) == row["sha256"]
output = {"status": "PASS", "scope": "W02_CONSTRUCTION_ONLY", "reviewed_git_head": head, "verified_at": datetime.now(timezone.utc).isoformat(), "artifact_count": len(manifest), "registered_assertion_counts": counts, "clean_snapshot_build": True, "receipt_jcs_hash_matches": True, "product_acceptance": "NOT_RUN", "checks": results}
(OUT / "checks.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in output.items() if key != "checks"}))
