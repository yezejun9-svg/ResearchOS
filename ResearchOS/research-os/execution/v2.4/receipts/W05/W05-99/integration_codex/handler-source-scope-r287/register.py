import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
WT = ROOT / ".local/worktrees/codex-w0599-host-configuration-handler"
BASE = "execution/v2.4/receipts/W05/W05-99/"
AUTHOR = BASE + "host_configuration_handler_scope_revision_codex/9d25ab2729444d0e96267dbc9c502430/"
REVIEW = BASE + "host_configuration_handler_scope_independent_review_codex/f1c35c71-265b-47c8-a85a-714839ca2e79/"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


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
assert (cp["revision"], ow["revision"], len(cp["failure_counters"])) == (286, 114, 246)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "2cdb0d43d5a600eef13c8f1735946a9adf52d079"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WT).decode().strip() == head
assert not subprocess.check_output(["git", "status", "--short", "--untracked-files=no"], cwd=WT)
proposal_ref = ref(AUTHOR + "scope_proposal.json", "3acc8acea045b287ad98340504c00c06c6e50921f33db8d666cf9790cc41893f")
review_ref = ref(REVIEW + "scope_review.json", "9e6c598fe2fdd4cd63c10012d1423806a5ba38041156a72087e93bf9894341e7")
proposal = json.loads((ROOT / proposal_ref["path"]).read_bytes())
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_SCOPE_READY" and proposal["exact_source_count"] == 27
manifest_ref = ref(AUTHOR + "manifest.final.json", "2cf73f8a2e85263f5e0134a2b4b7f3b00ed7bd2cf405ffea363ade3796669951")
manifest = json.loads((ROOT / manifest_ref["path"]).read_bytes())
assert len(manifest["files"]) == 242
for r in manifest["files"]:
    assert ref(r["path"]) == r
paths = copy.deepcopy(proposal["exact_scope"])
assert len(paths) == len({r["path"] for r in paths}) == 27
for r in paths:
    r["implementation_authorized"] = True
    if r["expected_absent"]:
        assert not (ROOT / r["path"]).exists() and not (WT / r["path"]).exists()
    else:
        expected = r["source_before"]
        assert ref(r["path"]) == expected
        assert hashlib.sha256((WT / r["path"]).read_bytes()).hexdigest() == expected["sha256"]
