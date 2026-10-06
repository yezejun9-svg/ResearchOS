"""Root CAS: preserve candidate failures and authorize bounded T08 repair."""
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
GO = ROOT / ".local/worktrees/codex-w0599-model-stream"
FOUNDATION = ROOT / ".local/worktrees/codex-w0599-host-config"
CP = ROOT / "execution/v2.4/checkpoint.json"
OWN = ROOT / "execution/v2.4/path_ownership.json"
STATE = ROOT / "execution/v2.4/step_state.json"
COMMANDS = ROOT / "execution/v2.4/commands.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def ref(path, expected=None):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    actual = digest(raw)
    if expected is not None:
        assert actual == expected, (str(path), actual)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": actual}


def snapshot(path, name, expected):
    original = ref(path, expected)
    target = OUT / name
    assert not target.exists()
    target.write_bytes(path.read_bytes())
    return {"original_ref": original, "snapshot_ref": ref(target, expected)}


def main():
    before = {p: p.read_bytes() for p in [CP, OWN, STATE, COMMANDS]}
    assert digest(before[CP]) == "f63e78ccd5f192f8afa256a8202fea8f495761c4fd394a4b01d6caa4b649220d"
    assert digest(before[OWN]) == "37adb680cc235f3d1bcba65e598dbfdfcfb4a9b1bcd6601c94854f1917f03168"
    assert digest(before[STATE]) == "fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149"
    assert digest(before[COMMANDS]) == "b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129"
    cp, own = json.loads(before[CP]), json.loads(before[OWN])
    assert cp["revision"] == 264 and own["revision"] == 92
    assert len(cp["failure_counters"]) == 153
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert head == "6e9ac45bff1c76fac37f0462a051412f53ab11d8"
    for path, raw in before.items():
        (OUT / (path.stem + ".original.json")).write_bytes(raw)

    review_path = ROOT / (BASE + "streaming_combined_source_review_codex/f67e12e4-175f-4fd9-9442-8bdf1c0ecf5e/source_review.json")
    review_ref = ref(review_path, "8111e8cf0e599b11343410c3493f619068b4c5c5fbbbb3340ecf61bf754b0d7f")
    review = json.loads(review_path.read_bytes())
    assert review["decision"] == "NEEDS_FIX"
    assert review["candidate_commit"] == "0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837"
    assert review["formal_acceptance_delta"] == 0
    review_fail_ref = ref(ROOT / review["failure_origins_ref"]["path"], review["failure_origins_ref"]["sha256"])
    review_failures = json.loads((ROOT / review_fail_ref["path"]).read_bytes())
    go_dir = GO / (BASE + "model_stream_executor_codex/candidate-b8938f84655849b9847611dbf3440442")
    go_handoff = snapshot(go_dir / "handoff.json", "go-handoff.original.json", "c8ca8acc2889e09403a2a11c5d75170c36ff3247e4763af3311980e0de8a4128")
    go_failures = snapshot(go_dir / "failure_origins.json", "go-failures.original.json", "7218e7597c1d9b54cad87b8e1d8c7825f38513c6973e31c57c5950da170c2d11")
    foundation_dir = FOUNDATION / (BASE + "host_configuration_foundation_executor_codex/implementation-1cc1b20e27534da8a78e7350fa533ea3")
    foundation_handoff = snapshot(foundation_dir / "handoff.json", "foundation-handoff.original.json", "ed6abcef4fc05cc1f2fb8e809a9ed4897051c64496505269e3e84374f7b64f54")
    foundation_failures = snapshot(foundation_dir / "failure_history.json", "foundation-failures.original.json", "62ef20c6840ae8edbbcc241eeaa5cc1a04fef46d9ad5d8819abb8bbc84b223b2")

    root_errors = [
        {"id": "independent-agent-spawn-thread-limit", "kind": "ACTUAL_COLLABORATION_TOOL_FAILURE", "observed_tool": "collaboration.spawn_agent", "actual_result": "collab spawn failed: agent thread limit reached", "exit_code": None, "no_agent_created": True, "resolution": "Reused existing SourceParent as independent L04 reviewer; no new chat or source write."},
        {"id": "read-new-cli-test-as-existing", "kind": "ACTUAL_ROOT_READ_TOOL_ERROR", "actual_tool_chunk": "542ba4", "actual_exit": 1, "error": "FileNotFoundError", "path": "apps/cli/cli_read_interrupt_test.go", "resolution": "This is a proposed new file, currently absent. No product or canonical write in failed read. Future proposal explicitly marks expected_present=false."},
    ]
    (OUT / "root-tool-failures.json").write_bytes(encode(root_errors))
    root_fail_ref = ref(OUT / "root-tool-failures.json")
    old_counters = copy.deepcopy(cp["failure_counters"])

    def append(origin, evidence, detail, attempts=1, status="ACTUAL_FAILURE_PRESERVED"):
        cp["failure_counters"].append({"origin_key": origin, "attempts": attempts, "retries_used": 0, "status": status, "evidence_ref": evidence, "detail": detail, "counter_reset": False, "formal_increment": 0})

    for row in json.loads((OUT / "go-failures.original.json").read_bytes())["origins"]:
        append("W05-99/model-stream-go-candidate/" + row["id"], go_failures["snapshot_ref"], row)
    for row in json.loads((OUT / "foundation-failures.original.json").read_bytes())["new_origins"]:
        append("W05-99/configuration-foundation/" + row["id"], foundation_failures["snapshot_ref"], row)
    append("W05-99/model-stream-independent/semantic-reasoning-secret-reassembly", review_fail_ref, {"finding_id": "W05-STREAM-SR-01", "candidate": review["candidate_commit"], "actual_red_probes": review_failures["own_expected_red_probes"], "independent_source_review_ref": review_ref, "original_candidate_immutable": True}, attempts=2, status="P1_SOURCE_BLOCKER_REPAIR_REQUIRED")
    for i, row in enumerate(review_failures["own_audit_errors"], 1):
        append("W05-99/model-stream-independent/audit-tooling-" + str(i), review_fail_ref, row)
    for row in root_errors:
        append("W05-99/root/" + row["id"], root_fail_ref, row)
    assert cp["failure_counters"][:153] == old_counters
    new_keys = [x["origin_key"] for x in cp["failure_counters"][153:]]
    assert len(new_keys) == 17 and len(set(new_keys)) == 17
    assert not set(new_keys).intersection(x["origin_key"] for x in old_counters)

    paths = ["internal/domain/runtime_model_stream.go", "internal/domain/runtime_model_stream_test.go", "apps/cli/cli_model_stream_integration_windows_test.go"]
    source_before = [ref(GO / path) for path in paths]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=GO).decode().strip() == review["candidate_commit"]
    assert not subprocess.check_output(["git", "status", "--porcelain", "-uno"], cwd=GO).strip()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    registration = {"schema": "researchos.root.model-stream-quarantine-repair-scope.v1", "actor": "codex:/root", "registered_at": now, "owner": "codex:/root/sources_parent_impl", "verifier": "codex:/root/w05_merge_review", "worktree": str(GO), "branch": "work/codex-w0599-model-stream", "base_candidate": review["candidate_commit"], "review_ref": review_ref, "exact_paths": paths, "source_before": source_before, "independently_reviewed_boundary": review["findings"][0]["minimum_fix_scope"], "controls": "SDK-selected aliases and detail merge semantics, alias priority, escaped/read/event/UTF8 splits, harmless prefix progress, terminal handling and real SDK->broker->SQLite->CLI no-secret negative. Rerun affected quarantine/causal/cancel/restore/verifier and full CLI after final exact source freeze.", "protected": "Preserve old candidate/receipts/JS2/SDK/schema/public protocol/migrations/original raw bytes/finite ceilings. No blanket rejection of thinking, whole-stream benign EOF buffering, secret reads or paid calls. Extra source path requires separate exact amendment.", "original_open_gates": review["declared_open_product_gates"], "formal_increment": 0, "current_formal_cases_last_actual": 1, "construction_parents": ["W04", "W05"], "main_source_unchanged": head}
    (OUT / "scope_registration.json").write_bytes(encode(registration))
    scope_ref = ref(OUT / "scope_registration.json")
    subs = own["card_path_bindings"]["W05-99"]["subtasks"]
    subs["real_model_streaming"].update(state="NEEDS_FIX_BOUNDED_T08_EXACT3_REPAIR_REGISTERED", candidate_commit=review["candidate_commit"], independent_source_review_ref=review_ref, quarantine_repair_scope_ref=scope_ref)
    subs["host_configuration_foundation"].update(state="CANDIDATE_EXACT5_INDEPENDENT_REVIEW_PENDING_MAIN_HOLD", candidate_commit="fef0ee2d56351e74ceed11b0b37d3f87e9c83494", candidate_handoff_ref=foundation_handoff["snapshot_ref"])
    own.update(revision=93, amended_at=now, amended_by="codex:/root")
    for worker in cp["workers"]:
        if worker.get("slice_id") == "REAL_MODEL_STREAMING":
            worker.update(state=subs["real_model_streaming"]["state"], source_review_ref=review_ref, quarantine_repair_scope_ref=scope_ref)
        if worker.get("slice_id") == "HOST_CONFIGURATION_FOUNDATION":
            worker.update(state=subs["host_configuration_foundation"]["state"], candidate_commit="fef0ee2d56351e74ceed11b0b37d3f87e9c83494", candidate_handoff_ref=foundation_handoff["snapshot_ref"])
    cp.update(revision=265, expected_previous_revision=264, head=head, updated_at=now, updated_by="codex:/root")
    cp["note"] = "Independent Go18+JS2+L01 review NEEDS_FIX: P1 SDK semantic reasoning aliases/details reconstruct synthetic protected secret. Original444blobs/39053vectors and265+188PASS remain truthful but not source-ready. Root authorizes exact3 bounded quarantine repair with frozen SDK/JS2/raw ceilings. L04 isolated exact5 candidate65PASS remains MAIN HOLD pending independent source/public22->23/typed backup/safety; original cancel ACK-final trigger conflict remains OPEN. All153 prior origins byte-preserved plus17 new archived origins=170; no registry/state/parent/formal increment. New OpenCode Go access verified, trusted runtime binding scope still read-only."
    cp["next_command"] = "Finish independent isolated L04 source review; implement/review registered exact3 T08 semantic quarantine repair, then integrate exact JS2+repairedGo only if independently source-ready. Independently scope OpenCode Go eight-path policy after repaired source integration; preserve all original failures/UNKNOWN and W04/W07 recapture until final source stability."
    cp["work_in_progress"].update(status="GO_SOURCE_NEEDS_FIX_T08_EXACT3_REGISTERED_L04_ISOLATED_CANDIDATE", next_action=cp["next_command"], main_source_head=head, quarantine_repair_scope_ref=scope_ref, model_stream_source_review_ref=review_ref, configuration_foundation_candidate_handoff_ref=foundation_handoff["snapshot_ref"])
    cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "SOURCE_NEEDS_FIX_T08_BOUNDED_REPAIR_AND_ORIGINAL_CANDIDATE_FAILURE_PRESERVATION", "review_ref": review_ref, "scope_ref": scope_ref, "failure_origins": [153, 170], "formal_increment": 0})
    for value in [review_ref, review_fail_ref, scope_ref, go_handoff["snapshot_ref"], go_failures["snapshot_ref"], foundation_handoff["snapshot_ref"], foundation_failures["snapshot_ref"], root_fail_ref]:
        if value["path"] not in cp["evidence_index"]:
            cp["evidence_index"].append(value["path"])
    record = {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "actual_at": now, "checkpoint": [264, 265], "ownership": [92, 93], "failure_origins": [153, 170], "main_head_unchanged": head, "source_review_ref": review_ref, "repair_scope_ref": scope_ref, "isolated_foundation_handoff_ref": foundation_handoff["snapshot_ref"], "old_state_registry_unchanged": True, "formal_increment": 0, "next_action": cp["next_command"]}
    (OUT / "record.json").write_bytes(encode(record))
    for path, raw in before.items():
        assert path.read_bytes() == raw, ("FOREIGN_WRITE", str(path))
    for path, raw in [(CP, encode(cp)), (OWN, encode(own))]:
        temporary = path.with_name(path.name + ".root265.tmp")
        temporary.write_bytes(raw)
        assert path.read_bytes() == before[path]
        os.replace(temporary, path)
    assert STATE.read_bytes() == before[STATE] and COMMANDS.read_bytes() == before[COMMANDS]
    print(json.dumps({"checkpoint": 265, "ownership": 93, "failure_origins": 170, "scope_ref": scope_ref, "record_ref": ref(OUT / "record.json"), "formal_increment": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
