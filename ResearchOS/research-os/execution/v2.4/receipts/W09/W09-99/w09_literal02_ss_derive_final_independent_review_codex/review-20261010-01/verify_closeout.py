import ast
import datetime as dt
import hashlib
import json
import ntpath
from pathlib import Path
import sys
import types

R = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
RUN = R / "execution/v2.4/receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01"
GUARD_PATH = R / "execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
ROOT_THREAD = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
REVIEWER = "codex:/root/backup_regression_resources"
RAW_REVIEWER = "/root/backup_regression_resources"
ROOT_ACTOR = "codex:/root"
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def pairs(items):
    doc = {}
    for key, value in items:
        if key in doc:
            raise ValueError("duplicate JSON key " + key)
        doc[key] = value
    return doc
def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs)
def path_for(ref):
    path = Path(ref["path"])
    return path if path.is_absolute() else R / path
def identity(ref):
    return ntpath.normcase(ntpath.normpath(str(path_for(ref))))
def same(left, right):
    return identity(left) == identity(right) and left["sha256"] == right["sha256"] and (left.get("bytes") is None or right.get("bytes") is None or left["bytes"] == right["bytes"])
def observed_ref(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "sha256": sha(data), "bytes": len(data)}
def pinned(path, expected_sha, expected_bytes):
    ref = observed_ref(path)
    if ref["sha256"] != expected_sha or ref["bytes"] != expected_bytes:
        raise ValueError("pin mismatch " + str(path))
    return ref
def write_new(name, document):
    data = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as stream:
        stream.write(data)
    return {"path": str(HERE / name), "sha256": sha(data), "bytes": len(data)}
checks = []
def require(label, condition):
    if not condition:
        raise ValueError(label)
    checks.append({"id": label, "result": "PASS"})
def docs(value):
    if type(value) is dict:
        yield value
        for item in value.values():
            yield from docs(item)
    elif type(value) is list:
        for item in value:
            yield from docs(item)
    elif type(value) is str:
        try:
            child = decode(value)
        except (ValueError, TypeError):
            return
        if type(child) in (dict, list):
            yield from docs(child)

facts_ref = pinned(HERE / "bounded-facts.json", "ca6917870bf9cff44fdc1e8c95065064add174002a58e9f03532344975680eac", 13472)
facts = decode(path_for(facts_ref).read_bytes())
refs = dict(facts["refs"])
require("CP398_ACTUAL_PIN", refs["cp"]["sha256"] == "f7a2027f5fe21fe5b0524d1731eba7304327e067f0ea937489b234e07dc2983e" and refs["cp"]["bytes"] == 5114554)
require("CURRENT_SS_ACTUAL_PIN", refs["ss"]["sha256"] == "168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e" and refs["ss"]["bytes"] == 254638)
refs["guard_library"] = pinned(GUARD_PATH, "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", 11404)
refs["Main_w09"] = pinned(R / "execution/v2.4/formal_profile_w09.py", "1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087", 71403)
refs["Main_case_index"] = pinned(R / "execution/v2.4/formal_case_index.py", "e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b", 71844)
refs["bridge_Source8"] = pinned(R / "execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-08/w09_root_bridge.source.py", "22e642b51fb9f7a13b2dcb9db3057078f5479c16fb91fe0deded6b0109d1fb09", 55717)
refs["derive_guard"] = observed_ref(RUN / "derive-7f3a638965a04675ac21860b0e09f01e/source-guard.closed.json")
refs["precheck_guard"] = observed_ref(RUN / "check-9482e0c14ee24c5fa7f24855f8dfc27a/source-guard.closed.json")
refs["old_index"] = pinned(RUN / "capture-a7067db724ce4a34a71a01055c9e00c8/index.proposed.json", "ce0424c83c54d08e82682382be3fbdd1c856fff8c2f697b8104a5a761962d9cb", 756)
refs["proposed_index"] = pinned(RUN / "capture-7d7d176970554ad3b9cdb72bc3b1ce8a/root-corrected-publication01/index.proposed.json", "6bdb7a703934007dae8e50e368d0e41b00b4a132ba5998158255881c21ed520d", 1340)
commit_seed = decode(path_for(refs["commit"]).read_bytes())
refs["owner"] = commit_seed["owner_ref"]
refs["owner_approval"] = commit_seed["approval_ref"]
refs["original_append"] = facts["append_audit"]["original_ref"]
refs["original_derive"] = facts["derive_audit"]["original_ref"]
index_seed = decode(path_for(refs["index"]).read_bytes())
for entry in index_seed["entries"]:
    if entry["event_id"] == "amsg_01a123f7-845b-7043-9dc7-f88b800cdf4b":
        refs["fixed_capture"] = entry["capture_ref"]
        refs["fixed_original"] = entry["origin_ref"]
