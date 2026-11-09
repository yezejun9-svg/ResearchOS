#!/usr/bin/env python3
"""ResearchOS specification-package checks. Does not run the product.
Uses only Python 3.10+ standard library. The embedded instance checker supports
the JSON Schema keywords used by this package; it is not a general conformance
certification for every JSON Schema/OpenAPI feature.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    "00_START_HERE.md", "01_PRD.md", "02_TECHNICAL_DESIGN.md",
    "03_DATA_CONTRACTS.md", "04_API_CONTRACTS.md", "05_WBS.md",
    "06_ACCEPTANCE_TESTS.md", "07_OPERATIONS_AND_EVOLUTION.md",
    "08_AGENT_EXECUTION_GOAL.md", "09_COMPONENT_DECISIONS.md",
    "10_UI_UX_DESIGN.md", "11_EVALUATION_AND_INTEGRATION.md",
    "12_IMPLEMENTATION_AND_HANDOFF.md", "13_HARNESS_DESIGN.md",
    "14_CLI_DESKTOP_PRODUCT.md", "15_NEW_PROJECT_WORKFLOW.md",
    "16_ADOPTION_JUDGMENT.md",
]
CONTRACTS = ["domain.schema.json", "openapi.json", "tasks.json", "acceptance.json", "ui.contract.json", "harness.contract.json", "product.contract.json", "client.protocol.schema.json", "adoption.contract.json", "adoption.schema.json"]
TASK_IDS = {f"W{i:02d}" for i in range(22)}
TEST_IDS = {f"C{i:02d}" for i in range(1, 27)} | {f"A{i:02d}" for i in range(1, 17)}
REQ_IDS = {f"R{i:02d}" for i in range(1, 21)}
ERRORS = []
CHECKS = []
CACHE = {}

def require(condition, message):
    if not condition:
        ERRORS.append(message)

def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result

def read_json(path):
    path = path.resolve()
    if path not in CACHE:
        CACHE[path] = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    return CACHE[path]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve_ref(ref, current):
    if "://" in ref:
        raise ValueError(f"Remote schema ref prohibited for package check: {ref}")
    file_part, _, fragment = ref.partition("#")
    target = (current.parent / unquote(file_part)).resolve() if file_part else current.resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError(f"Reference leaves package: {ref}")
    value = read_json(target)
    if fragment:
        if not fragment.startswith("/"):
            raise ValueError(f"Only JSON Pointer fragments are used here: {ref}")
        for token in fragment[1:].split("/"):
            token = unquote(token).replace("~1", "/").replace("~0", "~")
            value = value[int(token)] if isinstance(value, list) else value[token]
    return value, target

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def check_refs(path):
    count = 0
    for node in walk(read_json(path)):
        if "$ref" in node:
            try:
                resolve_ref(node["$ref"], path)
                count += 1
            except (ValueError, KeyError, IndexError, FileNotFoundError) as exc:
                ERRORS.append(f"{path.name} ref {node['$ref']}: {exc}")
    return count

def type_matches(value, kind):
    return {
        "null": lambda: value is None,
        "boolean": lambda: isinstance(value, bool),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
        "string": lambda: isinstance(value, str),
        "array": lambda: isinstance(value, list),
        "object": lambda: isinstance(value, dict),
    }.get(kind, lambda: False)()

def instance_errors(value, schema, current, location="$", depth=0):
    """Checks the explicit subset used by example fixtures; refs never fetch network."""
    if depth > 100:
        return [location + ": schema recursion exceeded"]
    if schema is True:
        return []
    if schema is False:
        return [location + ": forbidden by schema"]
    out = []
    def child(v, s, suffix="", filename=current):
        return instance_errors(v, s, filename, location + suffix, depth + 1)
    if "$ref" in schema:
        target, filename = resolve_ref(schema["$ref"], current)
        out += child(value, target, filename=filename)
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type_matches(value, t) for t in types):
            return out + [f"{location}: wrong type, expected {types}"]
    if "const" in schema and (value != schema["const"] or type(value) != type(schema["const"])):
        out.append(location + ": const mismatch")
    if "enum" in schema and not any(value == x and type(value) == type(x) for x in schema["enum"]):
        out.append(location + ": enum mismatch")
    for name in ("allOf", "anyOf", "oneOf"):
        if name in schema:
            results = [child(value, s) for s in schema[name]]
            passed = sum(not x for x in results)
            if name == "allOf":
                out += [e for part in results for e in part]
            elif (name == "anyOf" and passed == 0) or (name == "oneOf" and passed != 1):
                out.append(f"{location}: {name} branches passed={passed}")
    if "not" in schema and not child(value, schema["not"]):
        out.append(location + ": not condition matched")
    if "if" in schema:
        branch = "then" if not child(value, schema["if"]) else "else"
        if branch in schema:
            out += child(value, schema[branch])
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                out.append(f"{location}: missing {key}")
        for key, item in value.items():
            if key in props:
                out += child(item, props[key], "." + key)
            elif schema.get("additionalProperties") is False:
                out.append(f"{location}: unexpected {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                out += child(item, schema["additionalProperties"], "." + key)
        for count_key, comparison in [("minProperties", lambda a,b:a>=b), ("maxProperties",lambda a,b:a<=b)]:
            if count_key in schema and not comparison(len(value), schema[count_key]):
                out.append(location + ": " + count_key)
        for trigger, keys in schema.get("dependentRequired", {}).items():
            if trigger in value:
                for key in keys:
                    if key not in value:
                        out.append(f"{location}: dependency {trigger}->{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", float("inf")):
            out.append(location + ": array length")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            out.append(location + ": duplicate items")
        for index, item in enumerate(value):
            if "items" in schema:
                out += child(item, schema["items"], f"[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", float("inf")):
            out.append(location + ": string length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append(location + ": pattern mismatch")
        if schema.get("format") == "date-time":
            try:
                stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    raise ValueError("timezone required")
            except ValueError:
                out.append(location + ": invalid date-time")
        if schema.get("format") in ("uri", "uri-reference"):
            if schema["format"] == "uri" and not urlparse(value).scheme:
                out.append(location + ": invalid uri")
    if type_matches(value, "number"):
        for key, fn in [("minimum",lambda a,b:a>=b),("maximum",lambda a,b:a<=b),
                        ("exclusiveMinimum",lambda a,b:a>b),("exclusiveMaximum",lambda a,b:a<b)]:
            if key in schema and not fn(value, schema[key]):
                out.append(location + ": " + key)
    return out

def check():
    support_files = ["ui/design-tokens.json", "ui/reference.html", "ui/REFERENCE_CHECK.json",
                     "examples/README.md", "examples/contract_fixtures.json",
                     "examples/evaluation_contract_fixtures.json", "examples/evaluation_smoke_cases.json",
                     "examples/bootstrap_ledger.template.json", "examples/execution_receipt.template.json",
                     "references/README.md"]
    for rel in DOCS + ["contracts/" + x for x in CONTRACTS] + support_files:
        require((ROOT / rel).is_file(), f"Missing file: {rel}")
    if ERRORS:
        return
    for rel in DOCS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        require(len(text) > 300, f"Empty/placeholder document: {rel}")
        require(sum(line.startswith("```") for line in text.splitlines()) % 2 == 0,
                f"Unbalanced code fence: {rel}")
    CHECKS.append("required_files_and_markdown")
    tasks = read_json(ROOT / "contracts/tasks.json")["tasks"]
    cases = read_json(ROOT / "contracts/acceptance.json")["cases"]
    tids = [t["task_id"] for t in tasks]
    cids = [c["id"] for c in cases]
    require(set(tids) == TASK_IDS and len(tids) == len(TASK_IDS), "Task IDs must be W00-W21 exactly")
    require(set(cids) == TEST_IDS and len(cids) == len(TEST_IDS), "Test IDs must be C01-C26 and A01-A16 exactly")
    covered_reqs, covered_cases = set(), set()
    by_id = {t["task_id"]: t for t in tasks}
    for t in tasks:
        require(t.get("status") == "NOT_STARTED", t["task_id"] + ": product task status must remain NOT_STARTED")
        for d in t.get("depends_on", []):
            require(d in by_id and d != t["task_id"], f"{t['task_id']}: invalid dependency {d}")
        reqs, tests = set(t.get("requirement_ids", [])), set(t.get("acceptance_ids", []))
        require(bool(reqs) and reqs <= REQ_IDS, t["task_id"] + ": invalid requirement mapping")
        require(bool(tests) and tests <= TEST_IDS, t["task_id"] + ": invalid acceptance mapping")
        covered_reqs |= reqs
        covered_cases |= tests
        for key in ("owner_role", "input", "deliverable", "completion", "verification_command_keys"):
            require(bool(t.get(key)), f"{t['task_id']}: missing {key}")
    require(covered_reqs == REQ_IDS, "WBS must cover all R01-R20")
    require(covered_cases == TEST_IDS, "WBS must cover all acceptance cases")
    active, done = set(), set()
    def visit(task_id):
        if task_id in active:
            raise ValueError("Task dependency cycle at " + task_id)
        if task_id in done or task_id not in by_id:
            return
        active.add(task_id)
        for dep in by_id[task_id].get("depends_on", []):
            visit(dep)
        active.remove(task_id)
        done.add(task_id)
    for task_id in by_id:
        visit(task_id)
    command_plan = read_json(ROOT / "contracts/tasks.json").get("verification_command_plan", {})
    for t in tasks:
        require(set(t.get("verification_command_keys", [])) <= set(command_plan), t["task_id"] + ": undefined command key")
        require(bool(t.get("task_gate_checks")), t["task_id"] + ": missing phase-specific task gates")
    require("W18" in by_id["W16"]["depends_on"], "System release must depend on verified backup/restore W18")
    for c in cases:
        require(c.get("status") == "NOT_RUN", c["id"] + ": product test must remain NOT_RUN")
        owner = c.get("final_owner_task")
        require(owner in by_id, c["id"] + ": missing final owner task")
        if owner in by_id:
            require(c["id"] in by_id[owner].get("owned_acceptance_ids", []), c["id"] + ": final owner mapping disagrees")
            require(set(c["requirement_ids"]) <= set(by_id[owner]["requirement_ids"]), c["id"] + ": requirements missing from final owner")
            require(set(c["command_keys"]) <= set(by_id[owner]["verification_command_keys"]), c["id"] + ": commands missing from final owner")
        require(set(c.get("command_keys", [])) <= set(command_plan), c["id"] + ": undefined test command key")
        require(set(c.get("requirement_ids", [])) <= REQ_IDS and bool(c.get("requirement_ids")), c["id"] + ": bad requirement IDs")
        for key in ("setup", "actions", "assertions", "evidence_required", "mode", "mandatory_gate"):
            require(bool(c.get(key)), f"{c['id']}: missing {key}")
    CHECKS.append("task_DAG_requirements_acceptance_and_unrun_status")
    schema_path = ROOT / "contracts/domain.schema.json"
    api_path = ROOT / "contracts/openapi.json"
    schema, api = read_json(schema_path), read_json(api_path)
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "Unexpected schema dialect")
    require(api.get("openapi", "").startswith("3.1."), "OpenAPI must be 3.1")
    require(api.get("info", {}).get("version") == "2.3.0", "OpenAPI version must be 2.3.0")
    require("/v2.3/" in schema.get("$id", ""), "Domain schema ID must identify v2.3")
    for name in ("tasks.json", "acceptance.json"):
        require(read_json(ROOT / "contracts" / name).get("package_version") == "2.3.0", name + ": wrong package version")
    ref_count = (check_refs(schema_path) + check_refs(api_path)
                 + check_refs(ROOT / "contracts/client.protocol.schema.json")
                 + check_refs(ROOT / "contracts/adoption.schema.json"))
    operations = []
    for route, path in api["paths"].items():
        for verb, operation in path.items():
            if verb not in ("get","post","put","patch","delete","head","options","trace"):
                continue
            oid = operation.get("operationId")
            require(bool(oid), f"{verb} {route}: missing operationId")
            operations.append(oid)
            params = path.get("parameters", []) + operation.get("parameters", [])
            resolved = []
            for param in params:
                resolved.append(resolve_ref(param["$ref"], api_path)[0] if "$ref" in param else param)
            pnames = {p.get("name") for p in resolved if p.get("in") == "path" and p.get("required")}
            require(set(re.findall(r"{([^}]+)}", route)) <= pnames, f"{verb} {route}: path parameter undefined")
            require(any(str(k).startswith("2") for k in operation.get("responses", {})), f"{verb} {route}: no success response")
    require(len(operations) == len(set(operations)), "Duplicate operationId")
    CHECKS.append("local_schema_refs_and_OpenAPI_operation_structure")
    example_total = 0
    for p in sorted((ROOT / "examples").glob("*.json")):
        example_doc = read_json(p)
        for entry in example_doc.get("examples", []):
            definition = entry["schema_definition"]
            target = schema["$defs"][definition]
            errs = instance_errors(entry["value"], target, schema_path)
            expected = entry.get("expected_valid", True)
            require((not errs) == expected, f"{p.name}/{entry['name']}: expected_valid={expected}, errors={errs}")
            require(entry.get("measurement_mode") == "FIXTURE", f"{p.name}/{entry['name']}: must be FIXTURE")
            example_total += 1
    require(example_total >= 6, "Need positive and negative contract examples")
    CHECKS.append("positive_negative_contract_examples_supported_keyword_subset")
    ui_count, contrast_count = check_ui(schema, set(operations))
    check_traceability(tasks, cases)
    check_evaluation_contract(schema, cases)
    harness_count = check_harness_contract(schema, tasks, cases, command_plan)
    product_count, protocol_examples = check_product_contract(schema, tasks, cases, command_plan, set(operations))
    adoption_count, adoption_examples = check_adoption_contract(schema, tasks, cases, command_plan)
    return {"task_count":len(tasks), "requirement_count":len(REQ_IDS), "acceptance_case_count":len(cases),
            "schema_definition_count":len(schema.get("$defs",{})), "api_operation_count":len(operations),
            "resolved_ref_count":ref_count, "example_count":example_total,
            "ui_screen_count":ui_count, "token_contrast_checks":contrast_count,
            "evaluation_smoke_fixture_count":12, "harness_capability_count":harness_count,
            "cli_desktop_workflow_capability_count":product_count, "client_protocol_fixture_count":protocol_examples,
            "adoption_capability_count":adoption_count, "adoption_fixture_count":adoption_examples}

def adoption_fixture_errors(value, contract):
    """Static fixture invariants only; cannot prove real references, isolation or qualification."""
    errors = []
    if value.get("disposition") == "ADOPT":
        checks = value.get("hard_checks", [])
        ids = [c.get("check_id") for c in checks]
        if sorted(ids) != sorted(contract["required_hard_check_ids"]):
            errors.append("missing/duplicate hard checks")
        if any(c.get("status") not in {"PASS", "NOT_APPLICABLE"} for c in checks):
            errors.append("hard check failed or not run")
        if value.get("selected_candidate_ref") not in value.get("candidate_refs", []):
            errors.append("selected source not in frozen candidates")
        extents = contract["extent_by_strategy"].get(value.get("reuse_strategy"), [])
        if value.get("reuse_extent") not in extents:
            errors.append("strategy/extent mismatch")
    return errors

def check_adoption_contract(schema, tasks, cases, command_plan):
    contract = read_json(ROOT / "contracts/adoption.contract.json")
    require(contract["package_version"] == "2.3.0" and contract["product_status"] == "NOT_STARTED", "Adoption version/status differs")
    require(contract["task_type"] == "reuse_selection", "Source judgment task type differs")
    require(not contract["source_read_is_adoption"] and not contract["must_adopt_any_candidate"], "Inspection or mandatory adoption bypass")
    require(not contract["bootstrap_requires_W11"], "Bootstrap cannot depend on future Jev implementation")
    tm, cm = {t["task_id"]:t for t in tasks}, {c["id"]:c for c in cases}
    caps = contract["capabilities"]
    require(len(caps) == 4 and {c["id"] for c in caps} == {"J01", "J02", "J03", "J04"}, "Adoption capability inventory differs")
    for cap in caps:
        task, case = tm[cap["task_id"]], cm[cap["case_id"]]
        require(cap["status"] == "NOT_RUN", cap["id"] + ": product requirement cannot be pre-passed")
        require(case["final_owner_task"] == task["task_id"], cap["id"] + ": wrong final case owner")
        require(case["id"] in task["acceptance_ids"] and task["task_id"] in case["wbs_ids"], cap["id"] + ": broken traceability")
        require(cap["command_key"] in command_plan and cap["command_key"] in case["command_keys"] and cap["command_key"] in task["verification_command_keys"], cap["id"] + ": invalid command mapping")
        gate = next((g for g in task["task_gate_checks"] if g["check_id"] == cap["check_id"]), None)
        assertion = next((a for a in case["assertions"] if a["id"] == cap["assertion_id"]), None)
        require(gate is not None and assertion is not None and gate["expected"] == assertion["expected"], cap["id"] + ": gate/assertion mismatch")
        require(gate is not None and gate["mode"] == cap["mode"] == case["mode"], cap["id"] + ": measurement mode mismatch")
        require(cap["id"] in case["input"].get("adoption_replays", {}), cap["id"] + ": missing frozen replay")
    require("W11" not in tm["W01"]["depends_on"] and "W14" not in tm["W08"]["depends_on"], "Adoption workflow adds bootstrap cycle")
    require(contract["required_hard_check_ids"] == [f"G{i:02d}" for i in range(1,8)], "Adoption hard check set differs")
    require(contract["mandatory_live_jev_cases"] == ["A08", "A13"], "Real Jev gates removed")
    require("SKILL_UP" in schema["$defs"]["EvaluationReport"]["properties"]["engine"]["properties"]["name"]["enum"], "skill-up report engine missing")
    require(contract["skill_up"]["adapter_owner"] == "W10" and contract["skill_up"]["trial_owner"] == "W15", "skill-up path ownership differs")
    require(not contract["skill_up"]["desktop_startup_dependency"], "Optional evaluator blocks Desktop startup")
    require("adoption_decision_ref" in read_json(ROOT / "contracts/client.protocol.schema.json")["$defs"]["ReuseDecisionPayload"]["required"], "Implementation plan lacks adoption decision link")
    fixture_doc = read_json(ROOT / "examples/adoption_fixtures.json")
    fixture_schema_path = ROOT / "contracts/adoption.schema.json"
    defs = read_json(fixture_schema_path)["$defs"]
    fixtures = fixture_doc["fixtures"]
    require(fixture_doc["status"] == "NOT_RUN" and len(fixtures) == 12, "Adoption examples must be 12 unrun fixtures")
    for entry in fixtures:
        errors = instance_errors(entry["value"], defs[entry["schema_definition"]], fixture_schema_path)
        errors += adoption_fixture_errors(entry["value"], contract)
        require((not errors) == entry["expected_valid"], entry["name"] + ": fixture validity differs: " + str(errors))
        require(entry["measurement_mode"] == "FIXTURE", entry["name"] + ": not a fixture")
    for doc in ["00_START_HERE.md", "01_PRD.md", "02_TECHNICAL_DESIGN.md", "03_DATA_CONTRACTS.md", "04_API_CONTRACTS.md", "08_AGENT_EXECUTION_GOAL.md", "11_EVALUATION_AND_INTEGRATION.md", "13_HARNESS_DESIGN.md", "15_NEW_PROJECT_WORKFLOW.md", "16_ADOPTION_JUDGMENT.md"]:
        require("reuse_selection" in (ROOT / doc).read_text(), doc + ": source judgment scope missing")
    CHECKS.append("Jev_evidence_bound_adoption_skill_up_mapping_and_negative_fixtures")
    return len(caps), len(fixtures)

def check_harness_contract(schema, tasks, cases, command_plan):
    contract = read_json(ROOT / "contracts/harness.contract.json")
    require(contract.get("package_version") == "2.3.0", "Harness version differs")
    require(contract.get("product_status") == "NOT_STARTED", "Harness cannot imply product completion")
    task_map = {t["task_id"]: t for t in tasks}
    case_map = {c["id"]: c for c in cases}
    caps = contract.get("capabilities", [])
    require(len(caps) == 10 and {c["id"] for c in caps} == {f"H{i:02d}" for i in range(1,11)}, "Need H01-H10 exactly")
    doc = (ROOT / contract["authority"]).read_text(encoding="utf-8")
    for cap in caps:
        task, case = task_map.get(cap["task_id"]), case_map.get(cap["case_id"])
        require(task is not None and case is not None, cap["id"] + ": invalid task/case")
        if task is None or case is None:
            continue
        require(cap["status"] == "NOT_RUN", cap["id"] + ": cannot pre-pass runtime requirement")
        require(cap["case_id"] in task["acceptance_ids"] and cap["task_id"] in case["wbs_ids"], cap["id"] + ": broken traceability")
        require(cap["command_key"] in command_plan and cap["command_key"] in task["verification_command_keys"] and cap["command_key"] in case["command_keys"], cap["id"] + ": command not bound in planning contracts")
        gates = [g for g in task["task_gate_checks"] if g["check_id"] == cap["check_id"]]
        assertions = [a for a in case["assertions"] if a["id"] == cap["assertion_id"]]
        require(len(gates) == len(assertions) == 1, cap["id"] + ": missing/duplicate gate or assertion")
        if len(gates) == len(assertions) == 1:
            require(gates[0]["expected"] == assertions[0]["expected"], cap["id"] + ": divergent expected behavior")
        require(cap["id"] in case["input"].get("harness_replays", {}), cap["id"] + ": no frozen replay input")
        require(cap["id"] in doc, cap["id"] + ": absent from implementation design")
    policy = contract["route_policy"]
    product = read_json(ROOT / "contracts/product.contract.json")
    require(policy == product["route_policy"] and policy["single_business_scheduler"] is True, "Harness and product route policy disagree")
    a02 = case_map["A02"]["input"]
    require(a02["preferred_route"].upper() == policy["preferred"] and a02["maximum_reuse_routes"] == policy["maximum_reuse_routes"] and a02["repairs_per_route"] == policy["repairs_per_route"], "A02 reuse selection bounds differ")
    baselines = {b["id"]: b for b in contract["baselines"]}
    require(a02["baseline_commit"] == baselines["mu"]["revision"], "Mu qualification commit differs")
    require(all(b["qualification_status"] == "NOT_RUN" for b in baselines.values()), "Source review cannot imply product qualification")
    require(set(contract["defaults"]["decision_modes"]) == set(schema["$defs"]["DecisionMode"]["enum"]), "Harness decision modes invent domain values")
    coverage = schema["$defs"]["SourceCoverage"]["properties"]["status"]["enum"]
    require(set(contract["source_coverage_mapping"].values()) <= set(coverage), "Harness source coverage invents status")
    require(contract["defaults"]["budget_cap"] is None, "Unknown/unlimited amount cannot become zero")
    require(contract["defaults"]["no_progress_iterations"] == case_map["C16"]["input"]["no_progress_iteration_limit"], "Harness no-progress policy differs")
    short = (ROOT / "GOAL_START.txt").read_text(encoding="utf-8").strip()
    require(short.startswith("/goal ") and len(short) < 600, "Short goal must fit reviewed Mu goal-check window")
    require("08_AGENT_EXECUTION_GOAL.md" in short and "42" in short and "22" in short, "Short goal omits full spec or completion scope")
    source = read_json(ROOT / "references/Mu_Source_Manifest.json")
    require(source["commit"] == baselines["mu"]["revision"] and source["product_tests"] == "NOT_RUN", "Mu source evidence differs from baseline")
    CHECKS.append("harness_task_gate_assertion_route_mode_and_short_goal_consistency")
    return len(caps)

def check_product_contract(schema, tasks, cases, command_plan, operations):
    product = read_json(ROOT / "contracts/product.contract.json")
    require(product["package_version"] == "2.3.0" and product["product_status"] == "NOT_STARTED", "Product contract version/status differs")
    require(product["required_surfaces"] == ["CLI", "WINDOWS_DESKTOP"], "Both product clients are required")
    task_map, case_map = {t["task_id"]:t for t in tasks}, {c["id"]:c for c in cases}
    caps = product["capabilities"]
    expected = {f"P{i:02d}" for i in range(1,8)} | {"B01", "B02"}
    require(len(caps) == 9 and {c["id"] for c in caps} == expected, "Product/workflow capability inventory differs")
    for cap in caps:
        task, case = task_map[cap["task_id"]], case_map[cap["case_id"]]
        require(cap["status"] == "NOT_RUN", cap["id"] + ": runtime requirement cannot be pre-passed")
        require(case["id"] in task["acceptance_ids"] and task["task_id"] in case["wbs_ids"], cap["id"] + ": task/case mapping differs")
        require(cap["command_key"] in command_plan and cap["command_key"] in case["command_keys"] and cap["command_key"] in task["verification_command_keys"], cap["id"] + ": invalid command mapping")
        gate = next((g for g in task["task_gate_checks"] if g["check_id"] == cap["check_id"]), None)
        assertion = next((a for a in case["assertions"] if a["id"] == cap["assertion_id"]), None)
        require(gate is not None and assertion is not None and gate["expected"] == assertion["expected"], cap["id"] + ": gate/assertion mismatch")
        require(cap["id"] in case["input"].get("product_replays", {}), cap["id"] + ": missing frozen replay")
    routes = schema["$defs"]["ProjectBinding"]["properties"]["route"]["enum"]
    require(routes == product["route_policy"]["allowed_selected_routes"], "Domain binding route differs from product")
    require(product["route_policy"]["custom_only_after_evidence"], "Custom implementation needs gap evidence")
    require(product["bootstrap"]["order"] == ["LOCAL_INVENTORY", "RESEARCH", "REUSE_DECISION", "IMPLEMENTATION"], "Local-first workflow order differs")
    require("CLI/**" in task_map["W05"]["allowed_paths"] and "DESKTOP/**" in task_map["W13"]["allowed_paths"], "Product owners lack client write paths")
    require("W04" in task_map["W05"]["depends_on"], "CLI init/goal requires project/context implementation")
    protocol = product["local_protocol"]
    require(set(protocol["domain_operations"]) <= operations, "Client mapping uses undefined domain operation")
    require(set(protocol["payload_definitions"]) == set(protocol["methods"]), "Every local method requires a payload definition")
    client_schema_path = ROOT / "contracts/client.protocol.schema.json"
    client_schema = read_json(client_schema_path)
    require(set(client_schema["$defs"]["CommandEnvelope"]["properties"]["method"]["enum"]) == set(protocol["methods"]), "Client method enum differs")
    require(set(protocol["payload_definitions"].values()) <= set(client_schema["$defs"]), "Undefined client payload schema")
    for command in product["cli"]["commands"]:
        require(set(command["local_operations"]) <= set(protocol["methods"]), command["id"] + ": CLI operation not defined")
    ui = read_json(ROOT / "contracts/ui.contract.json")
    require(ui["product_surface"] == "WINDOWS_DESKTOP_WITH_SHARED_CLI_CORE", "UI is not bound to Desktop")
    for screen in ui["screens"]:
        require(screen["surface"] == "DESKTOP" and set(screen.get("local_operation_ids", [])) <= set(protocol["methods"]), screen["id"] + ": invalid desktop method mapping")
    fixture_doc = read_json(ROOT / "examples/client_protocol_fixtures.json")
    require(fixture_doc["status"] == "NOT_RUN", "Protocol fixture file is not a runtime result")
    fixtures = fixture_doc["fixtures"]
    require(len(fixtures) == 6 and any(not x["expected_valid"] for x in fixtures), "Protocol positive/negative examples missing")
    for entry in fixtures:
        errs = instance_errors(entry["value"], client_schema["$defs"][entry["schema_definition"]], client_schema_path)
        require((not errs) == entry["expected_valid"], entry["name"] + ": protocol fixture validity differs: " + str(errs))
        require(entry["measurement_mode"] == "FIXTURE", entry["name"] + ": examples must be fixtures")
    CHECKS.append("CLI_Desktop_shared_core_local_first_workflow_and_protocol_examples")
    return len(caps), len(fixtures)

def check_traceability(tasks, cases):
    task_doc = (ROOT / "05_WBS.md").read_text(encoding="utf-8")
    case_doc = (ROOT / "06_ACCEPTANCE_TESTS.md").read_text(encoding="utf-8")
    dependencies = {task["task_id"]: set(task["depends_on"]) for task in tasks}
    levels, completed = [], set()
    while len(completed) < len(tasks):
        ready = sorted(tid for tid, deps in dependencies.items() if tid not in completed and deps <= completed)
        if not ready:
            require(False, "Cannot derive WBS overview from task DAG")
            break
        levels.append(ready)
        completed.update(ready)
    overview = re.findall(r"^\| B(\d\d) \| (W\d\d(?:、W\d\d)*) \|$", task_doc, flags=re.M)
    require(overview == [(f"{i:02d}", "、".join(level)) for i, level in enumerate(levels)],
            "WBS overview batches disagree with task DAG")
    require(set(re.findall(r"^### (W\d\d)｜", task_doc, flags=re.M)) == TASK_IDS, "WBS document task headings disagree")
    require(set(re.findall(r"^### ([CA]\d\d) ·", case_doc, flags=re.M)) == TEST_IDS, "Acceptance document headings disagree")
    for task in tasks:
        match = re.search(r"^### " + task["task_id"] + r"｜.*?\n(.*?)(?=\n### W\d\d｜|\Z)", task_doc, flags=re.M | re.S)
        block = match.group(1) if match else ""
        expected = "、".join(task["requirement_ids"]) + "；" + "、".join(task["acceptance_ids"])
        require(expected in block, task["task_id"] + ": document traceability differs from JSON")
        require("**依赖**：" + ("、".join(task["depends_on"]) or "无") + "。" in block,
                task["task_id"] + ": document dependencies differ from JSON")
        for gate in task["task_gate_checks"]:
            require(gate["status"] == "NOT_RUN", gate["check_id"] + ": initial gate must be NOT_RUN")
            require(gate["check"] in block and gate["expected"] in block, gate["check_id"] + ": document gate differs")
    ownership = read_json(ROOT / "contracts/tasks.json")["acceptance_final_owners"]
    require(set(ownership) == TEST_IDS, "Final-owner index must contain all 42 cases exactly")
    owned = [cid for task in tasks for cid in task["owned_acceptance_ids"]]
    require(set(owned) == TEST_IDS and len(owned) == len(TEST_IDS), "Each case must have exactly one final owner")
    for case in cases:
        require(ownership.get(case["id"]) == case["final_owner_task"], case["id"] + ": owner index mismatch")
        require(case["gate_scope"] == "V2_RELEASE", case["id"] + ": wrong release scope")
        match = re.search(r"^### " + case["id"] + r" ·.*?\n(.*?)(?=\n### [CA]\d\d ·|\n## 6\.|\Z)", case_doc, flags=re.M | re.S)
        block = match.group(1) if match else ""
        require(json.dumps(case["input"], ensure_ascii=False, indent=2) in block, case["id"] + ": fixed input differs")
        for assertion in case["assertions"]:
            require(assertion["id"] in block and assertion["expected"] in block, assertion["id"] + ": assertion differs")
    required_count = next(c for c in cases if c["id"] == "A15")["input"]["required_cases"]
    require(required_count == len(TEST_IDS), "Release reproduction expects wrong case count")
    CHECKS.append("document_machine_traceability_and_unique_final_owners")

def check_ui(schema, operations):
    ui = read_json(ROOT / "contracts/ui.contract.json")
    tokens = read_json(ROOT / "ui/design-tokens.json")
    defs = schema["$defs"]
    screens = ui["screens"]
    require(ui["version"] == tokens["version"] == "2.3.0", "UI contract and token versions disagree")
    require(ui["product_implementation_status"] == "NOT_STARTED", "UI implementation must remain NOT_STARTED")
    require(len(screens) == 11 and {s["id"] for s in screens} == {f"S{i:02d}" for i in range(11)}, "Screen IDs must be S00-S10")
    require(len({s["route"] for s in screens}) == len(screens), "Duplicate UI route")
    states = {"loading", "empty", "ready", "error", "forbidden", "partial", "stale", "offline"}
    for screen in screens:
        require(set(screen["operation_ids"]) <= operations, screen["id"] + ": unknown API operation")
        require(set(screen["required_states"]) == states, screen["id"] + ": missing UI states")
        require(set(screen["acceptance_ids"]) <= TEST_IDS and bool(screen["acceptance_ids"]), screen["id"] + ": invalid test links")
        for binding in screen["field_bindings"]:
            require(binding["field"] in defs.get(binding["entity"], {}).get("properties", {}), screen["id"] + ": unknown field " + str(binding))
    require(set(ui["task_status_labels"]) == set(defs["TaskStatus"]["enum"]), "Task UI labels omit or invent status")
    require(set(ui["run_status_labels"]) == set(defs["Run"]["properties"]["status"]["enum"]), "Run UI labels omit or invent status")
    require(set(ui["stage_labels"]) == set(defs["Stage"]["enum"]), "UI stages disagree with domain")
    event = ui["event_contract"]
    require(event["operation_id"] in operations and set(event["recovery_operations"]) <= operations, "Event recovery operation missing")
    require(event["expired_cursor_status"] == 410 and event["side_effects_on_replay"] is False, "Unsafe event recovery contract")
    preview = ui["preview_contract"]
    require(preview["max_inline_bytes"] == 5 * 1024 * 1024 and preview["acceptance_id"] == "C25", "Preview contract mismatch")
    require(not preview["sealed_editing"] and not preview["html_scripts_enabled"] and not preview["external_content_auto_load"], "Unsafe preview defaults")
    matrix = ui["validation_matrix"]
    require(matrix["product_test_status"] == "NOT_RUN", "UI matrix cannot report product PASS")
    require(matrix["viewports"] == [[1440,1000],[1024,768],[768,1024],[390,844],[320,780]], "UI viewport matrix differs")
    require(set(matrix["themes"]) == set(tokens["themes"]) == {"light", "dark"}, "Two themes required")
    require(matrix["zoom_percent"] == [100,200] and matrix["keyboard_required"], "Missing zoom/keyboard coverage")
    require(tokens["layout"]["mobile_target_px"] >= 44 and tokens["motion_ms"]["reduced"] == 0, "Token accessibility defaults disagree")
    def luminance(color):
        values = [int(color[i:i+2], 16) / 255 for i in (1,3,5)]
        linear = [v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (0.2126,0.7152,0.0722)))
    contrast_count = 0
    for theme, colors in tokens["themes"].items():
        for name, color in colors.items():
            require(bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", color)), f"{theme}/{name}: invalid color")
        for front, back, minimum in tokens["contrast_pairs"]:
            a, b = sorted([luminance(colors[front]), luminance(colors[back])])
            ratio = (b + 0.05) / (a + 0.05)
            require(ratio >= minimum, f"{theme}/{front}/{back}: contrast {ratio:.2f} < {minimum}")
            contrast_count += 1
    ref = (ROOT / "ui/reference.html").read_text(encoding="utf-8")
    require("示例" in ref and "设计参考" in ref, "Reference UI must identify illustrative data")
    require(not re.search(r'<(?:script|link|img|iframe)[^>]+(?:src|href)=[\"\']https?://', ref, re.I), "Reference must not auto-fetch network assets")
    check = read_json(ROOT / "ui/REFERENCE_CHECK.json")
    require(check["scope"] == "OFFLINE_UI_REFERENCE_ONLY" and check["product_tests"] == "NOT_RUN", "Reference check scope mismatch")
    CHECKS.append("UI_routes_operations_fields_states_and_static_color_contrast")
    return len(screens), contrast_count

def check_evaluation_contract(schema, cases):
    defs = schema["$defs"]
    for definition in ("Artifact", "CreateArtifactRequest"):
        require("access_class" in defs[definition]["required"], definition + ": missing required access_class")
        require(set(defs[definition]["properties"]["access_class"]["enum"]) == {"PROJECT", "VERIFIER_ONLY"}, definition + ": bad access classification")
    for name in ("EvaluationCaseResult", "EvaluationCounts", "EvaluationReport", "EvaluationSummary"):
        require(name in defs, "Missing evaluation content definition: " + name)
    smoke = read_json(ROOT / "examples/evaluation_smoke_cases.json")
    require(smoke["version"] == "2.3.0" and smoke["measurement_mode"] == "FIXTURE" and smoke["status"] == "NOT_RUN", "Smoke fixtures are not product results")
    require(len(smoke["cases"]) == 12 and {c["id"] for c in smoke["cases"]} == {f"PF-{i:02d}" for i in range(1,13)}, "12 unique smoke fixtures required")
    require({c["expected_handling"] for c in smoke["cases"]} == {"PASS","FAIL","ABSTAIN","ERROR","INVALID","MISSING"}, "Smoke handling coverage incomplete")
    for case in smoke["cases"]:
        require(case["status"] == "NOT_RUN" and case["expected_decision"] in {"ADOPT","REJECT"}, case["id"] + ": missing frozen development label")
    require(set(smoke["additional_faults"]) >= {"zero_cases","unknown_case_id","config_hash_changed","candidate_hash_changed","unauthorized_egress","unexpected_sharing"}, "Additional evaluation fault coverage incomplete")
    a08 = next(c for c in cases if c["id"] == "A08")
    require(a08["input"]["qualification_key"] == ["task_type","language","provider","model_revision","rubric_revision"], "Qualification key omits provider or revision")
    for name in ("bootstrap_ledger.template.json", "execution_receipt.template.json"):
        template = read_json(ROOT / "examples" / name)
        require(template["template_version"] == "2.3.0" and template["status"] in {"NOT_STARTED","NOT_RUN"}, name + ": template must remain unexecuted")
    CHECKS.append("evaluation_protocol_fixture_labels_and_restricted_artifact_contract")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-manifest", action="store_true", help="Authoring only: skip final hash inventory")
    parser.add_argument("--write-report", action="store_true", help="Write PACKAGE_VALIDATION.json; never product results")
    args = parser.parse_args()
    counts = {}
    try:
        counts = check() or {}
        manifest_path = ROOT / "PACKAGE_MANIFEST.json"
        if not args.skip_manifest:
            manifest = read_json(manifest_path)
            require(manifest.get("package_version") == "2.3.0", "Manifest version must be 2.3.0")
            require(set(manifest.get("case_ids", [])) == TEST_IDS, "Manifest acceptance inventory mismatch")
            expected_files = {entry["path"] for entry in manifest["files"]}
            require(len(expected_files) == len(manifest["files"]), "Duplicate manifest file entry")
            for entry in manifest["files"]:
                p = (ROOT / entry["path"]).resolve()
                require(p.is_relative_to(ROOT) and p.is_file(), "Manifest path missing/invalid: " + entry["path"])
                if p.is_file():
                    require(p.stat().st_size == entry["size_bytes"] and digest(p) == entry["sha256"], "Manifest mismatch: " + entry["path"])
            actual_files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()
                            and p.name not in ("PACKAGE_MANIFEST.json","PACKAGE_VALIDATION.json")
                            and "__pycache__" not in p.parts}
            require(actual_files == expected_files, "Manifest inventory differs from package files")
            CHECKS.append("manifest_bytes_and_hashes")
    except Exception as exc:
        ERRORS.append(f"{type(exc).__name__}: {exc}")
    report = {"package_version":"2.3.0", "status":"PASS" if not ERRORS else "FAIL",
              "checked_at":dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z"),
              "scope":"SPECIFICATION_PACKAGE_ONLY", "product_tests":"NOT_RUN",
              "checks":CHECKS, "counts":counts, "errors":ERRORS,
              "limits":["Does not execute product tests or validate runtime authorization.",
                        "Embedded schema instance validation covers this package's used fixture keywords; not full standards certification.",
                        "Cross-entity business invariants require implementation and acceptance tests.",
                        "UI checks are static mappings and token contrast; browser layout and interactions are not certified."]}
    if (ROOT / "PACKAGE_MANIFEST.json").is_file():
        report["manifest_sha256"] = digest(ROOT / "PACKAGE_MANIFEST.json")
    if args.write_report:
        (ROOT / "PACKAGE_VALIDATION.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if ERRORS else 0

if __name__ == "__main__":
    sys.exit(main())
