"""Freeze public architecture/source references; never open product state."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[6]
assert (ROOT / "go.mod").is_file(), ROOT

sources = [
    "apps/control/main.go",
    "apps/control/runtime_verifier_replacement_windows.go",
    "apps/desktop/main/lib/desktop-management.js",
    "apps/desktop/main/main.js",
    "adapters/runtime/bridge_program.go",
    "adapters/runtime/bridge_windows.go",
    "adapters/runtime/mu/worker.mjs",
    "internal/domain/runtime_dispatch.go",
    "internal/domain/runtime_model.go",
    "internal/domain/runtime_model_windows.go",
    "internal/domain/runtime_model_verification.go",
    "internal/domain/runtime_broker_windows.go",
    "internal/domain/runtime_command_queue_windows.go",
    "internal/domain/runtime_coordinator_windows.go",
    "internal/domain/runtime_drain_windows.go",
    "internal/domain/runtime_recovery_windows.go",
    "internal/domain/runtime.go",
    "internal/domain/store.go",
    "internal/domain/client_runtime_setup_windows.go",
    "internal/domain/runtime_qualification_execution_windows.go",
    "internal/domain/runtime_qualification_confirmation_windows.go",
    "internal/domain/runtime_qualification.go",
    "internal/domain/orchestration_recovery.go",
    "internal/domain/budget.go",
    "internal/host/runtime_verifier_replacement_windows.go",
    "internal/store/sqlite.go",
    "ops/experiment_sandbox/sandbox_windows.go",
    "migrations/sqlite/0002_domain.sql",
    "migrations/sqlite/0016_runtime_qualification.sql",
]

def record(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

diagnosis = OUT.parent.parent / "normal_desktop_qualification_diagnosis_independent_codex" / "20261015-current-chat"
inputs = {"schema": "researchos.architecture-input-hashes.v1", "base_commit": "4f4023c956f84d65743f39ce77d6c8899a21ada1",
          "sources": [record(ROOT / p) for p in sources],
          "diagnosis": [record(diagnosis / p) for p in ("FINAL-DIAGNOSIS.md", "FINAL-manifest.json", "01-public-observation.json", "03-effect-and-native-lock.json")]}
(OUT / "input-hashes.json").write_text(json.dumps(inputs, indent=2) + "\n", encoding="utf-8")

for path in OUT.glob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))

manifest = {"schema": "researchos.architecture-deliverables.v1", "status": "DESIGN_ONLY",
            "files": [record(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "FINAL-manifest.json"],
            "validation": {"json_parse": "PASS", "source_paths_exist": True, "source_tests_run": False,
                           "actual_operations": False, "formal_case_increment": 0}}
(OUT / "FINAL-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"manifest": record(OUT / "FINAL-manifest.json"), "file_count": len(manifest["files"])}))
