"""Additional v2.4 specification checks; no product execution or dependencies.

The caller supplies its existing instance checker so this module neither imports
the main validator nor substitutes a different JSON Schema implementation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath


TASK_IDS = {f"W{i:02d}" for i in range(22)}
METHODS = {
    "host.status", "host.configure", "project.bootstrap", "session.list",
    "session.create", "session.get", "session.attach", "session.send",
    "session.control", "session.events", "session.handoff", "goal.start",
    "provider.models", "provider.probe", "workspace.register", "workspace.list",
    "workspace.tree", "workspace.read", "workspace.diff", "workspace.write",
    "artifact.import", "session.update", "permission.respond",
}
EVENTS = {
    "MESSAGE", "TOOL_STARTED", "TOOL_RESULT", "JUDGE_DECISION", "RUN_STATE",
    "GOAL_STATE", "ARTIFACT", "USAGE", "CHECKPOINT", "CLIENT_HANDOFF",
    "BOOTSTRAP_STATE", "PERMISSION_REQUIRED", "PERMISSION_RESOLVED", "ERROR",
}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _package_file(root, name):
    if not isinstance(name, str) or not name or PureWindowsPath(name).is_absolute():
        raise ValueError(f"invalid package-relative path: {name!r}")
    if ":" in name or "\\" in name:
        raise ValueError(f"invalid package-relative path: {name!r}")
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"path leaves package: {name}")
    if not path.is_file():
        raise ValueError(f"missing package file: {name}")
    return path


def _load(root, name, require):
    try:
        value = json.loads(_package_file(root, name).read_text(encoding="utf-8"),
                           object_pairs_hook=_unique_pairs)
        if not isinstance(value, dict):
            raise ValueError("document must be an object")
        return value
    except (OSError, ValueError) as exc:
        require(False, f"v2.4 {name}: {exc}")
        return {}


def _index(rows, key, label, require):
    result = {}
    if not isinstance(rows, list):
        require(False, f"{label} must be a list")
        return result
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(key), str):
            require(False, f"{label} contains an invalid {key}")
            continue
        identity = row[key]
        require(identity not in result, f"{label} duplicate {key}: {identity}")
        result[identity] = row
    return result


def _strings(value, label, require):
    valid = isinstance(value, list) and all(isinstance(item, str) for item in value)
    require(valid, f"{label} must be a string list")
    if not valid:
        return set()
    require(len(value) == len(set(value)), f"{label} contains duplicates")
    return set(value)


def _acyclic(steps, require):
    pending = {sid: set(step.get("dependencies", [])) & steps.keys()
               for sid, step in steps.items()}
    while pending:
        ready = {sid for sid, deps in pending.items() if not deps}
        if not ready:
            require(False, "execution.plan dependency cycle: " + ", ".join(sorted(pending)))
            return
        pending = {sid: deps - ready for sid, deps in pending.items() if sid not in ready}


def _check_scope(scope, label, require):
    require(not scope.startswith(("EXECUTION/v2.4", "SPEC/v2.4"))
            and "execution/v2.4/v2.4" not in scope
            and "spec/v2.4/v2.4" not in scope,
            f"{label} duplicates the mapped v2.4 namespace: {scope}")


def _argv(command, label, require):
    argv = command.get("argv_template")
    valid = isinstance(argv, list) and bool(argv) and all(isinstance(x, str) for x in argv)
    require(valid, f"{label} argv_template must be a nonempty string list")
    if not valid:
        return []
    require(not any(re.search(r"[<>{}]|PLACEHOLDER|PARENT_CHECK_ID_OR_CASE_SELECTOR", x) for x in argv),
            f"{label} unresolved argv selector placeholder")
    return argv


def _command_selection(task_doc, plan, tasks, cases, commands, require):
    selection = task_doc.get("verification_command_selection", {})
    expected_checks = {(tid, check["check_id"]) for tid, task in tasks.items()
                       for check in task.get("task_gate_checks", [])}
    expected_cases = {(cid, key) for cid, case in cases.items()
                      for key in case.get("command_keys", [])}
    seen_checks, seen_cases = set(), set()
    by_task = {tid: [] for tid in tasks}
    counts = []
    for group, field, seen, expected in (
        ("parent_check_bindings", "check_id", seen_checks, expected_checks),
        ("formal_case_bindings", "case_id", seen_cases, expected_cases),
    ):
        rows = selection.get(group, [])
        require(isinstance(rows, list) and bool(rows), f"command selection missing {group}")
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                require(False, f"{group} contains a non-object binding")
                continue
            tid, selector, key = row.get("task_id"), row.get(field), row.get("key")
            label = f"{group} {tid}/{selector}/{key}"
            identity = (tid, selector) if field == "check_id" else (selector, key)
            require(identity not in seen, f"{label} duplicate binding")
            seen.add(identity)
            require(identity in expected, f"{label} unknown or out-of-scope selector")
            require(tid in tasks and key in commands, f"{label} unknown task or command")
            if tid in by_task:
                by_task[tid].append(row)
            require(bool(row.get("binding")), f"{label} missing binding instructions")
            other_field = "case_id" if field == "check_id" else "check_id"
            require(other_field not in row, f"{label} mixes case and parent-check selectors")
            if field == "check_id":
                required_assertions = {selector}
                require(key in tasks.get(tid, {}).get("verification_command_keys", []),
                        f"{label} parent check command is not assigned to this task")
            else:
                case = cases.get(selector, {})
                required_assertions = {assertion["id"] for assertion in case.get("assertions", [])}
                require(case.get("final_owner_task") == tid, f"{label} is not assigned to the case final owner")
            actual_assertions = _strings(row.get("expected_assertion_ids"), f"{label} assertion IDs", require)
            require(actual_assertions == required_assertions, f"{label} expected assertion coverage differs")
            argv = _argv(row, label, require)
            if tid == "W00" and field == "check_id":
                require(key == "package.validate" and row.get("cwd") == "SPEC"
                        and argv == ["python", "tools/validate_package.py"],
                        f"{label} must invoke the actual package validator")
                continue
            require(row.get("cwd") == "REPOSITORY", f"{label} must run from REPOSITORY")
            flag, other_flag = "--" + field.replace("_", "-"), "--" + other_field.replace("_", "-")
            require(argv.count(flag) == 1 and other_flag not in argv,
                    f"{label} must use only its exact {flag} selector")
            if flag in argv:
                position = argv.index(flag)
                require(position + 1 < len(argv) and argv[position + 1] == selector,
                        f"{label} argv selector differs from binding")
            if tid == "W01" and field == "check_id":
                require(key == "core.qualify"
                        and argv == ["python", "qualification/v2.4/qualify.py", flag, selector],
                        f"{label} must use the direct qualification driver")
            else:
                require(argv == ["python", "execution/command_dispatcher/dispatch.py", key,
                                 "--task-id", tid, flag, selector],
                        f"{label} must use the exact dispatcher task/selector invocation")
        require(seen == expected, f"{group} coverage mismatch; missing={sorted(expected - seen)}; "
                f"unexpected={sorted(seen - expected)}")
        counts.append(len(seen))
    steps = {step["id"]: step for step in plan.get("steps", [])}
    canonical = lambda rows: sorted(json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows)
    for tid in tasks:
        final = steps.get(f"{tid}-99", {})
        actual = final.get("verification_commands", [])
        if tid == "W00":
            require(len(actual) == 1 and actual[0].get("key") == "package.validate"
                    and actual[0].get("cwd") == "SPEC"
                    and actual[0].get("argv_template") == ["python", "tools/validate_package.py"]
                    and bool(actual[0].get("binding"))
                    and final.get("handoff", {}).get("independent_review_required") is True,
                    "W00-99 must retain actual package validation plus independent evidence review")
        else:
            require(canonical(actual) == canonical(by_task[tid]),
                    f"{tid}-99 verification commands differ from registered exact bindings")
    return tuple(counts)


def _delivery(delivery, tasks, cases, commands, root, require):
    require(delivery.get("package_version") == "2.4.0", "delivery package_version must be 2.4.0")
    require(delivery.get("product_status") == "NOT_STARTED", "delivery must not claim product execution")
    require(delivery.get("all_original_requirements_remain_required") is True,
            "delivery must retain all original requirements")
    try:
        _package_file(root, delivery.get("authority"))
    except ValueError as exc:
        require(False, f"delivery authority: {exc}")
    capabilities = _index(delivery.get("capabilities"), "id", "delivery capabilities", require)
    require(set(capabilities) == {f"U{i:02d}" for i in range(1, 10)},
            "delivery capabilities must cover U01-U09 exactly")
    for uid, cap in capabilities.items():
        tid, cid, command = cap.get("task_id"), cap.get("case_id"), cap.get("command_key")
        task, case = tasks.get(tid, {}), cases.get(cid, {})
        require(tid in tasks, f"{uid} unknown task: {tid}")
        require(cid in cases, f"{uid} unknown case: {cid}")
        gates = {row.get("check_id"): row for row in task.get("task_gate_checks", [])}
        assertions = {row.get("id"): row for row in case.get("assertions", [])}
        gate, assertion = gates.get(cap.get("check_id")), assertions.get(cap.get("assertion_id"))
        require(gate is not None, f"{uid} missing task gate: {cap.get('check_id')}")
        require(assertion is not None, f"{uid} missing assertion: {cap.get('assertion_id')}")
        require(cid in task.get("acceptance_ids", []) and tid in case.get("wbs_ids", []),
                f"{uid} task/case relationship is not bidirectional")
        require(command in commands and command in task.get("verification_command_keys", [])
                and command in case.get("command_keys", []), f"{uid} verification command is not bound")
        require(cap.get("status") == "NOT_RUN", f"{uid} capability status must remain NOT_RUN")
        if gate and assertion:
            require(gate.get("status") == "NOT_RUN", f"{uid} task gate must remain NOT_RUN")
            require(cap.get("mode") == gate.get("mode"), f"{uid} gate mode differs from delivery")
            require(gate.get("expected") == assertion.get("expected"),
                    f"{uid} gate and assertion expectations differ")
    return len(capabilities)


def _plan(plan, tasks, cases, commands, root, require):
    require(plan.get("package_version") == "2.4.0", "execution.plan package_version must be 2.4.0")
    require(plan.get("product_status") == "NOT_STARTED", "execution.plan product_status must be NOT_STARTED")
    steps = _index(plan.get("steps"), "id", "execution.plan steps", require)
    require(bool(steps), "execution.plan has no steps")
    owned = {tid: set() for tid in TASK_IDS}
    all_checks = set()
    for sid, step in steps.items():
        tid = step.get("parent_task")
        require(bool(re.fullmatch(r"W\d{2}-\d{2}", sid)), f"invalid step ID: {sid}")
        require(tid in tasks and sid.startswith(str(tid) + "-"), f"{sid} invalid parent task: {tid}")
        if tid in owned:
            owned[tid].add(sid)
        require(step.get("status") == "NOT_STARTED", f"{sid} must remain NOT_STARTED")
        deps = _strings(step.get("dependencies"), f"{sid} dependencies", require)
        require(deps <= steps.keys(), f"{sid} unknown dependencies: {sorted(deps - steps.keys())}")
        require(sid not in deps, f"{sid} depends on itself")
        final = sid.endswith("-99")
        require(step.get("phase") == ("PARENT_FINAL_GATE" if final else "IMPLEMENTATION_SLICE"),
                f"{sid} phase must distinguish slice from parent final gate")
        for field in ("title", "actions", "deliverables", "write_scope", "limits", "rollback"):
            require(bool(step.get(field)), f"{sid} missing {field}")
        scopes = _strings(step.get("write_scope"), f"{sid} write_scope", require)
        parent_scopes = set(tasks.get(tid, {}).get("allowed_paths", []))
        require(scopes <= parent_scopes, f"{sid} write_scope absent from parent allowed_paths: "
                + ", ".join(sorted(scopes - parent_scopes)))
        receipt_scope = f"execution/v2.4/receipts/{tid}/{sid}/**"
        require(receipt_scope in scopes, f"{sid} write_scope must include own receipt directory")
        for scope in scopes:
            _check_scope(scope, sid, require)
        try:
            card = _package_file(root, step.get("card_path", f"tasks/steps/{sid}.md"))
            card_text = card.read_text(encoding="utf-8")
            require(sid in card_text and "NOT_STARTED" in card_text, f"{sid} task card identity/status missing")
        except (ValueError, OSError) as exc:
            require(False, f"{sid} task card: {exc}")
        read_refs = step.get("read_refs", [])
        require(isinstance(read_refs, list) and bool(read_refs), f"{sid} missing read_refs")
        for ref in read_refs if isinstance(read_refs, list) else []:
            try:
                _package_file(root, ref.get("path") if isinstance(ref, dict) else None)
                require(bool(ref.get("selector")), f"{sid} read_ref selector missing")
            except (ValueError, OSError) as exc:
                require(False, f"{sid} read_ref: {exc}")
        checks = _index(step.get("checks"), "id", f"{sid} checks", require)
        require(bool(checks), f"{sid} has no checks")
        for check_id, check in checks.items():
            require(check_id not in all_checks, f"duplicate step check ID: {check_id}")
            all_checks.add(check_id)
            require(bool(check.get("expected")), f"{check_id} expected result missing")
        verifies = step.get("verification_commands", [])
        require(isinstance(verifies, list) and bool(verifies), f"{sid} missing verification commands")
        for command in verifies if isinstance(verifies, list) else []:
            if not isinstance(command, dict):
                require(False, f"{sid} invalid verification command")
                continue
            require(command.get("key") in commands, f"{sid} unregistered command: {command.get('key')}")
            require(command.get("cwd") in {"SPEC", "REPOSITORY"}, f"{sid} invalid command cwd")
            require(bool(command.get("argv_template")) and bool(command.get("binding")),
                    f"{sid} verification invocation/binding missing")
            _argv(command, sid, require)
        affected = _strings(step.get("affected_formal_cases"), f"{sid} formal cases", require)
        require(affected <= cases.keys(), f"{sid} has unknown formal cases")
        handoff = step.get("handoff", {})
        require(handoff.get("independent_review_required") is True, f"{sid} requires independent review")
        require(handoff.get("state") == "execution/v2.4/step_state.json"
                and handoff.get("checkpoint") == "execution/v2.4/checkpoint.json",
                f"{sid} handoff must use v2.4 construction namespace")
    for tid in sorted(TASK_IDS):
        task, final_id = tasks.get(tid, {}), f"{tid}-99"
        for scope in task.get("allowed_paths", []):
            _check_scope(scope, tid, require)
        require(final_id in steps, f"{tid} missing parent final gate {final_id}")
        require(bool(owned[tid] - {final_id}), f"{tid} has no implementation slice")
        require(task.get("final_step_id") == final_id, f"{tid} final_step_id differs from plan")
        require(_strings(task.get("execution_steps"), f"{tid} execution_steps", require) == owned[tid],
                f"{tid} execution_steps differs from plan ownership")
        final = steps.get(final_id, {})
        required_deps = (owned[tid] - {final_id}) | {f"{dep}-99" for dep in task.get("depends_on", [])}
        require(required_deps <= set(final.get("dependencies", [])),
                f"{final_id} must depend on own slices and parent WBS dependency final gates: "
                + ", ".join(sorted(required_deps - set(final.get("dependencies", [])))))
        require(set(final.get("formal_final_cases", [])) == set(task.get("owned_acceptance_ids", [])),
                f"{final_id} formal cases differ from parent's final ownership")
    if all(isinstance(row.get("dependencies"), list)
           and all(isinstance(x, str) for x in row["dependencies"]) for row in steps.values()):
        _acyclic(steps, require)
    return len(steps), len(all_checks)


def _bindings(definition, discriminator, payload_key, require, label, completed=False):
    result = {}
    for branch in definition.get("allOf", []):
        condition = branch.get("if", {})
        properties = condition.get("properties", {})
        key = properties.get(discriminator, {}).get("const")
        target = branch.get("then", {}).get("properties", {}).get(payload_key, {}).get("$ref")
        if key is None or target is None:
            continue
        if completed and properties.get("status", {}).get("const") != "COMPLETED":
            continue
        require(key not in result, f"{label} duplicate typed branch: {key}")
        result[key] = target
    return result


def _definition(definitions, name):
    definition, seen = definitions.get(name, {}), set()
    while isinstance(definition, dict) and "$ref" in definition:
        ref = definition["$ref"]
        if ref in seen or not ref.startswith("#/$defs/"):
            return {}
        seen.add(ref)
        definition = definitions.get(ref.removeprefix("#/$defs/"), {})
    return definition if isinstance(definition, dict) else {}


def _protocol(schema, product, ui, require):
    definitions = schema.get("$defs", {})
    methods, events = schema.get("x-method-contracts", {}), schema.get("x-event-contracts", {})
    require(set(methods) == METHODS, "protocol method mappings must cover all 23 methods")
    require(set(events) == EVENTS, "protocol event mappings must cover all 14 event kinds")
    local = product.get("local_protocol", {})
    require(local.get("version") == "researchos-client/2", "product protocol version differs from v2")
    require(_strings(local.get("methods"), "product protocol methods", require) == METHODS,
            "product protocol method list differs from schema")
    require(_strings(ui.get("client_methods"), "UI client_methods", require) == METHODS,
            "UI client_methods must cover all protocol methods")
    actions = ui.get("client_actions", [])
    require(isinstance(actions, list) and bool(actions), "UI client_actions must be a nonempty list")
    for action in actions if isinstance(actions, list) else []:
        require(isinstance(action, dict) and action.get("method") in METHODS,
                f"UI client action uses an unknown protocol method: {action}")
    request = definitions.get("CommandEnvelope", {})
    response = definitions.get("CommandResponse", {})
    event = definitions.get("SessionEvent", {})
    for name, definition, discriminator, expected in (
        ("CommandEnvelope", request, "method", METHODS),
        ("CommandResponse", response, "method", METHODS),
        ("SessionEvent", event, "kind", EVENTS),
    ):
        require(definition.get("type") == "object" and definition.get("additionalProperties") is False,
                f"{name} must be a strict object")
        require(set(definition.get("properties", {}).get(discriminator, {}).get("enum", [])) == expected,
                f"{name} discriminator enum differs from typed mappings")
        require(definition.get("properties", {}).get("protocol_version", {}).get("const") == "researchos-client/2",
                f"{name} protocol_version must be researchos-client/2")
    payload_bindings = _bindings(request, "method", "payload", require, "request")
    result_bindings = _bindings(response, "method", "result", require, "completed response", completed=True)
    event_bindings = _bindings(event, "kind", "payload", require, "event")
    require(set(payload_bindings) == METHODS, "each method needs one typed request branch")
    require(set(result_bindings) == METHODS, "each method needs one typed COMPLETED result branch")
    require(set(event_bindings) == EVENTS, "each event kind needs one typed payload branch")
    expected_payloads, expected_results = {}, {}
    for method, contract in methods.items():
        for key, bindings, expected in (("payload", payload_bindings, expected_payloads),
                                        ("result", result_bindings, expected_results)):
            name = contract.get(key) if isinstance(contract, dict) else None
            expected[method] = name
            require(name in definitions, f"{method} missing {key} definition: {name}")
            require(bindings.get(method) == f"#/$defs/{name}", f"{method} {key} branch differs from mapping")
            definition = _definition(definitions, name)
            require(definition.get("type") == "object"
                    and definition.get("additionalProperties") is False
                    and (bool(definition.get("properties")) or name == "EmptyPayload"),
                    f"{method} {key} must resolve to a bounded typed object")
    require(local.get("payload_definitions") == expected_payloads, "product payload definitions differ from protocol")
    require(local.get("result_definitions") == expected_results, "product result definitions differ from protocol")
    require(local.get("event_definitions") == events, "product event definitions differ from protocol")
    for kind, name in events.items():
        require(name in definitions, f"{kind} event definition missing: {name}")
        require(event_bindings.get(kind) == f"#/$defs/{name}", f"{kind} event branch differs from mapping")
        definition = _definition(definitions, name)
        require(definition.get("type") == "object" and definition.get("additionalProperties") is False
                and bool(definition.get("properties")), f"{kind} event payload must be a bounded typed object")
    return len(methods), len(events)


def _fixtures(fixtures_doc, schema, root, require, instance_errors):
    require(fixtures_doc.get("package_version") == "2.4.0", "v2 protocol fixtures must declare package version")
    require(fixtures_doc.get("status") == "NOT_RUN" and fixtures_doc.get("measurement_mode") == "FIXTURE",
            "v2 protocol fixtures must not claim live product execution")
    schema_name = "contracts/client.protocol.schema.json"
    require(fixtures_doc.get("schema_file") == schema_name, "v2 protocol fixture schema path differs")
    fixtures = _index(fixtures_doc.get("fixtures"), "name", "v2 protocol fixtures", require)
    require(len(fixtures) >= 97, "v2 protocol fixtures lost required coverage (minimum 97)")
    covered = {"CommandEnvelope": set(), "CommandResponse": set(), "SessionEvent": set()}
    negative = {key: 0 for key in covered}
    definitions = schema.get("$defs", {})
    for name, fixture in fixtures.items():
        definition, expected = fixture.get("schema_definition"), fixture.get("expected_valid")
        require(type(expected) is bool, f"fixture {name} expected_valid must be boolean")
        require(fixture.get("measurement_mode") == "FIXTURE", f"fixture {name} must remain FIXTURE")
        require(definition in definitions, f"fixture {name} has unknown schema definition: {definition}")
        if definition not in definitions:
            continue
        try:
            errors = instance_errors(fixture.get("value"), definitions[definition], root / schema_name)
            require((not errors) == expected,
                    f"v2 fixture {name}: expected {'valid' if expected else 'invalid'}, got "
                    + ("valid" if not errors else "; ".join(errors[:3])))
        except (KeyError, ValueError, TypeError, OSError, IndexError) as exc:
            require(False, f"v2 fixture {name}: {exc}")
        value = fixture.get("value", {})
        if expected is True and definition in covered and isinstance(value, dict):
            if definition != "CommandResponse" or value.get("status") == "COMPLETED":
                covered[definition].add(value.get("kind" if definition == "SessionEvent" else "method"))
        if expected is False and definition in negative:
            negative[definition] += 1
    require(covered["CommandEnvelope"] == METHODS, "fixtures need a valid request for each of 23 methods")
    require(covered["CommandResponse"] == METHODS, "fixtures need a valid COMPLETED result for each method")
    require(covered["SessionEvent"] == EVENTS, "fixtures need a valid payload for each of 14 event kinds")
    for definition, count in negative.items():
        require(count > 0, f"fixtures need invalid {definition} coverage")
    return len(fixtures), sum(negative.values())


def check_v24(root, require, instance_errors):
    """Report v2.4 contract failures through require and return measured counts."""
    root = Path(root).resolve()
    task_doc = _load(root, "contracts/tasks.json", require)
    acceptance = _load(root, "contracts/acceptance.json", require)
    tasks = _index(task_doc.get("tasks"), "task_id", "v2.4 tasks", require)
    cases = _index(acceptance.get("cases"), "id", "v2.4 acceptance", require)
    require(set(tasks) == TASK_IDS, "v2.4 requires all W00-W21 parent tasks")
    commands = task_doc.get("verification_command_plan", {})
    delivery = _load(root, "contracts/delivery.contract.json", require)
    plan = _load(root, "contracts/execution.plan.json", require)
    product = _load(root, "contracts/product.contract.json", require)
    ui = _load(root, "contracts/ui.contract.json", require)
    schema = _load(root, "contracts/client.protocol.schema.json", require)
    fixtures = _load(root, "examples/client_protocol_v2_fixtures.json", require)
    capabilities = _delivery(delivery, tasks, cases, commands, root, require)
    step_count, check_count = _plan(plan, tasks, cases, commands, root, require)
    parent_bindings, case_bindings = _command_selection(task_doc, plan, tasks, cases, commands, require)
    methods, events = _protocol(schema, product, ui, require)
    fixture_count, invalid_count = _fixtures(fixtures, schema, root, require, instance_errors)
    return {"delivery_capabilities": capabilities, "execution_steps": step_count,
            "execution_step_checks": check_count, "parent_check_bindings": parent_bindings,
            "formal_case_command_bindings": case_bindings, "client_v2_methods": methods,
            "client_v2_event_kinds": events, "client_v2_fixtures": fixture_count,
            "client_v2_invalid_fixtures": invalid_count}
