"""One-use Windows Job owner. No product build/GUI is authorized by this file."""
from __future__ import annotations
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PYTHON = Path(r"C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe")
PYTHON_SHA = "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
CREATE_FLAGS = 0x00000004 | 0x08000000 | 0x00080000 | 0x00000400
WAIT_TIMEOUT = 258
STOP_EVENT_KEY = "OWNED_VERIFICATION_STOP_EVENT"

class SA(C.Structure):
    _fields_ = [("nLength", W.DWORD), ("lpSecurityDescriptor", W.LPVOID), ("bInheritHandle", W.BOOL)]
class SI(C.Structure):
    _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR), ("lpTitle", W.LPWSTR),
                ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
                ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                ("lpReserved2", C.POINTER(C.c_ubyte)), ("hStdInput", W.HANDLE), ("hStdOutput", W.HANDLE), ("hStdError", W.HANDLE)]
class SIX(C.Structure):
    _fields_ = [("StartupInfo", SI), ("lpAttributeList", W.LPVOID)]
class PI(C.Structure):
    _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]
class BASIC_LIMIT(C.Structure):
    _fields_ = [("PerProcessUserTimeLimit", C.c_longlong), ("PerJobUserTimeLimit", C.c_longlong),
                ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", C.c_size_t), ("MaximumWorkingSetSize", C.c_size_t),
                ("ActiveProcessLimit", W.DWORD), ("Affinity", C.c_size_t), ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]
