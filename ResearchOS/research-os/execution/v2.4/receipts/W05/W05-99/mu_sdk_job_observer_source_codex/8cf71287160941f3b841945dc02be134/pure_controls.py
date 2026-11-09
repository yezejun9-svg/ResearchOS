"""Pure source controls only; does not call the observer entry point or WinAPI."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
SOURCE = DIRECTORY / "mu_sdk_job_observer.proposed.py"


def main():
    raw = SOURCE.read_bytes()
    tree = ast.parse(raw)
    allowed = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign, ast.Expr)
    assert all(isinstance(node, allowed) for node in tree.body)
    for node in tree.body:
        if isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        elif isinstance(node, ast.Assign):
            ast.literal_eval(node.value)
    module = types.ModuleType("source_only_observer_controls")
    module.__file__ = str(SOURCE)
    exec(compile(raw, str(SOURCE), "exec"), module.__dict__)
    results = []
    def check(name, function, reject=False):
        try:
            function()
        except (ValueError, KeyError, TypeError) as error:
            if not reject:
                raise
            results.append({"name": name, "passed": True, "expected_rejection": str(error)})
        else:
            assert not reject, name + " accepted counterexample"
            results.append({"name": name, "passed": True})
    facts = {"process_id": 123, "thread_process_id": 123, "thread_id": 456,
             "creation_filetime": 1234567, "member_of_expected_job": True,
             "exit_code": 259, "wait_result": 258, "assigned_count": 1,
             "returned_count": 1, "active_pids": [123], "job_limit_flags": 0x2000}
    check("pure-observed-facts-positive-synthetic-no-receipt", lambda: module.validate_observed_facts(facts, 123, 1234567))
    mutations = {"process_id": 124, "thread_process_id": 124, "thread_id": 0,
                 "creation_filetime": 1234568, "member_of_expected_job": False,
                 "exit_code": 0, "wait_result": 0, "assigned_count": 2,
                 "returned_count": 0, "active_pids": [124], "job_limit_flags": 0}
    for key, value in mutations.items():
        check("reject-facts-" + key, lambda k=key, v=value: module.validate_observed_facts(dict(facts, **{k: v}), 123, 1234567), True)
    for flag in (0x800, 0x1000):
        check("reject-breakaway-" + str(flag), lambda f=flag: module.validate_observed_facts(dict(facts, job_limit_flags=0x2000 | f), 123, 1234567), True)
    check("reject-bool-pid", lambda: module.validate_observed_facts(facts, True, 1234567), True)
    doc = dict(module.LIMITS, qualification_requests=1, ordinary_requests=2)
    reg = {"limits": module.LIMITS, "started_monotonic": 100.0, "absolute_deadline_monotonic": 400.0}
    job = {"wall_seconds": 300, "absolute_deadline_monotonic": 400.0}
    check("pure-limits-positive", lambda: module.validate_limits(doc, reg, job, 101.0))
    for key in module.LIMITS:
        check("reject-limit-" + key, lambda k=key: module.validate_limits(dict(doc, **{k: doc[k] + 1}), reg, job, 101.0), True)
    check("reject-deadline-exhausted", lambda: module.validate_limits(doc, reg, job, 400.0), True)
    check("reject-nonfinite-clock", lambda: module.validate_limits(doc, reg, job, float("nan")), True)
    check("reject-start-in-future", lambda: module.validate_limits(doc, reg, job, 99.0), True)
    check("reject-job-deadline", lambda: module.validate_limits(doc, reg, dict(job, absolute_deadline_monotonic=401.0), 101.0), True)
    check("reject-request-partition", lambda: module.validate_limits(dict(doc, ordinary_requests=3), reg, job, 101.0), True)
    refs = {key: {"path": key, "sha256": "0" * 64, "bytes": 1}
            for key in ("controller_source", "observer_source", "hooks_source")}
    review = {"schema": "researchos.mu-sdk-controller-observer-independent-source-review.v1",
              "decision": "READY_SOURCE_ONLY", "actor_id": "codex:/root/command_queue",
              "controller_source_ref": refs["controller_source"], "observer_source_ref": refs["observer_source"],
              "hooks_source_ref": refs["hooks_source"], "runner_source_ref": module.RUNNER_REF,
              "callback_contract": "REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME", "formal_acceptance": False}
    check("pure-source-review-positive", lambda: module.validate_source_review(review, refs))
    for actor in (None, "", module.ROOT_ACTOR, module.AUTHOR, module.ACTOR):
        check("reject-reviewer-" + str(actor), lambda a=actor: module.validate_source_review(dict(review, actor_id=a), refs), True)
    for key in ("controller_source_ref", "observer_source_ref", "hooks_source_ref", "runner_source_ref"):
        check("reject-review-pin-" + key, lambda k=key: module.validate_source_review(dict(review, **{k: {}}), refs), True)
    check("reject-review-formal-acceptance", lambda: module.validate_source_review(dict(review, formal_acceptance=True), refs), True)
    check("reject-json-duplicate", lambda: module.strict_json(b'{"x":1,"x":2}'), True)
    check("reject-json-nan", lambda: module.strict_json(b'{"x":NaN}'), True)
    check("reject-json-array", lambda: module.strict_json(b'[]'), True)
    bootstrap = {"phase": "bootstrap", "runtime_profile": None, "public_route_manifest": None}
    check("bootstrap-explicit-null-public-refs", lambda: module.require(module.mode_public_pins(bootstrap) == (), "bootstrap refs"))
    check("reject-bootstrap-invented-profile", lambda: module.mode_public_pins(dict(bootstrap, runtime_profile={})), True)
    check("reject-bootstrap-missing-public-key", lambda: module.mode_public_pins({"phase": "bootstrap", "runtime_profile": None}), True)
    execute = {"phase": "execute", **{key: {"path": "synthetic", "sha256": "0"*64, "bytes": 0}
               for key in ("runtime_profile", "public_route_manifest", "cancel_fixture_receipt", "bootstrap_receipt")}}
    check("execute-requires-four-pins", lambda: module.require(len(module.mode_public_pins(execute)) == 4, "execute refs"))
    for key in ("runtime_profile", "public_route_manifest", "cancel_fixture_receipt", "bootstrap_receipt"):
        check("reject-execute-null-" + key, lambda k=key: module.mode_public_pins(dict(execute, **{k: None})), True)
    hooks_path = DIRECTORY.parents[1] / "mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed/owned_job_hooks.py"
    hooks_raw = hooks_path.read_bytes()
    hooks_ref = module.pin_of(hooks_path, hooks_raw)
    expected, call_line = module.expected_hook_code(hooks_ref)
    check("actual-pinned-hook-compile-no-execution", lambda: module.require(expected.co_name == "run_owned" and call_line > 0, "hook compile"))
    check("reject-callback-outside-real-owned-frame", lambda: module.observe_callback_frame({"hooks_source": hooks_ref}, 1, 2, 3, 123, 1234567, {"started": 100.0, "deadline": 400.0}), True)
    runner_raw = module.pin_bytes(module.RUNNER_REF)
    runner_ast = ast.parse(runner_raw)
    pure = types.ModuleType("two_pure_v8_projection_functions_only")
    pure.__file__ = module.RUNNER_REF["path"]
    pure.Path = Path
    pure.require = module.require
    pure.pin_path = lambda path: module.pin_of(path, runner_raw)
    public_environment = {"PATH": "C:/synthetic-tools", "SystemRoot": "C:/Windows"}
    pure.os = types.SimpleNamespace(environ=public_environment)
    for node in runner_ast.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("PHASE_BASIS_KEYS", "PROVIDER", "MODEL", "BASE", "CREDENTIAL_REF"):
                pure.__dict__[name] = ast.literal_eval(node.value)
    selected = [node for node in runner_ast.body if isinstance(node, ast.FunctionDef) and node.name in ("phase_basis", "cli_environment")]
    assert len(selected) == 2
    exec(compile(ast.Module(body=selected, type_ignores=[]), "<two-pure-projection-functions>", "exec"), pure.__dict__)
    sample = {key: None for key in pure.PHASE_BASIS_KEYS}
    sample.update(cli_binary={"path": "C:/synthetic/cli.exe"}, workspace="C:/synthetic/workspace",
                  goal_objective="synthetic goal", discovery_file="C:/synthetic/discovery.json",
                  cli_config_file="C:/synthetic/config.json", repository_root="C:/synthetic/repo",
                  config_revision=1, project_id="synthetic-project", prompt="synthetic evidence.txt", run_uuid="0"*32)
    for phase in ("bootstrap", "execute"):
        sample["phase"] = phase
        expected_basis = pure.phase_basis(sample, phase)
        check("projection-matches-v8-pure-functions-" + phase,
              lambda e=expected_basis: module.require(module.phase_projection(sample, runner_raw, public_environment) == e, "projection differs"))
        check("projection-detects-worker-environment-change-" + phase,
              lambda e=expected_basis: module.require(module.phase_projection(sample, runner_raw, dict(public_environment, PATH="changed")) == e, "environment differs"), True)
    report = {"schema": "researchos.mu-sdk-observer-pure-source-controls.v1", "scope": "PURE_FUNCTIONS_AND_COMPILE_ONLY",
              "source_ref": module.pin_of(SOURCE, raw), "hooks_ref": hooks_ref, "count": len(results),
              "failed": 0, "checks": results, "os_queries": 0, "target_processes_started": 0,
              "actual_observer_calls": 0, "provider_requests": 0, "runtime_receipts_issued": 0,
              "formal_acceptance": False}
    out = DIRECTORY / "pure-controls.v3.report.json"
    with out.open("xb") as handle:
        handle.write(module.json_bytes(report))
    print(json.dumps({"report": str(out), "count": len(results), "failed": 0}))


if __name__ == "__main__":
    main()
