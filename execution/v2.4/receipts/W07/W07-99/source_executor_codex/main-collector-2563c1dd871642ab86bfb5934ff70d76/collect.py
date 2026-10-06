"""One authorized current MAIN public-source collection; preserve all raw bytes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[6]
def sha(p): return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {"path": p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p), "sha256": sha(p)}
def save(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def run(argv, stem, env=None, timeout=900):
    started = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
    out, err = OUT / (stem + ".stdout"), OUT / (stem + ".stderr")
    out.write_bytes(p.stdout); err.write_bytes(p.stderr)
    inv = {"actualargv": argv, "cwd": str(ROOT), "exit_code": p.returncode, "started_at": started,
           "ended_at": datetime.now(timezone.utc).isoformat(), "stdout_ref": ref(out), "stderr_ref": ref(err)}
    save(OUT / (stem + ".invocation.json"), inv)
    return p

expected = {
    "ops/ci/sources.py": "24c4af577a52637f62703d186d2675a2fd9878384618c6469299cfc90b99281c",
    "tests/sources/check/parent_gate_test.py": "6b60756ec9d3654508e83cabc3913f0952b5dbb2df7c3ce058099cecf316f22b",
    "internal/domain/backup_upgrade_test.go": "46fd30bba4b2ab2f3438bae151592090ba693a841fde21d71689f42dab7838a4"}
assert all(sha(ROOT / p) == "sha256:" + h for p, h in expected.items())
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "cf7ec1ec70cdeea842d878d131773b64ecb61d85"
tracked = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT)
(OUT / "git-tracked-before.raw").write_bytes(tracked)
assert not tracked.strip()
(OUT / "git-status-before.raw").write_bytes(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
metadata = ["execution/v2.4/" + n + ".json" for n in ("checkpoint", "commands", "path_ownership")]
metadata_before = {p: sha(ROOT / p) for p in metadata}
for p in metadata: (OUT / (Path(p).stem + ".before.json")).write_bytes((ROOT / p).read_bytes())
previous = ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/main-collector-5003407cbeab4755b87893defd28a51c/inputs-before.json"
inputs = {p: sha(Path(p)) for p in json.loads(previous.read_text(encoding="utf-8"))}
save(OUT / "inputs-before.json", inputs)
go = ROOT / ".local/tools/go1.27.1/go/bin/go.exe"
browser = Path("C:/Users/yqyyds/.local/bin/browser-act.exe")
assert sha(go) == "sha256:d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
assert sha(browser) == "sha256:3f4b70e680b8a896f20b17fcf876e5b5fccd6489ce8b5e025cd9cbe70b522303"
pre = run([str(browser), "session", "list"], "browser-sessions-before", timeout=30)
assert pre.returncode == 0 and b"No active sessions" in pre.stdout
settings = {"GOTOOLCHAIN": "local", "GOENV": "off", "GOROOT": str(go.parents[1]),
    "GOCACHE": str(ROOT / ".local/gocache"), "GOPATH": str(ROOT / ".local/gopath"),
    "RESEARCHOS_GO": str(go), "RESEARCHOS_BROWSER_ACT": str(browser),
    "RESEARCHOS_BROWSER_ID": "direct_local_120993884286222444", "RESEARCHOS_TASK_ID": "W07",
    "RESEARCHOS_CHECK_ID": "W07-H07", "RESEARCHOS_CASE_ID": "", "RESEARCHOS_SOURCE_MODE": "live"}
env = dict(os.environ, **settings)
env.pop("RESEARCHOS_W07_PROOF_REF", None)
env.pop("GOMODCACHE", None)
save(OUT / "environment.json", {"explicit_settings": settings, "GOMODCACHE": "UNSET_DERIVED_FROM_GOPATH", "credential_values": "NOT_RECORDED"})
p = run([sys.executable, "-B", "-X", "utf8", "ops/ci/sources.py"], "collector", env)
after = {name: sha(Path(name)) for name in inputs}
save(OUT / "inputs-after.json", after)
metadata_after = {name: sha(ROOT / name) for name in metadata}
save(OUT / "metadata-drift.json", {"before": metadata_before, "after": metadata_after, "identical": metadata_before == metadata_after})
(OUT / "git-status-after.raw").write_bytes(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
(OUT / "git-tracked-after.raw").write_bytes(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT))
post = run([str(browser), "session", "list"], "browser-sessions-after", timeout=30)
assert post.returncode == 0 and b"No active sessions" in post.stdout
report = json.loads(p.stdout)
summary = {"collector_exit_code": p.returncode, "status": report.get("status"), "frozen_head": head,
    "inputs_identical": inputs == after, "metadata_identical": metadata_before == metadata_after,
    "product_proof_ref": report.get("product_proof_ref"), "source_count": len(report.get("source_hashes", {})),
    "source_before_equals_after": report.get("source_hashes") == report.get("source_hashes_after"),
    "go_environment": report.get("go_environment"), "session_cleanup": "NO_ACTIVE_SESSIONS",
    "formal_acceptance": "NOT_ISSUED", "next_actual_verifier": "codex:/root/w05_merge_review"}
save(OUT / "collection-summary.json", summary)
assert p.returncode == 0 and report["status"] == "PASS", summary
assert inputs == after and metadata_before == metadata_after
assert summary["source_before_equals_after"] and summary["source_count"] == 2283
print(json.dumps({"summary_ref": ref(OUT / "collection-summary.json"), "proof_ref": report["product_proof_ref"]}, ensure_ascii=False))
