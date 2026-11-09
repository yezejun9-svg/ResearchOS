"""W04-02 round-3 mutation matrix.

Every case is applied alone, the construction check runs, the failing assertion ids are recorded, and
the file is restored and hash-verified before the next case. Results are appended to a log as they
happen so a crash loses nothing.

Two kinds of case are in here and are reported separately:
  * product mutations, which must be killed by a named assertion;
  * the two test-side mutations of the roster floor itself, which must be killed by the floor - that
    is the only way to show the floor is not decorative.

Files outside this card's write_scope (materialize.go, http.go) are mutated as temporary diagnostics
only and restored hash-exact; nothing about them is delivered.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time

REPO = os.getcwd()
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ)
ENV.update({"GOTOOLCHAIN": "local", "GOFLAGS": "", "GOENV": "off", "PYTHONIOENCODING": "utf-8",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"), "RESEARCHOS_GO": GO})

CHG = "internal/domain/changes.go"
CTX = "internal/domain/context.go"
MAT = "internal/domain/materialize.go"
HTTP = "internal/domain/http.go"
TST = "tests/context/check/w0402.go"

OUT = os.path.join(".local", "mutation_round3.json")
LOG = os.path.join(".local", "mutation_round3.log")

IN_SCOPE = {CHG, CTX, TST}

# --- the 15 cases carried over from the delivered round-1/2 matrices -----------------------------
# anchors are copied verbatim from mut_w0402.py / mut_w0402b.py / mut_w0402c.py so the comparison
# with the delivered results is like for like. Z1 and Z7-impact-links-not-recorded were dropped by
# the original runner as shape guesses and are not claimed here either.
PRIOR = [
    ("Z2-context-cas-removed", CTX,
     '\tif Hash(state["revision"]) != Hash(b["expected_project_state_revision"]) {',
     '\tif false && Hash(state["revision"]) != Hash(b["expected_project_state_revision"]) {'),
    ("Z3-bundle-integrity-unchecked", MAT,
     '\tif bundle["receipt_hash"] != Receipt(bundle) || bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary"))) {',
     '\tif false && (bundle["receipt_hash"] != Receipt(bundle) || bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary")))) {'),
    ("Z4-worker-grant-unchecked", MAT,
     '\tif !p.Allowed(project, taskID, "", false) && !s.runtimeScope(tx, p, project, taskID, "getTask", nil) {',
     '\tif false && !p.Allowed(project, taskID, "", false) && !s.runtimeScope(tx, p, project, taskID, "getTask", nil) {'),
    ("Z5-existing-destination-accepted", MAT,
     '\tif _, e = os.Stat(destination); !os.IsNotExist(e) {',
     '\tif false && !os.IsNotExist(func() error { return nil }()) {'),
    ("Z6-delivered-inputs-stay-writable", MAT,
     '\t\tif e = os.Chmod(path, 0444); e != nil {',
     '\t\tif e = os.Chmod(path, 0666); e != nil {'),
    ("Z7-impact-link-basis-not-deterministic", CTX,
     '"relation": "DEPENDS_ON", "basis": "DETERMINISTIC"',
     '"relation": "DEPENDS_ON", "basis": "USER_STATED"'),
    ("Z7b-freeze-records-no-dependency-links", CTX,
     "\tfor _, r := range refs {", "\tfor _, r := range []Object{} {"),
    ("Z8-supported-checks-freeze-unenforced", CHG,
     '\tif Hash(b["test_check_ids"]) != Hash(changeChecks) {',
     '\tif false && Hash(b["test_check_ids"]) != Hash(changeChecks) {'),
    ("Z9-proposal-base-cas-removed", CHG,
     '\tif Hash(state["revision"]) != Hash(b["base_state_revision"]) {',
     '\tif false && Hash(state["revision"]) != Hash(b["base_state_revision"]) {'),
    ("Z10-missing-context-gate-removed", CTX,
     '\t\treturn Fail(422, "GATE_FAILED", "task context required")', "\t\treturn nil"),
    ("Z11-edit-target-staleness-unchecked", CHG,
     "\t\tif Hash(Ref(current, kind)) != Hash(r) {",
     "\t\tif false && Hash(Ref(current, kind)) != Hash(r) {"),
    ("AA1-author-can-accept-own-change", CHG,
     "\t\tif id == p.ID {", "\t\tif false && id == p.ID {"),
    ("AA2-resolution-does-not-require-an-applied-change", CHG,
     '\tif proposal["status"] != "APPLIED" {', '\tif false && proposal["status"] != "APPLIED" {'),
    # the variant the delivered round-1/2 matrix actually ran, kept for a like-for-like comparison
    ("AA2b-resolution-status-guard-inverted", CHG,
     '\tif proposal["status"] != "APPLIED" {', '\tif proposal["status"] == "APPLIED" {'),
    ("AC3-applied-change-stops-invalidating-its-dependents", CHG,
     '\t\t\to["status"] = "NEEDS_REVALIDATION"', '\t\t\to["status"] = "DRAFT"'),
    ("AD1-freeze-ignores-the-governing-decisions", CTX,
     '\t\t\tunresolved = append(unresolved, "governing decision no longer resolvable: "+Str(r, "id"))\n'
     '\t\t\tcontinue\n'
     '\t\t}\n'
     '\t\tdecisions = append(decisions, r)',
     '\t\t\tunresolved = append(unresolved, "governing decision no longer resolvable: "+Str(r, "id"))\n'
     '\t\t\tcontinue\n'
     '\t\t}\n'
     '\t\t_ = r'),
]

# --- new cases, one per remediated item ----------------------------------------------------------
NEW = [
    # item 1 / B3: the settled conflict must leave the project's blocking index
    ("N1-resolution-leaves-the-blocking-index-behind", CHG,
     '\t\tif fmt.Sprint(v) == id {\n\t\t\tcontinue\n\t\t}',
     '\t\tif false {\n\t\t\tcontinue\n\t\t}'),
    # item 1 / B4: a settled conflict must not be settleable again
    ("N2-resolved-conflict-can-be-resolved-again", CHG,
     '\tif o["status"] != "OPEN" {', '\tif false {'),
    # item 1 / B4: any applied change must not be able to settle any conflict
    ("N3-resolution-needs-no-relation-to-the-dispute", CHG,
     "\tif !settlesDispute(proposal, id, ids, triples) {",
     "\tif !settlesDispute(proposal, id, ids, triples) && false {"),
    # item 5 / B5: the service-side integrity guard, which Z3 could not reach
    ("N4-service-integrity-guard-only-checks-the-summary", MAT,
     '\tif bundle["receipt_hash"] != Receipt(bundle) || bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary"))) {',
     '\tif bundle["summary_hash"] != Digest([]byte(Str(bundle, "summary"))) {'),
    # item 2 / B6: the recovered next step must be accurate by value
    ("N5-continuation-drops-the-next-task", CTX,
     '"next_task_id": task["id"], "next_task_title": task["title"]',
     '"next_task_id": "", "next_task_title": task["title"]'),
    ("N6-continuation-drops-the-operators-intent", CTX,
     '"goal_intent": goal["original_intent"]', '"goal_intent": ""'),
    ("N7-continuation-drops-the-acceptance-contract", CTX,
     '"acceptance_contract": task["acceptance_contract"]}', '"acceptance_contract": nil}'),
    # item 3 / B2: the proposal's own impact arrays are really produced here. Mutating the closure
    # call rather than the stored fields, because blanking the fields leaves them unused and the
    # case then measures a compile error instead of a behaviour.
    ("N8-proposal-stops-naming-its-impact", CHG,
     "\timpacted, links, e := s.closure(tx, project, roots)",
     "\timpacted, links, e := s.closure(tx, project, nil)"),
    # item 2 / B6: unresolved_items and unfinished_commitments carry content, not just keys
    ("N9-freeze-stops-naming-open-conflicts", CTX,
     '\t\tunresolved = append(unresolved, "Open conflict: "+v.(string))',
     '\t\t_ = v'),
    ("N10-commitments-drop-the-dependency-status", CTX,
     '\t\t\tcommitments = append(commitments, "Dependency "+v.(string)+" remains "+Str(dep, "status"))',
     '\t\t\tcommitments = append(commitments, "Dependency "+v.(string))'),
    ("N11-freeze-invents-its-own-facts", CTX,
     '"facts": profile["facts"]', '"facts": Empty()'),
    # item 2 / B6: the delivered resume instruction is the one the service returned
    ("N12-manifest-carries-no-resume-instruction", MAT,
     '"resume_instruction": "Read the frozen bundle and produce candidates; acceptance requires the independent service."',
     '"resume_instruction": ""'),
    # item 4 / B1: the acceptance role gate is what that assertion now names
    ("N13-acceptance-role-gate-removed", HTTP,
     "\tif !roleOK {", "\tif !roleOK && false {"),
    # item 7: the revision-CAS mutant round 2 invented, expected to survive as an equivalent mutant
    ("N14-bundle-stores-the-claimed-revision", CTX,
     '"project_state_revision": state["revision"]',
     '"project_state_revision": b["expected_project_state_revision"]'),
    # item 8: the roster floor must itself be able to fail, in each direction separately.
    # N15 renames an emitted id, which is the silent-drop class the floor exists for.
    ("N15-an-assertion-id-is-renamed-away", TST,
     'ok("CTX-BUNDLE-REVISION-IS-ONE",', 'ok("CTX-BUNDLE-REVISION-IS-ONE-RENAMED",'),
    # N16 declares an id nothing emits: only the forward "nothing was dropped" leg may fail.
    ("N16-roster-declares-an-id-that-is-never-emitted", TST,
     '\t"CTX-BUNDLE-REVISION-IS-ONE",\n',
     '\t"CTX-BUNDLE-REVISION-IS-ONE",\n\t"CTX-DECLARED-BUT-NEVER-EMITTED",\n'),
    # N17 drops a declared id that IS emitted: only the reverse "floor matches the source" leg may fail.
    ("N17-roster-forgets-an-id-that-is-emitted", TST,
     '\t"CTX-BUNDLE-REVISION-IS-ONE",\n', ''),
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# A survivor is allowed, but only with a reason that says why no assertion could have caught it.
# An unexpected survivor is recorded as such rather than being quietly given a justification.
SURVIVOR_REASONS = {
    "N14-bundle-stores-the-claimed-revision": (
        "equivalent mutant, not a coverage gap. createContext refuses with 412 STALE_REVISION unless "
        "Hash(state['revision']) == Hash(b['expected_project_state_revision']) (context.go:202-204), so "
        "at the line this mutation changes the two values are Hash-equal by construction and no "
        "assertion over the bundle can distinguish them. The guard that makes them equal is itself "
        "mutation-covered: Z2-context-cas-removed deletes it and CTX-STALE-EXPECTED-REVISION-REJECTED "
        "dies. This is the mutation round 2 invented; it is reported as survived-with-proof rather than "
        "claimed as killed."),
    "N4-service-integrity-guard-only-checks-the-summary": (
        "UNEXPECTED if this still survives: CTX-SERVICE-REFUSES-A-TAMPER-THAT-LEAVES-THE-SUMMARY-ALONE "
        "corrupts $.facts, which leaves summary_hash matching, so only the receipt_hash half can refuse "
        "it. If this row is a survivor the second tamper leg is not reaching the guard."),
}


def reason_for(name):
    return SURVIVOR_REASONS.get(name, "UNEXPECTED SURVIVOR - no reason recorded")


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def log(line):
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def run_check():
    r = subprocess.run([GO, "run", "./tests/context/check"], cwd=REPO, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [l for l in (r.stdout or "").strip().splitlines() if l.startswith("{")]
    if not lines:
        return {"status": "NOJSON", "assertions": 0,
                "failures": [{"id": "RAW", "detail": ((r.stdout or "") + (r.stderr or ""))[:400]}]}
    try:
        return json.loads(lines[-1])
    except ValueError:
        return {"status": "BADJSON", "assertions": 0,
                "failures": [{"id": "RAW", "detail": lines[-1][:400]}]}


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    cases = [(n, p, a, b, "prior") for n, p, a, b in PRIOR] + \
            [(n, p, a, b, "new") for n, p, a, b in NEW]
    if only:
        cases = [c for c in cases if c[0] == only]
        if not cases:
            sys.exit("no such case: " + only)

    # anchors are verified before anything is written, so a moved anchor is reported rather than
    # silently skipping a case
    for name, path, old, new in [(c[0], c[1], c[2], c[3]) for c in cases]:
        if old is None:
            log("%-52s ANCHOR NOT SUPPLIED - carried by name only" % name)
            continue
        n = read(path).count(old)
        if n != 1:
            log("%-52s ANCHOR_COUNT=%d in %s" % (name, n, path))

    report = []
    for name, path, old, new, family in cases:
        if old is None or new is None or old == new:
            report.append({"mutation": name, "file": path, "family": family,
                           "status": "ANCHOR_MISSING", "note": "no distinct anchor supplied"})
            log("%-52s ANCHOR_MISSING" % name)
            continue
        original = read(path)
        count = original.count(old)
        if count != 1:
            report.append({"mutation": name, "file": path, "family": family,
                           "status": "ANCHOR_MISSING", "anchor_count": count})
            log("%-52s ANCHOR_MISSING count=%d" % (name, count))
            continue
        h0 = sha(path)
        started = time.time()
        write(path, original.replace(old, new, 1))
        d = run_check()
        write(path, original)
        restored = h0 == sha(path)
        failed = [f["id"] for f in (d.get("failures") or [])]
        entry = {"mutation": name, "file": path, "family": family,
                 "in_write_scope": path in IN_SCOPE,
                 "status": d.get("status"), "assertions": d.get("assertions", 0),
                 "failed_ids": failed, "restored_hash_exact": restored,
                 "seconds": round(time.time() - started, 1)}
        if d.get("status") == "PASS":
            entry["survivor_reason"] = reason_for(name)
        if d.get("status") in ("NOJSON", "BADJSON"):
            entry["crash_detail"] = (d.get("failures") or [{}])[0].get("detail", "")[:300]
        report.append(entry)
        log("%-52s %-8s assertions=%-4s failed=%d restored=%s %s"
            % (name, d.get("status"), d.get("assertions"), len(failed), restored,
               ",".join(failed[:5])))
        if not restored:
            sys.exit("RESTORE FAILED for %s - stopping before anything else is touched" % name)
        io.open(OUT, "w", encoding="utf-8", newline="\n").write(
            json.dumps(report, indent=1, ensure_ascii=False))

    d = run_check()
    report.append({"baseline_after_matrix": d.get("status"), "assertions": d.get("assertions"),
                   "failures": d.get("failures") or [],
                   "not_verified": d.get("not_verified") or []})
    log("BASELINE AFTER MATRIX %s %s" % (d.get("status"), d.get("assertions")))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(report, indent=1, ensure_ascii=False))


main()
