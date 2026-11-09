from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/作品集/ResearchOS/research-os")
WORKTREE = ROOT / ".local/worktrees/product-v1-native-qualification-producer-20261105"
OUT = Path(__file__).parent
B1 = Path(r"C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-rpc-runtime-author-20261105/final-rev6/source")
FILES = [
    "adapters/runtime/codex_qualification_windows.go",
    "adapters/runtime/codex_qualification_capture_windows.go",
    "adapters/runtime/codex_qualification_windows_test.go",
    "adapters/runtime/codex_qualification_capture_windows_test.go",
    "internal/qualificationprobe/plan.go",
    "internal/qualificationprobe/plan_test.go",
    "cmd/researchos-qualification-helper/main_windows.go",
    "cmd/researchos-qualification-helper/main_windows_test.go",
]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def patch(path: str, raw: bytes, inverse: bool) -> str:
    body = raw.decode("utf-8").splitlines()
    assert raw.endswith(b"\n") and b"\r" not in raw
    count = len(body)
    if inverse:
        header = [f"diff --git a/{path} b/{path}", "deleted file mode 100644", f"--- a/{path}", "+++ /dev/null", f"@@ -1,{count} +0,0 @@"]
        return "\n".join(header + ["-" + line for line in body]) + "\n"
    header = [f"diff --git a/{path} b/{path}", "new file mode 100644", "--- /dev/null", f"+++ b/{path}", f"@@ -0,0 +1,{count} @@"]
    return "\n".join(header + ["+" + line for line in body]) + "\n"


entries = []
forward = []
inverse = []
for rel in FILES:
    raw = (WORKTREE / rel).read_bytes()
    write(OUT / "source" / rel, raw)
    entries.append({"path": rel, "baseline_sha256": "ABSENT_BEFORE", "source_sha256": digest(raw)})
    forward.append(patch(rel, raw, False))
    inverse.append(patch(rel, raw, True))
write(OUT / "changes.patch", "".join(forward).encode("utf-8"))
write(OUT / "changes.inverse.patch", "".join(inverse).encode("utf-8"))

scope = ROOT / "execution/product-v1/receipts/single-harness-20261104/native-qualification-producer/scope.json"
contracts = {
    rel: digest((ROOT / rel).read_bytes())
    for rel in [
        "execution/product-v1/contracts/native-qualification-producer.v1.md",
        "execution/product-v1/contracts/native-qualification-source-boundary.v1.md",
    ]
}
b1 = {p.name: digest(p.read_bytes()) for p in sorted(B1.iterdir()) if p.is_file()}
manifest = {
    "schema": "researchos.native-qualification-producer-candidate.v1",
    "status": "FROZEN_SOURCE_PENDING_SUPERVISED_GO_FAKE_TEST_AND_INTEGRATION",
    "base_head": "c3c7812347bb72930365fbb5db0efee8a965bc78",
    "worktree": str(WORKTREE),
    "scope_sha256": digest(scope.read_bytes()),
    "contract_sha256": contracts,
    "b1_overlay_source": str(B1),
    "b1_overlay_sha256": b1,
    "files": entries,
    "forward_patch_sha256": digest((OUT / "changes.patch").read_bytes()),
    "inverse_patch_sha256": digest((OUT / "changes.inverse.patch").read_bytes()),
    "go_format": "PASS; pinned gofmt.exe applied to exact eight files",
    "go_tests": "NOT_RUN_BY_AUTHOR; Root f13 overlay required",
    "native_cli_auth_model_probe": "NOT_RUN",
    "formal_acceptance": False,
    "product_acceptance": False,
    "known_pending": [
        "Root-controlled B1 rev6 overlay Go compile and fake tests",
        "Independent source/security review",
        "Separate Host composition, shipped helper build pin, and pre-RPC failure settlement",
        "Actual supervised synthetic qualification and Native/model acceptance remain closed",
    ],
}
write(OUT / "MANIFEST.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
write(OUT / "FROZEN.txt", b"B3 exact-eight-file source candidate frozen. No author Go/Native/model execution. See MANIFEST.json.\n")
print(digest((OUT / "MANIFEST.json").read_bytes()))