corrections = review["mandatory_same_path_corrections"]
assert [r["id"] for r in corrections] == ["S27-C01", "S27-C02"]
for correction in corrections:
    for path in correction["paths"]:
        item = next(r for r in paths if r["path"] == path)
        item["allowed_function_boundaries"].append(correction["required_scope_override"])
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.configuration-handler-source-scope.v1", "actor": "codex:/root", "executor": "codex:/root/sources_parent_impl", "verifier": "codex:/root/w05_merge_review", "card": "W05-99", "at": now, "base_commit": head, "worktree": str(WT), "branch": "work/codex-w0599-host-configuration-handler", "proposal_ref": proposal_ref, "independent_scope_review_ref": review_ref, "root_interface_decisions_ref": cp["work_in_progress"]["configuration_handler_interface_decisions_ref"], "exact_source_count": 27, "exact_source_scope": paths, "mandatory_same_path_corrections": corrections, "contract": {k: proposal[k] for k in ["transaction_order", "credential_policy", "authority_port_contract", "endpoint_policy", "session_provenance", "host_status_policy", "original_request_record", "atomic_rollback_fixture_causality"]}, "case_matrix_ref": ref(AUTHOR + "case_matrix30.json", "69ad2acdec4a21fc8ace97a3a17191632d7071073e1d25d475306fa00c7bb0ea"), "implementation_order": proposal["implementation_order"], "protected": proposal["protected_paths"], "shared_lease": "Single handler owner client_protocol.go and foundation2 plus backup identity-reader. No concurrent F08 or other writer to these paths; provider exact2 isolated and does not overlap. Old configuration upgrade WT remains unchanged.", "validation": {"required": "Actual typed default/scoped configuration, offline create, metadata-only real Windows Host/SID/OWNER, global new identities/exact old replay/derived Session, legal rejection public backup/restore/replay/rebackup, raw/header/hash corruption, atomic real probe1->0/replaycall1, true settlement and fences, stable bounded head+99 projection/full201 history, typed/legacy/PC01/Goal exact-head and qualification refusal. Preserve old successful branch and all original assertions.", "compile": "Compile relevant common domain/API/Host on non-Windows without executing foreign binary, plus actual Windows builds/tests. No new Windows tag or skip to suppress old common tests. Build current apps/control and ops/backup for relevant native upgrade/Host controls; do not use an older binary as current source proof.", "fixtures": "Explicit SYNTHETIC metadata unit ports are local development proof. New Windows tests separately use actual temporary local Host/SID/trusted authority. No copied/fabricated original creation/config journal or current profile as old provenance.", "freeze": "Before first authoritative validation and after/current freeze exact source27/full actual Go compile dependency closure/SQL/schema mirrors/SDK locks/tool binaries/environment/native executables/bundle. Hash raw closed public DBs/artifacts and record actual argv/exit/cause; no stale input vectors or self-acceptance.", "failures": "Preserve every actual failed invocation with origin key/input/current source; same failed input max2 automatic retries,3 rounds without preregistered progress stops only that branch. No changes to old counters/history/1811. New affected path outside27 needs precise Root-reviewed amendment before edits.", "external_provider_calls": 0, "paid_calls": 0, "private_vault_or_holdout_reads": 0, "user_credentials": "Never access resource DPAPI Host. New synthetic temporary credential test setup only; configure/status/binding path never opens/unprotects credentials. Any SDK/native model integration uses named local httptest fixtures and records actual loopback calls separately, not LIVE/provider qualification.", "legacy_open": "Historical14 ActiveRecovery/F08 oldACK1811/provider9 held/LIVE B01 remain OPEN; no automatic retry or qualification claim."}, "receipt_namespace": BASE + "host_configuration_handler_executor_codex/**", "acceptance": "Authorized isolated source implementation and bounded validation only. Executor reports, different nonauthor verifies, Root integrates current Main and recaptures required formal evidence. No parent/card/business acceptance increment.", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
prior = copy.deepcopy(cp["failure_counters"])
author_diag_ref = ref(AUTHOR + "lookup_diagnostics.json", "14603175bd736641c99b11acf526345a2290dcb1c559a8566859900560a570fb")
author_diag = json.loads((ROOT / author_diag_ref["path"]).read_bytes())
old_review_failure_ref = ref(BASE + "host_configuration_handler_scope_independent_review_codex/639403fd-baf9-41d5-8568-3568300f9e11/failure_origins.json", "a1abc6c61e470d0e1664a63875feda4708fd98af7555c0284d4393387a5a6dc4")
old_diag = json.loads((ROOT / old_review_failure_ref["path"]).read_bytes())["tooling_diagnostics"]
new_review_failure_ref = ref(REVIEW + "failure_origins.json", "c3a434f8bb5403673039f295a854ceb95c0adf173a25c3e18b75c00dc12ceca8")
new_diag = json.loads((ROOT / new_review_failure_ref["path"]).read_bytes())["origins"]
new = [("W05-99/handler-proposal/" + d["tool_chunk"], author_diag_ref, d) for d in author_diag["tool_read_diagnostics"] if d["exit"] == 1]
new += [("W05-99/handler-scope-review/5dfc88", old_review_failure_ref, old_diag[1]), ("W05-99/handler-scope-review/fedb85", new_review_failure_ref, new_diag[0])]
assert len(new) == 4
for key, evidence, detail in new:
    assert key not in {r.get("origin_key") for r in cp["failure_counters"]}
    cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": "ACTUAL_READONLY_TOOLING_EXIT1_TRANSCRIPT_ONLY_NOT_PRODUCT", "evidence_ref": evidence, "detail": detail, "counter_reset": False, "formal_increment": 0})
assert cp["failure_counters"][:246] == prior and len(cp["failure_counters"]) == 250
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"evidence_ref": old_review_failure_ref, "detail": old_diag[0], "reason": "Actual outer0, not a failed invocation; original tool transcript retained."})
cp.setdefault("pending_original_tool_diagnostic_reconciliation", []).append({"evidence_ref": author_diag_ref, "prior_tool_chunks": author_diag["prior_lookup_diagnostics_preserved"], "status": "Preserved original prior locators; actual outer exit not yet re-established here, do not invent count. Executor to provide existing receipt facts before later import."})
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
sub = {"owner": "codex:/root/sources_parent_impl", "verifier": "codex:/root/w05_merge_review", "root": "codex:/root", "model": "gpt-6-astra", "reasoning_effort": "high", "base_commit": head, "worktree": str(WT.relative_to(ROOT)).replace("\\", "/"), "branch": scope["branch"], "paths": [r["path"] for r in paths], "scope_ref": scope_ref, "independent_scope_review_ref": review_ref, "state": "EXACT27_HANDLER_AND_BOUNDED_OLD_FIXTURE_IMPLEMENTATION_AUTHORIZED", "current_source_writer": True, "receipt_namespace": scope["receipt_namespace"], "single_shared_protocol_lease": True}
ow["card_path_bindings"]["W05-99"]["subtasks"]["host_configuration_public_handlers"] = sub
cp.update(revision=287, expected_previous_revision=286, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=115, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(configuration_handler_scope_ref=scope_ref, configuration_handler_scope_state="EXACT27_NONSELF_SCOPE_READY_SOURCE_IMPLEMENTATION_AUTHORIZED", configuration_handler_worktree=sub["worktree"], configuration_handler_writer=sub["owner"], next_action="Implement authorized handler27 in isolated WT with protected old assertions and actual validation. Independently review newly reported provider typed-route64/source2, no implicit original9 or publicbackup qualification. F08 waits handler shared lease release.")
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "HANDLER_EXACT27_NONSELF_SCOPE_REGISTERED_TWO_SAMEPATH_CORRECTIONS_SINGLE_WRITER_LEASE", "scope_ref": scope_ref, "review_ref": review_ref, "failure_origins": [246, 250], "no_old_failure_reset": True, "formal_increment": 0})
for r in [scope_ref, review_ref, author_diag_ref, old_review_failure_ref, new_review_failure_ref]:
    if r["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(r["path"])
save("record.json", {"checkpoint": [286, 287], "ownership": [114, 115], "failure_origins": [246, 250], "source_scope": 27, "scope_ref": scope_ref, "formal_increment": 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root287.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 287, "ownership": 115, "failure_origins": 250, "scope_ref": scope_ref, "source_scope": 27, "formal_increment": 0}))
