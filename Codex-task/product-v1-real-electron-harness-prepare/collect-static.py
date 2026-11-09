"""Read only explicit public sources; never import/launch the product or SDK."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("D:/作品集/ResearchOS/research-os")
CACHE = Path("C:/Users/yqyyds/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright-core")
SOURCES = {
    "apps/desktop/launch-development.mjs": [[83, 146], [152, 190], [218, 226]],
    "apps/desktop/main/main.js": [[28, 48], [369, 444], [479, 520]],
    "apps/desktop/main/lib/desktop-management.js": [[413, 461], [790, 830]],
    "apps/desktop/main/lib/first-use.js": [[1, 65]],
    "apps/desktop/main/lib/shared-host-locator.js": [[40, 49]],
    "apps/desktop/main/lib/ipc.js": [[363, 507]],
    "apps/desktop/main/lib/harness-wire.js": [[45, 100]],
    "apps/desktop/preload/preload.js": [[1, 140]],
    "apps/web/src/workbench.jsx": [[163, 190], [397, 530]],
    "apps/web/src/harness.js": [[90, 190]],
    "apps/web/src/screens.jsx": [[55, 63], [244, 250]],
    "internal/host/native_folder_windows.go": [[64, 108]],
    "internal/host/native_pipe_windows.go": [[76, 82], [127, 147]],
    "internal/host/native.go": [[337, 388]],
    "execution/product-v1/contracts/harness.v1.interface.rev2.json": [[1, 110], [1150, 1160]],
}


def pin(file):
    raw = file.read_bytes()
    return {"path": str(file), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def main():
    evidence = {"schema": "researchos.real-electron-harness.static-evidence/1",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "status": "PREPARATION_ONLY_NOT_RUN", "sources": [], "tools": [],
                "no_product_gui_model_native_db_execution": True}
    for name, ranges in SOURCES.items():
        file = REPO / name
        entry = pin(file)
        entry["relative_path"] = name
        lines = file.read_text(encoding="utf-8").splitlines()
        entry["excerpts"] = [{"line": i, "text": line} for i, line in enumerate(lines, 1)
                             if any(a <= i <= b for a, b in ranges)]
        evidence["sources"].append(entry)
    for name in ["package.json", "index.mjs", "index.js", "lib/coreBundle.js", "types/types.d.ts"]:
        evidence["tools"].append(pin(CACHE / name))
    package = json.loads((CACHE / "package.json").read_text(encoding="utf-8"))
    evidence["playwright"] = {"path": str(CACHE), "version": package["version"],
                              "electron_export": "_electron", "runtime_import_tested": False}
    for file in [Path("C:/nvm4w/nodejs/node.exe"),
                 Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")]:
        evidence["tools"].append(pin(file))
    target = HERE / "STATIC_EVIDENCE.json"
    if target.exists():
        raise SystemExit("STATIC_EVIDENCE_ALREADY_EXISTS")
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": evidence["status"], "path": str(target), **pin(target)}))


if __name__ == "__main__":
    main()
