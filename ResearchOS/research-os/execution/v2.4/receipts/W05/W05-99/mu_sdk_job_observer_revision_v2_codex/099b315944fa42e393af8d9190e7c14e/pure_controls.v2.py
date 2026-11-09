"""Synthetic code/frame and byte-buffer controls only; no target or WinAPI."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "mu_sdk_job_observer.v2.proposed.py"


def main():
    raw = SOURCE.read_bytes()
    tree = ast.parse(raw)
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            env[node.targets[0].id] = ast.literal_eval(node.value)
    selected = ("require", "pin_bytes", "json_bytes", "validate_public_environment", "phase_projection",
                "validate_source_review", "validate_launch_inputs", "validate_callback_launch",
                "code_identity", "observe_callback_frame")
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in selected]
    assert len(definitions) == len(selected)
    env.update(ast=ast, hashlib=hashlib, json=json, math=math, Path=Path, types=types)
    exec(compile(ast.Module(body=definitions, type_ignores=[]), "<observer-v2-selected-pure-AST>", "exec"), env)
    def pin(path, content):
        return {"path": str(Path(path)), "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    worker_path = str(Path("C:/source-only/phase_worker.py"))
    python_path = str(Path("C:/source-only/python.exe"))
    worker_raw, python_raw = b"value = 1\n", b"MZ-synthetic-only-not-executed"
    worker_ref, python_ref = pin(worker_path, worker_raw), pin(python_path, python_raw)
    buffers = {worker_path: worker_raw, python_path: python_raw}
    reads = {}
    class CheckedSyntheticFile:
        def __init__(self, path):
            self.path = path
        def read_bytes(self):
            reads[self.path] = reads.get(self.path, 0) + 1
            return buffers[self.path]
    env["checked_path"] = lambda path: CheckedSyntheticFile(path)
    env["os"] = types.SimpleNamespace(path=types.SimpleNamespace(lexists=lambda path: False))
    public_env = {"SystemRoot": "C:/Windows", "WINDIR": "C:/Windows", "PATH": "C:/source-only"}
    doc = {"discovery_file": "C:/isolated/discovery.json", "cli_config_file": "C:/isolated/config.json"}
    basis = {"child_environment": dict(public_env, RESEARCHOS_CLI_DISCOVERY=doc["discovery_file"],
                                        RESEARCHOS_CLI_CONFIG=doc["cli_config_file"])}
    context = {"phase_worker_source": worker_ref, "python_binary": python_ref,
               "phase_dir": str(Path("C:/source-only/phase")), "input_doc": doc,
               "public_environment": dict(public_env)}
    results = []
    def case(name, function, reject=False):
        try:
            value = function()
        except (ValueError, KeyError, TypeError, SyntaxError) as error:
            assert reject, name + " unexpectedly rejected: " + str(error)
            results.append({"name": name, "passed": True, "rejected": True, "reason": str(error)})
            return None
        assert not reject, name + " unexpectedly accepted"
        results.append({"name": name, "passed": True, "rejected": False})
        return value
    launch = case("valid-pinned-Python-worker-and-complete-frozen-environment", lambda: env["validate_launch_inputs"](context, basis))
    case("worker-and-Python-read-once-same-checked-buffer", lambda: env["require"](reads == {worker_path: 1, python_path: 1}, "extra raw read"))
    for name, path in (("worker", worker_path), ("Python", python_path)):
        original = buffers[path]
        buffers[path] = original + b"changed"
        case("reject-" + name + "-bytes", lambda: env["validate_launch_inputs"](context, basis), True)
        buffers[path] = original
    for name, key in (("worker", "phase_worker_source"), ("Python", "python_binary")):
        bad = copy.deepcopy(context)
        bad[key]["sha256"] = "0" * 64
        case("reject-" + name + "-hash", lambda c=bad: env["validate_launch_inputs"](c, basis), True)
    for name, key in (("worker", "phase_worker_source"), ("Python", "python_binary")):
        bad = copy.deepcopy(context)
        bad[key]["bytes"] += 1
        case("reject-" + name + "-size", lambda c=bad: env["validate_launch_inputs"](c, basis), True)
    env["os"].path.lexists = lambda path: True
    case("reject-existing-phase-input", lambda: env["validate_launch_inputs"](context, basis), True)
    env["os"].path.lexists = lambda path: False
    bad_basis = copy.deepcopy(basis)
    bad_basis["child_environment"]["PATH"] = "C:/unbound"
    case("reject-basis-environment-drift", lambda: env["validate_launch_inputs"](context, bad_basis), True)
    bad_basis = copy.deepcopy(basis)
    bad_basis["child_environment"]["RESEARCHOS_CLI_CONFIG"] = "foreign-config"
    case("reject-basis-CLI-config-drift", lambda: env["validate_launch_inputs"](context, bad_basis), True)
    for extra in ("REVIEW_DUMMY_EXTRA", "ComSpec", "PATHEXT", "PYTHONPATH", "PYTHONHOME"):
        bad = copy.deepcopy(context)
        bad["public_environment"][extra] = "synthetic-public-value"
        case("reject-extra-environment-" + extra, lambda c=bad: env["validate_launch_inputs"](c, basis), True)
    case("reject-env-NUL", lambda: env["validate_public_environment"](dict(public_env, TEMP="a\x00b")), True)
    case("reject-env-case-alias", lambda: env["validate_public_environment"](dict(public_env, Path="extra")), True)
    # Rebuild only code objects from the actual frozen base; never execute it.
    base_ref = env["BASE_REF"]
    base_raw = Path(base_ref["path"]).read_bytes()
    assert len(base_raw) == base_ref["bytes"] and hashlib.sha256(base_raw).hexdigest() == base_ref["sha256"]
    text = base_raw.decode().replace(env["SIGNATURE"], env["SIGNATURE"][:-2] + ", before_resume=None):")
    text = text.replace(env["ASSIGNED"], env["ASSIGNED"] + env["HOOK"])
    filename = str(Path(base_ref["path"])) + "::root-before-resume"
    compiled = compile(text, filename, "exec", dont_inherit=True)
    expected = next(c for c in compiled.co_consts if isinstance(c, types.CodeType) and c.co_name == "run_owned")
    call_line = next(n.lineno for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "before_resume")
    loc = {"pi": types.SimpleNamespace(hProcess=7, hThread=8, dwProcessId=41), "job": 9,
           "result": {"creation_time_100ns": 123456, "resumed": False},
           "cleanup": {"assigned_before_resume": True, "kill_on_job_close_configured": True},
           "stage": "ASSIGN_SUSPENDED_CHILD", "assigned": True, "flags": 0x08080404,
           "started": 100.0, "timeout": 200.0, "env": dict(public_env),
           "argv": list(launch["argv"]), "cwd": launch["cwd"]}
    owner = types.SimpleNamespace(f_code=expected, f_lineno=call_line, f_locals=loc, f_back=None)
    frame = types.SimpleNamespace(f_back=owner)
    context["hooks_source"] = {"synthetic": "compiled-pinned-base-only"}
    state = {"started": 90.0, "deadline": 350.0, "launch": launch,
             "job": {"actual_owned_runner_deadline_monotonic": 300.0, "actual_creation_time_100ns": 123456}}
    env.update(inspect=types.SimpleNamespace(currentframe=lambda: frame),
               time=types.SimpleNamespace(monotonic=lambda: 200.0),
               expected_hook_code=lambda reference: (expected, call_line))
    observe_frame = lambda: env["observe_callback_frame"](context, 7, 8, 9, 41, 123456, state)
    case("FRAME_POSITIVE_EXACT_REVIEWED_LAUNCH", observe_frame)
    initial = copy.deepcopy(loc)
    loc["argv"] = ["C:/foreign/unreviewed.exe", "--unrelated"]
    case("FRAME_FOREIGN_ARGV_NOW_REJECTED", observe_frame, True)
    loc["argv"] = list(initial["argv"])
    loc["cwd"] = "C:/foreign/workspace"
    case("FRAME_FOREIGN_CWD_NOW_REJECTED", observe_frame, True)
    loc["cwd"] = initial["cwd"]
    context["public_environment"]["REVIEW_DUMMY_EXTRA"] = "public-only"
    loc["env"] = dict(context["public_environment"])
    case("FRAME_EXTRA_ENV_EVEN_WHEN_CONTEXT_MATCHES_NOW_REJECTED", observe_frame, True)
    context["public_environment"] = dict(public_env)
    loc["env"] = dict(public_env)
    for index, label, replacement in ((0, "Python", "C:/foreign/python.exe"),
                                      (1, "isolation-flag", "-E"),
                                      (4, "encoding", "ascii"),
                                      (5, "worker", "C:/foreign/worker.py"),
                                      (6, "input", "C:/foreign/input.execute.json")):
        loc["argv"][index] = replacement
        case("FRAME_REJECT_" + label, observe_frame, True)
        loc["argv"] = list(initial["argv"])
    loc["argv"].append("--extra")
    case("FRAME_REJECT_EXTRA_ARG", observe_frame, True)
    loc["argv"] = list(initial["argv"])
    loc["env"]["PATH"] = "C:/foreign"
    context["public_environment"] = dict(loc["env"])
    case("FRAME_ENV_CONTEXT_MATCHES_BUT_BASIS_DIFFERS_REJECTED", observe_frame, True)
    loc["env"] = dict(public_env)
    context["public_environment"] = dict(public_env)
    loc["result"]["resumed"] = True
    case("FRAME_ALREADY_RESUMED_STILL_REJECTED", observe_frame, True)
    loc["result"]["resumed"] = False
    loc["assigned"] = False
    case("FRAME_UNASSIGNED_STILL_REJECTED", observe_frame, True)
    loc["assigned"] = True
    owner.f_lineno += 1
    case("FRAME_WRONG_LINE_STILL_REJECTED", observe_frame, True)
    owner.f_lineno -= 1
    # The v2 review tuple cannot be upgraded by defaults or an old READY label.
    review_context = {name: {"path": name, "sha256": "0" * 64, "bytes": 1}
                      for name in ("controller_source", "observer_source", "hooks_source", "phase_worker_source", "python_binary")}
    review = {"schema": "researchos.mu-sdk-controller-observer-independent-source-review.v2",
              "decision": "READY_SOURCE_ONLY", "actor_id": "codex:/root/command_queue_impl",
              "controller_source_ref": review_context["controller_source"],
              "observer_source_ref": review_context["observer_source"], "hooks_source_ref": review_context["hooks_source"],
              "runner_source_ref": env["RUNNER_REF"], "phase_worker_source_ref": review_context["phase_worker_source"],
              "python_binary_ref": review_context["python_binary"],
              "callback_contract": "REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME", "formal_acceptance": False}
    case("REVIEW_V2_COMPLETE_POSITIVE", lambda: env["validate_source_review"](review, review_context))
    old = {k: v for k, v in review.items() if k not in ("phase_worker_source_ref", "python_binary_ref")}
    old["schema"] = "researchos.mu-sdk-controller-observer-independent-source-review.v1"
    case("REVIEW_OLD_FOUR_SOURCE_READY_REJECTED", lambda: env["validate_source_review"](old, review_context), True)
    for key in ("phase_worker_source_ref", "python_binary_ref"):
        missing = {k: v for k, v in review.items() if k != key}
        case("REVIEW_MISSING_" + key, lambda r=missing: env["validate_source_review"](r, review_context), True)
        wrong = dict(review, **{key: {}})
        case("REVIEW_CHANGED_" + key, lambda r=wrong: env["validate_source_review"](r, review_context), True)
    for actor in (env["ROOT_ACTOR"], env["AUTHOR"], env["ACTOR"]):
        case("REVIEW_REJECT_SELF_" + actor, lambda a=actor: env["validate_source_review"](dict(review, actor_id=a), review_context), True)
    case("REVIEW_REQUEST_CHANGES_REJECTED", lambda: env["validate_source_review"](dict(review, decision="REQUEST_CHANGES"), review_context), True)
    # Both phase basis projections retain all v8 fields, now rejecting omitted extras.
    runner_raw = Path(env["RUNNER_REF"]["path"]).read_bytes()
    assert hashlib.sha256(runner_raw).hexdigest() == env["RUNNER_REF"]["sha256"]
    runner_tree = ast.parse(runner_raw)
    basis_keys = next(ast.literal_eval(n.value) for n in runner_tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PHASE_BASIS_KEYS" for t in n.targets))
    sample = {key: None for key in basis_keys}
    sample.update(doc, cli_binary={"path": "C:/synthetic/cli.exe"}, workspace="C:/synthetic/workspace",
                  goal_objective="synthetic goal", repository_root="D:/作品集/ResearchOS/research-os",
                  config_revision=1, project_id="synthetic-project", prompt="synthetic evidence.txt", run_uuid="0" * 32)
    for phase in ("bootstrap", "execute"):
        sample["phase"] = phase
        case("BASIS_VALID_" + phase, lambda: env["phase_projection"](sample, runner_raw, public_env))
        case("BASIS_EXTRA_ENV_REJECTED_" + phase,
             lambda: env["phase_projection"](sample, runner_raw, dict(public_env, REVIEW_DUMMY_EXTRA="public")), True)
    report = {"schema": "researchos.mu-sdk-observer-v2-pure-controls.v1", "source_ref": pin(SOURCE, raw),
              "count": len(results), "failed": 0, "checks": results,
              "scope": "Selected AST functions; synthetic frame/locals and byte buffers; pinned base compiled only",
              "real_live_frame_observed": False, "full_candidate_imports": 0, "native_processes": 0,
              "WinAPI_calls": 0, "observer_entrypoint_calls": 0, "provider_requests": 0,
              "candidate_runtime_receipts": 0, "formal_acceptance": False}
    output = HERE / "pure-controls.v2.report.json"
    with output.open("xb") as handle:
        handle.write((json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"count": len(results), "failed": 0, "report": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