class IO_COUNTERS(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
class EXT_LIMIT(C.Structure):
    _fields_ = [("BasicLimitInformation", BASIC_LIMIT), ("IoInfo", IO_COUNTERS), ("ProcessMemoryLimit", C.c_size_t),
                ("JobMemoryLimit", C.c_size_t), ("PeakProcessMemoryUsed", C.c_size_t), ("PeakJobMemoryUsed", C.c_size_t)]
class ACCOUNT(C.Structure):
    _fields_ = [(name, C.c_longlong) for name in ("TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime", "ThisPeriodTotalKernelTime")] + [
                (name, W.DWORD) for name in ("TotalPageFaultCount", "TotalProcesses", "ActiveProcesses", "TotalTerminatedProcesses")]

class Kernel:
    def __init__(self):
        self.dll = C.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([W.LPVOID, W.LPCWSTR], W.HANDLE),
            "SetInformationJobObject": ([W.HANDLE, C.c_int, W.LPVOID, W.DWORD], W.BOOL),
            "QueryInformationJobObject": ([W.HANDLE, C.c_int, W.LPVOID, W.DWORD, W.LPVOID], W.BOOL),
            "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
            "IsProcessInJob": ([W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)], W.BOOL),
            "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
            "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
            "ResumeThread": ([W.HANDLE], W.DWORD),
            "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
            "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
            "GetProcessTimes": ([W.HANDLE] + [C.POINTER(W.FILETIME)] * 4, W.BOOL),
            "CloseHandle": ([W.HANDLE], W.BOOL),
            "SetHandleInformation": ([W.HANDLE, W.DWORD, W.DWORD], W.BOOL),
            "GetFileSizeEx": ([W.HANDLE, C.POINTER(C.c_longlong)], W.BOOL),
            "CreateEventW": ([C.POINTER(SA), W.BOOL, W.BOOL, W.LPCWSTR], W.HANDLE),
            "SetEvent": ([W.HANDLE], W.BOOL),
            "InitializeProcThreadAttributeList": ([W.LPVOID, W.DWORD, W.DWORD, C.POINTER(C.c_size_t)], W.BOOL),
            "UpdateProcThreadAttribute": ([W.LPVOID, W.DWORD, C.c_size_t, W.LPVOID, C.c_size_t, W.LPVOID, W.LPVOID], W.BOOL),
            "DeleteProcThreadAttributeList": ([W.LPVOID], None),
            "CreateProcessW": ([W.LPCWSTR, W.LPWSTR, W.LPVOID, W.LPVOID, W.BOOL, W.DWORD, W.LPVOID, W.LPCWSTR, C.POINTER(SI), C.POINTER(PI)], W.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.dll, name); function.argtypes = args; function.restype = result
    @staticmethod
    def check(ok):
        if not ok: raise C.WinError(C.get_last_error())
        return ok
    def job(self, processes, memory_mib):
        handle = self.check(self.dll.CreateJobObjectW(None, None))
        try:
            limits = EXT_LIMIT()
            limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x8 | 0x200  # KILL_ON_CLOSE, ACTIVE_PROCESS, JOB_MEMORY; no breakaway
            limits.BasicLimitInformation.ActiveProcessLimit = processes
            limits.JobMemoryLimit = memory_mib * 1024 * 1024
            self.check(self.dll.SetInformationJobObject(handle, 9, C.byref(limits), C.sizeof(limits)))
            return handle
        except BaseException:
            self.dll.CloseHandle(handle)
            raise
    def event(self):
        security = SA(C.sizeof(SA), None, True)
        return self.check(self.dll.CreateEventW(C.byref(security), True, False, None))
    def create(self, argv, cwd, env, inherited, pi):
        size = C.c_size_t()
        self.dll.InitializeProcThreadAttributeList(None, 1, 0, C.byref(size))
        if not size.value: raise C.WinError(C.get_last_error())
        attributes = C.create_string_buffer(size.value)
        self.check(self.dll.InitializeProcThreadAttributeList(attributes, 1, 0, C.byref(size)))
        try:
            handles = (W.HANDLE * len(inherited))(*inherited)
            for handle in inherited: self.check(self.dll.SetHandleInformation(handle, 1, 1))
            self.check(self.dll.UpdateProcThreadAttribute(attributes, 0, 0x20002, C.cast(handles, W.LPVOID), C.sizeof(handles), None, None))
            startup = SIX(); startup.StartupInfo.cb = C.sizeof(SIX); startup.StartupInfo.dwFlags = 0x100
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = inherited[:3]
            startup.lpAttributeList = C.cast(attributes, W.LPVOID)
            command = C.create_unicode_buffer(subprocess.list2cmdline(argv))
            environment = C.create_unicode_buffer("\0".join(key + "=" + value for key, value in sorted(env.items())) + "\0\0")
            self.check(self.dll.CreateProcessW(argv[0], command, None, None, True, CREATE_FLAGS, C.cast(environment, W.LPVOID), cwd, C.byref(startup.StartupInfo), C.byref(pi)))
        finally:
            self.dll.DeleteProcThreadAttributeList(attributes)
    def assign(self, job, process): self.check(self.dll.AssignProcessToJobObject(job, process))
    def member(self, job, process):
        result = W.BOOL(); self.check(self.dll.IsProcessInJob(process, job, C.byref(result))); return bool(result.value)
    def resume(self, thread):
        if self.dll.ResumeThread(thread) == 0xFFFFFFFF: raise C.WinError(C.get_last_error())
    def signaled(self, process):
        state = self.dll.WaitForSingleObject(process, 0)
        if state not in (0, WAIT_TIMEOUT): raise C.WinError(C.get_last_error())
        return state == 0
    def account(self, job):
        info = ACCOUNT(); self.check(self.dll.QueryInformationJobObject(job, 1, C.byref(info), C.sizeof(info), None))
        return int(info.TotalProcesses), int(info.ActiveProcesses)
    def creation(self, process):
        values = [W.FILETIME() for _ in range(4)]
        self.check(self.dll.GetProcessTimes(process, *(C.byref(value) for value in values)))
        return str((values[0].dwHighDateTime << 32) | values[0].dwLowDateTime)
    def exit_code(self, process):
        code = W.DWORD(); self.check(self.dll.GetExitCodeProcess(process, C.byref(code))); return int(code.value)
    def terminate_job(self, job): self.check(self.dll.TerminateJobObject(job, 125))
    def terminate_root(self, process): self.check(self.dll.TerminateProcess(process, 125))
    def signal(self, event): self.check(self.dll.SetEvent(event))
    def file_size(self, handle):
        value = C.c_longlong(); self.check(self.dll.GetFileSizeEx(handle, C.byref(value))); return value.value
    def close(self, handle): self.check(self.dll.CloseHandle(handle))

def error_kind(error):
    return {"type": type(error).__name__, "errno": getattr(error, "errno", None), "winerror": getattr(error, "winerror", None)}
def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""): value.update(part)
    return value.hexdigest()
