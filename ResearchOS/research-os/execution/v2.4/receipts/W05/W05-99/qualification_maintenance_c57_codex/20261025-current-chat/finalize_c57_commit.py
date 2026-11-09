import hashlib
import json
import subprocess
from pathlib import Path

receipts = Path(__file__).parent
project = Path(r"D:\作品集\ResearchOS\research-os")
worktree = project / ".local/worktrees/qualification-maintenance-c57-20261025"
boot_receipts = project / "execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat"
manifest_path = receipts / "C57-COMMIT-SOURCE57-MANIFEST.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest["commit"] != "08d63ed86356a93fe5715732cfeae0624c5cb6c9" or manifest["parent"] != "085b4711afe0c1288448b174eef24ecd5af0551b":
    raise RuntimeError("C57 commit identity differs")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

patch_path = receipts / "C57-COMMIT-FULL.patch"
if patch_path.exists():
    raise RuntimeError("commit patch already exists; preserve it")
patch = subprocess.run(["git", "--no-pager", "diff", "--binary", "--full-index", "HEAD^", "HEAD"],
                       cwd=worktree, capture_output=True)
(receipts / "093-commit-diff.stdout.raw").write_bytes(patch.stdout)
(receipts / "093-commit-diff.stderr.raw").write_bytes(patch.stderr)
(receipts / "093-commit-diff.native-exit.txt").write_text(f"{patch.returncode}\n", encoding="utf-8")
if patch.returncode:
    raise RuntimeError("commit diff failed")
patch_path.write_bytes(patch.stdout)
staged_sha = sha(receipts / "C57-STAGED-FULL.patch")
if sha(patch_path) != staged_sha:
    raise RuntimeError("commit full patch differs from exact staged patch")

checks = [
    ("combined-065-domain", "FAIL", "Prepared nested fixture used unresolved temporary path"),
    ("combined-066-core", "PASS", "C51 core package matrix"),
    ("combined-067-boot", "FAIL", "C inherited ACL exposed Boot6 fixture baseline assumption"),
    ("combined-068-windows-build", "PASS", "Windows full build before test-only R4 and Boot6 v11"),
    ("combined-069-linux-build", "FAIL", "Windows-only base packages in ./..."),
    ("070-domain-lease-isolate", "FAIL", "Nested lease fixture reproduced in C temporary root"),
    ("071-domain-lease-isolate", "PASS", "Normalized prepared fixture in C temporary root"),
    ("072-boot-v10-env", "PASS", "Boot6 v10 D temporary root; does not close inherited C branch"),
    ("073-domain-lease-d-env", "PASS", "Normalized prepared fixture in D temporary root"),
    ("074-domain-combined-r4", "PASS", "C51 Domain target matrix after R4"),
    ("075-linux-selective-build", "FAIL", "Baseline Windows-only Domain methods excluded on Linux"),
    ("076-linux-supported-build", "PASS", "Only Linux-supported changed packages"),
    ("079-boot-v11-c-env", "PASS", "Full Boot6 packages in inherited C environment"),
    ("081-combined-v11-r4-tests", "PASS", "Eight C57 affected packages at final source"),
    ("082-combined-v11-windows-build", "PASS", "Windows full build at final source"),
]
ledger_path = receipts / "C57-DIAGNOSTIC-INCREMENT-065-082.jsonl"
if ledger_path.exists():
    raise RuntimeError("diagnostic increment already exists; preserve it")
lines = []
for name, classification, note in checks:
    files = {}
    for suffix in ("recipe.txt", "stdout.raw", "stderr.raw", "native-exit.txt"):
        path = receipts / f"{name}.{suffix}"
        files[suffix] = {"sha256": sha(path), "bytes": path.stat().st_size}
    exit_value = int((receipts / f"{name}.native-exit.txt").read_text(encoding="utf-8").strip())
    if (exit_value == 0) != (classification == "PASS"):
        raise RuntimeError(f"diagnostic status contradicts native exit: {name}")
    lines.append(json.dumps({"id": name, "classification": classification, "native_exit": exit_value,
                             "note": note, "files": files}, ensure_ascii=False))
ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

pretest = receipts / "C57-COMBINED-V11-PRECOMMIT.json"
posttest = receipts / "C57-COMBINED-V11-POSTTEST.json"
if sha(pretest) != sha(posttest):
    raise RuntimeError("combined 57 source moved during final tests")
source = json.loads(posttest.read_text(encoding="utf-8"))
if len(source["files"]) != 57 or source["changed_count"] != 52 or source["inherited_pin_count"] != 40:
    raise RuntimeError("final source scope count differs")
seal = {"schema": "researchos.c57-local-commit-finalizer.v1",
        "status": "LOCAL_COMMIT_CREATED_PENDING_INDEPENDENT_PHASE2_NO_FORMAL_ACCEPTANCE",
        "commit": manifest["commit"], "tree": manifest["tree"], "parent": manifest["parent"],
        "branch": manifest["branch"], "worktree": str(worktree),
        "scope_sha256": source["scope_sha256"],
        "source57_manifest_sha256": sha(manifest_path),
        "source57_pre_post_snapshot_sha256": sha(posttest),
        "c51_r4_sourcefreeze_sha256": sha(receipts / "C51-R4-SOURCEFREEZE.json"),
        "boot6_v11_manifest_sha256": sha(boot_receipts / "final-v11-six-source-manifest.json"),
        "boot6_v11_seal_sha256": sha(boot_receipts / "final-v11-additive-seal.json"),
        "staged_manifest_sha256": sha(receipts / "C57-STAGED-MANIFEST.json"),
        "full_commit_patch_sha256": sha(patch_path), "full_commit_patch_bytes": patch_path.stat().st_size,
        "diagnostic_increment_sha256": sha(ledger_path),
        "diagnostic_count": len(checks),
        "final_pass_ids": [name for name, result, _ in checks if result == "PASS"],
        "preserved_fail_ids": [name for name, result, _ in checks if result == "FAIL"],
        "limits": ["No original Root, DB, process, ACL or restart action",
                   "No actual distinct-SID Host closure or live historical verifier Wait",
                   "No Main adoption, push, independent Phase2 signature or formal acceptance"],
        "formal_acceptance_count": 0}
out = receipts / "C57-FINALIZER.json"
if out.exists():
    raise RuntimeError("finalizer already exists; preserve it")
out.write_text(json.dumps(seal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"finalizer_sha256": sha(out), "diagnostic_sha256": sha(ledger_path),
                  "full_patch_sha256": sha(patch_path), "commit": manifest["commit"]}))
