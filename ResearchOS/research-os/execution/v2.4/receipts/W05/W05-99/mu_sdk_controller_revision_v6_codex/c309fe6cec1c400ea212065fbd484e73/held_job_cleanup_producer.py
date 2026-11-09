"""Hold the actual assigned Job and primary process for fresh cleanup checks.

Import is inert. Capture is called before the first ResumeThread while the
controller still holds the original Job/process handles. The parent must stay
alive; duplicated handles and this object do not survive process exit.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import time
import uuid


_DUPLICATE_SAME_ACCESS = 2
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258


class _Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in (
        "TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime",
        "ThisPeriodTotalKernelTime")] + [(name, wintypes.DWORD) for name in (
        "TotalPageFaultCount", "TotalProcesses", "ActiveProcesses",
        "TotalTerminatedProcesses")]


class _Win32:
    """Native adapter instantiated only by capture(), never on import."""
    def __init__(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        H, D, B = wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL

        def bind(name, args, returns):
            fn = getattr(kernel, name)
            fn.argtypes, fn.restype = args, returns
            return fn

        self._current = bind("GetCurrentProcess", [], H)
        self._duplicate = bind("DuplicateHandle",
            [H, H, H, ctypes.POINTER(H), D, B, D], B)
        self._close = bind("CloseHandle", [H], B)
        self._in_job = bind("IsProcessInJob", [H, H, ctypes.POINTER(B)], B)
        self._pid = bind("GetProcessId", [H], D)
        self._times = bind("GetProcessTimes",
            [H, ctypes.POINTER(wintypes.FILETIME),
             ctypes.POINTER(wintypes.FILETIME),
             ctypes.POINTER(wintypes.FILETIME),
             ctypes.POINTER(wintypes.FILETIME)], B)
        self._query_job = bind("QueryInformationJobObject",
            [H, ctypes.c_int, ctypes.c_void_p, D, ctypes.c_void_p], B)
        self._wait = bind("WaitForSingleObject", [H, D], D)
        self._exit = bind("GetExitCodeProcess", [H, ctypes.POINTER(D)], B)

    @staticmethod
    def _require(ok, stage):
        if not ok:
            raise OSError(ctypes.get_last_error(), stage)

    def duplicate(self, handle):
        target = wintypes.HANDLE()
        current = self._current()
        self._require(self._duplicate(current, handle, current,
            ctypes.byref(target), 0, False, _DUPLICATE_SAME_ACCESS),
            "DuplicateHandle")
        return int(target.value)

    def in_job(self, process, job):
        member = wintypes.BOOL()
        self._require(self._in_job(process, job, ctypes.byref(member)),
                      "IsProcessInJob")
        return bool(member.value)

    def process_id(self, process):
        pid = self._pid(process)
        self._require(pid != 0, "GetProcessId")
        return int(pid)

    def creation_time_100ns(self, process):
        creation, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        self._require(self._times(process, ctypes.byref(creation),
            ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)),
            "GetProcessTimes")
        return (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)

    def active_processes(self, job):
        info = _Accounting()
        self._require(self._query_job(job,
            _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION, ctypes.byref(info),
            ctypes.sizeof(info), None), "QueryInformationJobObject")
        return int(info.ActiveProcesses)

    def primary_exit(self, process):
        state = int(self._wait(process, 0))
        if state == _WAIT_TIMEOUT:
            return False, None
        self._require(state == _WAIT_OBJECT_0, "WaitForSingleObject")
        code = wintypes.DWORD()
        self._require(self._exit(process, ctypes.byref(code)),
                      "GetExitCodeProcess")
        # A signaled process handle proves exit, even if its exit code is 259.
        return True, int(code.value)

    def close(self, handle):
        self._require(self._close(handle), "CloseHandle")


class HeldJobCleanupProducer:
    """One run's immutable identity and duplicated live kernel handles."""
    def __init__(self, run_uuid: str, owner_pid: int, api_factory=None):
        if (type(run_uuid) is not str or not run_uuid or
                type(owner_pid) is not int or owner_pid <= 0 or
                owner_pid != os.getpid()):
            raise ValueError("run UUID and current parent PID required")
        self.run_uuid = run_uuid
        self.owner_pid = owner_pid
        self.job_binding_id = uuid.uuid4().hex
        self.runner_pid = None
        self.creation_time_100ns = None
        self.job_handle = None
        self.primary_handle = None
        self._api_factory = api_factory or _Win32
        self._api = None
        self._captured = False
        self._errors = []

    def capture_before_resume(self, actual: dict):
        if self._api is not None:
            raise RuntimeError("cleanup producer capture is one-shot")
        if (type(actual) is not dict or
                actual.get("assigned_before_resume") is not True or
                actual.get("kill_on_job_close_configured") is not True or
                actual.get("resumed") is not False or
                type(actual.get("runner_pid")) is not int or
                type(actual.get("creation_time_100ns")) is not int or
                actual["runner_pid"] <= 0 or actual["creation_time_100ns"] <= 0 or
                type(actual.get("job_handle")) is not int or
                type(actual.get("process_handle")) is not int or
                actual["job_handle"] <= 0 or actual["process_handle"] <= 0 or
                self.owner_pid != os.getpid()):
            raise ValueError("actual suspended assigned Job frame required")
        self._api = self._api_factory()
        # Keep each successful duplicate in this already parent-rooted object;
        # a later capture failure cannot make the first handle disappear.
        self.job_handle = self._api.duplicate(actual["job_handle"])
        self.primary_handle = self._api.duplicate(actual["process_handle"])
        pid = self._api.process_id(self.primary_handle)
        creation = self._api.creation_time_100ns(self.primary_handle)
        member = self._api.in_job(self.primary_handle, self.job_handle)
        if (pid != actual["runner_pid"] or
                creation != actual["creation_time_100ns"] or not member):
            raise RuntimeError("duplicated primary identity or Job membership differs")
        self.runner_pid = pid
        self.creation_time_100ns = creation
        self._captured = True
        return self.identity()

    def identity(self):
        return {"run_uuid": self.run_uuid, "owner_pid": self.owner_pid,
                "runner_pid": self.runner_pid,
                "creation_time_100ns": self.creation_time_100ns,
                "job_binding_id": self.job_binding_id,
                "captured_before_resume": self._captured,
                "held_job_handle": self.job_handle is not None,
                "held_primary_handle": self.primary_handle is not None}

    def observe_current(self):
        if (not self._captured or self.job_handle is None or
                self.primary_handle is None or self.owner_pid != os.getpid()):
            raise RuntimeError("actual held Job and primary identity unavailable")
        result = {"schema": "researchos.held-job-cleanup-observation.v1",
                  **self.identity(), "active_processes": None,
                  "primary_exit_confirmed": False, "primary_exit_code": None,
                  "pid_match": False, "creation_match": False, "errors": []}
        try:
            pid = self._api.process_id(self.primary_handle)
            creation = self._api.creation_time_100ns(self.primary_handle)
            result["pid_match"] = pid == self.runner_pid
            result["creation_match"] = creation == self.creation_time_100ns
            result["active_processes"] = self._api.active_processes(self.job_handle)
            signaled, exit_code = self._api.primary_exit(self.primary_handle)
            result["primary_exit_confirmed"] = signaled
            result["primary_exit_code"] = exit_code
        except BaseException as exc:
            result["errors"].append(type(exc).__name__ + ": " + str(exc))
        result["observed_monotonic"] = time.monotonic()
        return result

    def close(self):
        errors = []
        if self._api is not None:
            for name in ("primary_handle", "job_handle"):
                handle = getattr(self, name)
                if handle is None:
                    continue
                try:
                    self._api.close(handle)
                except BaseException as exc:
                    errors.append({"stage": "CloseHandle", "which": name,
                                   "error_type": type(exc).__name__})
                else:
                    setattr(self, name, None)
        self._errors.extend(errors)
        return {"schema": "researchos.held-job-cleanup-close.v1",
                "run_uuid": self.run_uuid, "owner_pid": self.owner_pid,
                "job_handle_closed": self.job_handle is None,
                "primary_handle_closed": self.primary_handle is None,
                "closed": self.job_handle is None and self.primary_handle is None,
                "errors": list(self._errors)}
