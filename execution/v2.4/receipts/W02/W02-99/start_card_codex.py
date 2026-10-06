"""Root serial ownership and current-state registration for W02 parent gates."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
V24 = ROOT / "execution/v2.4"
SPEC = ROOT / ".local/worktrees/v24-continuation/spec/v2.4"
def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def ref(path, base=V24): return {"path":path.relative_to(base).as_posix(), "sha256":sha(path)}
cp_path, state_path, owner_path = (V24 / name for name in ["checkpoint.json", "step_state.json", "path_ownership.json"])
cp, state, owners = load(cp_path), load(state_path), load(owner_path)
assert cp["revision"] == 199 and owners["revision"] == 42
assert next(row for row in state["steps"] if row["id"] == "W01-99")["status"] == "ACCEPTED"
assert not any(row["id"] == "W02-99" for row in state["steps"])
head = subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
binding = dict(owner="codex:/root/w1102_impl", worktree=".local/worktrees/codex-w0299", paths=["execution/v2.4/receipts/W02/W02-99/**"], read_only_context=["current accepted product source", "execution/v2.4/commands.json", "execution/v2.4/path_ownership.json", "execution/v2.4/client_mapping.json", "qualification/v2.4/**", "current W01 independent qualification evidence"], shared_registry_writer="codex:/root", rationale="Frozen W02 parent has no final-owned formal cases. Build current qualification gates and immutable manifests inside card receipts. Root serializes exact3 build.check selectors and current ownership state, preserving old W02-03 handler and every old entry. Request concrete mapping before edits outside receipts.", model="gpt-6-astra", reason_for_model="Cross-client build provenance and exact dispatcher contract architecture require architecture reasoning. Reuse existing Astra worker after preserved earlier Sol capacity failures; no unchanged capacity retry.", limits=["Do not execute legacy build_check.py against shared local data or repeat unchanged Windows qualification GUI.", "Use new isolated build/contract/dispatcher synthetic fixtures; no provider, protected service, credentials or formal label reads.", "Reuse W01 source evidence only after exact input hashes match; no whole integrated-main binary claim from a prior source vector.", "Do not retry old W13 audit/NVDA or W14 UNKNOWN effect; no route/repair budget change."])
assert "W02-99" not in owners["card_path_bindings"]
owners["card_path_bindings"]["W02-99"] = binding
owners.update(revision=43, updated_at=now, updated_by="codex:/root", amended_at=now, amended_by="codex:/root")
write(owner_path, owners)
binding_path = HERE / "path_binding_codex.json"
write(binding_path, dict(recorded_at=now, step_id="W02-99", status="OWNER_REGISTERED_BEFORE_IMPLEMENTATION", path_revision=43, main_head=head, candidate_base=load(HERE / "worktree_prepared_codex.json")["base_source"], **binding))
state["steps"].append(dict(id="W02-99", status="IN_PROGRESS", executor_id=binding["owner"], started_at=now, evidence=[ref(binding_path)], execution_note="Three current local W02 parent gates; final-owned formal cases empty, associated A03/A15 remain owned by W06/W20. Independent acceptance required."))
write(state_path, state)
error_path = V24 / "receipts/W01/W01-99/integration_codex/acceptance_finalization_erratum_codex.json"
cp["failure_counters"].append(dict(origin_key="W01-root-next-packet-shape-postcondition", attempts=1, status="RESOLVED_METADATA_WITHOUT_REPEAT", evidence=ref(error_path, ROOT), detail="Root postcondition indexed show-only eligible in successful next packet. W01 state/CP199 already completed. Separate metadata finalizer validated VALIDATED_FILE and step W02-99; original failed script/packet preserved, no product test failure or gate replay."))
cp.update(head=head, current_step_id="W02-99", next_step_id="W02-99", updated_at=now, updated_by="codex:/root", work_in_progress=dict(step_id="W02-99", worktree=binding["worktree"], status="IN_PROGRESS", next_action="Implement distinct current clean-build/minimum-contract, executable/owner mapping and synthetic dispatcher failure gates; preserve old handler evidence. Then root register3 exact keys and independent review."), note="W01 parent independently accepted:36 materialized accepted, parent2/22 formal0/42. W02 is sole active engineering card.58 failure origins retained including resolved next-packet postcondition error; no failure counter reset.")
cp["workers"].append(dict(step_id="W02-99", owner=binding["owner"], worktree=binding["worktree"], state="PARENT_GATE_IMPLEMENTATION_IN_PROGRESS"))
cp["integrity_events"].append(dict(at=now, actor="codex:/root", card="W02-99", event="PARENT_CARD_REGISTERED_AFTER_DEPENDENCY_ACCEPTED", evidence=ref(binding_path), detail="Frozen task packet selected W02-99 after W01 independent acceptance. One engineering card; no provider/GUI/service probe."))
write(cp_path, cp)
event_path=HERE / "start_value_round_codex.json"
write(event_path, dict(schema="researchos.value-round.v1", round_id="W02-parent-owner-start-20261005", delta="DOCUMENTATION", summary="Register W02 parent owner/worktree after independently accepted W01 dependency. No new product capability claimed.", evidence_refs=[ref(binding_path, ROOT)]))
base=[sys.executable,"-B","-X","utf8",str(ROOT / "bootstrap/v24_checkpoint.py"),"--checkpoint",str(cp_path),"--state",str(state_path),"--plan",str(SPEC / "contracts/execution.plan.json"),"--delivery",str(SPEC / "contracts/delivery.contract.json")]
result=subprocess.run(base+["--expected-revision","199","--round-event",str(event_path),"--actor","codex:/root"],cwd=ROOT,capture_output=True)
(HERE / "checkpoint200.stdout.txt").write_bytes(result.stdout)
(HERE / "checkpoint200.stderr.txt").write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode("utf-8","replace")
packet=subprocess.run(base+["--next-packet"],cwd=ROOT,capture_output=True)
(HERE / "checkpoint200_next_packet.json").write_bytes(packet.stdout)
(HERE / "checkpoint200_next_packet.stderr.txt").write_bytes(packet.stderr)
assert packet.returncode == 0 and json.loads(packet.stdout)["step"]["id"] == "W02-99"
after=load(cp_path)
assert after["revision"] == 200 and len(after["failure_counters"]) == 58
assert after["value_checkpoint"]["source_hashes"]["step_state"] == sha(state_path)
print(json.dumps(dict(status="PASS", checkpoint=200, path_revision=43, active="W02-99", parent_accepted=2, formal_accepted=0, failures=58)))
