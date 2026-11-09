"""Sealed, finite A/B controller. Preparation only; never run without a new Root scope."""

import ctypes
from ctypes import wintypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import uuid


PREP = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\desktop-installed-delivery-20261025")
ARTIFACT = WORKTREE / ".local" / "native-folder-environment-cp570"
RECEIPTS = PREP.parent
SCHEMA = "researchos.native-folder-environment-run.v1"
KERNEL = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None
USER32 = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None
if os.name == "nt":
    KERNEL.GetProcessId.argtypes = [wintypes.HANDLE]
    KERNEL.GetProcessId.restype = wintypes.DWORD
    KERNEL.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_void_p, ctypes.c_void_p]
    KERNEL.GetProcessTimes.restype = wintypes.BOOL
    USER32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    USER32.GetWindowThreadProcessId.restype = wintypes.DWORD
    USER32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    USER32.GetClassNameW.restype = ctypes.c_int
    USER32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.c_void_p]
    USER32.GetWindowRect.restype = wintypes.BOOL
    USER32.IsWindowVisible.argtypes = [wintypes.HWND]
    USER32.IsWindowVisible.restype = wintypes.BOOL
    USER32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    USER32.PostMessageW.restype = wintypes.BOOL


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(directory, name, value):
    target = directory / name
    with target.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def relative_to(path, root):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def validate_scope(path):
    scope = json.loads(path.read_text(encoding="utf-8"))
    assert scope["schema"] == SCHEMA
    assert scope["native_execution_authorized"] is True
    assert scope["formal_increment"] == 0
    assert scope["case_order"] == ["A", "B"] and scope["max_helper_calls"] == 2
    assert scope["candidate_commit"] == "5c4c94022bd92da68ef544f2779527bfe065c428"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKTREE, text=True).strip() == scope["candidate_commit"]
    assert subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=WORKTREE) == b""
    assert scope["preparation_sha256"] == digest(PREP / "PREPARATION.json")
    assert scope["controller_sha256"] == digest(__file__)
    assert scope["helper_sha256"] == digest(ARTIFACT / "native-folder-environment.exe")
    assert Path(scope["artifact_root"]).resolve() == ARTIFACT.resolve()
    assert Path(scope["helper_path"]).resolve() == (ARTIFACT / "native-folder-environment.exe").resolve()
    state = Path(scope["state_root"]).resolve()
    out = Path(scope["receipts_root"]).resolve()
    assert relative_to(state, WORKTREE / ".local") and state != ARTIFACT.resolve()
    assert not relative_to(state, ARTIFACT)
    assert relative_to(out, RECEIPTS) and out != PREP.resolve()
    assert out.relative_to(RECEIPTS).parts[0].startswith("execution-")
    assert not state.exists() and not out.exists()
    # Values are controlled by the current OS session, never supplied by the scope.
    system_root = os.environ.get("SystemRoot")
    windir = os.environ.get("WINDIR")
    system_drive = os.environ.get("SystemDrive")
    assert system_root and windir and system_drive
    assert Path(system_root).resolve() == Path(windir).resolve()
    assert os.path.splitdrive(system_root)[0].casefold() == system_drive.casefold()
    assert len(system_drive) == 2 and system_drive[1] == ":"
    return scope, state, out, system_root, windir, system_drive


class FILETIME(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


def process_identity(child):
    handle = wintypes.HANDLE(child._handle)  # Retained Popen process handle.
    pid = KERNEL.GetProcessId(handle)
    assert pid == child.pid and pid > 0, "PROCESS_HANDLE_PID_CHANGED"
    created, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not KERNEL.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                  ctypes.byref(kernel), ctypes.byref(user)):
        raise OSError(ctypes.get_last_error(), "GET_PROCESS_TIMES_FAILED")
    ticks = (created.high << 32) | created.low
    return pid, ticks


