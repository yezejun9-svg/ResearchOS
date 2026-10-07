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
PREFIX = BASE + "provider_binding_failure_chain_independent_review_codex/7c23e2f1-71af-4ac7-88f7-75c94710e327/"
CP, OW, ST, CM = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


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


before = {p: p.read_bytes() for p in [CP, OW, ST, CM]}
cp, ow = json.loads(before[CP]), json.loads(before[OW])
assert cp["revision"] == 273 and ow["revision"] == 101 and len(cp["failure_counters"]) == 220
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "1c7d7d8af69fbb523586e0e3a874cff5f17a3c00"
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
review = ref(PREFIX + "review.json", "ada2a621189ded1a5cbde312832648af15d97ddea7fc2ca6e8cb1928fed1572e")
proposal = ref(PREFIX + "zero_model_execution_proposal.json", "80253716998cc2bcc1d9d1bd8fc7384718ccfa1898a05a84e78595d0be68503e")
failure = ref(PREFIX + "failure_origins.json", "56cd25ef1adcea35670c7eced55482c680500b8265fc03bf58f4c148df13517d")
pp = json.loads((ROOT / proposal["path"]).read_bytes())
ff = json.loads((ROOT / failure["path"]).read_bytes())
assert pp["source_candidate"] == "976c8c9a6bdf8703475e02b79b77f4c5fab2d650" and pp["original_chain_failure_count"] == 5
assert len(pp["source9"]) == 9 and len(ff["new_tooling_origins"]) == 3 and ff["new_product_failures"] == []
old = copy.deepcopy(cp["failure_counters"])
for item in ff["new_tooling_origins"]:
    assert item["actual_exit"] == 1
    for k in ["invocation", "stdout", "stderr", "script"]:
        if k in item:
            v = item[k]
            p = Path(v["path"])
            assert p.resolve().is_relative_to(ROOT.resolve()) and hashlib.sha256(p.read_bytes()).hexdigest() == v["sha256"]
    key = "W05-99/provider9-independent-readonly/" + item["id"]
    assert key not in {v.get("origin_key") for v in old}
    cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": "READONLY_TOOLING_FAILURE_REPORTED_ORIGINAL_RAW_LIMITATIONS_RETAINED", "evidence_ref": failure, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 223 and cp["failure_counters"][:220] == old
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
names = ["TestProviderBindingActualSameRunToolHistory/final-fixture.sqlite", "TestProviderBindingAllOriginalStatesPortable_CONFIRMED/effect_prepared.sqlite", "TestProviderBindingAllOriginalStatesPortable_CONFIRMED/effect_started.sqlite", "TestProviderBindingAllOriginalStatesPortable_CONFIRMED/final-fixture.sqlite", "TestProviderBindingAllOriginalStatesPortable_UNKNOWN/final-fixture.sqlite", "TestProviderBindingAllOriginalStatesPortable_NOT_APPLIED/final-fixture.sqlite"]
dbs = {}
for name in names:
    matches = [(p, v) for p, v in pp["plan"]["input_database_refs"].items() if p.endswith("/" + name)]
    assert len(matches) == 1
    p, v = matches[0]
    dbs[BASE + "provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63/" + p] = v
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.independent-execution-scope.v1", "state": "AUTHORIZED_ZERO_MODEL_CANDIDATE_ONLY_DIAGNOSTIC_NOT_SOURCE_ACCEPTANCE", "actor": "codex:/root", "executor": "codex:/root/w05_merge_review", "at": now, "project_id": "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", "parent": "W05", "card": "W05-99", "proposal_ref": proposal, "readonly_review_ref": review, "source_candidate": pp["source_candidate"], "source9": pp["source9"], "main_comparison_only": head, "configuration23": "EXCLUDED_ISOLATED_MAIN_HOLD", "allowed_writes": ["new isolated candidate checkout/cache", "execution/v2.4/receipts/W05/W05-99/provider_binding_zero_model_adjudication_codex/<new-uuid>/** receipt-owned test overlay/driver/binary and copied corruption fixtures only"], "product_source_writes": 0, "original_database_refs": dbs, "budget": {"fixtures": 6, "maximum_internal_cases": 18, "maximum_public_positive_cases": 6, "additional_public_corruption_cases": 0, "model_calls": 0, "paid_calls": 0, "worker_starts": 0, "automatic_retries": 0}, "controls": pp["plan"]["controls"], "freeze": pp["preexecution_freeze"], "zero_model_proof": pp["zero_model_proof"], "fixed_combinations": ["remove original dispatch and provider_transport", "remove admission.profile_ref and admission.profile.model_config.provider_policy and provider_transport"], "preserve": {"history_chain": "W05-99/provider9-original-history-refusal", "history_failed_invocations": 5, "counter_reset": False, "author_held_tests_remain_held": pp["held_positives_remain_held"], "author_retry_authorized": False, "public_private_resource_reads": 0, "old_receipts_immutable": True}, "stop": pp["stop"], "decision": "Record exact internal versus public refusal layers. Unexpected acceptance or unrelated prerequisite failure stops dependent lane; retain immutable actual raw. No repair/rerun/held-positive execution without distinct Root causal scope. No SOURCE_READY, LIVE or formal increment from this diagnostic.", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
sub.update(readonly_failure_chain_review_ref=review, zero_model_independent_scope_ref=scope_ref, zero_model_scope_state=scope["state"], author_retry_authorized=False)
cp.update(revision=274, expected_previous_revision=273, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=102, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "Execute only registered independent candidate976 zero-model P12 controls against six sealed public DB copies; source9 unchanged/noSQL23/noCLI qualification, original-history5 held, first unexpected accept/prerequisite failure stops lane. Main L02 current234PASS0skip; schema23 isolated12gates currentfreeze/nonself beforeMain. F08 readonly pending23. Root alone canonical CAS; all22parents/42CURRENT required."
cp["note"] = "P9 read-only audit445blobs/source9 stable; currentqualificationHELD, originalmodel-history5 not resumed. Registered candidate-only zero-model6fixtures max18internal/6publicpositive controls, no additional syntheticpublic corruption.220prefix+3distinct readonlyaudittoolingorigins=223, originalraw limitations explicit. Prior9providerorigins not recounted. Main CLI234PASS no formal qualification."
cp["work_in_progress"].update(status="P9_INDEPENDENT_ZERO_MODEL_DIAGNOSTIC_REGISTERED_SCHEMA23_ISOLATED_MAINCLI_VALIDATED", next_action=cp["next_command"], provider_binding_readonly_review_ref=review, provider_binding_zero_model_scope_ref=scope_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "P9_ZERO_MODEL_SIX_PUBLIC_FIXTURES_DIAGNOSTIC_REGISTERED_ORIGINAL_CHAIN5_PRESERVED", "scope_ref": scope_ref, "failure_origins": [220, 223], "formal_increment": 0})
for v in [review, proposal, failure, scope_ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [273, 274], "ownership": [101, 102], "failure_origins": [220, 223], "scope_ref": scope_ref, "history_chain_failure_count": 5, "counter_reset": False, "formal_increment": 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, value in [(CP, cp), (OW, ow)]:
    tmp = p.with_name(p.name + ".root274.tmp")
    with tmp.open("xb") as f:
        f.write(enc(value))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert ST.read_bytes() == before[ST] and CM.read_bytes() == before[CM]
print(json.dumps({"checkpoint": 274, "ownership": 102, "failure_origins": 223, "scope_ref": scope_ref, "formal_increment": 0}))
