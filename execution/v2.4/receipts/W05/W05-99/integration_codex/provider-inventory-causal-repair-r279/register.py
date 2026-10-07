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
P = BASE + "provider_inventory_repair_scope_readonly_codex/939895be3999443788f92f0012bfbd2b/"
I = BASE + "provider_binding_zero_model_adjudication_codex/d7f95235-03e1-464f-b3b0-374ca7394fda/"
WT = ROOT / ".local/worktrees/codex-w0599-provider-binding"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p, expected=None):
    raw = (ROOT / p).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if expected:
        assert h == expected, p
    return {"path": p, "sha256": h, "bytes": len(raw)}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 278 and ow["revision"] == 106 and len(cp["failure_counters"]) == 232
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "26e1043751c989d4e6016a76f113e343c9e38382"
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
review = ref(I + "review.json", "5909a180bd55c0ce46864832f2287fbd8a68fd988d9463709670ac0ee129e68d")
failure = ref(I + "failure_origins.final.json", "f3736edfec0211ea2273debebbb180c34a989b4e4016919b3bd5ce05fc2fd929")
proposal = ref(P + "scope_proposal.json", "a40bd6e2ab2d0f3fc651afad145998b296781ef3ef1be6b569d2a250417fda09")
clarification = ref(P + "causal_guard_clarification.json", "dd69f97435c7ce30f612925a1a350eaf668a34fbdd53c746c80debed2cfb1b76")
pp, cc, ff, rr = [json.loads((ROOT / r["path"]).read_bytes()) for r in [proposal, clarification, failure, review]]
assert rr["executed"]["internal_cases"] == 2 and rr["executed"]["public_positive_cases"] == 0 and rr["executed"]["model_calls"] == 0
assert len(ff["entries"]) == ff["new_product_origins"] == 1 and ff["original_history_counter"] == 5
old = copy.deepcopy(cp["failure_counters"])
item = ff["entries"][0]
for n in ["invocation", "stdout", "stderr", "actual", "closed_database"]:
    p = Path(item[n]["path"])
    assert p.resolve().is_relative_to(ROOT.resolve())
    assert hashlib.sha256(p.read_bytes()).hexdigest() == item[n]["sha256"]
