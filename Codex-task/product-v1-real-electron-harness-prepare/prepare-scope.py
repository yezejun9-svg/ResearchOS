"""Generate an intentionally non-executable template from public static pins."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    evidence = json.loads((HERE / "STATIC_EVIDENCE.json").read_text(encoding="utf-8"))
    sources = {row["relative_path"]: row for row in evidence["sources"]}
    tools = {row["path"].replace("\\", "/"): row for row in evidence["tools"]}
    cache = evidence["playwright"]["path"].replace("\\", "/")
    node = "C:/nvm4w/nodejs/node.exe"
    powershell = "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
    scope = {
        "schema": "researchos.real-electron-single-codex-scope/1",
        "status": "NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_AND_SUPERVISION",
        "scope_nonce": None,
        "run_root": "C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-real-run-<ROOT-NEW-NONCE>",
        "project_display_name": "ResearchOS V1 owned readonly fixture",
        "contract_sha256": "046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c",
        "source": {
            "root": "<new-clean-product-v1-build-WT>", "head": None,
            "pin_status": "CURRENT_STATIC_BASELINE_ONLY_REPLACE_WITH_FINAL_INTEGRATED_BUILD_INPUTS",
            "pins": [{"path": name, "sha256": row["sha256"]} for name, row in sources.items()],
        },
        "bundle": {
            "root": "<new-clean-product-v1-build-WT>/.local/desktop-v1-build-01",
            "manifest_sha256": None, "electron_sha256": None,
            "control_sha256": None, "source_binding_review": None,
        },
        "launcher": {"path": "<new-clean-product-v1-build-WT>/apps/desktop/launch-development.mjs",
                     "sha256": sources["apps/desktop/launch-development.mjs"]["sha256"]},
        "node": {"path": node, "sha256": tools[node]["sha256"]},
        "playwright": {
            "root": cache, "version": "1.62.1",
            "inventory_path": str(HERE / "SDK_INVENTORY.json"),
            "inventory_sha256": digest(HERE / "SDK_INVENTORY.json"),
        },
        "codex": {
            "executable": "C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe",
            "sha256": "9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42",
            "version_evidence": "0.166.0 (Root metadata probe only; real execution NOT_RUN)",
        },
        "windows": {
            "system_root": "C:/Windows", "normal_user_profile": "C:/Users/yqyyds",
            "normal_app_data": "C:/Users/yqyyds/AppData/Roaming",
            "normal_local_app_data": "C:/Users/yqyyds/AppData/Local",
            "powershell": powershell, "powershell_sha256": tools[powershell]["sha256"],
        },
        "harness": {"runner_sha256": digest(HERE / "real-electron-flow.mjs"),
                    "folder_helper_sha256": digest(HERE / "choose-owned-folder.ps1")},
        "native_picker": {"automation": "REAL_OWNED_SHELL_WINDOW_ONLY",
                          "runtime_verified": False, "operator_fallback": False},
        "budget": {"task_submissions": 1, "automatic_retries": 0, "harness_id": "codex",
                   "provider_calls_per_task": "NOT_ENFORCED_BY_UI_RUNNER"},
        "deadlines": {"flow_ms": 300000, "close_ms": 30000},
        "root_supervision": {"required": True, "mechanism": "ROOT_EXISTING_UNNAMED_JOB",
                             "controller_sha256": None, "launch_contract_sha256": None,
                             "outer_deadline_ms": 360000,
                             "proof": "ROOT exact original Job handle / Assign+IsProcessInJob-before-Resume / no-breakaway / final accounting; not runner self-attestation"},
        "product_acceptance": "NOT_RUN", "formal_increment": 0, "product_increment": 0,
    }
    target = HERE / "scope.template.json"
    if target.exists():
        raise SystemExit("SCOPE_TEMPLATE_ALREADY_EXISTS")
    target.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": scope["status"], "path": str(target), "sha256": digest(target)}))


if __name__ == "__main__":
    main()
