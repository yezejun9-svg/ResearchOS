"""Root-only checkpoint CAS; no product acceptance or registry mutation."""
import copy
import datetime
import hashlib
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path(r"D:\作品集\ResearchOS\research-os")
OUT = pathlib.Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
CP = ROOT / "execution/v2.4/checkpoint.json"
OWN = ROOT / "execution/v2.4/path_ownership.json"
STATE = ROOT / "execution/v2.4/step_state.json"
COMMANDS = ROOT / "execution/v2.4/commands.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def ref(name, expected=None):
    path = ROOT / name
    raw = path.read_bytes()
    value = digest(raw)
    if expected is not None:
        assert value == expected, (name, value)
    return {"path": name, "sha256": value}


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return result.stdout


def main():
    before = {p: p.read_bytes() for p in [CP, OWN, STATE, COMMANDS]}
    cp = json.loads(before[CP])
    own = json.loads(before[OWN])
    assert cp["revision"] == 261 and own["revision"] == 90
    assert len(cp["failure_counters"]) == 134
    assert digest(before[CP]) == "eced82721ac7cc143e20b117e1bc4b6c42bebda6c8d6d72790d922c12ff96f0f"
    assert digest(before[OWN]) == "b6c9f542ead482fd2dd023cda959e435e59d108627d0864fad40b7b75c257c97"
    assert digest(before[STATE]) == "fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149"
    assert digest(before[COMMANDS]) == "b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129"
    head = git("rev-parse", "HEAD").decode().strip()
    assert head == "5378be91e77c289f996f080c2740729d263a6a52"
    for path, raw in before.items():
        (OUT / (path.stem + ".original.json")).write_bytes(raw)

    http_review = ref(BASE + "independent_cli_http_source_review/3c350a21-0f55-4821-a414-9b1a8c5c8d01/source_review.json", "005b880289f30e3245c5cb0af096391375b55bf50218a2167dad0ac1b83025fd")
    http_integration = ref(BASE + "integration_codex/cli-http-source-integration-78930a4b2e9343f8b5df4511b06d5b4f/result.json", "d0d319860969cd5d06d5a4e4931309c490a45c9185393fae3f27136cf636bbbc")
    integration = json.loads((ROOT / http_integration["path"]).read_bytes())
    assert integration["actual_exit"] == 0 and integration["verified_candidate_files"] == 33
    assert integration["integrated_head"] == head
    for path, expected in {"apps/cli/cli_v2.go": "072afeb88f1a2f028df1c99b55735b3c583c729e86b2a53b9e60e889e6a2c304", "apps/cli/cli_http_status_test.go": "240d43b2a03eb990600ca80b880a7d7071218c8725965e152cdb8c4edf57d0c0"}.items():
        ref(path, expected)
    js_review = ref(BASE + "streaming_worker_source_review_codex/78b593d8-b803-4718-bc97-e2302a6c3b57/source_review.json", "86bef488d74e2aaa2be5b0ec783d9e991ec4af3f5bee55a56055f23c947dd6ba")
    js = json.loads((ROOT / js_review["path"]).read_bytes())
    assert js["decision"] == "SOURCE_READY_JS_ONLY" and js["formal_acceptance_delta"] == 0
    original_js = ROOT / ".local/worktrees/codex-w0599-model-stream-worker/execution/v2.4/receipts/W05/W05-99/model_stream_worker_executor_codex/implementation-6f05ada907be4eb8b01ac21fe0e10455/failure_origins.json"
    raw_js = original_js.read_bytes()
    assert digest(raw_js) == "8eeaec1ebeeed5cfd6aa6a4f2f6518ec11f574ab2a639f4fccfe9493a1152a02"
    (OUT / "js-failure-origins.original.json").write_bytes(raw_js)
    js_fail_ref = ref(str((OUT / "js-failure-origins.original.json").relative_to(ROOT)).replace("\\", "/"))
    failures = json.loads(raw_js)["new_origins"]
    assert len(failures) == 6
    current_ref = ref(BASE + "integration_codex/current-status-e6b27de1d7b8496a87d40b7cba166344/formal-index.json")
    current = json.loads((ROOT / current_ref["path"]).read_bytes())
    assert current["integrity"] == "PARTIAL" and current["accepted_case_ids"] == ["A05"]

    old_counters = copy.deepcopy(cp["failure_counters"])
    cp["failure_counters"].append({"origin_key": "W05-99/L01-independent-audit-tooling-keyerror", "attempts": 1, "retries_used": 0, "status": "ACTUAL_REVIEW_TOOL_ERROR_PRESERVED", "evidence_ref": http_review, "detail": {"classification": "REVIEW_TOOL_ERROR_NOT_PRODUCT", "error": "First audit.py assumed outer driver stdout_sha256; actual KeyError before replay. Original script retained, v2 validates exact manifest and subordinate invocations; independently focused39 pass."}, "counter_reset": False, "formal_increment": 0})
    inspection = {"kind": "OBSERVED_ROOT_TOOL_RESULT", "tool_chunk": "458ca6", "actual_exit": 1, "error": "FileNotFoundError", "path": BASE + "integration_codex/current-status-d366de82047f4da9b0e11395dc4a4272/invocation.json", "cause": "Root inspection used generic invocation.json instead of actual task-packet.invocation.json and looked for subtasks one level too high.", "resolution": "Actual rg discovery and corrected read chunk151710/3eb53f/e2dcc6; no product, canonical or registry write occurred in failed inspection.", "original_tool_output_available_in_chat": True, "not_a_recreated_command_run": True}
    (OUT / "root-inspection-tool-error.json").write_bytes(encode(inspection))
    cp["failure_counters"].append({"origin_key": "W05-99/root-inspection-invocation-locator", "attempts": 1, "retries_used": 0, "status": "ACTUAL_READ_TOOL_ERROR_PRESERVED", "evidence_ref": ref(str((OUT / "root-inspection-tool-error.json").relative_to(ROOT)).replace("\\", "/")), "detail": inspection, "counter_reset": False, "formal_increment": 0})
    for failure in failures:
        cp["failure_counters"].append({"origin_key": "W05-99/model-stream-worker/" + failure["id"], "attempts": 1, "retries_used": 0, "status": "ACTUAL_CANDIDATE_FAILURE_PRESERVED_SOURCE_JS_ONLY_REVIEWED", "evidence_ref": js_fail_ref, "detail": failure, "counter_reset": False, "formal_increment": 0})
    assert cp["failure_counters"][:134] == old_counters
    assert len({x["origin_key"] for x in cp["failure_counters"]}) == len(cp["failure_counters"])

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    subs = own["card_path_bindings"]["W05-99"]["subtasks"]
    subs["cli_http_classification"].update(state="SOURCE_READY_INTEGRATED_MAIN", candidate_commit=integration["candidate_commit"], integrated_head=head, independent_source_review_ref=http_review, integration_ref=http_integration)
    subs["real_model_streaming_worker"].update(state="SOURCE_READY_JS_ONLY_COMBINED_REVIEW_PENDING", candidate_commit=js["candidate_commit"], independent_source_review_ref=js_review)
    own.update(revision=91, amended_at=now, amended_by="codex:/root")
    for worker in cp["workers"]:
        if worker.get("slice_id") == "CLI_HTTP_CLASSIFICATION":
            worker.update(state="SOURCE_READY_INTEGRATED_MAIN", source_review_ref=http_review, integration_ref=http_integration)
        if worker.get("slice_id") == "REAL_MODEL_STREAMING_WORKER":
            worker.update(state="SOURCE_READY_JS_ONLY_COMBINED_REVIEW_PENDING", source_review_ref=js_review, candidate_commit=js["candidate_commit"])
    cp.update(revision=262, expected_previous_revision=261, head=head, updated_at=now, updated_by="codex:/root")
    cp["note"] = "L01 exact2 source independently SOURCE_READY and actually integrated33 blobs into Main5378. JS2 independently SOURCE_READY_JS_ONLY20/20 plus realEOF negative; Go19/SQLite/CLI/restore/quarantine composition remains in progress. All134 old origins retained plus6 original JS failures+L01 review tool error+Root read locator error=142. Registry39/state40cards/currentA05 unchanged; W04 source revalidation deferred until composed source and host configuration integrations stabilize."
    cp["next_command"] = "Finish/review Go19+immutable JS2/L01 actual causal streaming, cancel/restore/aux bounds/full regression; independently register nonoverlapping SQL23 configuration foundation scope before implementation. No formal increment; preserve old input/archive/unknown-effect restrictions."
    cp["work_in_progress"].update(owner="codex:/root/sources_parent_impl", status="W05_GO19_COMPOSITION_HTTP_INTEGRATED_JS_ONLY_READY", main_source_head=head, next_action=cp["next_command"], current_formal_index_ref=current_ref, formal_cases_current=1, accepted_card_count=40, historical_parent_registration_count=6)
    paths = [http_review["path"], http_integration["path"], js_review["path"], current_ref["path"], BASE + "host_configuration_readonly_codex/71bb78d0-c399-4414-8e50-3cc3a6fa90af/proposal.json", str((OUT / "record.json").relative_to(ROOT)).replace("\\", "/")]
    for path in paths:
        if path not in cp["evidence_index"]:
            cp["evidence_index"].append(path)
    cp["dirty_paths"] = sorted(x for x in git("diff", "--name-only", "-z").decode("utf-8").split("\0") if x)
    cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "L01_ACTUAL_SOURCE_INTEGRATION_JS_ONLY_INDEPENDENT_REVIEW_AND_FAILURE_PRESERVATION", "http_review_ref": http_review, "http_integration_ref": http_integration, "js_review_ref": js_review, "current_formal_index_ref": current_ref, "formal_increment": 0})
    record = {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "actual_at": now, "main_head_before_metadata": head, "checkpoint": [261, 262], "ownership": [90, 91], "failure_origins": [134, 142], "http_review_ref": http_review, "http_integration_ref": http_integration, "js_review_ref": js_review, "current_formal_index_ref": current_ref, "state_registry_unchanged": True, "formal_increment": 0, "accepted_cards": 40, "historical_registered_parents": 6, "current_formal_cases": 1, "next_action": cp["next_command"]}
    (OUT / "record.json").write_bytes(encode(record))
    updated = {CP: encode(cp), OWN: encode(own)}
    for path, raw in before.items():
        assert path.read_bytes() == raw, ("FOREIGN_WRITE", str(path))
    for path, raw in updated.items():
        assert path.read_bytes() == before[path]
        temporary = path.with_name(path.name + ".root262.tmp")
        temporary.write_bytes(raw)
        os.replace(temporary, path)
    assert STATE.read_bytes() == before[STATE] and COMMANDS.read_bytes() == before[COMMANDS]
    print(json.dumps({"checkpoint_revision": cp["revision"], "ownership_revision": own["revision"], "failure_origins": len(cp["failure_counters"]), "record_ref": ref(str((OUT / "record.json").relative_to(ROOT)).replace("\\", "/")), "formal_increment": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