def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError("duplicate scope key")
        result[key] = value
    return result
def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())

def child_env(plan, attempt, event=0):
    # No ambient env dictionary is copied. These are public fixed OS/tool paths.
    env = {"SystemRoot": r"C:\Windows", "WINDIR": r"C:\Windows", "OS": "Windows_NT",
           "ComSpec": r"C:\Windows\System32\cmd.exe", "PATH": r"C:\Windows\System32;C:\Windows;C:\Program Files\Git\cmd;C:\nvm4w\nodejs",
           "USERPROFILE": str(attempt / "profile"), "HOME": str(attempt / "profile"),
           "APPDATA": str(attempt / "profile/AppData/Roaming"), "LOCALAPPDATA": str(attempt / "profile/AppData/Local"),
           "TEMP": str(attempt / "tmp"), "TMP": str(attempt / "tmp"), "PYTHONDONTWRITEBYTECODE": "1"}
    allowed = {"GOENV", "GOTOOLCHAIN", "GOPROXY", "GOSUMDB", "GOMODCACHE", "GOROOT", "GOCACHE", "GOTMPDIR", "GOWORK", "CGO_ENABLED"}
    for key, value in plan.get("env", {}).items():
        if key not in allowed or not isinstance(value, str) or "\0" in value: raise ValueError("environment key/value refused")
        if key in {"GOENV", "GOPROXY", "GOSUMDB", "GOWORK"} and value != "off": raise ValueError("offline environment required")
        if key == "GOTOOLCHAIN" and value != "local": raise ValueError("local toolchain required")
        if key == "CGO_ENABLED" and value != "0": raise ValueError("CGO disabled required")
        env[key] = value
    if event: env[STOP_EVENT_KEY] = str(event)
    return env

def validate_plan(path, pin):
    if os.name != "nt" or Path(sys.executable).resolve() != PYTHON.resolve() or sha(PYTHON) != PYTHON_SHA: raise ValueError("fixed Windows Python required")
    if ROOT.resolve() != ROOT or (ROOT / "scopes").resolve() != ROOT / "scopes": raise ValueError("owned path alias refused")
    if not path.resolve().is_relative_to(ROOT / "scopes") or sha(path) != pin: raise ValueError("exact new scope required")
    raw = path.read_bytes()
    if len(raw) > 256 * 1024: raise ValueError("scope too large")
    plan = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    if plan["schema"] != "researchos.owned-windows-run/1" or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", plan["scope_id"]): raise ValueError("scope identity")
    if plan["controller_sha256"] != sha(Path(__file__)): raise ValueError("controller pin differs")
    if plan["purpose"] == "fixture":
        if plan["authorization"] != "C_OWNED_SHORT_FIXTURE" or Path(plan["executable"]).resolve() != PYTHON.resolve() or plan["timeout_seconds"] > 3: raise ValueError("fixture scope refused")
        helper = str(ROOT / "fixtures/child.py")
        if plan["argv"][:4] != ["-I", "-S", "-X", "utf8"] or len(plan["argv"]) < 6 or plan["argv"][4] != helper: raise ValueError("fixture command refused")
    elif plan["purpose"] not in ("build", "gui") or plan["authorization"] != "ROOT_REVIEWED_EXACT_COMMAND": raise ValueError("Root review required")
    for key, low, high in [("timeout_seconds", .05, 1800), ("grace_seconds", 0, 5), ("cleanup_seconds", .1, 10)]:
        if type(plan[key]) not in (int, float) or not low <= plan[key] <= high: raise ValueError("time budget")
    for key, low, high in [("process_limit", 1, 64), ("memory_mib", 64, 8192), ("max_raw_bytes", 1024, 1 << 30)]:
        if type(plan[key]) is not int or not low <= plan[key] <= high: raise ValueError("resource budget")
    if plan["graceful"] not in ("none", "event") or plan["graceful"] == "none" and plan["grace_seconds"] != 0: raise ValueError("grace mode")
    if not Path(plan["cwd"]).is_dir() or not Path(plan["cwd"]).is_absolute() or not Path(plan["executable"]).is_absolute(): raise ValueError("absolute command required")
    if not isinstance(plan["argv"], list) or any(not isinstance(v, str) or "\0" in v for v in plan["argv"]): raise ValueError("argv refused")
    if sha(Path(plan["executable"])) != plan["executable_sha256"]: raise ValueError("executable pin")
    if not plan["inputs"]: raise ValueError("reviewed input pins required")
    for item in plan["inputs"]:
        if not Path(item["path"]).is_absolute() or sha(Path(item["path"])) != item["sha256"]: raise ValueError("input pin")
    child_env(plan, ROOT / "runs" / plan["scope_id"])
    return plan

