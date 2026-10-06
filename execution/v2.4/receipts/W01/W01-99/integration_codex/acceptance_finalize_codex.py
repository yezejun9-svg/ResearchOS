"""Finish CP199 metadata after packet next correctly omitted show-only eligible."""
from pathlib import Path
import datetime as dt
import hashlib
import json
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / "execution/v2.4"
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    return json.loads(path.read_bytes())
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
cp = load(V24 / "checkpoint.json")
state_path = V24 / "step_state.json"
state = load(state_path)
packet = load(HERE / "checkpoint199_next_packet.json")
assert cp["revision"] == 199 and packet["step"]["id"] == "W02-99"
assert packet["state_source"] == "VALIDATED_FILE"
assert next(row for row in state["steps"] if row["id"] == "W01-99")["status"] == "ACCEPTED"
assert len(cp["failure_counters"]) == 57
assert cp["value_checkpoint"]["source_hashes"]["step_state"] == digest(state_path)
assert cp["value_checkpoint"]["formal_gate"]["accepted_parent_step_ids"] == ["W00-99", "W01-99"]
write(HERE / "acceptance_finalization_erratum_codex.json", dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), actor="codex:/root", original_script="accept_parent_codex.py", original_exit_code=1, original_error="KeyError: 'eligible'", actual_completed_operations="W01 independent acceptance and CP199 value checkpoint successfully written; validated next packet selected W02-99.", cause="Frozen task_packet next returns state_source and step but not show-only eligible. Root integration metadata postcondition incorrectly indexed eligible.", resolution="Validate actual next-packet shape without repeating gate, state mutation, value round or tests. Preserve failed script, original packet and error; add failure origin at next checkpoint.", product_tests_failed=0, repeated_gui_provider_service_calls=0))
write(HERE / "acceptance_record_codex.json", dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), actor="codex:/root", status="INDEPENDENT_ACCEPTANCE_RECORDED", step_id="W01-99", review_sha256=digest(HERE.parent / "independent_review_codex.json"), checkpoint_revision=199, materialized_accepted=36, parent_accepted=2, parent_required=22, formal_accepted=0, formal_required=42, failure_origins_preserved=53, failure_origins_total=57, next_step=packet["step"]["id"], state_sha256=digest(state_path), finalization_erratum_sha256=digest(HERE / "acceptance_finalization_erratum_codex.json")))
print(json.dumps(dict(status="PASS", checkpoint=199, parent_accepted=2, formal_accepted=0, next_step=packet["step"]["id"], failure_origins=57)))
