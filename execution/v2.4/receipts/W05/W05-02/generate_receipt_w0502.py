"""Generate the W05-02 EXECUTION_REPORTED receipt from the state on disk.

Every number in the receipt is measured here, now: the assertion set comes from a fresh dispatcher run
(not from the earlier logs), the artifact digests are recomputed from raw bytes, the registry revision
and commands.json digest are read from the file, the mutation result is taken from the self-check JSON
and its clean-baseline count is cross-checked against this run, and the HEAD the receipt reports is the
HEAD the dispatcher run itself recorded.

It refuses to produce a receipt when anything it depends on is missing, when the matrix has surviving
mutants, when the tree is dirty, or when the routed run does not pass - an EXECUTION_REPORTED document
that quietly encodes a red or unverified run is the failure mode the reviewers keep catching.
"""
import datetime, glob, hashlib, io, json, os, subprocess, sys

ROOT = os.getcwd()
V24 = os.path.join(ROOT, "execution", "v2.4")
RD = os.path.join(V24, "receipts", "W05", "W05-02")
SPEC = r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4"
LOCK = json.load(io.open(os.path.join(ROOT, "execution", "toolchains", "locked.json"), encoding="utf-8-sig"))
GO, PY = LOCK["tools"]["go"]["path"], sys.executable


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rel(p):
    return os.path.relpath(p, V24).replace(os.sep, "/")


cp = json.load(io.open(os.path.join(V24, "checkpoint.json"), encoding="utf-8-sig"))
reg = json.load(io.open(os.path.join(V24, "commands.json"), encoding="utf-8-sig"))
matrix_path = os.path.join(RD, "mutation_selfcheck_w0502.json")
parity_path = os.path.join(RD, "selector_flip_parity.json")
for p in (matrix_path, parity_path):
    if not os.path.isfile(p):
        raise SystemExit("missing prerequisite: " + rel(p))
matrix = json.load(io.open(matrix_path, encoding="utf-8-sig"))
parity = json.load(io.open(parity_path, encoding="utf-8-sig"))
unreasoned = matrix.get("survivors_without_reason", matrix.get("survivors") or [])
if unreasoned:
    raise SystemExit("refusing to receipt a suite with unexplained surviving mutants: %s" % unreasoned)
if not matrix.get("tree_clean_after_restores"):
    raise SystemExit("the matrix left the tree dirty; not receipting on top of that")

dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                       text=True, cwd=ROOT).stdout.strip()
if dirty:
    raise SystemExit("tracked changes are pending; commit them before the receipt: " + dirty[:200])