owner_seed = decode(path_for(refs["owner"]).read_bytes())
for number, evidence in enumerate(owner_seed["evidence"]):
    source = R / "execution/v2.4" / evidence["path"]
    rr = observed_ref(source)
    require("OWNER_EVIDENCE_SHA_" + str(number), rr["sha256"] == evidence["sha256"])
    refs[("context", "review", "issuance")[number]] = rr
guard_raw = path_for(refs["guard_library"]).read_bytes()
module = types.ModuleType("w09_closeout_guard")
module.__file__ = str(GUARD_PATH)
sys.modules[module.__name__] = module
exec(compile(guard_raw, module.__file__, "exec"), module.__dict__)
guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
primary = None
draft = None
closure = None
try:
    unique = {}
    for ref in refs.values():
        require("RESOURCE_REF_SHAPE", type(ref) is dict and set(ref) == {"path", "sha256", "bytes"} and type(ref["bytes"]) is int)
        absolute = dict(ref, path=str(path_for(ref)))
        key = identity(absolute)
        if key in unique:
            require("RESOURCE_DUPLICATE_STABILITY", unique[key]["sha256"] == absolute["sha256"] and unique[key]["bytes"] == absolute["bytes"])
        unique[key] = absolute
    guard.acquire(list(unique.values()))
    def raw(name):
        return guard.get_buffer(str(path_for(refs[name])))
    def doc(name):
        return decode(raw(name))
    commit, before, desired, after, intent, owner, approval = [doc(name) for name in ("commit", "before", "desired", "ss", "intent", "owner", "owner_approval")]
    require("COMMITTED_SINGLE_SS_SCHEMA", commit["schema"] == "researchos.w09-root-single-owner-append-committed.v1" and commit["Canon_written"] is True and commit["only_SS_written"] is True)
    require("BEFORE_ARCHIVE_EXACT_ORIGINAL", commit["before_ref"]["sha256"] == refs["before"]["sha256"] == "fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149" and commit["before_ref"]["bytes"] == refs["before"]["bytes"])
    require("AFTER_CURRENT_EXACT_DESIRED_BYTES", same(commit["after_ref"], refs["ss"]) and raw("desired") == raw("ss"))
    require("SS_EXACT_ONE_APPEND", type(before["steps"]) is list and type(after["steps"]) is list and len(before["steps"]) == 45 and len(after["steps"]) == 46 and after["steps"][:-1] == before["steps"] and after["steps"][-1] == owner)
    inverse = dict(after)
    inverse["steps"] = after["steps"][:-1]
    require("SS_COMPLETE_STRUCTURAL_INVERSE_AND_METADATA", inverse == before and desired == after)
    require("INTENT_MATCHES_ARCHIVE_AND_DESIRED", intent["before_ref"] == commit["before_ref"] and same(intent["desired_ref"], refs["desired"]) and intent["exact_old_rows_preserved"] is True and intent["metadata_preserved"] is True and intent["complete_structural_inverse"] is True)
    require("OWNER_EXACT_APPROVED4858", same(commit["owner_ref"], refs["owner"]) and refs["owner"]["sha256"] == "4858c914f310e2fc83999a511fc070e054c57b12ce594ab14347e0f1612ee9d6" and owner["executor_id"] == ROOT_ACTOR and owner["verifier_id"] == RAW_REVIEWER)
    require("INDEPENDENT_APPROVAL_EXACT_BD843", same(commit["approval_ref"], refs["owner_approval"]) and refs["owner_approval"]["sha256"] == "bd843d082c1f9dbdf92d51aba2c6848511a1ab0799a3ae88773e299f867016fd" and approval["decision"] == "APPROVED_PROSPECTIVE_OWNER_ONLY" and approval["reviewer_id"] == RAW_REVIEWER and same(approval["prospective_owner_ref"], refs["owner"]))
    precheck, derive = doc("precheck"), doc("derive")
    require("MAIN_PRECHECK_PASS_FOR_EXACT_OWNER", same(commit["precheck_result_ref"], refs["precheck"]) and precheck["schema"] == "researchos.w09-main-owner-precheck.v1" and precheck["status"] == "PASS" and same(precheck["owner_ref"], refs["owner"]) and precheck["canonical_acceptance_written"] is False)
    index, old_index, cp = doc("index"), doc("old_index"), doc("cp")
    require("PUBLISHED_INDEX_EXACT_PROPOSED_BYTES", raw("index") == raw("proposed_index"))
    index_inverse = dict(index)
    index_inverse["entries"] = index["entries"][:-1]
    require("PUBLISHED_INDEX_PRESERVES_COMPLETE_OLD_PREFIX", len(index["entries"]) == len(old_index["entries"]) + 1 and index_inverse == old_index)
    require("CP398_FIXED_INDEX_SLOT", cp["revision"] == 398 and same(cp["artifacts"]["w09_root_delivery_capture_index_ref"], refs["index"]))
    capture, issuance = doc("fixed_capture"), doc("issuance")
    constants = {target.id: node.value for node in ast.parse(raw("Main_w09").decode("utf-8")).body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    require("PUBLISHED_CAPTURE_LITERAL_MATCHES_MAIN", capture["source_audit_path"] == ast.literal_eval(constants["ROOT_SOURCE_AUDIT_LOG"]))
    require("PUBLISHED_ISSUANCE_CAPTURE_ORIGINAL_BINDING", same(issuance["delivery_ref"], refs["fixed_capture"]) and same(issuance["origin_event_ref"], refs["fixed_original"]) and issuance["reviewer_id"] == RAW_REVIEWER and issuance["executor_id"] == ROOT_ACTOR and issuance["issuer_id"] == RAW_REVIEWER)
    for name in ("append_guard", "precheck_guard", "derive_guard"):
        observed = doc(name)
        require("ROOT_GUARD_CLOSED_" + name, observed["verification"] == "PASSED" and observed["closed"] is True and observed["retained_handles_count"] == 0 and observed["errors"] == [] and all(entry["closed"] is True for entry in observed["entries"]))
    audit_facts = {}
    for name, expected_chunk, expected_exit, publisher_name, publisher_key in (("append_audit", "bc9a81", 0, "commit", "receipt_ref"), ("derive_audit", "bc5257", 1, "derive", "result_ref")):
        audit = doc(name)
        original_key = "original_append" if name == "append_audit" else "original_derive"
        lines = raw(original_key).splitlines(keepends=True)
        require("ROOT_FIXED_THREE_LF_" + name, len(lines) == 3 and all(line.endswith(b"\n") for line in lines) and audit["original_line_sha256"] == [sha(line) for line in lines])
        header, call, result = [decode(line) for line in lines]
        require("ROOT_ACTUAL_AUTHENTICATED_CALL_PAIR_" + name, header["type"] == "session_meta" and header["payload"]["id"] == ROOT_THREAD and audit["Root_thread_id"] == ROOT_THREAD and audit["actor_id"] == ROOT_ACTOR and call["payload"]["type"] in ("custom_tool_call", "function_call") and result["payload"]["type"] in ("custom_tool_call_output", "function_call_output") and call["payload"]["call_id"] == result["payload"]["call_id"])
        require("ROOT_AUDIT_EXACT_RESULT_SHA_" + name, audit["binding_sha256"] == refs[publisher_name]["sha256"] and same(audit["original_capture_ref"], refs[original_key]))
        hosts = [item for item in docs(result["payload"]["output"]) if item.get("chunk_id") == expected_chunk]
        require("ROOT_EXACT_HOST_UNIQUE_" + name, len(hosts) == 1)
        host = hosts[0]
        require("ROOT_ACTUAL_OUTER_EXIT_" + name, type(host.get("exit_code")) is int and host["exit_code"] == expected_exit)
        output_lines = host["output"].splitlines()
        marker = "ROOT_ACTUAL_PYTHON_EXIT=" + str(expected_exit)
        require("ROOT_ACTUAL_PYTHON_EXIT_" + name, output_lines.count(marker) == 1)
        published = [decode(line) for line in output_lines if line.startswith("{")]
        matched = [item for item in published if publisher_key in item and same(item[publisher_key], refs[publisher_name])]
        require("ROOT_EXACT_TYPED_ARTIFACT_PUBLICATION_" + name, len(matched) == 1)
        if name == "append_audit":
            require("ROOT_PUBLICATION_CURRENT4_CAS", len(matched[0]["current4"]) == 4 and all(any(same(rr, refs[k]) for rr in matched[0]["current4"]) for k in ("cp", "ow", "ss", "cm")))
        else:
            require("ROOT_DERIVE_PUBLISHED_STAGE", matched[0]["stage"] == "derive")
        audit_facts[name] = {"chunk_id": expected_chunk, "actual_outer_exit": expected_exit, "actual_python_exit": expected_exit, "actual_native_exit": None, "actual_Mode_producer_exit": None, "original_ref": refs[original_key], "call_id": call["payload"]["call_id"], "call_timestamp": call["timestamp"], "result_timestamp": result["timestamp"]}
    require("DERIVE_CURRENT_FORMAL_SCHEMA_AND_CAS", derive["schema"] == "researchos.formal-case-index.v1" and derive["scope"] == "DERIVED_READ_ONLY_CURRENT_FORMAL_STATUS" and derive["bridge_CAS"]["status"] == "PASS" and derive["product_business_acceptance_created"] is False)
    require("DERIVE_PARTIAL_EXACT_TWO_OF42", derive["integrity"] == "PARTIAL" and derive["required_formal_cases"] == 42 and derive["formal_cases_accepted"] == 2 and derive["accepted_case_ids"] == ["A06", "C19"])
    selected = [row for row in derive["cases"] if row["case_id"] in ("A06", "C19")]
    require("DERIVE_W09_TWO_VALID_CASES", len(selected) == 2 and all(row["status"] == "VALID_ACCEPTED" and row["final_owner_task"] == "W09" and row["reasons"] == [] for row in selected))
    own = [row for row in derive["owners"] if row["task_id"] == "W09"]
    require("DERIVE_W09_OWNER_VALID_ACCEPTED", len(own) == 1 and own[0]["parent_status"] == "ACCEPTED" and own[0]["integrity"] == "VALID_ACCEPTED" and set(own[0]["accepted_case_ids"]) == {"A06", "C19"} and own[0]["reasons"] == [])
    require("PARTIAL_EXACT_W04_W07_REVALIDATION_CAUSES", len(derive["reasons"]) == 2 and {reason["task_id"] for reason in derive["reasons"]} == {"W04", "W07"} and all(reason["code"] == "NEEDS_REVALIDATION" for reason in derive["reasons"]))
    for key in ("ss", "Main_w09", "Main_case_index"):
        matches = [value for path, value in derive["input_hashes"].items() if ntpath.normcase(ntpath.normpath(path)) == identity(refs[key])]
        require("DERIVE_MAIN_AND_SS_CURRENT_PIN_" + key, matches == [refs[key]["sha256"]])
    for key in ("cp", "ow", "ss", "cm"):
        now = observed_ref(path_for(refs[key]))
        require("FINAL_READ_CAS_CURRENT4_" + key, same(now, refs[key]))
    draft = {"schema": "researchos.w09-ss-append-derived-cases-independent-review.v1", "decision": "ACCEPTED_W09_SS_APPEND_AND_DERIVED_CASES_IN_SCOPE", "reviewer_id": REVIEWER, "raw_backend": RAW_REVIEWER, "executor_id": ROOT_ACTOR, "ss_append_receipt_ref": refs["commit"], "derive_result_ref": refs["derive"], "precheck_result_ref": refs["precheck"], "prospective_owner_ref": refs["owner"], "owner_approval_ref": refs["owner_approval"], "ss_before_archive_ref": refs["before"], "ss_after_ref": refs["ss"], "published_capture_index_ref": refs["index"], "current4_refs": [refs[key] for key in ("cp", "ow", "ss", "cm")], "accepted_case_ids": ["A06", "C19"], "overall_integrity": "PARTIAL", "formal_case_count": 2, "required_formal_case_count": 42, "derived_case_rows": selected, "partial_reasons": derive["reasons"], "actual_root_exits": audit_facts, "overall_derive_actual_outer_exit": 1, "overall_derive_actual_python_exit": 1, "global_goal_complete": False, "review_scope": "POSTCOMMIT_SS_APPEND_AND_ALREADY_EXECUTED_DERIVATION_ONLY", "formal_review_or_check_or_derive_replayed": False, "Native_or_Mode_or_product_replayed": False, "Main_or_Canon_or_SS_written_by_reviewer": False, "checks": checks, "input_refs": list(unique.values()), "reviewed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
except BaseException as exc:
    primary = {"type": type(exc).__name__, "message": str(exc)}
finally:
    closure = guard.close()
    closure_ref = write_new("SourceGuard.closed.json", closure)
if primary is not None or closure.get("closed") is not True or closure.get("retained_handles_count") != 0 or closure.get("errors"):
    decision = {"schema": "researchos.w09-ss-append-derived-cases-independent-review.v1", "decision": "CHANGES_REQUIRED", "reviewer_id": REVIEWER, "raw_backend": RAW_REVIEWER, "primary_error": primary, "checks": checks, "SourceGuard_ref": closure_ref, "global_goal_complete": False, "product_replayed": False, "Canon_written": False}
    decision_ref = write_new("decision.json", decision)
    print(json.dumps({"decision_ref": decision_ref, "decision": "CHANGES_REQUIRED", "primary_error": primary, "SourceGuard_ref": closure_ref}, ensure_ascii=False))
    print("ROOT_PYTHON_EXIT=1")
    sys.exit(1)
draft["SourceGuard_ref"] = closure_ref
draft["SourceGuard_closed"] = True
draft["retained_handles_count"] = 0
draft["SourceGuard_errors"] = []
decision_ref = write_new("decision.json", draft)
print(json.dumps({"decision": draft["decision"], "decision_ref": decision_ref, "SourceGuard_ref": closure_ref, "checks_passed": len(checks), "accepted_case_ids": ["A06", "C19"], "overall_integrity": "PARTIAL", "formal_cases": "2/42", "actual_derive_outer_exit": 1, "actual_derive_python_exit": 1}, ensure_ascii=False))
print("ROOT_PYTHON_EXIT=0")
