"""Root-only W07 registration, with durable intent and guarded crash recovery.

Development/static inspection does not issue acceptance. Only the actual Root
may invoke this program after observing the independently delivered message.
The pending journal is never a completion claim. Only completed.json is one.
All other canonical writers must respect Root's serial registration lease.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback
import uuid

PROJECT_ID = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
BASE_SCRIPT_SHA256 = "8776837b5a48d765c0268bbb58bfe517eea6d3424ebf31646635e5cfcdda593a"
ACTOR = "codex:/root"
EXECUTOR = "codex:/root/sources_parent_impl"
REVIEWER = "codex:/root/w05_merge_review"
PREFIX = "execution/v2.4/receipts/W07/W07-99"
CANONICAL = tuple("execution/v2.4/" + name for name in
                  ("step_state.json", "checkpoint.json", "path_ownership.json"))
ATTESTATION = "ACTUAL_ROOT_RECEIVED_INDEPENDENT_MESSAGE"


def require(condition, code, detail):
    if not condition:
        raise ValueError(code + ": " + str(detail))


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY", key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("NONFINITE_JSON: " + value)
    def number(value):
        parsed = float(value)
        require(math.isfinite(parsed), "NONFINITE_JSON", value)
        return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid, parse_float=number)


def encoded(value, crlf=False):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    return (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")


def immutable_bytes(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    immutable_bytes(path, encoded(value))


def sha(path):
    return digest(path.read_bytes())


def ref(repo, path):
    return {"path": path.relative_to(repo).as_posix(), "sha256": sha(path)}


def confined(repo, supplied, prefix=None):
    candidate = Path(supplied)
    if not candidate.is_absolute():
        candidate = repo / candidate
    resolved = candidate.resolve(strict=True)
    require(resolved.is_relative_to(repo), "PATH_ESCAPE", candidate)
    cursor = candidate
    while cursor != repo:
        require(not cursor.is_symlink() and not cursor.is_junction(), "PATH_LINK", cursor)
        require(cursor.parent != cursor, "PATH_ESCAPE", candidate)
        cursor = cursor.parent
    if prefix is not None:
        require(resolved.is_relative_to(repo / prefix), "PATH_SCOPE", candidate)
    return resolved


def canonical_paths(repo):
    result = {}
    for relative in CANONICAL:
        # A disappeared/replaced target is a recovery conflict, never permission
        # to recreate it. Resolve the existing trusted parent even if missing.
        parent = confined(repo, Path(relative).parent)
        target = parent / Path(relative).name
        result[relative] = target
    return result


def module(path, name):
    # Execute the same bytes whose digest is retained, not a second import read.
    source = path.read_bytes()
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    exec(compile(source, str(path), "exec"), loaded.__dict__)
    require(sha(path) == digest(source), "TOOL_CHANGED", path)
    return loaded, digest(source)


@contextmanager
def registration_lock(repo):
    # OS releases the byte lock on crash. The lock file itself is retained.
    require(os.name == "nt", "PLATFORM", "Windows registration only")
    import msvcrt
    path = repo / PREFIX / "integration_codex/root-registration.lock"
    try:
        immutable_bytes(path, b"0")
    except FileExistsError:
        pass
    with path.open("r+b") as stream:
        require(stream.read(1) == b"0", "LOCK_FORMAT", path)
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def hash_or_missing(path):
    try:
        if path.is_symlink() or path.is_junction():
            return "FOREIGN_LINK"
        return sha(path)
    except FileNotFoundError:
        return "MISSING"
    except OSError as exc:
        return "UNREADABLE:" + type(exc).__name__


def cas_replace(path, previous_sha256, raw, out):
    # The disposable rename payload is not a receipt; archived desired/original
    # bytes and the journal remain immutable and are never moved or removed.
    staging = out / "atomic-staging" / (uuid.uuid4().hex + ".payload")
    immutable_bytes(staging, raw)
    require(hash_or_missing(path) == previous_sha256, "CANONICAL_CAS", path)
    os.replace(staging, path)
    require(sha(path) == digest(raw), "CANONICAL_WRITE_HASH", path)


def event(out, phase, **details):
    save(out / "events" / (uuid.uuid4().hex + ".json"),
         {"at": now(), "phase": phase, **details})


def observed_canonical(repo):
    return {name: hash_or_missing(path) for name, path in canonical_paths(repo).items()}


def error_origin(out, phase, exc, trace, mode):
    path = out / "failure-origins" / (uuid.uuid4().hex + ".json")
    save(path, {"schema": "researchos.root-registration-failure-origin.v1",
               "origin_key": "W07-99|root-registration|" + out.name + "|" + path.stem,
               "attempt": 1, "at": now(), "actor": ACTOR, "mode": mode,
               "phase": phase, "exception_type": type(exc).__name__,
               "error": str(exc), "traceback": trace, "counter_reset": False,
               "counter_recording": "Durable new origin; existing checkpoint counters remain byte-exact on rollback. Root must append this origin to its next serial checkpoint reconciliation; never reset or discard it."})
    return path


def validate_journal(repo, out, journal):
    require(journal.get("schema") == "researchos.root-registration-pending.v1", "JOURNAL_SCHEMA", out)
    require(journal.get("actor") == ACTOR and journal.get("project_id") == PROJECT_ID,
            "JOURNAL_IDENTITY", out)
    require(Path(journal["repo"]).resolve() == repo, "JOURNAL_REPO", out)
    require(journal.get("status") == "PENDING_NOT_ACCEPTED", "JOURNAL_STATUS", out)
    require([e["path"] for e in journal["files"]] == list(CANONICAL), "JOURNAL_TARGETS", out)
    files = []
    for entry in journal["files"]:
        decoded = dict(entry)
        for kind in ("original", "desired"):
            reference = entry[kind + "_ref"]
            path = confined(repo, reference["path"])
            require(path.is_relative_to(out / "canonical-bytes"), "JOURNAL_BACKUP_SCOPE", path)
            raw = path.read_bytes()
            require(digest(raw) == reference["sha256"] == entry[kind + "_sha256"], "JOURNAL_BACKUP_HASH", path)
            strict(raw)
            decoded[kind + "_bytes"] = raw
        files.append(decoded)
    return files


def recover_files(repo, out, journal, origin_ref):
    require(not (out / "completed.json").exists(), "ALREADY_COMPLETED", out)
    files = validate_journal(repo, out, journal)
    observations = []
    for entry in reversed(files):
        path = canonical_paths(repo)[entry["path"]]
        current = hash_or_missing(path)
        row = {"path": entry["path"], "observed_sha256": current}
        if current == entry["original_sha256"]:
            row["action"] = "ALREADY_ORIGINAL"
        elif current == entry["desired_sha256"]:
            try:
                cas_replace(path, current, entry["original_bytes"], out)
                row["action"] = "RESTORED_OWN_WRITE"
            except Exception as exc:
                row.update(action="RECOVERY_FAILED", error=str(exc), traceback=traceback.format_exc())
        else:
            row["action"] = "FOREIGN_CHANGE_NOT_TOUCHED"
        observations.append(row)
        event(out, "RECOVERY_FILE", **row)
    after = observed_canonical(repo)
    restored = all(after[e["path"]] == e["original_sha256"] for e in files)
    result = {"schema": "researchos.root-registration-recovery.v1", "at": now(),
              "status": "RESTORED_ORIGINAL" if restored else "PARTIAL_REGISTRATION",
              "failure_origin_ref": origin_ref, "files": observations,
              "actual_canonical_sha256": after, "counter_reset": False,
              "acceptance_created": False}
    save(out / "recoveries" / (uuid.uuid4().hex + ".json"), result)
    return result


def require_hash(path, expected, label):
    require(isinstance(expected, str) and len(expected) == 64 and
            all(c in "0123456789abcdef" for c in expected), "EXPECTED_HASH_REQUIRED", label)
    require(sha(path) == expected, "EXPECTED_HASH_MISMATCH", label)


def check_w07(api, repo, plan, out, stem):
    derived = api.derive_formal_cases(repo, repo / CANONICAL[0], plan)
    save(out / (stem + "-formal-index.json"), derived)
    checked = api.recheck_inputs(derived["dependency_snapshot"])
    save(out / (stem + "-input-recheck.json"), checked)
    rows = [row for row in derived["owners"] if row["task_id"] == "W07"]
    require(len(rows) == 1 and rows[0]["integrity"] == "VALID_ACCEPTED" and
            rows[0]["accepted_case_ids"] == ["A05"], "W07_POSTDERIVE", rows)
    require("A05" in derived["accepted_case_ids"] and checked["status"] == "PASS", "POSTDERIVE_INPUTS", checked)
    # W04 can remain NEEDS_REVALIDATION. Never promote PARTIAL global integrity
    # to PASS, and never require all unrelated owners to be current green.
    require(derived["integrity"] in {"PASS", "PARTIAL"}, "DERIVED_GLOBAL_INVALID", derived["integrity"])
    return derived


def register(args, repo, out, progress):
    progress["phase"] = "CAPTURE_ORIGINALS"
    paths = canonical_paths(repo)
    require(all(not path.is_symlink() and not path.is_junction() for path in paths.values()),
            "CANONICAL_LINK", "Canonical originals must be ordinary files")
    original = {name: path.read_bytes() for name, path in paths.items()}
    original_hashes = {name: digest(raw) for name, raw in original.items()}
    values = {name: strict(raw) for name, raw in original.items()}
    state, cp, own = [values[name] for name in CANONICAL]
    require(cp["project_id"] == PROJECT_ID and Path(cp["repository_root"]).resolve() == repo,
            "CHECKPOINT_IDENTITY", cp.get("project_id"))
    for name, raw in original.items():
        immutable_bytes(out / "canonical-bytes" / (Path(name).name + ".original"), raw)
    require(args.root_attestation == ATTESTATION, "ACTUAL_ROOT_ATTESTATION_REQUIRED", "No synthetic delivery")
    require(all((args.context, args.review, args.received_message)) and
            bool(args.event_locator or args.expected_event_locator_sha256),
            "MISSING_DELIVERY_ARGUMENT", "context/review/message/expected locator")
    context_path, review_path, message_path, event_path = [confined(repo, p, PREFIX) for p in
                                                         (args.context, args.review, args.received_message,
                                                          args.raw_event or args.received_message)]
    for path, expected, label in ((review_path, args.expected_review_sha256, "review"),
                                  (message_path, args.expected_message_sha256, "message"),
                                  (event_path, args.expected_raw_event_sha256 or
                                   (args.expected_message_sha256 if event_path == message_path else None), "raw event")):
        require_hash(path, expected, label)
    api_path = confined(repo, "execution/v2.4/formal_case_index.py")
    api, api_sha = module(api_path, "researchos_root_w07_index")
    reader = api.Reader(repo)
    reader.read_hashes[api_path] = api_sha
    reader.read_hashes[repo / CANONICAL[0]] = original_hashes[CANONICAL[0]]
    identity_path = confined(repo, "execution/project_identity.json")
    reader.read(identity_path)
    context, review, message = [reader.read(p) for p in (context_path, review_path, message_path)]
    require(context.get("schema") == "researchos.w07.current-context.v1" and context.get("task_id") == "W07"
            and context.get("step_id") == "W07-99", "CONTEXT_IDENTITY", context_path)
    require(context["executor_id"] == EXECUTOR and review["reviewer_id"] == REVIEWER,
            "ASSIGNED_ACTORS", "Root-assigned actual executor and reviewer")
    require(context["proof_ref"]["sha256"] == args.expected_proof_sha256, "EXPECTED_PROOF_HASH", context["proof_ref"])
    proof_path = reader.ref(context["proof_ref"])
    require_hash(proof_path, args.expected_proof_sha256, "proof")
    locator = message.get("event_locator")
    require(isinstance(locator, (str, dict)) and bool(locator), "ACTUAL_EVENT_LOCATOR", message_path)
    locator_digest = digest(json.dumps(locator, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":"), allow_nan=False).encode("utf-8"))
    if args.expected_event_locator_sha256:
        require(locator_digest == args.expected_event_locator_sha256, "EXPECTED_EVENT_LOCATOR_HASH", message_path)
    if args.event_locator:
        try:
            expected_locator = strict(args.event_locator)
        except ValueError:
            expected_locator = args.event_locator
        require(locator == expected_locator, "ACTUAL_EVENT_LOCATOR", message_path)
    if "raw_event_ref" in message:
        require(message["raw_event_ref"] == ref(repo, event_path), "ACTUAL_EVENT_REFERENCE", event_path)
    else:
        require(event_path == message_path, "ACTUAL_EVENT_REFERENCE", "Without separate raw ref, retain the already recorded original Root envelope itself")
    if isinstance(locator, dict):
        require(locator.get("task_name") == "/root" and locator.get("sender_task") == REVIEWER.removeprefix("codex:")
                and locator.get("message_type") == message.get("event_type") and bool(locator.get("source"))
                and locator.get("message_content_sha256") == digest(message["content"].encode("utf-8")),
                "ACTUAL_EVENT_LOCATOR_FIELDS", "Preserve actual envelope without inventing a missing platform event ID")
    raw_event = event_path.read_bytes()
    reader.ref(ref(repo, event_path))
    # Raw source may be the exact message text or an actual platform envelope.
    # The Root's external observation is the trust source, never synthesized here.
    event_text = raw_event.decode("utf-8")
    try:
        envelope = strict(raw_event)
    except (ValueError, UnicodeError):
        envelope = None
    actual_content = envelope.get("content") if isinstance(envelope, dict) else event_text
    require(actual_content == message.get("content") and isinstance(actual_content, str),
            "ACTUAL_EVENT_CONTENT", "Retain exact received content bytes/text")
    if isinstance(envelope, dict):
        require(envelope.get("sender") == REVIEWER and envelope.get("event_locator") == locator,
                "ACTUAL_EVENT_ENVELOPE", event_path)
    save(out / "observed-delivery-binding.json", {"actor": ACTOR, "attestation": args.root_attestation,
         "event_locator": locator, "event_locator_sha256": locator_digest, "raw_event_ref": ref(repo, event_path),
         "message_ref": ref(repo, message_path), "review_sha256": args.expected_review_sha256,
         "proof_sha256": args.expected_proof_sha256, "at": now(),
         "boundary": "Root attests actual platform observation; JSON self-consistency alone is not independent delivery authentication."})
    current_spec = reader.read(confined(repo, "execution/v2.4/current_spec.json"))
    spec = confined(repo, current_spec["snapshot_relative_to_candidate_branch_worktree"])
    plan = confined(repo, spec / "contracts/execution.plan.json")
    require(sha(plan) == current_spec["plan_sha256"] == api.FROZEN_HASHES["execution.plan.json"], "PLAN_BASELINE", plan)
    require(context["acceptance_baseline_ref"]["sha256"] == api.FROZEN_HASHES["acceptance.json"],
            "ACCEPTANCE_BASELINE", context["acceptance_baseline_ref"])
    require(reader.ref(context["acceptance_baseline_ref"]).name == "acceptance.json", "ACCEPTANCE_NAME", context_path)
    plan_value = reader.read(plan)
    _, _, _, _, planned = api._catalog(reader, plan)
    api._canonical_state(reader, repo / CANONICAL[0], planned)
    owner = next(row for row in state["steps"] if row["id"] == "W07-99")
    require(owner["status"] in {"IN_PROGRESS", "EXECUTION_REPORTED"}, "OWNER_STATE", owner["status"])
    old_owner = deepcopy(owner)
    save(out / "previous-owner-registration.json", {"schema": "researchos.previous-owner-registration.v1",
         "owner": old_owner, "state_sha256": original_hashes[CANONICAL[0]], "recorded_at": now()})
    step = next(row for row in plan_value["steps"] if row["id"] == "W07-99")
    statuses = {row["id"]: row["status"] for row in state["steps"]}
    require(all(statuses.get(k) == "ACCEPTED" for k in step["dependencies"]), "DEPENDENCIES", step["dependencies"])
    profile = api._w07_profile(reader)
    for reference in owner["evidence"]:
        path = reader.ref({"path": "execution/v2.4/" + reference["path"], "sha256": reference["sha256"]})
        if path.suffix == ".json":
            value = reader.read(path)
            require(not isinstance(value, dict) or value.get("schema") not in profile.SCHEMAS.values(), "COMPETING_ROOT", path)
    progress["phase"] = "FULL_PENDING_PREVALIDATION"
    pinned, tools = profile._vector(api._profile_api(), reader, context)
    proof, _ = profile.product(api._profile_api(), reader, context, tools)
    profile._dispatches(api._profile_api(), reader, context, pinned, proof)
    profile._global(api._profile_api(), reader, context, proof, review_path)
    issuance = {"schema": "researchos.w07.root-observed-issuance.v1", "task_id": "W07", "step_id": "W07-99",
                "run_id": context["run_id"], "actor": ACTOR, "executor_id": context["executor_id"],
                "reviewer_id": review["reviewer_id"], "context_ref": ref(repo, context_path),
                "review_ref": ref(repo, review_path), "delivery_ref": ref(repo, message_path), "observed_at": now()}
    issuance_path = out / "issuance.json"
    save(issuance_path, issuance)
    intent_time = now()
    pending_owner = deepcopy(owner)
    pending_owner.update(status="IN_PROGRESS", accepted_at=intent_time)
    save(out / "pending-validation-intent.json", {"status": "PENDING_NOT_ACCEPTED",
         "owner_status": "IN_PROGRESS", "registration_intent_at": intent_time,
         "note": "The accepted_at argument only supplies the prospective time bound required by _independent; no ACCEPTED owner exists or has been written."})
    profile._independent(api._profile_api(), reader, pending_owner, context_path, review_path, issuance_path, context)
    reader.finish()
    pre_snapshot = {"files": {str(p): h for p, h in reader.read_hashes.items() if p not in paths.values()},
                    "inventories": [{"repo": str(repo), "coverage": context["source_coverage"],
                                     "paths": [r["path"] for r in context["version_vector"]["source_files"]]}]}
    save(out / "prevalidation-inputs.json", pre_snapshot)
    require(observed_canonical(repo) == original_hashes, "PREPARATION_CAS", "canonical changed during validation")
    progress["phase"] = "PREPARE_DESIRED_BYTES"
    owner.update(status="ACCEPTED", executor_id=EXECUTOR, verifier_id=REVIEWER, accepted_at=intent_time,
                 note="Actual current W07 A05 independently reviewed and Root-observed; completion requires transaction completed marker. Historical evidence retained.")
    for path in (context_path, review_path, issuance_path):
        reference = ref(repo, path)
        owner["evidence"].append({"path": reference["path"].removeprefix("execution/v2.4/"), "sha256": reference["sha256"]})
    require(owner["evidence"][:len(old_owner["evidence"])] == old_owner["evidence"], "OLD_EVIDENCE_CHANGED", "W07-99")
    require([row for row in state["steps"] if row["id"] != "W07-99"] ==
            [row for row in strict(original[CANONICAL[0]])["steps"] if row["id"] != "W07-99"],
            "OTHER_OWNER_CHANGED", "W04 historical registration and all other rows")
    original_parent_records = deepcopy(cp["parent_tasks_accepted"])
    original_failure_counters = deepcopy(cp["failure_counters"])
    require(not any(str(p).startswith("W07") for p in original_parent_records), "PARENT_ALREADY_REGISTERED", "W07")
    old_revision, old_ownership_revision = cp["revision"], own["revision"]
    cp.update(revision=old_revision + 1, expected_previous_revision=old_revision, updated_at=now(), updated_by=ACTOR,
              head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip())
    cp["accepted_steps"] = [row["id"] for row in state["steps"] if row["status"] == "ACCEPTED"]
    cp["parent_tasks_accepted"].append("W07(full owned current LIVE_SERVICE A05 and gates, actual independent acceptance)")
    cp["next_command"] = "Confirm W07 completed marker; preserve historical parent registrations including stale W04; separately register approved W04 current revalidation and continue W05 open obligations."
    cp["note"] += " | W07 transaction records current A05; parent count is historical construction registrations, including gates-only parents and stale W04. Prior failure counters retained."
    for worker in cp["workers"]:
        if worker.get("step_id") == "W07-99" and not worker.get("slice_id"):
            worker.update(state="ACCEPTED_CURRENT_FORMAL_A05", independent_review=ref(repo, review_path), current_context_ref=ref(repo, context_path))
    own.update(revision=old_ownership_revision + 1, updated_at=now(), updated_by=ACTOR)
    own["card_path_bindings"]["W07-99"].update(state="ACCEPTED_CURRENT_FORMAL_A05", current_context_ref=ref(repo, context_path),
            independent_review_ref=ref(repo, review_path), root_issuance_ref=ref(repo, issuance_path))
    cp["evidence_index"].extend((out / name).relative_to(repo).as_posix() for name in ("registration.json", "handoff.json", "completed.json"))
    require(cp["failure_counters"] == original_failure_counters and cp["parent_tasks_accepted"][:-1] == original_parent_records,
            "HISTORICAL_COUNTERS_CHANGED", "Root metadata")
    desired = {CANONICAL[0]: encoded(state, True), CANONICAL[1]: encoded(cp), CANONICAL[2]: encoded(own, True)}
    files = []
    for name in CANONICAL:
        desired_path = out / "canonical-bytes" / (Path(name).name + ".desired")
        immutable_bytes(desired_path, desired[name])
        files.append({"path": name, "original_sha256": original_hashes[name], "desired_sha256": digest(desired[name]),
                      "original_ref": ref(repo, out / "canonical-bytes" / (Path(name).name + ".original")),
                      "desired_ref": ref(repo, desired_path)})
    journal = {"schema": "researchos.root-registration-pending.v1", "status": "PENDING_NOT_ACCEPTED",
               "actor": ACTOR, "project_id": PROJECT_ID, "repo": str(repo), "transaction_id": out.name,
               "created_at": now(), "registration_intent_at": intent_time, "files": files,
               "context_ref": ref(repo, context_path), "review_ref": ref(repo, review_path),
               "message_ref": ref(repo, message_path), "issuance_ref": ref(repo, issuance_path),
               "script_ref": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__))},
               "failure_counter_count_before": len(original_failure_counters), "counter_reset": False}
    save(out / "pending-journal.json", journal)
    progress["journal"] = journal
    expected_current = dict(original_hashes)
    for name in CANONICAL:
        progress["phase"] = "REPLACE_" + Path(name).name
        require(observed_canonical(repo) == expected_current, "TRANSACTION_CAS", progress["phase"])
        require(api.recheck_inputs(pre_snapshot)["status"] == "PASS", "PREWRITE_INPUT_DRIFT", name)
        cas_replace(paths[name], original_hashes[name], desired[name], out)
        expected_current[name] = digest(desired[name])
        event(out, progress["phase"], path=name, desired_sha256=expected_current[name])
    progress["phase"] = "POSTDERIVE"
    derived = check_w07(api, repo, plan, out, "postwrite")
    progress["phase"] = "PARENT_LEDGER"
    ledger_path = confined(repo, "execution/v2.4/parent_gate_ledger.py")
    ledger, ledger_sha = module(ledger_path, "researchos_root_parent_ledger")
    parent_ledger = ledger.build(repo, spec)
    save(out / "actual-parent-ledger.json", parent_ledger)
    require(parent_ledger["parents"]["W07"]["formal_evidence_integrity"] == "VALID_ACCEPTED" and
            parent_ledger["parents"]["W07"]["formal_cases_accepted"] == ["A05"], "LEDGER_A05", parent_ledger["parents"]["W07"])
    progress["phase"] = "FINAL_DERIVE_AND_CAS"
    final = check_w07(api, repo, plan, out, "final")
    require(final["accepted_case_ids"] == derived["accepted_case_ids"] and
            final["owners"] == derived["owners"], "OWNER_DERIVATION_DRIFT", "postwrite/final")
    require(observed_canonical(repo) == expected_current, "FINAL_CANONICAL_CAS", "all three files")
    require(api.recheck_inputs(pre_snapshot)["status"] == "PASS", "FINAL_PREVALIDATION_DRIFT", "evidence")
    require(sha(api_path) == api_sha and sha(ledger_path) == ledger_sha, "FINAL_TOOL_DRIFT", "formal tooling")
    summary = {"actor": ACTOR, "at": now(), "counter_reset": False,
               "previous_sha256": original_hashes, "desired_sha256": expected_current,
               "historical_parent_registration_count": len(cp["parent_tasks_accepted"]),
               "historical_parent_registration_records": cp["parent_tasks_accepted"],
               "count_semantics": "Historical construction registration count, including gates-only parents and stale W04; not a count of current fully accepted parents.",
               "formal_current_accepted_case_ids": final["accepted_case_ids"],
               "formal_current_case_count": final["formal_cases_accepted"],
               "formal_global_integrity": final["integrity"], "formal_owner_states": final["owners"],
               "formal_global_reasons": final["reasons"], "failure_origin_count_before": len(original_failure_counters),
               "checkpoint_revision": cp["revision"], "ownership_revision": own["revision"],
               "context_ref": ref(repo, context_path), "review_ref": ref(repo, review_path), "issuance_ref": ref(repo, issuance_path),
               "journal_ref": ref(repo, out / "pending-journal.json"),
               "derived_ref": ref(repo, out / "final-formal-index.json"), "ledger_ref": ref(repo, out / "actual-parent-ledger.json"),
               "completion_rule": "These details alone do not complete registration; require completed.json and its exact hashes."}
    save(out / "registration.json", {"schema": "researchos.root-current-acceptance-registration.v1", **summary})
    save(out / "handoff.json", {"schema": "researchos.root-resume-handoff.v1", "goal_status": "ACTIVE",
         "required_parents": 22, "required_formal_cases": 42, "blocked_steps": cp["blocked_steps"],
         "next_action": cp["next_command"], **summary})
    # Final reader/CAS boundary after all receipt serialization, immediately
    # before the only success marker. Other writers must obey the Root lease.
    require(api.recheck_inputs(final["dependency_snapshot"])["status"] == "PASS", "COMPLETION_INPUT_DRIFT", "final snapshot")
    require(observed_canonical(repo) == expected_current, "COMPLETION_CANONICAL_CAS", "all three files")
    progress["phase"] = "WRITE_COMPLETION_MARKER"
    completion = {"schema": "researchos.root-registration-completed.v1", "status": "W07_CURRENT_ACCEPTED",
         "at": now(), "actor": ACTOR, "journal_ref": ref(repo, out / "pending-journal.json"),
         "registration_ref": ref(repo, out / "registration.json"), "handoff_ref": ref(repo, out / "handoff.json"),
         "canonical_sha256": expected_current, "accepted_owner": "W07", "accepted_case_ids": ["A05"],
         "formal_global_integrity": final["integrity"], "counter_reset": False}
    marker_bytes = out / "completion-marker-bytes.json"
    save(marker_bytes, completion)
    # NTFS hard-link insertion is atomic and fails if completed.json exists;
    # crashes cannot expose a partly written marker. Both paths are retained.
    require(api.recheck_inputs(final["dependency_snapshot"])["status"] == "PASS", "MARKER_INPUT_DRIFT", "final snapshot")
    require(observed_canonical(repo) == expected_current, "MARKER_CANONICAL_CAS", "all three files")
    os.link(marker_bytes, out / "completed.json")
    progress["phase"] = "COMPLETED"
    return {"status": "W07_CURRENT_ACCEPTED", "completed_ref": ref(repo, out / "completed.json"),
            "formal_global_integrity": final["integrity"], "formal_current_case_ids": final["accepted_case_ids"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--actor", choices=[ACTOR], required=True)
    for name in ("context", "review", "received-message", "raw-event", "recover"):
        parser.add_argument("--" + name, type=Path)
    for name in ("expected-review-sha256", "expected-proof-sha256", "expected-message-sha256",
                 "expected-raw-event-sha256", "expected-event-locator-sha256", "expected-journal-sha256", "event-locator", "root-attestation"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    identity_path = confined(repo, "execution/project_identity.json")
    identity = strict(identity_path.read_bytes())
    require(identity.get("project_id") == PROJECT_ID and identity.get("name") == "ResearchOS"
            and Path(identity["repository_root"]).resolve() == repo, "CANONICAL_REPOSITORY_IDENTITY", repo)
    locked = strict(confined(repo, "execution/toolchains/locked.json").read_bytes())["tools"]["python"]
    require(Path(sys.executable).resolve() == Path(locked["path"]).resolve() and
            sha(Path(sys.executable)) == locked["sha256"], "LOCKED_PYTHON", sys.executable)
    canonical_paths(repo)
    with registration_lock(repo):
        if args.recover:
            journal_path = confined(repo, args.recover, PREFIX + "/integration_codex")
            require(journal_path.name == "pending-journal.json", "RECOVERY_JOURNAL_NAME", journal_path)
            out = journal_path.parent
            require(out.name.startswith("current-issuance-") and not (out / "completed.json").exists(), "RECOVERY_SCOPE", out)
            origin = error_origin(out, "EXPLICIT_CRASH_RECOVERY", RuntimeError("Root requested recovery of incomplete registration"),
                                  "Original process crash trace is unavailable; no exception is invented.", "RECOVERY")
            try:
                require_hash(journal_path, args.expected_journal_sha256, "recovery journal")
                journal = strict(journal_path.read_bytes())
                validate_journal(repo, out, journal)
                result = recover_files(repo, out, journal, ref(repo, origin))
            except Exception as exc:
                failed = error_origin(out, "RECOVERY_CHECK_OR_WRITE", exc, traceback.format_exc(), "RECOVERY")
                result = {"status": "PARTIAL_REGISTRATION", "failure_origin_ref": ref(repo, failed),
                          "actual_canonical_sha256": observed_canonical(repo), "counter_reset": False}
                save(out / "recoveries" / (uuid.uuid4().hex + ".json"), result)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result["status"] == "RESTORED_ORIGINAL" else 1
        out = repo / PREFIX / "integration_codex" / ("current-issuance-" + uuid.uuid4().hex)
        out.mkdir()
        progress = {"phase": "START", "journal": None}
        event(out, "START", actor=args.actor, argv=sys.argv, cwd=str(Path.cwd()), script_sha256=sha(Path(__file__)))
        try:
            result = register(args, repo, out, progress)
        except BaseException as exc:
            if (out / "completed.json").exists():
                # A completed transaction cannot be rolled back by a later
                # reporting exception. Record it without contradicting commit.
                error_origin(out, "POST_COMPLETION_REPORTING", exc, traceback.format_exc(), "COMPLETED_NO_ROLLBACK")
                raise
            origin = error_origin(out, progress["phase"], exc, traceback.format_exc(), "REGISTRATION")
            if progress["journal"] is not None:
                try:
                    result = recover_files(repo, out, progress["journal"], ref(repo, origin))
                except Exception as recovery_error:
                    failed = error_origin(out, "RECOVERY_AFTER_" + progress["phase"], recovery_error,
                                          traceback.format_exc(), "RECOVERY")
                    result = {"status": "PARTIAL_REGISTRATION", "failure_origin_ref": ref(repo, failed),
                              "actual_canonical_sha256": observed_canonical(repo), "counter_reset": False}
                    save(out / "recoveries" / (uuid.uuid4().hex + ".json"), result)
            else:
                result = {"status": "FAILED_BEFORE_CANONICAL_WRITES", "failure_origin_ref": ref(repo, origin),
                          "actual_canonical_sha256": observed_canonical(repo)}
                save(out / "failed-before-writes.json", result)
            print(json.dumps(result, ensure_ascii=False))
            return 1
        print(json.dumps(result, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    sys.exit(main())