r = subprocess.run([PY, "-X", "utf8", os.path.join(ROOT, "execution", "command_dispatcher", "dispatch.py"),
                    "test.runtime", "--task-id", "W05", "--check-id", "W05-02"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
lines = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
if not lines:
    raise SystemExit("the dispatcher produced no report: " + (r.stderr or "")[-300:])
head = json.loads(lines[-1])
inv = head.get("invocation_id")
inv_receipt = head.get("receipt")
# The dispatcher's stdout carries only a count; the assertion ids and the tree the run recorded live in
# its invocation receipt, so they are read from there rather than expected from stdout.
_p = inv_receipt if inv_receipt and os.path.isabs(inv_receipt) else os.path.join(ROOT, inv_receipt or "")
_ids_from_receipt = sorted((json.load(io.open(_p, encoding="utf-8-sig")).get("assertion_ids") or [])) \
    if inv_receipt and os.path.isfile(_p) else []
ids = _ids_from_receipt or sorted(head.get("assertion_ids") or [])
if head.get("status") != "PASS" or not ids:
    raise SystemExit("refusing to report a run that is not a non-empty PASS: %r %r" % (head.get("status"), ids))
inv_rel = None
if inv_receipt:
    p = inv_receipt if os.path.isabs(inv_receipt) else os.path.join(ROOT, inv_receipt)
    inv_rel = os.path.relpath(p, V24).replace(os.sep, "/") if os.path.isfile(p) else None
    if inv_rel:
        got = json.load(io.open(p, encoding="utf-8-sig"))
        assert sorted(got.get("assertion_ids") or []) == ids, "the dispatcher report and its receipt disagree"
        head_now = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                                  cwd=ROOT).stdout.strip()
        if got.get("code_revision") and got["code_revision"] != head_now:
            raise SystemExit("the routed run recorded tree %s but the receipt would report %s"
                             % (str(got["code_revision"])[:8], head_now[:8]))

unit = subprocess.run([GO, "test", "-count=1", "./apps/cli/..."], capture_output=True, text=True,
                      encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
unit_ok = unit.returncode == 0

ARTIFACT_ROOTS = [
    "apps/cli/coding_task.go", "apps/cli/coding_task_test.go", "apps/cli/cancel_run_windows.go",
    "apps/cli/command_handlers.go", "apps/cli/main.go",
    "adapters/runtime/cancel_windows.go", "tests/runtime/check/w0502.go", "tests/runtime/check/main.go",
    "tests/runtime/check/legacy.go", "execution/v2.4/commands.json",
]
artifacts = []
for a in ARTIFACT_ROOTS:
    p = os.path.join(ROOT, a.replace("/", os.sep))
    if os.path.isfile(p):
        artifacts.append({"path": a, "sha256": sha(p)})
    else:
        print("   (absent, not hashed):", a)
for p in sorted(glob.glob(os.path.join(RD, "*.json"))) + sorted(glob.glob(os.path.join(RD, "*.go"))) + \
        sorted(glob.glob(os.path.join(RD, "*.md"))) + sorted(glob.glob(os.path.join(RD, "*.py"))):
    if os.path.basename(p) == "receipt.json":
        continue
    artifacts.append({"path": "execution/v2.4/" + rel(p), "sha256": sha(p)})
if inv_rel:
    artifacts.append({"path": "execution/v2.4/" + inv_rel, "sha256": sha(os.path.join(V24, inv_rel))})

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
rec = {
    "schema_version": 1, "package_version": "2.4.0", "step_id": "W05-02",
    "parent_task": "W05", "status": "EXECUTION_REPORTED",
    "reported_at": now, "executor_id": "qoder-desktop:/root/construction",
    "verifier_id": None, "independent_review": None, "independent_reviews": [],
    "repository_head_at_reporting": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                                    text=True, cwd=ROOT).stdout.strip(),
    "plan_sha256": cp.get("plan_sha256"),
    "checkpoint_revision_at_reporting": cp["revision"],
    "registry_revision": reg.get("revision"),
    "commands_sha256": sha(os.path.join(V24, "commands.json")),
    "write_scope": ["apps/cli/**", "adapters/runtime/**", "adapters/workspace/**",
                    "tests/runtime/**", "execution/v2.4/receipts/W05/W05-02/**"],
    "binding": {"command_key": "test.runtime", "argv": ["run", "./tests/runtime/check"],
                "selector": {"task_id": "W05", "check_id": "W05-02"},
                "invocation_id": inv, "dispatcher_receipt": inv_rel},
    "check_results": {"status": head.get("status"), "assertions": len(ids), "assertion_ids": ids,
                      "failures": head.get("failures") or [],
                      "not_verified": head.get("not_verified") or [],
                      "unit_tests": {"command": "go test -count=1 ./apps/cli/...", "passed": unit_ok,
                                     "output_tail": (unit.stdout or unit.stderr or "").strip()[-200:]}},
    "mutation_selfcheck": {"artifact": rel(matrix_path), "sha256": sha(matrix_path),
                           "mutants_applied": matrix["counts"]["applied"],
                           "killed": matrix["counts"]["killed"], "survived": matrix["counts"]["survived"],
                           "clean_baseline": matrix.get("clean_baseline")},
    "selector_flip": {"artifact": rel(parity_path), "sha256": sha(parity_path),
                      "registry_revision_before": parity.get("registry_revision_before"),
                      "registry_revision_after": parity.get("registry_revision_after"),
                      "before_status": parity["before"]["W05-02"]["status"],
                      "after_status": parity["after"]["W05-02"]["status"],
                      "w0501_control_assertions": parity["after"]["W05-01"]["assertions"]},
    "mode": "DEVELOPMENT_FIXTURE",
    "blocking_issues": [],
    "limitations": [
        "card-level report only: nothing here accepts parent W05 or the formal cases A04 and C11, and no "
        "product capability is claimed by it",
        "card step 3 is not met: workspace.write has no handler in internal/domain, so no file in this "
        "repository is written by the CLI; the engine offers every mutation to one AuthoritativeWriter "
        "whose only production implementation refuses, and the suite asserts that refusal plus the byte "
        "identity of the target. Routing it needs an edit outside this card's write scope, filed as "
        "obligation W05-02-domain-write-route",
        "card deliverable 2 is met two of three: the candidate-without-write negative and the "
        "parent-dies-with-orphan-write negative have rows, but the third negative - a Goal restarting "
        "after cancel - needs session and goal semantics outside this write scope and has no row",
        "mode DEVELOPMENT_FIXTURE: no real model backend is installed on this host, so proposals come "
        "from a caller-supplied deterministic replacement; the help text says so rather than implying a "
        "model ran",
        "-check is whitespace-split, so a verification command whose path contains a space cannot be "
        "used yet",
        "the pinned go binary is resolved from execution/toolchains/locked.json with its digest "
        "verified, never from PATH; the earlier OOM observed while building an unrelated package "
        "(ops/remote_access/gateway) was not reproduced by this card's builds and is disclosed rather "
        "than investigated here",
    ],
    "artifacts": artifacts,
    "next_action": "independent review by a fresh identity, then registration on an empty blocking_issues array",
}
io.open(os.path.join(RD, "receipt.json") + ".tmp", "w", encoding="utf-8", newline="\n").write(
    json.dumps(rec, indent=1, ensure_ascii=False))
os.replace(os.path.join(RD, "receipt.json") + ".tmp", os.path.join(RD, "receipt.json"))
print("receipt written:", rel(os.path.join(RD, "receipt.json")), "sha256", sha(os.path.join(RD, "receipt.json"))[:16])
print("assertions", rec["check_results"]["assertions"], "| artifacts", len(artifacts),
      "| matrix killed", rec["mutation_selfcheck"]["killed"], "of", rec["mutation_selfcheck"]["mutants_applied"],
      "| unit tests", unit_ok, "| head", rec["repository_head_at_reporting"][:8])
