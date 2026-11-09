#!/usr/bin/env python3
"""Independent round-1 mutation matrix for ResearchOS card W08-01.

Reviewer identity: qoder-desktop:/root/w0801_verifier_r1. This is the reviewer's OWN matrix; the
executor's mut_w0801_round1.py was not re-run or reused.

Oracle: the card's real handler, `go run ./tests/research/check`, under the same
RESEARCHOS_TASK_ID=W08 / RESEARCHOS_CHECK_ID=W08-01 binding the dispatcher injects. Proven
equivalent first: the direct run and the dispatcher's frozen stdout.txt share sha256
98820a8d96d9818f705573144fdfa1caaa63a263ef56e649b2227a977b281057 byte for byte.

Protocol per mutant:
  1. assert both mutable files still match the frozen digest (clean tree),
  2. run clean      -> must be PASS with 64 assertion ids, else the mutant is not measured (BASELINE-RED),
  3. apply the mutation as REACHABLE code,
  4. run mutated    -> collect assertion_ids, failures, exit code, live child-process count,
  5. restore byte-for-byte and re-verify the digest,
  6. run clean again (also serves as step 2 for the next mutant once the digest re-verifies).

Classification (anchors = assertions that MUST go red, chosen from the delivered bytes, never stale):
  caught          >=1 anchor is in the mutated failures list
  survived        no anchor red, >=1 anchor still green
  anchor-missing  no anchor red and no anchor green (the id is not produced by this build)
  unguarded       the mutant has no anchor because no assertion names that guard at all
  collateral-caught  no named anchor, but something else went red anyway
  crashed         the mutated tree did not report (build failure, panic, unparsable stdout)
Collateral reds are always recorded, never used to upgrade a survivor.
"""
import hashlib
import json
import os
import subprocess
import time

REPO = "D:/作品集/ResearchOS/research-os"
ADOPT = "internal/domain/adoption.go"
CHECK = "tests/research/check/main.go"
EVDIR = "execution/v2.4/receipts/W08/W08-01/review_r1"
GO = "D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe"
DIGESTS = {
    ADOPT: "a0c6fcb6efae0524216d7c03e228f801e9fb7888d9f8b799307cae03321a1cd3",
    CHECK: "a506e40467e5bae45726bbc848faa4b06fb03ee263dade2db4a0e45fe40931e4",
}
CLEAN_SHA = "98820a8d96d9818f705573144fdfa1caaa63a263ef56e649b2227a977b281057"
ENV = dict(os.environ, GOTOOLCHAIN="local",
           GOPATH="D:/作品集/ResearchOS/research-os/.local/gopath",
           GOCACHE="D:/作品集/ResearchOS/research-os/.local/gocache",
           RESEARCHOS_TASK_ID="W08", RESEARCHOS_CHECK_ID="W08-01",
           PYTHONIOENCODING="utf-8")

PROBE = "W0801-ROUTING-SELF-PROBE-REFUSES-FOREIGN-BINDING"

