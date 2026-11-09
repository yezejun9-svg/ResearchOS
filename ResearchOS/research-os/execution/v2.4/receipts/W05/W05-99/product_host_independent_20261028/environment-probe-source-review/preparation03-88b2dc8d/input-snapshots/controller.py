"""Sealed finite C then A2-or-D controller. Preparation only until Root run scope."""

import ctypes
from ctypes import wintypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid


PREP = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\desktop-installed-delivery-20261025")
ARTIFACT = WORKTREE / ".local" / "native-folder-environment-cp570" / "revision02"
RECEIPTS = PREP.parent
OLD_STATE = WORKTREE / ".local" / "native-folder-environment-cp572-AB01"
OLD_RECEIPT = RECEIPTS / "execution-cp572-AB01"
SOURCE_SCOPE = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp573\Native-folder-followup-preparation03-scope.json")
SCHEMA = "researchos.native-folder-followup-run.v1"
SOURCE_SCOPE_SHA256 = "f43998c1617d0e7596b7ef9f05b618e8b30f7de789511b295d66be992af7bb7a"
APPROVED_OS_KEYS = ("ComSpec", "Path", "PATHEXT", "OS", "ProgramData", "ProgramFiles",
                    "ProgramFiles(x86)", "USERNAME", "USERDOMAIN", "SystemDrive")
CASE_PLAN = {"first": "C", "if_visible_cancelled": "A2", "if_shell_null": "D"}
SHELL_NULL_MAX_NS = 2_000_000_000
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


