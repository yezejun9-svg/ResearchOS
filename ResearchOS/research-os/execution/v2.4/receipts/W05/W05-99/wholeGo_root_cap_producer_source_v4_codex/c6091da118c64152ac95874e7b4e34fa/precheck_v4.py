"""Pure fake-kernel source check. Extracts two AST functions; no candidate import."""
import ast
import ctypes
import json
from pathlib import Path
from types import SimpleNamespace
import sys

sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_v3_codex/baa0423d87784ee0bbf526de45a20a8c/wholego_cap_metadata.v3.proposed.py"
NEW = HERE / "wholego_cap_metadata.v4.proposed.py"
old_tree = ast.parse(OLD.read_text(encoding="utf-8"), filename=str(OLD))
new_tree = ast.parse(NEW.read_text(encoding="utf-8"), filename=str(NEW))
compile(new_tree, str(NEW), "exec", dont_inherit=True)
old_fns = {n.name: n for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_fns = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
assert set(old_fns) == set(new_fns)
assert all(ast.dump(old_fns[name], include_attributes=False) ==
           ast.dump(new_fns[name], include_attributes=False)
           for name in old_fns if name != "observed_windows_process")
assert "GetExitCodeProcess" in ast.dump(new_fns["observed_windows_process"])
assert "exited.low == 0 and exited.high == 0" in NEW.read_text(encoding="utf-8")

class Fn:
    def __init__(self, action):
        self.action = action
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.action(*args)

class Kernel:
    def __init__(self, *, exit_code=259, exit_time=0, times_ok=True,
                 exit_query_ok=True, member=True):
        self.exit_code = exit_code
        self.exit_time = exit_time
        self.times_ok = times_ok
        self.exit_query_ok = exit_query_ok
        self.member = member
        self.closed = []
        self.OpenProcess = Fn(lambda access, inherit, pid: 771)
        self.GetProcessTimes = Fn(self.times)
        self.IsProcessInJob = Fn(self.job)
        self.GetExitCodeProcess = Fn(self.exit_query)
        self.CloseHandle = Fn(self.close)

    def times(self, handle, created, exited, kernel_time, user_time):
        if not self.times_ok:
            return 0
        created_p = ctypes.cast(created, ctypes.POINTER(ctypes.c_uint32))
        exited_p = ctypes.cast(exited, ctypes.POINTER(ctypes.c_uint32))
        created_p[0], created_p[1] = 654, 321
        exited_p[0], exited_p[1] = self.exit_time, 0
        return 1

    def job(self, handle, expected, member_ptr):
        ctypes.cast(member_ptr, ctypes.POINTER(ctypes.c_int))[0] = int(self.member)
        return 1

    def exit_query(self, handle, exit_ptr):
        if not self.exit_query_ok:
            return 0
        ctypes.cast(exit_ptr, ctypes.POINTER(ctypes.c_uint32))[0] = self.exit_code
        return 1

    def close(self, handle):
        self.closed.append(handle.value)
        return 1

def run_case(kernel, expected):
    fake_ctypes = SimpleNamespace(
        WinDLL=lambda name, use_last_error: kernel,
        Structure=ctypes.Structure, c_uint32=ctypes.c_uint32, c_int=ctypes.c_int,
        c_void_p=ctypes.c_void_p, POINTER=ctypes.POINTER, byref=ctypes.byref)
    selected = [new_fns["require"], new_fns["observed_windows_process"]]
    mod = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    ns = {"ctypes": fake_ctypes, "os": SimpleNamespace(name="nt")}
    exec(compile(mod, str(NEW), "exec", dont_inherit=True), ns)
    try:
        actual = ns["observed_windows_process"](39468)
    except ValueError as exc:
        assert expected is None and str(exc) in {
            "ROOT_RUNNER_PROCESS_ALREADY_EXITED_OR_UNOBSERVED",
            "ROOT_RUNNER_PROCESS_NOT_IN_WINDOWS_JOB"}, str(exc)
    else:
        assert expected is not None and actual == expected, (expected, actual)
    assert kernel.closed == [771], kernel.closed

run_case(Kernel(), (321 << 32) | 654)
run_case(Kernel(exit_code=0, exit_time=42), None)
run_case(Kernel(exit_code=259, exit_time=42), None)
run_case(Kernel(exit_query_ok=False), None)
run_case(Kernel(times_ok=False), None)
result = {
    "schema": "researchos.whole-go-cap-v4-pure-precheck.v1",
    "source_ast_compile": True,
    "unchanged_functions_ast": len(old_fns) - 1,
    "candidate_imported": False,
    "actual_os_probe_count": 0,
    "go_cli_sdk_provider_executions": 0,
    "positive": "query-success + STILL_ACTIVE=259 + zero exit FILETIME + Job member",
    "negative": ["retained exited handle", "259 with nonzero exit FILETIME",
                 "GetExitCodeProcess failure", "GetProcessTimes failure"],
    "all_cases_close_handle": True,
    "scope": "SOURCE_ONLY"
}
with (HERE / "precheck.v4.json").open("xb") as out:
    out.write((json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
print(json.dumps(result, ensure_ascii=False))