assert item["actual_exit"] == 1
key = "W05-99/P9-P12-SR01/" + item["invocation"]["sha256"]
assert key not in {v.get("origin_key") for v in old}
cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": "ACTUAL_P1_INTERNAL_ORIGINAL_MODEL_INVENTORY_UNEXPECTED_ACCEPT", "evidence_ref": failure, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 233 and cp["failure_counters"][:232] == old
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
for p in pp["exact_proposed_paths"]:
    assert hashlib.sha256((WT / p["path"]).read_bytes()).hexdigest() == p["sha256"]
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WT).decode().strip() == "02bc9ccee834a38c3d78ddaae3ea7fce0cae76ac"
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.causal-source-repair-scope.v1", "actor": "codex:/root", "executor": "codex:/root/command_queue_impl", "verifier": "codex:/root/w05_merge_review", "at": now, "parent": "W05", "card": "W05-99", "issue": "P9-P12-SR01", "original_candidate": pp["frozen_candidate"], "receipt_only_base": "02bc9ccee834a38c3d78ddaae3ea7fce0cae76ac", "worktree": ".local/worktrees/codex-w0599-provider-binding", "proposal_ref": proposal, "clarification_ref": clarification, "independent_p1_review_ref": review, "failed_origin_ref": failure, "exact_paths": pp["exact_proposed_paths"], "source_bounds": "Exactly2 already-owned provider files: original-effect classifier/provenance helper and matching newzero-model tests only. Other7provider files, wire/history prompt/UA/affinity, SQL/API/CLI/SDK/backups/currentMain/Canonicals unchanged. No missing-source reconstruction or schema24/F08 changes.", "classification": cc["original_join_contract"], "immutability_limits": cc["immutability_and_limits"], "controls": cc["bounded_execution_after_root_registration"]["controls"], "validation": {"author_attempts": 1, "fixture_db_reads": "Only copies of sealed original public C10 sixDB inputs and sealed P12 red mutation, hash originals before/after; explicit SYNTHETIC_NOT_PRODUCT legacy controls allowed", "new_original_history_snapshots": 0, "model_calls": 0, "worker_starts": 0, "paid_calls": 0, "http_calls": 0, "held_positive_tests": "Both original held tests remain stopped; no SDK native model regression or qualification driver invoked", "maximum_zero_model_control_cases": 64, "public_local_backup_optional": "At most6 unchanged CreateBackup/RestoreBackup/rebackup positive chains and6 corrupted CreateBackup refusal controls with syntheticlocal key/workspace mapping only, no private resources/HTTP. Preserve exact earlier rejection layer; never label lower-layer error as new semantic or public RestoreBackup proof. First unexpected reject stops lane. No forged archive alteration authorized.", "freeze": "Actual source9+exact2diff/full Go dependency/SQL/API/SDK/tool/env/overlay/testbinary/bundle vectors before firstcase and after/current. Existing old427manifest and recorded617inputs not substituted for current. Original P12 red executable/raw/closed DB immutable; run exact red copy against newfrozen binary once then remaining controls only if proper rejection.", "stop": "First unexpected accept/reject/missing temporal provenance stops that branch with complete raw and closed DB. No automatic second repair, latest RuntimeRegistration/timestamp/whitelist fallback or current Session/head scan. Root decides any separate recovery. Unprovable genuine legacy branch is an explicit compatibility blocker."}, "history": {"original_model_history_failed_invocations": 5, "original_author_held_positive_tests": True, "new_independent_zero_model_issue_failed_invocations": 1, "counter_reset": False, "new_input_is_causal_source_repair": True}, "qualification": "Author execution report only, nonself replay/currentcomposition required before source acceptance. Neither C10 heldhistorical pass nor newzero-model success grants provider native/LIVE or W05/42 acceptance.", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
sub.update(state="ACTUAL_P12_P1_SOURCE_READY_REFUSED_EXACT2_ONCE_ZERO_MODEL_CAUSAL_REPAIR_AUTHORIZED", current_source_writer=True, p12_independent_p1_review_ref=review, p12_failed_origin_ref=failure, p12_causal_repair_scope_ref=scope_ref, author_retry_authorized=False)
cp["failure_chains"]["W05-99/P9-P12-SR01"] = {"actual_failed_invocations": 1, "failed_origin_ref": failure, "repair_scope_ref": scope_ref, "status": "ONCE_CAUSAL_ZERO_MODEL_SOURCE_REPAIR_AUTHORIZED_ORIGINAL_INPUT_AND_FAILURE_RETAINED", "counter_reset": False}
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"source_ref": proposal, "observations": pp["tool_diagnostics"], "reason": "Read-only proposal transcript errors no saved original raw/precise individualexit; preserved without fabricated execution or ambiguous counts."})
cp.update(revision=279, expected_previous_revision=278, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=107, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "P12actualP1 oneorigin imported232to233; Cmd exact2 once zero-model causalvalidator repair with original6closedDB/redmutation/currentfrozenbinary, first unexpected accept/reject stop, originalmodelhistory5held. Config11 frozenc82f/125ea/foundationfef0 nonauthorW05 actualsource12gatesreview, originalnewtestargfailure pendingsealedimport once. Main23 and provider sourceHOLD untilindependentcurrentcomposition. F08/configure onlyfuture14 proposals; all22parents/42CURRENT required."
cp["note"] = "OriginalP12 only2internalcases reproducedPREPARED missingdispatch+transport nil/emptyinventory in2validators, publicrestore NOTtested;233 includes original232prefix+oneP1 semanticfail. Exact2causalrepairlimit1 authorattempt/no modelworkerpaidHTTP/originalheld positives. Classification must use positive originalimmutable Run/epoch/revision-bound lineage, never missingmarker->legacy. Runtimebindings/plans update-only triggers notdeletionproof explicitly noted. Config11 current191PASS sourceunaccepted untilW05 nonauthor actualreview."
cp["work_in_progress"].update(status="P12_ACTUAL_P1_ONCE_EXACT2_ZERO_MODEL_REPAIR_CONFIG11_NONAUTHOR_REPLAY", next_action=cp["next_command"], provider_inventory_causal_repair_scope_ref=scope_ref, provider_zero_model_independent_p1_ref=review)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "P12_ACTUAL_P1_IMPORTED_AND_EXACT2_ZERO_MODEL_CAUSAL_REPAIR_REGISTERED", "scope_ref": scope_ref, "failure_origins": [232, 233], "original_model_history5_held": True, "formal_increment": 0})
for v in [review, failure, proposal, clarification, scope_ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [278, 279], "ownership": [106, 107], "failure_origins": [232, 233], "scope_ref": scope_ref, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root279.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 279, "ownership": 107, "failure_origins": 233, "scope_ref": scope_ref, "formal_increment": 0}))
