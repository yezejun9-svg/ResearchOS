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
    digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if expected:
        assert digest == expected, relative
    return {"path": relative, "sha256": digest}


before = {path: path.read_bytes() for path in [CP, OW, ST, CM]}
cp, ow = json.loads(before[CP]), json.loads(before[OW])
assert cp["revision"] == 269 and ow["revision"] == 97
assert len(cp["failure_counters"]) == 201
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "396287cc5427eb125aaedb8a2b7fadf63e6b9322"
for path, raw in before.items():
    with (OUT / (path.stem + ".original.json")).open("xb") as stream:
        stream.write(raw)
review_ref = ref(BASE + "host_configuration_upgrade_scope_review_codex/2c7bb855-7562-41b6-8c8e-5456f9fc81dc/review.json", "beb79cec5f61ed838f6a4e9e47e76e5662bb76f36d7fdb66c3d78a3ed6f9aea3")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_SCOPE_READY_SCHEMA23_PREREQUISITES_ONLY"
assert review["base_head"] == head
foundation_commit = "fef0ee2d56351e74ceed11b0b37d3f87e9c83494"
assert review["foundation_commit"] == foundation_commit
paths = review["exact_existing_paths"] + review["exact_new_paths"]
assert len(paths) == len(set(paths)) == 8
assert len(review["mandatory_completion_gates"]) == 12
foundation_ref = ref(BASE + "host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json", "3d817abd65d3a66e6741659927d4e796ac93b7e36184f582dee1daff3e1fcbc8")
main_review_ref = ref(BASE + "main_stream_composition_independent_review_codex/c22da050-5fd2-4394-932c-5a5534360295/review.json", "085e491b938b4789b45e459848bea930336b4adff3d79abd3637316164ca15c6")
main_review = json.loads((ROOT / main_review_ref["path"]).read_bytes())
assert main_review["decision"] == "CURRENT_MAIN_STREAM_COMPOSITION_VERIFIED_FIXTURE_ONLY_WITH_OPEN_PRODUCT_GATES"
assert main_review["main_head"] == head and main_review["formal_acceptance_delta"] == 0
rebase_ref = ref(BASE + "cli_read_interrupt_executor_codex/composition-rebase-r269/result.json")
rebase = json.loads((ROOT / rebase_ref["path"]).read_bytes())
assert rebase["actual_exit"] == 0 and rebase["cli_exact4_unchanged"]
focused_ref = ref(BASE + "cli_read_interrupt_executor_codex/implementation-20261006-r266/closure-7b651b5cfbb34df2ad7145c4ee5ae273/result.json")
focused = json.loads((ROOT / focused_ref["path"]).read_bytes())
assert focused["actual_exit"] == 0 and not focused["source_drift"]
assert focused["assertion_counts"] == {"pass": 40, "fail": 0, "skip": 0}
timeout_result_ref = ref(BASE + "cli_read_interrupt_executor_codex/implementation-20261006-r266/closure-c99a5908d47845a19616a173f1751c35/result.json")
timeout_invocation_ref = ref(BASE + "cli_read_interrupt_executor_codex/implementation-20261006-r266/closure-c99a5908d47845a19616a173f1751c35/test.invocation.json")
timeout_analysis_ref = ref(BASE + "cli_read_interrupt_executor_codex/implementation-20261006-r266/full-cli-timeout-analysis-r269.json")
timeout = json.loads((ROOT / timeout_result_ref["path"]).read_bytes())
assert timeout["actual_exit"] == 1 and not timeout["source_drift"]
source_before = []
for relative in paths:
    path = ROOT / relative
    if relative in review["exact_existing_paths"]:
        assert path.is_file()
        source_before.append({"path": relative, "exists": True, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    else:
        assert not path.exists()
        source_before.append({"path": relative, "exists": False, "sha256": None})
save("source_before.json", source_before)
source_ref = ref((OUT / "source_before.json").relative_to(ROOT).as_posix())
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
worktree = ".local/worktrees/codex-w0599-host-configuration-upgrade"
assert not (ROOT / worktree).exists()
scope = {"schema": "researchos.root.configuration-upgrade-exact8-source-scope.v1", "actor": "codex:/root", "registered_at": now,
         "owner": "codex:/root/sources_parent_impl", "verifier": "codex:/root/w05_merge_review", "root": "codex:/root",
         "base_head": head, "worktree": worktree, "branch": "work/codex-w0599-host-configuration-upgrade", "paths": paths,
         "source_before_ref": source_ref, "independent_scope_review_ref": review_ref,
         "immutable_foundation_commit": foundation_commit, "foundation_source_review_ref": foundation_ref,
         "foundation_composition_authority": "Compose exact immutable foundation5 Git blobs and its reviewed sealed receipts in the fresh isolated worktree; no changes to those5 files, no MAIN SQL23 migration.",
         "current_main_stream_composition_review_ref": main_review_ref,
         "exact_bounds": review["exact_bounds"], "mandatory_completion_gates": review["mandatory_completion_gates"], "limits": review["limits"],
         "source_only_authority": "Fresh isolated exact8 prerequisites for exactly22to23: actual public backup/restore/upgrade, typed inventories, domain pre-DDL forward schema refusal and real Windows old-writer lock controls. All12 gates and independent final review required before any MAIN integration.",
         "protected_unchanged": ["foundation5 immutable source", "SQL0001..0023 and reserved future0024 absent", "backup_queue_upgrade.go/backup_recovery.go/backup_command_queue.go", "API/CLI/SDK/runtime provider/credential Host", "Root shared canonical files and previous evidence/deletions"],
         "main_gate": "FOUNDATION_AND_PREREQUISITES_MAIN_HOLD_UNTIL_ALL12_GATES_AND_CURRENT_COMPOSITION_INDEPENDENTLY_VERIFIED; F08/host.configure/LIVE/formal unchanged.",
         "model": "gpt-6-astra", "reasoning_effort": "high", "model_reason": "Reuse existing source/backup executor with exact independent scope and preserved historical evidence.",
         "receipt_namespace": BASE + "host_configuration_upgrade_executor_codex/**", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
subs = ow["card_path_bindings"]["W05-99"]["subtasks"]
for key in ["durable_queue_control", "fixed_queue_upgrade"]:
    sub = subs[key]
    overlaps = sorted(set(sub["paths"]) & set(paths))
    assert overlaps
    sub.setdefault("historical_path_transfers", []).append({"at": now, "paths": overlaps, "new_owner": scope["owner"], "scope_ref": scope_ref, "reason": "Previously integrated immutable source is historical; exact8 new source writer exclusively isolated."})
for key in ["real_model_streaming", "real_model_streaming_worker"]:
    subs[key].update(state="SOURCE_INTEGRATED_CURRENT_MAIN_COMPOSITION_INDEPENDENTLY_VERIFIED_FIXTURE_ONLY", current_source_writer=False, current_main_composition_review_ref=main_review_ref)
subs["host_configuration_upgrade_prerequisites"] = {key: scope[key] for key in ["owner", "verifier", "root", "worktree", "branch", "paths", "source_before_ref", "receipt_namespace", "model", "reasoning_effort"]}
subs["host_configuration_upgrade_prerequisites"].update(base_commit=head, state="REGISTERED_EXACT8_SCHEMA23_PREREQUISITES_ISOLATED_MAIN_HOLD", scope_ref=scope_ref, independent_scope_review_ref=review_ref, immutable_foundation_commit=foundation_commit, protected_unchanged=scope["protected_unchanged"], current_source_writer=True)
subs["cli_read_interruption"].update(current_composition_head=rebase["head"], current_composition_rebase_ref=rebase_ref, current_focused_result_ref=focused_ref, state="EXACT4_FOCUSED40_PASS_FULL480_PENDING_SOURCE_UNACCEPTED")
observations = [
    {"origin_key": "W05-99/root/r269-cli-current-composition-whole-package-180-timeout", "actual_exit": 1, "actual_attempts": 1, "status": "INCOMPLETE_PACKAGE_TIMEOUT_PRESERVED", "result_ref": timeout_result_ref, "invocation_ref": timeout_invocation_ref, "analysis_ref": timeout_analysis_ref, "completed_assertions": 109, "test_level_fail_records": 0, "qualification": "Unaccepted incomplete full package; bounded current480s runner is a separately retained execution, not overwritten retry."},
    {"origin_key": "W05-99/root/r270-scope-review-path-locator", "tool_chunk": "b0dd45", "actual_aggregate_exit": 0, "actual_error": "PowerShell Get-Content path-not-found", "actual_attempts": 1, "failed_path": "execution/receipts/W05-99/host_configuration_upgrade_scope_review_codex/2c7bb855-7562-41b6-8c8e-5456f9fc81dc/review.json", "corrected_path": review_ref["path"], "source_mutation": False, "product_test_executed": False, "qualification": "Read-only locator error retained despite shell aggregate0; corrected discovery9d9953 and successful read9a92b1."}
]
save("root_observations.json", {"schema": "researchos.root.actual-observations.v1", "at": now, "observations": observations})
observations_ref = ref((OUT / "root_observations.json").relative_to(ROOT).as_posix())
old = copy.deepcopy(cp["failure_counters"])
for item in observations:
    assert item["origin_key"] not in {entry.get("origin_key") for entry in old}
    cp["failure_counters"].append({"origin_key": item["origin_key"], "attempts": 1, "retries_used": 0, "status": item.get("status", "ACTUAL_READ_ONLY_TOOL_ERROR_PRESERVED"), "evidence_ref": observations_ref, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 203 and cp["failure_counters"][:201] == old
cp.update(revision=270, expected_previous_revision=269, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=98, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "Finish L02 exact4 current composition fullCLI480 closed-input test then frozen independent review; implement provider exact9 FIXTURE P01-P12 (LIVE B01 blocked) and schema23 prerequisites exact8+immutable foundation5 isolated all12gates. Root alone archives/CAS/integrates after nonself reviews. Revalidate W04/W07 at final source freeze;22parents/42CURRENT required."
cp["note"] = "Current MAIN independent SDK20/core286/CLI194 allPASS and closed inputs stable; composition remains FIXTURE-only with F08/P9/LIVE gates open. New exact8 schema23 prerequisites isolated only, immutable foundation5 composed there, no SQL24 creation and MAIN schema22 retained. L02 latestfocused40PASS/current39061inputs stable, original180s fulltimeout incomplete109 retained, new480s full pending.201originalfailureorigins preserved+2actualRootobservations=203, no reset; other11old deletions retained. Current0/42formal; stale nested1 corrected without altering formal state."
cp["work_in_progress"].update(status="CURRENT_MAIN_STREAM_FIXTURE_VERIFIED_PROVIDER9_SCHEMA23_PREREQ8_ISOLATED_L02_FULL_PENDING", next_action=cp["next_command"], main_source_head=head, formal_cases_current=0, current_main_stream_composition_review_ref=main_review_ref, host_configuration_upgrade_prerequisites_scope_ref=scope_ref, cli_read_current_composition_ref=rebase_ref, cli_read_current_focused_ref=focused_ref, cli_read_incomplete_full_timeout_ref=timeout_result_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "CURRENT_MAIN_INDEPENDENT_COMPOSITION_ADOPTED_AND_EXACT8_SCHEMA23_PREREQUISITES_SCOPE_REGISTERED", "scope_ref": scope_ref, "current_main_review_ref": main_review_ref, "failure_origins": [201,203], "formal_increment": 0})
for item in [scope_ref, source_ref, review_ref, foundation_ref, main_review_ref, rebase_ref, focused_ref, timeout_result_ref, timeout_invocation_ref, timeout_analysis_ref, observations_ref]:
    if item["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(item["path"])
cp["dirty_paths"] = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=ROOT).decode().splitlines()
save("record.json", {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "at": now, "checkpoint": [269,270], "ownership": [97,98], "failure_origins": [201,203], "scope_ref": scope_ref, "main_review_ref": main_review_ref, "state_registry_unchanged": True, "formal_cases_current": 0, "formal_increment": 0})
assert all(path.read_bytes() == raw for path,raw in before.items())
for path, value in [(CP,cp),(OW,ow)]:
    temporary = path.with_name(path.name + ".root270.tmp")
    with temporary.open("xb") as stream:
        stream.write(enc(value))
    assert path.read_bytes() == before[path]
    os.replace(temporary,path)
assert ST.read_bytes() == before[ST] and CM.read_bytes() == before[CM]
print(json.dumps({"checkpoint":270,"ownership":98,"failure_origins":203,"scope_ref":scope_ref,"record_ref":ref((OUT/"record.json").relative_to(ROOT).as_posix()),"formal_increment":0}))