def windows_for(pid):
    rows = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def visit(hwnd, _):
        owner = wintypes.DWORD()
        thread_id = USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            class_name = ctypes.create_unicode_buffer(256)
            USER32.GetClassNameW(hwnd, class_name, 256)
            rect = RECT()
            USER32.GetWindowRect(hwnd, ctypes.byref(rect))
            rows.append({"hwnd": int(hwnd), "pid": owner.value, "thread": int(thread_id),
                         "class": class_name.value, "visible": bool(USER32.IsWindowVisible(hwnd)),
                         "rect": [rect.left, rect.top, rect.right, rect.bottom]})
        return True

    callback = callback_type(visit)
    USER32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    USER32.EnumWindows.restype = wintypes.BOOL
    if not USER32.EnumWindows(callback, 0):
        raise OSError(ctypes.get_last_error(), "ENUM_WINDOWS_FAILED")
    return rows


def exact_dialog(rows):
    matches = [row for row in rows if row["class"] == "#32770" and row["visible"] and
               row["rect"][2] > row["rect"][0] and row["rect"][3] > row["rect"][1]]
    return matches[0] if len(matches) == 1 else None


def read_lines(stream, destination):
    try:
        for line in stream:
            destination.put(("line", line.rstrip("\r\n")))
    except BaseException as exc:
        destination.put(("error", repr(exc)))
    finally:
        destination.put(("eof", None))


def next_event(inbox, seconds):
    kind, value = inbox.get(timeout=seconds)
    if kind != "line":
        raise RuntimeError(f"HELPER_STREAM_{kind}:{value}")
    event = json.loads(value)
    if not isinstance(event, dict):
        raise RuntimeError("HELPER_EVENT_NOT_OBJECT")
    return event


def unresolved_hold(out, scope_hash, child, exc):
    pid = child.pid if child else None
    nonce = uuid.uuid4().hex
    save(out, "UNRESOLVED.json", {"reason": repr(exc), "helper_pid": pid,
                                  "helper_alive": bool(child and child.poll() is None),
                                  "forced_termination": False, "automatic_retry": False})
    save(out, "WAITING_FOR_ROOT.json", {"controller_pid": os.getpid(), "helper_pid": pid,
                                         "scope_sha256": scope_hash, "release_nonce": nonce,
                                         "release_path": str(out / "ROOT-RELEASE.json")})
    if child is None or child.poll() is not None:
        return
    # Retain the owning Popen handle until Root has independently retired the
    # process, then supplies the exact release record. No timeout or kill.
    while True:
        try:
            release_path = out / "ROOT-RELEASE.json"
            if release_path.exists():
                release = json.loads(release_path.read_text(encoding="utf-8"))
                if (release.get("controller_pid") == os.getpid() and
                    release.get("helper_pid") == pid and
                    release.get("scope_sha256") == scope_hash and
                    release.get("release_nonce") == nonce and
                    child.poll() is not None):
                    child.wait()
                    return
            time.sleep(2)
        except KeyboardInterrupt:
            continue
        except BaseException:
            time.sleep(2)


