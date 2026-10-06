import copy
import datetime
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec/"
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
assert cp["revision"] == 281 and ow["revision"] == 109 and len(cp["failure_counters"]) == 237
review_ref = ref(BASE + "source_review.json", "8c58e9d9986da7103cb729a4e2b5fa54412b78319eda8d70a4e52c266c317ad3")
failure_ref = ref(BASE + "failure_origins.final.json", "b02f3c55d0bdd4d0dd59f073394c92353038cfea1690f05b977a653bf99a54e9")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_READY_EXACT11_WITH_IMMUTABLE_FOUNDATION5_AND_DECLARED_OPEN_GATES"
assert review["reviewer"] != review["executor"] != review["foundation_author"]
assert review["reviewer"] != review["foundation_author"]
assert review["independent_tests"]["unique_pass"] == 191 and not review["blocking_new_product_findings"]
assert len(review["source_rows"]) == 16 and len({r["path"] for r in review["source_rows"]}) == 16
for r in review["evidence"]:
    ref(r["path"], r["sha256"])
origins = json.loads((ROOT / failure_ref["path"]).read_bytes())["origins"]
assert len(origins) == 3 and origins[0]["already_imported"] and origins[0]["imported_checkpoint"] == 281
assert origins[1]["shell_exit"] == 0 and origins[2]["actual_exit"] == 1
for n in ["driver", "diagnosis", "correction"]:
    ref(origins[2][n]["path"], origins[2][n]["sha256"])
old = copy.deepcopy(cp["failure_counters"])
key = "W05-99/configuration-independent-protected-audit/" + origins[2]["driver"]["sha256"]
assert key not in {v.get("origin_key") for v in old}
cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": "ACTUAL_REVIEW_TOOL_ASSERTION_OLD10_PROTECTED_LIST_VS_AUTHORIZED11", "evidence_ref": failure_ref, "detail": origins[2], "raw_capture_limit": "Original tool chunk d46eb9; no manufactured native raw.", "counter_reset": False, "formal_increment": 0})
assert cp["failure_counters"][:237] == old and len(cp["failure_counters"]) == 238
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"evidence_ref": failure_ref, "observation": origins[1], "reason": "Actual outer shell exit0 with nonterminating readonly NotFound. Preserve exact fact; not a failed process invocation or product failure."})
archive_ref = ref("execution/v2.4/receipts/W05/W05-99/integration_codex/source-evidence-archive-r281/completed.json")
archive = json.loads((ROOT / archive_ref["path"]).read_bytes())
assert archive["head"] == "24072356acfd4c314c048b30a37334f9aef055d5" and not archive["source_integration"]
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.reviewed-source-main-integration-scope.v1", "actor": "codex:/root", "at": now, "parent": "W05", "card": "W05-99", "purpose": "Exact reviewed private configuration storage plus schema22-to23 upgrade/backup source composition; public host.configure/session runtime binding and formal gates remain OPEN.", "main_base": archive["head"], "candidate_commits_in_order": [review["foundation"], review["parent_source10"], review["candidate"]], "independent_source_review_ref": review_ref, "exact_source16": review["source_rows"], "integration": "Root serially cherry-picks only the three reviewed commits and their own immutable public evidence. Compare every Git blob and actual tracked source delta; current Main L02/stream preserved; original11 tracked deletions unstaged, source scopes not broadened, no source conflict resolver authorized without new evidence.", "verification": "Freeze actual Main source/Go dependencies/SQL/API/SDK locks/tool env/bundle/compiler and actual test executable vectors. One full CLI suite plus exact191 configuration/queue domain selector, full internal/api and targeted native Host backup/bootstrap/current-contract checks. Loopback/local fixture only, actual service models/paid calls0; provider9 held positives never invoked. Stop unexplained failure; retain raw and counter.", "main_schema23_source_integration_authorized": True, "main_configuration_product_acceptance": False, "inherited_open": ["Historical14 ActiveRecovery", "F08 cancel finalization", "Public host.configure/Session runtime binding", "Provider9 and LIVE qualification", "22 parents/42 current formal gates"], "models": 0, "paid_calls": 0, "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
for p, b in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(b)
for name in ["host_configuration_foundation", "host_configuration_upgrade_prerequisites"]:
    sub = ow["card_path_bindings"]["W05-99"]["subtasks"][name]
    sub.update(state="EXACT16_NONSELF_SOURCE_READY_ROOT_MAIN_COMPOSITION_AUTHORIZED_PENDING_ACTUAL", current_source_writer=False, independent_source_review_ref=review_ref, main_integration_scope_ref=scope_ref)
cp.update(revision=282, expected_previous_revision=281, head=archive["head"], updated_at=now, updated_by="codex:/root")
ow.update(revision=110, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(configuration_main_integration_scope_ref=scope_ref, configuration_nonself_source_review_ref=review_ref, status="ROOT_EXACT16_MAIN_SOURCE_COMPOSITION_AND_PROVIDER_P1_STOPPED_FOR_CAUSE_REVIEW")
cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
cp["next_command"] = "Root exact16 nonself-reviewed configuration Main integration/actual composition; ProviderP1 once source repair stopped on unmodifiedPREPARED earlyepoch false rejection, next narrow type cause review/Root scope required, originalhistory5held. F08 delta readonly design review, then full nonauthor review. All22parents/42current required."
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "CONFIGURATION_EXACT16_NONSELF_SOURCE_READY_MAIN_COMPOSITION_SCOPED", "review_ref": review_ref, "scope_ref": scope_ref, "failure_origins": [237, 238], "formal_increment": 0})
for v in [review_ref, failure_ref, scope_ref, archive_ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [281, 282], "ownership": [109, 110], "failure_origins": [237, 238], "scope_ref": scope_ref, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root282.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 282, "ownership": 110, "failure_origins": 238, "scope_ref": scope_ref, "formal_increment": 0}))
