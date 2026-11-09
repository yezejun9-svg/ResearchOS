"""Hold verified Windows source files open against later path replacement.

Construction and import do not open files or load kernel32. Only acquire() does.
The caller must keep this object alive until its Job cleanup has completed.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import hmac
import ntpath
import re


_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x00000001
_OPEN_EXISTING = 3
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_LOCAL_DRIVE = re.compile(r"^[A-Za-z]:$")
_DOS_DEVICE = re.compile(
    r"^(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)",
    re.IGNORECASE,
)
_DEFAULT_PER_FILE_CAP = 128 * 1024 * 1024
_DEFAULT_TOTAL_CAP = 512 * 1024 * 1024


def _canonical(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise ValueError("reference path must be an absolute local drive path")
    regular = path.replace("/", "\\")
    drive, tail = ntpath.splitdrive(regular)
    # A local drive is exactly one ASCII letter and a colon. UNC, extended
    # namespace and device drives can otherwise masquerade as rooted tails.
    if (_LOCAL_DRIVE.fullmatch(drive) is None or not tail.startswith("\\")
            or tail.startswith("\\\\") or ":" in tail
            or any(ord(char) < 32 for char in regular)):
        raise ValueError("reference path must be an absolute local drive path")
    components = tail[1:].split("\\")
    if (not components[0] or any(
            not part or part in (".", "..") or part.endswith((" ", "."))
            or _DOS_DEVICE.match(part) is not None
            for part in components)):
        raise ValueError("reference path must have regular file components")
    return ntpath.normcase(ntpath.normpath(regular))


def _final_path(path: str) -> str:
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def _normalize_references(references, per_file_cap: int, total_cap: int):
    if not isinstance(references, (list, tuple)) or not references:
        raise ValueError("at least one exact source reference is required")
    unique = {}
    total = 0
    for ref in references:
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "bytes"}:
            raise ValueError("reference must contain exactly path, sha256 and bytes")
        path, digest, size = ref["path"], ref["sha256"], ref["bytes"]
        key = _canonical(path)
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise ValueError("reference requires a plain SHA-256 hex digest")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0 or size > per_file_cap:
            raise ValueError("reference size exceeds per-file cap")
        digest = digest.lower()
        if key in unique:
            if unique[key]["sha256"] != digest or unique[key]["bytes"] != size:
                raise ValueError("duplicate normalized path has conflicting pins")
            continue
        total += size
        if total > total_cap:
            raise ValueError("unique source bytes exceed total cap")
        unique[key] = {"path": path, "canonical_path": key, "sha256": digest, "bytes": size}
    return list(unique.values())


class _Win32API:
    """Default adapter, instantiated only inside acquire()."""

    def __init__(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._create = kernel.CreateFileW
        self._create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        self._create.restype = wintypes.HANDLE
        self._final = kernel.GetFinalPathNameByHandleW
        self._final.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
        self._final.restype = wintypes.DWORD
        self._size = kernel.GetFileSizeEx
        self._size.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_longlong)]
        self._size.restype = wintypes.BOOL
        self._read = kernel.ReadFile
        self._read.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                               ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        self._read.restype = wintypes.BOOL
        self._close = kernel.CloseHandle
        self._close.argtypes = [wintypes.HANDLE]
        self._close.restype = wintypes.BOOL

    @staticmethod
    def _error(stage: str):
        return OSError(ctypes.get_last_error(), stage)

    def open_read_shared_read(self, path: str):
        handle = self._create(path, _GENERIC_READ, _FILE_SHARE_READ, None,
                              _OPEN_EXISTING, _FILE_ATTRIBUTE_NORMAL, None)
        if handle in (None, _INVALID_HANDLE_VALUE):
            raise self._error("CreateFileW")
        return handle

    def final_path(self, handle) -> str:
        capacity = 4096
        while capacity <= 32768:
            target = ctypes.create_unicode_buffer(capacity)
            count = self._final(handle, target, capacity, 0)
            if count == 0:
                raise self._error("GetFinalPathNameByHandleW")
            if count < capacity:
                return target.value
            capacity = count + 1
        raise ValueError("final path exceeds Windows path bound")

    def size(self, handle) -> int:
        result = ctypes.c_longlong()
        if not self._size(handle, ctypes.byref(result)) or result.value < 0:
            raise self._error("GetFileSizeEx")
        return result.value

    def read_exact(self, handle, size: int) -> bytes:
        parts = []
        remaining = size
        while remaining:
            amount = min(remaining, 1024 * 1024)
            buffer = ctypes.create_string_buffer(amount)
            received = wintypes.DWORD()
            if not self._read(handle, buffer, amount, ctypes.byref(received), None):
                raise self._error("ReadFile")
            if received.value == 0:
                raise ValueError("file ended before pinned size")
            parts.append(buffer.raw[:received.value])
            remaining -= received.value
        return b"".join(parts)

    def close(self, handle) -> None:
        if not self._close(handle):
            raise self._error("CloseHandle")


class SourceReadGuard:
    """One-shot held-handle source verifier. Constructor has no OS effects."""

    def __init__(self, per_file_cap: int = _DEFAULT_PER_FILE_CAP,
                 total_cap: int = _DEFAULT_TOTAL_CAP, api_factory=None):
        if (isinstance(per_file_cap, bool) or isinstance(total_cap, bool)
                or not isinstance(per_file_cap, int) or not isinstance(total_cap, int)
                or per_file_cap <= 0 or total_cap < per_file_cap):
            raise ValueError("invalid source byte caps")
        self.per_file_cap = per_file_cap
        self.total_cap = total_cap
        self._api_factory = api_factory or _Win32API
        self._api = None
        self._attempted = False
        self._entries = []
        self.buffers = {}
        self._errors = []
        self._failure = None

    def acquire(self, references):
        """Open once, verify final target and bytes on held handles, return buffers."""
        if self._attempted:
            raise RuntimeError("source guard is one-shot")
        self._attempted = True
        stage = "preflight"
        try:
            prepared = _normalize_references(references, self.per_file_cap, self.total_cap)
            stage = "api_initialization"
            self._api = self._api_factory()
            for ref in prepared:
                entry = {**ref, "verified": False, "final_path_match": False,
                         "closed": True, "handle": None}
                self._entries.append(entry)
                stage = "CreateFileW"
                entry["handle"] = self._api.open_read_shared_read(ref["path"])
                entry["closed"] = False
                stage = "GetFinalPathNameByHandleW"
                actual = self._api.final_path(entry["handle"])
                if _canonical(_final_path(actual)) != ref["canonical_path"]:
                    raise ValueError("held handle resolves outside authorized target")
                entry["final_path_match"] = True
                stage = "GetFileSizeEx"
                actual_size = self._api.size(entry["handle"])
                if actual_size != ref["bytes"] or actual_size > self.per_file_cap:
                    raise ValueError("held file size differs from exact pin")
                stage = "ReadFile"
                raw = self._api.read_exact(entry["handle"], actual_size)
                if len(raw) != actual_size or self._api.size(entry["handle"]) != actual_size:
                    raise ValueError("held file size changed during read")
                stage = "SHA256"
                if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), ref["sha256"]):
                    raise ValueError("held file content differs from exact pin")
                entry["verified"] = True
                self.buffers[ref["canonical_path"]] = raw
            return self.buffers
        except Exception as exc:
            self._failure = {"stage": stage, "error_type": type(exc).__name__}
            if isinstance(exc, OSError) and isinstance(exc.errno, int):
                self._failure["winerror"] = exc.errno
            self.close()
            raise

    def get_buffer(self, path: str) -> bytes:
        """Fetch only the already verified buffer for an exact reference path."""
        return self.buffers[_canonical(path)]

    def close(self) -> dict:
        """Attempt every CloseHandle; retain failed handles for explicit retry/audit."""
        for entry in self._entries:
            if entry["handle"] is None or entry["closed"]:
                continue
            try:
                self._api.close(entry["handle"])
            except Exception as exc:
                error = {"stage": "CloseHandle", "path": entry["path"],
                         "error_type": type(exc).__name__}
                if isinstance(exc, OSError) and isinstance(exc.errno, int):
                    error["winerror"] = exc.errno
                self._errors.append(error)
            else:
                entry["closed"] = True
                entry["handle"] = None
        self.buffers.clear()
        retained = sum(1 for entry in self._entries if entry["handle"] is not None)
        return {
            "schema": "researchos.source-read-guard-observation.v1",
            "attempted": self._attempted,
            "verification": "FAILED" if self._failure else (
                "PASSED" if self._entries and all(e["verified"] for e in self._entries)
                else "NOT_RUN"),
            "share_mode": "FILE_SHARE_READ_ONLY",
            "entries": [{"path": e["path"], "sha256": e["sha256"], "bytes": e["bytes"],
                         "verified": e["verified"], "final_path_match": e["final_path_match"],
                         "closed": e["closed"]} for e in self._entries],
            "closed": retained == 0,
            "retained_handles_count": retained,
            "failure": self._failure,
            "errors": list(self._errors),
        }
