"""Isolated AST and in-memory lifecycle controls; no controller import or native I/O."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(__file__).with_name("controller.py")
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
NAMES = {
    "require", "cleanup_confirmed", "ResidentSourceOwner",
    "get_resident_source_owner", "_require_source_owner",
    "_append_cleanup_error", "source_retention_status",
    "reconcile_retained_sources",
}


class FakeLock:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeGuard:
    def __init__(self, close_results=None):
        self._entries = [{"handle": 1, "closed": False}]
        self.close_calls = 0
        self.close_results = list(close_results or [])

    def close(self):
        self.close_calls += 1
        if self.close_results:
            result = self.close_results.pop(0)
        else:
            result = {"closed": True, "retained_handles_count": 0, "errors": []}
        if result["closed"]:
            self._entries[0]["closed"] = True
            self._entries[0]["handle"] = None
        return result


class FakeWatchdog:
    def __init__(self, result=None):
        self.observation = {"errors": []}
        self.stop_calls = 0
        self.result = result or {"duplicate_handle_closed": True, "errors": []}

    def stop_and_close(self):
        self.stop_calls += 1
        return self.result


def native_result(**overrides):
    cleanup = {
        "errors": [], "active_processes_last_observed": 0,
        "primary_exit_confirmed": True, "job_idle_confirmed": True,
        "handles_closed": True,
    }
    cleanup.update(overrides)
    return {"job_cleanup": cleanup}


def isolated_namespace():
    selected = [n for n in TREE.body if getattr(n, "name", None) in NAMES]
    assert len(selected) == len(NAMES)
    selected += [n for n in TREE.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "_RESIDENT_OWNER_ATTR"
                         for t in n.targets)]
    namespace = {
        "sys": SimpleNamespace(),
        "os": SimpleNamespace(getpid=lambda: 4567),
        "threading": SimpleNamespace(RLock=FakeLock),
        "time": SimpleNamespace(monotonic=lambda: 100.0),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])),
                 str(SOURCE), "exec"), namespace)
    return namespace


def finalization_prefix(namespace):
    """Execute the exact C5 finally nodes before heartbeat/receipt side effects."""
    launch = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_launch_reviewed_phase_with_guard")
    native_try = next(n for n in ast.walk(launch) if isinstance(n, ast.Try)
                      and n.finalbody and "run_owned_hooked" in ast.unparse(n.body))
    prefix = []
    for node in native_try.finalbody:
        if isinstance(node, ast.Expr) and ast.unparse(node) == "stop_heartbeat.set()":
            break
        prefix.append(node)
    assert len(prefix) >= 5 and "source_owner.retain" in ast.unparse(prefix)
    names = ("result", "watchdog", "source_guard", "source_owner", "doc",
             "error", "watchdog_observation", "source_guard_observation",
             "activated")
    assignments = [ast.Assign(
        targets=[ast.Name(id=name, ctx=ast.Store())],
        value=ast.Subscript(value=ast.Name(id="context", ctx=ast.Load()),
                            slice=ast.Constant(name), ctx=ast.Load())) for name in names]
    result = ast.Return(value=ast.Dict(
        keys=[ast.Constant(name) for name in
              ("error", "watchdog_observation", "source_guard_observation")],
        values=[ast.Name(id=name, ctx=ast.Load()) for name in
                ("error", "watchdog_observation", "source_guard_observation")]))
    function = ast.FunctionDef(
        name="exercise_final", args=ast.arguments(posonlyargs=[], args=[
            ast.arg(arg="context")], vararg=None, kwonlyargs=[], kw_defaults=[],
            kwarg=None, defaults=[]), body=assignments + prefix + [result],
        decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 str(SOURCE) + "::isolated-finally", "exec"), namespace)
    return namespace["exercise_final"]


def run():
    ns = isolated_namespace()
    owner = ns["get_resident_source_owner"]()
    assert owner is ns["get_resident_source_owner"]()
    exercise = finalization_prefix(ns)
    cases = []
    counter = 0

    for label, result in [
        ("native_result_missing", None),
        ("native_active_process", native_result(active_processes_last_observed=1)),
        ("native_job_not_idle", native_result(job_idle_confirmed=False)),
        ("native_handles_open", native_result(handles_closed=False)),
        ("native_primary_exit_unknown", native_result(primary_exit_confirmed=False)),
        ("native_cleanup_error", native_result(errors=["native failed"])),
        ("native_active_bool_false", native_result(active_processes_last_observed=False)),
    ]:
        counter += 1
        run_uuid = f"run-{counter}"
        guard, watchdog = FakeGuard(), FakeWatchdog()
        owner.reserve(run_uuid, guard)
        owner.invoked(run_uuid)
        owner.attach_watchdog(run_uuid, watchdog)
        observed = exercise({"result": result, "watchdog": watchdog,
            "source_guard": guard, "source_owner": owner,
            "doc": {"run_uuid": run_uuid}, "error": None,
            "watchdog_observation": None, "source_guard_observation": None,
            "activated": False})
        assert guard.close_calls == watchdog.stop_calls == 0, label
        assert observed["source_guard_observation"]["state"] == "RETAINED_UNCONFIRMED"
        assert ns["source_retention_status"](run_uuid, owner)["retained_handles_count"] == 1
        cases.append(label + "_retains_guard_and_job")

    counter += 1
    run_uuid = f"run-{counter}"
    guard, watchdog = FakeGuard(), FakeWatchdog()
    owner.reserve(run_uuid, guard)
    owner.invoked(run_uuid)
    owner.attach_watchdog(run_uuid, watchdog)
    observed = exercise({"result": native_result(), "watchdog": watchdog,
        "source_guard": guard, "source_owner": owner,
        "doc": {"run_uuid": run_uuid}, "error": None,
        "watchdog_observation": None, "source_guard_observation": None,
        "activated": False})
    assert guard.close_calls == watchdog.stop_calls == 1
    assert observed["source_guard_observation"]["closed"] is True
    assert owner.record(run_uuid) is None
    cases.append("strict_native_cleanup_releases_guard_and_watchdog")

    counter += 1
    run_uuid = f"run-{counter}"
    guard = FakeGuard()
    watchdog = FakeWatchdog({"duplicate_handle_closed": False, "errors": ["close failed"]})
    owner.reserve(run_uuid, guard)
    owner.invoked(run_uuid)
    owner.attach_watchdog(run_uuid, watchdog)
    exercise({"result": native_result(), "watchdog": watchdog,
        "source_guard": guard, "source_owner": owner,
        "doc": {"run_uuid": run_uuid}, "error": None,
        "watchdog_observation": None, "source_guard_observation": None,
        "activated": False})
    assert watchdog.stop_calls == 1 and guard.close_calls == 0
    assert owner.record(run_uuid)["state"] == "RETAINED_UNCONFIRMED"
    cases.append("watchdog_duplicate_close_failure_retains_guard")

    counter += 1
    run_uuid = f"run-{counter}"
    events = []
    class OrderedGuard(FakeGuard):
        def close(self):
            events.append("guard_close")
            return super().close()
    guard = OrderedGuard()
    owner.reserve(run_uuid, guard)
    owner.invoked(run_uuid)
    ns["CANONICAL_TRANSACTION_REF"] = {"path": "memory-only"}
    ns["module"] = lambda ref, name: (events.append("transaction_source_load"), object())[1]
    exercise({"result": native_result(), "watchdog": None,
        "source_guard": guard, "source_owner": owner,
        "doc": {"run_uuid": run_uuid}, "error": None,
        "watchdog_observation": None, "source_guard_observation": None,
        "activated": True})
    assert events == ["transaction_source_load", "guard_close"]
    assert owner.record(run_uuid) is None
    cases.append("canonical_transaction_source_loaded_before_guard_close")

    counter += 1
    run_uuid = f"run-{counter}"
    guard = FakeGuard()
    owner.reserve(run_uuid, guard)
    exercise({"result": None, "watchdog": None, "source_guard": guard,
        "source_owner": owner, "doc": {"run_uuid": run_uuid}, "error": "precheck",
        "watchdog_observation": None, "source_guard_observation": None,
        "activated": False})
    assert guard.close_calls == 1 and owner.record(run_uuid) is None
    cases.append("pre_native_failure_may_close")

    retained = "run-1"
    guard, watchdog = owner.record(retained)["guard"], owner.record(retained)["watchdog"]
    def proof(run_uuid, owner_pid, watchdog):
        return {"run_uuid": run_uuid, "owner_pid": owner_pid,
                "observed_monotonic": 101.0, "native_result": native_result()}
    for label, args in [
        ("wrong_owner_pid", (retained, 9999, owner, proof)),
        ("wrong_run_uuid", ("unknown", 4567, owner, proof)),
        ("wrong_probe_run_uuid", (retained, 4567, owner, lambda **kw: {
            "run_uuid": "another", "owner_pid": 4567, "observed_monotonic": 101.0,
            "native_result": native_result()})),
        ("missing_live_probe", (retained, 4567, owner, None)),
        ("stale_job_cleanup", (retained, 4567, owner, lambda **kw: {
            "run_uuid": retained, "owner_pid": 4567, "observed_monotonic": 99.0,
            "native_result": native_result()})),
        ("active_job_cleanup", (retained, 4567, owner, lambda **kw: {
            "run_uuid": retained, "owner_pid": 4567, "observed_monotonic": 101.0,
            "native_result": native_result(active_processes_last_observed=1)})),
    ]:
        try:
            ns["reconcile_retained_sources"](*args)
        except RuntimeError:
            pass
        else:
            raise AssertionError(label + " released without current proof")
        assert guard.close_calls == watchdog.stop_calls == 0
        cases.append(label + "_reconcile_denied")

    reconciled = ns["reconcile_retained_sources"](retained, 4567, owner, proof)
    assert reconciled["state"] == "RELEASED_AFTER_CONFIRMED_CLEANUP"
    assert guard.close_calls == watchdog.stop_calls == 1 and owner.record(retained) is None
    cases.append("fresh_matching_strict_cleanup_reconciles")

    pre_native_guard = FakeGuard(close_results=[
        {"closed": False, "retained_handles_count": 1, "errors": ["close failed"]},
        {"closed": True, "retained_handles_count": 0, "errors": ["old close failed"]}])
    owner.reserve("pre-native-retained", pre_native_guard)
    assert pre_native_guard.close()["closed"] is False
    owner.retain("pre-native-retained", "pre-native close failed")
    recovered = ns["reconcile_retained_sources"]("pre-native-retained", 4567, owner)
    assert recovered["state"] == "RELEASED_AFTER_CONFIRMED_CLEANUP"
    cases.append("pre_native_close_retry_requires_no_job_proof")

    # No selected code creates a thread or accesses native APIs or files.
    outer = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                 and n.name == "launch_reviewed_phase").body[-1]
    assert isinstance(outer, ast.Try)
    assert all("guard.close()" not in ast.unparse(n) for n in outer.finalbody
               if not isinstance(n, ast.If))
    assert isinstance(outer.finalbody[-1], ast.If)
    assert "record['state'] == 'PRE_NATIVE'" in ast.unparse(outer.finalbody[-1].test)
    assert "guard.close()" in ast.unparse(outer.finalbody[-1].body)
    cases.append("outer_finally_has_no_unconditional_guard_close")
    return {"schema": "researchos.mu-sdk-controller-c5-pure-controls.v1",
            "status": "PASS_IN_MEMORY_ONLY", "cases": cases,
            "real_winapi_calls": 0, "native_jobs": 0, "threads_started": 0,
            "provider_requests": 0, "sql_writes": 0, "main_or_canonical_writes": 0}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
