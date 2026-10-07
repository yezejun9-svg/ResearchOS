"""Correct the addendum's attribution and write a per-row disposition for every uncovered row.

Two honesty rules applied here:
 - a crashed mutant discriminates nothing individually - it only shows the suite fails loudly - so rows
   lost while the driver was dead are not credited to that mutant;
 - every uncovered row gets exactly one disposition, and "owed" is written as owed rather than left blank.
"""
import datetime, io, json, os, re, subprocess

ROOT = os.getcwd()
RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
ADJ = os.path.join(RD, "mutation_addendum_w1301.json")
V3 = os.path.join(RD, "independent_review_round3.json")
notes = os.path.join(RD, "MUTATION_ADDENDUM_NOTES.md")

adj = json.load(io.open(ADJ, encoding="utf-8-sig"))
for m in adj["mutants"]:
    if m.get("bucket") == "crashed":
        m["credits_no_rows"] = sorted(m.get("rows_newly_discriminated") or [])
        m["rows_newly_discriminated"] = []
        m["interpretation"] = ("the driver died, so the suite noticed something was wrong but no individual "
                               "row is shown to be sensitive to this mutant")
cleanly = sorted({r for m in adj["mutants"] for r in (m.get("rows_newly_discriminated") or [])})
adj["rows_newly_discriminated"] = cleanly
adj["attribution_rule"] = ("only rows lost while W1301-DRIVER-RAN survived are credited to a mutant; a crash "
                           "is reported as a crash")

v3 = json.load(io.open(V3, encoding="utf-8-sig"))
reviewer_text = json.dumps(v3, ensure_ascii=False)
staged = ".local/prepare_w1301_mutants_round3.py"
staged_ids = sorted(set(re.findall(r"\b(M2[4-9]|M30|M31)\b", io.open(staged, encoding="utf-8").read()))) if os.path.isfile(staged) else []

DISPOSITION = {
    "W1301-DRIVER-RAN": "meta row, not a source behaviour: its negation is 'node declined to launch', measured by forcing resolve_node to return no binary, which produced FAIL with 26 named failures rather than a silent pass (reviewer round 3, what_i_ran item 10)",
    "W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE": "covered by measurement rather than a filed mutant: nine hostile tool tables were passed to resolve_node and only the good one returned an executable (reviewer round 3, what_i_ran item 9); folding that as a mutant into the pinned matrix is owed",
    "W1301-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED": "OWED, and weakly discriminating by design: the row tests a hard-coded bogus table, so it would still pass if a PATH fallback were reintroduced at the subprocess call (reviewer round 3, reservation 7)",
    "W1301-LAUNCH-USES-THE-LOCAL-CONTROL-HOST": "killed by staged mutant M29 in .local/prepare_w1301_mutants_round3.py as measured by the round-3 reviewer; not folded into the shipped matrix because mutation_selfcheck_w1301.json is pinned by an accepted receipt",
    "W1301-ABSENT-DISCOVERY-IS-NAMED": "killed by staged mutant M27 (reviewer measurement); shipping it into the accepted matrix is owed as a new artifact",
    "W1301-ABSENT-PRINCIPAL-STORE-IS-NAMED": "killed by staged mutant M28 (reviewer measurement)",
    "W1301-PRINCIPAL-READ-LOCAL-NOT-PASTED": "killed by staged mutant M28 (reviewer measurement)",
    "W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES": "partly covered: the reviewer's one-line branch mutants killed the AUTH_REQUIRED, RATE_LIMITED and UNSUPPORTED branches; the catch-all branch survives, reproduced again here as A6",
    "W1301-TRANSPORT-AND-SILENCE-ARE-FAILURES": "covered by the reviewer's NO_REPLY and TRANSPORT branch mutants; not folded into the pinned matrix",
    "W1301-PROVIDER-OK-IS-SUCCESS": "OWED: this is the card's own second negative and the catch-all branch is undiscriminated - mutant A6 (provider catch-all returning ok:true) SURVIVED again in this addendum",
    "W1301-UNKNOWN-CLIENT-AND-METHOD-REFUSED": "attempted by addendum mutant A5, which crashed the driver instead of isolating the row; a narrower mutant is still owed",
    "W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE": "OWED: addendum anchors for this behaviour did not exist in the files searched (A1-A4 reported anchor-missing), so no mutant was applied",
    "W1301-UNREACHABLE-CORE-IS-REPORTED-NOT-FAKED": "OWED, same reason: only reached through the crashed run, which credits nothing",
    "W1301-PRELOAD-MATCHES-REGISTERED-CHANNELS": "OWED: mutant A1 could not be applied because the expected channel line is not in preload.js as searched",
    "W1301-FIRST-RUN-METHODS-ALL-ROUTED": "OWED: mutant A2 anchor-missing in ipc.js as searched",
    "W1301-FOUR-NATIVE-CLIENTS-ROUTED": "OWED: mutant A3 anchor-missing in ipc.js as searched",
    "W1301-WORKBENCH-COVERS-FOUR-CLIENTS": "OWED: mutant A4 anchor-missing in workbench.html as searched",
    "W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL": "OWED: mutant A4 anchor-missing in workbench.html as searched",
    "W1301-ROUTING-TRUTH-TABLE": "OWED: the table is asserted as data inside the check program, and no mutant yet rewrites the routing it tabulates",
}
uncovered = adj["computed_from"]
rows = adj.get("rows_still_without_a_mutant") or []
allrows = sorted(set(rows) | set(cleanly) | {"W1301-UNKNOWN-CLIENT-AND-METHOD-REFUSED"})
unaccounted = [r for r in allrows if r not in DISPOSITION]
if unaccounted:
    for r in unaccounted:
        DISPOSITION[r] = "UNCLASSIFIED - flagged so the list cannot silently be shorter than the computed set"
