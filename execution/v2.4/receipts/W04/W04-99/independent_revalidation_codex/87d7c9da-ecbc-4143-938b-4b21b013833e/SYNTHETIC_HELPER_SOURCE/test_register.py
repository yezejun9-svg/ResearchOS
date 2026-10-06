"""SYNTHETIC_NOT_PRODUCT: focused transition refusals; never real state/apply."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
import uuid

import register as r

OUT = None
SOURCE = None
CONTROL_RESULTS = []


class Fixture:
    def __init__(self, root):
        self.root = root
        self.root.mkdir(parents=True)
        self.context_path = r.BASE + "integration_codex/synthetic-context.json"
        self.review_path = r.BASE + "synthetic-review.json"
        self.issuance_path = r.BASE + "integration_codex/synthetic-issuance.json"
        self.ex = "synthetic:executor-old"
        self.ve = "synthetic:reviewer-old"
        self.index = {"executor_id": self.ex, "cases": {}, "run_id": "SYNTHETIC_NOT_PRODUCT"}
        for cid in r.CASES:
            self.index["cases"][cid] = {"run_receipt": self.put(r.BASE + "executor_codex/synthetic/" + cid + ".json",
                {"executor_id": self.ex, "verifier_id": self.ve, "environment_mode": "FIXTURE",
                 "started_at": "2026-01-01T00:00:00+00:00", "ended_at": "2026-01-01T00:01:00+00:00"})}
        index_ref = self.put(r.BASE + "executor_codex/synthetic/execution_index.json", self.index)
        self.context = {"schema": r.SCHEMAS["context"], "execution_index": index_ref,
                        "version_vector": {group: [] for group in r.GROUPS}}
        self.context["version_vector"]["source_files"] = [{"path": "internal/product.go", "sha256": "a" * 64}]
        context_ref = self.put(self.context_path, self.context)
        self.review = {"schema": r.SCHEMAS["review"], "scope": "EXTERNAL_FIXTURE_VERIFICATION", "task_id": "W04", "step_id": "W04-99",
            "executor_id": self.ex, "verifier_id": self.ve, "issued_at": "2026-01-01T00:02:00+00:00",
            "evidence_index_ref": index_ref, "current_context_ref": context_ref,
            "acceptance_baseline_ref": {"path": "spec/acceptance.json", "sha256": "b" * 64},
            "construction_decision": "ACCEPTED", "open_blockers": [],
            "owned_case_verdicts": [{"case_id": cid, "final_owner_task": "W04", "mode": "FIXTURE", "status": "PASS", "assertion_ids": ids,
                "semantic_review": {"status": "CONFIRMED", "statement": "SYNTHETIC_NOT_PRODUCT inert data", "raw_evidence_refs": [{"synthetic": True}]}} for cid, ids in r.CASES.items()],
            "parent_gate_verdicts": [{"check_id": gid, "mode": "FIXTURE", "status": "PASS"} for gid in r.GATES]}
        review_ref = self.put(self.review_path, self.review)
        self.message = {"sender": self.ve, "message_id": "SYNTHETIC_ONLY_NO_REAL_DELIVERY", "review_sha256": review_ref["sha256"],
                        "content": "SYNTHETIC_NOT_PRODUCT " + review_ref["sha256"]}
        message_ref = self.put(r.BASE + "integration_codex/synthetic-message.json", self.message)
        self.issuance = {"schema": r.SCHEMAS["issuance"], "scope": "ROOT_OBSERVED_INDEPENDENT_ISSUANCE",
            "observer_id": r.ROOT_ACTOR, "issuer_id": self.ve, "review_ref": review_ref, "current_context_ref": context_ref,
            "channel": "independent_agent_message", "message_id": self.message["message_id"], "message_ref": message_ref,
            "observed_at": "2026-01-01T00:03:00+00:00"}
        issuance_ref = self.put(self.issuance_path, self.issuance)
        self.roots = {"context": context_ref, "review": review_ref, "issuance": issuance_ref}
        self.nonroots = [self.state_ref(self.put(r.BASE + "synthetic-nonroot-" + str(i) + ".json", {"schema": "synthetic.nonroot", "i": i})) for i in range(4)]
        self.row = {"id": "W04-99", "status": "ACCEPTED", "executor_id": self.ex, "verifier_id": self.ve,
                    "started_at": "2026-01-01T00:00:00+00:00", "accepted_at": "2026-01-01T00:04:00+00:00",
                    "scope_note": "SYNTHETIC_NOT_PRODUCT, zero actual acceptance",
                    "evidence": self.nonroots + [self.state_ref(x) for x in self.roots.values()]}

    def put(self, path, value):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(r.encoded(value))
        return {"path": path, "sha256": r.sha(p.read_bytes())}

    def state_ref(self, ref):
        return {"path": ref["path"].removeprefix("execution/v2.4/"), "sha256": ref["sha256"]}

    def set_message(self, value):
        self.issuance["message_ref"] = self.put(self.issuance["message_ref"]["path"], value)
        self.roots["issuance"] = self.put(self.issuance_path, self.issuance)

    def audit(self):
        return r.Audit(self.root)


class TransitionControls(unittest.TestCase):
    def setUp(self):
        self.f = Fixture(OUT / (self._testMethodName + "-" + uuid.uuid4().hex))

    def refuse(self, code, call):
        with self.assertRaises(r.Refusal) as raised:
            call()
        self.assertEqual(raised.exception.code, code)
        CONTROL_RESULTS.append({"test": self._testMethodName, "expected": code, "actual": raised.exception.code,
                                "status": "PASS", "scope": "SYNTHETIC_NOT_PRODUCT", "formal_acceptance_delta": 0})
        print("SYNTHETIC_NOT_PRODUCT REFUSAL " + self._testMethodName + " " + code)

    def template(self):
        assignment = {"executor_id": "synthetic:executor-new", "reviewer_id": "synthetic:reviewer-new"}
        return r.template_for({"owner": self.f.row, "nonroots": self.f.nonroots}, self.f.roots,
            {"path": r.BASE + "integration_codex/synthetic-archive.json", "sha256": "d" * 64}, assignment,
            "2026-01-02T00:00:00+00:00")

    def plan_ref(self):
        return {"path": r.BASE + "integration_codex/revalidation-synthetic/transition_plan.json", "sha256": "e" * 64}

    def test_01_old_root_missing_drift_and_competing(self):
        r.root_inventory(self.f.audit(), self.f.row, 7)
        missing = deepcopy(self.f.row)
        missing["evidence"].pop()
        self.refuse("MISSING_OLD_ROOT", lambda: r.root_inventory(self.f.audit(), missing))
        competing = deepcopy(self.f.row)
        extra = self.f.put(r.BASE + "competing-review.json", self.f.review)
        competing["evidence"].append(self.f.state_ref(extra))
        self.refuse("CONFLICTING_REVIEW", lambda: r.root_inventory(self.f.audit(), competing))
        self.f.put(self.f.review_path, {**self.f.review, "changed": True})
        self.refuse("HASH_MISMATCH", lambda: r.root_inventory(self.f.audit(), self.f.row, 7))

    def test_02_actual_old_delivery_required(self):
        r.delivery_chain(self.f.audit(), self.f.roots, self.f.row)
        original = deepcopy(self.f.message)
        self.f.set_message({**original, "sender": "synthetic:other"})
        self.refuse("ACTUAL_MESSAGE_LINK", lambda: r.delivery_chain(self.f.audit(), self.f.roots, self.f.row))
        self.f.set_message({**original, "review_sha256": "0" * 64})
        self.refuse("ACTUAL_MESSAGE_LINK", lambda: r.delivery_chain(self.f.audit(), self.f.roots, self.f.row))
        self.f.issuance.pop("message_ref")
        self.f.roots["issuance"] = self.f.put(self.f.issuance_path, self.f.issuance)
        self.refuse("MISSING_ACTUAL_MESSAGE", lambda: r.delivery_chain(self.f.audit(), self.f.roots, self.f.row))

    def test_03_same_applicability_baseline_ids_mode_blocker(self):
        self.refuse("SAME_APPLICABILITY", lambda: r.require_changed(self.f.context, self.f.context, self.f.review, self.f.review))
        new_context = deepcopy(self.f.context)
        new_context["version_vector"]["source_files"][0]["sha256"] = "c" * 64
        self.assertTrue(r.require_changed(self.f.context, new_context, self.f.review, self.f.review))
        changed = deepcopy(self.f.review)
        changed["acceptance_baseline_ref"]["sha256"] = "0" * 64
        self.refuse("BASELINE_CHANGED", lambda: r.require_changed(self.f.context, new_context, self.f.review, changed))
        changed = deepcopy(self.f.review)
        changed["open_blockers"] = ["synthetic unresolved old acceptance dispute"]
        self.refuse("UNRESOLVED_REVIEW", lambda: r.require_changed(self.f.context, new_context, changed, self.f.review))
        for field, value in (("mode", "LIVE"), ("assertion_ids", ["A05-01"])):
            changed = deepcopy(self.f.review)
            changed["owned_case_verdicts"][0][field] = value
            self.refuse("EXPECTED_IDS_MODE_SEMANTICS", lambda: r.require_changed(self.f.context, new_context, self.f.review, changed))

    def test_04_new_actor_namespace_and_message(self):
        assignment = {"executor_id": self.f.ex, "reviewer_id": self.f.ve, "root_id": r.ROOT_ACTOR,
                      "executor_namespace": r.BASE + "executor_revalidation_codex/"}
        self.refuse("NAMESPACE_OWNERSHIP", lambda: r.delivery_chain(self.f.audit(), self.f.roots, assignment=assignment))
        for bad_actor in (self.f.ex, r.ROOT_ACTOR):
            review = deepcopy(self.f.review)
            review["verifier_id"] = bad_actor
            roots = deepcopy(self.f.roots)
            roots["review"] = self.f.put(r.BASE + "bad-new-review-" + str(len(bad_actor)) + ".json", review)
            self.refuse("INDEPENDENT_ACTORS", lambda: r.delivery_chain(self.f.audit(), roots, assignment=assignment))
        self.f.set_message({**self.f.message, "content": "synthetic missing real review hash"})
        self.refuse("ACTUAL_MESSAGE_LINK", lambda: r.delivery_chain(self.f.audit(), self.f.roots, assignment=assignment))

    def test_05_archive_complete_immutable_history(self):
        archive = {"schema": "researchos.w04.historical-acceptance-archive.v1", "scope": "HISTORICAL_ONLY_NOT_CURRENT_ROOT",
                   "owner": self.f.row, "roots": self.f.roots, "nonroots": self.f.nonroots, "original_evidence": self.f.row["evidence"]}
        r.verify_archive(archive, self.f.row, self.f.roots, self.f.nonroots)
        for mutation in ("roots", "nonroots", "actor", "time", "schema"):
            bad = deepcopy(archive)
            if mutation == "roots": bad["roots"].pop("issuance")
            elif mutation == "nonroots": bad["nonroots"].pop()
            elif mutation == "actor": bad["owner"]["executor_id"] = "synthetic:rewritten"
            elif mutation == "time": bad["owner"]["accepted_at"] = "2026-02-01T00:00:00+00:00"
            else: bad["schema"] = r.SCHEMAS["review"]
            self.refuse("ARCHIVE_SCHEMA" if mutation == "schema" else "ARCHIVE_INCOMPLETE_OR_REWRITTEN",
                        lambda: r.verify_archive(bad, self.f.row, self.f.roots, self.f.nonroots))

    def test_06_full_state_cas_including_unrelated_owner(self):
        state = {"steps": [self.f.row, {"id": "W07-99", "status": "EXECUTION_REPORTED"}]}
        original = r.encoded(state)
        r.full_state_cas(original, r.sha(original), self.f.row)
        for row_index in (0, 1):
            changed = deepcopy(state)
            changed["steps"][row_index]["status"] = "different concurrent task status"
            self.refuse("FULL_STATE_CAS", lambda: r.full_state_cas(r.encoded(changed), r.sha(original), self.f.row))
        changed = deepcopy(self.f.row)
        changed["executor_id"] = "synthetic:another"
        self.refuse("OLD_ROW_CAS", lambda: r.full_state_cas(original, r.sha(original), changed))

    def test_07_reviewed_vector_or_registry_drift(self):
        for name in ("internal/product.json", r.REGISTRY):
            ref = self.f.put(name, {"scope": "SYNTHETIC_NOT_PRODUCT", "revision": 1})
            audit = self.f.audit()
            audit.bytes(ref)
            self.f.put(name, {"scope": "SYNTHETIC_NOT_PRODUCT", "revision": 2})
            self.refuse("NEEDS_REVALIDATION", audit.finish)

    def test_08_unchanged_v1_negative_controls_and_prefix(self):
        public = SOURCE / "execution/v2.4/formal_case_index.py"
        prefix = public.read_bytes()[:51719]
        self.assertEqual(hashlib.sha256(prefix).hexdigest(), r.PREFIX_SHA)
        base = SOURCE / r.BASE / "formal_validator_codex"
        before = {name: r.sha((base / name).read_bytes()) for name in ("validate.py", "test_validate.py")}
        sys.path.insert(0, str(base))
        spec = importlib.util.spec_from_file_location("w04_original_synthetic_builder", base / "test_validate.py")
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        # Only the fixture builder's scratch directory is relocated. Shared
        # validator functions/constants/profile/PREFIX are never replaced.
        builder.HERE = self.f.root / "existing-v1-synthetic"
        builder.HERE.mkdir()
        methods = ("test_conflicting_registered_review", "test_hash_bound_supersession_without_actual_old_issuance_is_unsupported",
                   "test_unregistered_supersession_rejected")
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.TestSuite(builder.IntegrityControls(m) for m in methods))
        r.exclusive(self.f.root / "existing-v1-controls.raw.txt", stream.getvalue().encode())
        self.assertEqual(result.testsRun, 3)
        self.assertEqual((len(result.failures), len(result.errors), len(result.skipped)), (0, 0, 0), stream.getvalue())
        self.assertEqual(before, {name: r.sha((base / name).read_bytes()) for name in before})
        self.assertEqual(public.read_bytes()[:51719], prefix)
        CONTROL_RESULTS.append({"test": self._testMethodName, "scope": "SYNTHETIC_NOT_PRODUCT", "status": "PASS",
                                "existing_v1_controls": 3, "skipped": 0, "formal_acceptance_delta": 0})
        print("SYNTHETIC_NOT_PRODUCT existing v1 negative controls: 3 PASS, prefix unchanged")

    def test_09_resolver_exact_slots_fields_order_and_plan(self):
        template = self.template()
        ref = self.plan_ref()
        resolved = r.resolve_row(template, ref, "2026-01-03T00:00:00+00:00")
        r.verify_resolved(template, resolved, ref, "2026-01-03T00:00:00+00:00")
        for key in ("third", "duplicate", "missing"):
            bad = deepcopy(template)
            if key == "third": bad["third"] = {r.TAG: "unknown"}
            elif key == "duplicate": bad["evidence"].insert(0, {r.TAG: "self_plan_ref"})
            else: bad["evidence"].pop()
            self.refuse("RESOLVER_CLOSED_WORLD", lambda: r.slots(bad))
        for key in ("actor", "order", "plan"):
            bad = deepcopy(resolved)
            if key == "actor": bad["executor_id"] = "synthetic:changed"
            elif key == "order": bad["evidence"][0], bad["evidence"][1] = bad["evidence"][1], bad["evidence"][0]
            else: bad["evidence"][-1]["sha256"] = "f" * 64
            self.refuse("RESOLVED_ROW_CHANGED", lambda: r.verify_resolved(template, bad, ref, "2026-01-03T00:00:00+00:00"))

    def test_10_plan_review_hash_helper_resolver_and_real_message(self):
        template = self.template()
        plan_ref, review_ref = self.plan_ref(), {"path": r.BASE + "synthetic-transition-review.json", "sha256": "f" * 64}
        plan = {"stable_row": template, "stable_row_sha256": r.object_sha(template), "resolver": r.RESOLVER,
                "helper_ref": {"path": "synthetic/register.py", "sha256": "a" * 64}, "tests_ref": {"path": "synthetic/test_register.py", "sha256": "b" * 64}}
        reviewer = "synthetic:reviewer-new"
        review = {"schema": "researchos.w04.transition-independent-review.v1", "decision": "APPROVED_CURRENT_APPLICABILITY_TRANSITION",
            "reviewer_id": reviewer, "plan_ref": plan_ref, "stable_row_sha256": plan["stable_row_sha256"],
            "helper_ref": plan["helper_ref"], "tests_ref": plan["tests_ref"], "resolver": r.RESOLVER, "invariants": r.INVARIANTS,
            "old_acceptance_disputed": False, "deferred_final_time_verification": True, "missing": [], "failed": [],
            "issued_at": "2026-01-03T00:00:00+00:00"}
        content = "SYNTHETIC_NOT_PRODUCT " + plan_ref["sha256"] + " " + review_ref["sha256"]
        message = {"sender": reviewer, "recorded_by": r.ROOT_ACTOR, "recipient": r.ROOT_ACTOR, "event_type": "MESSAGE",
            "received_at": "2026-01-03T00:01:00+00:00", "content": content, "review_ref": review_ref, "plan_ref": plan_ref,
            "event_locator": {"source": "SYNTHETIC_NOT_PRODUCT", "task_name": "/root", "sender_task": reviewer,
                              "message_type": "MESSAGE", "message_content_sha256": r.sha(content.encode())}}
        r.authorization(review, plan_ref, plan, message, review_ref, reviewer)
        changed_ref = {**plan_ref, "sha256": "0" * 64}
        self.refuse("TRANSITION_REVIEW_BINDING", lambda: r.authorization(review, changed_ref, plan, message, review_ref, reviewer))
        for field in ("helper_ref", "tests_ref"):
            changed = deepcopy(plan)
            changed[field]["sha256"] = "0" * 64
            self.refuse("TRANSITION_REVIEW_BINDING", lambda: r.authorization(review, plan_ref, changed, message, review_ref, reviewer))
        changed = deepcopy(plan)
        changed["resolver"]["encoding"] = "synthetic changed encoding"
        self.refuse("STABLE_ROW_CHANGED", lambda: r.authorization(review, plan_ref, changed, message, review_ref, reviewer))
        changed = deepcopy(message)
        changed["content"] = "SYNTHETIC missing hashes"
        self.refuse("ACTUAL_ROOT_MESSAGE", lambda: r.authorization(review, plan_ref, plan, changed, review_ref, reviewer))

    def test_11_actual_apply_clock_not_prepare_or_caller_future(self):
        template, ref = self.template(), self.plan_ref()
        for value in ("2026-01-01T00:00:00+00:00", "9999-01-01T00:00:00+00:00"):
            bad = deepcopy(template)
            bad["accepted_at"] = value
            self.refuse("RESOLVER_CLOSED_WORLD", lambda: r.resolve_row(bad, ref, "2026-01-03T00:00:00+00:00"))
        self.refuse("APPLY_BEFORE_ACTUAL_DELIVERY", lambda: r.resolve_row(template, ref, "9999-01-01T00:00:00+00:00"))
        resolved = r.resolve_row(template, ref, "2026-01-03T00:00:00+00:00")
        resolved["accepted_at"] = "2026-01-02T00:00:00+00:00"
        self.refuse("ACTUAL_APPLY_TIME", lambda: r.verify_resolved(template, resolved, ref, "2026-01-03T00:00:00+00:00"))
        with self.assertRaises(SystemExit) as stopped:
            r.parser().parse_args(["--repo", "synthetic", "--out", "synthetic", "--actor", r.ROOT_ACTOR,
                                  "--phase", "apply", "--accepted-at", "9999-01-01T00:00:00+00:00"])
        self.assertEqual(stopped.exception.code, 2)

    def test_12_atomic_cas_foreign_recovery_and_no_partial_marker(self):
        state_path = self.f.root / r.STATE
        original = r.encoded({"scope": "SYNTHETIC_NOT_PRODUCT", "steps": [self.f.row, {"id": "W07-99", "status": "SYNTHETIC_OTHER"}]})
        template = self.template()
        plan = {"stable_row": template, "old_row": self.f.row, "expected_full_state_sha256": r.sha(original)}
        plan_ref = self.f.put(self.plan_ref()["path"], plan)
        resolved = r.resolve_row(template, plan_ref, "2026-01-03T00:00:00+00:00")
        proposed = r.strict(original)
        proposed["steps"][0] = resolved
        desired, foreign = r.encoded(proposed), r.encoded({"scope": "SYNTHETIC_NOT_PRODUCT", "foreign": True})
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_bytes(foreign)
        out = self.f.root / "synthetic-intent"
        out.mkdir()
        self.refuse("FULL_STATE_CAS", lambda: r.atomic_state(self.f.root, r.sha(original), desired, out))
        self.assertEqual(state_path.read_bytes(), foreign)
        r.exclusive(out / "original.json", original)
        r.exclusive(out / "desired.json", desired)
        journal = {"schema": "researchos.w04.transition-pending-intent.v1", "target": r.STATE, "actor": r.ROOT_ACTOR, "project_id": r.PROJECT,
                   "original_state_ref": r.reference(self.f.root, out / "original.json"), "desired_state_ref": r.reference(self.f.root, out / "desired.json"),
                   "plan_ref": plan_ref, "resolver": r.RESOLVER, "resolved_row": resolved, "resolved_row_sha256": r.object_sha(resolved),
                   "actual_apply_time": resolved["accepted_at"], "lower_time_bound": "2026-01-03T00:00:00+00:00",
                   "resolved_row_raw_ref": self.f.put("synthetic-intent/row.json", resolved)}
        result = r.recover(self.f.root, journal, out)
        self.assertEqual(result["status"], "PARTIAL_REGISTRATION_FOREIGN_STATE_NOT_TOUCHED")
        self.assertEqual(state_path.read_bytes(), foreign)
        self.assertFalse((out / "completed.json").exists())
        # Isolated synthetic own-write recovery is auditable and idempotent;
        # no real Root state or actual apply invocation is accessed here.
        state_path.write_bytes(desired)
        self.assertEqual(r.recover(self.f.root, journal, out)["status"], "EXPLICIT_AUDITED_RECOVERY_TO_ORIGINAL")
        self.assertEqual(state_path.read_bytes(), original)
        self.assertEqual(r.recover(self.f.root, journal, out)["status"], "ALREADY_ORIGINAL_NO_ACCEPTANCE")
        CONTROL_RESULTS.append({"test": self._testMethodName, "scope": "SYNTHETIC_NOT_PRODUCT", "status": "PASS", "foreign_bytes_preserved": True, "formal_acceptance_delta": 0})

    def test_13_final_row_hash_and_history_semantics(self):
        template, plan_ref = self.template(), self.plan_ref()
        row = r.resolve_row(template, plan_ref, "2026-01-03T00:00:00+00:00")
        plan = {"stable_row": template}
        intent = {"plan_ref": plan_ref, "resolver": r.RESOLVER, "resolved_row": row, "resolved_row_sha256": r.object_sha(row),
                  "lower_time_bound": "2026-01-03T00:00:00+00:00", "actual_apply_time": row["accepted_at"]}
        commit = deepcopy(intent)
        r.verify_commit_row(plan, plan_ref, commit, intent, row)
        bad = deepcopy(commit)
        bad["resolved_row_sha256"] = "0" * 64
        self.refuse("COMMIT_ROW_HASH", lambda: r.verify_commit_row(plan, plan_ref, bad, intent, row))
        changed = deepcopy(row)
        changed["evidence"][0]["sha256"] = "0" * 64
        bad = {**deepcopy(commit), "resolved_row": changed, "resolved_row_sha256": r.object_sha(changed)}
        self.refuse("RESOLVED_ROW_CHANGED", lambda: r.verify_commit_row(plan, plan_ref, bad, bad, changed))

    def test_14_bound_source_snapshots_no_receipt_substitution_or_alias(self):
        original = self.f.root / "internal/product.go"
        original.parent.mkdir(parents=True)
        original.write_bytes(b"synthetic old source")
        original_ref = r.reference(self.f.root, original)
        frozen = self.f.root / r.BASE / "synthetic-source-snapshot/old.go"
        r.exclusive(frozen, original.read_bytes())
        mapping = self.f.put(r.BASE + "synthetic-source-snapshot/source_snapshot.json",
            {"sources": [{"original_ref": original_ref, "snapshot_ref": r.reference(self.f.root, frozen)}]})
        root = self.f.put(r.BASE + "synthetic-bound-root.json", {"input_hashes": {str(self.f.root / mapping["path"]): mapping["sha256"]}})
        original.write_bytes(b"synthetic new source")
        audit = self.f.audit()
        r.discover_historical_snapshots(audit, [root])
        self.assertEqual(audit.bytes(original_ref, True), b"synthetic old source")
        self.assertEqual(audit.drifts[0]["binding_refs"][0]["mapping_ref"], mapping)
        audit.finish()
        self.refuse("HASH_MISMATCH", lambda: self.f.audit().bytes(original_ref, True))
        self.refuse("PATH_SCOPE", lambda: r.path_in(self.f.root, "internal/../product.go"))
        self.refuse("PATH_SCOPE", lambda: r.path_in(self.f.root, "internal//product.go"))
        receipt = self.f.put(r.BASE + "synthetic-old-message.json", {"content": "old"})
        copy = self.f.put(r.BASE + "synthetic-copy-message.json", {"content": "old"})
        self.f.put(receipt["path"], {"content": "changed"})
        audit.applicability[(receipt["path"], receipt["sha256"])] = copy
        self.refuse("OLD_RECEIPT_DRIFT", lambda: audit.bytes(receipt, True))
        frozen.write_bytes(b"synthetic substituted source")
        self.refuse("HASH_MISMATCH", lambda: r.discover_historical_snapshots(self.f.audit(), [root]))

    def test_15_four_compiled_captures_and_final_collector_exit(self):
        namespace = r.BASE + "executor_revalidation_codex/"
        assignment = {"executor_id": self.f.ex, "reviewer_id": self.f.ve, "executor_namespace": namespace, "assigned_at": "2026-01-01T00:00:00+00:00"}
        run_dir = namespace + "runs/SYNTHETIC_NOT_PRODUCT"
        source_names = ["collect.py", "bridge.py", "test_bridge.py", "parent_driver.py", "evidence_module.py", "expected.json", "frozen_inputs/commands-v24-r37.json", "frozen_inputs/legacy_entries.json", "test_collect.py"]
        sources = [self.f.put(namespace + name, {"scope": "SYNTHETIC_NOT_PRODUCT", "inert_source_name": name}) for name in source_names]
        files = [{"path": str(self.f.root / item["path"]), "sha256": item["sha256"]} for item in sources]
        actor_ref = self.f.put(r.SCOPE_DIR + "actor_assignment.json", assignment)
        python_ref = self.f.put("synthetic-inert-python.txt", {"scope": "SYNTHETIC_NOT_PRODUCT_INERT_NOT_EXECUTABLE"})
        python = self.f.root / python_ref["path"]
        self.f.put("execution/toolchains/locked.json", {"tools": {"python": {"path": str(python), "sha256": python_ref["sha256"]}}})
        files += [{"path": str(self.f.root / item["path"]), "sha256": item["sha256"]} for item in (actor_ref, python_ref)]
        dependency = self.f.put(run_dir + "/dependencies.json", {"exit_code": 0, "actual_argv": ["synthetic-go", "list", "-deps", "-test", "-json"]})
        captures = {}
        for name in ("before", "preproof", "prepublish", "after"):
            filename = "compiled-inputs-" + name + ".json"
            captures[filename] = self.f.put(run_dir + "/" + filename, {"schema": "researchos.w04.auxiliary-compiled-inputs.v1", "files": files, "unchanged": True, "invocation_ref": dependency})
        index_ref = self.f.put(run_dir + "/execution_index.json", self.f.index)
        handoff = self.f.put(run_dir + "/handoff.json", {"execution_index": index_ref, "status": "EXECUTED_PENDING_INDEPENDENT_REVIEW"})
        proof = self.f.put(run_dir + "/proof.json", {"run_id": self.f.index["run_id"], "status": "PASS", "started_at": "2026-01-01T00:00:00+00:00", "ended_at": "2026-01-01T00:01:00+00:00"})
        stdout = self.f.put(run_dir + "/outer.stdout.json", {"status": "EXECUTED_PENDING_INDEPENDENT_REVIEW", "execution_index": index_ref, "run": str(self.f.root / run_dir)})
        stderr = self.f.put(run_dir + "/outer.stderr.json", {"scope": "SYNTHETIC_NOT_PRODUCT"})
        outer = {"exit_code": 0, "cwd": str(self.f.root), "executable_sha256": python_ref["sha256"], "actual_argv": [str(python), str(self.f.root / namespace / "collect.py"), "--executor-id", self.f.ex, "--verifier-id", self.f.ve, "--root-id", r.ROOT_ACTOR, "--actor-assignment", str(self.f.root / actor_ref["path"])],
                 "started_at": "2026-01-01T00:00:00+00:00", "ended_at": "2026-01-01T00:01:30+00:00", "stdout": stdout, "stderr": stderr}
        outer_ref = self.f.put(run_dir + "/outer.json", outer)
        completion = {"schema": "researchos.w04.collection-completion.v1", "executor_id": self.f.ex, "capture_refs": captures,
                      "collector_source_refs": sources, "proof_ref": proof, "handoff_ref": handoff, "outer_invocation_ref": outer_ref}
        completion_ref = self.f.put(run_dir + "/completion.json", completion)
        new = {"context": {"execution_index": index_ref}, "index": self.f.index, "review": {"issued_at": "2026-01-01T00:02:00+00:00",
               "collection_completion_ref": completion_ref, "collection_source_order_review": "VERIFIED_EXCLUSIVE_RUN_BEFORE_PREPROOF_PREPUBLISH_FINALLY_AFTER_AND_FINAL_EXIT"}}
        r.collection_completion(self.f.audit(), completion_ref, new, assignment)
        bad = deepcopy(completion)
        bad["capture_refs"].pop("compiled-inputs-after.json")
        self.refuse("COMPILED_CAPTURE_COVERAGE", lambda: r.collection_completion(self.f.audit(), self.f.put(run_dir + "/missing.json", bad), new, assignment))
        bad = deepcopy(completion)
        bad["capture_refs"]["compiled-inputs-after.json"] = captures["compiled-inputs-before.json"]
        self.refuse("COLLECTION_RUN_ALIAS", lambda: r.collection_completion(self.f.audit(), self.f.put(run_dir + "/alias.json", bad), new, assignment))
        bad = deepcopy(completion)
        bad["outer_invocation_ref"] = self.f.put(run_dir + "/failed-outer.json", {**outer, "exit_code": 1})
        self.refuse("COLLECTOR_FINAL_EXIT", lambda: r.collection_completion(self.f.audit(), self.f.put(run_dir + "/late-failure.json", bad), new, assignment))
        changed_files = deepcopy(files)
        changed_files[0]["sha256"] = "f" * 64
        bad = deepcopy(completion)
        bad["capture_refs"]["compiled-inputs-after.json"] = self.f.put(run_dir + "/compiled-inputs-after.json", {"schema": "researchos.w04.auxiliary-compiled-inputs.v1", "files": changed_files, "unchanged": True})
        self.refuse("COMPILED_CAPTURE_DRIFT", lambda: r.collection_completion(self.f.audit(), self.f.put(run_dir + "/drift.json", bad), new, assignment))


def main():
    global OUT, SOURCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    SOURCE = args.repo_source.resolve(strict=True)
    OUT = args.out.resolve()
    OUT.mkdir(parents=True, exist_ok=False)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TransitionControls))
    report = {"schema": "researchos.w04.transition-synthetic-controls.v1", "scope": "SYNTHETIC_NOT_PRODUCT",
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
              "controls": CONTROL_RESULTS, "formal_acceptance_delta": 0, "canonical_state_access": False,
              "actual_apply_executed": False, "product_commands": 0,
              "tests_sha256": r.sha(Path(__file__).read_bytes()),
              "source_ref": r.reference(Path(__file__).resolve().parent, Path(__file__).resolve().parent / "register.py")}
    r.save(OUT / "report.json", report)
    return 0 if result.wasSuccessful() and result.testsRun == 15 and not result.skipped else 1


if __name__ == "__main__":
    sys.exit(main())
