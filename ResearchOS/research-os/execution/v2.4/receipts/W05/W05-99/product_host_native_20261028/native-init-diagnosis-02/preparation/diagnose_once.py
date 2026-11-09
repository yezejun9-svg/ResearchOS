"""Preparation only. Run only with a separately sealed Root scope.

One fresh Electron/Core pair, one Native3 workspace-choice frame, one normal
owned-window close. A failed identity or close check leaves this controller
alive with its child handles and receipts for Root reconciliation.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def beneath(parent, child):
    parent, child = Path(parent).resolve(), Path(child).resolve()
    return child != parent and parent in child.parents


def save(out, name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_alive(pid):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.WaitForSingleObject.restype = ctypes.c_uint32
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    h = kernel.OpenProcess(0x00100000, 0, int(pid))  # SYNCHRONIZE only
    if not h:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: no such PID.
            return False
        raise RuntimeError(f"PROCESS_OPEN_FAILED:{pid}:{error}")
    try:
        result = kernel.WaitForSingleObject(h, 0)
        if result not in (0, 0x102):
            raise RuntimeError(f"PROCESS_QUERY_FAILED:{pid}:{result}")
        return result == 0x102
    finally:
        kernel.CloseHandle(h)


def hold(out, reason, electron, witness_path, children):
    try:
        current_witness = read_json(witness_path) if witness_path and witness_path.exists() else None
    except Exception as exc:
        current_witness = {"read_error": str(exc)}
    data = {"status": "UNRESOLVED_CONTROLLER_HOLDING_OWNED_HANDLES", "reason": str(reason),
            "electron_pid": electron.pid if electron else None,
            "electron_terminal": electron.poll() is not None if electron else None,
            "witness_path": str(witness_path) if witness_path else None,
            "witness": current_witness,
            "children": [{"pid": p.pid, "terminal": p.poll() is not None} for p in children],
            "forced_termination": False, "retry": False}
    save(out, "UNRESOLVED.json", data)
    print(json.dumps(data, ensure_ascii=False), flush=True)
    while True:
        time.sleep(5)


def wait_terminal(child, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if child.poll() is not None:
            return child.returncode
        time.sleep(0.1)
    return None


def launch(exe, args, cwd, env, out, name):
    stdout = open(out / f"{name}.stdout.raw", "xb")
    stderr = open(out / f"{name}.stderr.raw", "xb")
    try:
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0  # SW_HIDE, same launch posture as driver-v2.
        child = subprocess.Popen([str(exe), *map(str, args)], cwd=cwd, env=env,
                                 stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                 startupinfo=startup, shell=False)
    finally:
        stdout.close()
        stderr.close()
    save(out, f"{name}.spawn.json", {"pid": child.pid, "executable": str(exe), "args": list(map(str, args))})
    return child


def verify_scope(scope):
    assert scope["native_chooser_diagnosis_authorized"] is True
    assert scope["mode"] == "ONE_OWNED_NATIVE_CHOOSER_DIAGNOSIS_NO_PROVIDER"
    assert scope["formal_increment"] == 0
    worktree = Path(scope["worktree"]).resolve()
    bundle = Path(scope["bundle_root"]).resolve()
    state = Path(scope["state_root"]).resolve()
    out = Path(scope["receipts_root"]).resolve()
    assert beneath(worktree / ".local", bundle)
    assert beneath(worktree / ".local", state)
    assert beneath(SOURCE / "native-init-diagnosis-02", out)
    assert not beneath(HERE, out)
    assert not beneath(state, out) and not beneath(out, state)
    assert not state.exists() and not out.exists()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=worktree, text=True).strip()
    assert head == scope["candidate_commit"] and head.startswith("5c4c940")
    assert tree == scope["candidate_tree"]
    assert subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=worktree) == b""
    for ref in scope["bound_files"]:
        raw = Path(ref["path"]).read_bytes()
        assert len(raw) == ref["bytes"] and sha(raw) == ref["sha256"], ref["path"]
    required = [HERE / "diagnose_once.py", HERE / "choose-once.ps1",
                SOURCE / "driver-v2" / "choose-owned-folder.ps1",
                SOURCE / "driver-v2" / "close-owned-window.ps1",
                bundle / "installed-product.json"]
    assert all(any(Path(ref["path"]).resolve() == p.resolve() for ref in scope["bound_files"])
               for p in required), "SCOPE_MISSING_BOUND_TOOL"
    marker = read_json(bundle / "installed-product.json")
    assert marker["installation_id"] == scope["installation_id"]
    assert Path(marker["install_root"]).resolve() == bundle
    for row in marker["files"]:
        path = (bundle / row["path"]).resolve()
        assert beneath(bundle, path)
        raw = path.read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    assert scope["powershell_path"] and Path(scope["powershell_path"]).is_file()
    return worktree, bundle, state, out, marker


def main():
    if len(sys.argv) != 2 or os.name != "nt":
        raise SystemExit("usage: diagnose_once.py SEALED_SCOPE.json (Windows only)")
    scope = read_json(sys.argv[1])
    _, bundle, state, out, marker = verify_scope(scope)
    out.mkdir(parents=True, exist_ok=False)
    state.mkdir(parents=True, exist_ok=False)
    local, roaming, profile, temp = (state / name for name in ("LocalAppData", "Roaming", "User", "Temp"))
    workspace = state / "项目 空间"
    for path in (local, roaming, profile, temp, workspace):
        path.mkdir()
    (workspace / "README.md").write_text("ResearchOS owned native diagnosis\r\n", encoding="utf-8")
    witness_path = local / "ResearchOS" / "data" / "product-supervisor.json"
    env = {k: v for k, v in os.environ.items() if k.upper() in
           {"SYSTEMROOT", "WINDIR", "COMSPEC", "OS", "PATHEXT", "PATH"}}
    env.update({"LOCALAPPDATA": str(local), "APPDATA": str(roaming), "USERPROFILE": str(profile),
                "TEMP": str(temp), "TMP": str(temp)})
    electron = bundle / marker["binaries"]["electron"]["path"]
    core = bundle / marker["binaries"]["control"]["path"]
    app = bundle / "apps" / "desktop"
    assert beneath(bundle, electron) and beneath(bundle, core) and beneath(bundle, app)
    pwsh = Path(scope["powershell_path"])
    children = []
    desktop = None
    witness = None
    try:
        desktop = launch(electron, ["--remote-debugging-address=127.0.0.1",
                                    "--remote-debugging-port=0", app], bundle, env, out, "electron")
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if desktop.poll() is not None:
                raise RuntimeError("OWNED_ELECTRON_EXITED_BEFORE_READY")
            if witness_path.exists():
                candidate = read_json(witness_path)
                if candidate.get("state") == "READY":
                    witness = candidate
                    break
            time.sleep(0.1)
        if witness is None:
            raise RuntimeError("OWNED_READY_TIMEOUT")
        assert witness["schema"] == "researchos.product-supervisor/1"
        assert witness["parent_process"]["PID"] == desktop.pid
        assert Path(witness["install_root"]).resolve() == bundle
        assert witness["installation_id"] == marker["installation_id"]
        assert Path(witness["data_root"]).resolve() == witness_path.parent
        save(out, "witness-before.json", witness)
        core_pid = int(witness["control_process"]["PID"])
        confirm = launch(pwsh, ["-NoProfile", "-NonInteractive", "-File", SOURCE / "driver-v2" / "choose-owned-folder.ps1",
                                "-OwnedCorePid", core_pid, "-OwnedCoreImage", core,
                                "-OwnedCoreCreatedNS", witness["control_process"]["CreatedNS"],
                                "-OwnedCoreSHA256", witness["control_process"]["ImageSHA256"],
                                "-OwnedWorkspace", workspace], bundle, env, out, "folder-confirm")
        children.append(confirm)
        client = launch(pwsh, ["-NoProfile", "-NonInteractive", "-File", HERE / "choose-once.ps1",
                               "-WitnessPath", witness_path, "-CoreImage", core,
                               "-Workspace", workspace, "-OutDirectory", out], bundle, env, out, "native-client")
        children.append(client)
        client_exit = wait_terminal(client, 60)
        if client_exit is None:
            raise RuntimeError("NATIVE_CLIENT_TIMEOUT_NO_RETRY")
        folder_exit = wait_terminal(confirm, 35)
        if folder_exit is None:
            raise RuntimeError("FOLDER_CONTROLLER_TIMEOUT_NO_RETRY")
        save(out, "exchange-result.json", {"client_exit": client_exit, "folder_exit": folder_exit,
                                            "request_raw_present": (out / "native-request.raw").exists(),
                                            "reply_raw_present": (out / "native-reply.raw").exists()})
        # NATIVE_ERROR is a completed diagnostic exchange, so close normally.
        # A client-side failure is also closed after both helper processes end.
        close = launch(pwsh, ["-NoProfile", "-NonInteractive", "-File", SOURCE / "driver-v2" / "close-owned-window.ps1",
                              "-OwnedDesktopPid", desktop.pid, "-OwnedDesktopImage", electron,
                              "-OwnedDesktopCreatedNS", witness["parent_process"]["CreatedNS"],
                              "-OwnedDesktopSHA256", witness["parent_process"]["ImageSHA256"]],
                       bundle, env, out, "normal-close")
        children.append(close)
        close_exit = wait_terminal(close, 35)
        if close_exit != 0:
            raise RuntimeError(f"OWNED_NORMAL_CLOSE_UNCONFIRMED:{close_exit}")
        close_output = read_json(out / "normal-close.stdout.raw")
        if (close_output.get("scope") != "ONLY_OWNED_PRODUCT_WINDOW_CLOSE" or
                close_output.get("desktop_pid") != desktop.pid or
                close_output.get("message_delivered") is not True):
            raise RuntimeError("OWNED_NORMAL_CLOSE_RECEIPT_INVALID")
        end = time.monotonic() + 35
        while time.monotonic() < end and (process_alive(desktop.pid) or process_alive(core_pid)):
            time.sleep(0.2)
        if process_alive(desktop.pid) or process_alive(core_pid):
            raise RuntimeError("OWNED_PROCESSES_STILL_ALIVE_AFTER_CLOSE")
        save(out, "RESULT.json", {"status": "OWNED_PAIR_CLOSED", "request_count_maximum": 1,
                                  "client_exit": client_exit, "folder_exit": folder_exit,
                                  "close_exit": close_exit, "electron_pid": desktop.pid, "core_pid": core_pid,
                                  "electron_absent": True, "core_absent": True,
                                  "raw_reply": str(out / "native-reply.raw"), "formal_increment": 0})
    except BaseException as exc:
        # Do not lose the owned handles if the exact close sequence cannot be proved.
        hold(out, exc, desktop, witness_path, children)


if __name__ == "__main__":
    main()
