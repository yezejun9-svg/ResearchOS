"""Mutation self-check for W08-01.

Each mutant removes one decision from internal/domain/adoption.go (or the routing guard in the check program) and the
matrix records which named assertion the red run actually reported. A mutant is only 'caught' when the failure list
contains the assertion id that the mutant was built to break; anything else is reported as survived, crashed or
anchor-missing rather than rounded up. Files are restored from byte copies and verified by digest after every run.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ADOPTION = "internal/domain/adoption.go"
CHECK = "tests/research/check/main.go"
EXE = os.path.abspath(".local/_w0801_mutant.exe")
GO = r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe"
ENV = dict(os.environ, GOTOOLCHAIN="local",
           GOPATH=r"D:\作品集\ResearchOS\research-os\.local\gopath",
           GOCACHE=r"D:\作品集\ResearchOS\research-os\.local\gocache",
           RESEARCHOS_TASK_ID="W08", RESEARCHOS_CHECK_ID="W08-01", PYTHONUTF8="1")

MUTANTS = [
    ("M01-clone-as-research-allowed", ADOPTION,
     "\tif decision != \"REUSE_LOCAL\" && decision != \"CUSTOM_GAP\" {", "\tif false {",
     "W0801-GUARD-CLONE-IS-NOT-RESEARCH"),
    ("M02-empty-gap-passes", ADOPTION,
     "\tif decision == \"CUSTOM_GAP\" && strings.TrimSpace(Str(b, \"remaining_gap\")) == \"\" {", "\tif false {",
     "W0801-GUARD-CUSTOM-GAP-EMPTY-REFUSED"),
    ("M03-no-rejected-alternatives-passes", ADOPTION,
     "\tif decision != \"CUSTOM_GAP\" && len(StrList(b[\"rejected_alternatives\"])) == 0 {", "\tif false {",
     "W0801-GUARD-NO-REJECTED-ALTERNATIVES-REFUSED"),
    ("M04-undeclared-field-ignored", ADOPTION,
     "\t\tknown := false", "\t\tknown := true",
     "W0801-GUARD-UNDECLARED-FIELD-REFUSED"),
    ("M05-missing-field-not-refused", ADOPTION,
     "\t\tif _, ok := b[k]; !ok {\n\t\t\treturn \"\", Fail(400, \"INVALID_REQUEST\", \"reuse decision is missing \"+k)",
     "\t\tif false {\n\t\t\treturn \"\", Fail(400, \"INVALID_REQUEST\", \"reuse decision is missing \"+k)",
     "W0801-GUARD-MISSING-PROJECT_ID"),
    ("M06-absent-reported-as-notstarted", ADOPTION,
     "out = append(out, StageProjectionTurn{Stage: stage, Status: \"ABSENT\",",
     "out = append(out, StageProjectionTurn{Stage: stage, Status: StageNotStarted,",
     "W0801-PROJ-ABSENT-DISTINCT-NOTSTARTED"),
    ("M07-completed-row-self-justifying", ADOPTION,
     "\t\t\t\tif decision == nil {\n\t\t\t\t\treturn nil, Fail(422, \"GATE_FAILED\", \"REUSE_DECISION is recorded completed with no decision to show\")",
     "\t\t\t\tif false {\n\t\t\t\t\treturn nil, Fail(422, \"GATE_FAILED\", \"REUSE_DECISION is recorded completed with no decision to show\")",
     "W0801-PROJ-COMPLETED-WITHOUT-DECISION-REFUSED"),
    ("M08-score-without-jev-call-accepted", ADOPTION,
     "\t\tif !called && isNum {", "\t\tif false {", "W0801-JEV-SCORE-WITHOUT-CALL-REFUSED"),
    ("M09-hardfail-overridden-by-score", ADOPTION,
     "\t\tif check[\"status\"] != \"PASS\" && check[\"status\"] != \"NOT_APPLICABLE\" {", "\t\tif false {",
     "W0801-JEV-HARDFAIL-OVERRIDES-SCORE"),
    ("M10-missing-evidence-ignored", ADOPTION,
     "\tif len(Arr(receipt, \"missing_evidence\")) > 0 {", "\tif false {",
     "W0801-JEV-MISSING-EVIDENCE-REFUSED"),
    ("M11-unqualified-signal-scored", ADOPTION,
     "\tif !found {\n\t\treturn 0, Fail(422, \"GATE_FAILED\", \"no qualified candidate: the receipt carries no score produced by a Jev call\")",
     "\tif false {\n\t\treturn 0, Fail(422, \"GATE_FAILED\", \"no qualified candidate: the receipt carries no score produced by a Jev call\")",
     "W0801-JEV-NO-QUALIFIED-SIGNAL-REFUSED"),
    ("M12-cited-artifact-existence-unread", ADOPTION,
     "\t\to, e := s.readObject(tx, p, project, \"Artifact\", id)\n\t\tif e != nil {\n\t\t\treturn nil, e\n\t\t}",
     "\t\to, e := s.readObject(tx, p, project, \"Artifact\", id)\n\t\tif e != nil {\n\t\t\to, e = Object{\"id\": id}, error(nil)\n\t\t}",
     "W0801-RECORD-ABSENT-ARTIFACT-REFUSED"),
    ("M13-project-binding-unchecked", ADOPTION,
     "\tif Str(b, \"project_id\") != project {", "\tif false {", "W0801-RECORD-PROJECT-MISMATCH-REFUSED"),
    ("M14-mode-unvalidated", ADOPTION,
     "\tif mode != \"FIXTURE\" && mode != \"LIVE\" {", "\tif false {", "W0801-RECORD-UNKNOWN-MODE-REFUSED"),
    ("M15-routing-guard-removed", CHECK,
     "\tif tid != \"W08\" || cid != \"W08-01\" {", "\tif false {",
     "W0801-ROUTING-SELF-PROBE-REFUSES-FOREIGN-BINDING"),
    ("M16-research-row-never-required", ADOPTION,
     "if s := researchStatusName(byStage); s != StageCompleted && s != StagePartial {",
     "if s := researchStatusName(byStage); s == \"\" {",
     "W0801-PROJ-NO-SKIP-WITHOUT-RESEARCH"),
    ("M17-absent-and-notstarted-collapsed", ADOPTION,
     "return \"ABSENT\"", "return StageNotStarted",
     "W0801-PROJ-NO-SKIP-WHEN-RESEARCH-ROW-ABSENT"),
]


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_check():
    build = subprocess.run([GO, "build", "-o", EXE, "./tests/research/check"], capture_output=True, text=True,
                           env=ENV, timeout=900, encoding="utf-8", errors="replace")
    if build.returncode != 0:
        return "crashed", [], build.stderr.strip()[-300:]
    proc = subprocess.run([EXE], capture_output=True, text=True, env=ENV, timeout=900, cwd=os.getcwd(),
                          encoding="utf-8", errors="replace")
    try:
        report = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return "crashed", [], (proc.stderr or proc.stdout)[-300:]
    failed = [f["id"] for f in (report.get("failures") or [])]
    return ("survived" if not failed else "caught"), failed, ""


def main():
    originals = {p: (open(p, "rb").read(), digest(p)) for p in {m[1] for m in MUTANTS}}
    rows = []
    for name, path, old, new, expect in MUTANTS:
        row = {"mutant": name, "file": path, "expected_assertion": expect}
        text = originals[path][0].decode("utf-8")
        count = text.count(old)
        if count != 1:
            row["classification"] = "anchor-missing"
            row["anchor_occurrences"] = count
            rows.append(row)
            continue
        open(path, "w", encoding="utf-8", newline="").write(text.replace(old, new, 1))
        try:
            classification, failed, note = run_check()
            row["assertions_that_went_red"] = failed
            row["expected_in_red"] = expect in failed
            if classification == "crashed":
                row["classification"] = "crashed"
                row["note"] = note
            elif row["expected_in_red"]:
                row["classification"] = "caught"
            else:
                row["classification"] = "survived"
        finally:
            open(path, "wb").write(originals[path][0])
            if digest(path) != originals[path][1]:
                row["restore_verified"] = False
                rows.append(row)
                json.dump({"rows": rows, "aborted": "restore failed for " + path},
                          open(".local/mutation_selfcheck_round1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                raise SystemExit("RESTORE FAILED for %s" % path)
            row["restore_verified"] = True
        rows.append(row)
        print("%-42s %-12s red=%d expected=%s" % (name, row["classification"], len(row.get("assertions_that_went_red", [])),
                                                 row.get("expected_in_red")))

    summary = {}
    for r in rows:
        summary[r["classification"]] = summary.get(r["classification"], 0) + 1
    for path, (blob, _) in originals.items():
        assert digest(path) == hashlib.sha256(blob).hexdigest(), "tree not clean after mutations"
    # The artifact is written before any cleanup, and cleanup is tolerant: a locked scratch binary must never be able
    # to cost the measurement its record.
    json.dump({"total": len(MUTANTS), "summary": summary, "rows": rows},
              open(".local/mutation_selfcheck_round1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if os.path.exists(EXE):
        try:
            os.remove(EXE)
        except OSError as exc:
            print("note: scratch binary left in place (%s) - %s" % (exc.__class__.__name__, EXE))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