def env_digest(env):
    return hashlib.sha256(json.dumps(env, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


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


def checked_ref(ref):
    path = Path(ref["path"])
    assert path.stat().st_size == ref["bytes"] and digest(path) == ref["sha256"]
    return path


def no_reparse(path):
    metadata = os.lstat(path)
    assert not stat.S_ISLNK(metadata.st_mode), "SYNTHETIC_STATE_SYMLINK"
    assert not (getattr(metadata, "st_file_attributes", 0) & 0x400), "SYNTHETIC_STATE_REPARSE"
    return metadata


def manifest_state(root):
    # This is the CP572-owned synthetic state only. Enumerate without following
    # any symlink/junction; hash contents to expose Shell cache changes.
    root = Path(root)
    no_reparse(root)
    entries = []

    def visit(directory):
        for entry in sorted(os.scandir(directory), key=lambda row: row.name.casefold()):
            path = Path(entry.path)
            metadata = no_reparse(path)
            rel = path.relative_to(root).as_posix()
            if stat.S_ISDIR(metadata.st_mode):
                entries.append({"path": rel, "type": "dir", "mtime_ns": metadata.st_mtime_ns})
                visit(path)
            elif stat.S_ISREG(metadata.st_mode):
                entries.append({"path": rel, "type": "file", "bytes": metadata.st_size,
                                "sha256": digest(path), "mtime_ns": metadata.st_mtime_ns})
            else:
                raise RuntimeError("SYNTHETIC_STATE_UNEXPECTED_ENTRY:" + rel)
            assert len(entries) <= 10000, "SYNTHETIC_STATE_TOO_MANY_ENTRIES"

    visit(root)
    payload = {"root": str(root), "entries": entries}
    payload["sha256"] = hashlib.sha256(json.dumps(entries, sort_keys=True, ensure_ascii=False,
                                               separators=(",", ":")).encode("utf-8")).hexdigest()
    return payload


def build_environments(state, system_root, windir):
    local, roaming, profile, temporary, workspace = [state / name for name in
        ("LocalAppData", "Roaming", "User", "Temp", "项目 空间")]
    for path in (local, roaming, profile, temporary, workspace):
        assert path.is_dir() and no_reparse(path), "SYNTHETIC_STATE_DIRECTORY_MISSING"
    a = {"SystemRoot": system_root, "WINDIR": windir, "TEMP": str(temporary),
         "TMP": str(temporary), "USERPROFILE": str(profile), "APPDATA": str(roaming),
         "LOCALAPPDATA": str(local)}
    c = dict(a)
    for key in APPROVED_OS_KEYS:
        if os.environ.get(key):
            c[key] = os.environ[key]
    drive, tail = os.path.splitdrive(str(profile))
    assert drive and tail.startswith("\\"), "SYNTHETIC_HOME_NOT_DRIVE_ABSOLUTE"
    c["HOMEDRIVE"], c["HOMEPATH"] = drive, tail
    assert set(c) - set(a) <= set(APPROVED_OS_KEYS) | {"HOMEDRIVE", "HOMEPATH"}
    return a, c, workspace


def validate_scope(path):
    if not __debug__:
        raise RuntimeError("PYTHON_OPTIMIZATION_FORBIDDEN")
    scope = json.loads(path.read_text(encoding="utf-8"))
    assert scope["schema"] == SCHEMA
    assert scope["native_execution_authorized"] is True
    assert scope["formal_increment"] == 0
    assert scope["case_plan"] == CASE_PLAN and scope["max_helper_calls"] == 2
    assert scope["shell_null_max_elapsed_ns"] == SHELL_NULL_MAX_NS
    assert scope["candidate_commit"] == "5c4c94022bd92da68ef544f2779527bfe065c428"
    git = ["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false"]
    assert subprocess.check_output(git + ["rev-parse", "HEAD"], cwd=WORKTREE, text=True).strip() == scope["candidate_commit"]
    assert subprocess.check_output(git + ["status", "--porcelain=v1", "--untracked-files=all"], cwd=WORKTREE) == b""
    assert digest(SOURCE_SCOPE) == SOURCE_SCOPE_SHA256
    source_scope = json.loads(SOURCE_SCOPE.read_text(encoding="utf-8"))
    for name in ("prior_controller_ref", "prior_preparation_ref", "helper_ref", "actual_adoption_ref",
                 "analysis_ref", "old_probe_environment_ref", "old_probe_spawn_ref"):
        checked_ref(source_scope[name])
    assert scope["source_scope_sha256"] == SOURCE_SCOPE_SHA256
    assert scope["preparation_sha256"] == digest(PREP / "PREPARATION.json")
    assert scope["controller_sha256"] == digest(__file__)
    assert scope["helper_sha256"] == digest(ARTIFACT / "native-folder-environment.exe")
    assert Path(scope["artifact_root"]).resolve() == ARTIFACT.resolve()
    assert Path(scope["helper_path"]).resolve() == (ARTIFACT / "native-folder-environment.exe").resolve()
    assert Path(scope["state_root"]) == OLD_STATE
    state = OLD_STATE
    for candidate in (WORKTREE, WORKTREE / ".local", WORKTREE / ".local" / "native-folder-environment-cp572-AB01"):
        no_reparse(candidate)
    assert state.resolve(strict=True) == OLD_STATE.resolve(strict=True)
    out = Path(scope["receipts_root"]).resolve()
    assert relative_to(out, RECEIPTS) and out != PREP.resolve()
    assert out.relative_to(RECEIPTS).parts[0].startswith("execution-")
    assert not out.exists()
    # Values are controlled by the current OS session, never supplied by the scope.
    system_root = os.environ.get("SystemRoot")
    windir = os.environ.get("WINDIR")
    assert system_root and windir
    assert Path(system_root).resolve() == Path(windir).resolve()
    a, c, workspace = build_environments(state, system_root, windir)
    old_env = json.loads((OLD_RECEIPT / "environment-contract.json").read_text(encoding="utf-8"))
    old_spawn = json.loads((OLD_RECEIPT / "A" / "spawn.json").read_text(encoding="utf-8"))
    assert sorted(a) == old_env["A_keys"] == old_spawn["env_keys"]
    assert str(workspace) == old_env["same_hint"] == old_spawn["hint"]
    assert scope["a_env_sha256"] == env_digest(a) and scope["c_env_sha256"] == env_digest(c)
    state_before = manifest_state(state)
    assert scope["state_manifest_sha256"] == state_before["sha256"]
    return scope, state, out, a, c, workspace, state_before


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


def read_lines(stream, destination, raw_bytes, faults):
    try:
        for line in stream:
            raw_bytes.extend(line)
            destination.put(("line", line.decode("utf-8", errors="strict").rstrip("\r\n")))
    except BaseException as exc:
        faults.append(repr(exc))
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


def choose_branch(first):
    result = first["result"]
    assert result["event"] == "result" and result.get("error") == "INVALID_REQUEST: folder selection cancelled"
    assert not result.get("chosen"), "C_UNEXPECTED_SELECTION"
    elapsed = result.get("elapsed_ns")
    assert type(elapsed) is int and elapsed > 0, "C_INVALID_ELAPSED_TIME"
    if first["cancelled"] is True:
        return "A2"
    if first["cancelled"] is False and elapsed <= SHELL_NULL_MAX_NS:
        return "D"
    raise RuntimeError("C_UNEXPECTED_BRANCH_STATE")


def startup_for(hidden):
    startup = subprocess.STARTUPINFO()
    if hidden:
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    return startup


def verify_startup(ready, hidden, expected_flags):
    assert bool(ready["startup_flags"] & 1) is hidden, "HELPER_STARTUP_VISIBILITY_MISMATCH"
    if hidden:
        assert ready["startup_show"] == 0, "HELPER_NOT_STARTUP_HIDDEN"
    if expected_flags is not None:
        assert (ready["startup_flags"] & ~1) == (expected_flags & ~1), "STARTUP_OTHER_FLAGS_CHANGED"
        assert (ready["startup_flags"] ^ expected_flags) == (0 if hidden else 1), "STARTUP_EXPECTED_BIT_DELTA_MISSING"


def safe_record(out, name, value):
    try:
        save(out, name, value)
        return True
    except BaseException:
        return False


def safe_append(path, value):
    try:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        return True
    except BaseException:
        return False


def ignore_interrupts():
    # The same pattern as the reviewed native chooser diagnosis hold. An OS
    # force termination is outside this script's authority, not a cleanup path.
    for name in ("SIGINT", "SIGBREAK", "SIGTERM"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, signal.SIG_IGN)
            except BaseException:
                pass


def release_valid(path, waiting):
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    required = {"schema", "actor", "scope_sha256", "controller_pid", "helper_pid",
                "release_nonce", "root_confirmed_identity_absence", "confirmed_absent_at"}
    if set(value) != required or value["schema"] != "researchos.native-folder-environment-root-release.v1":
        return False
    for key in ("scope_sha256", "controller_pid", "helper_pid", "release_nonce"):
        if value[key] != waiting[key]:
            return False
    if value["actor"] != "codex:/root" or value["root_confirmed_identity_absence"] is not True:
        return False
    confirmed = datetime.datetime.fromisoformat(value["confirmed_absent_at"].replace("Z", "+00:00"))
    entered = datetime.datetime.fromisoformat(waiting["at"])
    return confirmed.tzinfo is not None and confirmed >= entered


def unresolved_hold(out, scope_hash, child, nonce, exc):
    # Enter this function with the live/unknown Popen handle still in `child`.
    # No receipt write, signal, scan, print, or sleep may escape this loop.
    waiting = None
    unresolved_written = False
    waiting_written = False
    announced = False
    while True:
        try:
            ignore_interrupts()
            if waiting is None:
                release_path = out / "ROOT-RELEASE.json"
                try:
                    release_preexisted = release_path.exists()
                except BaseException:
                    release_preexisted = True
                waiting = {"schema": "researchos.native-folder-environment-waiting.v1",
                           "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           "scope_sha256": scope_hash, "controller_pid": os.getpid(),
                           "helper_pid": child.pid, "release_nonce": nonce,
                           "release_path": str(release_path), "release_preexisted_wait": release_preexisted,
                           "reason": repr(exc), "forced_termination": False, "automatic_retry": False}
            if not announced:
                try:
                    print(json.dumps({"status": "WAITING_FOR_ROOT", "controller_pid": os.getpid(),
                                      "helper_pid": child.pid, "release_path": str(release_path)}), flush=True)
                    announced = True
                except BaseException:
                    pass
            unresolved = {"status": "UNRESOLVED_CONTROLLER_HOLDING_HELPER_HANDLE", "reason": repr(exc),
                          "helper_pid": child.pid, "helper_image": str(ARTIFACT / "native-folder-environment.exe"),
                          "forced_termination": False, "automatic_retry": False}
            if not unresolved_written:
                unresolved_written = safe_record(out, "UNRESOLVED.json", unresolved)
            if not waiting_written:
                waiting_written = safe_record(out, "WAITING_FOR_ROOT.json", waiting)
            if (waiting_written and not waiting["release_preexisted_wait"] and release_path.exists() and
                    release_valid(release_path, waiting)):
                if child.poll() is not None:
                    child.wait()  # No live helper handle is released.
                    if safe_record(out, "ROOT-RELEASED.json", {"status": "ROOT_RELEASED_AFTER_HELPER_ABSENCE",
                                                             "scope_sha256": scope_hash,
                                                             "controller_pid": os.getpid(),
                                                             "helper_pid": child.pid,
                                                             "formal_increment": 0}):
                        return
            time.sleep(2)
        except BaseException as hold_error:
            try:
                safe_append(out / "hold-errors.jsonl", {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                                        "error": repr(hold_error)})
            except BaseException:
                pass
            try:
                time.sleep(2)
            except BaseException:
                pass


def run_case(label, helper, workspace, env, out, scope_hash, state, hidden, expected_flags):
    case_out = out / label
    case_out.mkdir(exist_ok=False)
    child = None
    nonce = uuid.uuid4().hex
    # This pre-spawn contract survives even if the first post-spawn receipt
    # fails. It binds Root's release to this controller/scope/nonce; the true
    # helper PID is added to WAITING_FOR_ROOT after Popen returns.
    save(case_out, "hold-contract.json", {"scope_sha256": scope_hash, "controller_pid": os.getpid(),
                                          "release_nonce": nonce, "helper_image": str(helper)})
    before = manifest_state(state)
    save(case_out, "state-before.json", before)
    raw_stdout = bytearray()
    try:
        startup = startup_for(hidden)  # SW_HIDE only for C and A2.
        with (case_out / "stderr.raw").open("xb") as stderr_file:
            child = subprocess.Popen([str(helper), str(workspace)], cwd=ARTIFACT, env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=stderr_file, startupinfo=startup, shell=False)
        held_pid, held_created = process_identity(child)
        save(case_out, "spawn.json", {"pid": held_pid, "created_filetime": held_created,
                                      "image": str(helper), "startup_requested_flags": startup.dwFlags,
                                      "startup_requested_show": startup.wShowWindow,
                                      "env_keys": sorted(env), "system_drive": env.get("SystemDrive"),
                                      "env_sha256": env_digest(env), "hint": str(workspace)})
        inbox = queue.Queue()
        reader_faults = []
        reader = threading.Thread(target=read_lines, args=(child.stdout, inbox, raw_stdout, reader_faults), daemon=True)
        reader.start()
        ready = next_event(inbox, 10)
        assert ready["event"] == "ready" and ready["pid"] == held_pid
        verify_startup(ready, hidden, expected_flags)
        save(case_out, "ready.json", ready)
        child.stdin.write(b"open\n")
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
        reader.join(timeout=5)
        assert not reader.is_alive() and not reader_faults, "HELPER_STDOUT_READER_UNRESOLVED"
        with (case_out / "stdout.raw").open("xb") as stream:
            stream.write(raw_stdout)
        after = manifest_state(state)
        save(case_out, "state-after.json", after)
        before_by = {row["path"]: row for row in before["entries"]}
        after_by = {row["path"]: row for row in after["entries"]}
        save(case_out, "state-delta.json", {"before_sha256": before["sha256"],
                                           "after_sha256": after["sha256"],
                                           "changed_paths": sorted(path for path in before_by.keys() | after_by.keys()
                                                                   if before_by.get(path) != after_by.get(path))})
        save(case_out, "exit.json", {"exit_code": exit_code, "controller_cancelled": bool(cancelled),
                                     "error": result.get("error"), "elapsed_ns": result.get("elapsed_ns"),
                                     "stdout_sha256": hashlib.sha256(raw_stdout).hexdigest(),
                                     "state_before_sha256": before["sha256"], "state_after_sha256": after["sha256"]})
        if exit_code != 0:
            raise RuntimeError("HELPER_NONZERO_EXIT")
        if result.get("chosen") or not result.get("error"):
            raise RuntimeError("UNEXPECTED_FOLDER_SELECTION_OR_EMPTY_ERROR")
        return {"case": label, "cancelled": bool(cancelled), "result": result,
                "ready": ready, "state_before_sha256": before["sha256"],
                "state_after_sha256": after["sha256"]}
    except BaseException as exc:
        if child is not None:
            try:
                with (case_out / "stdout.partial.raw").open("xb") as stream:
                    stream.write(raw_stdout)
            except BaseException:
                pass
            unresolved_hold(case_out, scope_hash, child, nonce, exc)
        raise


def main():
    if os.name != "nt" or len(sys.argv) != 2:
        raise SystemExit("usage: controller.py SEALED_RUN_SCOPE.json (Windows only)")
    path = Path(sys.argv[1]).resolve()
    scope_hash = digest(path)
    scope, state, out, a, c, workspace, initial_state = validate_scope(path)
    out.mkdir(parents=True, exist_ok=False)
    save(out, "environment-contract.json", {"A_keys": sorted(a), "C_keys": sorted(c),
                                             "C_added_keys": sorted(set(c) - set(a)),
                                             "A_sha256": env_digest(a), "C_sha256": env_digest(c),
                                             "same_hint": str(workspace), "scope_sha256": scope_hash,
                                             "initial_state_sha256": initial_state["sha256"]})
    helper = ARTIFACT / "native-folder-environment.exe"
    first = run_case("C", helper, workspace, c, out, scope_hash, state, True, None)
    branch = choose_branch(first)
    save(out, "branch-decision.json", {"selected": branch, "C": first,
                                       "formal_increment": 0})
    second = run_case(branch, helper, workspace, a if branch == "A2" else c, out,
                      scope_hash, state, branch == "A2", first["ready"]["startup_flags"])
    save(out, "RESULT.json", {"status": "FINITE_FOLLOWUP_DIAGNOSTIC_COMPLETED", "cases": [first, second],
                              "branch": branch, "helper_calls": 2,
                              "formal_increment": 0, "at": datetime.datetime.now(datetime.timezone.utc).isoformat()})


if __name__ == "__main__":
    main()
