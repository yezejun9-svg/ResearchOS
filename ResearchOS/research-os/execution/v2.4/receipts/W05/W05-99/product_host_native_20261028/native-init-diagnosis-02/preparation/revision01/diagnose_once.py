"""Preparation only. Run only with a separately sealed Root scope.

One fresh Electron/Core pair, one Native3 workspace-choice frame, one normal
owned-window close. A failed identity or close check leaves this controller
alive with its child handles and receipts for Root reconciliation.
"""
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent.parent
OWNED_HANDLES = []  # Append immediately after Popen, before any receipt or stream I/O.

SCAN_SCRIPT = r'''
$ErrorActionPreference='Stop'
$names = @(ConvertFrom-Json -InputObject $env:ROS_SCAN_NAMES_JSON)
$known = @(ConvertFrom-Json -InputObject $env:ROS_SCAN_KNOWN_PIDS_JSON)
$rows = foreach ($item in @(Get-CimInstance Win32_Process)) {
  if ($names -notcontains [string]$item.Name -and $known -notcontains [int]$item.ProcessId) { continue }
  $createdNS = $null
  $readError = $null
  try {
    $native = Get-Process -Id $item.ProcessId -ErrorAction Stop
    $createdNS = [long](($native.StartTime.ToUniversalTime().Ticks - [long]621355968000000000) * [long]100)
  } catch { $readError = [string]$_.Exception.Message }
  [pscustomobject]@{ pid=[int]$item.ProcessId; image=[string]$item.ExecutablePath;
    created_ns=if($null -ne $createdNS){$createdNS.ToString()}else{$null};
    read_error=$readError }
}
ConvertTo-Json -InputObject @($rows) -Depth 4 -Compress
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def beneath(parent, child):
    parent, child = Path(parent).resolve(), Path(child).resolve()
    return child != parent and parent in child.parents


def save(out, name, value):
    path = out / name
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError("RECEIPT_ALREADY_EXISTS_DIFFERENT:" + str(path))


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


def normpath(value):
    return os.path.normcase(os.path.normpath(os.path.abspath(str(value)))).casefold()


def bundle_images(bundle, marker):
    images = set()
    for row in marker["files"]:
        if str(row["path"]).lower().endswith(".exe"):
            image = (bundle / row["path"]).resolve()
            if not beneath(bundle, image):
                raise RuntimeError("BUNDLE_IMAGE_OUTSIDE_ROOT")
            images.add(normpath(image))
    for role in ("electron", "control", "cli"):
        image = (bundle / marker["binaries"][role]["path"]).resolve()
        if normpath(image) not in images:
            raise RuntimeError("BUNDLE_BINARY_NOT_IN_INVENTORY:" + role)
    return sorted(images)


def known_identities(bundle, marker, saved_witness, witness_path):
    known = {}
    for entry in OWNED_HANDLES:
        process = entry["process"]
        known[process.pid] = {"pid": process.pid, "image": normpath(entry["image"]),
                              "created_ns": None, "role": entry["name"]}
    witness = saved_witness
    if witness is None and witness_path.exists():
        witness = read_json(witness_path)
    if witness is not None:
        if (witness["schema"] != "researchos.product-supervisor/1" or
                normpath(witness["install_root"]) != normpath(bundle) or
                witness["installation_id"] != marker["installation_id"]):
            raise RuntimeError("KNOWN_WITNESS_MISMATCH")
        desktop = next((entry["process"] for entry in OWNED_HANDLES if entry["name"] == "electron"), None)
        if desktop is None or witness["parent_process"]["PID"] != desktop.pid:
            raise RuntimeError("KNOWN_WITNESS_PARENT_MISMATCH")
        for role, binary in (("parent_process", "electron"), ("control_process", "control")):
            row = witness[role]
            pid = int(row["PID"])
            image = normpath(bundle / marker["binaries"][binary]["path"])
            if (pid <= 0 or row["ImageSHA256"] != marker["binaries"][binary]["sha256"] or
                    pid in known and known[pid]["image"] != image):
                raise RuntimeError("KNOWN_PID_IMAGE_CONFLICT")
            known[pid] = {"pid": pid, "image": image, "created_ns": str(row["CreatedNS"]),
                          "role": role}
    return sorted(known.values(), key=lambda row: row["pid"])


def scan_once(pwsh, bundle, images, known):
    env = {k: v for k, v in os.environ.items() if k.upper() in
           {"SYSTEMROOT", "WINDIR", "COMSPEC", "OS", "PATHEXT", "PATH"}}
    env["ROS_SCAN_NAMES_JSON"] = json.dumps(sorted({Path(image).name for image in images}))
    env["ROS_SCAN_KNOWN_PIDS_JSON"] = json.dumps([row["pid"] for row in known])
    try:
        result = subprocess.run([str(pwsh), "-NoProfile", "-NonInteractive", "-Command", SCAN_SCRIPT],
                                cwd=bundle, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="strict", timeout=20,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 0:
            raise RuntimeError("PROCESS_SCAN_FAILED:" + result.stderr[-1000:])
        rows = json.loads(result.stdout.lstrip("\ufeff"))
        if not isinstance(rows, list) or any(type(row.get("pid")) is not int or row["pid"] <= 0 for row in rows):
            raise RuntimeError("PROCESS_SCAN_BAD_ROWS")
        return {"status": "OBSERVED", "rows": rows}
    except BaseException as exc:
        return {"status": "UNKNOWN", "reason": str(exc)}


def scan_blockers(observation, images, known):
    if observation["status"] != "OBSERVED":
        return ["SCAN_UNKNOWN"]
    known_by_pid = {row["pid"]: row for row in known}
    result = []
    for row in observation["rows"]:
        pid = row["pid"]
        image = normpath(row["image"]) if row.get("image") else None
        expected = known_by_pid.get(pid)
        if expected:
            if image == expected["image"] and (expected["created_ns"] is None or
                                                 row.get("created_ns") == expected["created_ns"]):
                result.append("KNOWN_IDENTITY_STILL_PRESENT:" + str(pid))
            else:
                result.append("KNOWN_PID_REUSED_OR_UNKNOWN:" + str(pid))
        if not image or row.get("read_error"):
            result.append("CANDIDATE_IDENTITY_UNKNOWN:" + str(pid))
        elif image in images:
            result.append("EXACT_BUNDLE_IMAGE_STILL_RUNNING:" + str(pid))
    return sorted(set(result))


def validate_root_release(path, waiting):
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8-sig"))
    keys = {"schema", "actor", "scope_sha256", "controller_pid", "release_nonce",
            "known_identities", "root_confirmed_identity_absence", "confirmed_absent_at"}
    if set(value) != keys or value["schema"] != "researchos.native-chooser-root-release.v1":
        raise RuntimeError("ROOT_RELEASE_SHAPE_INVALID")
    for key in ("scope_sha256", "controller_pid", "release_nonce", "known_identities"):
        if value[key] != waiting[key]:
            raise RuntimeError("ROOT_RELEASE_BINDING_MISMATCH:" + key)
    if value["actor"] != "codex:/root" or value["root_confirmed_identity_absence"] is not True:
        raise RuntimeError("ROOT_RELEASE_AUTHORITY_MISMATCH")
    confirmed = datetime.datetime.fromisoformat(value["confirmed_absent_at"].replace("Z", "+00:00"))
    entered = datetime.datetime.fromisoformat(waiting["at"])
    if confirmed.tzinfo is None or confirmed < entered:
        raise RuntimeError("ROOT_RELEASE_PREMATURE")
    return sha(raw)


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


def hold(out, reason, bundle, marker, pwsh, scope_sha, saved_witness, witness_path):
    # Signal and receipt failures cannot discard Popen handles. Only Root's
    # unique post-WAITING release plus two clean independent scans may exit.
    for sig in (signal.SIGINT, getattr(signal, "SIGBREAK", None)):
        if sig is not None:
            try:
                signal.signal(sig, signal.SIG_IGN)
            except BaseException:
                pass
    try:
        known = known_identities(bundle, marker, saved_witness, witness_path)
        known_error = None
    except BaseException as exc:
        known, known_error = [], str(exc)
    try:
        images = bundle_images(bundle, marker)
        image_error = None
    except BaseException as exc:
        images, image_error = [], str(exc)
    release_path = out / "ROOT-RELEASE.json"
    waiting = {"schema": "researchos.native-chooser-waiting.v1", "status": "WAITING_FOR_ROOT",
               "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "scope_sha256": scope_sha, "controller_pid": os.getpid(),
               "release_nonce": secrets.token_hex(16), "release_path": str(release_path),
               "known_identities": known, "known_identity_error": known_error,
               "bundle_images": images, "bundle_image_error": image_error,
               "release_preexisted_wait": release_path.exists(),
               "reason": str(reason), "forced_termination": False, "automatic_retry": False}
    unresolved = {"status": "UNRESOLVED_CONTROLLER_HOLDING_OWNED_HANDLES",
                  "reason": str(reason), "owned_handles": [
                      {"name": item["name"], "pid": item["process"].pid,
                       "image": item["image"]} for item in OWNED_HANDLES],
                  "witness_path": str(witness_path), "witness": saved_witness,
                  "forced_termination": False, "automatic_retry": False}
    safe_record(out, "UNRESOLVED.json", unresolved)
    waiting_written = safe_record(out, "WAITING_FOR_ROOT.json", waiting)
    try:
        print(json.dumps({"status": "WAITING_FOR_ROOT", "controller_pid": os.getpid(),
                          "release_path": str(release_path)}, ensure_ascii=False), flush=True)
    except BaseException:
        pass
    prior_release_sha = None
    clean_scans = 0
    while True:
        try:
            if not waiting_written:
                waiting_written = safe_record(out, "WAITING_FOR_ROOT.json", waiting)
            if (waiting_written and not waiting["release_preexisted_wait"] and
                    known_error is None and image_error is None and release_path.exists()):
                release_sha = validate_root_release(release_path, waiting)
                observation = scan_once(pwsh, bundle, images, known)
                blockers = scan_blockers(observation, images, known)
                observation.update({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                    "phase": "root_release", "blockers": blockers,
                                    "release_sha256": release_sha})
                if not safe_append(out / "release-scans.jsonl", observation):
                    clean_scans = 0
                elif blockers:
                    clean_scans = 0
                else:
                    clean_scans = clean_scans + 1 if release_sha == prior_release_sha else 1
                prior_release_sha = release_sha
                if clean_scans >= 2:
                    released = {"status": "ROOT_RELEASED_AFTER_TWO_ABSENCE_SCANS",
                                "release_sha256": release_sha, "scope_sha256": scope_sha,
                                "controller_pid": os.getpid(), "known_identities": known,
                                "product_clean_close": False, "formal_increment": 0}
                    if safe_record(out, "ROOT-RELEASED.json", released):
                        return 1
            else:
                clean_scans = 0
            time.sleep(2)
        except BaseException as exc:
            clean_scans = 0
            safe_append(out / "hold-errors.jsonl", {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                                     "error": str(exc)})
            try:
                time.sleep(2)
            except BaseException:
                pass


def wait_terminal(child, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if child.poll() is not None:
            return child.returncode
        time.sleep(0.1)
    return None


def launch(exe, args, cwd, env, out, name):
    image = str(Path(exe).resolve())
    argv = [image, *map(str, args)]
    stdout = open(out / f"{name}.stdout.raw", "xb")
    stderr = open(out / f"{name}.stderr.raw", "xb")
    try:
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0  # SW_HIDE, same launch posture as driver-v2.
        child = subprocess.Popen(argv, cwd=cwd, env=env,
                                 stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                 startupinfo=startup, shell=False)
        OWNED_HANDLES.append({"name": name, "process": child, "image": image})
    finally:
        stdout.close()
        stderr.close()
    save(out, f"{name}.spawn.json", {"pid": child.pid, "executable": image, "args": argv[1:]})
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
    assert not beneath(HERE.parent, out)
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
    scope_sha = sha(Path(sys.argv[1]).read_bytes())
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
        desktop_exit = desktop.poll()
        witness_retired = not witness_path.exists()
        if desktop_exit != 0 or not witness_retired:
            save(out, "PAIR_ABSENT_CLOSE_UNPROVEN.json", {"status": "PAIR_ABSENT_CLOSE_UNPROVEN",
                                                         "electron_exit": desktop_exit,
                                                         "witness_retired": witness_retired,
                                                         "core_absent": True, "electron_absent": True})
            raise RuntimeError("PAIR_ABSENT_BUT_CLEAN_CLOSE_UNPROVEN")
        save(out, "RESULT.json", {"status": "OWNED_PAIR_CLEAN_CLOSE_CONFIRMED", "request_count_maximum": 1,
                                  "client_exit": client_exit, "folder_exit": folder_exit,
                                  "close_exit": close_exit, "electron_exit": desktop_exit,
                                  "witness_retired": witness_retired,
                                  "electron_pid": desktop.pid, "core_pid": core_pid,
                                  "electron_absent": True, "core_absent": True,
                                  "raw_reply": str(out / "native-reply.raw"), "formal_increment": 0})
    except BaseException as exc:
        # Do not lose the owned handles if the exact close sequence cannot be proved.
        while True:
            try:
                return hold(out, exc, bundle, marker, pwsh, scope_sha, witness, witness_path)
            except BaseException as hold_error:
                exc = hold_error
                try:
                    time.sleep(2)
                except BaseException:
                    pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
