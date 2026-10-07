import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
CP = ROOT / "execution/v2.4/checkpoint.json"
OW = ROOT / "execution/v2.4/path_ownership.json"
ST = ROOT / "execution/v2.4/step_state.json"
CM = ROOT / "execution/v2.4/commands.json"


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write(enc(value))


def ref(relative, expected=None):
    path = ROOT / relative
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected:
        assert value == expected, relative
    return {"path": relative, "sha256": value}


before = {path: path.read_bytes() for path in [CP, OW, ST, CM]}
cp, ow = json.loads(before[CP]), json.loads(before[OW])
assert cp["revision"] == 268 and ow["revision"] == 96 and len(cp["failure_counters"]) == 198
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "396287cc5427eb125aaedb8a2b7fadf63e6b9322"
for path, raw in before.items():
    with (OUT / (path.stem + ".original.json")).open("xb") as stream:
        stream.write(raw)
proposal_ref = ref(BASE + "provider_binding_executor_scope_codex/79c9c61c276a42e1962556af982dc51d/proposal.json", "107e1b7abf5c06aa5aae87c27be9f5102c0c4c806655eeed9554be66c08193bc")
review_ref = ref(BASE + "provider_binding_scope_review_codex/e350f920-2862-4dc3-906e-c6e1044e63ec/source_scope_review.json", "5cab5541af5d477f4e27ead0a5a408d75051b0eb56a0ce7ac2b62364cdc73727")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_SCOPE_READY_CONDITIONAL_REPAIRED_COMPOSITION_AND_LIVE_PLAN"
paths = [item["path"] for item in review["exact_source_scope"]]
assert len(paths) == len(set(paths)) == 9 and paths[-1] == "internal/domain/runtime_model_stream.go"
integration_ref = ref(BASE + "integration_codex/main-stream-source-integration-r268/result.json", "2a76e1bbd9e1264c0fe9a7f8269985be0586bf546839fe3cb7d35f6b9e3bb9ec")
integration = json.loads((ROOT / integration_ref["path"]).read_bytes())
assert integration["head"] == head and integration["actual_exit"] == 0 and not integration["build_source_drift"]
assert len(integration["changed_source_paths"]) == 20 and integration["builder"]["vendored_files_verified"] == 5083
resource_ref = ref(BASE + "vendor_resource_restore_independent_review_codex/cc65c5e5-9b17-4c0d-9add-e560b1850a09/review.json", "5e83c9aa66baab0e5a91b4feb40429e5d46cc031c7fa61433478699d30682ef9")
stream_ref = ref(BASE + "streaming_signed_zero_source_review_codex/4bb6828c-89ea-4a19-b0ed-e3b07da94b8a/source_review.json", "9f0035ba65341adacc98d00e6da220c239769a83c26475e262b2816868ee0d26")
budget_ref = ref(BASE + "provider_budget_resource_readonly_codex/budget-4d5e48bb6b764a34ac537990b10290f2/conclusion.json", "54ded5ab5926efcd754b92cf0a59ec4ad85daee4d428e0b76103c97f5d6eb4c6")
formal_ref = ref(BASE + "integration_codex/current-status-r269/formal-index.json")
formal = json.loads((ROOT / formal_ref["path"]).read_bytes())
assert formal["formal_cases_accepted"] == 0 and formal["accepted_case_ids"] == []
source_before = []
for relative in paths:
    path = ROOT / relative
    if path.is_file():
        source_before.append({"path": relative, "exists": True, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    else:
        assert relative in ["internal/domain/runtime_provider_binding_test.go", "internal/domain/runtime_provider_binding_windows_test.go", "adapters/runtime/mu/worker-provider-binding.test.mjs"]
        source_before.append({"path": relative, "exists": False, "sha256": None})
save("source_before.json", source_before)
source_ref = ref((OUT / "source_before.json").relative_to(ROOT).as_posix())
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
worktree = ".local/worktrees/codex-w0599-provider-binding"
assert not (ROOT / worktree).exists()
scope = {"schema": "researchos.root.provider-binding-exact9-source-scope.v1", "actor": "codex:/root", "registered_at": now,
         "owner": "codex:/root/command_queue_impl", "verifier": "codex:/root/w05_merge_review", "root": "codex:/root",
         "base_head": head, "worktree": worktree, "branch": "work/codex-w0599-provider-binding", "paths": paths,
         "source_before_ref": source_ref, "proposal_ref": proposal_ref, "review_ref": review_ref,
         "accepted_repaired_candidate_review_ref": stream_ref, "actual_main_integration_ref": integration_ref,
         "resource_recovery_review_ref": resource_ref, "budget_resource_ref": budget_ref,
         "exact_source_bounds": review["exact_source_scope"], "mandatory_implementation_conditions": review["mandatory_implementation_conditions"],
         "mandatory_sequence": review["mandatory_sequence"], "required_controls": review["required_controls"],
         "source_only_authority": "Fresh isolated exact9 implementation and P01-P12 actual FIXTURE controls on repaired integrated baseline; no paid or external model calls. Independent current MAIN tests remain pending and source-source composition must be current before further integration.",
         "live_gate": "B01_STRICT_UPPER_BOUND_NOT_ESTABLISHED_LIVE_ONLY_BLOCKED; estimates0.50/3.00 are not UPPER_BOUND or ACTUAL. Preserve actual_cost=null and existing original reservations/UNKNOWN; no retry/fallback/admission/registration/Host private activity.",
         "protected_unchanged": ["SDK code/version/manifest/locks", "build.mjs", "SQL0002/0022/isolated0023", "public schemas/API/CLI", "credential/vault/Host implementation", "old failure/raw/ZIP and unknown origin deletions", "Root shared canonical files"],
         "model": "gpt-6-astra", "reasoning_effort": "high", "model_reason": "Reuse existing actual SDK/queue architecture executor for cross-round original-authority and portable proof changes; no new user chat.",
         "receipt_namespace": BASE + "provider_binding_executor_codex/**", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
subs = ow["card_path_bindings"]["W05-99"]["subtasks"]
for key in ["real_model_streaming", "real_model_streaming_worker"]:
    sub = subs[key]
    overlaps = sorted(set(sub["paths"]) & set(paths))
    sub.setdefault("historical_path_transfers", []).append({"at": now, "paths": overlaps, "new_owner": scope["owner"], "scope_ref": scope_ref, "reason": "Reviewed frozen source integrated; old execution ownership is historical, next exact9 source writer isolated and exclusive."})
    sub.update(state="SOURCE_INTEGRATED_MAIN_COMPOSITION_TEST_PENDING", current_source_writer=False, main_integration_ref=integration_ref)
subs["vendor_fixed_asset_resource_recovery"].update(state="RESOURCE_RECOVERY_INDEPENDENTLY_VERIFIED_ALL5083_NO_RUNTIME_QUALIFICATION", independent_review_ref=resource_ref)
subs["provider_transport_reasoning_binding"] = {key: scope[key] for key in ["owner", "verifier", "root", "worktree", "branch", "paths", "source_before_ref", "receipt_namespace", "model", "reasoning_effort"]}
subs["provider_transport_reasoning_binding"].update(base_commit=head, state="REGISTERED_EXACT9_FIXTURE_ONLY_LIVE_B01_BLOCKED", scope_ref=scope_ref, proposal_ref=proposal_ref, independent_scope_review_ref=review_ref, source_policy="opencode-go-deepseek-v1", protected_unchanged=scope["protected_unchanged"], current_source_writer=True)
old = copy.deepcopy(cp["failure_counters"])
observations_ref = ref(BASE + "integration_codex/source-evidence-archive-r268/root-observations.json")
observations = json.loads((ROOT / observations_ref["path"]).read_bytes())["observations"]
save("tools-locator-observation.json", {"origin_key": "W05-99/root/r268-formal-tool-directory-locator", "tool_chunk": "8222c8", "actual_aggregate_exit": 1, "actual_attempts": 1, "failed_path": "tools", "corrected_module_path": "execution/v2.4/formal_case_index.py", "source_mutation": False, "product_test_executed": False})
tool_ref = ref((OUT / "tools-locator-observation.json").relative_to(ROOT).as_posix())
observations.append(json.loads((ROOT / tool_ref["path"]).read_bytes()))
for item in observations:
    assert item["origin_key"] not in {entry.get("origin_key") for entry in old}
    cp["failure_counters"].append({"origin_key": item["origin_key"], "attempts": 1, "retries_used": 0, "status": "ACTUAL_READ_ONLY_TOOL_ERROR_PRESERVED", "evidence_ref": tool_ref if item["origin_key"].endswith("directory-locator") else observations_ref, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 201 and cp["failure_counters"][:198] == old
cp.update(revision=269, expected_previous_revision=268, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=97, amended_at=now, amended_by="codex:/root")
cp["current_effective_formal_status"] = {"derived_from_ref": formal_ref, "actual_at": now, "formal_cases_accepted": 0, "accepted_case_ids": [], "historical_parent_registrations": cp["parent_tasks_accepted"], "effective_parent_count_not_inferred": True}
cp["next_command"] = "Independent current MAIN T08 tests/closed compiled vector; implement isolated exact9 provider FIXTURE P01-P12 (LIVE B01 blocked). Root rebase L02 exact4 on reviewed stream composition/newbundle and freeze full CLI closure for independent review; F08 read-only proposal pending scope review. Revalidate W04/W07 after final source freeze; never claim complete before22/42 effective."
cp["note"] = "Exact6 fixed Gitblob recovery independently verified5083allmatch; archived963publicfiles and integrated frozen cumulative JS/Go20source files. MAIN real Mu build5083verified/closedinputs stable with freshbundle2a8e7013; independent MAIN composition tests pending. Fresh provider9 scope exclusively isolated FIXTURE-only. Current actual formal derive0/42 after source change; old acceptances/old failure evidence retained unchanged.198old origins+3readonlylocatorerrors=201, no reset. Other11old deletions retained."
cp["work_in_progress"].update(status="T08_MAIN_SOURCE_INTEGRATED_CURRENT_TEST_PENDING_PROVIDER9_FIXTURE_SCOPED_L02_EXACT4_CONTINUES", next_action=cp["next_command"], main_stream_integration_ref=integration_ref, vendor_resource_recovery_review_ref=resource_ref, provider_binding_scope_ref=scope_ref, current_formal_index_ref=formal_ref, live_budget_resource_ref=budget_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "ACTUAL_MAIN_STREAM_SOURCE_INTEGRATION_VENDOR_REBUILD_AND_EXACT9_PROVIDER_FIXTURE_SCOPE", "scope_ref": scope_ref, "integration_ref": integration_ref, "current_formal_index_ref": formal_ref, "failure_origins": [198,201], "formal_increment": 0})
for item in [scope_ref, source_ref, integration_ref, resource_ref, budget_ref, formal_ref, observations_ref, tool_ref]:
    if item["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(item["path"])
cp["dirty_paths"] = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=ROOT).decode().splitlines()
save("record.json", {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "at": now, "checkpoint": [268,269], "ownership": [96,97], "failure_origins": [198,201], "scope_ref": scope_ref, "main_integration_ref": integration_ref, "state_registry_unchanged": True, "formal_cases_current": 0, "formal_increment": 0})
assert all(path.read_bytes() == raw for path,raw in before.items())
for path, value in [(CP,cp),(OW,ow)]:
    temporary = path.with_name(path.name + ".root269.tmp")
    with temporary.open("xb") as stream:
        stream.write(enc(value))
    assert path.read_bytes() == before[path]
    os.replace(temporary,path)
assert ST.read_bytes() == before[ST] and CM.read_bytes() == before[CM]
print(json.dumps({"checkpoint":269,"ownership":97,"failure_origins":201,"scope_ref":scope_ref,"record_ref":ref((OUT/"record.json").relative_to(ROOT).as_posix()),"formal_increment":0}))