def run_owned(plan, attempt, raw_handles, kernel=None):
    k = kernel or Kernel(); pi = PI()  # Allocated before Create: survives any post-return interruption.
    job = event = 0
    r = {"status": "UNKNOWN", "errors": [], "job_assigned": False, "resumed": False, "timed_out": False,
         "raw_limit_exceeded": False, "terminate_job_attempts": 0, "terminate_original_root_attempts": 0,
         "job_total_processes": 0, "root_signaled": False, "job_active_zero": False, "close_order": [],
         "automatic_retry": False, "resource_ready": False, "formal_increment": 0}
    closed_ok = True
    def problem(phase, error): r["errors"].append({"phase": phase, **error_kind(error)})
    def observe():
        signaled = k.signaled(pi.hProcess)
        total, active = k.account(job)
        r["job_total_processes"] = max(r["job_total_processes"], total)
        r["root_signaled"], r["job_active_zero"] = signaled, active == 0
        return signaled and active == 0
    started = time.monotonic()
    try:
        job = k.job(plan["process_limit"], plan["memory_mib"])
        if plan["graceful"] == "event": event = k.event()
        env = child_env(plan, attempt, event)
        r["environment_keys_only"] = sorted(env)
        deadline = time.monotonic() + plan["timeout_seconds"]
        k.create([plan["executable"], *plan["argv"]], plan["cwd"], env, [*raw_handles, *([event] if event else [])], pi)
        r["root_pid"] = int(pi.dwProcessId)
        r["creation_filetime"] = k.creation(pi.hProcess)
        k.assign(job, pi.hProcess)
        if not k.member(job, pi.hProcess): raise RuntimeError("Job assignment unconfirmed")
        r["job_assigned"] = True
        if time.monotonic() >= deadline: r["timed_out"] = True
        else:
            k.resume(pi.hThread); r["resumed"] = True
        # No journal, hashing, file read or Python stream/pipeline join follows
        # Resume before this bounded original-handle observation loop.
        grace_deadline = None
        while True:
            r["timed_out"] |= time.monotonic() >= deadline
            if any(k.file_size(h) > plan["max_raw_bytes"] for h in raw_handles[1:]): r["raw_limit_exceeded"] = True
            if observe(): break
            if time.monotonic() >= deadline or r["raw_limit_exceeded"]:
                r["timed_out"] |= time.monotonic() >= deadline
                if event and grace_deadline is None:
                    k.signal(event); grace_deadline = time.monotonic() + plan["grace_seconds"]
                if grace_deadline is None or time.monotonic() >= grace_deadline: break
            time.sleep(.01)
    except BaseException as error:
        problem("create_assign_resume_or_monitor", error)
    finally:
        # This also covers Create success followed by KeyboardInterrupt before
        # any Python assignment/return marker, and uncertain Assign/Resume.
        if pi.hProcess and not (r["root_signaled"] and r["job_active_zero"]):
            cleanup_deadline = time.monotonic() + plan["cleanup_seconds"]
            if job:
                r["terminate_job_attempts"] += 1
                try: k.terminate_job(job)
                except BaseException as error: problem("terminate_job", error)
            if not r["job_assigned"]:
                r["terminate_original_root_attempts"] += 1
                try: k.terminate_root(pi.hProcess)
                except BaseException as error: problem("terminate_original_root", error)
            while True:
                try:
                    if job and observe(): break
                except BaseException as error:
                    problem("cleanup_observation", error)
                    break
                if time.monotonic() >= cleanup_deadline: break
                time.sleep(.01)
        if pi.hProcess:
            r["root_pid"] = int(pi.dwProcessId)
            r["original_process_handle"] = hex(pi.hProcess)
            r["original_thread_handle"] = hex(pi.hThread or 0)
            try:
                if "creation_filetime" not in r: r["creation_filetime"] = k.creation(pi.hProcess)
                if k.signaled(pi.hProcess): r["root_exit_code"] = k.exit_code(pi.hProcess)
            except BaseException as error: problem("exit_code", error)
        # Job fail-safe precedes every raw-file close, sync, hash and result write.
        for name, handle in [("job", job), ("event", event), ("thread", pi.hThread), ("process", pi.hProcess)]:
            if handle:
                r["close_order"].append(name)
                try: k.close(handle)
                except BaseException as error: closed_ok = False; problem("close_" + name, error)
        r["elapsed_seconds"] = time.monotonic() - started
    r["stop_proved"] = bool(pi.hProcess and r["root_signaled"] and r["job_active_zero"] and closed_ok)
    if not r["stop_proved"] or r["errors"]: r["status"] = "UNKNOWN_OR_LAUNCH_FAILED"
    elif r["raw_limit_exceeded"]: r["status"] = "OUTPUT_LIMIT_STOPPED"
    elif r["timed_out"]: r["status"] = "TIMED_OUT_STOPPED"
    elif r.get("root_exit_code") != 0: r["status"] = "CHILD_NONZERO_STOPPED"
    else: r["status"] = "COMPLETED_OWNED_JOB_STOPPED"
    return r

