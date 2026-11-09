from pathlib import Path
import json
import os
import subprocess
import time

QA = Path(__file__).resolve().parent
WT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-path-entry-20261105")
TOOLS = Path(r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin")
source = WT / "internal/host/native_folder_windows.go"
old = "The folder path is invalid or does not exist. Enter an existing folder path and try again."
new = "文件夹路径无效或不存在。请输入已有的文件夹路径后重试。"
text = source.read_text(encoding="utf-8")
assert text.count(old) == 1 and new not in text
source.write_bytes(text.replace(old, new, 1).encode("utf-8"))
subprocess.run([str(TOOLS / "gofmt.exe"), "-w", str(source)], check=True)
env = dict(os.environ)
env.update({
    "GOCACHE": str(QA / "go-cache"), "GOTMPDIR": str(QA / "go-tmp"),
    "TEMP": str(QA / "test-temp"), "TMP": str(QA / "test-temp"),
    "GOMODCACHE": r"D:\作品集\ResearchOS\research-os\.local\tools\gopath\pkg\mod",
    "GOPROXY": "off", "GOSUMDB": "off", "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly",
    "RESEARCHOS_NATIVE_FOLDER_GUI_TEST": "0", "RESEARCHOS_NATIVE_FOLDER_HELPER": "",
})
checks = json.loads((QA / "checks.json").read_text(encoding="utf-8"))
assert [x["stage"] for x in checks["checks"]] == ["focused-test", "vet"]
commands = [
    ("final-compile", [str(TOOLS / "go.exe"), "test", "./internal/host", "-run", "^$", "-count=1", "-timeout=90s"]),
    ("final-vet", [str(TOOLS / "go.exe"), "vet", "./internal/host"]),
]
for name, argv in commands:
    print(json.dumps({"stage": name, "state": "started"}), flush=True)
    started = time.monotonic()
    proc = subprocess.run(argv, cwd=WT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    (QA / f"{name}.stdout.log").write_bytes(proc.stdout)
    (QA / f"{name}.stderr.log").write_bytes(proc.stderr)
    record = {"stage": name, "argv": argv, "cwd": str(WT), "exit_code": proc.returncode, "elapsed_seconds": round(time.monotonic() - started, 3)}
    checks["checks"].append(record)
    checks["final_warning"] = {"text": new, "caption": "ResearchOS", "flags": "0x30", "owner": "callback hwnd", "lparam_read": False}
    (QA / "checks.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(record), flush=True)
    if proc.returncode != 0:
        print(proc.stderr.decode("utf-8", errors="replace")[-4000:], flush=True)
        raise SystemExit(proc.returncode)