# id, guard under test, file, old, new, anchors-that-must-go-red
M = [
    # ---- ValidateReuseDecision: the frozen-contract guard ----
    ("R1-M01", "missing-field loop over the 14 declared fields", ADOPT,
     'for _, k := range reuseDecisionRequired {\n\t\tif _, ok := b[k]; !ok {',
     'for _, k := range reuseDecisionRequired {\n\t\tif _, ok := b[k]; !ok && false {',
     ["W0801-GUARD-MISSING-PROJECT_ID", "W0801-GUARD-MISSING-LICENSE_REF",
      "W0801-GUARD-MISSING-ADOPTION_DECISION_REF"]),
    ("R1-M02", "undeclared-field refusal (additionalProperties:false)", ADOPT,
     '\t\tif !known {\n\t\t\treturn "", Fail(400, "INVALID_REQUEST", "reuse decision carries an undeclared field "+k)',
     '\t\tif !known && false {\n\t\t\treturn "", Fail(400, "INVALID_REQUEST", "reuse decision carries an undeclared field "+k)',
     ["W0801-GUARD-UNDECLARED-FIELD-REFUSED"]),
    ("R1-M03", "COUNTER-EXAMPLE 1 clone recorded as ADOPT_UPSTREAM", ADOPT,
     '\tif decision != "REUSE_LOCAL" && decision != "CUSTOM_GAP" {\n\t\tinventory := Str(b, "local_inventory_artifact_id")',
     '\tif false && decision != "REUSE_LOCAL" && decision != "CUSTOM_GAP" {\n\t\tinventory := Str(b, "local_inventory_artifact_id")',
     ["W0801-GUARD-CLONE-IS-NOT-RESEARCH"]),
    ("R1-M04", "empty required scalar (no licence evidence)", ADOPT,
     '\t\tif strings.TrimSpace(Str(b, k)) == "" {',
     '\t\tif strings.TrimSpace(Str(b, k)) == "" && false {',
     ["W0801-GUARD-NO-LICENCE-REFUSED"]),
    ("R1-M05", "CUSTOM_GAP must state the remaining gap", ADOPT,
     '\tif decision == "CUSTOM_GAP" && strings.TrimSpace(Str(b, "remaining_gap")) == "" {',
     '\tif decision == "CUSTOM_GAP" && strings.TrimSpace(Str(b, "remaining_gap")) == "" && false {',
     ["W0801-GUARD-CUSTOM-GAP-EMPTY-REFUSED"]),
    ("R1-M06", "decision must record rejected alternatives", ADOPT,
     '\tif decision != "CUSTOM_GAP" && len(StrList(b["rejected_alternatives"])) == 0 {',
     '\tif decision != "CUSTOM_GAP" && len(StrList(b["rejected_alternatives"])) == 0 && false {',
     ["W0801-GUARD-NO-REJECTED-ALTERNATIVES-REFUSED"]),
    ("R1-M07", "decision needs a research basis and an evidence artifact", ADOPT,
     '\tif len(research) == 0 || len(evidence) == 0 {',
     '\tif len(research) == 0 && false || len(evidence) == 0 && false {',
     ["W0801-GUARD-NO-RESEARCH-BASIS-REFUSED"]),
    ("R1-M08", "decision enum membership (out-of-enum decision kind)", ADOPT,
     '\tif !reuseDecisions[decision] {',
     '\tif !reuseDecisions[decision] && false {', []),
    ("R1-M09", "adoption_decision_ref entity_type leg", ADOPT,
     '\tif !ok || Str(ref, "entity_type") != "Artifact" || Str(ref, "id") == "" || Str(ref, "content_hash") == "" {',
     '\tif !ok || (Str(ref, "entity_type") != "Artifact" && false) || Str(ref, "id") == "" || Str(ref, "content_hash") == "" {',
     []),
    ("R1-M10", "input_revision must be a positive integer", ADOPT,
     '\tif n, isNum := b["input_revision"].(float64); !isNum || n < 1 {',
     '\tif n, isNum := b["input_revision"].(float64); !isNum || n < 1 && false {', []),

    # ---- ProjectStages: the shared init/Desktop projection ----
    ("R1-M11", "ABSENT kept distinct from NOT_STARTED in the turn", ADOPT,
     'out = append(out, StageProjectionTurn{Stage: stage, Status: "ABSENT",',
     'out = append(out, StageProjectionTurn{Stage: stage, Status: StageNotStarted,',
     ["W0801-PROJ-ABSENT-DISTINCT-NOTSTARTED"]),
    ("R1-M12", "COUNTER-EXAMPLE 3 no-skip gate: do not present a decision whose RESEARCH is not done", ADOPT,
     '\t\t\t\tif s := researchStatusName(byStage); s != StageCompleted && s != StagePartial {',
     '\t\t\t\tif s := researchStatusName(byStage); false && s != StageCompleted {',
     ["W0801-PROJ-NO-SKIP-WITHOUT-RESEARCH", "W0801-PROJ-NO-SKIP-WHEN-RESEARCH-ROW-ABSENT",
      "W0801-PRODUCT-PROJ-REFUSES-WITHOUT-RESEARCH-ROW"]),
    ("R1-M13", "ABSENT-vs-NOT_STARTED naming inside the refusal message", ADOPT,
     '\tif !present {\n\t\treturn "ABSENT"\n\t}',
     '\tif !present {\n\t\treturn StageNotStarted\n\t}',
     ["W0801-PROJ-NO-SKIP-WHEN-RESEARCH-ROW-ABSENT"]),
    ("R1-M14", "projection re-derives the guard rather than trusting the stored COMPLETED row", ADOPT,
     '\t\t\t\tif _, e := ValidateReuseDecision(decision); e != nil {',
     '\t\t\t\tif _, e := ValidateReuseDecision(decision); e != nil && false {',
     ["W0801-PROJ-COMPLETED-WITH-BAD-DECISION-REFUSED"]),
    ("R1-M15", "COMPLETED reuse stage with no decision behind it is refused", ADOPT,
     '\t\t\t\tif decision == nil {',
     '\t\t\t\tif decision == nil && false {',
     ["W0801-PROJ-COMPLETED-WITHOUT-DECISION-REFUSED"]),
    ("R1-M16", "an unfinished stage must name a reader action (NOT_STARTED yields empty)", ADOPT,
     '\tcase StageNotStarted:\n\t\tswitch stage {',
     '\tcase StageNotStarted:\n\t\tif true {\n\t\t\treturn ""\n\t\t}\n\t\tswitch stage {',
     ["W0801-PROJ-READER-ACTION-EVERY-INCOMPLETE"]),
    ("R1-M16b", "per-stage reader action wording (all NOT_STARTED collapse to the generic line)", ADOPT,
     '\tcase StageNotStarted:\n\t\tswitch stage {',
     '\tcase StageNotStarted:\n\t\tswitch stage { //lint:ignore',
     ["W0801-PROJ-READER-ACTION-EVERY-INCOMPLETE"]),
    ("R1-M17", "RESEARCH=FAILED refused by the no-skip gate (third named form)", ADOPT,
     '\t\t\t\tif s := researchStatusName(byStage); s != StageCompleted && s != StagePartial {',
     '\t\t\t\tif s := researchStatusName(byStage); s != StageCompleted && s != StagePartial && s != StageFailed {',
     []),

    # ---- ReuseJevGate: J01 judge-before-reusing ----
    ("R1-M18", "COUNTER-EXAMPLE 2 a score may not appear without jev_called", ADOPT,
     '\t\tif !called && isNum {',
     '\t\tif !called && isNum && false {',
     ["W0801-JEV-SCORE-WITHOUT-CALL-REFUSED"]),
    ("R1-M19", "missing_evidence re-derived rather than trusted", ADOPT,
     '\tif len(Arr(receipt, "missing_evidence")) > 0 {',
     '\tif len(Arr(receipt, "missing_evidence")) > 0 && false {',
     ["W0801-JEV-MISSING-EVIDENCE-REFUSED"]),
    ("R1-M20", "hard failure outranks score: deterministic_results re-derived", ADOPT,
     '\tfor _, v := range Arr(receipt, "deterministic_results") {\n\t\tcheck, ok := v.(map[string]any)',
     '\tfor _, v := range []any{} {\n\t\tcheck, ok := v.(map[string]any)',
     ["W0801-JEV-HARDFAIL-OVERRIDES-SCORE"]),
    ("R1-M21", "receipt must carry status/selected/signals", ADOPT,
     '\tfor _, k := range []string{"status", "selected", "signals"} {',
     '\tfor _, k := range []string{} {', []),
    ("R1-M22", "no qualified candidate: refuse when nothing produced a score", ADOPT,
     '\tif !found {\n\t\treturn 0, Fail(422, "GATE_FAILED", "no qualified candidate',
     '\tif !found && false {\n\t\treturn 0, Fail(422, "GATE_FAILED", "no qualified candidate',
     ["W0801-JEV-NO-QUALIFIED-SIGNAL-REFUSED"]),
    ("R1-M23", "receipt must be DECIDED", ADOPT,
     '\tif Str(receipt, "status") != "DECIDED" {',
     '\tif Str(receipt, "status") != "DECIDED" && false {',
     ["W0801-JEV-ABSTAIN-REFUSED"]),
    ("R1-M24", "a receipt that selected nothing has no candidate", ADOPT,
     '\tif strings.TrimSpace(Str(receipt, "selected")) == "" {',
     '\tif strings.TrimSpace(Str(receipt, "selected")) == "" && false {',
     ["W0801-JEV-NO-CANDIDATE-REFUSED"]),

    # ---- RecordReuseDecision: the durable write ----
    ("R1-M25", "measurement_mode must be FIXTURE or LIVE", ADOPT,
     '\tif mode != "FIXTURE" && mode != "LIVE" {',
     '\tif false && mode != "FIXTURE" {',
     ["W0801-RECORD-UNKNOWN-MODE-REFUSED"]),
    ("R1-M26", "payload bound to the project it is written for", ADOPT,
     '\tif Str(b, "project_id") != project {',
     '\tif false && Str(b, "project_id") != project {',
     ["W0801-RECORD-PROJECT-MISMATCH-REFUSED"]),
    ("R1-M27", "every cited artifact must exist and be visible", ADOPT,
     '\tfor _, id := range cited {\n\t\to, e := s.readObject(tx, p, project, "Artifact", id)',
     '\tfor _, id := range cited[:0] {\n\t\to, e := s.readObject(tx, p, project, "Artifact", id)',
     ["W0801-RECORD-ABSENT-ARTIFACT-CREATES-NOTHING", "W0801-RECORD-ABSENT-ARTIFACT-REFUSED"]),
    ("R1-M28", "adoption_decision_ref effectiveness check (s.effective)", ADOPT,
     '\tif e := s.effective(tx, project, ref); e != nil {',
     '\tif e := s.effective(tx, project, ref); e != nil && false {', []),
    ("R1-M29", "promotion writes only its own stage row", ADOPT,
     '\tif e := s.putOpaque(ctx, tx, project, KindBootstrapStage, id, stage); e != nil {\n\t\treturn nil, e\n\t}',
     '\tif e := s.putOpaque(ctx, tx, project, KindBootstrapStage, id, stage); e != nil {\n\t\treturn nil, e\n\t}\n\trid := "stage-" + project + "-" + strings.ToLower(StageResearch)\n\trrow := Object{"id": rid, "project_id": project, "stage": StageResearch,\n\t\t"status": StageCompleted, "file_failures": Empty(), "observed_at": Now(), "revision": rev}\n\tif e := s.putOpaque(ctx, tx, project, KindBootstrapStage, rid, rrow); e != nil {\n\t\treturn nil, e\n\t}',
     ["W0801-RECORD-DOES-NOT-PROMOTE-RESEARCH"]),
    ("R1-M30", "the write must actually commit", ADOPT,
     '\treturn out, tx.Commit()',
     '\t_ = tx.Commit()\n\treturn out, nil',
     ["W0801-RECORD-STAGE-ROW-WRITTEN"]),

    # ---- routing guard in the check program ----
    ("R1-M31", "routing guard: refuse a binding this handler does not own", CHECK,
     '\tif tid != "W08" || cid != "W08-01" {\n\t\treport("FAIL")\n\t\treturn\n\t}',
     '\tif false && (tid != "W08" || cid != "W08-01") {\n\t\treport("FAIL")\n\t\treturn\n\t}',
     [PROBE]),
    ("R1-M32", "probe depth cap alone removed, routing guard still in place", CHECK,
     '\t} else if os.Getenv("W0801_PROBE_CHILD") == "1" {',
     '\t} else if false && os.Getenv("W0801_PROBE_CHILD") == "1" {',
     [PROBE]),
    ("R1-M33", "reachability probe: rename the depth-cap branch label", CHECK,
     '\t\tok("W0801-ROUTING-SELF-PROBE-REFUSES-FOREIGN-BINDING", false, "probe nesting stopped at depth 1")',
     '\t\tok("W0801-ROUTING-DEPTH-CAP-BRANCH-REACHED", false, "probe nesting stopped at depth 1")',
     ["W0801-ROUTING-DEPTH-CAP-BRANCH-REACHED"]),
]

