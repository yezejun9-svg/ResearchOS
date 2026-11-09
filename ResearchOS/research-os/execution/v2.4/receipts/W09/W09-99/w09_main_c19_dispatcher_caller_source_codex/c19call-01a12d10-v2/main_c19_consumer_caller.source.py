"""Future Root-owned C19 two-consumer caller. Source only until CP370 grant.

The caller accepts a separately registered Root request, never this receipt as
authority. It creates no process when imported. Its only executable routes are
the two frozen C19 construction commands below.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
SOURCE_DIR = Path(__file__).resolve().parent
PYTHON = Path(r"C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe")
HELPER = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
GUARD = ROOT / "execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
INTERFACE = ROOT / "execution/v2.4/receipts/W09/W09-99/main_c19_native_actual_independent_review_codex/review-1a12035-v2/two-consumer-mode-interface.json"
DISPATCHER = ROOT / "execution/command_dispatcher/dispatch.py"
ROUTER = ROOT / "ops/ci/w09_formal_router.py"
RUN_ID = "9e912dfc1058454da08ae7f93f4de24d"
NATIVE_HDF_SHA = "49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270"
NATIVE_HANDOFF_SHA = "cc4e8de2bf69b1b322fb500369b85bc4d737b26f761fa746a52e8088c6257835"
NATIVE_REQUEST_SHA = "8c0b984f4bdcd4a89464645e82780dfafbaeba8dfcdb0dbed0958df7b283e84e"
TEMP = ROOT / ".local" / ("w09-c19-main-" + RUN_ID) / "temp"
ROUTES = ("test.research.fixture", "test.retrieval")
SOURCE_ACTOR = "codex:/root/w09_formal_profile_source_impl"
LOCKED_SHA = {
    str(HELPER): "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad",
    str(GUARD): "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",
    str(INTERFACE): "669208b0f10e2bb130299fb04f796695837a5911efbd9b554d110efffe7fb355",
}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def bad_number(_):
        raise ValueError("NONFINITE_NUMBER")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_number)


def pin(path):
    original = Path(path)
    require(not original.is_symlink(), "PIN_ALIAS")
    p = original.resolve(strict=True)
    require(p.is_file() and not p.is_symlink(), "PIN_NOT_REGULAR_FILE")
    raw = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def verify_ref(ref):
    require(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}, "REF_SHAPE")
    require(type(ref["path"]) is str and Path(ref["path"]).is_absolute(), "REF_PATH")
    require(type(ref["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", ref["sha256"]), "REF_SHA")
    require(type(ref["bytes"]) is int and ref["bytes"] >= 0, "REF_BYTES")
    actual = pin(ref["path"])
    require(actual == ref, "REF_CHANGED")
    return actual


def checked(ref):
    actual = verify_ref(ref)
    raw = Path(actual["path"]).read_bytes()
    require(len(raw) == actual["bytes"] and hashlib.sha256(raw).hexdigest() == actual["sha256"],
            "REF_CHANGED_AFTER_PIN")
    return strict_json(raw), actual


def ref_of(path):
    return pin(path)


def source_ref(request, key, expected_name):
    data, ref = checked(request[key])
    require(Path(ref["path"]).name == expected_name, key + "_NAME")
    return data, ref


def root_request(request):
    require(type(request) is dict and request.get("schema") == "researchos.w09-c19-two-dispatcher-root-request.v1", "REQUEST_SCHEMA")
    require(request.get("issued_by") == "codex:/root" and request.get("formal_acceptance") is False,
            "ROOT_REQUEST_AUTHORITY")
    require(request.get("native_producer_rerun") is False and request.get("registry_writes") is False
            and request.get("canonical_writes") is False and request.get("go_provider_calls") is False,
            "REQUEST_SIDE_EFFECTS")
    require(request.get("exact_routes") == list(ROUTES), "REQUEST_ROUTES")
    scope, scope_ref = source_ref(request, "scope_ref", "scope-registration.root.json")
    require(scope.get("issued_by") == "codex:/root" and scope.get("formal_dispatcher") is True
            and scope.get("formal_acceptance") is False and scope.get("parent_acceptance") is False
            and type(scope.get("formal_case_accepted_delta")) is int
            and scope["formal_case_accepted_delta"] == 0, "SCOPE_AUTHORITY")
    require(scope.get("expected_checkpoint_revision") == 370
            and scope.get("expected_path_ownership_revision") == 174
            and scope.get("expected_previous_checkpoint_revision") == 369
            and scope.get("routes") == list(ROUTES), "SCOPE_REGISTERED_SLICE")
    require(scope.get("source_actor") == SOURCE_ACTOR
            and scope.get("source_reviewer") not in (None, SOURCE_ACTOR), "SELF_APPROVAL")
    source_hdf, source_hdf_ref = checked(scope["source_hdf_ref"])
    require(source_hdf.get("status") == "SOURCE_ONLY_PENDING_ROOT_REGISTRATION"
            and source_hdf.get("caller_source_ref") == pin(__file__)
            and request.get("source_hdf_ref") == source_hdf_ref, "SOURCE_NOT_EXACT_ACCEPTED_BYTES")
    source_manifest, source_manifest_ref = checked(source_hdf["manifest_ref"])
    require(source_manifest.get("schema") == "researchos.w09-c19-two-consumer-source-manifest.v1"
            and source_manifest.get("caller_source_ref") == pin(__file__), "SOURCE_MANIFEST")
    review, review_ref = checked(scope["source_review_ref"])
    require(review.get("reviewer_id") not in (None, SOURCE_ACTOR)
            and review.get("decision") == "ACCEPTED_SOURCE_ONLY"
            and review.get("formal_acceptance") is False, "SOURCE_NOT_INDEPENDENTLY_ACCEPTED")
    require(request["source_review_ref"] == review_ref, "SOURCE_REVIEW_REF_CHANGED")
    vector, vector_ref = checked(request["current_canonical_vector_ref"])
    require(vector.get("schema") == "researchos.w09-c19-consumer-current-canonical-vector.v1"
            and vector.get("checkpoint_revision") == 370
            and vector.get("path_ownership_revision") == 174, "CURRENT_VECTOR_VERSION")
    paths = [ROOT / "execution/v2.4" / (name + ".json") for name in
             ("checkpoint", "path_ownership", "step_state", "commands")]
    require(vector.get("refs") == [pin(p) for p in paths], "CURRENT_CANON_DRIFT")
    cp = strict_json(paths[0].read_bytes())
    owner = strict_json(paths[1].read_bytes())
    require(type(cp.get("revision")) is int and cp["revision"] == 370
            and type(cp.get("expected_previous_revision")) is int
            and cp["expected_previous_revision"] == 369
            and type(owner.get("revision")) is int and owner["revision"] == 174,
            "CURRENT_CANON_REVISIONS")
    require(cp.get("work_in_progress", {}).get("w09_c19_two_dispatcher_scope_ref") == scope_ref,
            "SCOPE_NOT_IN_CURRENT_CP")
    proof, proof_ref = checked(request["actual_registration_proof_ref"])
    require(proof.get("issued_by") == "codex:/root"
            and proof.get("scope_ref") == scope_ref
            and proof.get("current_canonical_vector_ref") == vector_ref
            and proof.get("previous_checkpoint_revision") == 369
            and proof.get("registered_checkpoint_revision") == 370, "REGISTRATION_NOT_PROVEN")
    current_owner, owner_ref = checked(request["current_owner_ref"])
    worker, worker_ref = checked(request["current_worker_ref"])
    require(current_owner.get("scope_ref") == scope_ref and worker.get("scope_ref") == scope_ref
            and current_owner.get("owner_id") == "codex:/root"
            and worker.get("worker_id") == "codex:/root"
            and current_owner.get("selected_worker_ref") == worker_ref
            and worker.get("selected_owner_ref") == owner_ref,
            "CURRENT_OWNER_WORKER")
    require(type(request.get("output_dir")) is str, "OUTPUT_DIR_TYPE")
    output = Path(request["output_dir"])
    require(output.is_absolute() and output.resolve().is_relative_to(ROOT / "execution/v2.4/receipts/W09/W09-99")
            and not output.exists(), "OUTPUT_NOT_FRESH_OWNED")
    return scope, output, [scope_ref, source_hdf_ref, source_manifest_ref, review_ref,
                           vector_ref, proof_ref, owner_ref, worker_ref]


def frozen_plan():
    plan_path = Path(r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\contracts\execution.plan.json")
    raw = plan_path.read_bytes()
    plan = strict_json(raw)
    rows = []
    def walk(value):
        if isinstance(value, dict):
            if value.get("id") == "W09-99" and "verification_commands" in value:
                rows.extend(value["verification_commands"])
            for x in value.values(): walk(x)
        elif isinstance(value, list):
            for x in value: walk(x)
    walk(plan)
    found = [x for x in rows if x.get("key") in ROUTES and x.get("cwd") == "REPOSITORY"
             and x.get("argv_template", [None])[-2:] == ["--case-id", "C19"]]
    require(len(found) == 2 and {x["key"] for x in found} == set(ROUTES), "FROZEN_C19_COMMANDS")
    for item in found:
        require(item["argv_template"] == ["python", "execution/command_dispatcher/dispatch.py",
                item["key"], "--task-id", "W09", "--case-id", "C19"],
                "FROZEN_C19_ARGV")
    result = pin(plan_path)
    require(result["bytes"] == len(raw) and result["sha256"] == hashlib.sha256(raw).hexdigest(),
            "PLAN_CHANGED_DURING_READ")
    return result


def selected_registry(plan_ref):
    pointer_ref = pin(ROOT / "execution/v2.4/current_spec.json")
    pointer = strict_json(Path(pointer_ref["path"]).read_bytes())
    registry_ref = pin(ROOT / "execution/v2.4/commands.json")
    registry = strict_json(Path(registry_ref["path"]).read_bytes())
    require(pointer.get("pointer") == "v2.4"
            and pointer.get("plan_sha256") == plan_ref["sha256"]
            and registry.get("plan_sha256") == plan_ref["sha256"],
            "AUTO_REGISTRY_NOT_FROZEN_V24")
    require(all(registry.get("commands", {}).get(key, {}).get("state") == "BOUND"
                for key in ROUTES), "C19_REGISTRY_UNBOUND")
    return pointer_ref, registry_ref


def qualified_modes():
    interface, interface_ref = checked({**pin(INTERFACE), "sha256": LOCKED_SHA[str(INTERFACE)]})
    require(interface.get("run_id") == RUN_ID and interface.get("actual_consumers_run") is False
            and interface.get("formal_acceptance") is False, "NATIVE_INTERFACE")
    require(type(interface.get("modes")) is list and len(interface["modes"]) == 2, "MODES_COUNT")
    results = []
    for route, row in zip(ROUTES, interface["modes"]):
        require(row.get("route") == [route, "W09", "", "C19"]
                and row.get("consumer_environment_required") == {"TEMP": str(TEMP), "TMP": str(TEMP)}
                and row.get("pure_interface_verification", {}).get("mode") == "FIXTURE"
                and row["pure_interface_verification"].get("formal_authority") is False,
                "MODE_ROUTE_OR_ENV")
        review, review_ref = checked(row["independent_review_ref"])
        decision, decision_ref = checked(row["mode_decision_ref"])
        require(decision.get("decision") == "QUALIFIED" and decision.get("mode") == "FIXTURE"
                and decision.get("run_id") == RUN_ID and decision.get("route") == row["route"]
                and decision.get("reviewer_id") not in (None, SOURCE_ACTOR)
                and decision.get("formal_acceptance") is False
                and decision.get("independent_review_ref", {}).get("sha256") == review_ref["sha256"]
                and row.get("consumer_mode_decision_sha256") == decision_ref["sha256"],
                "MODE_NOT_QUALIFIED")
        results.append((review_ref, decision_ref))
    require(results[0][1] != results[1][1], "MODE_REUSED")
    return interface, interface_ref, results


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def nested_refs(value):
    if isinstance(value, dict):
        if set(value) == {"path", "sha256", "bytes"}:
            yield value
        else:
            for item in value.values():
                yield from nested_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_refs(item)


def packet_inventory(packet):
    mapping = packet.get("raw_copy_mapping")
    require(type(mapping) is list and mapping, "NATIVE_PACKET_EMPTY")
    originals = {}
    archives = {}
    for pair in mapping:
        oref = verify_ref(pair["original_ref"])
        aref = verify_ref(pair["archive_ref"])
        require(oref["bytes"] == aref["bytes"] and oref["sha256"] == aref["sha256"],
                "NATIVE_ARCHIVE_MISMATCH")
        for table, ref in ((originals, oref), (archives, aref)):
            key = ref["path"].casefold()
            require(key not in table, "NATIVE_ALIAS_COLLISION")
            table[key] = ref
    for table in (originals, archives):
        roots = {str(Path(ref["path"]).parent) for ref in table.values()}
        common = Path(os.path.commonpath(roots))
        actual = {}
        for p in common.rglob("*"):
            require(not p.is_symlink(), "NATIVE_SYMLINK")
            if p.is_file():
                key = str(p.resolve()).casefold()
                require(key not in actual, "NATIVE_TREE_ALIAS")
                actual[key] = pin(p)
        require(actual == table, "NATIVE_TREE_MEMBER_DRIFT")
    return [*originals.values(), *archives.values()]


def strict_pass(result, receipt, route, expected):
    require(type(result.get("actual_exit")) is int and result["actual_exit"] == 0
            and result.get("timed_out") is False and result.get("error") is None,
            "OUTER_JOB_FAILED")
    cleanup = result["job_cleanup"]
    require(cleanup.get("unnamed_exclusive_job") is True
            and cleanup.get("kill_on_job_close_configured") is True
            and cleanup.get("assigned_before_resume") is True
            and cleanup.get("primary_exit_confirmed") is True
            and cleanup.get("job_idle_confirmed") is True
            and cleanup.get("active_processes_last_observed") == 0
            and cleanup.get("handles_closed") is True and cleanup.get("errors") == [],
            "OWNED_DESCENDANTS_NOT_CLOSED")
    require(type(result.get("owned_child_pid")) is int
            and type(result.get("creation_time_100ns")) is int, "PRIMARY_IDENTITY_UNKNOWN")
    require(receipt.get("status") == "PASS" and type(receipt.get("exit_code")) is int
            and receipt["exit_code"] == 0 and type(receipt.get("child_exit_code")) is int
            and receipt["child_exit_code"] == 0 and receipt.get("command_key") == route,
            "DISPATCH_RECEIPT_NOT_PASS")
    require(receipt.get("selectors") == {"task_id": "W09", "check_id": "", "case_id": "C19"}
            and receipt.get("registry_spec") == "v2.4", "DISPATCH_SELECTOR")
    require(receipt.get("assertion_ids") == ["C19-01", "C19-02", "C19-03"], "C19_ASSERTIONS")
    require(receipt.get("registered_command_revision") == expected["registry_sha256"]
            and receipt.get("dispatcher_sha256") == expected["dispatcher_sha256"]
            and receipt.get("toolchain_revision") == expected["toolchain_sha256"],
            "DISPATCH_INPUT_REVISION_CHANGED")
    versions = receipt.get("input_versions")
    require(type(versions) is list and
            {item.get("path"): item.get("sha256") for item in versions if type(item) is dict}
            .get("ops/ci/w09_formal_router.py") == expected["router_sha256"],
            "ROUTER_INPUT_REVISION_CHANGED")


def execute(request_ref):
    request, request_pin = checked(request_ref)
    scope, output, registration_refs = root_request(request)
    plan_ref = frozen_plan()
    pointer_ref, registry_ref = selected_registry(plan_ref)
    expected_dispatch = {"registry_sha256": registry_ref["sha256"],
                         "dispatcher_sha256": pin(DISPATCHER)["sha256"],
                         "toolchain_sha256": pin(ROOT / "execution/toolchains/locked.json")["sha256"],
                         "router_sha256": pin(ROUTER)["sha256"]}
    interface, interface_ref, modes = qualified_modes()
    require(scope.get("frozen_plan_ref") == plan_ref
            and scope.get("native_qualified_hdf_ref") == request.get("native_qualified_hdf_ref")
            and scope.get("native_historical_request_ref") == request.get("native_historical_request_ref"),
            "NATIVE_PROVENANCE_SCOPE")
    native_hdf, native_hdf_ref = checked(request["native_qualified_hdf_ref"])
    native_root_request, native_root_request_ref = checked(request["native_historical_request_ref"])
    handoff, handoff_ref = checked(request["native_handoff_ref"])
    require(native_hdf_ref["sha256"] == NATIVE_HDF_SHA
            and native_root_request_ref["sha256"] == NATIVE_REQUEST_SHA
            and handoff_ref["sha256"] == NATIVE_HANDOFF_SHA, "NATIVE_ROOT_PINS")
    require(scope.get("native_handoff_ref") == handoff_ref
            and handoff.get("run_id") == RUN_ID and handoff.get("all_guards_closed") is True
            and handoff.get("all_owned_jobs_closed") is True, "NATIVE_HANDOFF")
    ready, ready_ref = checked(handoff["prepare_ready_ref"])
    closed, closed_ref = checked(handoff["producer_closed_ref"])
    packet, packet_ref = checked(handoff["native_packet_ref"])
    require(closed.get("all_owned_jobs_closed") is True and packet.get("run_id") == RUN_ID,
            "NATIVE_PACKET_NOT_CLOSED")
    require(native_hdf.get("status") == "ACTUAL_MAIN_C19_NATIVE_COMPONENT_AND_FIXTURE_MODES_QUALIFIED"
            and native_hdf.get("actor_role") == "INDEPENDENT_NON_AUTHOR", "NATIVE_NOT_QUALIFIED")
    require(native_root_request.get("schema") == "researchos.root-w09-main-c19-native-request.v1"
            and native_root_request.get("issued_by") == "codex:/root", "HISTORICAL_NATIVE_REQUEST")
    require(pin(PYTHON)["sha256"] == strict_json((ROOT / "execution/toolchains/locked.json").read_bytes())["tools"]["python"]["sha256"],
            "PYTHON_NOT_LOCKED")
    for path, expected in LOCKED_SHA.items():
        require(pin(path)["sha256"] == expected, "LOCKED_SOURCE_DRIFT")
    require(TEMP.is_dir() and TEMP.resolve().is_relative_to(ROOT), "NATIVE_TEMP_MISSING")
    expected_report = ROOT / interface["native_report_ref"]
    expected_tool = ROOT / interface["native_tool_run_ref"]
    require(pin(expected_report)["sha256"] == interface["native_report_sha256"]
            and pin(expected_tool)["sha256"] == interface["native_tool_run_sha256"],
            "NATIVE_REPORT_OR_TOOL_DRIFT")
    refs = [request_pin, *registration_refs, plan_ref, interface_ref, native_hdf_ref,
            native_root_request_ref, handoff_ref, ready_ref, closed_ref, packet_ref,
            pin(expected_report), pin(expected_tool), pin(PYTHON),
            pin(HELPER), pin(GUARD), pin(DISPATCHER), pin(ROUTER),
            pin(ROOT / "execution/toolchains/locked.json"), pin(ROOT / "execution/project_identity.json"),
            registry_ref, pointer_ref, pin(__file__)]
    for review_ref, decision_ref in modes: refs.extend([review_ref, decision_ref])
    refs.extend(packet_inventory(packet))
    for document in (request, scope, handoff, ready, closed, packet, native_hdf):
        for ref in nested_refs(document):
            verify_ref(ref)
            refs.append(ref)
    for p in (ROOT / "execution/v2.4/receipts/W09/W09-99/main_c19_native_actual_independent_review_codex/review-1a12035-v2").glob("*.json"):
        refs.append(pin(p))
    for p in (ROOT / "execution/v2.4" / (name + ".json") for name in
              ("checkpoint", "path_ownership", "step_state", "commands")):
        refs.append(pin(p))
    helper = module(HELPER, "w09_owned_helper")
    guard_mod = module(GUARD, "w09_source_guard")
    refs.extend(pin(p) for p in helper.runtime_resource_paths())
    for obj in list(sys.modules.values()):
        path = getattr(obj, "__file__", None)
        if path and Path(path).is_file(): refs.append(pin(path))
    unique = {}
    for ref in refs:
        key = ref["path"].casefold()
        require(key not in unique or unique[key] == ref, "CONFLICTING_PIN")
        unique[key] = ref
    held = guard_mod.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    try:
        held.acquire(list(unique.values()))
        env = {"SystemRoot": "C:/Windows", "WINDIR": "C:/Windows",
               "ComSpec": "C:/Windows/System32/cmd.exe", "PATH": str(PYTHON.parent) + ";C:/Windows/System32",
               "PATHEXT": ".COM;.EXE;.BAT;.CMD", "USERPROFILE": str(TEMP.parent / "profile"),
               "LOCALAPPDATA": str(TEMP.parent / "profile"), "APPDATA": str(TEMP.parent / "profile"),
               "TEMP": str(TEMP), "TMP": str(TEMP), "PYTHONUTF8": "1",
               "RESEARCHOS_W09_NATIVE_REPORT_REF": interface["native_report_ref"],
               "RESEARCHOS_W09_NATIVE_REPORT_SHA256": interface["native_report_sha256"],
               "RESEARCHOS_W09_TOOL_RUN_REF": interface["native_tool_run_ref"],
               "RESEARCHOS_W09_TOOL_RUN_SHA256": interface["native_tool_run_sha256"],
               "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "NUL",
               "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
        require(Path(env["USERPROFILE"]).is_dir(), "PROFILE_ENV_MISSING")
        for i, route in enumerate(ROUTES):
            row = interface["modes"][i]
            env["RESEARCHOS_W09_MODE_DECISION_REF"] = row["consumer_mode_decision_ref"]
            env["RESEARCHOS_W09_MODE_DECISION_SHA256"] = row["consumer_mode_decision_sha256"]
            argv = [str(PYTHON), "-I", "-S", "-B", "-X", "utf8", str(DISPATCHER),
                    route, "--task-id", "W09", "--case-id", "C19"]
            name = route.replace(".", "-")
            stdout, stderr = output / (name + ".stdout.raw"), output / (name + ".stderr.raw")
            with stdout.open("xb") as so, stderr.open("xb") as se:
                result = helper.run_owned(argv, str(ROOT), env, so, se, 120, creation_flags=0x08000000)
            record = {"route": route, "argv": argv, "cwd": str(ROOT),
                      "result": result, "stdout_ref": pin(stdout), "stderr_ref": pin(stderr),
                      "mode_decision_ref": modes[i][1], "descendant_unobserved_pid": None,
                      "descendant_unobserved_filetime": None, "formal_acceptance": False}
            (output / (name + ".outer-observation.json")).write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            results.append(record)
            require(type(result.get("actual_exit")) is int and result["actual_exit"] == 0,
                    "FIRST_FAILURE_STOP")
            lines = stdout.read_text(encoding="utf-8").splitlines()
            require(len(lines) == 1, "DISPATCH_STDOUT_SHAPE")
            summary = strict_json(lines[0])
            require(summary.get("status") == "PASS" and type(summary.get("assertions")) is int
                    and summary["assertions"] == 3, "DISPATCH_SUMMARY")
            receipt_path = Path(summary["receipt"])
            require(receipt_path.resolve().is_relative_to(ROOT / "execution/invocations")
                    and receipt_path.name == "receipt.json", "DISPATCH_RECEIPT_PATH")
            receipt = strict_json(receipt_path.read_bytes())
            strict_pass(result, receipt, route, expected_dispatch)
            record["dispatcher_receipt_ref"] = pin(receipt_path)
            verified = output / (name + ".verified.json")
            with verified.open("xb") as file:
                file.write((json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        status = "TWO_C19_CONSTRUCTION_CONSUMERS_OBSERVED_PENDING_INDEPENDENT_REVIEW"
    except BaseException:
        status = "STOPPED_FIRST_FAILURE_OR_SOURCE_DRIFT"
        raise
    finally:
        cleanup = held.close()
        close = {"status": status if "status" in locals() else "STOPPED_BEFORE_DISPATCH",
                 "source_guard_cleanup": cleanup, "routes_attempted": [x["route"] for x in results],
                 "all_job_descendants_closed": all(x["result"]["job_cleanup"].get("job_idle_confirmed") is True
                                               and x["result"]["job_cleanup"].get("active_processes_last_observed") == 0
                                               for x in results),
                 "formal_case_accepted_delta": 0, "formal_acceptance": False, "parent_acceptance": False}
        (output / "caller.closed.json").write_text(json.dumps(close, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        require(cleanup["closed"] and cleanup["retained_handles_count"] == 0 and not cleanup["errors"],
                "SOURCE_GUARD_NOT_CLOSED")


if __name__ == "__main__":
    require(len(sys.argv) == 4, "USAGE_REQUEST_PATH_SHA_BYTES")
    execute({"path": sys.argv[1], "sha256": sys.argv[2], "bytes": int(sys.argv[3])})