def run_case(label, helper, workspace, env, out, scope_hash):
    case_out = out / label
    case_out.mkdir(exist_ok=False)
    child = None
    try:
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0  # SW_HIDE for both cases.
        with (case_out / "stderr.raw").open("xb") as stderr_file:
            child = subprocess.Popen([str(helper), str(workspace)], cwd=ARTIFACT, env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=stderr_file, text=True, encoding="utf-8",
                                     errors="strict", startupinfo=startup, shell=False)
        held_pid, held_created = process_identity(child)
        save(case_out, "spawn.json", {"pid": held_pid, "created_filetime": held_created,
                                      "image": str(helper), "startup_requested_flags": startup.dwFlags,
                                      "startup_requested_show": startup.wShowWindow,
                                      "env_keys": sorted(env), "system_drive": env.get("SystemDrive"),
                                      "hint": str(workspace)})
        inbox = queue.Queue()
        threading.Thread(target=read_lines, args=(child.stdout, inbox), daemon=True).start()
        ready = next_event(inbox, 10)
        assert ready["event"] == "ready" and ready["pid"] == held_pid
        assert ready["startup_flags"] & 1 and ready["startup_show"] == 0, "HELPER_NOT_STARTUP_HIDDEN"
        save(case_out, "ready.json", ready)
        child.stdin.write("open\n")
        child.stdin.flush()
        child.stdin.close()
        started = time.monotonic()
        observed = []
        stable_hwnd = None
        stable_since = None
        cancelled = None
        while time.monotonic() - started < 25:
            rows = windows_for(held_pid)
            candidate = exact_dialog(rows)
            if rows:
                observed.append({"elapsed_ms": round((time.monotonic() - started) * 1000), "windows": rows})
            if candidate:
                if stable_hwnd != candidate["hwnd"]:
                    stable_hwnd, stable_since = candidate["hwnd"], time.monotonic()
                if time.monotonic() - stable_since >= 0.5:
                    assert process_identity(child) == (held_pid, held_created), "HELPER_IDENTITY_CHANGED"
                    fresh = exact_dialog(windows_for(held_pid))
                    assert fresh and fresh["hwnd"] == stable_hwnd, "DIALOG_IDENTITY_CHANGED"
                    sent = USER32.PostMessageW(wintypes.HWND(stable_hwnd), 0x111, 2, 0)  # WM_COMMAND/IDCANCEL.
                    cancelled = {"hwnd": stable_hwnd, "pid": held_pid, "post_idcancel": bool(sent),
                                 "last_error": ctypes.get_last_error() if not sent else 0}
                    if not sent:
                        raise RuntimeError("OWNED_IDCANCEL_POST_FAILED")
                    break
            else:
                stable_hwnd, stable_since = None, None
            if child.poll() is not None:
                break
            time.sleep(0.05)
        save(case_out, "windows.json", observed)
        save(case_out, "cancel.json", cancelled or {"post_idcancel": False, "reason": "NO_VISIBLE_OWNED_DIALOG"})
        try:
            result = next_event(inbox, 10)
        except queue.Empty as exc:
            raise RuntimeError("HELPER_NO_RESULT_AFTER_OBSERVATION") from exc
        assert result["event"] == "result" and result["pid"] == held_pid
        save(case_out, "result.json", result)
        try:
            exit_code = child.wait(timeout=10)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("HELPER_STILL_LIVE_AFTER_RESULT") from exc
        save(case_out, "exit.json", {"exit_code": exit_code, "controller_cancelled": bool(cancelled),
                                     "error": result.get("error"), "elapsed_ns": result.get("elapsed_ns")})
        if exit_code != 0:
            raise RuntimeError("HELPER_NONZERO_EXIT")
        if result.get("chosen") or not result.get("error"):
            raise RuntimeError("UNEXPECTED_FOLDER_SELECTION_OR_EMPTY_ERROR")
        return {"case": label, "cancelled": bool(cancelled), "result": result}
    except BaseException as exc:
        unresolved_hold(case_out, scope_hash, child, exc)
        raise


def main():
    if os.name != "nt" or len(sys.argv) != 2:
        raise SystemExit("usage: controller.py SEALED_RUN_SCOPE.json (Windows only)")
    path = Path(sys.argv[1]).resolve()
    scope_hash = digest(path)
    scope, state, out, system_root, windir, system_drive = validate_scope(path)
    state.mkdir(parents=True, exist_ok=False)
    out.mkdir(parents=True, exist_ok=False)
    local, roaming, profile, temporary, workspace = [state / name for name in
        ("LocalAppData", "Roaming", "User", "Temp", "项目 空间")]
    for item in (local, roaming, profile, temporary, workspace):
        item.mkdir()
    (workspace / "README.md").write_text("owned native environment probe\n", encoding="utf-8")
    env_a = {"SystemRoot": system_root, "WINDIR": windir, "TEMP": str(temporary),
             "TMP": str(temporary), "USERPROFILE": str(profile), "APPDATA": str(roaming),
             "LOCALAPPDATA": str(local)}
    env_b = dict(env_a)
    env_b["SystemDrive"] = system_drive
    save(out, "environment-contract.json", {"A_keys": sorted(env_a), "B_keys": sorted(env_b),
                                             "B_only": {"SystemDrive": system_drive},
                                             "same_hint": str(workspace), "scope_sha256": scope_hash})
    helper = ARTIFACT / "native-folder-environment.exe"
    results = []
    for label, env in (("A", env_a), ("B", env_b)):
        results.append(run_case(label, helper, workspace, env, out, scope_hash))
    save(out, "RESULT.json", {"status": "A_B_DIAGNOSTIC_COMPLETED", "cases": results,
                              "formal_increment": 0, "at": datetime.datetime.now(datetime.timezone.utc).isoformat()})


if __name__ == "__main__":
    main()
