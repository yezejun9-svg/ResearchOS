"""Update the v2.4 construction value checkpoint without changing product gates.

Usage: python bootstrap/v24_checkpoint.py --checkpoint PATH --state PATH
       --plan PATH --delivery PATH --expected-revision N --baseline
   or: python bootstrap/v24_checkpoint.py ... --round-event PATH
       [--force-checkpoint --reason TEXT]

Round event JSON (stored inside the repository):
  {"schema":"researchos.value-round.v1", "round_id":"unique-id",
   "delta":"DOCUMENTATION|FIXTURE|INFRASTRUCTURE|USER_FLOW",
   "summary":"observed change", "evidence_refs":[{"path":"repo/relative/file",
   "sha256":"64 lowercase hexadecimal characters"}],
   "capability_observed":"specific observable behavior"}  # USER_FLOW only

This is a construction checkpoint, not an AcceptanceReceipt. A file hash proves
the referenced bytes exist; it does not certify the observation's truth.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


SCHEMA = "researchos.value-checkpoint.v1"
ROUND_SCHEMA = "researchos.value-round.v1"
DELTAS = {"DOCUMENTATION", "FIXTURE", "INFRASTRUCTURE", "USER_FLOW"}
HASH = re.compile(r"[0-9a-f]{64}\Z")


class CheckpointError(ValueError):
    pass


def strict_json(raw: bytes) -> dict:
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise CheckpointError("duplicate JSON key: " + key)
            out[key] = value
        return out

    def invalid_number(value):
        raise CheckpointError("nonfinite JSON number: " + value)

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_number)
    if not isinstance(value, dict):
        raise CheckpointError("JSON root must be an object")
    return value


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    return strict_json(raw), raw


def inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise CheckpointError("evidence path must be repository relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise CheckpointError("evidence file absent or outside repository: " + relative)
    return path


def accepted_and_status(state: dict, plan: dict) -> tuple[set[str], dict[str, str], dict[str, dict]]:
    if not isinstance(state.get("steps"), list) or not isinstance(plan.get("steps"), list):
        raise CheckpointError("state.steps and plan.steps must be arrays")
    plans = {row["id"]: row for row in plan["steps"]}
    if len(plans) != len(plan["steps"]):
        raise CheckpointError("duplicate plan step")
    statuses = {}
    for row in state["steps"]:
        step_id, status = row.get("id"), row.get("status")
        if step_id not in plans or step_id in statuses or not isinstance(status, str):
            raise CheckpointError("unknown, duplicate or malformed state step")
        statuses[step_id] = status
    accepted = {step_id for step_id, row in plans.items()
                if row.get("phase") == "IMPLEMENTATION_SLICE" and statuses.get(step_id) == "ACCEPTED"}
    return accepted, statuses, plans


def gates(statuses: dict[str, str], plans: dict[str, dict], formal_index: dict | None = None) -> dict:
    parents = sorted(step_id for step_id, row in plans.items()
                     if row.get("phase") == "PARENT_FINAL_GATE" and statuses.get(step_id) == "ACCEPTED")
    if sum(row.get("phase") == "PARENT_FINAL_GATE" for row in plans.values()) != 22:
        raise CheckpointError("frozen 22-parent plan mismatch")
    result = {"required_parent_tasks": 22, "accepted_parent_step_ids": parents,
              "required_formal_cases": 42, "formal_cases_accepted": "NOT_DERIVABLE_FROM_STEP_STATE",
              "formal_evidence_integrity": "NOT_DERIVED", "accepted_case_ids": [],
              "overall": "OPEN_PENDING_INDEPENDENT_FORMAL_CASE_EVIDENCE"}
    if formal_index is not None:
        result.update(formal_cases_accepted=formal_index["formal_cases_accepted"],
                      accepted_case_ids=formal_index["accepted_case_ids"],
                      formal_evidence_integrity=formal_index["integrity"],
                      formal_evidence_reasons=formal_index["reasons"],
                      case_states=formal_index["cases"])
        if len(parents) == 22 and formal_index["integrity"] == "PASS" and formal_index["formal_cases_accepted"] == 42:
            result["overall"] = "COMPLETE_INDEPENDENT_FORMAL_EVIDENCE"
    return result


def formal_reader(root: Path):
    """Load only repository source; evidence never supplies an executable path."""
    source = root / "execution/v2.4/formal_case_index.py"
    if not source.is_file():
        return None  # Standalone synthetic checkpoint callers have no evidence reader.
    resolved = source.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise CheckpointError("formal reader source outside repository")
    spec = importlib.util.spec_from_file_location("researchos_formal_case_index", resolved)
    module = importlib.util.module_from_spec(spec)
    raw = resolved.read_bytes()
    exec(compile(raw, str(resolved), "exec"), module.__dict__)
    module.loaded_source_sha256 = sha(raw)
    return module


def ready_flows(statuses: dict[str, str], plans: dict[str, dict], delivery: dict) -> list[dict]:
    capabilities = delivery.get("capabilities")
    if not isinstance(capabilities, list):
        raise CheckpointError("delivery capabilities missing")
    result = []
    for capability in capabilities:
        flow_id, task_id = capability.get("id"), capability.get("task_id")
        if flow_id == "U09":  # U09 is the direction checkpoint, not a user journey.
            continue
        remaining = [row for row in plans.values()
                     if row.get("parent_task") == task_id and row.get("phase") == "IMPLEMENTATION_SLICE"
                     and statuses.get(row["id"]) != "ACCEPTED"]
        ready = [row for row in remaining
                 if statuses.get(row["id"], "NOT_STARTED") in {"NOT_STARTED", "IN_PROGRESS"}
                 and all(statuses.get(dep) == "ACCEPTED" for dep in row.get("dependencies", []))]
        if not ready:
            continue
        next_card = min(ready, key=lambda row: (row.get("priority", 9999), row["id"]))
        result.append({"capability_id": flow_id, "title": capability.get("title"),
                       "next_step_id": next_card["id"], "next_step_status": statuses.get(next_card["id"], "NOT_STARTED"),
                       "remaining_implementation_cards": len(remaining),
                       "ready_dependency_ids": list(next_card.get("dependencies", [])),
                       "evidence_basis": "frozen plan dependencies and current step_state statuses",
                       "formal_case_status": "NOT_VERIFIED_BY_THIS_CHECKPOINT"})
    return sorted(result, key=lambda row: (row["remaining_implementation_cards"], row["capability_id"]))


def prioritized_step(current: dict, statuses: dict, plans: dict, delivery: dict,
                     default_step_id: str | None) -> str | None:
    """Consume U09 only at a card boundary; never reset or dispatch a blocked card."""
    if not current.get("value_checkpoint", {}).get("pause_nonblocking_expansion"):
        return default_step_id
    candidates = flow_priority(statuses, plans, delivery)["candidates"]
    return candidates[0]["next_step_id"] if candidates else None


def flow_priority(statuses: dict, plans: dict, delivery: dict) -> dict:
    """Prefer direct user slices, otherwise expose required parent frontiers only."""
    direct = ready_flows(statuses, plans, delivery)
    if direct:
        return {"candidates": direct, "required_parent_closures": [], "blocking_reason": None}

    def order(step_id):
        if step_id not in plans:
            raise CheckpointError("unknown dependency step: " + step_id)
        return plans[step_id].get("priority", 9999), step_id

    closures = []
    for capability in delivery["capabilities"]:
        if capability.get("id") not in {f"U{i:02d}" for i in range(1, 9)}:
            continue
        parent = capability["task_id"] + "-99"
        if parent not in plans or plans[parent].get("phase") != "PARENT_FINAL_GATE":
            raise CheckpointError("user capability owner parent missing: " + parent)
        if statuses.get(parent) == "ACCEPTED":
            continue
        visiting, visited, remaining = set(), set(), []

        def visit(step_id):
            order(step_id)
            if step_id in visiting:
                raise CheckpointError("dependency cycle at: " + step_id)
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in sorted(plans[step_id].get("dependencies", []), key=order):
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)
            if statuses.get(step_id) != "ACCEPTED":
                remaining.append(step_id)

        visit(parent)
        blockers = [{"step_id": step_id, "status": statuses.get(step_id, "NOT_STARTED")}
                    for step_id in remaining
                    if statuses.get(step_id, "NOT_STARTED") not in {"NOT_STARTED", "IN_PROGRESS"}]
        ready = [step_id for step_id in remaining
                 if statuses.get(step_id, "NOT_STARTED") in {"NOT_STARTED", "IN_PROGRESS"}
                 and all(statuses.get(dep) == "ACCEPTED"
                         for dep in plans[step_id].get("dependencies", []))]
        next_id = min(ready, key=order) if ready else None
        closures.append({"capability_id": capability["id"], "title": capability.get("title"),
                         "target_parent": parent, "scope": "PREREQUISITE_FOR_USER_FLOW",
                         "unaccepted_dependency_closure": remaining,
                         "remaining_required_cards": len(remaining), "blockers": blockers,
                         "next_step_id": next_id,
                         "next_step_status": statuses.get(next_id, "NOT_STARTED") if next_id else None,
                         "ready_dependency_ids": list(plans[next_id].get("dependencies", [])) if next_id else [],
                         "evidence_basis": "complete frozen owner-parent dependency closure and current step_state statuses",
                         "formal_case_status": "NOT_VERIFIED_BY_THIS_CHECKPOINT"})
    closures.sort(key=lambda row: (bool(row["blockers"]), row["remaining_required_cards"],
                                  order(row["next_step_id"] or row["target_parent"]), row["capability_id"]))
    candidates = [row for row in closures if row["next_step_id"] is not None]
    reason = None if candidates else ("NO_ELIGIBLE_FRONTIER_IN_REQUIRED_PARENT_CLOSURES" if closures
                                      else "ALL_USER_CAPABILITY_OWNER_PARENTS_ACCEPTED")
    return {"candidates": candidates, "required_parent_closures": closures, "blocking_reason": reason}


def next_packet(checkpoint_path: Path, state_path: Path, plan_path: Path,
                delivery_path: Path) -> tuple[dict, int]:
    current, original = read(checkpoint_path)
    state, state_raw = read(state_path)
    plan, plan_raw = read(plan_path)
    delivery, _ = read(delivery_path)
    if current.get("plan_sha256") != sha(plan_raw) or state.get("plan_sha256") != sha(plan_raw):
        raise CheckpointError("frozen plan hash mismatch")
    _, statuses, plans = accepted_and_status(state, plan)
    tool = plan_path.resolve().parent.parent / "tools" / "task_packet.py"
    if not tool.is_file():
        raise CheckpointError("frozen task_packet.py missing")

    def packet(command: str, step_id: str | None = None) -> tuple[dict, int]:
        argv = [sys.executable, "-B", "-X", "utf8", str(tool), "--plan", str(plan_path), command]
        if step_id is not None:
            argv.append(step_id)
        argv.extend(["--state", str(state_path)])
        result = subprocess.run(argv, capture_output=True, encoding="utf-8", timeout=60)
        if result.returncode not in (0, 3):
            raise CheckpointError("frozen task packet rejected current state: " + result.stderr.strip())
        body = strict_json(result.stdout.encode("utf-8"))
        if body.get("state_source") != "VALIDATED_FILE":
            raise CheckpointError("unvalidated task state is not actionable")
        return body, result.returncode

    result, code = packet("next")
    default_id = (result.get("step") or {}).get("id")
    value = current.get("value_checkpoint", {})
    priority = flow_priority(statuses, plans, delivery) if value.get("pause_nonblocking_expansion") else None
    selected = (priority["candidates"][0]["next_step_id"] if priority["candidates"] else None) if priority else default_id
    if priority:
        if selected is None:
            result.update(step=None, status="NO_READY_USER_FLOW")
            code = 3
        else:
            result, code = packet("show", selected)
            if result.get("eligible") is not True:
                raise CheckpointError("recommended user flow is not eligible")
    if checkpoint_path.read_bytes() != original or state_path.read_bytes() != state_raw:
        raise CheckpointError("checkpoint or state changed during selection")
    result["value_checkpoint_policy"] = {"checkpoint_revision": current["revision"],
                                         "status": value.get("status"),
                                         "priority_consumed": bool(value.get("pause_nonblocking_expansion")),
                                         "default_step_id": default_id, "selected_step_id": selected,
                                         "selection": priority,
                                         "authority": "READ_ONLY_SELECTION_NOT_DISPATCH_OR_ACCEPTANCE"}
    return result, code


def validate_round(event: dict, event_path: Path, root: Path) -> dict:
    required = {"schema", "round_id", "delta", "summary", "evidence_refs"}
    if not required.issubset(event) or set(event) - (required | {"capability_observed"}):
        raise CheckpointError("round event fields missing or unknown")
    if event["schema"] != ROUND_SCHEMA or not isinstance(event["round_id"], str) or not event["round_id"].strip():
        raise CheckpointError("invalid round identity or schema")
    if event["delta"] not in DELTAS or not isinstance(event["summary"], str) or not event["summary"].strip():
        raise CheckpointError("invalid round delta or summary")
    if not isinstance(event["evidence_refs"], list) or not event["evidence_refs"]:
        raise CheckpointError("round requires actual evidence references")
    if event["delta"] == "USER_FLOW":
        if not isinstance(event.get("capability_observed"), str) or not event["capability_observed"].strip():
            raise CheckpointError("USER_FLOW requires a concrete observed capability")
    elif "capability_observed" in event:
        raise CheckpointError("only USER_FLOW may claim an observed capability")
    refs = []
    for ref in event["evidence_refs"]:
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"} or not isinstance(ref["sha256"], str):
            raise CheckpointError("invalid evidence reference")
        digest = ref["sha256"].removeprefix("sha256:")
        if not HASH.fullmatch(digest) or sha(inside(root, ref["path"]).read_bytes()) != digest:
            raise CheckpointError("evidence hash mismatch: " + ref["path"])
        refs.append({"path": ref["path"], "sha256": digest})
    if len({row["path"] for row in refs}) != len(refs):
        raise CheckpointError("duplicate evidence reference")
    event_relative = event_path.resolve().relative_to(root.resolve()).as_posix()
    return {"round_id": event["round_id"], "delta": event["delta"], "summary": event["summary"],
            "evidence_refs": refs, "event_ref": {"path": event_relative, "sha256": sha(event_path.read_bytes())},
            **({"capability_observed": event["capability_observed"]} if event["delta"] == "USER_FLOW" else {})}


def update_value(current: dict, accepted: set[str], statuses: dict[str, str], plans: dict[str, dict],
                 delivery: dict, *, baseline: bool, round_record: dict | None,
                 force: bool, reason: str | None, now: str, formal_index: dict | None = None) -> dict:
    old = current.get("value_checkpoint")
    if not isinstance(old, dict):
        raise CheckpointError("value_checkpoint must be an object")
    frozen = delivery.get("value_checkpoint")
    if not isinstance(frozen, dict) or any(frozen.get(k) != v for k, v in {
            "after_step_count": 3, "no_user_capability_rounds": 2,
            "no_value_checkpoints_before_replan": 2, "new_candidates_alone_count_as_value": False,
            "does_not_lower_product_acceptance": True}.items()):
        raise CheckpointError("frozen U09 thresholds changed")
    priority = flow_priority(statuses, plans, delivery)
    candidates = priority["candidates"]
    gate = gates(statuses, plans, formal_index)
    if baseline:
        if old.get("status") != "NOT_RUN" or round_record is not None or force or reason:
            raise CheckpointError("baseline only initializes an unobserved checkpoint")
        if old.get("capabilities_observed") or old.get("documentation_only_checkpoints"):
            raise CheckpointError("historical value observations exist; baseline would erase them")
        return {**copy.deepcopy(old), "schema": SCHEMA, "status": "BASELINE_CAPTURED",
                "historical_observation": "NOT_RECONSTRUCTED", "baseline_at": now,
                "baseline_accepted_implementation_card_ids": sorted(accepted),
                "last_checkpoint_accepted_card_ids": sorted(accepted), "pending_rounds": [],
                "history": [], "all_round_ids": [], "documentation_only_checkpoints": 0,
                "capabilities_observed": [], "user_flow_candidates": candidates,
                "required_parent_closures": priority["required_parent_closures"],
                "selection_blocking_reason": priority["blocking_reason"],
                "formal_gate": gate, "next_priority": "FOLLOW_FROZEN_PLAN"}
    if old.get("schema") != SCHEMA or not isinstance(old.get("history"), list):
        raise CheckpointError("baseline required; historical rounds are unknown")
    if round_record is None or round_record["round_id"] in old.get("all_round_ids", []):
        raise CheckpointError("new unique round event required")
    value = copy.deepcopy(old)
    value["all_round_ids"].append(round_record["round_id"])
    value["pending_rounds"].append(round_record)
    value["user_flow_candidates"] = candidates
    value["required_parent_closures"] = priority["required_parent_closures"]
    value["selection_blocking_reason"] = priority["blocking_reason"]
    if value.get("pause_nonblocking_expansion"):
        value["recommended_flow"] = candidates[0] if candidates else None
    value["formal_gate"] = gate
    if round_record["delta"] == "USER_FLOW":
        value["capabilities_observed"].append({"round_id": round_record["round_id"],
                                                "behavior": round_record["capability_observed"],
                                                "evidence_refs": round_record["evidence_refs"],
                                                "authority": "DEVELOPMENT_OBSERVATION_ONLY"})
    previous = set(value["last_checkpoint_accepted_card_ids"])
    if not previous.issubset(accepted):
        raise CheckpointError("accepted implementation cards regressed")
    new_cards = sorted(accepted - previous)
    no_capability_rounds = 0
    for item in reversed(value["pending_rounds"]):
        if item["delta"] == "USER_FLOW":
            break
        no_capability_rounds += 1
    trigger = "THREE_ACCEPTED_IMPLEMENTATION_CARDS" if len(new_cards) >= 3 else (
        "TWO_ROUNDS_WITHOUT_USER_CAPABILITY" if no_capability_rounds >= 2 else None)
    if force:
        if not isinstance(reason, str) or not reason.strip():
            raise CheckpointError("early checkpoint requires a reason")
        trigger = trigger or "MANUAL_EARLY"
    elif reason:
        raise CheckpointError("reason is only valid with --force-checkpoint")
    if trigger is None:
        value["status"] = "PENDING_THRESHOLD"
        return value
    only_scaffolding = all(item["delta"] != "USER_FLOW" for item in value["pending_rounds"])
    streak = value["documentation_only_checkpoints"] + 1 if only_scaffolding else 0
    record = {"number": len(value["history"]) + 1, "at": now, "trigger": trigger,
              "early_reason": reason if trigger == "MANUAL_EARLY" else None,
              "round_ids": [item["round_id"] for item in value["pending_rounds"]],
              "round_evidence_refs": [item["event_ref"] for item in value["pending_rounds"]],
              "new_accepted_implementation_card_ids": new_cards,
              "only_documentation_fixture_or_infrastructure": only_scaffolding,
              "observed_user_capability": not only_scaffolding,
              "formal_gate": gate}
    value["history"].append(record)
    value["pending_rounds"] = []
    value["last_checkpoint_accepted_card_ids"] = sorted(accepted)
    value["documentation_only_checkpoints"] = streak
    if streak >= 2:
        value["status"] = "PRIORITIZE_USER_FLOW" if candidates else "BLOCKED_NO_READY_USER_FLOW"
        value["next_priority"] = "SHORTEST_DEPENDENCY_READY_USER_FLOW"
        value["pause_nonblocking_expansion"] = True
        value["priority_reason"] = "Two consecutive value checkpoints added only documentation, fixtures or infrastructure; U09 requires the shortest dependency-ready user flow without changing formal gates."
        value["recommended_flow"] = candidates[0] if candidates else None
        value["recommendation_authority"] = "CONSTRUCTION_PRIORITY_ONLY_NOT_DISPATCHED"
    else:
        value["status"] = "CHECKED"
        value["next_priority"] = "FOLLOW_FROZEN_PLAN"
        value["pause_nonblocking_expansion"] = False
        value["recommended_flow"] = None
    return value


def update_file(checkpoint: Path, state_path: Path, plan_path: Path, delivery_path: Path,
                expected_revision: int, *, baseline: bool = False, event_path: Path | None = None,
                force: bool = False, reason: str | None = None, actor: str = "codex:construction") -> dict:
    checkpoint, state_path, plan_path, delivery_path = (p.resolve() for p in
                                                        (checkpoint, state_path, plan_path, delivery_path))
    root = checkpoint.parents[2]
    if not state_path.is_relative_to(root) or not checkpoint.is_relative_to(root):
        raise CheckpointError("checkpoint and state must share repository")
    lock = checkpoint.with_name(checkpoint.name + ".value.lock")
    fd = None
    owns_lock = False
    temporary = None
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        owns_lock = True
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        fd = None
        current, original = read(checkpoint)
        state, state_raw = read(state_path)
        plan, plan_raw = read(plan_path)
        delivery, delivery_raw = read(delivery_path)
        if type(current.get("revision")) is not int or current["revision"] != expected_revision:
            raise CheckpointError("CAS revision mismatch")
        if current.get("plan_sha256") != sha(plan_raw) or state.get("plan_sha256") != sha(plan_raw):
            raise CheckpointError("frozen plan hash mismatch")
        accepted, statuses, plans = accepted_and_status(state, plan)
        event_record = None
        if event_path is not None:
            event_path = event_path.resolve()
            if not event_path.is_relative_to(root):
                raise CheckpointError("round event must be inside repository")
            event, _ = read(event_path)
            event_record = validate_round(event, event_path, root)
        now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        reader = formal_reader(root)
        formal_index = reader.derive_formal_cases(root, state_path, plan_path) if reader is not None else None
        reader_source_hash = reader.loaded_source_sha256 if reader is not None else None
        updated = copy.deepcopy(current)
        updated["value_checkpoint"] = update_value(current, accepted, statuses, plans, delivery,
                                                     baseline=baseline, round_record=event_record,
                                                     force=force, reason=reason, now=now, formal_index=formal_index)
        updated["expected_previous_revision"] = expected_revision
        updated["revision"] = expected_revision + 1
        updated["updated_at"] = now
        updated["updated_by"] = actor
        updated["value_checkpoint"]["source_hashes"] = {"step_state": sha(state_raw),
                                                          "execution_plan": sha(plan_raw),
                                                          "delivery_contract": sha(delivery_raw)}
        # Reject stale source or a non-cooperating writer before the atomic swap.
        if (checkpoint.read_bytes() != original or state_path.read_bytes() != state_raw
                or plan_path.read_bytes() != plan_raw or delivery_path.read_bytes() != delivery_raw):
            raise CheckpointError("CAS source changed before replace")
        if reader is not None:
            if sha((root / "execution/v2.4/formal_case_index.py").read_bytes()) != reader_source_hash:
                raise CheckpointError("formal reader changed before replace")
            observed = reader.recheck_inputs(formal_index["dependency_snapshot"])
            if observed["status"] != "PASS":
                raise CheckpointError("formal evidence changed before replace: " + observed["reason"])
        with tempfile.NamedTemporaryFile(mode="wb", dir=checkpoint.parent,
                                         prefix=checkpoint.name + ".value.", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write((json.dumps(updated, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, checkpoint)
        temporary = None
        return updated
    finally:
        if fd is not None:
            os.close(fd)
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if owns_lock:
            lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--expected-revision", type=int)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--baseline", action="store_true")
    mode.add_argument("--round-event", type=Path)
    mode.add_argument("--next-packet", action="store_true")
    parser.add_argument("--force-checkpoint", action="store_true")
    parser.add_argument("--reason")
    parser.add_argument("--actor", default="codex:construction")
    args = parser.parse_args()
    try:
        if args.next_packet:
            if args.expected_revision is not None or args.force_checkpoint or args.reason:
                raise CheckpointError("next packet is read only; mutation options are invalid")
            result, code = next_packet(args.checkpoint, args.state, args.plan, args.delivery)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return code
        if args.expected_revision is None:
            raise CheckpointError("checkpoint update requires --expected-revision")
        result = update_file(args.checkpoint, args.state, args.plan, args.delivery,
                             args.expected_revision, baseline=args.baseline,
                             event_path=args.round_event, force=args.force_checkpoint,
                             reason=args.reason, actor=args.actor)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "REJECTED", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    value = result["value_checkpoint"]
    print(json.dumps({"status": value["status"], "revision": result["revision"],
                      "checkpoint_count": len(value["history"]),
                      "documentation_only_checkpoints": value["documentation_only_checkpoints"],
                      "recommended_flow": value.get("recommended_flow"),
                      "formal_gate": value["formal_gate"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
