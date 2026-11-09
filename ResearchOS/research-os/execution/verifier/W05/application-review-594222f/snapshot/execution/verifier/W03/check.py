"""Independent W03 review: frozen evidence plus clean-snapshot local checks."""
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
RUN = "3de29703-976f-4fed-870b-62123619053b"
BASE = ROOT / "execution/receipts/W03" / RUN
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def run(argv, cwd, env, timeout=120):
    started = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    return {"argv": argv, "cwd": str(cwd), "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

receipt = read(BASE / "receipt.json")
manifest = read(BASE / "artifacts.json")
assert len(manifest) == 63
assert sha(BASE / "artifacts.json") == receipt["artifact_manifest_hash"]
for row in manifest: assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
expected_hash = receipt.pop("receipt_hash")
def restricted_jcs(value):
    if isinstance(value, dict):
        assert all(key.isascii() for key in value)
        for item in value.values(): restricted_jcs(item)
    elif isinstance(value, list):
        for item in value: restricted_jcs(item)
    elif isinstance(value, str): value.encode("utf-8")
    elif isinstance(value, int): assert abs(value) <= 9007199254740991
    else: assert value is None
restricted_jcs(receipt)
assert "sha256:" + hashlib.sha256(json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == expected_hash
assert sha(ROOT / "spec/v2.0/PACKAGE_MANIFEST.json") == receipt["input_manifest_hash"]
assert sha(ROOT / "execution/route.json") == receipt["route_revision"]
registry = read(ROOT / "execution/commands.json")
locked = read(ROOT / "execution/toolchains/locked.json")
counts = {}
for row in receipt["verification_results"]:
    inv = read(ROOT / row["actual_invocation_reference"])
    assert inv["status"] == "PASS" and inv["exit_code"] == 0
    assert inv["registered_command_revision"] == sha(ROOT / "execution/commands.json")
    assert inv["dispatcher_sha256"] == sha(ROOT / "execution/command_dispatcher/dispatch.py")
    assert inv["toolchain_revision"] == sha(ROOT / "execution/toolchains/locked.json")
    for stream in ("stdout", "stderr"):
        item = inv[stream]
        assert sha(ROOT / item["path"]) == item["sha256"]
    for item in inv["input_versions"]: assert sha(ROOT / item["path"]) == item["sha256"]
    assert inv["assertion_ids"] == row["assertion_ids"]
    counts[row["command_key"]] = len(inv["assertion_ids"])
assert counts == {"build.check": 9, "contracts.validate": 5, "test.domain": 16, "domain.http.check": 12}
coverage = read(ROOT / "contracts/operation_coverage.json")
assert len(coverage["operations"]) == 124
assert sum(op["status"] == "IMPLEMENTED_CORE" for op in coverage["operations"]) == 26
for name, digest in coverage["contract_hashes"].items(): assert sha(ROOT / "spec/v2.0/contracts" / name) == digest
assert len(read(ROOT / "execution/acceptance_status.json")["cases"]) == 42
assert all(row["status"] == "NOT_RUN" for row in read(ROOT / "execution/acceptance_status.json")["cases"].values())
for tool in locked["tools"].values(): assert sha(Path(tool["path"])) == tool["sha256"]
entry = registry["commands"]["build.check"]
env = {name: os.environ[name] for name in entry["allowed_env"] if name in os.environ}
env.update(entry["fixed_env"])
env.update({name: locked["tools"][tool]["path"] for name, tool in entry["tool_env"].items()})
env.update(PYTHONDONTWRITEBYTECODE="1", RESEARCHOS_TASK_ID="W03")
python = locked["tools"]["python"]["path"]
git = locked["tools"]["git"]["path"]
go = locked["tools"]["go"]["path"]
head = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
assert not subprocess.check_output([git, "diff", "--name-only", receipt["base_revision"], "--", "spec/v2.0"], cwd=ROOT, text=True).strip()
archive = subprocess.check_output([git, "archive", "--format=zip", head], cwd=ROOT)
results = []
with tempfile.TemporaryDirectory(prefix="v-", dir=OUT) as temp:
    clean = Path(temp)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle: bundle.extractall(clean)
    assert not (clean / "apps/web/node_modules").exists()
    results.append(run([python, "-X", "utf8", "ops/ci/build.py"], clean, env))
    assert results[-1]["exit_code"] == 0, results[-1]
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(run, [python, "-X", "utf8", command], clean, env) for command in ("ops/ci/contracts.py", "ops/ci/domain.py", "tests/domain/http_contract_check.py")]
        results.extend(job.result() for job in jobs)
    for result, count in zip(results, (9, 5, 16, 12)):
        assert result["exit_code"] == 0, result
        report = json.loads(result["stdout"])
        assert report["status"] == "PASS" and report["assertions"] == count
    regression_file = clean / "internal/domain/verifier_regressions_test.go"
    regression_file.write_bytes((OUT / "regressions_test.go.txt").read_bytes())
    results.append(run([go, "test", "-count=1", "-json", "-run", "^TestVerifier", "./internal/domain"], clean, env))
    assert results[-1]["exit_code"] == 0, results[-1]
    events = [json.loads(line) for line in results[-1]["stdout"].splitlines() if line.startswith("{")]
    passed = {e["Test"] for e in events if e.get("Action") == "pass" and "Test" in e}
    assert passed == {"TestVerifierIntegerOverflow", "TestVerifierCursorQuery", "TestVerifierSlowBody"}
for row in manifest: assert sha(ROOT / row["path"]) == row["sha256"]
output = {"status": "PASS", "scope": "W03_CONSTRUCTION_ONLY", "reviewed_git_head": head, "verified_at": datetime.now(timezone.utc).isoformat(), "artifact_count": len(manifest), "registered_assertion_counts": counts, "clean_snapshot_build": True, "receipt_jcs_hash_matches": True, "independent_regressions": sorted(passed), "product_acceptance": "NOT_RUN", "checks": results}
(OUT / "checks.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in output.items() if key != "checks"}))
