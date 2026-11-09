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
    "12_IMPLEMENTATION_AND_HANDOFF.md",
]
CONTRACTS = ["domain.schema.json", "openapi.json", "tasks.json", "acceptance.json", "ui.contract.json"]
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
    require(api.get("info", {}).get("version") == "2.0.0", "OpenAPI version must be 2.0.0")
    require("/v2.0/" in schema.get("$id", ""), "Domain schema ID must identify v2.0")
    for name in ("tasks.json", "acceptance.json"):
        require(read_json(ROOT / "contracts" / name).get("package_version") == "2.0.0", name + ": wrong package version")
    ref_count = check_refs(schema_path) + check_refs(api_path)
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
    return {"task_count":len(tasks), "requirement_count":len(REQ_IDS), "acceptance_case_count":len(cases),
            "schema_definition_count":len(schema.get("$defs",{})), "api_operation_count":len(operations),
            "resolved_ref_count":ref_count, "example_count":example_total,
            "ui_screen_count":ui_count, "token_contrast_checks":contrast_count,
            "evaluation_smoke_fixture_count":12}

def check_traceability(tasks, cases):
    task_doc = (ROOT / "05_WBS.md").read_text(encoding="utf-8")
    case_doc = (ROOT / "06_ACCEPTANCE_TESTS.md").read_text(encoding="utf-8")
    require(set(re.findall(r"^### (W\d\d)｜", task_doc, flags=re.M)) == TASK_IDS, "WBS document task headings disagree")
    require(set(re.findall(r"^### ([CA]\d\d) ·", case_doc, flags=re.M)) == TEST_IDS, "Acceptance document headings disagree")
    for task in tasks:
        match = re.search(r"^### " + task["task_id"] + r"｜.*?\n(.*?)(?=\n### W\d\d｜|\Z)", task_doc, flags=re.M | re.S)
        block = match.group(1) if match else ""
        expected = "、".join(task["requirement_ids"]) + "；" + "、".join(task["acceptance_ids"])
        require(expected in block, task["task_id"] + ": document traceability differs from JSON")
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
    require(ui["version"] == tokens["version"] == "2.0.0", "UI contract and token versions disagree")
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
    require(smoke["version"] == "2.0.0" and smoke["measurement_mode"] == "FIXTURE" and smoke["status"] == "NOT_RUN", "Smoke fixtures are not product results")
    require(len(smoke["cases"]) == 12 and {c["id"] for c in smoke["cases"]} == {f"PF-{i:02d}" for i in range(1,13)}, "12 unique smoke fixtures required")
    require({c["expected_handling"] for c in smoke["cases"]} == {"PASS","FAIL","ABSTAIN","ERROR","INVALID","MISSING"}, "Smoke handling coverage incomplete")
    for case in smoke["cases"]:
        require(case["status"] == "NOT_RUN" and case["expected_decision"] in {"ADOPT","REJECT"}, case["id"] + ": missing frozen development label")
    require(set(smoke["additional_faults"]) >= {"zero_cases","unknown_case_id","config_hash_changed","candidate_hash_changed","unauthorized_egress","unexpected_sharing"}, "Additional evaluation fault coverage incomplete")
    a08 = next(c for c in cases if c["id"] == "A08")
    require(a08["input"]["qualification_key"] == ["task_type","language","provider","model_revision","rubric_revision"], "Qualification key omits provider or revision")
    for name in ("bootstrap_ledger.template.json", "execution_receipt.template.json"):
        template = read_json(ROOT / "examples" / name)
        require(template["template_version"] == "2.0.0" and template["status"] in {"NOT_STARTED","NOT_RUN"}, name + ": template must remain unexecuted")
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
            require(manifest.get("package_version") == "2.0.0", "Manifest version must be 2.0.0")
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
    report = {"package_version":"2.0.0", "status":"PASS" if not ERRORS else "FAIL",
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
