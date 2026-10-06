"""Independent reviewer's per-leg mutation matrix for W09-02 (round 1).

Written from scratch by qoder-desktop:/root/w0902_verifier_r1; none of the executor's mutants
are reused. Targets are the legs the receipt left open:

  V01-V03  readFile's three lexical operands, one operand at a time (text removal, not `false`).
  V04      classifyOpen's INTERMEDIATE-component Lstat-failure branch (never paired with a row).
  V05      classifyOpen's ModeSymlink branch replaced by the irregular-mode message.
  V06      classifyOpen's irregular-mode condition flipped whole (`&& false` form) - the shape
           the executor's guard claims to refuse but only refuses for anchors with >=2 operators.
  V07      source_kind dropped from the projection record (removes the field, not its value).
  V08      BOTH toolchain legs blinded at once - the pair the executor disclosed as unrun.
  V09      route() ignores task_id (a narrower flip than their M08; tests the truth table's power).
  V10a     CLASS_ROWS declares a witness the roster does not emit (input change, expect caught).
  V10b     same bad input WITH the absence operand dropped (expect survived -> says which leg kills it).

Every row: sha256 before -> apply -> run -> bucket -> restore -> sha256 after must equal before.
buckets are crashed / anchor-missing / survived / caught / red-elsewhere, never rounded up.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
HANDLER = "tests/evidence/check/revoke_cache.py"
LOCAL = "adapters/retrieval/local.go"
ORIGIN = "internal/domain/evidence_origin.go"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", GOTOOLCHAIN="local", RESEARCHOS_GO=GO,
           GOPATH=os.path.join(ROOT, ".local", "gopath"),
           GOCACHE=os.path.join(ROOT, ".local", "gocache"))

MUTANTS = [
    ("V01-empty-name-operand-removed", LOCAL,
     '\tif relative == "" || relative == "." || !filepath.IsLocal(relative) {',
     '\tif relative == "." || !filepath.IsLocal(relative) {',
     "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",
     "one operand of a three-operand disjunction removed by text surgery"),
    ("V02-dot-operand-removed", LOCAL,
     '\tif relative == "" || relative == "." || !filepath.IsLocal(relative) {',
     '\tif relative == "" || !filepath.IsLocal(relative) {',
     "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",
     "the dot operand removed; IsLocal('.') is itself false, so masking is the expected outcome"),
    ("V03-islocal-operand-removed", LOCAL,
     '\tif relative == "" || relative == "." || !filepath.IsLocal(relative) {',
     '\tif relative == "" || relative == "." {',
     "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",
     "the containment operand removed entirely: does anything downstream still refuse the escape?"),
    ("V04-intermediate-lstat-branch-generic", LOCAL,
     'return fmt.Errorf("path component %q could not be inspected inside the registered root: %w", prefix, openErr)',
     'return fmt.Errorf("registered root refused the path: %w", openErr)',
     "W0902-ADAPTER-NAMES-AN-ABSENT-FILE-AS-ABSENCE",
     "the intermediate-component inspection branch is replaced by the generic branch; no row names it"),
    ("V05-symlink-branch-becomes-irregular", LOCAL,
     'return fmt.Errorf("path component %q is a symbolic link to %q; snapshots must be a regular file inside the registered root", prefix, target)',
     'return fmt.Errorf("path component %q is a link or reparse point with irregular mode %s; snapshots must be a regular file inside the registered root", prefix, info.Mode())',
     "W0902-ADAPTER-NAMES-A-JUNCTION-ESCAPE-AS-A-LINK",
     "the ModeSymlink return is made to say the irregular-mode message; the test accepts either wording"),
    ("V06-irregular-condition-whole-flip", LOCAL,
     "\t\tif !info.Mode().IsRegular() && !info.Mode().IsDir() {",
     "\t\tif false {",
     "W0902-ADAPTER-NAMES-A-JUNCTION-ESCAPE-AS-A-LINK",
     "compound flipped whole (two operands at once) - the shape the guard says it refuses"),
    ("V07-source-kind-field-removed", ORIGIN,
     '"evidence_id": id, "evidence_kind": kind, "source_kind": ev["source_kind"], "origin_relation": relation,',
     '"evidence_id": id, "evidence_kind": kind, "origin_relation": relation,',
     "W0902-SHARED-PROJECTION-CARRIES-EVIDENCE-AND-SOURCE-KIND",
     "the field is deleted from the shared record rather than blanked"),
    ("V08a-digest-leg-blinded-alone", HANDLER,
     '        if digest != tools.get("sha256"):',
     '        if False:',
     "W0902-TOOLCHAIN-REFUSES-A-REAL-BUT-WRONG-BINARY",
     "re-run of the executor's M09 shape as my own anchor, so my pair starts from a measured single"),
    ("V08-both-legs-pair", HANDLER, None, None,
     "W0902-TOOLCHAIN-REFUSES-A-REAL-BUT-WRONG-BINARY",
     "both legs blinded in one run: digest leg -> False and version leg -> False"),
    ("V09-route-ignores-task-id", HANDLER,
     '    return "serve" if (task, check, case) == (OWNED_TASK, OWNED_CHECK, "") else "refuse"',
     '    return "serve" if check == OWNED_CHECK else "refuse"',
     "W0902-ROUTING-TRUTH-TABLE",
     "a narrower inversion than M08: the binding's task_id is ignored. Does the declared truth table see it?"),
    ("V10a-class-declares-unemitted-witness", HANDLER,
     '    "path_escape": ["W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",',
     '    "path_escape": ["W0902-REVIEWER-INVENTED-ROW-DOES-NOT-EXIST", "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",',
     "W0902-EVERY-NEGATIVE-CLASS-HAS-ITS-OWN-WITNESS",
     "input change: the class table names a witness the roster never emits; expect the row to go red"),
    ("V10b-bad-class-with-absence-blind", HANDLER, None, None,
     "W0902-EVERY-NEGATIVE-CLASS-HAS-ITS-OWN-WITNESS",
     "V10a plus the absence operand dropped: if this survives, the row's only killer was that operand"),
]

# two-operand mutations applied together
COMBOS = {
    "V08-both-legs-pair": [("        if digest != tools.get(\"sha256\"):", "        if False:"),
                           ('        if version.returncode != 0 or (version.stdout or "").strip() != tools.get("version_output"):',
                            "        if False:")],
    "V10b-bad-class-with-absence-blind": [
        ('    "path_escape": ["W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",',
         '    "path_escape": ["W0902-REVIEWER-INVENTED-ROW-DOES-NOT-EXIST", "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",'),
        ("       not any(absent_classes.values()) and all(len(rows) >= 2 for rows in CLASS_ROWS.values()),",
         "       all(len(rows) >= 2 for rows in CLASS_ROWS.values()),")],
}

OPERAND = re.compile(r"&&|\|\|")


def operand_count(text):
    stripped = re.sub(r'"(?:[^"\\]|\\.)*"', "S", text or "")
    stripped = re.sub(r"'(?:[^'\\]|\\.)*'", "S", stripped)
    return len(OPERAND.findall(stripped))


def constant_over_disjunction(anchor, replacement):
    """The executor's guard, verbatim, so I can report what it would have refused."""
    if "&& false" in (replacement or "") or "|| true" in (replacement or ""):
        return operand_count(anchor) > 1 and operand_count(replacement) < operand_count(anchor) - 1
    return False


