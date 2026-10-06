"""Independent verifier mutation battery for W09-01 (round 1) -- final driver.

Signed: qoder-desktop:/root/w0901_verifier_r1. This is NOT the executor's matrix.

Self-rules:
  * PRIMARY rows edit exactly ONE leg of one guard (`legs_edited == 1`); a whole compound
    condition is never flipped.
  * PAIR rows (kind == "redundancy_probe") deliberately edit two legs of the SAME
    protection that the primary row showed to be individually redundant, to prove the
    protection itself is real and to name the assertion that catches it. They are labelled
    and reported separately; they are not counted as single-leg mutants.
  * an anchor must occur EXACTLY ONCE, else the row is `anchor-missing` (never a kill,
    never a survival);
  * the package must still compile -- `go build` first; a compile failure is `crashed`;
  * every touched file's raw bytes are captured before and restored byte-for-byte after,
    with the digest verified;
  * survivors are reported completely.

Product measurement is my own `go test -json -run '^TestW0901' ./internal/domain`, not the
executor's handler; handler measurement is the delivered handler run directly.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path("D:/作品集/ResearchOS/research-os").resolve()
GO = str(ROOT / ".local/tools/go1.27.1/go/bin/go.exe")
HANDLER = ROOT / "tests/evidence/check/main.py"
OUT = ROOT / "execution/v2.4/receipts/W09/W09-01/verifier_mutation_r1.json"
LOG = ROOT / "execution/v2.4/receipts/W09/W09-01/verifier_mutation_r1_log.txt"

ROSTER41 = json.loads((ROOT / "execution/v2.4/receipts/W09/W09-01/receipt.json")
                      .read_text(encoding="utf-8"))["assertion_roster"]
_handler_src = (ROOT / "tests/evidence/check/main.py").read_text(encoding="utf-8")
_block = _handler_src.split("EXPECTED_IDS = [", 1)[1].split("]\n", 1)[0]
EXPECTED31 = sorted(set(re.findall(r'"(W0901-[A-Z0-9-]+)"', _block)))
assert set(EXPECTED31) <= set(ROSTER41)

SRC = "internal/domain/sources.go"
ORI = "internal/domain/evidence_origin.go"
RET = "internal/domain/retrieval.go"
LOC = "internal/domain/retrieval_local.go"
ADP = "adapters/retrieval/local.go"
HND = "tests/evidence/check/main.py"

U = "<none: no assertion in this card's roster names this leg>"

MUTANTS = [
    # ================= sources.go :: createEvidence (4 guards) =================
    {"name": "V01-create-snapshot-currency-leg", "kind": "single_leg", "expect":
     ["W0901-CREATE-REFUSED-WHEN-SNAPSHOT-NOT-CURRENT"],
     "edits": [(SRC, '\tif artifact["validity"] != "CURRENT" || artifact["content_hash"] != artifactRef["content_hash"] {',
               '\tif artifact["content_hash"] != artifactRef["content_hash"] {')]},
    {"name": "V02-create-snapshot-hash-leg", "kind": "single_leg", "expect":
     ["W0901-SUMMARY-BODY-CANNOT-BE-SWAPPED-FOR-SEALED-ORIGINAL"],
     "edits": [(SRC, '\tif artifact["validity"] != "CURRENT" || artifact["content_hash"] != artifactRef["content_hash"] {',
               '\tif artifact["validity"] != "CURRENT" {')]},
    {"name": "V03-create-kind-match-guard", "kind": "single_leg", "expect":
     ["W0901-OBSERVED-CLAIM-REFUSED-OVER-SIMULATED-SNAPSHOT"],
     "edits": [(SRC, '\tif artifact["evidence_kind"] != b["evidence_kind"] {', '\tif false {')]},
    {"name": "V04-create-observed-requires-live", "kind": "single_leg", "expect":
     ["W0901-OBSERVED-CLAIM-REFUSED-OVER-FIXTURE-MODE-SNAPSHOT"],
     "edits": [(SRC, '\tif b["evidence_kind"] == "OBSERVED" && artifact["measurement_mode"] != "LIVE" {', '\tif false {')]},

    # ================= evidence_origin.go ==========================================
    {"name": "O01-origin-subject-kind-leg", "kind": "single_leg", "expect":
     ["W0901-SIMULATED-EVIDENCE-REFUSED-ORIGIN-REVIEW"],
     "edits": [(ORI, '\tif ev["evidence_kind"] != "OBSERVED" || ev["validity"] != "CURRENT" {',
               '\tif ev["validity"] != "CURRENT" {')]},
    {"name": "O02-origin-subject-currency-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ORI, '\tif ev["evidence_kind"] != "OBSERVED" || ev["validity"] != "CURRENT" {',
               '\tif ev["evidence_kind"] != "OBSERVED" {')]},
    {"name": "O03-origin-origin-validity-leg", "kind": "single_leg", "expect":
     ["W0901-STALE-ORIGIN-CANNOT-ANCHOR-A-NEW-DOWNSTREAM"],
     "edits": [(ORI, '\t\tif origin["evidence_kind"] != "OBSERVED" || origin["validity"] != "CURRENT" {',
               '\t\tif origin["evidence_kind"] != "OBSERVED" {')]},
    {"name": "O04-origin-origin-kind-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ORI, '\t\tif origin["evidence_kind"] != "OBSERVED" || origin["validity"] != "CURRENT" {',
               '\t\tif origin["validity"] != "CURRENT" {')]},
    {"name": "O05-origin-citation-containment", "kind": "single_leg", "expect":
     ["W0901-UNCITED-REPOST-CANNOT-BE-ATTACHED-TO-THE-ORIGIN"],
     "edits": [(ORI, '\t\tif !strings.Contains(string(sourceBody), originURL) {',
               '\t\tif !strings.Contains(string(sourceBody), originURL) && false {')]},
    {"name": "O06-origin-basis-cites-evidence-hash-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ORI, '\tif !ok || ref["id"] != basisArtifactID || basis["content_hash"] != ref["content_hash"] {',
               '\tif !ok || ref["id"] != basisArtifactID {')]},
    {"name": "O07-reviewed-basis-revoked-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ORI, '\tif err != nil || status != "CURRENT" || revoked || rootRev != snapRev || hash != basis["content_hash"] {',
               '\tif err != nil || status != "CURRENT" || rootRev != snapRev || hash != basis["content_hash"] {')]},
    {"name": "O08-reviewed-basis-hash-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ORI, '\tif err != nil || status != "CURRENT" || revoked || rootRev != snapRev || hash != basis["content_hash"] {',
               '\tif err != nil || status != "CURRENT" || revoked || rootRev != snapRev {')]},

    # ================= retrieval.go ===============================================
    {"name": "R01-requireCurrentArtifactBody-currency", "kind": "single_leg", "expect":
     ["W0901-REVOKED-ROOT-SEALED-BODY-READ-DENIED"],
     "edits": [(RET, '\tif a["validity"] != "CURRENT" {\n\t\treturn Fail(409, "STATE_CONFLICT", "artifact body is no longer current")',
               '\tif false {\n\t\treturn Fail(409, "STATE_CONFLICT", "artifact body is no longer current")')]},
    {"name": "R02-requireCurrentArtifactBody-local-live-hash", "kind": "single_leg", "expect": [U],
     "edits": [(RET, '\tif local && (data == nil || Digest(data) != a["content_hash"]) {\n\t\treturn Fail(412, "STALE_INPUT", "local source changed or root authorization moved")',
               '\tif local && (data == nil || Digest(data) != a["content_hash"]) && false {\n\t\treturn Fail(412, "STALE_INPUT", "local source changed or root authorization moved")')]},
    {"name": "R09-currentAuthorizedSnapshots-local-hash-leg", "kind": "single_leg", "expect": [U],
     "edits": [(RET, '\t\tif local && (data == nil || Digest(data) != a["content_hash"]) {\n\t\t\tcontinue',
               '\t\tif local && (data == nil || Digest(data) != a["content_hash"]) && false {\n\t\t\tcontinue')]},
    {"name": "R03-readLocalSnapshot-hash-leg", "kind": "single_leg", "expect": [U],
     "edits": [(LOC, '\t\tif e == nil && Digest(data) == x.hash {', '\t\tif e == nil {')]},
    {"name": "R04-readLocalSnapshot-revoked-leg", "kind": "single_leg", "expect": [U],
     "edits": [(LOC, '\t\tif x.status != "CURRENT" || x.revoked || x.rootRev != x.snapRev {',
               '\t\tif x.status != "CURRENT" || x.rootRev != x.snapRev {')]},
    {"name": "R05-readLocalSnapshot-status-leg", "kind": "single_leg", "expect": [U],
     "edits": [(LOC, '\t\tif x.status != "CURRENT" || x.revoked || x.rootRev != x.snapRev {',
               '\t\tif x.revoked || x.rootRev != x.snapRev {')]},
    {"name": "R06-searchEvidence-local-hash-leg", "kind": "single_leg", "expect": [U],
     "edits": [(RET, '\t\t\tif data == nil || Digest(data) != a["content_hash"] {', '\t\t\tif data == nil {')]},
    {"name": "R07-searchEvidence-uploaded-body-hash-leg", "kind": "single_leg", "expect": [U],
     "edits": [(RET, '\t\t\tif err != nil || Digest(data) != a["content_hash"] {\n\t\t\t\treturn nil, Fail(422, "CONTENT_HASH_MISMATCH", "sealed snapshot unavailable")',
               '\t\t\tif err != nil {\n\t\t\t\treturn nil, Fail(422, "CONTENT_HASH_MISMATCH", "sealed snapshot unavailable")')]},
    {"name": "R08-searchEvidence-post-read-currency-leg", "kind": "single_leg", "expect": [U],
     "edits": [(RET, '\t\tif a["validity"] != "CURRENT" {\n\t\t\twarnings = append(warnings, "snapshot unavailable: "+id)',
               '\t\tif false {\n\t\t\twarnings = append(warnings, "snapshot unavailable: "+id)')]},

    # ================= retrieval_local.go =========================================
    {"name": "L01-canonical-measurement-mode-leg", "kind": "single_leg", "expect": [U],
     "edits": [(LOC, 'if a["evidence_kind"] != "OBSERVED" || a["measurement_mode"] != "LIVE" ||',
               'if a["evidence_kind"] != "OBSERVED" ||')]},
    {"name": "L02-canonical-evidence-kind-leg", "kind": "single_leg", "expect": [U],
     "edits": [(LOC, 'if a["evidence_kind"] != "OBSERVED" || a["measurement_mode"] != "LIVE" ||',
               'if a["measurement_mode"] != "LIVE" ||')]},
    {"name": "L03-capture-root-revoked-leg", "kind": "single_leg", "expect":
     ["W0901-REVOKED-ROOT-CANNOT-CAPTURE-AGAIN"],
     "edits": [(LOC, '\tif err != nil || revoked {\n\t\treturn nil, Fail(404, "NOT_FOUND", "authorized root unavailable")',
               '\tif err != nil {\n\t\treturn nil, Fail(404, "NOT_FOUND", "authorized root unavailable")')]},
    {"name": "L04-retire-evidence-propagation", "kind": "single_leg", "expect":
     ["W0901-REVOCATION-PROPAGATES-THROUGH-THE-CITATION-CHAIN"],
     "edits": [(LOC, '\t\tif o["validity"] == "CURRENT" {\n\t\t\to["validity"] = validity',
               '\t\tif false {\n\t\t\to["validity"] = validity')]},
    {"name": "L05-retire-artifact-validity", "kind": "single_leg", "expect":
     ["W0901-CREATE-REFUSED-WHEN-SNAPSHOT-NOT-CURRENT"],
     "edits": [(LOC, '\tif a["validity"] == "CURRENT" {\n\t\ta["validity"] = validity',
               '\tif false {\n\t\ta["validity"] = validity')]},
    {"name": "L06-capture-idempotence-reuses-current-hash", "kind": "single_leg", "expect": [U],
     "edits": [(LOC, '\tif previousID != "" && previousHash == Digest(data) {', '\tif false {')]},

    # ================= adapters/retrieval/local.go ================================
    {"name": "A01-root-relative-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ADP, '!filepath.IsLocal(relative) {', '!filepath.IsLocal(relative) && false {')]},
    {"name": "A02-root-identity-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ADP, '\t\tif actual != expectedIdentity {\n\t\t\treturn nil, fmt.Errorf("registered root identity changed")',
               '\t\tif actual != expectedIdentity && false {\n\t\t\treturn nil, fmt.Errorf("registered root identity changed")')]},
    {"name": "A03-expected-identity-missing-leg", "kind": "single_leg", "expect": [U],
     "edits": [(ADP, '\tif expectedIdentity == "" {\n\t\treturn nil, fmt.Errorf("registered root identity missing")',
               '\tif expectedIdentity == "impossible-sentinel-value" {\n\t\treturn nil, fmt.Errorf("registered root identity missing")')]},

    # ================= tests/evidence/check/main.py (the handler) =================
    {"name": "H01-route-always-serves", "kind": "single_leg", "handler": True,
     "expect": ["W0901-ROUTING-FOREIGN-BINDING-REFUSED", "W0901-ROUTING-TRUTH-TABLE"],
     "edits": [(HND, '    return "serve" if (task, check, case) == (OWNED_TASK, OWNED_CHECK, "") else "refuse"',
               '    return "serve"')]},
    {"name": "H02-route-never-serves", "kind": "single_leg", "handler": True,
     "expect": ["W0901-ROUTING-BINDING-SERVED"],
     "edits": [(HND, '    return "serve" if (task, check, case) == (OWNED_TASK, OWNED_CHECK, "") else "refuse"',
               '    return "refuse"')]},
    {"name": "H03-probe-depth-cap-removed", "kind": "single_leg", "handler": True,
     "note": "cap removal alone: on the delivered tree the child refuses before serve(), so no nesting happens; "
             "the cap is only load-bearing together with a broken route -- see the paired cap probe.",
     "expect": [U],
     "edits": [(HND, '    if os.environ.get("W0901_PROBE_DEPTH", ""):', '    if os.environ.get("W0901_PROBE_DEPTH_UNSET_SENTINEL", ""):')]},
    {"name": "H04-expected-roster-drops-one-id", "kind": "single_leg", "handler": True,
     "expect": ["W0901-ROSTER-EMITTED-EQUALS-EXPECTED", "W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED"],
     "edits": [(HND, '    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",\n', '')]},
    {"name": "H05-expected-roster-invents-one-id", "kind": "single_leg", "handler": True,
     "expect": ["W0901-ROSTER-EMITTED-EQUALS-EXPECTED", "W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED"],
     "edits": [(HND, '    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",\n',
               '    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",\n    "W0901-VERIFIER-FABRICATED-ID-THAT-NO-TEST-EMITS",\n')]},
    {"name": "H06-expected-roster-duplicates-an-id", "kind": "single_leg", "handler": True,
     "expect": ["W0901-ROSTER-EMITTED-EQUALS-EXPECTED", "W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED"],
     "edits": [(HND, '    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",\n',
                '    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",\n    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",\n')]},
    {"name": "H15-go-test-emits-an-id-no-list-knows", "kind": "single_leg", "handler": True,
     "note": "the decisive anti-tautology probe: a NEW emission added on the Go side only, unknown to EXPECTED_IDS",
     "expect": ["W0901-ROSTER-EMITTED-EQUALS-EXPECTED", "W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED"],
     "edits": [("internal/domain/evidence_w0901_test.go",
                '\tw09Assertion(t, "W0901-SEALED-BODY-READS-BACK-BYTES-IDENTICAL"',
                '\tw09Assertion(t, "W0901-VERIFIER-INTRUDER-ID-NOT-IN-EXPECTED-ROSTER", Object{"verifier_probe": true})\n\tw09Assertion(t, "W0901-SEALED-BODY-READS-BACK-BYTES-IDENTICAL"')]},
    {"name": "H07-roster-emitted-unexpected-leg", "kind": "single_leg", "handler": True,
     "note": "blinding one leg; paired with H04/H05 to show the OTHER legs are alive",
     "expect": [U],
     "edits": [(HND, '       result["code"] == 0 and not missing and not unexpected and not duplicates and not not_passing',
               '       result["code"] == 0 and not missing and not duplicates and not not_passing')]},
    {"name": "H08-roster-source-crosscheck-neutralised", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '    ok("W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED", source_ids is not None and source_ids == sorted(EXPECTED_IDS),',
               '    ok("W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED", True,')]},
    {"name": "H09-resolve-go-digest-check-neutralised", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '        if digest != tools.get("sha256"):', '        if digest != tools.get("sha256") and False:')]},
    {"name": "H10-resolve-go-version-check-neutralised", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '        if version.returncode != 0 or (version.stdout or "").strip() != tools.get("version_output"):',
               '        if version.returncode != 0:')]},
    {"name": "H11-resolve-go-absoluteness-check-neutralised", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '        if not path or not os.path.isabs(path) or not os.path.isfile(path):',
               '        if not path or not os.path.isfile(path):')]},
    {"name": "H12-suite-green-drops-failed-tests-leg", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '       result["code"] == 0 and not result["timed_out"] and not result["failed"]\n       and set(OWNED_TESTS) <= set(result["passed"]),',
               '       result["code"] == 0 and not result["timed_out"]\n       and set(OWNED_TESTS) <= set(result["passed"]),')]},
    {"name": "H13-counterexample-group-drops-its-positive-control", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '    "cache-hits-after-revocation": [\n        "W0901-SEALED-BODY-SERVED-BEFORE-REVOCATION",\n',
               '    "cache-hits-after-revocation": [\n')]},
    {"name": "H14-evidence-dir-check-neutralised", "kind": "single_leg", "handler": True,
     "expect": [U],
     "edits": [(HND, '       under_card_path and not short_files and not empty_files and bool(result["records"]),',
               '       True,')]},

    # ================= redundancy probes (two legs of the SAME protection) ========
    {"name": "P01-both-live-hash-legs-of-local-revalidation", "kind": "redundancy_probe", "expect":
     ["W0901-SEARCH-REVALIDATES-CURRENT-SOURCE-HASH-BEFORE-HIT"],
     "edits": [(LOC, '\t\tif e == nil && Digest(data) == x.hash {', '\t\tif e == nil {'),
               (RET, '\t\t\tif data == nil || Digest(data) != a["content_hash"] {', '\t\t\tif data == nil {')]},
    {"name": "P02-both-revocation-and-status-legs-of-readLocalSnapshot", "kind": "redundancy_probe", "expect":
     ["W0901-REVOKED-ROOT-FRESH-SEARCH-RETURNS-NO-HITS"],
     "edits": [(LOC, '\t\tif x.status != "CURRENT" || x.revoked || x.rootRev != x.snapRev {', '\t\tif false {')]},
    {"name": "P03-both-qualifying-legs-of-canonicalLocalArtifact", "kind": "redundancy_probe", "expect":
     ["W0901-SIMULATED-BYTES-REFUSED-RESEAL-AS-LIVE-LOCAL-SNAPSHOT"],
     "edits": [(LOC, '\t\tif a["evidence_kind"] != "OBSERVED" || a["measurement_mode"] != "LIVE" || a["access_class"] != "PROJECT" || a["media_type"] != "text/plain; charset=utf-8" || len(Arr(a, "input_refs")) != 0 || len(Arr(a, "source_refs")) != 0 {',
               '\t\tif false {')]},
    {"name": "P04-root-relative-plus-identity-legs-of-the-adapter", "kind": "redundancy_probe", "expect":
     ["W0901-CROSS-PROJECT-SAME-NAME-CAPTURE-THROUGH-FIRST-ROOT-REFUSED"],
     "edits": [(ADP, '!filepath.IsLocal(relative) {', '!filepath.IsLocal(relative) && false {'),
               (ADP, '\t\tif actual != expectedIdentity {\n\t\t\treturn nil, fmt.Errorf("registered root identity changed")',
                '\t\tif actual != expectedIdentity && false {\n\t\t\treturn nil, fmt.Errorf("registered root identity changed")')]},
    {"name": "P05-probe-cap-removed-AND-route-broken", "kind": "redundancy_probe", "handler": True,
     "expect": ["W0901-ROUTING-FOREIGN-BINDING-REFUSED"],
     "note": "This is the load-bearing pair for the self-probe depth cap. It is run with a hard wall-clock cap and a "
             "python-process count measurement; if the cap were NOT real this would spawn a chain of handlers, each "
             "also running go test. Capped at 150s.",
     "edits": [(HND, '    if os.environ.get("W0901_PROBE_DEPTH", ""):', '    if os.environ.get("W0901_PROBE_DEPTH_UNSET_SENTINEL", ""):'),
               (HND, '    return "serve" if (task, check, case) == (OWNED_TASK, OWNED_CHECK, "") else "refuse"', '    return "serve"')]},
    {"name": "H16-receipt-root-moved-out-of-card-dir", "kind": "single_leg", "handler": True,
     "note": "falsification probe for the evidence-location row: if RECEIPT_ROOT moves outside the card directory, "
             "does W0901-GO-TEST-EVIDENCE-WRITTEN-UNDER-CARD-DIRECTORY actually go red, or is it decorative?",
     "expect": ["W0901-GO-TEST-EVIDENCE-WRITTEN-UNDER-CARD-DIRECTORY"],
     "edits": [(HND, 'RECEIPT_ROOT = ROOT / "execution" / "v2.4" / "receipts" / "W09" / "W09-01" / "dispatched"',
               'RECEIPT_ROOT = ROOT / "execution" / "v2.4" / "receipts" / "W09" / "W09-01" / "verifier_h16_scratch"')]},
    {"name": "P06-create-currency-AND-hash-legs-both-gone", "kind": "redundancy_probe", "expect":
     ["W0901-CREATE-REFUSED-WHEN-SNAPSHOT-NOT-CURRENT", "W0901-SUMMARY-BODY-CANNOT-BE-SWAPPED-FOR-SEALED-ORIGINAL"],
     "edits": [(SRC, '\tif artifact["validity"] != "CURRENT" || artifact["content_hash"] != artifactRef["content_hash"] {', '\tif false {')]},
]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


TOUCHED = sorted({rel for m in MUTANTS for rel, _, _ in m["edits"]})
BASELINES = {rel: sha(ROOT / rel) for rel in TOUCHED}


def env_base():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["GOTOOLCHAIN"] = "local"
    env["GOPATH"] = str(ROOT / ".local" / "gopath")
    env["GOCACHE"] = str(ROOT / ".local" / "gocache")
    env["RESEARCHOS_GO"] = GO
    env.pop("W0901_PROBE_DEPTH", None)
    return env


def go_test_ids(timeout=420):
    argv = [GO, "test", "-count=1", "-json", "-timeout", "300s", "-run", "^TestW0901", "./internal/domain"]
    try:
        c = subprocess.run(argv, cwd=str(ROOT), env=env_base(), capture_output=True, timeout=timeout)
        out, err, rc = c.stdout, c.stderr, c.returncode
    except subprocess.TimeoutExpired as exc:
        return {"rc": 124, "emitted": [], "failed_tests": ["timeout"], "passed_tests": [],
                "build_error": (exc.stderr or b"").decode("utf-8", "replace")[-800:], "stderr": ""}
    events = []
    build_error = ""
    for line in out.decode("utf-8", "replace").splitlines():
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            build_error += line[:300]
    failed, passed = set(), set()
    for ev in events:
        if ev.get("Action") == "fail":
            (failed.add(ev["Test"]) if ev.get("Test") else None)
            if not ev.get("Test"):
                build_error += (ev.get("Output") or "")[:400]
        if ev.get("Action") == "pass" and ev.get("Test"):
            passed.add(ev["Test"])
    emitted = set()
    for line in "".join(e.get("Output", "") for e in events).splitlines():
        line = line.strip()
        if line.startswith("W09_ASSERTION "):
            try:
                emitted.add(json.loads(line[14:])["assertion_id"])
            except Exception:
                pass
    return {"rc": rc, "emitted": sorted(emitted), "failed_tests": sorted(failed),
            "passed_tests": sorted(passed), "build_error": build_error[-800:],
            "stderr": err.decode("utf-8", "replace")[-300:]}


def count_pythons():
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, timeout=20)
        return len([l for l in r.stdout.splitlines() if "python.exe" in l.lower()])
    except Exception:
        return -1


def run_handler(timeout=180):
    env = env_base()
    env.update({"RESEARCHOS_TASK_ID": "W09", "RESEARCHOS_CHECK_ID": "W09-01", "RESEARCHOS_CASE_ID": ""})
    before = count_pythons()
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(HANDLER)], cwd=str(ROOT), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak = before
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        try:
            out, err = proc.communicate(timeout=20)
        except Exception:
            out, err = b"", b""
    peak = max(peak, count_pythons())
    lines = (out or b"").decode("utf-8", "replace").strip().splitlines()
    report = {}
    if lines:
        try:
            report = json.loads(lines[-1])
        except ValueError:
            report = {}
    return {"rc": 124 if timed_out else proc.returncode, "timed_out": timed_out,
            "assertion_ids": report.get("assertion_ids", []), "stdout_lines": len(lines),
            "report": {k: report.get(k) for k in ("status", "assertions", "missing_assertion_ids",
                                                  "unexpected_assertion_ids", "failures", "routing_probe")},
            "python_processes_before": before, "python_processes_peak": peak,
            "python_processes_after": count_pythons()}


def go_build_ok():
    try:
        r = subprocess.run([GO, "build", "./internal/domain", "./adapters/retrieval"], cwd=str(ROOT),
                           env=env_base(), capture_output=True, timeout=300)
        return r.returncode == 0, r.stderr.decode("utf-8", "replace")[-500:]
    except Exception as exc:
        return False, str(exc)[:400]


print("baselines:", json.dumps(BASELINES, indent=1))
ONLY = [a for a in sys.argv[1:]]
MERGE = os.environ.get("VMERGE") == "1"
results = []
for m in MUTANTS:
    if ONLY and not any(m["name"].startswith(o) for o in ONLY):
        continue
    rels = sorted({rel for rel, _, _ in m["edits"]})
    row = {"mutant": m["name"], "kind": m["kind"], "files": rels, "legs_edited": len(m["edits"]),
           "expected": m["expect"]}
    if m.get("note"):
        row["note"] = m["note"]
    originals = {rel: (ROOT / rel).read_bytes() for rel in rels}
    row["digests_before"] = {rel: hashlib.sha256(originals[rel]).hexdigest() for rel in rels}
    row["digests_match_baselines"] = all(row["digests_before"][rel] == BASELINES[rel] for rel in rels)
    bad = []
    mutated = dict(originals)
    for rel, o, nw in m["edits"]:
        raw = mutated[rel]
        crlf = b"\r\n" in raw
        ob = o.replace("\n", "\r\n").encode("utf-8") if crlf else o.encode("utf-8")
        nb = nw.replace("\n", "\r\n").encode("utf-8") if crlf else nw.encode("utf-8")
        cnt = raw.count(ob)
        if cnt != 1:
            bad.append([rel, o[:70], cnt])
        else:
            mutated[rel] = raw.replace(ob, nb, 1)
    if bad:
        row.update(classification="anchor-missing", anchor_problems=bad,
                   restored_verified=all(sha(ROOT / rel) == BASELINES[rel] for rel in rels))
        results.append(row)
        print(json.dumps({k: row[k] for k in ("mutant", "classification")}, ensure_ascii=False))
        continue
    for rel in rels:
        (ROOT / rel).write_bytes(mutated[rel])
    try:
        okc, msg = go_build_ok()
        if not okc:
            row.update(classification="crashed", build_error=msg)
        elif m.get("handler"):
            obs = run_handler(timeout=45 if m["name"] == "P05-probe-cap-removed-AND-route-broken"
                              else (150 if m["kind"] == "redundancy_probe" else 180))
            red = sorted(set(ROSTER41) - set(obs["assertion_ids"]))
            row.update(red_assertions=red, handler_rc=obs["rc"], handler_status=obs["report"].get("status"),
                       unexpected=obs["report"].get("unexpected_assertion_ids"),
                       missing=obs["report"].get("missing_assertion_ids"),
                       routing_probe=obs["report"].get("routing_probe"), stdout_lines=obs["stdout_lines"],
                       python_processes={"before": obs["python_processes_before"], "peak": obs["python_processes_peak"],
                                         "after": obs["python_processes_after"]})
            named = [e for e in m["expect"] if not e.startswith("<")]
            if obs["rc"] == 124:
                row["classification"] = "crashed-timeout-capped"
                row["process_cap_observation"] = "the run hit the verifier's own wall-clock cap"
            elif not red and obs["rc"] == 0:
                row["classification"] = "SURVIVED"
            elif named and all(e in red for e in named):
                row["classification"] = "killed"
            else:
                row["classification"] = "red-elsewhere"
        else:
            obs = go_test_ids()
            red = sorted(set(EXPECTED31) - set(obs["emitted"]))
            row.update(red_assertions=red, go_rc=obs["rc"], failed_tests=obs["failed_tests"])
            if obs["build_error"]:
                row["build_error"] = obs["build_error"]
            named = [e for e in m["expect"] if not e.startswith("<")]
            if obs["rc"] != 0 and not red and not named:
                row["classification"] = "crashed"
            elif not red:
                row["classification"] = "SURVIVED"
            elif named and all(e in red for e in named):
                row["classification"] = "killed"
            else:
                row["classification"] = "red-elsewhere"
    finally:
        for rel in rels:
            (ROOT / rel).write_bytes(originals[rel])
        row["digests_after"] = {rel: sha(ROOT / rel) for rel in rels}
        row["restored_verified"] = all(row["digests_after"][rel] == row["digests_before"][rel] for rel in rels)
        if not row["restored_verified"]:
            for rel in rels:
                if row["digests_after"][rel] != row["digests_before"][rel]:
                    (ROOT / rel).write_bytes(originals[rel])
            row["EMERGENCY_RESTORE"] = True
            row["restored_verified"] = all(sha(ROOT / rel) == BASELINES[rel] for rel in rels)
    results.append(row)
    print(json.dumps({k: row[k] for k in ("mutant", "kind", "classification", "restored_verified")},
                     ensure_ascii=False))

FINAL = {rel: sha(ROOT / rel) for rel in TOUCHED}
single = [r for r in results if r["kind"] == "single_leg"]
pairs = [r for r in results if r["kind"] == "redundancy_probe"]
report = {
    "verifier_id": "qoder-desktop:/root/w0901_verifier_r1",
    "step_id": "W09-01", "parent_task": "W09", "round": 1,
    "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
    "repository_head_at_review": subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True,
                                                 text=True).stdout.strip(),
    "method": ("each row edits exactly one operand of one guard (single_leg) or, for redundancy_probe, the "
               "remaining operand of a protection a single_leg row already showed to be individually redundant; "
               "go build then `go test -json -run ^TestW0901 ./internal/domain` is executed by this driver and the "
               "red set is computed as EXPECTED31 minus the ids the suite still emits; handler rows run the delivered "
               "tests/evidence/check/main.py directly and the red set is ROSTER41 minus its assertion_ids"),
    "card_ids_expected": len(EXPECTED31), "roster41": len(ROSTER41),
    "touched_files": TOUCHED, "baselines": BASELINES, "final": FINAL,
    "all_restored_identical": BASELINES == FINAL,
    "single_leg_total": len(single),
    "single_leg_summary": {c: sum(1 for r in single if r["classification"] == c) for c in
                           ("killed", "SURVIVED", "red-elsewhere", "crashed", "anchor-missing")},
    "single_leg_survivors": [r["mutant"] for r in single if r["classification"] == "SURVIVED"],
    "redundancy_probe_total": len(pairs),
    "redundancy_probe_summary": {c: sum(1 for r in pairs if r["classification"] == c) for c in
                                 ("killed", "SURVIVED", "red-elsewhere", "crashed", "anchor-missing")},
    "rows": results,
}
if ONLY and MERGE and OUT.is_file():
    prev = json.loads(OUT.read_text(encoding="utf-8"))
    by_name = {r["mutant"]: r for r in prev["rows"]}
    by_name.update({r["mutant"]: r for r in results})
    report["rows"] = [by_name[m["name"]] for m in MUTANTS if m["name"] in by_name]
    report["all_restored_identical"] = prev["all_restored_identical"] and report["all_restored_identical"]
    single = [r for r in report["rows"] if r["kind"] == "single_leg"]
    pairs = [r for r in report["rows"] if r["kind"] == "redundancy_probe"]
    report["single_leg_total"] = len(single)
    report["single_leg_summary"] = {c: sum(1 for r in single if r["classification"] == c) for c in
                                    ("killed", "SURVIVED", "red-elsewhere", "crashed", "anchor-missing")}
    report["single_leg_survivors"] = [r["mutant"] for r in single if r["classification"] == "SURVIVED"]
    report["redundancy_probe_total"] = len(pairs)
    report["redundancy_probe_summary"] = {c: sum(1 for r in pairs if r["classification"] == c) for c in
                                          ("killed", "SURVIVED", "red-elsewhere", "crashed", "anchor-missing")}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
LOG.write_text("\n".join(json.dumps({k: r.get(k) for k in ("mutant", "kind", "classification", "expected",
                                                            "red_assertions", "restored_verified")},
                                    ensure_ascii=False) for r in results) + "\n", encoding="utf-8")
print(json.dumps({"single_leg_summary": report["single_leg_summary"],
                  "redundancy_probe_summary": report["redundancy_probe_summary"],
                  "all_restored_identical": report["all_restored_identical"]}, ensure_ascii=False))