# Designed, and deliberately NOT executed.
NOT_RUN = [{
    "id": "R1-M34",
    "mutant": "R1-M31 + R1-M32 together: routing guard AND probe depth cap removed",
    "why_not_run": "With both gone the child neither refuses at the binding check nor stops at the "
                   "mark, so every nesting level execs one more copy: tests/research/check/main.go:302 "
                   "exec.CommandContext(self) has no gate other than the mark at :297. The executor "
                   "measured several hundred live processes from exactly this configuration. Running it "
                   "again would load this host and add no information, because R1-M31 already shows the "
                   "probe assertion measures the guard, and R1-M32/R1-M33 show the cap only fires once "
                   "the guard is gone.",
    "substitute_evidence": "R1-M31 (guard removed, cap retained) run under a live process sampler; "
                           "R1-M33 showing the cap branch is never reached in a clean build.",
}]


def sha(path):
    return hashlib.sha256(open(os.path.join(REPO, path), "rb").read()).hexdigest()


def child_procs():
    try:
        out = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True,
                             timeout=25).stdout
    except Exception:
        return -1
    n = 0
    for line in out.splitlines():
        low = line.lower()
        if low.startswith('"check.exe') or low.startswith('"research.check'):
            n += 1
    return n


def run(label):
    t = time.time()
    try:
        p = subprocess.run([GO, "run", "./tests/research/check"], capture_output=True, cwd=REPO,
                           env=ENV, timeout=900)
    except subprocess.TimeoutExpired:
        return {"label": label, "status": "TIMEOUT", "rc": None, "ids": [], "failures": [],
                "n_ids": 0, "seconds": round(time.time() - t, 2)}
    rec = {"label": label, "rc": p.returncode, "seconds": round(time.time() - t, 2),
           "procs_sample": child_procs()}
    out = p.stdout.strip()
    if not out:
        rec.update(status="NO-REPORT", stderr_tail=p.stderr.decode("utf-8", "replace")[-2000:])
        return rec
    try:
        rep = json.loads(out.decode("utf-8"))
    except Exception as e:
        rec.update(status="UNPARSABLE", detail=str(e), stderr_tail=p.stderr.decode("utf-8", "replace")[-2000:],
                   stdout_head=out[:800].decode("utf-8", "replace"))
        return rec
    rec.update(status=rep.get("status"), ids=sorted(rep.get("assertion_ids") or []),
               failures=[f.get("id") for f in (rep.get("failures") or [])],
               n_ids=len(rep.get("assertion_ids") or []))
    return rec