def digest(path):
    return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()


def run_handler():
    completed = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, HANDLER)],
                               cwd=ROOT, env=dict(ENV, RESEARCHOS_TASK_ID="W09", RESEARCHOS_CHECK_ID="W09-02"),
                               capture_output=True, timeout=900)
    line = (completed.stdout or b"").decode("utf-8", errors="replace").strip().splitlines()
    report = json.loads(line[-1]) if line else {}
    return completed.returncode, report, len(line)


def apply(path, pairs):
    full = os.path.join(ROOT, path)
    text = open(full, encoding="utf-8").read()
    for anchor, replacement in pairs:
        if text.count(anchor) != 1:
            return "anchor-missing", "anchor occurs %d times" % text.count(anchor)
        text = text.replace(anchor, replacement, 1)
    open(full, "w", encoding="utf-8", newline="").write(text)
    return "applied", None


def main():
    code0, base0, _ = run_handler()
    baseline = {"rc": code0, "status": base0.get("status"), "assertions": base0.get("assertions")}
    print("clean baseline", json.dumps(baseline))
    rows = []
    for name, path, anchor, replacement, target, note in MUTANTS:
        row = {"name": name, "file": path, "named_assertion": target, "note": note}
        before = digest(path)
        original = open(os.path.join(ROOT, path), encoding="utf-8").read()
        pairs = COMBOS.get(name) or ([(anchor, replacement)] if anchor else [])
        row["would_the_executors_guard_refuse"] = bool(anchor and constant_over_disjunction(anchor, replacement))
        row["guard_operand_counts"] = [operand_count(anchor), operand_count(replacement)] if anchor else None
        state, detail = apply(path, pairs)
        if state != "applied":
            rows.append(dict(row, bucket=state, detail=detail, restored=digest(path) == before))
            print("%-42s %-14s" % (name, state))
            continue
        try:
            code, report, lines = run_handler()
            ids = report.get("assertion_ids") or []
            failed = [f.get("id") for f in (report.get("failures") or [])]
            row["failed_ids"] = failed[:8]
            row["assertions_emitted"] = len(ids)
            row["report_status"] = report.get("status")
            row["stdout_lines"] = lines
            if report.get("status") == "PASS" and code == 0:
                bucket = "survived"
            elif code != 0 and target in failed:
                bucket = "caught"
            elif code != 0 and not ids and not failed:
                bucket = "crashed"
            else:
                bucket = "red-elsewhere"
        except subprocess.TimeoutExpired:
            bucket, row["detail"] = "crashed", "mutated run timed out"
        finally:
            open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="").write(original)
            row["digest_after_restore_matches"] = digest(path) == before
        row["bucket"] = bucket
        rows.append(row)
        print("%-42s %-14s restore=%s failed=%s" % (name, bucket, row["digest_after_restore_matches"],
                                                    row.get("failed_ids")))
    out = {"clean_baseline": baseline, "rows": rows,
           "buckets": {},
           "tree_clean_after_run": subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                                  cwd=ROOT, capture_output=True, text=True).stdout.strip() == ""}
    for r in rows:
        out["buckets"][r["bucket"]] = out["buckets"].get(r["bucket"], 0) + 1
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mutation_review_round1.json")
    open(dest, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({"buckets": out["buckets"], "tree_clean": out["tree_clean_after_run"]}))
    print("wrote", dest)


if __name__ == "__main__":
    sys.exit(main())
