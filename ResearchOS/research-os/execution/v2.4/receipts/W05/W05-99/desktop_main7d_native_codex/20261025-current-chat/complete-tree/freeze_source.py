"""Freeze the exact seven-file candidate before the long development build."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
LABEL = sys.argv[1] if len(sys.argv) == 2 and sys.argv[1] in {"02", "03"} else None
if LABEL is None:
    raise SystemExit("explicit new freeze suffix 02 or 03 required")
ROOT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\desktop-main7d-native-20261025")
source = ROOT / "apps/desktop/build-development.py"
spec = importlib.util.spec_from_file_location("build_development", source)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


snapshot = builder.source_snapshot()
if snapshot["head"] != "7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e" or \
   snapshot["tree"] != "de59625ee5c1d360c741c95ec3f84b6f2764bb0e" or \
   set(snapshot["candidate_delta"]) != builder.ALLOWLIST:
    raise SystemExit("seven-file source scope or base changed")
parts = []
existing = subprocess.run(["git", "diff", "HEAD", "--binary", "--", "apps/desktop/main/main.js"],
                          cwd=ROOT, capture_output=True, check=True)
parts.append(existing.stdout)
for relative in sorted(builder.ALLOWLIST - {"apps/desktop/main/main.js"}):
    item = subprocess.run(["git", "diff", "--no-index", "--binary", "--", "NUL", relative],
                          cwd=ROOT, capture_output=True)
    if item.returncode != 1 or not item.stdout.startswith(b"diff --git "):
        raise SystemExit(f"new source patch unavailable: {relative}: {item.returncode}")
    parts.append(item.stdout)
patch = b"".join(parts)
patch_path = HERE / f"SOURCE-FREEZE-{LABEL}.patch"
with patch_path.open("xb") as stream:
    stream.write(patch)
delta = {row["path"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
         for row in snapshot["files"] if row["path"] in builder.ALLOWLIST}
record = {"schema": "researchos.desktop-complete-tree-source-freeze.v1",
          "base_commit": snapshot["head"], "base_tree": snapshot["tree"],
          "scope_sha256": "a9e0c1b29282468b2d7a10d2cbd3db88feaa673b8480e0aab3d6176019bc7ab3",
          "source_input_count": len(snapshot["files"]), "source_snapshot_digest": snapshot["digest"],
          "candidate_delta": snapshot["candidate_delta"], "seven_file_hashes": delta,
          "patch": {"path": str(patch_path), "sha256": sha(patch_path), "bytes": len(patch)},
          "focused_checks": {name: {"exit": (HERE / (name + ".native-exit.txt")).read_text(encoding="ascii").strip(),
                                    "stdout_sha256": sha(HERE / (name + ".stdout.raw")),
                                    "stderr_sha256": sha(HERE / (name + ".stderr.raw"))}
                             for name in ["focused-03.pre-python-bundle-tests",
                                          "focused-04.pre-launcher-check" if LABEL == "03" else "focused-02.pre-node-launcher-smoke-tests",
                                          "focused-04.pre-launcher-smoke-tests" if LABEL == "03" else "focused-02.pre-node-launcher-smoke-tests"]},
          "limitation": "Mock/source checks only; no Electron or Core launch"}
with (HERE / f"SOURCE-FREEZE-{LABEL}.json").open("xb") as stream:
    stream.write((json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"seven_files": len(delta), "patch_sha256": record["patch"]["sha256"],
                  "source_snapshot_digest": snapshot["digest"], "manifest_sha256": sha(HERE / f"SOURCE-FREEZE-{LABEL}.json")}, ensure_ascii=False))
