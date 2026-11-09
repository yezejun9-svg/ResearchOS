"""Root-only exact3 scope transfer, preserving all historical authorities."""
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


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def ref(path, expected=None):
    path = ROOT / path
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected is not None:
        assert value == expected, (str(path), value)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": value}


def main():
    before = {p: p.read_bytes() for p in [CP, OWN, STATE, COMMANDS]}
    cp, own = json.loads(before[CP]), json.loads(before[OWN])
    assert cp["revision"] == 265 and own["revision"] == 93
    assert len(cp["failure_counters"]) == 170
    assert hashlib.sha256(before[STATE]).hexdigest() == "fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149"
    assert hashlib.sha256(before[COMMANDS]).hexdigest() == "b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert head == "4ba293847072069cd99154e5054f6ef4ae2b92e1"
    for path, raw in before.items():
        (OUT / (path.stem + ".original.json")).write_bytes(raw)
    review_ref = ref(BASE + "cli_read_interrupt_scope_review_codex/3dd10de3-d92f-4d2c-b31f-f130937dbf95/exact_scope_review.json", "476171e14a13b4043f53ca95d55b21563a7dc86683f0ef6b0885bd047de071e5")
    review = json.loads((ROOT / review_ref["path"]).read_bytes())
    assert review["decision"] == "NEEDS_FIX_SCOPE"
    proposal_ref = ref(BASE + "cli_read_interrupt_executor_codex/proposal-470a14015ba749c4a38f873795e55169/proposal.json", "0db18522d3b2f163ca73a630f60675f8406cc1c02470e54bc086e7c66e49ba80")
    foundation_review_ref = ref(BASE + "host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json", "3d817abd65d3a66e6741659927d4e796ac93b7e36184f582dee1daff3e1fcbc8")
    foundation_review = json.loads((ROOT / foundation_review_ref["path"]).read_bytes())
    assert foundation_review["decision"] == "SOURCE_READY_ISOLATED_FOUNDATION_MAIN_HOLD"
    paths = ["apps/cli/cli_stream.go", "apps/cli/cli_continuation.go", "apps/cli/cli_read_interrupt_test.go"]
    assert not (ROOT / paths[-1]).exists()
    source_before = [ref(path) for path in paths[:2]] + [{"path": paths[-1], "sha256": None, "expected_present": False}]
    subs = own["card_path_bindings"]["W05-99"]["subtasks"]
    assert not set(paths).intersection(subs["real_model_streaming"]["paths"])
    transfers = []
    for card, card_binding in own["card_path_bindings"].items():
        for name, binding in card_binding.get("subtasks", {}).items():
            hits = sorted(set(paths).intersection(binding.get("paths", [])))
            if hits:
                transfers.append({"card": card, "subtask": name, "owner": binding.get("owner"), "original_state": binding.get("state"), "paths": hits})
    assert {(x["card"], x["subtask"]) for x in transfers} == {("W18-02", "cli_restore_continuation"), ("W05-99", "cli_goal_follower"), ("W05-99", "durable_queue_control")}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    scope = {"schema": "researchos.root.cli-read-interrupt-exact3-scope.v1", "actor": "codex:/root", "registered_at": now, "owner": "codex:/root", "verifier": "codex:/root/w05_merge_review", "model": "gpt-6-astra", "reasoning_effort": "high", "base_head": head, "worktree": ".local/worktrees/codex-w0599-cli-read-interrupt", "branch": "work/codex-w0599-cli-read-interrupt", "original_exact2_proposal_ref": proposal_ref, "independent_exact2_needs_fix_ref": review_ref, "scope_revision": "Adopt independently recommended exact3 and every explicit ordering/control condition; original proposal and NEEDS_FIX_SCOPE remain immutable.", "exact_paths": paths, "source_before": source_before, "additional_path_boundary": "cli_continuation.go: retain cliReadContinuation compatibility wrapper, add private cliReadContinuationContext(parent,...), WithTimeout(parent,8s). Only status uses read context; preserve 2MiB/10pages/identity/projection/other callers.", "production_boundary": "Only status,/status read interruption. Local CLI INTERRUPTED_READ_ONLY/130, no public enum, no execution/cancellation completion claim. Single receiver/atomic observer state, context cancellation through every typed read/continuation/body; stop and join before return. Original active flow unchanged.", "required_ordering": review["required_ordering"], "required_tests": review["required_tests"], "protected": review["protected"], "transferred_historical_construction_bindings": transfers, "composition_gate": "Isolated implementation allowed. No source readiness/MAIN integration until final source freeze and independent current combined Go/JS/L01/L02 CLI qualification. No provider shared paths modified. Root later recaptures W04/W07.", "no_private_credentials_or_paid_api": True, "formal_increment": 0, "construction_parents": ["W04", "W05"]}
    (OUT / "scope_registration.json").write_bytes(encode(scope))
    scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
    for item in transfers:
        binding = own["card_path_bindings"][item["card"]]["subtasks"][item["subtask"]]
        binding.setdefault("historical_integrated_source_path_transfers", []).append({"paths": item["paths"], "new_owner": "codex:/root", "new_subtask": "W05-99/cli_read_interruption", "scope_ref": scope_ref, "old_evidence_and_other_paths_preserved": True, "transferred_at": now})
    subs["cli_read_interruption"] = {"owner": "codex:/root", "verifier": "codex:/root/w05_merge_review", "paths": paths, "worktree": scope["worktree"], "branch": scope["branch"], "base_commit": head, "state": "IN_PROGRESS_EXACT3_ISOLATED_COMPOSITION_FREEZE_REQUIRED", "scope_ref": scope_ref, "independent_scope_review_ref": review_ref, "receipt_namespace": BASE + "cli_read_interrupt_executor_codex/**", "model": "gpt-6-astra", "reasoning_effort": "high"}
    subs["host_configuration_foundation"].update(state="SOURCE_READY_ISOLATED_FOUNDATION_MAIN_HOLD", independent_source_review_ref=foundation_review_ref, verified_candidate_blobs=142)
    own.update(revision=94, amended_at=now, amended_by="codex:/root")
    old_counters = copy.deepcopy(cp["failure_counters"])
    additions = [
        {"origin_key": "W05-99/cli-read-interrupt/exact2-scope-missing-continuation-context", "attempts": 1, "retries_used": 0, "status": "INDEPENDENT_SCOPE_NEEDS_FIX_PRESERVED_EXACT3_REGISTERED", "evidence_ref": review_ref, "detail": review["findings"], "actual_test_exit": None},
        {"origin_key": "W05-99/root/deepseek-public-model-limit-web-timeout", "attempts": 2, "retries_used": 1, "status": "ACTUAL_READ_TIMEOUTS_PRESERVED_NATIVE_READ_SUCCEEDED", "evidence_ref": ref(BASE + "provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-native-read/observations.json", "72387e6e7bdcf0891751fb236c665c3a3ffe51be9cd7f74a54d089d9ff507048"), "detail": {"original_failed_refs": [ref(BASE + "provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-capture/capture.json"), ref(BASE + "provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-cached-success/capture.json")], "actual_results": "Both400Timeout; native curl actualexit0 exact23982byte official HTML archived. Failed files not successful content authority.", "private_paid_calls": 0}},
        {"origin_key": "W05-99/root/model-cost-host-runtime-path-query", "attempts": 1, "retries_used": 0, "status": "ACTUAL_READ_PATH_ERROR_PRESERVED", "evidence_ref": scope_ref, "detail": {"observed_tool_chunk": "142fc4", "missing_path": "internal/host/runtime_windows.go", "stderr": "system cannot find specified file; corrected rg --files found runtime_check_windows.go/model_credential.go", "actual_aggregate_exit": 0, "not_a_recreated_run": True}},
    ]
    assert not set(x["origin_key"] for x in additions).intersection(x["origin_key"] for x in old_counters)
    for item in additions:
        item.update(counter_reset=False, formal_increment=0)
    cp["failure_counters"].extend(additions)
    assert cp["failure_counters"][:170] == old_counters
    cp.update(revision=266, expected_previous_revision=265, head=head, updated_at=now, updated_by="codex:/root")
    for worker in cp["workers"]:
        if worker.get("slice_id") == "HOST_CONFIGURATION_FOUNDATION":
            worker.update(state="SOURCE_READY_ISOLATED_FOUNDATION_MAIN_HOLD", independent_source_review_ref=foundation_review_ref, verified_candidate_blobs=142)
    cp["workers"].append({"step_id": "W05-99", "slice_id": "CLI_READ_INTERRUPTION", "owner": "codex:/root", "verifier": "codex:/root/w05_merge_review", "worktree": scope["worktree"], "state": subs["cli_read_interruption"]["state"], "scope_ref": scope_ref})
    cp["note"] = "Root exact3 L02 status interruption scope adopts independent required continuation context/linearization/join controls; historical W18/W05 path owners explicitly transferred for these paths only. L04 independent65+4SQL PASS and142blobs SOURCE_READY_ISOLATED_FOUNDATION_MAIN_HOLD, not141 nor current-schema release ready. Go T08 original candidate remains NEEDS_FIX; exact3 repair tests in progress incl actual SDK semantic argument lanes. Provider9 proposal/new-model qualifications remain unaccepted. All170 prior origins preserved plus3=173; no formal/state/registry increment."
    cp["next_command"] = "Continue registered isolated L02 exact3 and T08 exact3 source repair, independent current source reviews; independently review provider9 scope then serialize overlapping Go paths after T08 integration. L04 SQL23 remains hold. Preserve all old UNKNOWN/failed evidence; current1case lastactual unchanged until Root finalsource W04/W07 recapture."
    cp["work_in_progress"].update(status="T08_EXACT3_REPAIR_L02_EXACT3_REGISTERED_L04_SOURCE_READY_ISOLATED_HOLD", main_source_head=head, next_action=cp["next_command"], cli_read_interruption_scope_ref=scope_ref, configuration_foundation_source_review_ref=foundation_review_ref)
    cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "L02_EXACT3_SCOPED_HISTORICAL_PATH_TRANSFER_AND_ISOLATED_L04_SOURCE_REVIEW", "scope_ref": scope_ref, "foundation_review_ref": foundation_review_ref, "failure_origins": [170, 173], "formal_increment": 0})
    for value in [scope_ref, review_ref, foundation_review_ref]:
        if value["path"] not in cp["evidence_index"]:
            cp["evidence_index"].append(value["path"])
    record = {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "actual_at": now, "checkpoint": [265, 266], "ownership": [93, 94], "failure_origins": [170, 173], "scope_ref": scope_ref, "foundation_review_ref": foundation_review_ref, "main_source_unchanged": True, "formal_increment": 0, "state_registry_unchanged": True}
    (OUT / "record.json").write_bytes(encode(record))
    for path, raw in before.items():
        assert path.read_bytes() == raw, ("FOREIGN_WRITE", str(path))
    for path, raw in [(CP, encode(cp)), (OWN, encode(own))]:
        temporary = path.with_name(path.name + ".root266.tmp")
        temporary.write_bytes(raw)
        assert path.read_bytes() == before[path]
        os.replace(temporary, path)
    assert STATE.read_bytes() == before[STATE] and COMMANDS.read_bytes() == before[COMMANDS]
    print(json.dumps({"checkpoint": 266, "ownership": 94, "failure_origins": 173, "scope_ref": scope_ref, "record_ref": ref((OUT / "record.json").relative_to(ROOT).as_posix()), "formal_increment": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
