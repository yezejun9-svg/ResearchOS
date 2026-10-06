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
from unittest.mock import patch
from types import SimpleNamespace

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

    def transaction(self, label):
        """Execute real mutation guards; external provenance providers are inert.

        No frozen reader/profile is mocked. The separate reader test executes
        both real readers. This fixture isolates the registration transaction,
        explicitly not the full real product provenance graph.
        """
        f = Fixture(self.f.root / label)
        for name in ("register.py", "test_register.py"):
            r.exclusive(f.root / "synthetic-helper" / name, Path(__file__).with_name(name).read_bytes())
        q = r.load_module(f.root / "synthetic-helper/register.py", "synthetic_transaction_" + uuid.uuid4().hex)
        old = {"owner":f.row, "roots":f.roots, "nonroots":f.nonroots,
               "chain":{"context":f.context, "review":f.review}}
        assignment = {"executor_id":"synthetic:executor-new", "reviewer_id":"synthetic:reviewer-new"}
        archive = {"schema":"researchos.w04.historical-acceptance-archive.v1", "scope":"HISTORICAL_ONLY_NOT_CURRENT_ROOT",
                   "owner":f.row, "roots":f.roots, "nonroots":f.nonroots, "original_evidence":f.row["evidence"]}
        archive_ref = f.put(r.BASE + "integration_codex/synthetic-archive.json", archive)
        new = {"context":deepcopy(f.context), "review":deepcopy(f.review), "index":f.index,
               "issuance":deepcopy(f.issuance), "message":deepcopy(f.message)}
        new["context"]["version_vector"]["source_files"][0]["sha256"] = "c"*64
        new["context"]["registry_snapshot_ref"] = f.put(r.BASE + "integration_codex/registry-snapshot.json", {"scope":"SYNTHETIC_NOT_PRODUCT"})
        state = {"scope":"SYNTHETIC_NOT_PRODUCT", "retained_top_field":{"revision":82}, "steps":[f.row, {"id":"W07-99", "status":"SYNTHETIC_KEEP", "evidence":["unchanged"]}]}
        state_ref = f.put(r.STATE, state)
        registry_ref = f.put(r.REGISTRY, {"scope":"SYNTHETIC_NOT_PRODUCT", "revision":999})
        lower = "2026-01-03T00:00:00+00:00"
        new["issuance"]["observed_at"] = lower
        new["message"] = {"sender":assignment["reviewer_id"], "recorded_by":r.ROOT_ACTOR, "recipient":r.ROOT_ACTOR,
            "event_type":"MESSAGE", "received_at":lower, "content":"SYNTHETIC_NOT_PRODUCT " + f.roots["review"]["sha256"]}
        def locate(message):
            message["event_locator"] = {"source":"SYNTHETIC_NOT_PRODUCT", "task_name":"/root", "sender_task":assignment["reviewer_id"],
                "message_type":"MESSAGE", "message_content_sha256":r.sha(message["content"].encode())}
            return message
        new["message"] = locate(new["message"])
        new["issuance"]["message_ref"] = f.put(r.BASE + "integration_codex/new-case-message.json", new["message"])
        latest = f.put(r.BASE + "integration_codex/plan/latest_state.original.json", state)
        stable = r.template_for(old, f.roots, archive_ref, assignment, "2026-01-01T00:00:00+00:00")
        plan = {"schema":"researchos.w04.explicit-applicability-transition-plan.v1", "resolver":r.RESOLVER, "invariants":r.INVARIANTS,
            "scope_ref":{"sha256":r.SCOPE_SHA}, "amendment_ref":r.AMENDMENT, "historical_purpose_scope_ref":r.HISTORY_SCOPE,
            "old_row":f.row, "old_row_sha256":r.object_sha(f.row), "old_roots":f.roots, "old_nonroots":f.nonroots,
            "archive_ref":archive_ref, "stable_row":stable, "stable_row_sha256":r.object_sha(stable), "new_roots":f.roots,
            "helper_ref":r.reference(f.root, f.root/'synthetic-helper/register.py'), "tests_ref":r.reference(f.root, f.root/'synthetic-helper/test_register.py'),
            "source_review_ref":{}, "source_review_message_ref":{}, "collection_completion_ref":{}, "collection_review_ref":{},
            "external_compiled_input_hashes":{}, "applicability_differences":r.require_changed(f.context,new["context"],f.review,new["review"]),
            "case_actual_message_ref":new["issuance"]["message_ref"], "registry_snapshot_ref":new["context"]["registry_snapshot_ref"],
            "registry_sha256":registry_ref["sha256"], "input_hashes":{r.STATE:state_ref["sha256"], r.REGISTRY:registry_ref["sha256"]},
            "expected_full_state_sha256":state_ref["sha256"], "latest_state_ref":latest}
        plan_ref = f.put(r.BASE + "integration_codex/plan/transition_plan.json", plan)
        review = {"schema":"researchos.w04.transition-independent-review.v1", "decision":"APPROVED_CURRENT_APPLICABILITY_TRANSITION",
            "reviewer_id":assignment["reviewer_id"], "plan_ref":plan_ref, "stable_row_sha256":plan["stable_row_sha256"],
            "helper_ref":plan["helper_ref"], "tests_ref":plan["tests_ref"], "resolver":r.RESOLVER, "invariants":r.INVARIANTS,
            "old_acceptance_disputed":False, "deferred_final_time_verification":True, "missing":[], "failed":[], "issued_at":lower}
        review_ref = f.put(r.BASE + "independent_revalidation_codex/transaction-review.json", review)
        message = locate({"sender":assignment["reviewer_id"], "recorded_by":r.ROOT_ACTOR, "recipient":r.ROOT_ACTOR, "event_type":"MESSAGE",
            "received_at":lower, "review_ref":review_ref, "plan_ref":plan_ref, "content":"SYNTHETIC_NOT_PRODUCT " + plan_ref["sha256"] + " " + review_ref["sha256"]})
        message_ref = f.put(r.BASE + "integration_codex/transition-message.json", message)
        assignment["old_owner_ref"] = f.put(r.BASE + "integration_codex/old-owner.json", {"synthetic":True})
        public = SimpleNamespace(derive_formal_cases=lambda *args:{"owners":[{"task_id":"W04","integrity":"VALID_ACCEPTED","accepted_case_ids":list(r.CASES)},
             {"task_id":"W07","integrity":"NEEDS_REVALIDATION","reason":"SYNTHETIC_STALE_PRESERVED"}], "dependency_snapshot":{}},
             recheck_inputs=lambda *args:{"status":"PASS"})
        def inputs(repo, *args):
            audit = q.Audit(repo)
            audit.bytes(state_ref)
            return audit, old, new, assignment, plan["applicability_differences"], (repo/r.STATE).read_bytes(), public, None, Path('synthetic-spec')
        mocks = patch.multiple(q, audit_inputs=inputs, scope=lambda *args:({}, {}, assignment), historical=lambda *args:old,
            delivery_chain=lambda *args, **kwargs:new, source_approval=lambda *args:None,
            collection_completion=lambda *args:{"sidecar_ref":{}}, tools_and_spec=lambda *args:(public,None,Path('synthetic-spec')),
            unchanged_check=lambda audit,validator,spec,roots,phase,out,stem:r.save(out/(stem+'.json'), {"scope":"SYNTHETIC_TRANSACTION_RESULT_NOT_REAL_REVIEW","phase":phase}))
        out = f.root / r.BASE / 'integration_codex/apply'
        out.mkdir(parents=True)
        return SimpleNamespace(f=f,q=q,old=old,new=new,assignment=assignment,plan=plan,plan_ref=plan_ref,review_ref=review_ref,message_ref=message_ref,mocks=mocks,out=out)

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
        context_ref = self.f.put(r.SCOPE_DIR + "synthetic-current.json", {"execution_index": index_ref})
        sidecar = {"schema": "researchos.w04.collection-independent-attestation.v1", "scope": "INDEPENDENT_COLLECTION_ORDER_AND_COMPLETION",
                   "task_id": "W04", "step_id": "W04-99", "reviewer_id": self.f.ve, "executor_id": self.f.ex,
                   "issued_at": "2026-01-01T00:01:45+00:00", "current_context_ref": context_ref,
                   "execution_index_ref": index_ref, "collection_completion_ref": completion_ref, "run_id": self.f.index["run_id"],
                   "capture_refs": captures, "collector_source_refs": sources, "outer_invocation_ref": outer_ref,
                   "collection_source_order_review": r.COLLECTION_ORDER}
        sidecar_ref = self.f.put(r.BASE + "independent_revalidation_codex/synthetic-sidecar.json", sidecar)
        review = deepcopy(self.f.review)
        review.update(issued_at="2026-01-01T00:02:00+00:00", current_context_ref=context_ref, evidence_index_ref=index_ref)
        for verdict in review["owned_case_verdicts"]:
            verdict["semantic_review"]["raw_evidence_refs"] = [{**sidecar_ref, "locator": {"json_pointer": "/collection_source_order_review"}}]
        new = {"context": {"execution_index": index_ref}, "index": self.f.index, "review": review}
        r.collection_completion(self.f.audit(), completion_ref, new, assignment)
        for field, value, code in (("reviewer_id", "synthetic:other", "COLLECTION_SIDECAR_ACTOR"),
                                  ("issued_at", "2025-12-31T00:00:00+00:00", "COLLECTION_SIDECAR_TIME"),
                                  ("run_id", "ANOTHER_RUN", "COLLECTION_SIDECAR_TUPLE"),
                                  ("collection_source_order_review", "claimed", "COLLECTION_SIDECAR_ORDER"),
                                  ("collection_completion_ref", {**completion_ref, "sha256": "f"*64}, "COLLECTION_SIDECAR_TUPLE")):
            altered = deepcopy(sidecar)
            altered[field] = value
            bad_ref = self.f.put(r.BASE + "independent_revalidation_codex/bad-" + field + ".json", altered)
            bad_new = deepcopy(new)
            for verdict in bad_new["review"]["owned_case_verdicts"]:
                verdict["semantic_review"]["raw_evidence_refs"] = [{**bad_ref, "locator": {"json_pointer": "/collection_source_order_review"}}]
            self.refuse(code, lambda: r.collection_completion(self.f.audit(), completion_ref, bad_new, assignment))
        bad_new = deepcopy(new)
        bad_new["review"]["owned_case_verdicts"][0]["semantic_review"]["raw_evidence_refs"] = []
        self.refuse("COLLECTION_SIDECAR_BINDING", lambda: r.collection_completion(self.f.audit(), completion_ref, bad_new, assignment))
        bad_new = deepcopy(new)
        bad_new["review"]["collection_completion_ref"] = completion_ref
        self.refuse("V1_UNKNOWN_FIELD", lambda: r.collection_completion(self.f.audit(), completion_ref, bad_new, assignment))
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


    def test_16_actual_frozen_readers_legal_sidecar_and_unknown_fields(self):
        base = SOURCE / r.BASE / 'formal_validator_codex'
        before = {str(p):r.sha(p.read_bytes()) for p in (base/'validate.py', SOURCE/'execution/v2.4/formal_case_index.py')}
        sys.path.insert(0,str(base))
        builder = r.load_module(base/'test_validate.py', 'actual_reader_fixture_' + uuid.uuid4().hex)
        builder.HERE = self.f.root/'actual-frozen-readers'
        builder.HERE.mkdir()
        f = builder.Fixture()
        f.temp._finalizer.detach()  # retain explicit SYNTHETIC input/output evidence
        sidecar_path = r.BASE + 'independent_revalidation_codex/synthetic-collection.json'
        f.docs[sidecar_path] = {'scope':'SYNTHETIC_NOT_PRODUCT', 'collection_source_order_review':r.COLLECTION_ORDER}
        review = f.docs[builder.P+'independent_review.json']
        for row in review['owned_case_verdicts']:
            row['semantic_review']['raw_evidence_refs'].append(builder.raw(sidecar_path, '/collection_source_order_review'))
        f.docs[r.STATE]['steps'][-1]['status'] = 'IN_PROGRESS'
        f.sync()
        public = r.load_module(SOURCE/'execution/v2.4/formal_case_index.py','actual_public_' + uuid.uuid4().hex)
        readers = [('validator',builder.v.check),('formal_index',public._check_w04_profile)]
        outcomes = []
        for label, check in readers:
            result = check(f.root, r.STATE, 'frozen', builder.I+'current.json', builder.P+'independent_review.json', builder.I+'issuance.json', 'reviewed')
            self.assertEqual((result['integrity'],result['eligible_owned_case_count'],result['formal_accepted_count']), ('PASS',3,0))
            outcomes.append({'reader':label,'valid_legal_sidecar':'PASS','formal_acceptance_count':0})
        for field in ('collection_completion_ref','collection_source_order_review'):
            review[field] = 'SYNTHETIC_UNSUPPORTED_TOP_LEVEL'
            f.sync()
            for label, check in readers:
                with self.assertRaises(Exception) as caught:
                    check(f.root,r.STATE,'frozen',builder.I+'current.json',builder.P+'independent_review.json',builder.I+'issuance.json','reviewed')
                self.assertEqual(caught.exception.code,'UNKNOWN_FIELD')
                outcomes.append({'reader':label,'field':field,'actual_error':str(caught.exception)})
            del review[field]
            f.sync()
        self.assertEqual(before,{p:r.sha(Path(p).read_bytes()) for p in before})
        r.save(self.f.root/'actual-reader-results.json',{'scope':'SYNTHETIC_NOT_PRODUCT','source_hashes':before,'outcomes':outcomes})

    def test_17_apply_registered_unique_state_own_write(self):
        t = self.transaction('positive')
        with t.mocks:
            result = t.q.apply(t.f.root,t.out,t.plan_ref,t.review_ref,t.message_ref)
            self.assertEqual(result['status'],'APPLICATION_COMMITTED_INDEPENDENT_CLOSURE_PENDING')
            before = r.strict((t.out/'apply_state.original.json').read_bytes())
            after = r.strict((t.f.root/r.STATE).read_bytes())
            self.assertEqual(before['retained_top_field'],after['retained_top_field'])
            self.assertEqual(before['steps'][1],after['steps'][1])
            commit_ref = r.reference(t.f.root,t.out/'transition_commit_receipt.json')
            checks = t.out/'independent-registered'
            checks.mkdir()
            checked = t.q.verify_registered(t.f.root,checks,commit_ref)
            self.assertEqual(checked['status'],'CHECKS_PASS_PENDING_ACTUAL_INDEPENDENT_DECISION')
            self.assertEqual(checked['actual_row_sha256'],r.object_sha(after['steps'][0]))
            derived = r.strict((checks/'independent-actual-formal-index.json').read_bytes())
            self.assertEqual(derived['owners'][1]['integrity'],'NEEDS_REVALIDATION')
        CONTROL_RESULTS.append({'test':self._testMethodName,'scope':'SYNTHETIC_NOT_PRODUCT','status':'PASS',
            'boundary':'Real apply/verify_registered/plan hash/own-write/CAS/resolver/authorization; external provenance readers provided by explicit inert fixtures. Both frozen readers are exercised separately, not patched.', 'formal_acceptance_delta':0})

    def test_18_registered_rejects_foreign_rows_fields_and_inputs(self):
        for mutation in ('other-row','top-field','changed-source','changed-original','changed-desired','missing-intent','missing-commit','bad-time'):
            t = self.transaction(mutation)
            with t.mocks:
                t.q.apply(t.f.root,t.out,t.plan_ref,t.review_ref,t.message_ref)
                commit_ref = r.reference(t.f.root,t.out/'transition_commit_receipt.json')
                state_path = t.f.root/r.STATE
                if mutation in ('other-row','top-field'):
                    value = r.strict(state_path.read_bytes())
                    if mutation == 'other-row': value['steps'][1]['status']='FOREIGN'
                    else: value['retained_top_field']['revision']=999
                    state_path.write_bytes(r.encoded(value))
                elif mutation == 'changed-source': (t.f.root/r.REGISTRY).write_bytes(b'{"changed":true}')
                elif mutation in ('changed-original','changed-desired'):
                    name = 'apply_state.original.json' if mutation == 'changed-original' else 'apply_state.desired.json'
                    (t.out/name).write_bytes(b'{"changed":true}')
                elif mutation == 'missing-intent': (t.out/'pending_intent.json').rename(t.out/'saved-pending-intent.json')
                elif mutation == 'missing-commit': (t.out/'transition_commit_receipt.json').rename(t.out/'saved-commit.json')
                else:
                    intent = r.strict((t.out/'pending_intent.json').read_bytes())
                    intent['actual_apply_time']='9999-01-01T00:00:00+00:00'
                    (t.out/'pending_intent.json').write_bytes(r.encoded(intent))
                preserved = state_path.read_bytes()
                checks = t.out/'independent-refusal'
                checks.mkdir()
                with self.assertRaises((t.q.Refusal,FileNotFoundError)) as caught:
                    t.q.verify_registered(t.f.root,checks,commit_ref)
                self.assertEqual(state_path.read_bytes(),preserved)
                r.save(checks/'actual-refusal.json',{'scope':'SYNTHETIC_NOT_PRODUCT','mutation':mutation,'actual_error':str(caught.exception),'foreign_state_preserved':True})

    def test_19_fault_after_replace_explicit_recovery(self):
        for foreign in (False, True):
            t = self.transaction('foreign' if foreign else 'own')
            original = (t.f.root/r.STATE).read_bytes()
            actual_atomic = t.q.atomic_state
            def fault(*args):
                actual_atomic(*args)
                raise RuntimeError('SYNTHETIC_FAULT_AFTER_ACTUAL_ATOMIC_REPLACE')
            with t.mocks, patch.object(t.q,'atomic_state',fault):
                with self.assertRaisesRegex(RuntimeError,'SYNTHETIC_FAULT') as caught:
                    t.q.apply(t.f.root,t.out,t.plan_ref,t.review_ref,t.message_ref)
            r.save(t.out/'synthetic-fault-origin.json',{'scope':'SYNTHETIC_NOT_PRODUCT','actual_error':str(caught.exception),
                 'stage':'after_actual_atomic_replace','counter_reset':False,'completed':(t.out/'completed.json').exists()})
            self.assertFalse((t.out/'completed.json').exists())
            journal = r.strict((t.out/'pending_intent.json').read_bytes())
            if foreign:
                state = r.strict((t.f.root/r.STATE).read_bytes())
                state['steps'][1]['status']='FOREIGN_CONCURRENT_UPDATE'
                (t.f.root/r.STATE).write_bytes(r.encoded(state))
            preserved = (t.f.root/r.STATE).read_bytes()
            recovered = t.q.recover(t.f.root,journal,t.out)
            self.assertEqual(recovered['status'],'PARTIAL_REGISTRATION_FOREIGN_STATE_NOT_TOUCHED' if foreign else 'EXPLICIT_AUDITED_RECOVERY_TO_ORIGINAL')
            self.assertEqual((t.f.root/r.STATE).read_bytes(),preserved if foreign else original)

    def test_20_own_write_cannot_authorize_altered_other_fields(self):
        t = self.transaction('tampered-authenticated-desired')
        with t.mocks:
            t.q.apply(t.f.root,t.out,t.plan_ref,t.review_ref,t.message_ref)
        intent = r.strict((t.out/'pending_intent.json').read_bytes())
        desired = r.strict((t.out/'apply_state.desired.json').read_bytes())
        desired['retained_top_field']['revision']=9000
        raw = r.encoded(desired)
        (t.out/'tampered-desired.json').write_bytes(raw)
        (t.f.root/r.STATE).write_bytes(raw)
        intent['desired_state_ref']=r.reference(t.f.root,t.out/'tampered-desired.json')
        bad_intent = t.f.put((t.out/'tampered-intent.json').relative_to(t.f.root).as_posix(),intent)
        with self.assertRaisesRegex(t.q.Refusal,'OWN_WRITE_EXACT_STATE'):
            t.q.authenticate_intent_state(t.q.Audit(t.f.root),t.plan_ref,bad_intent)
        self.assertEqual((t.f.root/r.STATE).read_bytes(),raw)


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
    return 0 if result.wasSuccessful() and result.testsRun == 20 and not result.skipped else 1


if __name__ == "__main__":
    sys.exit(main())
