import hashlib
import json
from pathlib import Path

RECEIPTS = Path(__file__).resolve().parent
TREE = Path(r"D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-20261015")
PATHS = [
    "adapters/runtime/bridge_windows.go",
    "adapters/runtime/qualification_failure_proof_windows.go",
    "adapters/runtime/qualification_failure_proof_windows_test.go",
    "internal/domain/runtime_broker_windows.go",
    "internal/domain/runtime_command_queue_windows.go",
    "internal/domain/runtime_command_queue_windows_test.go",
    "internal/domain/runtime_coordinator_windows.go",
    "internal/domain/runtime_qualification_failure_windows.go",
    "internal/domain/runtime_qualification_failure_windows_test.go",
]


def record(path):
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


commands = []
for recipe in sorted(RECEIPTS.glob("b*.recipe.json")):
    stem = recipe.name.removesuffix(".recipe.json")
    if int(stem.split("-", 1)[0][1:]) > 110:
        continue
    command = RECEIPTS / (stem + ".command.json")
    result = RECEIPTS / (stem + ".result.json")
    entry = {"id": stem, "recipe": record(recipe), "capture": command.exists(), "result": result.exists()}
    if result.exists():
        data = json.loads(result.read_text(encoding="utf-8"))
        entry.update(native_exit=data.get("native_exit"), stdout_sha256=data.get("stdout_sha256"), stderr_sha256=data.get("stderr_sha256"))
    commands.append(entry)

patch = RECEIPTS / "B-whole-source.patch"
manifest = {
    "schema": "researchos.qualification-failure-B-source-evidence.v1",
    "status": "AUTHOR_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW",
    "base_commit": "f48fca0e4013bda19913a34d91da0cd23157a08b",
    "base_tree": "16e72ccf939c13142091495458ad04348a3ba660",
    "candidate_commit": "75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603",
    "candidate_tree": "ba3f9d4c101df39ab17856158d5fc72a9f0600ce",
    "branch": "codex/qualification-failure-b-20261015",
    "worktree": str(TREE),
    "source": {p: record(TREE / p) for p in PATHS},
    "whole_binary_patch": {"path": patch.name, **record(patch), "from": "base_commit", "to": "candidate_commit"},
    "focused_test": {"id": "b78-final-focused", **json.loads((RECEIPTS / "b78-final-focused.result.json").read_text(encoding="utf-8"))},
    "existing_regression": {"id": "b105-existing-regression", **json.loads((RECEIPTS / "b105-existing-regression.result.json").read_text(encoding="utf-8"))},
    "command_ledger": commands,
    "capture_gaps": [e["id"] for e in commands if not e["capture"] or not e["result"]],
    "formal_increment": 0,
}
(RECEIPTS / "B-evidence-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"sources={len(PATHS)} commands={len(commands)} gaps={manifest['capture_gaps']} patch_sha256={manifest['whole_binary_patch']['sha256']}")
