"""In-memory SourceReadGuard controls; no kernel32 or target files are opened."""

import ast
import hashlib
import json
from pathlib import Path

from source_read_guard import SourceReadGuard


class FakeAPI:
    def __init__(self, files, close_fails=()):
        self.files = files
        self.handles = {}
        self.opened = []
        self.closed = []
        self.close_fails = set(close_fails)

    def open_read_shared_read(self, path):
        handle = len(self.opened) + 1
        self.opened.append(path)
        self.handles[handle] = path
        return handle

    def final_path(self, handle):
        return "\\\\?\\" + self.handles[handle]

    def size(self, handle):
        return len(self.files[self.handles[handle]])

    def read_exact(self, handle, size):
        return self.files[self.handles[handle]][:size]

    def close(self, handle):
        if handle in self.close_fails:
            raise OSError(32, "CloseHandle")
        self.closed.append(handle)


def ref(path, data):
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def main():
    source = Path(__file__).with_name("source_read_guard.py")
    tree = ast.parse(source.read_text(encoding="utf-8"))
    class_methods = {node.name for node in tree.body if isinstance(node, ast.ClassDef)
                     and node.name == "SourceReadGuard"
                     for node in node.body if isinstance(node, ast.FunctionDef)}
    assert {"__init__", "acquire", "get_buffer", "close"} <= class_methods
    assert "_FILE_SHARE_READ = 0x00000001" in source.read_text(encoding="utf-8")

    first = r"D:\trial\source.py"
    second = r"D:\trial\worker.mjs"
    payload = {first: b"one source", second: b"second source"}
    fake = FakeAPI(payload)
    factory_calls = []
    guard = SourceReadGuard(api_factory=lambda: (factory_calls.append(True), fake)[1])
    assert not factory_calls and not fake.opened, "constructor touched native adapter"
    buffers = guard.acquire([ref(first, payload[first]), ref(first.lower(), payload[first]),
                             ref(second, payload[second])])
    assert len(fake.opened) == 2 and len(factory_calls) == 1
    assert buffers[guard_key(first)] == payload[first] and guard.get_buffer(second) == payload[second]
    result = guard.close()
    assert result["verification"] == "PASSED" and result["closed"] is True
    assert result["retained_handles_count"] == 0 and len(fake.closed) == 2 and not guard.buffers
    assert guard.close() == result, "idempotent close changed observation"

    mismatch = FakeAPI(payload)
    failed = SourceReadGuard(api_factory=lambda: mismatch)
    wrong = ref(second, b"wrong pin")
    try:
        failed.acquire([ref(first, payload[first]), wrong])
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched second pin was accepted")
    failure = failed.close()
    assert failure["verification"] == "FAILED" and failure["closed"] is True
    assert len(mismatch.closed) == 2 and failure["retained_handles_count"] == 0

    conflicting = SourceReadGuard(api_factory=lambda: FakeAPI(payload))
    bad = ref(first, payload[first]); bad["sha256"] = "0" * 64
    try:
        conflicting.acquire([ref(first, payload[first]), bad])
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting duplicate was accepted")
    assert conflicting.close()["entries"] == []

    retained_api = FakeAPI({first: payload[first]}, close_fails={1})
    retained = SourceReadGuard(api_factory=lambda: retained_api)
    retained.acquire([ref(first, payload[first])])
    held = retained.close()
    assert held["closed"] is False and held["retained_handles_count"] == 1
    assert held["errors"] and '"handle":' not in json.dumps(held).lower()
    retained_api.close_fails.clear()
    released = retained.close()
    assert released["closed"] is True and released["retained_handles_count"] == 0
    assert released["errors"], "prior close failure was erased"

    return {"schema": "researchos.source-read-guard-pure-controls.v1",
            "status": "PASS_IN_MEMORY_ONLY", "cases": [
                "constructor_no_native_action", "exact_held_buffer", "normpath_dedup",
                "mid_acquire_failure_closes_all", "conflicting_duplicate_preflight",
                "close_failure_retained_then_retry", "json_safe_observation"],
            "real_winapi_calls": 0, "target_file_reads": 0, "provider_requests": 0}


def guard_key(path):
    import ntpath
    return ntpath.normcase(ntpath.normpath(path))


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True))
