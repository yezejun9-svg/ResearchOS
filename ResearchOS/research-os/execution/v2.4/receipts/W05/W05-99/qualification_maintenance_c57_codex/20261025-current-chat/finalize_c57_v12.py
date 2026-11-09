import hashlib
import json
import subprocess
from pathlib import Path

receipts = Path(__file__).parent
project = Path(r"D:\作品集\ResearchOS\research-os")
worktree = project / ".local/worktrees/qualification-maintenance-c57-20261025"
boot = project / "execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest_path = receipts / "C57-V12-COMMIT-SOURCE57-MANIFEST.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
old_finalizer = receipts / "C57-FINALIZER.json"
pre = receipts / "C57-V12-PRETEST.json"
post = receipts / "C57-V12-POSTTEST.json"
if sha(pre) != sha(post) or manifest["source_snapshot_sha256"] != sha(post):
    raise RuntimeError("V12 source moved during integration")
if manifest["parent"] != "08d63ed86356a93fe5715732cfeae0624c5cb6c9" or manifest["delta_count"] != 2 or manifest["cumulative_changed_count"] != 52:
    raise RuntimeError("V12 commit scope differs")

def run_patch(name, args):
    result = subprocess.run(args, cwd=worktree, capture_output=True)
    (receipts / f"{name}.stdout.raw").write_bytes(result.stdout)
    (receipts / f"{name}.stderr.raw").write_bytes(result.stderr)
    (receipts / f"{name}.native-exit.txt").write_text(f"{result.returncode}\n", encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{name} failed: {result.returncode}")
    return result.stdout

delta = run_patch("108-v12-commit-delta", ["git", "--no-pager", "diff", "--binary", "--full-index", "HEAD^", "HEAD"])
delta_path = receipts / "C57-V12-COMMIT-DELTA.patch"
if delta_path.exists():
    raise RuntimeError("V12 delta patch exists; preserve it")
delta_path.write_bytes(delta)
if sha(delta_path) != sha(receipts / "C57-V12-STAGED-DELTA.patch"):
    raise RuntimeError("V12 commit delta differs from staged delta")
cumulative = run_patch("109-v12-cumulative-patch", ["git", "--no-pager", "diff", "--binary", "--full-index", "085b4711afe0c1288448b174eef24ecd5af0551b", "HEAD"])
cumulative_path = receipts / "C57-V12-CUMULATIVE-FULL.patch"
if cumulative_path.exists():
    raise RuntimeError("V12 cumulative patch exists; preserve it")
cumulative_path.write_bytes(cumulative)

own_checks = []
for name in ("095-v12-pretest", "096-v12-interface", "097-v12-windows-build", "098-v12-posttest",
             "105-v12-stage-orchestrator", "106-v12-commit", "107-v12-commit-verify"):
    item = {"id": name, "native_exit": int((receipts / f"{name}.native-exit.txt").read_text(encoding="utf-8").strip())}
    for suffix in ("stdout.raw", "stderr.raw", "native-exit.txt"):
        item[suffix] = sha(receipts / f"{name}.{suffix}")
    if item["native_exit"] != 0:
        raise RuntimeError(f"V12 own check failed: {name}")
    own_checks.append(item)
ledger_path = receipts / "C57-V12-DIAGNOSTIC-INCREMENT-095-109.jsonl"
if ledger_path.exists():
    raise RuntimeError("V12 diagnostic increment exists; preserve it")
ledger_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in own_checks) + "\n", encoding="utf-8")

boot_results = {}
for name in ("final-v12-c-windows-tests", "final-v12-d-windows-tests", "final-v12-linux-crossbuild"):
    boot_results[name] = {"native_exit": int((boot / f"{name}.exit.txt").read_text(encoding="utf-8").strip()),
                          "stdout_sha256": sha(boot / f"{name}.stdout.raw"),
                          "stderr_sha256": sha(boot / f"{name}.stderr.raw")}
    if boot_results[name]["native_exit"] != 0:
        raise RuntimeError(f"Boot6 V12 author check failed: {name}")

finalizer = {"schema": "researchos.c57-v12-local-commit-finalizer.v1",
             "status": "LOCAL_V12_COMMIT_CREATED_PENDING_INDEPENDENT_PHASE2_NO_FORMAL_ACCEPTANCE",
             "commit": manifest["commit"], "tree": manifest["tree"], "parent": manifest["parent"],
             "baseline": manifest["baseline"], "branch": manifest["branch"],
             "source57_manifest_sha256": sha(manifest_path),
             "source57_pre_post_snapshot_sha256": sha(post),
             "boot6_v12_manifest_sha256": sha(boot / "final-v12-six-source-manifest.json"),
             "boot6_v12_seal_sha256": sha(boot / "final-v12-additive-seal.json"),
             "old_08d63_finalizer_sha256": sha(old_finalizer),
             "v12_staged_manifest_sha256": sha(receipts / "C57-V12-STAGED-MANIFEST.json"),
             "v12_delta_patch_sha256": sha(delta_path), "v12_delta_patch_bytes": len(delta),
             "cumulative_patch_sha256": sha(cumulative_path), "cumulative_patch_bytes": len(cumulative),
             "diagnostic_increment_sha256": sha(ledger_path),
             "integration_tests": {"interface_096_exit": 0, "windows_build_097_exit": 0,
                                   "boot6_author_results": boot_results},
             "source_delta_count": 2, "baseline_changed_count": 52, "source_allowlist_count": 57,
             "inherited_pin_count": 40, "formal_acceptance_count": 0,
             "limits": ["No original Root, DB, process, ACL or restart action",
                        "No Main merge, push, or formal adoption",
                        "Independent Phase2 signature remains separate"]}
out = receipts / "C57-V12-FINALIZER.json"
if out.exists():
    raise RuntimeError("V12 finalizer exists; preserve it")
out.write_text(json.dumps(finalizer, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"finalizer_sha256": sha(out), "delta_sha256": sha(delta_path),
                  "cumulative_sha256": sha(cumulative_path), "diagnostic_sha256": sha(ledger_path)}))
