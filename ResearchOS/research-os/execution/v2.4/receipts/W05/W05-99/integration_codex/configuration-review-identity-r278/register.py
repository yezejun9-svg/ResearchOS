import datetime
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p):
    return {"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 277 and ow["revision"] == 105 and len(cp["failure_counters"]) == 232
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
oldref = ref(BASE + "integration_codex/configuration-independent-review-r277/scope_registration.json")
assert oldref["sha256"] == "159c8066693557daceaf499e843130851b58ccfb660b8ff578a6f01e2f327a08"
oldscope = json.loads((ROOT / oldref["path"]).read_bytes())
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
clarification = {"schema": "researchos.root.independent-review-identity-correction.v1", "actor": "codex:/root", "at": now, "original_scope_ref": oldref, "correction": "Original Root declaration that Cmd did not author foundation5 was inaccurate. Cmd confirmed prior foundation5 authorship before any new program/test execution. Cmd is not config10/test1 author; its current static10/read-only observations may remain advisory, but cannot sign own foundation composition. No acceptance was issued. Original scope bytes preserved.", "new_reviewer": "codex:/root/w05_merge_review", "basis": "W05 reviewer did not author configuration10/test1/foundation5 and earlier independently reviewed immutable foundation5. P12 diagnostics have stopped with actual P1 and require different author repair; w05 can audit this independent schema branch.", "product_source_changes": 0, "actual_tests_by_cmd": 0, "formal_increment": 0}
save("identity_clarification.json", clarification)
newscope = dict(oldscope)
newscope.update(at=now, reviewer="codex:/root/w05_merge_review", original_scope_ref=oldref, identity_correction_ref=ref((OUT / "identity_clarification.json").relative_to(ROOT).as_posix()), review_policy="W05 reviewer did not author configuration10/test1/foundation5. Prior Cmd static10 work is advisory only; no Cmd tests or acceptance occurred. Final exact11 commit plus immutablefoundation5 current source/compile vectors and separate12gates required before nonself source acceptance; Main composition remains Root's later gate.")
save("scope_registration.json", newscope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
config = ow["card_path_bindings"]["W05-99"]["subtasks"]["host_configuration_upgrade_prerequisites"]
config["independent_reviewer_history"].append({"verifier": config["verifier"], "scope_ref": oldref, "identity_correction_ref": newscope["identity_correction_ref"], "state": "STOPPED_STATIC_ONLY_NO_EXECUTION_NO_ACCEPTANCE_FOUNDATION_SELF_AUTHOR_BOUNDARY"})
config.update(verifier=newscope["reviewer"], independent_source_review_scope_ref=scope_ref)
cp.update(revision=278, expected_previous_revision=277, updated_at=now, updated_by="codex:/root")
ow.update(revision=106, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "P12actualP1 internalMODELinventory omissions reproduced2cases with0models/sourceunchanged; guardfixproposal then Root causal author scope, originalhistory5held. Config11 finalfreeze then W05 nonauthor foundation+upgrade review; priorCmdstatic10advisory only (oldfoundation author), CP277 original declaration corrected in new immutable clarification before any execution/acceptance. Main23HOLD, F08/configure future scopes pending. All22parents/42CURRENT required."
cp["work_in_progress"].update(status="P12_ACTUAL_P1_GUARDFIX_SCOPE_PENDING_CONFIG11_NONAUTHOR_REVIEWER_CORRECTED", next_action=cp["next_command"], configuration_independent_source_review_scope_ref=scope_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "REVIEWER_PRIOR_FOUNDATION_AUTHORSHIP_CORRECTED_BEFORE_ANY_SOURCE_ACCEPTANCE", "scope_ref": scope_ref, "counter_unchanged": 232, "formal_increment": 0})
cp["evidence_index"].extend([scope_ref["path"], newscope["identity_correction_ref"]["path"]])
save("record.json", {"checkpoint": [277, 278], "ownership": [105, 106], "failure_origins": [232, 232], "scope_ref": scope_ref, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + ".root278.tmp")
    with temp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 278, "ownership": 106, "failure_origins": 232, "scope_ref": scope_ref, "formal_increment": 0}))