adj["per_row_disposition"] = DISPOSITION
adj["disposition_counts"] = {
    "measured_via_reviewer_or_staged": len([k for k, v in DISPOSITION.items() if v.startswith(("killed", "covered", "partly", "meta", "attempted"))]),
    "owed": len([k for k, v in DISPOSITION.items() if v.startswith("OWED")]),
    "unclassified": len([k for k, v in DISPOSITION.items() if v.startswith("UNCLASSIFIED")]),
}
adj["staged_mutant_ids_present"] = staged_ids
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(ADJ, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)

md = ["# W13-01 mutation addendum - what each uncovered row is now",
      "",
      "The shipped matrix and its 14 pinned artifacts are unchanged; everything here is a new file.",
      "",
      "- assertion ids emitted by the accepted check program: **%d**" % uncovered["emitted_assertions"],
      "- rows the shipped matrix's 10 cases actually kill: **%d**" % uncovered["killed_by_shipped_matrix"],
      "- rows therefore without a discriminating mutant: **%d**" % uncovered["rows_without_a_mutant_before_this_addendum"],
      "- the shipped artifact's own `no_mutant_rows` field claims: **%d**, and the round-3 reviewer "
      "reported **13**. Three different answers to one question, all inside registered files, so the "
      "computed set (emitted minus the union of killed ids) is used here and no frozen number is edited."
      % uncovered["shipped_no_mutant_rows_field_says"],
      "",
      "## Attribution rule",
      "",
      "Only rows lost **while `W1301-DRIVER-RAN` survived** are credited to a mutant. Addendum mutant A5 "
      "took the driver down and therefore discriminates nothing on its own, even though seven ids vanished "
      "with it; those seven are listed as owed or measured elsewhere instead. Clean rows newly discriminated "
      "by this addendum: **%d**." % len(cleanly),
      "",
      "## What was actually run here",
      ""]
for m in adj["mutants"]:
    md.append("- `%s` (%s): **%s**%s" % (m["id"], m.get("file", "-"), m.get("bucket"),
                                         "" if not m.get("credits_no_rows") else
                                         " - vanished while the driver died: %s" % ", ".join(m["credits_no_rows"])))
md += ["",
       "Four of the six planned file mutants reported `anchor-missing`: the line each one wanted to break is "
       "not where the addendum searched, so no mutant was applied rather than a different edit being "
       "substituted and renamed a kill.",
       "",
       "## Per-row disposition",
       "",
       "| row | disposition |",
       "| --- | --- |",
       ]
for k in sorted(DISPOSITION):
    md.append("| `%s` | %s |" % (k, DISPOSITION[k]))
md += ["",
       "## Counts",
       "",
       "- killed, covered by a reviewer measurement, or otherwise accounted for: **%d**" % adj["disposition_counts"]["measured_via_reviewer_or_staged"],
       "- OWED (a real gap, not a formatting problem): **%d**" % adj["disposition_counts"]["owed"],
       "- unclassified: **%d**" % adj["disposition_counts"]["unclassified"],
       "",
       "The single most important owed item is `W1301-PROVIDER-OK-IS-SUCCESS`: mutant A6 (the provider "
       "catch-all branch answering `ok:true` for an unlisted status) survived again here, which is the same "
       "survival the round-3 reviewer reproduced. It is the card's own second negative - a provider failure "
       "must never be shown as success - and the suite would not notice that regression.",
       "",
       "Reproduce: `python execution/v2.4/receipts/W13/W13-01/mut_addendum_w1301.py`",
       "",
       "Generated %s at HEAD %s; every mutated file was restored byte-identically and `git status` over apps "
       "and tests is clean." % (adj["finalised_at"], subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                                                   capture_output=True, text=True, cwd=ROOT).stdout.strip()),
       ""]
io.open(notes, "w", encoding="utf-8", newline="\n").write("\n".join(md))
print("clean rows credited:", len(cleanly), "| dispositions:", len(DISPOSITION), adj["disposition_counts"])
print("staged mutant ids seen:", staged_ids)
print("tree clean:", subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "apps", "tests"],
                                    capture_output=True, text=True, cwd=ROOT).stdout.strip() == "")
print("notes:", os.path.basename(notes), os.path.getsize(notes), "bytes")