def execute(scope, pin, *, kernel=None):
    plan = validate_plan(scope, pin)
    (ROOT / "runs").mkdir(exist_ok=True)
    if (ROOT / "runs").resolve() != ROOT / "runs": raise ValueError("run parent alias refused")
    attempt = ROOT / "runs" / plan["scope_id"]
    attempt.mkdir()  # Exclusive one-use consumption. Never delete on failure.
    for directory in ["profile/AppData/Local", "profile/AppData/Roaming", "tmp"]: (attempt / directory).mkdir(parents=True)
    write_new(attempt / "CONSUMED.json", {"scope_sha256": pin, "scope_id": plan["scope_id"], "purpose": plan["purpose"],
        "status": "CONSUMED_LAUNCH_OUTCOME_UNKNOWN", "automatic_retry": False, "controller_sha256": sha(Path(__file__))})
    # Ordinary files, not PIPEs: a descendant cannot block owner cleanup by
    # holding an output pipe. Raw output is examined only after Job close.
    files = []
    try:
        files.append(open(os.devnull, "rb"))
        files.append((attempt / "stdout.raw").open("xb"))
        files.append((attempt / "stderr.raw").open("xb"))
        handles = [msvcrt.get_osfhandle(f.fileno()) for f in files]
        result = run_owned(plan, attempt, handles, kernel)
    finally:
        for stream in files: stream.close()
    result.update(scope_sha256=pin, scope_id=plan["scope_id"], purpose=plan["purpose"], input_drift=None)
    # An unconfirmed stop is never followed by reads/hashes of possibly live
    # writers. Keep raw files unsealed for readback, not a completion claim.
    if result["stop_proved"]:
        result["input_drift"] = any(sha(Path(item["path"])) != item["sha256"] for item in plan["inputs"])
        if result["input_drift"]: result["status"] = "UNKNOWN_INPUT_DRIFT"
        result["raw"] = [{"file": name, "bytes": (attempt / name).stat().st_size, "sha256": sha(attempt / name)} for name in ("stdout.raw", "stderr.raw")]
    else:
        result["raw"] = [{"file": name, "unsealed": True} for name in ("stdout.raw", "stderr.raw")]
    write_new(attempt / "RESULT.json", result)
    return result

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--scope", type=Path, required=True); parser.add_argument("--scope-sha256", required=True)
    args = parser.parse_args()
    try:
        result = execute(args.scope, args.scope_sha256)
        print(json.dumps({key: result[key] for key in ("scope_id", "status", "stop_proved", "resource_ready", "formal_increment")}))
        return 0 if result["status"] == "COMPLETED_OWNED_JOB_STOPPED" else 1
    except BaseException as error:
        print(json.dumps({"status": "UNKNOWN_OR_BLOCKED_READBACK_REQUIRED", "error": error_kind(error), "automatic_retry": False}))
        return 2
if __name__ == "__main__": raise SystemExit(main())