def apply(path, old, new):
    p = os.path.join(REPO, path)
    b = open(p, "rb").read().decode("utf-8")
    c = b.count(old)
    if c != 1:
        raise RuntimeError("anchor count %d for %r in %s" % (c, old[:70], path))
    open(p, "wb").write(b.replace(old, new).encode("utf-8"))


def restore(path, original):
    open(os.path.join(REPO, path), "wb").write(original)
    return sha(path) == DIGESTS[path]


def main():
    clean_roster = json.loads(open(os.path.join(REPO, EVDIR, "dispatch_run1.stdout"),
                                   encoding="utf-8").read())
    assert clean_roster["assertions"] == 64
    orig = {f: open(os.path.join(REPO, f), "rb").read() for f in (ADOPT, CHECK)}
    for f, d in DIGESTS.items():
        assert sha(f) == d, "baseline digest moved for " + f
    print("== baseline digests confirmed; clean stdout sha", CLEAN_SHA[:16], flush=True)

    results = []
    prev_clean = None
    for mid, desc, path, old, new, anchors in M:
        entry = {"id": mid, "guard": desc, "file": path, "must_red_anchors": anchors}
        if prev_clean is not None:
            cb = dict(prev_clean)
            cb["reused_from"] = "clean-after of the previous mutant (digest re-verified since)"
            entry["clean_before"] = cb
        else:
            cb = run(mid + "/clean-before")
            entry["clean_before"] = {k: cb.get(k) for k in ("status", "n_ids", "rc", "seconds", "procs_sample")}
        if cb.get("status") != "PASS" or cb.get("n_ids") != 64:
            entry["classification"] = "BASELINE-RED"
            results.append(entry)
            print(mid, "BASELINE-RED", entry["clean_before"], flush=True)
            prev_clean = None
            continue
        try:
            apply(path, old, new)
            entry["mutation_applied"] = True
        except Exception as e:
            entry["mutation_applied"] = False
            entry["detail"] = str(e)
            entry["classification"] = "MUTANT-NOT-APPLIED"
            results.append(entry)
            print(mid, "NOT-APPLIED", e, flush=True)
            restore(path, orig[path])
            prev_clean = None
            continue
        mut = run(mid + "/mutated")
        rest_ok = restore(path, orig[path])
        ca = run(mid + "/clean-after")
        entry["mutated"] = {k: mut.get(k) for k in ("status", "n_ids", "rc", "seconds", "procs_sample")}
        entry["mutated_failures"] = mut.get("failures")
        entry["mutated_stderr_tail"] = mut.get("stderr_tail")
        entry["mutated_stdout_head"] = mut.get("stdout_head")
        entry["restored_digest_ok"] = rest_ok
        entry["clean_after"] = {k: ca.get(k) for k in ("status", "n_ids", "rc", "seconds", "procs_sample")}
        ids_now, fails_now = set(mut.get("ids") or []), set(mut.get("failures") or [])
        per = []
        for a in anchors:
            if a in fails_now:
                per.append({"anchor": a, "state": "red"})
            elif a in ids_now:
                per.append({"anchor": a, "state": "still-green"})
            else:
                per.append({"anchor": a, "state": "anchor-missing"})
        entry["per_anchor"] = per
        known = set(json.loads(open(os.path.join(REPO, EVDIR, "clean_roster_ids.json"),
                                    encoding="utf-8").read()))
        entry["collateral_reds"] = sorted(x for x in fails_now if x and x not in anchors and x in known)
        entry["new_failure_ids_not_in_clean_roster"] = sorted(x for x in fails_now if x and x not in known)
        entry["ids_lost_vs_clean"] = sorted(set(entry["clean_roster_ref"] or []) - ids_now) \
            if False else sorted(known - ids_now)
        if not rest_ok:
            entry["classification"] = "RESTORE-FAILED"
        elif mut.get("status") in ("NO-REPORT", "UNPARSABLE", "TIMEOUT"):
            entry["classification"] = "crashed"
        elif not anchors:
            entry["classification"] = "collateral-caught" if fails_now else "unguarded (no assertion names this guard)"
        elif any(p["state"] == "red" for p in per):
            entry["classification"] = "caught"
        elif any(p["state"] == "still-green" for p in per):
            entry["classification"] = "survived"
        else:
            entry["classification"] = "anchor-missing"
        results.append(entry)
        print("%-8s %-46s clean=%s/%s mut=%s/%s red=%d restore=%s after=%s/%s procs=%s" % (
            mid, entry["classification"], cb.get("status"), cb.get("n_ids"), mut.get("status"),
            mut.get("n_ids"), len(fails_now), rest_ok, ca.get("status"), ca.get("n_ids"),
            entry["mutated"].get("procs_sample")), flush=True)
        for f in (ADOPT, CHECK):
            assert sha(f) == DIGESTS[f], "digest moved mid-matrix for " + f
        prev_clean = ca if ca.get("status") == "PASS" and ca.get("n_ids") == 64 else None

    tally = {}
    for r in results:
        tally[r["classification"]] = tally.get(r["classification"], 0) + 1
    out = {"reviewer_id": "qoder-desktop:/root/w0801_verifier_r1",
           "matrix": "reviewer round-1 independent mutation matrix (built from the delivered bytes, "
                     "not from the executor's script)",
           "oracle": "go run ./tests/research/check with RESEARCHOS_TASK_ID=W08 RESEARCHOS_CHECK_ID=W08-01",
           "oracle_equivalence": "stdout bytes identical to the dispatcher's frozen stdout.txt, sha256 " + CLEAN_SHA,
           "clean_roster_count": 64,
           "tally": tally,
           "not_run_by_design": NOT_RUN,
           "results": results}
    with open(os.path.join(REPO, EVDIR, "mutation_matrix_reviewer_r1.json"), "wb") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"))
    print("TALLY", json.dumps(tally, indent=1), flush=True)
    for f in (ADOPT, CHECK):
        print("final digest", f, sha(f), sha(f) == DIGESTS[f])


if __name__ == "__main__":
    main()
