"""Read-only admission of one completed W11 LIVE evaluation; never runs a provider.

Uses public, pinned evidence only. Original timestamps/modes are retained. This is
an executor report, not an independent acceptance or a new LIVE measurement.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from datetime import datetime, timezone
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASE = "execution/verifier/W11/"
FROZEN = BASE + "frozen-live-ac9d6153/"
PRODUCT = BASE + "product-live-591d16e/"
INSTALLED = BASE + "installed-ready-a9576d5a/"
MAP = BASE + "formal-object-boundary/A08-evidence-map.json"
PAST = "execution/receipts/W11/frozen-live/ac9d6153-7ac9-42ed-a97f-d5d05409752d/"
ANCHORS = {
    MAP: "f89aff985a063ea0b5b1013b8a3fe0cf03e7a1392caf11410cf30bb72d9f9671",
    FROZEN + "evidence-index.json": "2b9834d3daa52b46192f2e7df566a55155fe309469dd6e9a4196bd6a3eda714e",
    PRODUCT + "evidence-index.json": "65728d2eee13d9f16acb989e935d7a40589bb141a4298ef21e3c227ebff3abd2",
    INSTALLED + "evidence-index.json": "958ec328d7a0c9cc748516da9f1ec816fd29237e25453bbbea9078f4c0f41631",
}
SOURCE_PATHS = {
    "adapters/protectedstore/" + p for p in (
        "frozen_engine_windows.go", "frozen_summary.go", "frozen_development.go",
        "frozen_development.json", "frozen_provider_windows.go", "frozen_generator_windows.go")
} | {"evaluation/holdout/jev/" + p for p in (
    "generator.go", "truth.go", "generate_windows.go", "rubric.go")}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
        raise ValueError("unsafe evidence path")
    if not (name.startswith(BASE) or name.startswith(PAST)):
        raise ValueError("evidence path outside public allowlist")
    resolved = (root / name).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("evidence path escapes repository")
    return resolved


class Admission:
    def __init__(self, root):
        self.root = root
        self.checks = []
        self.verified = {}
        self.original = {}
        self.metrics = []

    def check(self, name, expected, actual, refs):
        passed = expected == actual
        self.checks.append(dict(assertion_id=name, expected=expected, actual=actual,
                                status="PASS" if passed else "FAIL", evidence_refs=refs))
        if not passed:
            raise ValueError("assertion failed: " + name)

    def pin(self, name, expected):
        raw = safe_path(self.root, name).read_bytes()
        self.check("HASH:" + name, expected, digest(raw), [name])
        self.verified[name] = dict(sha256=digest(raw), bytes=len(raw))
        return raw

    def read(self, name):
        if name not in self.verified:
            raise ValueError("unpinned evidence: " + name)
        raw = self.pin(name, self.verified[name]["sha256"])
        return json.loads(raw.decode("utf-8-sig"))

    def run(self):
        for name, sha in ANCHORS.items():
            self.pin(name, sha)
        mapping = self.read(MAP)
        for name in ANCHORS:
            if name.endswith("evidence-index.json"):
                parent = name.rsplit("/", 1)[0] + "/"
                for entry in self.read(name)["files"]:
                    raw = self.pin(parent + entry["path"], entry["sha256"])
                    self.check("SIZE:" + parent + entry["path"], entry["bytes"], len(raw), [name])
        for assertion in mapping["assertions"]:
            for ref in assertion["evidence"]:
                self.pin(ref["path"], ref["sha256"])
        frozen_review = self.read(FROZEN + "review.json")
        product_review = self.read(PRODUCT + "review.json")
        for ref in frozen_review["prior_independent_evidence"] + product_review["prior_references"]:
            self.pin(ref["path"], ref["sha256"])
        for ref in self.read(FROZEN + "parent-source-index.json"):
            self.pin(ref["path"], ref["sha256"])
        bindings = self.read(FROZEN + "source-bindings.json")
        self.check("FROZEN-SOURCE-INVENTORY", sorted(SOURCE_PATHS),
                   sorted(x["path"] for x in bindings["sources"]), [FROZEN + "source-bindings.json"])
        continuity = []
        for source in bindings["sources"]:
            rev, name = source["frozen_source_revision"], source["path"]
            self.check("FROZEN-REVISION:" + name, "f0f88cb6bd65120ccb354ec92fdedf45bde25dc1", rev,
                       [FROZEN + "source-bindings.json"])
            raw = subprocess.run(["git", "show", rev + ":" + name], cwd=self.root,
                                 check=True, capture_output=True).stdout
            self.check("GIT-SOURCE:" + name, source["sha256"], digest(raw), [rev + ":" + name])
            current = (self.root / name).read_bytes()
            continuity.append(dict(path=name, frozen_sha256=digest(raw), current_sha256=digest(current),
                                   current_matches_frozen=digest(raw) == digest(current)))
        aggregate = self.read(FROZEN + "aggregate.stdout.json")
        frozen = aggregate["frozen_run"]
        self.check("ORIGINAL-TERMINAL-EXACT", aggregate, self.read(PAST + "terminal-status.json"), [PAST])
        self.check("SERVICE-COMPLETED", ["COMPLETED", "FAILED", "NONE", "ADVISORY", 30],
                   [frozen["run_state"], frozen["qualification"], frozen["automatic_authority"],
                    aggregate["maximum_mode"], frozen["request_budget"]], [FROZEN + "aggregate.stdout.json"])
        self.check("PROJECT-BINDING", "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", frozen["project_id"], [FROZEN])
        development = self.read(BASE + "development-v2-live-89172731/verified-development-aggregate.json")
        self.check("DEVELOPMENT-EMBEDDED-HASH", frozen["development_aggregate_hash"],
                   "sha256:" + bindings["development_aggregate_sha256"], [FROZEN + "source-bindings.json"])
        self.check("INITIAL-LIVE-SAMPLES", [60, 30], [development["overall"]["case_count"], aggregate["total"]], [FROZEN, BASE + "development-v2-live-89172731/"])
        self.check("LANGUAGE-KEYS", ["zh", "zh-en"], [k["scope"]["language"] for k in frozen["keys"]], [FROZEN])
        for key in frozen["keys"]:
            lang = key["scope"]["language"]
            self.check(lang + ":REQUEST-ACCOUNTING", [15, 15, 15, 0, 15, 0],
                       [key[x] for x in ("planned", "started_requests", "recorded_invocations", "unknown_requests", "http_200", "errors")], [FROZEN])
            dev = next(k for k in development["keys"] if k["qualification_key"] == key["scope"])["metrics"]
            for field, value in key["development"].items():
                self.check(lang + ":DEVELOPMENT:" + field, dev[field], value, [FROZEN, BASE + "development-v2-live-89172731/"])
            self.check(lang + ":SAMPLE-GATE-INSUFFICIENT", False,
                       key["development_count"] >= 60 and key["planned"] >= 30, [FROZEN])
            tp = key["nonabstained_accept_count"] - key["false_accept"]
            tn = key["nonabstained_reject_count"] - key["false_reject"]
            pa = key["positive_label_count"] - tp - key["false_reject"]
            na = key["negative_label_count"] - tn - key["false_accept"]
            self.check(lang + ":MATRIX", [True, key["correct"], key["abstain"], key["planned"]],
                       [min(tp, tn, pa, na) >= 0, tp + tn, pa + na,
                        key["correct"] + key["false_accept"] + key["false_reject"] + key["abstain"]], [FROZEN])
            self.metrics.append(dict(language=lang, development=key["development_count"], holdout=key["planned"],
                sample_gate_passed=False, false_accept_denominator=key["negative_label_count"],
                false_accept_rate=key["false_accept"] / key["negative_label_count"],
                nonabstained_coverage=(tp + tn + key["false_accept"] + key["false_reject"]) / key["planned"],
                accept_coverage=key["nonabstained_accept_count"] / key["planned"],
                actual_automatic_action_coverage=0, correct=key["correct"], abstain=key["abstain"],
                baseline=key["baseline"], cost_status=frozen["cost_status"]))
        for field in ("total", "correct", "false_accept", "false_reject", "abstain", "critical_false_accept"):
            self.check("OVERALL:" + field, aggregate[field], sum(k["planned" if field == "total" else field] for k in frozen["keys"]), [FROZEN])
        checks = self.read(FROZEN + "checks.json")
        self.check("PRIOR-SAFE-ASSERTIONS", [47, True], [len(checks), all(c["status"] == "PASS" and c["expected"] == c["actual"] for c in checks)], [FROZEN + "checks.json"])
        closed = self.read(BASE + "client-busy-591d16e/review.json")
        self.check("HISTORICAL-PIPE-FINDING-CLOSED", ["W11_LIVE_PIPE_BUSY_CLIENT", "CLOSED", "PASS_IN_SCOPE"],
                   [closed["finding"], closed["finding_status"], closed["verdict"]], [BASE + "client-busy-591d16e/review.json"])
        canary = self.read(INSTALLED + "canary-verification/report.json")
        self.check("ORIGINAL-NATIVE-CANARY-16", [16, True], [len(canary["assertions"]), all(c["status"] == "PASS" and c["expected"] == c["actual"] for c in canary["assertions"])], [INSTALLED])
        native = self.read(BASE + "formal-object-boundary/native-results.json")
        self.check("ACTUAL-FORMAL-HANDLE-DENIALS", [8, True], [len(native["assertions"]), all(c["actual_error"] == c["expected_error"] == 5 and c["bytes_read"] == c["bytes_written"] == 0 and c["status"] == "PASS" for c in native["assertions"])], [BASE + "formal-object-boundary/native-results.json"])
        identity = self.read(INSTALLED + "extra-native.json")
        self.check("NATIVE-DISTINCT-IDENTITY", [False, True, True, 5, 5],
                   [identity[x] for x in ("developer_elevated", "different_os_identity", "public_pid_matches_service", "ordinary_config_client_error", "public_second_instance_error")], [INSTALLED])
        outcomes = self.read(PRODUCT + "outcomes.json")
        self.check("PRODUCT-TWO-KEYS", ["zh", "zh-en"], [o["language"] for o in outcomes], [PRODUCT])
        receipts = []
        for outcome in outcomes:
            lang = outcome["language"]
            result = outcome["result"]
            self.check(lang + ":PRODUCT-SAFE-FAILURE", ["FAILED", "ADVISORY", True, "LIVE", 2, 45, 15],
                       [result[x] for x in ("status", "maximum_mode", "jev_called", "measurement_mode", "revision", "total_case_count", "holdout_case_count")], [PRODUCT + "outcomes.json"])
            self.check(lang + ":RESULT-PERSISTED", result, self.read(PRODUCT + lang + "-qualification-persisted.response.json"), [PRODUCT])
            receipt = self.read(PRODUCT + lang + "-independent-acceptance.response.json")
            self.check(lang + ":RECEIPT-PERSISTED", receipt, self.read(PRODUCT + lang + "-acceptance-persisted.response.json"), [PRODUCT])
            self.check(lang + ":INDEPENDENT-ACCEPTANCE", ["PASS", "LIVE", True, result["acceptance_id"], 3, True],
                       [receipt["verdict"], receipt["measurement_mode"], receipt["verifier_principal_id"] not in receipt["executor_principal_ids"], receipt["id"], len(receipt["checks"]), all(c["status"] == "PASS" for c in receipt["checks"])], [PRODUCT])
            self.check(lang + ":PUBLIC-SUMMARY-EXACT", aggregate, self.read(PRODUCT + lang + "-public-summary-content.response.json"), [PRODUCT])
            self.check(lang + ":PUBLIC-SUMMARY-HASH", outcome["public_summary_artifact"]["content_hash"],
                       "sha256:" + self.verified[PRODUCT + lang + "-public-summary-content.response.json"]["sha256"], [PRODUCT])
            receipts.append(dict(language=lang, id=receipt["id"], created_at=receipt["created_at"], checks=receipt["checks"]))
        events = self.read(PRODUCT + "http-events.json") + self.read(PRODUCT + "additional-http-events.json")
        for event in events:
            self.pin(PRODUCT + event["response_file"], event["body_sha256"])
        statuses = {e["name"]: e["status"] for e in events}
        for name, status in {"owner-holdout-content-denied": 404, "owner-holdout-metadata-denied": 404,
                             "verifier-holdout-content-denied": 503, "owner-restricted-search": 404,
                             "owner-artifact-list": 200, "owner-context-list": 200, "owner-event-list": 200}.items():
            self.check("PRODUCT-ISOLATION:" + name, status, statuses[name], [PRODUCT + "http-events.json", PRODUCT + "additional-http-events.json"])
        prior = self.read(BASE + "8a5ca295-69c0-4ebd-9ae3-8a8e266bc942.json")
        self.check("PRIOR-HARD-GATE-FIXTURE", [("C07", "PASS", "FIXTURE"), ("C08", "PASS", "FIXTURE")],
                   [(c["case_id"], c["verdict"], c["mode"]) for c in prior["owned_case_verdicts"]], [BASE + "8a5ca295-69c0-4ebd-9ae3-8a8e266bc942.json"])
        prerequisites = {
            "A08-01": ["FROZEN-SOURCE-INVENTORY", "DEVELOPMENT-EMBEDDED-HASH", "PROJECT-BINDING", "PRIOR-SAFE-ASSERTIONS"],
            "A08-02": [f"{lang}:{check}" for lang in ("zh", "zh-en") for check in ("SAMPLE-GATE-INSUFFICIENT", "PRODUCT-SAFE-FAILURE")],
            "A08-03": ["zh:MATRIX", "zh-en:MATRIX", "OVERALL:abstain", "SERVICE-COMPLETED"],
            "A08-04": ["SERVICE-COMPLETED", "zh:INDEPENDENT-ACCEPTANCE", "zh-en:INDEPENDENT-ACCEPTANCE", "zh:RESULT-PERSISTED", "zh-en:RESULT-PERSISTED"],
            "A08-05": ["PRIOR-HARD-GATE-FIXTURE", "zh:RECEIPT-PERSISTED", "zh-en:RECEIPT-PERSISTED", "SERVICE-COMPLETED"],
            "A08-06": ["ORIGINAL-NATIVE-CANARY-16", "ACTUAL-FORMAL-HANDLE-DENIALS", "NATIVE-DISTINCT-IDENTITY", "PRODUCT-ISOLATION:owner-holdout-content-denied", "PRODUCT-ISOLATION:verifier-holdout-content-denied", "PRODUCT-ISOLATION:owner-restricted-search"],
        }
        results = {c["assertion_id"]: c["status"] for c in self.checks}
        for assertion in mapping["assertions"]:
            ids = prerequisites[assertion["id"]]
            self.check(assertion["id"], {name: "PASS" for name in ids},
                       {name: results[name] for name in ids}, assertion["evidence"])
        results = {c["assertion_id"]: c["status"] for c in self.checks}
        for gate, ids in mapping["task_gates"].items():
            required = ids + (["INITIAL-LIVE-SAMPLES"] if gate == "W11-G02" else [])
            self.check(gate, {name: "PASS" for name in required},
                       {name: results[name] for name in required}, [MAP])
        self.original = dict(start_environment=self.read(PAST + "environment.json"), frozen_at=frozen["frozen_at"],
            timestamp_semantics=frozen_review["freeze_evidence"]["timestamp_semantics"],
            product_acceptances=receipts, source_continuity=continuity,
            task_gate_assertion_map=mapping["task_gates"], evidence_assertions=mapping["assertions"],
            original_modes={"W11-G02": "LIVE_SERVICE", "W11-G03": "LIVE_SERVICE", "W11-G04": "FIXTURE", "A08": "LIVE_SERVICE", "C07/C08": "FIXTURE"},
            scope_limits=product_review["scope_limits"] + [frozen_review["freeze_evidence"]["independence_limit"]],
            prior_open_findings=frozen_review.get("open_findings", []), superseding_client_review=closed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, default=ROOT)
    args = parser.parse_args()
    start = datetime.now(timezone.utc).isoformat()
    admission = Admission(args.evidence_root.resolve())
    error = None
    try:
        admission.run()
    except (ValueError, OSError, KeyError, StopIteration, subprocess.CalledProcessError) as exc:
        error = str(exc)
    output = ROOT / "execution/receipts/W11/admitted" / str(uuid.uuid4())
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema="researchos.w11-readonly-live-admission.v1", status="FAIL" if error else "PASS",
        measurement_mode="READ_ONLY_ADMISSION_OF_PAST_LIVE", started_at=start,
        finished_at=datetime.now(timezone.utc).isoformat(), assertion_count=len(admission.checks),
        assertions=admission.checks, evidence_files=admission.verified, original_provenance=admission.original,
        per_key_metrics=admission.metrics, new_provider_calls=0, private_body_or_labels_read=False,
        service_operations=[], automatic_authority="NONE", whole_W11_accepted=False,
        independent_acceptance="PENDING", error=error)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=report["status"], assertion_count=report["assertion_count"],
                         report=str(output / "report.json"), error=error), ensure_ascii=False))
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
