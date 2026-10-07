import copy
import datetime
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/provider-inventory-causal-repair-r279/scope_registration.json"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p):
    raw = p.read_bytes()
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 279 and ow["revision"] == 107 and len(cp["failure_counters"]) == 233
assert ref(OLD)["sha256"] == "86902da3eb7775d2f0726fffa256bf598c1715d89f977b50afb59a1cb6c169c2"
original = json.loads(OLD.read_bytes())
corrected = copy.deepcopy(original)
bad = "Existing old427manifest and recorded617inputs not substituted for current."
good = "Original manifests or recorded input vectors do not substitute for the complete actual current source/dependency/tool/bundle/test executable vectors."
assert corrected["validation"]["freeze"].count(bad) == 1
corrected["validation"]["freeze"] = corrected["validation"]["freeze"].replace(bad, good)
check = copy.deepcopy(corrected)
check["validation"]["freeze"] = original["validation"]["freeze"]
assert check == original
save("scope_registration.corrected.json", corrected)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
save("scope_clarification.json", {"schema": "researchos.root.scope-accuracy-clarification.v1", "at": now, "actor": "codex:/root", "original_ref": ref(OLD), "corrected_scope_ref": ref(OUT / "scope_registration.corrected.json"), "reason": "Root wrote two unverified input counts (427/617). They are withdrawn; no numerical historical count is asserted by this clarification.", "only_field_changed": "validation.freeze one sentence", "exact_source_scope_and_execution_limits_unchanged": True, "original_record_immutable": True, "source_acceptance": False, "formal_increment": 0})
scope_ref = ref(OUT / "scope_registration.corrected.json")
clarification_ref = ref(OUT / "scope_clarification.json")
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
origins = copy.deepcopy(cp["failure_counters"])
# The original tool console is retained by the conversation. No unavailable raw
# bytes are reconstructed or represented as a captured execution receipt.
save("root_locator_failure_observation.json", {"schema": "researchos.transcript-observation.v1", "actor": "codex:/root", "tool_chunk_id": "ea83cf", "actual_exit": 1, "commands": ["Get-ChildItem -LiteralPath D:/作品集/ResearchOS/research-os/integration_codex/provider-inventory-causal-repair-r279", "Get-Content -LiteralPath D:/作品集/ResearchOS/research-os/integration_codex/provider-inventory-causal-repair-r279/scope_registration.json -Raw"], "observed_error": "Both paths do not exist: the actual directory is under execution/v2.4/receipts/W05/W05-99/integration_codex.", "raw_captured": False, "raw_limit": "Original output exists in tool transcript; this is an explicit observation, not fabricated original raw.", "product_tests_executed": 0, "mutations": 0, "counter_reset": False})
failure_ref = ref(OUT / "root_locator_failure_observation.json")
key = "W05-99/Root/locator/ea83cf"
assert key not in {v.get("origin_key") for v in origins}
cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": "ACTUAL_READONLY_LOCATOR_COMMAND_EXIT1_TRANSCRIPT_ONLY", "evidence_ref": failure_ref, "counter_reset": False, "formal_increment": 0})
assert cp["failure_counters"][:233] == origins and len(cp["failure_counters"]) == 234
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
assert sub["p12_causal_repair_scope_ref"] == ref(OLD)
sub.update(p12_causal_repair_scope_ref=scope_ref, p12_scope_accuracy_clarification_ref=clarification_ref)
cp["failure_chains"]["W05-99/P9-P12-SR01"]["repair_scope_ref"] = scope_ref
cp["work_in_progress"]["provider_inventory_causal_repair_scope_ref"] = scope_ref
cp.update(revision=280, expected_previous_revision=279, updated_at=now, updated_by="codex:/root")
ow.update(revision=108, amended_at=now, amended_by="codex:/root")
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "ROOT_SCOPE_UNVERIFIED_COUNTS_WITHDRAWN_ORIGINAL_PRESERVED", "original_scope_ref": ref(OLD), "scope_ref": scope_ref, "clarification_ref": clarification_ref, "failure_origins": [233, 234], "failure_added": "One actual readonly Root locator invocation; accuracy correction is not a test failure.", "original_model_history5_held": True, "formal_increment": 0})
for v in [scope_ref, clarification_ref, failure_ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [279, 280], "ownership": [107, 108], "failure_origins": [233, 234], "scope_ref": scope_ref, "clarification_ref": clarification_ref, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root280.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert OLD.read_bytes() == enc(original)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 280, "ownership": 108, "failure_origins": 234, "scope_ref": scope_ref, "clarification_ref": clarification_ref, "formal_increment": 0}))
