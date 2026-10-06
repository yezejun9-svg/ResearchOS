"""Explicit W04 applicability transition; no v1 supersession or product execution.

prepare/dry-run audits real existing evidence and writes only immutable plans.
apply requires independent authorization bound to that exact plan. Synthetic
controls call the pure guards against isolated synthetic documents, never CLI
apply or canonical ResearchOS state. Shared validators are loaded unchanged.
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
from pathlib import Path, PureWindowsPath
import sys
import subprocess
import traceback
import uuid

PROJECT = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
ROOT_ACTOR = "codex:/root"
BASE = "execution/v2.4/receipts/W04/W04-99/"
SCOPE_DIR = BASE + "integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/"
STATE = "execution/v2.4/step_state.json"
REGISTRY = "execution/v2.4/commands.json"
PREFIX_SHA = "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1"
SCOPE_SHA = "d696fd97101dee79d927d0a76e1bfa6cec10a36a525782e515adaecc15c6f4e1"
ASSIGNMENT_SHA = "97b28880a7bc6f034b83ee5db199d563a3cc47f8d9a743d85651f7dc8f96535d"
SCOPE_REVIEW_SHA = "e41a81d749e73a7408f5fbc23320eb1a57cc65d1248520d6c00d63def64c6bbc"
OLD_REGISTERED = {"path": BASE + "integration_codex/registered_integrity_round2_invocation_codex.json",
                  "sha256": "2a11aa38b260d9dd3b1e134be4f6e6f3062275c3cd507c066a12a9656a31edb0"}
SCHEMAS = {"context": "researchos.w04.current-context.v1", "review": "researchos.w04.independent-review.v1",
           "issuance": "researchos.w04.root-observed-issuance.v1"}
CASES = {"C03": ["C03-01", "C03-02", "C03-03"], "C04": ["C04-01", "C04-02", "C04-03"],
         "A01": ["A01-01", "A01-02", "A01-03", "A01-04"]}
GATES = ["W04-G01", "W04-G02", "W04-G03", "W04-H01", "W04-B01"]
GROUPS = ("spec_files", "source_files", "input_files", "lock_files", "tool_files")
HISTORY_SCOPE = {"path": BASE + "integration_codex/historical-purpose-amendment-f996016351e24358973ebd6a8b128e96/scope_amendment.json",
                 "sha256": "a4a798bd65c082e42def9e434f04627f967a18ee876c7b205d0655b69ee31285"}
EXPECTED_OLD = {"path": BASE + "executor_codex/expected.json", "sha256": "075cdf560c9b4e791493218e056325c27010987f6f43242720d25282197f24ce"}
EXPECTED_MANIFEST = {"path": BASE + "executor_codex/runs/20261005T224949Z-418d17844405/source_snapshot_manifest.json",
                     "sha256": "98e6c224e47a7a1a9fd28c0a90901aa344f6b79826e45a03a5cca6d9356f2aeb"}
EXPECTED_COPY = {"path": str(Path(EXPECTED_MANIFEST["path"]).parent / "source_snapshot" / EXPECTED_OLD["path"]).replace("\\", "/"), "sha256": EXPECTED_OLD["sha256"]}
EXPECTED_VECTOR = {"path": str(Path(EXPECTED_MANIFEST["path"]).parent / "version_vector.json").replace("\\", "/"),
                   "sha256": "e39862de172e308b0cb5d81d0c6b7b1bb51d6ba19e1f9f2d22e6502fa07120dc"}
OLD_AUDIT = {"path": BASE + "independent-review-codex-final-20261006-61a0d2e7/audit_result.json", "sha256": "b2ffa00c4f842ba2b1e9f45da5570f86b01970f95a719ebf552b03129baf6e27"}
OLD_STATE_SHA = "64ef113e768e530d721977cf10c736d4c285fd9896ba00727871ff449c422760"
OLD_STATE_COPY = {"path": BASE + "integration_codex/step_state_before_acceptance.json", "sha256": OLD_STATE_SHA}
OLD_STATE_COMMIT = "f68c83c2918ae25d9811e4e9f703f1a158e143d2"
COLLECTION_ORDER = "VERIFIED_EXCLUSIVE_RUN_BEFORE_PREPROOF_PREPUBLISH_FINALLY_AFTER_AND_FINAL_EXIT"


class Refusal(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(code + ": " + str(detail))


def need(condition, code, detail):
    if not condition:
        raise Refusal(code, detail)


def strict(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, "DUPLICATE_JSON_KEY", key)
            value[key] = item
        return value
    def bad(value):
        raise Refusal("NONFINITE_JSON", value)
    def number(value):
        value = float(value)
        need(math.isfinite(value), "NONFINITE_JSON", value)
        return value
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad, parse_float=number)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def object_sha(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def at(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(stamp.tzinfo is not None, "TIMEZONE_REQUIRED", value)
    return stamp


def now():
    return datetime.now(timezone.utc).isoformat()


def exclusive(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    exclusive(path, encoded(value))


def path_in(repo, relative):
    raw_parts = str(relative).replace("\\", "/").split("/")
    need(all(part not in {"", ".", ".."} for part in raw_parts), "PATH_SCOPE", relative)
    p = Path(relative)
    need(not p.is_absolute() and not PureWindowsPath(str(relative)).drive and ".." not in p.parts,
         "PATH_SCOPE", relative)
    p = repo / p
    need(p.resolve().is_relative_to(repo), "PATH_SCOPE", relative)
    cursor = p
    while cursor != repo:
        need(not cursor.is_symlink() and not cursor.is_junction(), "PATH_LINK", cursor)
        cursor = cursor.parent
    return p


def reference(repo, path):
    return {"path": path.relative_to(repo).as_posix(), "sha256": sha(path.read_bytes())}


def load_module(path, name):
    raw = path.read_bytes()
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    exec(compile(raw, str(path), "exec"), value.__dict__)
    need(sha(path.read_bytes()) == sha(raw), "TOOL_CHANGED", path)
    return value


class Audit:
    """Hash every followed reference; fallback is only an exact frozen source copy."""
    def __init__(self, repo):
        self.repo = Path(repo).resolve()
        self.observed = {}
        self.applicability = {}
        self.drifts = []
        self.visited = set()
        self.snapshot_bindings = {}
        self.bound_metadata = set()
        self.external_inputs = {}
        self.aliases = {}
        self.historical_observations = []

    def bytes(self, ref, historical=False):
        need(isinstance(ref, dict) and isinstance(ref.get("path"), str) and
             isinstance(ref.get("sha256"), str) and len(ref["sha256"]) == 64, "REFERENCE_SHAPE", ref)
        ref = normalized_ref(self.repo, ref)
        need(ref is not None, "REFERENCE_OUTSIDE_REPO", "External reads require an explicit compiled-input guard")
        alias = ref["path"].casefold()
        need(alias not in self.aliases or self.aliases[alias] == ref["path"], "AMBIGUOUS_REFERENCE_PATH", ref)
        self.aliases[alias] = ref["path"]
        path = path_in(self.repo, ref["path"])
        raw = path.read_bytes() if path.is_file() else None
        actual = sha(raw) if raw is not None else None
        if actual != ref["sha256"]:
            key = (ref["path"], ref["sha256"])
            need(historical and key in self.applicability, "HASH_MISMATCH", ref["path"])
            # Only existing source copies bound by the old immutable graph can
            # explain an old source version. No raw/JSON/message substitution.
            exact_asset = ref == EXPECTED_OLD and any(
                item["mapping_ref"] == EXPECTED_MANIFEST and item["snapshot_ref"] == EXPECTED_COPY
                for item in self.snapshot_bindings.get(key, []))
            need(source_path(ref["path"]) or ref["path"] == REGISTRY or exact_asset, "OLD_RECEIPT_DRIFT", ref["path"])
            frozen = self.applicability[key]
            raw = self.bytes(frozen)
            need(sha(raw) == ref["sha256"], "HISTORICAL_SOURCE_HASH", ref["path"])
            self.drifts.append({"path": ref["path"], "old_sha256": ref["sha256"],
                                "current_sha256": actual, "snapshot_ref": frozen,
                                "binding_refs": self.snapshot_bindings.get(key, [])})
        else:
            prior = self.observed.get(ref["path"])
            need(prior is None or prior == actual, "READ_DRIFT", ref["path"])
            self.observed[ref["path"]] = actual
        return raw

    def doc(self, ref, historical=False):
        return strict(self.bytes(ref, historical))

    def current(self, relative):
        path = path_in(self.repo, relative)
        raw = path.read_bytes()
        reference = {"path": relative, "sha256": sha(raw)}
        self.bytes(reference)
        return strict(raw), reference

    def closure(self, value, historical=False, parent=None, field=None):
        if isinstance(value, list):
            for item in value:
                self.closure(item, historical, parent, field)
        elif isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                value = normalized_ref(self.repo, value)
                if value is None:
                    return
                name = value["path"]
                # Package-manifest internal names are not repo-relative refs.
                repo_ref = name.startswith(("execution/", ".local/", "internal/", "apps/", "adapters/", "migrations/", "tests/", "spec/")) or name in {"go.mod", "go.sum"}
                if repo_ref:
                    key = (name, value["sha256"])
                    if key not in self.visited:
                        self.visited.add(key)
                        raw = self.bytes(value, historical)
                        if name.endswith(".json"):
                            self.closure(strict(raw), historical, value)
                return
            for ref in mapped_hashes(self.repo, value):
                if not (historical and historical_state_observation(self, parent, field, ref)):
                    self.closure(ref, historical, parent, field)
            for key, item in value.items():
                self.closure(item, historical, parent, key)

    def finish(self):
        for name, expected in self.external_inputs.items():
            need(Path(name).is_file() and sha(Path(name).read_bytes()) == expected, "NEEDS_REVALIDATION", name)
        for name, expected in self.observed.items():
            p = path_in(self.repo, name)
            need(p.is_file() and sha(p.read_bytes()) == expected, "NEEDS_REVALIDATION", name)
        for drift in self.drifts:
            p = path_in(self.repo, drift["path"])
            current = sha(p.read_bytes()) if p.is_file() else None
            need(current == drift["current_sha256"], "NEEDS_REVALIDATION", drift["path"])


def source_path(name):
    return Path(name).suffix.lower() in {".go", ".py", ".sql", ".mjs", ".js", ".ts", ".tsx", ".css", ".html"} or name in {"go.mod", "go.sum"}


def normalized_ref(repo, ref):
    name = ref["path"]
    if Path(name).is_absolute():
        p = Path(name)
        if not p.is_relative_to(repo):
            return None  # External tool paths are independently locked.
        name = p.relative_to(repo).as_posix()
    else:
        name = name.replace("\\", "/")
    path_in(repo, name)
    return {"path": name, "sha256": ref["sha256"]}


def mapped_hashes(repo, value):
    for name, digest in value.items():
        if isinstance(name, str) and isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest):
            if Path(name).is_absolute():
                ref = normalized_ref(repo, {"path": name, "sha256": digest})
                if ref:
                    yield ref


def historical_state_observation(audit, parent, field, ref):
    # Exact purpose classification, never a general STATE or JSON fallback.
    if parent != OLD_AUDIT or field != "input_hashes" or ref != {"path": STATE, "sha256": OLD_STATE_SHA}:
        return False
    ruling = audit.doc(HISTORY_SCOPE)["mutable_state_observation_ruling"]
    need(ruling["parent_audit_ref"] == parent and ruling["field"] == field
         and ruling["historical_sha256"] == ref["sha256"] and ruling["corroboration_ref"] == OLD_STATE_COPY
         and ruling["first_tracked_commit"] == OLD_STATE_COMMIT, "HISTORY_SCOPE_BINDING", ruling)
    # Reading the unchanged parent itself is mandatory; no invented old edge.
    document = audit.doc(parent)
    entries = list(mapped_hashes(audit.repo, document[field]))
    need(entries.count(ref) == 1 and normalized_ref(audit.repo, {"path": ruling["original_path"], "sha256": OLD_STATE_SHA}) == ref,
         "HISTORY_OBSERVATION_PARENT", parent)
    raw = audit.bytes(OLD_STATE_COPY)
    writer = BASE + "integration_codex/accept_parent_codex.py"
    git_refs = []
    for name in (OLD_STATE_COPY["path"], writer):
        argv = ["git", "show", OLD_STATE_COMMIT + ":" + name]
        run = subprocess.run(argv, cwd=audit.repo, capture_output=True, check=False)
        need(run.returncode == 0, "HISTORY_GIT_PROVENANCE", name)
        actual = path_in(audit.repo, name).read_bytes()
        need(actual == run.stdout, "HISTORY_GIT_PROVENANCE", name)
        audit.bytes({"path": name, "sha256": sha(actual)})
        git_refs.append({"argv": argv, "exit_code": run.returncode, "blob_sha256": sha(run.stdout), "stderr_sha256": sha(run.stderr)})
        if name == writer:
            text = actual.decode("utf-8")
            need("state_raw, cp_raw = state_path.read_bytes(), cp_path.read_bytes()" in text
                 and "('step_state_before_acceptance.json',state_raw)" in text
                 and "with (HERE/name).open('xb') as stream: stream.write(raw_before)" in text,
                 "HISTORY_WRITER_PROVENANCE", writer)
    need(sha(raw) == OLD_STATE_SHA, "HISTORY_COPY_HASH", OLD_STATE_COPY)
    observation = {"classification": "HISTORICAL_READ_OBSERVATION_WITH_NEW_TRANSITION_CORROBORATION",
        "parent_audit_ref": parent, "field": field, "original_ref": ref,
        "additional_corroboration_ref": OLD_STATE_COPY, "scope_amendment_ref": HISTORY_SCOPE,
        "git_provenance": git_refs, "original_review_bound_copy": False,
        "current_state_cas_substitute": False}
    if observation not in audit.historical_observations:
        audit.historical_observations.append(observation)
    return True


def historical_manifest_vector(audit, manifest, ref):
    need(manifest.get("unavailable_originals") == [], "OLD_SOURCE_SNAPSHOT", ref)
    if ref == EXPECTED_MANIFEST:
        need(manifest.get("schema") == "researchos.failed-source-snapshot.v1"
             and manifest.get("source_vector_sha256") == EXPECTED_VECTOR["sha256"], "EXACT_EARLIER_SOURCE_VECTOR", ref)
        vector_ref = EXPECTED_VECTOR
    else:
        need(manifest.get("schema") == "researchos.execution-source-snapshot.v1", "OLD_SOURCE_SNAPSHOT", ref)
        vector_ref = manifest["version_vector_ref"]
    return audit.doc(vector_ref)


def historical_expected_mapping(audit, original, frozen, binding):
    if original != EXPECTED_OLD or frozen != EXPECTED_COPY or binding != EXPECTED_MANIFEST:
        return False
    ruling = audit.doc(HISTORY_SCOPE)["source_asset_ruling"]
    need(ruling["permitted_exact_original_ref"] == original
         and ruling["required_exact_old_mapping_manifest_ref"] == binding
         and ruling["permitted_exact_snapshot_ref"] == frozen, "HISTORY_ASSET_SCOPE", original)
    vector = historical_manifest_vector(audit, audit.doc(binding), binding)
    need(original in vector["source_files"], "HISTORY_ASSET_SOURCE_VECTOR", original)
    audit.bytes(frozen)
    return True


def discover_historical_snapshots(audit, roots):
    """First follow immutable JSON only, then validate every source normally.

    An original_ref is a historical version claim, not a request to read the
    current source. A snapshot_ref must itself have the exact claimed bytes.
    Multiple identical copies may corroborate one version; conflicting aliases
    or differing bytes refuse. The plan records every actual mapping document.
    """
    seen, bindings = set(), {}
    def walk(value, binding=None, field=None):
        if isinstance(value, list):
            for item in value:
                walk(item, binding, field)
        elif isinstance(value, dict):
            if value.get("schema") == "researchos.root-registration-integrity-repair.v1":
                need(binding == {"path": BASE + "integration_codex/registration_repair_source_codex.json",
                                 "sha256": "66b68be4ec06416d42c9054e338c6541b15d7ee8e2ac35f61737f1abe7133aeb"}
                     and len(value["source_changes"]) == 2, "UNBOUND_REPAIR_HISTORY", binding)
                for change in value["source_changes"]:
                    before, after = change["before"], change["after"]
                    need(source_path(before["path"]) and source_path(after["path"])
                         and before["path"].startswith(BASE + "integration_codex/")
                         and before["path"] != after["path"], "REPAIR_HISTORY_MAPPING", change)
                    audit.bytes(before)
                    key = (after["path"], before["sha256"])
                    bindings.setdefault(key, []).append({"mapping_ref": binding, "snapshot_ref": before,
                                                        "kind": "PRE_ACCEPTANCE_SOURCE_REPAIR_HISTORY"})
            if "original_ref" in value and "snapshot_ref" in value:
                original, frozen = value["original_ref"], value["snapshot_ref"]
                exact_asset = historical_expected_mapping(audit, original, frozen, binding)
                if source_path(original["path"]) or exact_asset:
                    need(binding is not None and original["path"] != frozen["path"]
                         and frozen["path"].startswith(BASE) and original["sha256"] == frozen["sha256"],
                         "OLD_SOURCE_SNAPSHOT_BINDING", value)
                    path_in(audit.repo, original["path"])
                    audit.bytes(frozen)
                    key = (original["path"], original["sha256"])
                    bindings.setdefault(key, []).append({"mapping_ref": binding, "snapshot_ref": frozen})
                walk(value["snapshot_ref"], binding)
                return
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                value = normalized_ref(audit.repo, value)
                if value is None:
                    return
                name = value["path"]
                if value == EXPECTED_OLD:
                    # Source-asset discovery only. Closure later requires the
                    # exact old bound manifest mapping; this grants no fallback.
                    return
                if name == REGISTRY or not name.startswith(("execution/", ".local/", "spec/")) or not name.endswith(".json"):
                    return
                key = (name, value["sha256"])
                if key not in seen:
                    seen.add(key)
                    document = audit.doc(value)
                    audit.bound_metadata.add(key)
                    walk(document, value)
                return
            for ref in mapped_hashes(audit.repo, value):
                if not historical_state_observation(audit, binding, field, ref):
                    walk(ref, binding, field)
            for key, child in value.items():
                walk(child, binding, key)
    walk(roots)
    if (EXPECTED_OLD["path"], EXPECTED_OLD["sha256"]) in bindings:
        need((EXPECTED_VECTOR["path"], EXPECTED_VECTOR["sha256"]) in audit.bound_metadata,
             "OLD_BOUND_SOURCE_VECTOR_MISSING", EXPECTED_VECTOR)
    for key, entries in bindings.items():
        # Same path with different spellings/aliases is rejected by path_in;
        # each selected copy and each corroborating copy has been hash checked.
        copies = {item["snapshot_ref"]["path"]: item["snapshot_ref"] for item in entries}
        audit.applicability[key] = copies[sorted(copies)[0]]
        audit.snapshot_bindings[key] = entries
    return bindings


def root_inventory(audit, row, expected_count=None):
    evidence = row["evidence"]
    if expected_count is not None:
        need(len(evidence) == expected_count, "OLD_EVIDENCE_COUNT", len(evidence))
    roots, nonroots, seen = {}, [], set()
    for r in evidence:
        need(r["path"] not in seen, "DUPLICATE_REFERENCE", r["path"])
        seen.add(r["path"])
        translated = {"path": "execution/v2.4/" + r["path"], "sha256": r["sha256"]}
        raw = audit.bytes(translated)
        value = strict(raw) if r["path"].endswith(".json") else {}
        kind = next((k for k, s in SCHEMAS.items() if isinstance(value, dict) and value.get("schema") == s), None)
        if kind:
            need(kind not in roots, "CONFLICTING_REVIEW", kind)
            roots[kind] = translated
        else:
            nonroots.append(deepcopy(r))
    need(set(roots) == set(SCHEMAS), "MISSING_OLD_ROOT", roots)
    return roots, nonroots


def review_semantics(review):
    need(review.get("schema") == SCHEMAS["review"] and review.get("scope") == "EXTERNAL_FIXTURE_VERIFICATION"
         and review.get("task_id") == "W04" and review.get("step_id") == "W04-99", "REVIEW_IDENTITY", review)
    need(review.get("construction_decision") == "ACCEPTED" and review.get("open_blockers") == [], "UNRESOLVED_REVIEW", review)
    need(not review.get("supersedes_review_refs") and not review.get("supersession_reason"), "SUPERSESSION_NOT_SUPPORTED", "v1 unchanged")
    rows = review["owned_case_verdicts"]
    need(len(rows) == 3 and {r["case_id"] for r in rows} == set(CASES), "EXPECTED_IDS", "cases")
    for row in rows:
        need(row["final_owner_task"] == "W04" and row["mode"] == "FIXTURE" and row["status"] == "PASS"
             and sorted(row["assertion_ids"]) == sorted(CASES[row["case_id"]])
             and row["semantic_review"]["status"] == "CONFIRMED" and row["semantic_review"]["raw_evidence_refs"], "EXPECTED_IDS_MODE_SEMANTICS", row)
    gates = review["parent_gate_verdicts"]
    need(len(gates) == 5 and {r["check_id"] for r in gates} == set(GATES)
         and all(r["mode"] == "FIXTURE" and r["status"] == "PASS" for r in gates), "EXPECTED_GATES", gates)


def delivery_chain(audit, roots, row=None, assignment=None):
    context, review, issuance = [audit.doc(roots[k]) for k in ("context", "review", "issuance")]
    review_semantics(review)
    index = audit.doc(context["execution_index"])
    ex, ve, observer = review["executor_id"], review["verifier_id"], issuance["observer_id"]
    need(len({ex.casefold(), ve.casefold(), observer.casefold()}) == 3 and observer == ROOT_ACTOR,
         "INDEPENDENT_ACTORS", [ex, ve, observer])
    need(index["executor_id"] == ex and review["evidence_index_ref"] == context["execution_index"]
         and review["current_context_ref"] == roots["context"], "CHAIN_INDEX", roots)
    need(issuance.get("schema") == SCHEMAS["issuance"] and issuance.get("scope") == "ROOT_OBSERVED_INDEPENDENT_ISSUANCE"
         and issuance["issuer_id"] == ve and issuance["review_ref"] == roots["review"]
         and issuance["current_context_ref"] == roots["context"] and issuance["channel"] == "independent_agent_message", "DELIVERY_CHAIN", issuance)
    need(bool(issuance.get("message_id")) and isinstance(issuance.get("message_ref"), dict), "MISSING_ACTUAL_MESSAGE", issuance)
    message = audit.doc(issuance["message_ref"])
    need(message.get("sender") == ve and message.get("message_id") == issuance["message_id"]
         and message.get("review_sha256") == roots["review"]["sha256"] and isinstance(message.get("content"), str)
         and roots["review"]["sha256"] in message["content"], "ACTUAL_MESSAGE_LINK", message)
    need(at(review["issued_at"]) <= at(issuance["observed_at"]), "DELIVERY_TIME", issuance)
    for cid in CASES:
        run = audit.doc(index["cases"][cid]["run_receipt"])
        need(run["executor_id"] == ex and run["verifier_id"] == ve and run["environment_mode"] == "FIXTURE"
             and at(run["started_at"]) <= at(run["ended_at"]) <= at(review["issued_at"]), "RUN_ACTOR_TIME", cid)
    if row is not None:
        need(row["status"] == "ACCEPTED" and row["executor_id"] == ex and row["verifier_id"] == ve
             and at(issuance["observed_at"]) <= at(row["accepted_at"]), "OLD_ROW_IDENTITY_TIME", row)
    if assignment is not None:
        need((ex, ve, observer) == (assignment["executor_id"], assignment["reviewer_id"], assignment["root_id"]), "ASSIGNMENT_MISMATCH", assignment)
        need(context["execution_index"]["path"].startswith(assignment["executor_namespace"])
             and roots["review"]["path"].startswith(BASE + "independent_revalidation_codex/")
             and roots["context"]["path"].startswith(SCOPE_DIR)
             and roots["issuance"]["path"].startswith(SCOPE_DIR), "NAMESPACE_OWNERSHIP", roots)
    return {"context": context, "review": review, "issuance": issuance, "message": message, "index": index}


def applicability(vector):
    # Relocating the collector/package or changing receipt filenames alone is
    # not a changed product applicability. Namespace-only transitions refuse.
    projected = {}
    for group in GROUPS:
        for r in vector[group]:
            name = r["path"]
            if "/frozen_inputs/package/" in name:
                name = "package/" + name.split("/frozen_inputs/package/", 1)[1]
            elif name.startswith("execution/v2.4/receipts/"):
                continue
            projected[group + ":" + name] = r["sha256"]
    return projected


def require_changed(old_context, new_context, old_review, new_review):
    review_semantics(old_review)
    review_semantics(new_review)
    need(old_review["acceptance_baseline_ref"]["sha256"] == new_review["acceptance_baseline_ref"]["sha256"], "BASELINE_CHANGED", "acceptance")
    old, new = applicability(old_context["version_vector"]), applicability(new_context["version_vector"])
    differences = [{"key": k, "old": old.get(k), "new": new.get(k)} for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
    need(differences, "SAME_APPLICABILITY", "A separate semantic replacement protocol would be required")
    return differences


def verify_archive(archive, old_row, roots, nonroots):
    need(archive.get("schema") == "researchos.w04.historical-acceptance-archive.v1"
         and archive.get("scope") == "HISTORICAL_ONLY_NOT_CURRENT_ROOT", "ARCHIVE_SCHEMA", archive)
    need(archive["owner"] == old_row and archive["roots"] == roots and archive["nonroots"] == nonroots
         and archive["original_evidence"] == old_row["evidence"], "ARCHIVE_INCOMPLETE_OR_REWRITTEN", archive)


def full_state_cas(raw, expected_sha, expected_old_row):
    need(sha(raw) == expected_sha, "FULL_STATE_CAS", "Even an unrelated task update requires a new plan")
    state = strict(raw)
    owners = [r for r in state["steps"] if r["id"] == "W04-99"]
    need(len(owners) == 1 and owners[0] == expected_old_row, "OLD_ROW_CAS", "W04-99")
    return state


def historical(audit, freeze):
    old_row = freeze["owner"]
    original_state = audit.doc(freeze["state_ref"])
    need(next(r for r in original_state["steps"] if r["id"] == "W04-99") == old_row, "HISTORICAL_STATE_ROW", freeze)
    roots, nonroots = root_inventory(audit, old_row, 7)
    need(len(nonroots) == 4, "OLD_NONROOT_COUNT", nonroots)
    chain = delivery_chain(audit, roots, old_row)
    context = chain["context"]
    old_refs = [{"path": "execution/v2.4/" + r["path"], "sha256": r["sha256"]} for r in old_row["evidence"]]
    discover_historical_snapshots(audit, old_refs + [OLD_REGISTERED])
    expected = {(r["path"], r["sha256"]) for group in GROUPS for r in context["version_vector"][group]}
    manifests = []
    for name, digest in sorted(audit.bound_metadata):
        if name.endswith("/source_snapshot_manifest.json"):
            candidate = audit.doc({"path": name, "sha256": digest})
            manifests.append((candidate, {"path": name, "sha256": digest}))
    need(manifests, "OLD_BOUND_SOURCE_MANIFEST_MISSING", "No new source copies can repair the old chain")
    for snapshot, snapshot_ref in manifests:
        run_dir = Path(snapshot_ref["path"]).parent.as_posix()
        # Each historical manifest must cover its own actually bound vector.
        # The earlier repaired run must never be relabelled the final run.
        vector = historical_manifest_vector(audit, snapshot, snapshot_ref)
        manifest_expected = {(r["path"], r["sha256"]) for group in GROUPS for r in vector[group]}
        mapped = {}
        for item in snapshot["snapshots"]:
            original, frozen = item["original_ref"], item["snapshot_ref"]
            key = (original["path"], original["sha256"])
            need(key not in mapped and frozen["path"].startswith(run_dir + "/source_snapshot/")
                 and frozen["sha256"] == original["sha256"], "OLD_SOURCE_SNAPSHOT_BINDING", item)
            audit.bytes(frozen)
            mapped[key] = frozen
        need(set(mapped) == manifest_expected, "OLD_SOURCE_SNAPSHOT_COVERAGE", "exact historical manifest's own vector union")
    if "registry_snapshot_ref" in context:
        old_registry = context["registry_ref"]
        frozen_registry = context["registry_snapshot_ref"]
        need(old_registry["path"] == REGISTRY and old_registry["sha256"] == frozen_registry["sha256"], "OLD_REGISTRY_SNAPSHOT", context)
        audit.bytes(frozen_registry)
        audit.applicability[(old_registry["path"], old_registry["sha256"])] = frozen_registry
    invocation = audit.doc(OLD_REGISTERED)
    result = audit.doc(invocation["stdout"])
    need(invocation["exit_code"] == 0 and invocation["actual_argv"][-2:] == ["--phase", "registered"]
         and result["phase"] == "registered" and result["integrity"] == "PASS"
         and result["formal_accepted_count"] == 3 and set(result["eligible_owned_cases"]) == set(CASES)
         and result["assertion_count"] == 10, "OLD_REGISTERED_PASS_PROVENANCE", invocation)
    audit.closure([{"path": "execution/v2.4/" + r["path"], "sha256": r["sha256"]} for r in old_row["evidence"]], True)
    audit.closure(OLD_REGISTERED, True)
    for _, snapshot_ref in manifests:
        audit.closure(snapshot_ref, True)
    audit.finish()
    return {"owner": old_row, "roots": roots, "nonroots": nonroots, "chain": chain,
            "graph_hashes": deepcopy(audit.observed), "applicability_observations": deepcopy(audit.drifts),
            "snapshot_mapping_refs": [{"original_ref": {"path": key[0], "sha256": key[1]}, "bindings": entries}
                                      for key, entries in sorted(audit.snapshot_bindings.items())],
            "product_source_differences": [item for item in audit.drifts if (item["path"], item["old_sha256"]) in expected and not item["path"].startswith("execution/")],
            "shared_tool_source_differences": [item for item in audit.drifts if item["path"].startswith("execution/") and source_path(item["path"])],
            "pre_acceptance_repair_history_refs": [{"path": name, "sha256": digest} for name, digest in sorted(audit.bound_metadata) if "registration_repair" in name or "registration-repair" in name],
            "historical_mutable_observations": deepcopy(audit.historical_observations),
            "snapshot_ref": manifests[0][1], "all_bound_snapshot_refs": [ref for _, ref in manifests], "registered_pass_ref": OLD_REGISTERED}


AMENDMENT = {"path": BASE + "revalidation_scope_review_codex/e4e2caf5-70e2-4568-86e0-1611eb0dee5a/acyclic_transition_scope_amendment.json",
             "sha256": "ba95eb6c1608ea201ac40aed1988d023b556d1ae4238aeba396d512508890d65"}
RESOLVER = {"version": "w04-explicit-applicability-transition-two-slots-v1",
            "encoding": "UTF-8 strict JSON; ensure_ascii=False sort_keys=True separators=(',',':') allow_nan=False",
            "slots": {"/evidence/-1": "self_plan_ref", "/accepted_at": "actual_apply_time"}}
TAG = "$w04_transition_slot"
INVARIANTS = ["OLD_COMPLETE_PROVENANCE_PRESERVED", "OLD_SEMANTIC_ACCEPTANCE_UNDISPUTED", "CHANGED_APPLICABILITY_SAME_BASELINE_IDS_MODES",
              "NEW_REAL_DISTINCT_ACTORS_AND_DELIVERY", "EXACT_REMOVE3_ADD3_KEEP4", "LATEST_FULL_STATE_CAS", "UNCHANGED_V1_GATES",
              "EXACT_HELPER_TESTS_RESOLVER", "ONLY_TWO_SIGNED_SLOTS", "DEFERRED_FINAL_TIME_AND_ROW_INDEPENDENT_VERIFICATION"]


def slots(template):
    found = {}
    def visit(value, pointer):
        if isinstance(value, dict):
            if TAG in value:
                need(set(value) == {TAG}, "RESOLVER_SLOT_SHAPE", pointer)
                found[pointer] = value[TAG]
            else:
                for key, child in value.items():
                    visit(child, pointer + "/" + key)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                visit(child, pointer + "/" + str(i))
    visit(template, "")
    expected = {"/accepted_at": "actual_apply_time", "/evidence/" + str(len(template["evidence"]) - 1): "self_plan_ref"}
    need(found == expected, "RESOLVER_CLOSED_WORLD", found)
    need(template["accepted_at"] == {TAG: "actual_apply_time"} and template["evidence"][-1] == {TAG: "self_plan_ref"},
         "RESOLVER_SLOT_LOCATION", template)


def template_for(old, new_roots, archive_ref, assignment, started_at):
    template = deepcopy(old["owner"])
    template.update(executor_id=assignment["executor_id"], verifier_id=assignment["reviewer_id"], started_at=started_at,
        accepted_at={TAG: "actual_apply_time"},
        execution_note="Explicit changed-applicability W04 revalidation: C03/C04/A01,10 assertions,6 bindings,5 gates,11 actual native dispatches. Historical verdict preserved; v1 supersession remains unsupported.",
        scope_note="New CURRENT registration via independently authorized exact transition; archive contributes zero cases. Final time/row requires independent registered-stage verification.")
    def state_ref(value):
        need(value["path"].startswith("execution/v2.4/"), "ROW_REFERENCE_SCOPE", value)
        return {"path": value["path"].removeprefix("execution/v2.4/"), "sha256": value["sha256"]}
    template["evidence"] = deepcopy(old["nonroots"]) + [state_ref(new_roots[k]) for k in ("context", "review", "issuance")]
    template["evidence"] += [state_ref(archive_ref), {TAG: "self_plan_ref"}]
    slots(template)
    return template


def resolve_row(template, plan_ref, lower_bound):
    slots(template)
    # The clock is chosen here at actual apply; no CLI timestamp argument exists.
    applied_at = now()
    need(at(applied_at) >= at(lower_bound), "APPLY_BEFORE_ACTUAL_DELIVERY", lower_bound)
    result = deepcopy(template)
    need(plan_ref["path"].startswith(BASE + "integration_codex/") and plan_ref["path"].endswith("transition_plan.json"),
         "PLAN_REFERENCE_SCOPE", plan_ref)
    result["evidence"][-1] = {"path": plan_ref["path"].removeprefix("execution/v2.4/"), "sha256": plan_ref["sha256"]}
    result["accepted_at"] = applied_at
    return result


def verify_resolved(template, resolved, plan_ref, lower_bound):
    slots(template)
    expected = deepcopy(template)
    expected["accepted_at"] = resolved.get("accepted_at")
    expected["evidence"][-1] = {"path": plan_ref["path"].removeprefix("execution/v2.4/"), "sha256": plan_ref["sha256"]}
    need(resolved == expected, "RESOLVED_ROW_CHANGED", "Only the two signed slots may resolve")
    need(at(lower_bound) <= at(resolved["accepted_at"]) <= at(now()), "ACTUAL_APPLY_TIME", resolved["accepted_at"])


def actual_message(message, sender, hashes):
    need(message.get("sender") == sender and message.get("recorded_by") == ROOT_ACTOR
         and message.get("recipient") == ROOT_ACTOR and message.get("event_type") in {"MESSAGE", "FINAL_ANSWER"},
         "ACTUAL_ROOT_MESSAGE", message)
    content = message.get("content")
    need(isinstance(content, str) and all(h in content for h in hashes) and message.get("received_at")
         and isinstance(message.get("event_locator"), dict), "ACTUAL_ROOT_MESSAGE", message)
    locator = message["event_locator"]
    need(locator.get("task_name") == "/root" and locator.get("sender_task") == sender.removeprefix("codex:")
         and locator.get("message_type") == message["event_type"] and bool(locator.get("source"))
         and locator.get("message_content_sha256") == sha(content.encode()), "ACTUAL_EVENT_LOCATOR", locator)
    at(message["received_at"])


def authorization(review, plan_ref, plan, message, review_ref, assigned_reviewer):
    need(review.get("schema") == "researchos.w04.transition-independent-review.v1" and
         review.get("decision") == "APPROVED_CURRENT_APPLICABILITY_TRANSITION" and review.get("reviewer_id") == assigned_reviewer,
         "TRANSITION_REVIEW", review)
    need(review.get("plan_ref") == plan_ref and review.get("stable_row_sha256") == plan["stable_row_sha256"]
         and review.get("helper_ref") == plan["helper_ref"] and review.get("tests_ref") == plan["tests_ref"]
         and review.get("resolver") == RESOLVER and review.get("invariants") == INVARIANTS
         and review.get("old_acceptance_disputed") is False and review.get("deferred_final_time_verification") is True
         and review.get("missing") == [] and review.get("failed") == [], "TRANSITION_REVIEW_BINDING", review)
    need(object_sha(plan["stable_row"]) == plan["stable_row_sha256"] and plan["resolver"] == RESOLVER,
         "STABLE_ROW_CHANGED", plan_ref)
    slots(plan["stable_row"])
    actual_message(message, assigned_reviewer, [plan_ref["sha256"], review_ref["sha256"]])
    need(message.get("review_ref") == review_ref and message.get("plan_ref") == plan_ref,
         "TRANSITION_MESSAGE_BINDING", message)
    need(at(review["issued_at"]) <= at(message["received_at"]), "TRANSITION_DELIVERY_TIME", message)


def scope(audit):
    registration = audit.doc({"path": SCOPE_DIR + "scope_registration.json", "sha256": SCOPE_SHA})
    review = audit.doc(registration["review_ref"])
    need(registration["review_ref"]["sha256"] == SCOPE_REVIEW_SHA and registration["actor"] == ROOT_ACTOR
         and registration["actual_scope_message_received"] is True, "SCOPE_AUTHORIZATION", registration)
    assignment = audit.doc({"path": SCOPE_DIR + "actor_assignment.json", "sha256": ASSIGNMENT_SHA})
    need(registration["actor_assignment_ref"]["sha256"] == ASSIGNMENT_SHA and assignment["assigned_by"] == ROOT_ACTOR
         and assignment["executor_namespace"] == BASE + "executor_revalidation_codex/"
         and len({assignment[k].casefold() for k in ("executor_id", "reviewer_id", "root_id")}) == 3, "ACTOR_ASSIGNMENT", assignment)
    amendment = audit.doc(AMENDMENT)
    history_scope = audit.doc(HISTORY_SCOPE)
    need(history_scope.get("registered_by") == ROOT_ACTOR and history_scope.get("helper_requires_independent_fix_review") is True,
         "HISTORY_SCOPE_AUTHORIZATION", history_scope)
    need(amendment["parent_scope_ref"] == registration["review_ref"]
         and amendment["decision"] == "PROTOCOL_SCOPE_READY_PENDING_IMPLEMENTATION_REVIEW", "RESOLVER_SCOPE", amendment)
    return registration, review, assignment


def tools_and_spec(audit):
    public_path = path_in(audit.repo, "execution/v2.4/formal_case_index.py")
    need(sha(public_path.read_bytes()[:51719]) == PREFIX_SHA, "FROZEN_PREFIX_CHANGED", public_path)
    public_ref = reference(audit.repo, public_path)
    audit.bytes(public_ref)
    public = load_module(public_path, "w04_transition_public_unchanged")
    validator_path = path_in(audit.repo, BASE + "formal_validator_codex/validate.py")
    audit.bytes(reference(audit.repo, validator_path))
    validator = load_module(validator_path, "w04_transition_validator_unchanged")
    current_spec, _ = audit.current("execution/v2.4/current_spec.json")
    spec = path_in(audit.repo, current_spec["snapshot_relative_to_candidate_branch_worktree"])
    need(sha((spec / "contracts/execution.plan.json").read_bytes()) == public.FROZEN_HASHES["execution.plan.json"], "FROZEN_PLAN", spec)
    return public, validator, spec


def unchanged_check(audit, validator, spec, roots, phase, out, stem):
    try:
        result = validator.check(audit.repo, audit.repo / STATE, spec, audit.repo / roots["context"]["path"],
                                 audit.repo / roots["review"]["path"], audit.repo / roots["issuance"]["path"], phase)
        save(out / (stem + ".json"), {"status": "PASS", "phase": phase, "result": result,
             "execution_kind": "UNCHANGED_READ_ONLY_VALIDATOR_API", "product_commands": 0})
    except BaseException as exc:
        save(out / (stem + ".json"), {"status": "FAIL", "phase": phase, "error": str(exc), "traceback": traceback.format_exc()})
        raise
    need(result["integrity"] == "PASS" and result["formal_accepted_count"] == (3 if phase == "registered" else 0)
         and set(result["eligible_owned_cases"]) == set(CASES), "V1_PHASE_RESULT", result)
    return result


def collection_completion(audit, completion_ref, new, assignment):
    completion = audit.doc(completion_ref)
    need(completion.get("schema") == "researchos.w04.collection-completion.v1"
         and completion.get("executor_id") == assignment["executor_id"], "COLLECTION_COMPLETION", completion)
    index_ref = new["context"]["execution_index"]
    run_dir = Path(index_ref["path"]).parent.as_posix()
    need(run_dir.startswith(assignment["executor_namespace"] + "runs/")
         and Path(run_dir).name == new["index"]["run_id"], "COLLECTION_RUN_IDENTITY", run_dir)
    names = ["compiled-inputs-before.json", "compiled-inputs-preproof.json", "compiled-inputs-prepublish.json", "compiled-inputs-after.json"]
    captures = completion.get("capture_refs", {})
    need(set(captures) == set(names), "COMPILED_CAPTURE_COVERAGE", captures)
    files = None
    for name in names:
        ref = captures[name]
        need(ref["path"] == run_dir + "/" + name, "COLLECTION_RUN_ALIAS", ref)
        doc = audit.doc(ref)
        need(doc.get("schema") == "researchos.w04.auxiliary-compiled-inputs.v1" and doc.get("files"), "COMPILED_CAPTURE_SHAPE", ref)
        current_files = doc["files"]
        need(len({item["path"].casefold() for item in current_files}) == len(current_files), "COMPILED_DUPLICATE_PATH", ref)
        if files is None:
            files = current_files
            invocation = audit.doc(doc["invocation_ref"])
            need(invocation["exit_code"] == 0 and invocation["actual_argv"][1:5] == ["list", "-deps", "-test", "-json"], "COMPILED_DEPENDENCY_INVOCATION", invocation)
            audit.closure(doc["invocation_ref"])
        else:
            need(doc.get("unchanged") is True and current_files == files, "COMPILED_CAPTURE_DRIFT", ref)
    file_map = {}
    for item in files:
        p = Path(item["path"])
        need(p.is_absolute() and p.resolve() == p and p.is_file(), "COMPILED_INPUT_PATH", item)
        need(sha(p.read_bytes()) == item["sha256"], "COMPILED_INPUT_DRIFT", item)
        file_map[str(p)] = item["sha256"]
        if p.is_relative_to(audit.repo):
            audit.bytes({"path": p.relative_to(audit.repo).as_posix(), "sha256": item["sha256"]})
        else:
            audit.external_inputs[str(p)] = item["sha256"]
    sources = completion.get("collector_source_refs", [])
    names9 = {"collect.py", "bridge.py", "test_bridge.py", "parent_driver.py", "evidence_module.py", "expected.json", "frozen_inputs/commands-v24-r37.json", "frozen_inputs/legacy_entries.json", "test_collect.py"}
    need(len(sources) == 9 and {ref["path"].removeprefix(assignment["executor_namespace"]) for ref in sources} == names9,
         "COLLECTOR_SOURCE_COVERAGE", sources)
    for ref in sources:
        audit.bytes(ref)
        need(file_map.get(str(audit.repo / ref["path"])) == ref["sha256"], "COLLECTOR_COMPILED_BINDING", ref)
    for key, filename in (("handoff_ref", "handoff.json"), ("proof_ref", "proof.json")):
        need(completion[key]["path"] == run_dir + "/" + filename, "COLLECTION_RUN_ALIAS", completion[key])
    handoff, proof = audit.doc(completion["handoff_ref"]), audit.doc(completion["proof_ref"])
    need(handoff["execution_index"] == index_ref and handoff["status"] == "EXECUTED_PENDING_INDEPENDENT_REVIEW"
         and proof["run_id"] == new["index"]["run_id"] and proof["status"] == "PASS", "COLLECTION_RESULT_BINDING", completion)
    outer = audit.doc(completion["outer_invocation_ref"])
    argv = outer["actual_argv"]
    lock, _ = audit.current("execution/toolchains/locked.json")
    python = lock["tools"]["python"]
    need(outer["exit_code"] == 0 and Path(outer["cwd"]).resolve() == audit.repo
         and str(audit.repo / assignment["executor_namespace"] / "collect.py") in argv
         and "--prepare-only" not in argv, "COLLECTOR_FINAL_EXIT", outer)
    need(Path(argv[0]).resolve() == Path(python["path"]).resolve()
         and file_map.get(str(Path(python["path"]))) == python["sha256"]
         and outer.get("executable_sha256") == python["sha256"], "COLLECTOR_LOCKED_EXECUTABLE", outer)
    for option, value in (("--executor-id", assignment["executor_id"]), ("--verifier-id", assignment["reviewer_id"]), ("--root-id", ROOT_ACTOR)):
        need(argv.count(option) == 1 and argv[argv.index(option) + 1] == value, "COLLECTOR_ACTUAL_ACTOR", argv)
    option = "--actor-assignment"
    actual_assignment, actual_assignment_ref = audit.current(SCOPE_DIR + "actor_assignment.json")
    need(argv.count(option) == 1 and Path(argv[argv.index(option) + 1]).resolve() == audit.repo / SCOPE_DIR / "actor_assignment.json"
         and actual_assignment == assignment
         and file_map.get(str(audit.repo / SCOPE_DIR / "actor_assignment.json")) == actual_assignment_ref["sha256"],
         "COLLECTOR_ASSIGNMENT_BINDING", argv)
    need(at(outer["started_at"]) >= at(assignment["assigned_at"]), "COLLECTION_BEFORE_ASSIGNMENT", outer)
    need(at(outer["started_at"]) <= at(proof["started_at"]) <= at(proof["ended_at"]) <= at(outer["ended_at"]) <= at(new["review"]["issued_at"]), "COLLECTOR_ACTUAL_TIME", outer)
    stdout = audit.bytes(outer["stdout"])
    audit.bytes(outer["stderr"])
    result = strict(stdout)
    need(result["status"] == "EXECUTED_PENDING_INDEPENDENT_REVIEW" and result["execution_index"] == index_ref
         and Path(result["run"]).resolve() == audit.repo / run_dir, "COLLECTOR_STDOUT_RUN", result)
    sidecar_ref = collection_review(audit, completion_ref, completion, new, assignment, outer)
    audit.closure(completion_ref)
    return {"completion": completion, "sidecar_ref": sidecar_ref}


def collection_review(audit, completion_ref, completion, new, assignment, outer):
    review = new["review"]
    need("collection_completion_ref" not in review and "collection_source_order_review" not in review,
         "V1_UNKNOWN_FIELD", "Collection attestation belongs in legal semantic raw evidence")
    sidecars = []
    rows = review.get("owned_case_verdicts", [])
    need(len(rows) == 3 and {row["case_id"] for row in rows} == set(CASES), "COLLECTION_SIDECAR_BINDING", "all case verdicts")
    for row in rows:
        found = []
        for raw_ref in row["semantic_review"]["raw_evidence_refs"]:
            if raw_ref.get("locator") != {"json_pointer": "/collection_source_order_review"}:
                continue
            need(set(raw_ref) == {"path", "sha256", "locator"}, "COLLECTION_SIDECAR_BINDING", raw_ref)
            ref = {key: raw_ref[key] for key in ("path", "sha256")}
            need(ref["path"].startswith(BASE + "independent_revalidation_codex/"), "COLLECTION_SIDECAR_NAMESPACE", ref)
            found.append(ref)
        need(len(found) == 1, "COLLECTION_SIDECAR_BINDING", row["case_id"])
        sidecars += found
    need(all(ref == sidecars[0] for ref in sidecars), "COLLECTION_SIDECAR_BINDING", sidecars)
    ref = sidecars[0]
    sidecar = audit.doc(ref)
    fields = {"schema", "scope", "task_id", "step_id", "reviewer_id", "executor_id", "issued_at", "current_context_ref",
              "execution_index_ref", "collection_completion_ref", "run_id", "capture_refs", "collector_source_refs",
              "outer_invocation_ref", "collection_source_order_review"}
    need(set(sidecar) == fields and sidecar["schema"] == "researchos.w04.collection-independent-attestation.v1"
         and sidecar["scope"] == "INDEPENDENT_COLLECTION_ORDER_AND_COMPLETION" and sidecar["task_id"] == "W04"
         and sidecar["step_id"] == "W04-99", "COLLECTION_SIDECAR_SHAPE", sidecar)
    need(sidecar["reviewer_id"] == assignment["reviewer_id"] == review["verifier_id"]
         and sidecar["executor_id"] == assignment["executor_id"] == review["executor_id"]
         and sidecar["reviewer_id"] not in {sidecar["executor_id"], ROOT_ACTOR}, "COLLECTION_SIDECAR_ACTOR", sidecar)
    need(sidecar["current_context_ref"] == review["current_context_ref"]
         and sidecar["execution_index_ref"] == new["context"]["execution_index"] == review["evidence_index_ref"]
         and sidecar["collection_completion_ref"] == completion_ref and sidecar["run_id"] == new["index"]["run_id"]
         and all(sidecar[key] == completion[key] for key in ("capture_refs", "collector_source_refs", "outer_invocation_ref")),
         "COLLECTION_SIDECAR_TUPLE", sidecar)
    need(sidecar["collection_source_order_review"] == COLLECTION_ORDER, "COLLECTION_SIDECAR_ORDER", sidecar)
    need(at(outer["ended_at"]) <= at(sidecar["issued_at"]) <= at(review["issued_at"]), "COLLECTION_SIDECAR_TIME", sidecar)
    audit.closure(ref)
    return ref


def audit_inputs(repo, roots, out, prefix, collection_ref):
    audit = Audit(repo)
    registration, scope_review, assignment = scope(audit)
    freeze = audit.doc(assignment["old_owner_ref"])
    old = historical(audit, freeze)
    current_raw = path_in(repo, STATE).read_bytes()
    full_state_cas(current_raw, sha(current_raw), old["owner"])
    new = delivery_chain(audit, roots, assignment=assignment)
    new["collection_review_ref"] = collection_completion(audit, collection_ref, new, assignment)["sidecar_ref"]
    actual_message(new["message"], assignment["reviewer_id"], [roots["review"]["sha256"]])
    need(at(new["review"]["issued_at"]) <= at(new["message"]["received_at"]) <= at(new["issuance"]["observed_at"]), "NEW_ACTUAL_DELIVERY_TIME", new["message"])
    differences = require_changed(old["chain"]["context"], new["context"], old["chain"]["review"], new["review"])
    for value in roots.values():
        audit.closure(value)
    public, validator, spec = tools_and_spec(audit)
    unchanged_check(audit, validator, spec, roots, "reviewed", out, prefix + "-reviewed-integrity")
    audit.finish()
    return audit, old, new, assignment, differences, current_raw, public, validator, spec


def source_approval(audit, review_ref, message_ref, assignment):
    review, message = audit.doc(review_ref), audit.doc(message_ref)
    need(review.get("schema") == "researchos.w04.transition-source-review.v1" and review.get("decision") == "SOURCE_READY"
         and review.get("reviewer_id") == assignment["reviewer_id"] and review.get("missing") == [] and review.get("failed") == [],
         "SOURCE_APPROVAL", review)
    need(review.get("helper_sha256") == sha(Path(__file__).read_bytes())
         and review.get("tests_sha256") == sha(Path(__file__).with_name("test_register.py").read_bytes()), "SOURCE_APPROVAL_HASH", review)
    controls = audit.doc(review["controls_ref"])
    need(controls["scope"] == "SYNTHETIC_NOT_PRODUCT" and controls["tests_run"] >= 22
         and controls["failures"] == controls["errors"] == controls["skipped"] == 0
         and controls["source_ref"]["sha256"] == review["helper_sha256"]
         and controls["tests_sha256"] == review["tests_sha256"], "SOURCE_CONTROLS", controls)
    actual_message(message, assignment["reviewer_id"], [review_ref["sha256"], review["helper_sha256"]])
    need(message.get("review_ref") == review_ref and at(review["issued_at"]) <= at(message["received_at"]), "SOURCE_MESSAGE_BINDING", message)


def prepare(repo, out, roots, source_review_ref, source_message_ref, collection_ref):
    audit, old, new, assignment, differences, state_raw, public, _, spec = audit_inputs(repo, roots, out, "prepare", collection_ref)
    # Observe W07 currentness truthfully; no repair/recollection occurs here.
    current = public.derive_formal_cases(repo, repo / STATE, spec / "contracts/execution.plan.json")
    save(out / "preparation-formal-index.json", current)
    w07 = next(row for row in current["owners"] if row["task_id"] == "W07")
    save(out / "w07-applicability-observation.json", {"scope": "READ_ONLY_NO_A05_REISSUANCE", "owner": w07,
         "instruction": "Preserve any actual stale reason; final W07 full-vector workflow must revalidate after shared registry/source changes. This tool never claims simultaneous CURRENT without valid exact vectors."})
    source_approval(audit, source_review_ref, source_message_ref, assignment)
    graph = {"schema": "researchos.w04.old-graph-manifest.v1", "historical_files": old["graph_hashes"],
             "permitted_applicability_differences": old["applicability_observations"], "old_registered_pass_ref": old["registered_pass_ref"],
             **{key: old[key] for key in ("snapshot_mapping_refs", "product_source_differences", "shared_tool_source_differences", "pre_acceptance_repair_history_refs", "historical_mutable_observations")}}
    save(out / "old_graph_manifest.json", graph)
    archive = {"schema": "researchos.w04.historical-acceptance-archive.v1", "scope": "HISTORICAL_ONLY_NOT_CURRENT_ROOT",
               "owner": old["owner"], "roots": old["roots"], "nonroots": old["nonroots"], "original_evidence": old["owner"]["evidence"],
               "freeze_ref": assignment["old_owner_ref"], "source_snapshot_ref": old["snapshot_ref"],
               "all_bound_source_snapshot_refs": old["all_bound_snapshot_refs"],
               "graph_manifest_ref": reference(repo, out / "old_graph_manifest.json"), "semantic_verdict_preserved": True}
    verify_archive(archive, old["owner"], old["roots"], old["nonroots"])
    save(out / "historical_acceptance_archive.json", archive)
    archive_ref = reference(repo, out / "historical_acceptance_archive.json")
    starts = [audit.doc(new["index"]["cases"][cid]["run_receipt"])["started_at"] for cid in CASES]
    stable = template_for(old, roots, archive_ref, assignment, min(starts, key=at))
    helper_ref = reference(repo, Path(__file__).resolve())
    tests_ref = reference(repo, Path(__file__).resolve().with_name("test_register.py"))
    audit.bytes(helper_ref)
    audit.bytes(tests_ref)
    exclusive(out / "latest_state.original.json", state_raw)
    plan = {"schema": "researchos.w04.explicit-applicability-transition-plan.v1", "status": "PENDING_INDEPENDENT_PLAN_REVIEW_NOT_ACCEPTED",
            "created_at": now(), "actor": ROOT_ACTOR, "resolver": RESOLVER, "invariants": INVARIANTS,
            "scope_ref": {"path": SCOPE_DIR + "scope_registration.json", "sha256": SCOPE_SHA}, "amendment_ref": AMENDMENT,
            "source_review_ref": source_review_ref, "source_review_message_ref": source_message_ref,
            "collection_completion_ref": collection_ref, "collection_review_ref": new["collection_review_ref"],
            "historical_purpose_scope_ref": HISTORY_SCOPE, "external_compiled_input_hashes": dict(audit.external_inputs),
            "assignment_ref": {"path": SCOPE_DIR + "actor_assignment.json", "sha256": ASSIGNMENT_SHA},
            "expected_full_state_sha256": sha(state_raw), "latest_state_ref": reference(repo, out / "latest_state.original.json"),
            "old_row": old["owner"], "old_row_sha256": object_sha(old["owner"]), "old_roots": old["roots"],
            "old_nonroots": old["nonroots"], "archive_ref": archive_ref, "new_roots": roots,
            "case_actual_message_ref": new["issuance"]["message_ref"], "registry_snapshot_ref": new["context"]["registry_snapshot_ref"],
            "registry_sha256": sha((repo / REGISTRY).read_bytes()), "applicability_differences": differences,
            "stable_row": stable, "stable_row_sha256": object_sha(stable), "helper_ref": helper_ref, "tests_ref": tests_ref,
            "input_hashes": dict(audit.observed), "historical_applicability_observations": audit.drifts,
            "deferred_final_time_verification": True, "formal_acceptance_delta": 0}
    audit.finish()
    full_state_cas((repo / STATE).read_bytes(), plan["expected_full_state_sha256"], old["owner"])
    save(out / "transition_plan.json", plan)
    return {"status": "PLAN_ONLY_PENDING_INDEPENDENT_REVIEW", "plan_ref": reference(repo, out / "transition_plan.json"), "formal_acceptance_delta": 0}


def verify_plan_current(audit, plan, old, new, assignment, differences, committed=None):
    need(plan["schema"] == "researchos.w04.explicit-applicability-transition-plan.v1" and plan["resolver"] == RESOLVER
         and plan["invariants"] == INVARIANTS and plan["scope_ref"]["sha256"] == SCOPE_SHA and plan["amendment_ref"] == AMENDMENT,
         "PLAN_PROTOCOL", plan)
    need(plan["old_row"] == old["owner"] and plan["old_row_sha256"] == object_sha(old["owner"])
         and plan["old_roots"] == old["roots"] and plan["old_nonroots"] == old["nonroots"], "PLAN_OLD_HISTORY", plan)
    archive = audit.doc(plan["archive_ref"])
    verify_archive(archive, old["owner"], old["roots"], old["nonroots"])
    starts = [audit.doc(new["index"]["cases"][cid]["run_receipt"])["started_at"] for cid in CASES]
    expected = template_for(old, plan["new_roots"], plan["archive_ref"], assignment, min(starts, key=at))
    need(plan["stable_row"] == expected and object_sha(expected) == plan["stable_row_sha256"], "STABLE_ROW_CHANGED", "exact reconstructed template")
    need(plan["helper_ref"] == reference(audit.repo, Path(__file__).resolve()) and
         plan["tests_ref"] == reference(audit.repo, Path(__file__).resolve().with_name("test_register.py")), "HELPER_CHANGED", "helper/tests raw SHA")
    source_approval(audit, plan["source_review_ref"], plan["source_review_message_ref"], assignment)
    collection = collection_completion(audit, plan["collection_completion_ref"], new, assignment)
    need(collection["sidecar_ref"] == plan["collection_review_ref"] and plan["historical_purpose_scope_ref"] == HISTORY_SCOPE,
         "PLAN_COLLECTION_HISTORY_BINDING", plan)
    need(audit.external_inputs == plan["external_compiled_input_hashes"], "COMPILED_EXTERNAL_DRIFT", "actual external dependencies")
    need(plan["applicability_differences"] == differences and plan["case_actual_message_ref"] == new["issuance"]["message_ref"]
         and plan["registry_snapshot_ref"] == new["context"]["registry_snapshot_ref"], "PLAN_GRAPH_CHANGED", plan)
    own_write = authenticate_committed_state(audit, *committed) if committed is not None else None
    if own_write is not None:
        need(own_write["plan"] == plan, "OWN_WRITE_PLAN_BINDING", "signed plan bytes")
    for name, expected_hash in plan["input_hashes"].items():
        if name == STATE and own_write is not None:
            need(expected_hash == own_write["before"] == plan["expected_full_state_sha256"], "OWN_WRITE_INPUT_BINDING", name)
            audit.bytes({"path": name, "sha256": own_write["after"]})
        else:
            audit.bytes({"path": name, "sha256": expected_hash})
    need(sha((audit.repo / REGISTRY).read_bytes()) == plan["registry_sha256"], "NEEDS_REVALIDATION", "registry binding changed")
    audit.finish()


def atomic_state(repo, expected_hash, raw, out):
    target = path_in(repo, STATE)
    temporary = out / ("atomic-payload-" + uuid.uuid4().hex + ".tmp")
    exclusive(temporary, raw)
    need(sha(target.read_bytes()) == expected_hash, "FULL_STATE_CAS", "immediately before atomic replacement")
    os.replace(temporary, target)
    need(sha(target.read_bytes()) == sha(raw), "READBACK_HASH", STATE)


def recover(repo, journal, out):
    need(journal["schema"] == "researchos.w04.transition-pending-intent.v1" and journal["target"] == STATE
         and journal["actor"] == ROOT_ACTOR and journal["project_id"] == PROJECT, "RECOVERY_JOURNAL", journal)
    need(not (out / "completed.json").exists(), "ALREADY_COMPLETED", out)
    audit = Audit(repo)
    for key in ("original_state_ref", "desired_state_ref"):
        need(path_in(repo, journal[key]["path"]).parent == out, "RECOVERY_BACKUP_SCOPE", journal[key])
    original = audit.bytes(journal["original_state_ref"])
    desired = audit.bytes(journal["desired_state_ref"])
    plan = audit.doc(journal["plan_ref"])
    original_doc = full_state_cas(original, plan["expected_full_state_sha256"], plan["old_row"])
    need(journal["resolver"] == RESOLVER and journal["actual_apply_time"] == journal["resolved_row"]["accepted_at"]
         and object_sha(journal["resolved_row"]) == journal["resolved_row_sha256"], "RECOVERY_RESOLVER", journal)
    verify_resolved(plan["stable_row"], journal["resolved_row"], journal["plan_ref"], journal["lower_time_bound"])
    expected_doc = deepcopy(original_doc)
    expected_doc["steps"] = [journal["resolved_row"] if row["id"] == "W04-99" else row for row in expected_doc["steps"]]
    need(strict(desired) == expected_doc and audit.doc(journal["resolved_row_raw_ref"]) == journal["resolved_row"],
         "RECOVERY_ONLY_AUTHORIZED_ROW", journal)
    audit.finish()
    current = (repo / STATE).read_bytes()
    if sha(current) == sha(original):
        status = "ALREADY_ORIGINAL_NO_ACCEPTANCE"
    elif sha(current) == sha(desired):
        atomic_state(repo, sha(desired), original, out)
        status = "EXPLICIT_AUDITED_RECOVERY_TO_ORIGINAL"
    else:
        status = "PARTIAL_REGISTRATION_FOREIGN_STATE_NOT_TOUCHED"
    receipt = {"status": status, "at": now(), "scope": "RECOVERY_NOT_CURRENT_ACCEPTANCE",
               "canonical_sha256": sha((repo / STATE).read_bytes()), "counter_reset": False,
               "original_sha256": sha(original), "desired_sha256": sha(desired), "plan_ref": journal["plan_ref"],
               "origin_key": "W04-transition-recovery|" + uuid.uuid4().hex, "formal_acceptance_delta": 0}
    save(out / ("recovery-" + uuid.uuid4().hex + ".json"), receipt)
    return receipt


def verify_commit_row(plan, plan_ref, commit, intent, actual_row):
    need(commit["plan_ref"] == plan_ref and intent["plan_ref"] == plan_ref and commit["resolver"] == RESOLVER
         and intent["resolver"] == RESOLVER, "COMMIT_PLAN_BINDING", commit)
    need(actual_row == commit["resolved_row"] == intent["resolved_row"]
         and object_sha(actual_row) == commit["resolved_row_sha256"] == intent["resolved_row_sha256"], "COMMIT_ROW_HASH", actual_row)
    verify_resolved(plan["stable_row"], actual_row, plan_ref, intent["lower_time_bound"])
    need(actual_row["accepted_at"] == intent["actual_apply_time"] == commit["actual_apply_time"], "COMMIT_TIME_BINDING", commit)


def authenticate_intent_state(audit, plan_ref, intent_ref):
    plan, intent = audit.doc(plan_ref), audit.doc(intent_ref)
    need(intent.get("schema") == "researchos.w04.transition-pending-intent.v1"
         and intent.get("target") == STATE and intent.get("project_id") == PROJECT
         and intent.get("actor") == ROOT_ACTOR and intent.get("plan_ref") == plan_ref
         and intent.get("resolver") == RESOLVER, "OWN_WRITE_INTENT", intent)
    directory = Path(intent_ref["path"]).parent
    for key in ("original_state_ref", "desired_state_ref", "resolved_row_raw_ref"):
        need(Path(intent[key]["path"]).parent == directory, "OWN_WRITE_BACKUP_SCOPE", key)
    original, desired = audit.bytes(intent["original_state_ref"]), audit.bytes(intent["desired_state_ref"])
    original_doc = full_state_cas(original, plan["expected_full_state_sha256"], plan["old_row"])
    need(audit.bytes(plan["latest_state_ref"]) == original, "OWN_WRITE_ORIGINAL_PLAN", intent)
    row = intent["resolved_row"]
    need(object_sha(row) == intent["resolved_row_sha256"] and intent["actual_apply_time"] == row["accepted_at"]
         and audit.bytes(intent["resolved_row_raw_ref"]) == encoded(row), "OWN_WRITE_ROW_HASH", intent)
    verify_resolved(plan["stable_row"], row, plan_ref, intent["lower_time_bound"])
    expected = deepcopy(original_doc)
    expected["steps"] = [row if item["id"] == "W04-99" else item for item in expected["steps"]]
    need(desired == encoded(expected), "OWN_WRITE_EXACT_STATE", "only exact resolved row may change; all top-level fields and other owners preserved")
    need(path_in(audit.repo, STATE).read_bytes() == desired, "OWN_WRITE_CURRENT_STATE", STATE)
    prior = audit.observed.get(STATE)
    need(prior in (None, sha(original), sha(desired)), "OWN_WRITE_PRIOR_STATE", prior)
    # The sole permitted old->new observation update is authenticated above.
    audit.observed[STATE] = sha(desired)
    return {"before":sha(original), "after":sha(desired), "plan":plan, "intent":intent, "row":row}


def authenticate_committed_state(audit, plan_ref, commit_ref):
    commit = audit.doc(commit_ref)
    need(commit.get("schema") == "researchos.w04.explicit-transition-commit.v1"
         and commit.get("status") == "REGISTERED_PENDING_INDEPENDENT_FINAL_ROW_AUDIT"
         and commit.get("plan_ref") == plan_ref, "OWN_WRITE_COMMIT", commit)
    need(Path(commit["intent_ref"]["path"]).parent == Path(commit_ref["path"]).parent, "OWN_WRITE_COMMIT_SCOPE", commit)
    bound = authenticate_intent_state(audit, plan_ref, commit["intent_ref"])
    verify_commit_row(bound["plan"], plan_ref, commit, bound["intent"], bound["row"])
    need(commit["before_state_sha256"] == bound["before"] and commit["after_state_sha256"] == bound["after"], "COMMIT_STATE_HASH", commit)
    for key in ("transition_review_ref", "transition_message_ref", "case_message_ref"):
        need(commit[key] == bound["intent"][key], "OWN_WRITE_AUTHORIZATION_BINDING", key)
    need(commit["case_message_ref"] == bound["plan"]["case_actual_message_ref"], "OWN_WRITE_CASE_MESSAGE", commit)
    return bound


def apply(repo, out, plan_ref, review_ref, message_ref):
    audit = Audit(repo)
    plan = audit.doc(plan_ref)
    original = path_in(repo, STATE).read_bytes()
    state = full_state_cas(original, plan["expected_full_state_sha256"], plan["old_row"])
    checked, old, new, assignment, differences, same_raw, public, validator, spec = audit_inputs(repo, plan["new_roots"], out, "apply", plan["collection_completion_ref"])
    need(checked.doc(plan_ref) == plan, "PLAN_CHANGED", plan_ref)
    need(same_raw == original, "FULL_STATE_CAS", "audit changed canonical snapshot")
    verify_plan_current(checked, plan, old, new, assignment, differences)
    review, message = checked.doc(review_ref), checked.doc(message_ref)
    authorization(review, plan_ref, plan, message, review_ref, assignment["reviewer_id"])
    lower_bound = max([new["message"]["received_at"], new["issuance"]["observed_at"], message["received_at"], review["issued_at"]], key=at)
    resolved = resolve_row(plan["stable_row"], plan_ref, lower_bound)
    verify_resolved(plan["stable_row"], resolved, plan_ref, lower_bound)
    proposed = deepcopy(state)
    proposed["steps"] = [resolved if row["id"] == "W04-99" else row for row in proposed["steps"]]
    desired = encoded(proposed)
    exclusive(out / "apply_state.original.json", original)
    exclusive(out / "apply_state.desired.json", desired)
    exclusive(out / "resolved_row.raw.json", encoded(resolved))
    journal = {"schema": "researchos.w04.transition-pending-intent.v1", "status": "PENDING_NOT_ACCEPTED", "actor": ROOT_ACTOR,
         "project_id": PROJECT, "target": STATE, "created_at": now(), "plan_ref": plan_ref, "transition_review_ref": review_ref,
         "transition_message_ref": message_ref, "case_message_ref": plan["case_actual_message_ref"],
         "original_state_ref": reference(repo, out / "apply_state.original.json"), "desired_state_ref": reference(repo, out / "apply_state.desired.json"),
         "resolved_row": resolved, "resolved_row_sha256": object_sha(resolved), "resolved_row_raw_ref": reference(repo, out / "resolved_row.raw.json"),
         "actual_apply_time": resolved["accepted_at"], "lower_time_bound": lower_bound, "resolver": RESOLVER}
    save(out / "pending_intent.json", journal)
    checked.finish()
    full_state_cas((repo / STATE).read_bytes(), plan["expected_full_state_sha256"], plan["old_row"])
    atomic_state(repo, plan["expected_full_state_sha256"], desired, out)
    actual = strict((repo / STATE).read_bytes())
    row = next(row for row in actual["steps"] if row["id"] == "W04-99")
    need(row == resolved and object_sha(row) == journal["resolved_row_sha256"], "RESOLVED_ROW_READBACK", row)
    need([row for row in actual["steps"] if row["id"] != "W04-99"] == [row for row in state["steps"] if row["id"] != "W04-99"], "FOREIGN_ROW_CHANGED", "all other owners")
    unchanged_check(checked, validator, spec, plan["new_roots"], "registered", out, "registered-integrity")
    derived = public.derive_formal_cases(repo, repo / STATE, spec / "contracts/execution.plan.json")
    save(out / "actual-formal-index.json", derived)
    owned = next(item for item in derived["owners"] if item["task_id"] == "W04")
    need(owned["integrity"] == "VALID_ACCEPTED" and set(owned["accepted_case_ids"]) == set(CASES), "REGISTERED_W04_INVALID", owned)
    recheck = public.recheck_inputs(derived["dependency_snapshot"])
    save(out / "registered-input-recheck.json", recheck)
    need(recheck["status"] == "PASS", "NEEDS_REVALIDATION", recheck)
    authenticate_intent_state(checked, plan_ref, reference(repo, out / "pending_intent.json"))
    checked.finish()
    need((repo / STATE).read_bytes() == desired, "POSTCOMMIT_FULL_STATE_CAS", STATE)
    receipt = {"schema": "researchos.w04.explicit-transition-commit.v1", "status": "REGISTERED_PENDING_INDEPENDENT_FINAL_ROW_AUDIT",
          "at": now(), "plan_ref": plan_ref, "transition_review_ref": review_ref, "transition_message_ref": message_ref,
          "case_message_ref": plan["case_actual_message_ref"], "intent_ref": reference(repo, out / "pending_intent.json"),
          "before_state_sha256": sha(original), "after_state_sha256": sha(desired), "resolved_row": row,
          "resolved_row_sha256": object_sha(row), "actual_apply_time": resolved["accepted_at"], "resolver": RESOLVER,
          "registered_result_ref": reference(repo, out / "registered-integrity.json"), "formal_index_ref": reference(repo, out / "actual-formal-index.json"),
          "other_owner_current_states": [item for item in derived["owners"] if item["task_id"] != "W04"],
          "independent_final_time_check": "PENDING_REAL_REGISTERED_STAGE_REVIEW", "counter_reset": False}
    save(out / "transition_commit_receipt.json", receipt)
    marker = {"schema": "researchos.w04.transition-application-completed.v1", "status": "APPLICATION_COMMITTED_INDEPENDENT_CLOSURE_PENDING",
              "commit_ref": reference(repo, out / "transition_commit_receipt.json"), "at": now(), "final_row_sha256": object_sha(row)}
    save(out / "completion-marker-bytes.json", marker)
    checked.finish()
    need(public.recheck_inputs(derived["dependency_snapshot"])["status"] == "PASS" and (repo / STATE).read_bytes() == desired,
         "COMPLETION_CAS", "all current inputs and exact full state")
    os.link(out / "completion-marker-bytes.json", out / "completed.json")
    return marker


def verify_registered(repo, out, commit_ref):
    audit = Audit(repo)
    commit = audit.doc(commit_ref)
    marker, _ = audit.current((Path(commit_ref["path"]).parent / "completed.json").as_posix())
    need(marker.get("schema") == "researchos.w04.transition-application-completed.v1"
         and marker.get("status") == "APPLICATION_COMMITTED_INDEPENDENT_CLOSURE_PENDING"
         and marker.get("commit_ref") == commit_ref
         and marker.get("final_row_sha256") == commit["resolved_row_sha256"], "REGISTRATION_NOT_COMPLETED", marker)
    intent = audit.doc(commit["intent_ref"])
    plan_ref = commit["plan_ref"]
    plan = audit.doc(plan_ref)
    row = next(r for r in strict((repo / STATE).read_bytes())["steps"] if r["id"] == "W04-99")
    verify_commit_row(plan, plan_ref, commit, intent, row)
    registration, _, assignment = scope(audit)
    original = audit.doc(intent["original_state_ref"])
    desired = audit.doc(intent["desired_state_ref"])
    need(sha(audit.bytes(intent["original_state_ref"])) == commit["before_state_sha256"]
         and sha(audit.bytes(intent["desired_state_ref"])) == commit["after_state_sha256"], "COMMIT_STATE_HASH", commit)
    authenticate_committed_state(audit, plan_ref, commit_ref)
    old = historical(audit, audit.doc(assignment["old_owner_ref"]))
    new = delivery_chain(audit, plan["new_roots"], assignment=assignment)
    differences = require_changed(old["chain"]["context"], new["context"], old["chain"]["review"], new["review"])
    verify_plan_current(audit, plan, old, new, assignment, differences, committed=(plan_ref, commit_ref))
    review_ref, message_ref = commit["transition_review_ref"], commit["transition_message_ref"]
    review, message = audit.doc(review_ref), audit.doc(message_ref)
    authorization(review, plan_ref, plan, message, review_ref, assignment["reviewer_id"])
    actual_message(new["message"], assignment["reviewer_id"], [plan["new_roots"]["review"]["sha256"]])
    lower = max([new["message"]["received_at"], new["issuance"]["observed_at"], message["received_at"], review["issued_at"]], key=at)
    need(lower == intent["lower_time_bound"], "COMMIT_DELIVERY_TIME_BOUND", intent)
    public, validator, spec = tools_and_spec(audit)
    roots, _ = root_inventory(audit, row)
    need(roots == plan["new_roots"], "COMMIT_ACTIVE_ROOTS", roots)
    unchanged_check(audit, validator, spec, roots, "registered", out, "independent-registered-integrity")
    derived = public.derive_formal_cases(repo, repo / STATE, spec / "contracts/execution.plan.json")
    save(out / "independent-actual-formal-index.json", derived)
    w04 = next(r for r in derived["owners"] if r["task_id"] == "W04")
    need(w04["integrity"] == "VALID_ACCEPTED" and set(w04["accepted_case_ids"]) == set(CASES), "INDEPENDENT_REGISTERED_RESULT", w04)
    need(public.recheck_inputs(derived["dependency_snapshot"])["status"] == "PASS", "NEEDS_REVALIDATION", "independent registered snapshot")
    audit.finish()
    result = {"schema": "researchos.w04.transition-final-row-check.v1", "status": "CHECKS_PASS_PENDING_ACTUAL_INDEPENDENT_DECISION",
              "commit_ref": commit_ref, "plan_ref": plan_ref, "actual_row_sha256": object_sha(row), "actual_apply_time": row["accepted_at"],
              "executed_by": "Recorded by actual caller outside this helper; helper does not sign independent acceptance",
              "formal_acceptance_created_by_helper": False}
    save(out / "final-row-check.json", result)
    return result


@contextmanager
def writer_lock(repo):
    need(os.name == "nt", "PLATFORM", "Windows Root serial writer only")
    import msvcrt
    path = path_in(repo, SCOPE_DIR + "transition-writer.lock")
    try:
        exclusive(path, b"0")
    except FileExistsError:
        pass
    with path.open("r+b") as stream:
        need(stream.read(1) == b"0", "LOCK_FORMAT", path)
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def cli_ref(repo, value):
    need(value is not None, "MISSING_ARGUMENT", "Required real evidence reference")
    # CLI references are explicit JSON {path,sha256}, not mutable path-only picks.
    ref = strict(value)
    Audit(repo).bytes(ref)
    return ref


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--actor", required=True)
    p.add_argument("--phase", choices=("prepare", "dry-run", "apply", "recover", "verify-registered"), required=True)
    for key in ("context", "review", "issuance", "collection", "source-review", "source-message", "plan", "transition-review", "transition-message", "intent", "commit"):
        p.add_argument("--" + key + "-ref")
    return p


def main():
    args = parser().parse_args()
    repo = args.repo.resolve(strict=True)
    identity = strict(path_in(repo, "execution/project_identity.json").read_bytes())
    need(identity["project_id"] == PROJECT and Path(identity["repository_root"]).resolve() == repo,
         "CANONICAL_PROJECT_IDENTITY", repo)
    lock = strict(path_in(repo, "execution/toolchains/locked.json").read_bytes())["tools"]["python"]
    need(Path(sys.executable).resolve() == Path(lock["path"]).resolve() and sha(Path(sys.executable).read_bytes()) == lock["sha256"], "LOCKED_PYTHON", sys.executable)
    need(args.actor == ROOT_ACTOR if args.phase != "verify-registered" else args.actor in {ROOT_ACTOR, "codex:/root/w05_merge_review"}, "ACTUAL_ACTOR_REQUIRED", args.actor)
    out = args.out.resolve()
    need(out.is_relative_to(repo / BASE / "integration_codex"), "OUTPUT_SCOPE", out)
    path_in(repo, out.relative_to(repo))
    out.mkdir(parents=True, exist_ok=True)
    invocation = out / ("invocation-" + uuid.uuid4().hex + ".json")
    save(invocation, {"actual_argv": sys.argv, "cwd": str(Path.cwd()), "actor": args.actor, "phase": args.phase,
                      "started_at": now(), "script_sha256": sha(Path(__file__).read_bytes()), "scope": "EXPLICIT_TRANSITION_NOT_PRODUCT_EXECUTION"})
    try:
        with writer_lock(repo):
            if args.phase in {"prepare", "dry-run"}:
                roots = {k: cli_ref(repo, getattr(args, k + "_ref")) for k in SCHEMAS}
                result = prepare(repo, out, roots, cli_ref(repo, args.source_review_ref), cli_ref(repo, args.source_message_ref), cli_ref(repo, args.collection_ref))
            elif args.phase == "apply":
                result = apply(repo, out, cli_ref(repo, args.plan_ref), cli_ref(repo, args.transition_review_ref), cli_ref(repo, args.transition_message_ref))
            elif args.phase == "recover":
                intent_ref = cli_ref(repo, args.intent_ref)
                need(path_in(repo, intent_ref["path"]).parent == out, "RECOVERY_OUTPUT_SCOPE", intent_ref)
                result = recover(repo, Audit(repo).doc(intent_ref), out)
            else:
                result = verify_registered(repo, out, cli_ref(repo, args.commit_ref))
    except BaseException as exc:
        # No silent rollback after a postcommit failure. The immutable pending
        # intent supports an explicit Root recovery with own-write hash CAS.
        failure = {"schema": "researchos.w04.transition-failure-origin.v1", "origin_key": "W04-transition|" + uuid.uuid4().hex,
                   "at": now(), "phase": args.phase, "code": getattr(exc, "code", type(exc).__name__), "error": str(exc),
                   "traceback": traceback.format_exc(), "current_state_sha256": sha((repo / STATE).read_bytes()),
                   "pending_intent_exists": (out / "pending_intent.json").exists(), "completed_marker_exists": (out / "completed.json").exists(),
                   "current_acceptance_claimed": False, "counter_reset": False,
                   "next_action": "Keep every receipt. Root may explicitly recover an incomplete intent; foreign state hash is never overwritten. A new attempt needs a new plan and independent authorization."}
        save(out / ("failure-origin-" + uuid.uuid4().hex + ".json"), failure)
        print(json.dumps(failure, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
