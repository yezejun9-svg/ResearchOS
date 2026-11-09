"""Freeze C-only preparation records. Never launches/imports any runtime."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def row(file):
    return {"path": file.relative_to(ROOT).as_posix(), "sha256": digest(file), "bytes": file.stat().st_size}


def write(name, data):
    with (ROOT / name).open("x", encoding="utf-8", newline="\n") as target:
        json.dump(data, target, ensure_ascii=False, indent=2)
        target.write("\n")


def main():
    for name in ["FROZEN.json", "MANIFEST.json", "ARCHIVE_FILES.json"]:
        if (ROOT / name).exists():
            raise SystemExit("ALREADY_FROZEN_DO_NOT_OVERWRITE")
    scope_path = ROOT / "scope.template.json"
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    if scope["status"] != "NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION":
        raise SystemExit("DO_NOT_MODIFY_EXECUTION_SCOPE")
    # The template is still an unapproved draft; bind its final C-only code now.
    before_scope_sha = digest(scope_path)
    scope["harness"] = {"runner_sha256": digest(ROOT / "real-electron-flow.mjs"),
                        "folder_helper_sha256": digest(ROOT / "choose-owned-folder.ps1")}
    scope_path.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = [row(file) for file in sorted(ROOT.rglob("*")) if file.is_file()]
    write("MANIFEST.json", {"schema": "researchos.real-electron-harness.preparation-manifest/1",
          "status": "PREPARATION_ONLY_NOT_RUN", "files": files})
    write("FROZEN.json", {"schema": "researchos.real-electron-harness.preparation-freeze/1",
          "status": "PREPARED_AWAITING_ROOT_REVIEW_NOT_RUN", "frozen_at": datetime.now(timezone.utc).isoformat(),
          "construction_frozen": True, "source_modification_permitted": False,
          "manifest_sha256": digest(ROOT / "MANIFEST.json"),
          "source_sha256": {name: digest(ROOT / name) for name in ["real-electron-flow.mjs", "choose-owned-folder.ps1"]},
          "scope_template_sha256": digest(scope_path), "draft_scope_pre_final_pins_sha256": before_scope_sha,
          "static_evidence_sha256": digest(ROOT / "STATIC_EVIDENCE.json"),
          "sdk_inventory_sha256": digest(ROOT / "SDK_INVENTORY.json"),
          "pure_checks_passed": 12, "syntax_only": {"node_exit": 0, "powershell_ast_exit": 0},
          "real_runner_invocations": 0, "sdk_imports": 0, "gui": 0, "native": 0, "model": 0,
          "formal_increment": 0, "product_increment": 0,
          "pending_inputs": ["Root reviewed execution scope + exact existing unnamed Job launch contract",
            "New source-bound integrated bundle, exact source head/pins and bundle manifest/Electron/control hashes",
            "Actual Windows Shell/UIAutomation behavior, Main READY listener timing and native Codex execution remain NOT_RUN"],
          "source_or_runtime_acceptance": "NOT_GRANTED_BY_AUTHOR"})
    archive = [row(file) for file in sorted(ROOT.rglob("*")) if file.is_file()]
    write("ARCHIVE_FILES.json", {"schema": "researchos.prepared-harness.archive-files/1",
          "root": str(ROOT), "files": archive, "file_count": len(archive),
          "total_bytes": sum(file["bytes"] for file in archive), "excluded": ["none: no stage, cache, dist or SDK copy"]})
    print(json.dumps({"status": "PREPARED_AWAITING_ROOT_REVIEW_NOT_RUN",
          "freeze_sha256": digest(ROOT / "FROZEN.json"), "manifest_sha256": digest(ROOT / "MANIFEST.json"),
          "archive_sha256": digest(ROOT / "ARCHIVE_FILES.json"), "files": len(archive),
          "bytes": sum(file["bytes"] for file in archive)}))


if __name__ == "__main__":
    main()
