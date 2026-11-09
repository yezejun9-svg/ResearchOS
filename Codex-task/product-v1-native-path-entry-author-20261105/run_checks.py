from pathlib import Path
import json
import os
import subprocess
import time

QA = Path(__file__).resolve().parent
WT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-path-entry-20261105")
GO = r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe"
for name in ("go-cache", "go-tmp", "test-temp"):
    (QA / name).mkdir(exist_ok=False)
env = dict(os.environ)
env.update({
    "GOCACHE": str(QA / "go-cache"),
    "GOTMPDIR": str(QA / "go-tmp"),
    "TEMP": str(QA / "test-temp"),
    "TMP": str(QA / "test-temp"),
    "GOMODCACHE": r"D:\作品集\ResearchOS\research-os\.local\tools\gopath\pkg\mod",
    "GOPROXY": "off", "GOSUMDB": "off", "GOTOOLCHAIN": "local",
    "GOFLAGS": "-mod=readonly", "RESEARCHOS_NATIVE_FOLDER_GUI_TEST": "0",
    "RESEARCHOS_NATIVE_FOLDER_HELPER": "",
})
commands = [
    ("focused-test", [GO, "test", "./internal/host", "-run", "TestNativeFolderValidation|TestNativeFolderInitializationEffectsPreserved|TestNativeFolderCancelledChoiceDoesNotGrant|TestNativeWorkspaceChooseNeedsConfirmedHostSelection|TestNativeWorkspaceChooseRequiresExplicitNullablePath|TestNativeWindowsFolderChooserAPIsPresent", "-count=1", "-timeout=90s", "-json"]),
    ("vet", [GO, "vet", "./internal/host"]),
]
results = []
for name, argv in commands:
    print(json.dumps({"stage": name, "state": "started"}), flush=True)
    started = time.monotonic()
    proc = subprocess.run(argv, cwd=WT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=360)
    (QA / f"{name}.stdout.log").write_bytes(proc.stdout)
    (QA / f"{name}.stderr.log").write_bytes(proc.stderr)
    record = {"stage": name, "argv": argv, "cwd": str(WT), "exit_code": proc.returncode, "elapsed_seconds": round(time.monotonic() - started, 3)}
    results.append(record)
    (QA / "checks.json").write_text(json.dumps({"checks": results, "gui_runs": 0, "model_runs": 0, "formal_increment": 0, "product_acceptance_increment": 0}, indent=2), encoding="utf-8")
    print(json.dumps(record), flush=True)
    if proc.returncode != 0:
        print(proc.stderr.decode("utf-8", errors="replace")[-4000:], flush=True)
        raise SystemExit(proc.returncode)
