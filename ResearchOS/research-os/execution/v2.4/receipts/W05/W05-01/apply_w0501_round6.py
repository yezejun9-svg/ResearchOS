"""W05-01 round-6 remediation for W0501-R5-B-01, plus the two registrar and capture defects the fifth
review found while it was checking the fix.

The blocker was propagation, not capability: the round-5 assertion made five earlier sentences false and they
were still standing in the receipt, in the disclosure array, in the generator that writes both, in the
registrar that would have copied one into the append-only acceptance record, and in the un-narrowed
continuation obligation. Two further repairs the reviewer found by reading the instruments rather than the
prose: the -list capture digests a wall-clock line so it cannot evidence the names it is cited for, and the
registrar allow-list omits the plain ACCEPTED name, so a clean acceptance verdict would have been refused.
"""
import datetime, io, json, os

REPO = r"D:/作品集/ResearchOS/research-os"
os.chdir(REPO)
NL = chr(10)
GO = os.path.join("tests", "runtime", "check", "w0501.go")
GEN = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01", "generate_receipt_w0501.py")
REG = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01", "register_w0501_accepted.py")
CP = os.path.join("execution", "v2.4", "checkpoint.json")


def rep_lit(text, needle, new, label):
    if text.count(needle) != 1:
        raise SystemExit("%s: needle hits %d" % (label, text.count(needle)))
    i = text.find(needle)
    a = text.rfind('"', 0, i)
    b = text.find('"', i)
    if a < 0 or b <= a or '"' in new:
        raise SystemExit("%s: cannot bound literal safely" % label)
    print("%s: replaced %d chars" % (label, b - a - 1))
    return text[:a + 1] + new + text[b:]


def rep_concat(text, needle, new, label):
    """Replace a Go or Python string that may continue across source lines as adjacent literals."""
    if text.count(needle) != 1:
        raise SystemExit("%s: needle hits %d" % (label, text.count(needle)))
    i = text.find(needle)
    a = text.rfind('"', 0, i)
    pos = a + 1
    while True:
        b = text.find('"', pos)
        nxt = text[b + 2:b + 220].lstrip()
        if nxt.startswith('"'):
            pos = text.find('"', b + 2)
            continue
        break
    if '"' in new:
        raise SystemExit("%s: replacement has a double quote" % label)
    print("%s: replaced a %d char span" % (label, b - a))
    return text[:a] + '"' + new + '"' + text[b + 1:]


CLI = ("the deliverable own-CLI leg is NOT_RUN for a reason measured in the registry: cli.entry_run is the only cli.* key in "
 "execution/v2.4/commands.json at revision 14, its state is UNBOUND, its selectors are wildcards so the card selector triple does "
 "match it, its owner_card names the already-accepted W03-01 interactive CLI, and dispatching it for this card returns "
 "NOT_IMPLEMENTED with zero assertions, which is never a PASS. The gap is an accepted owner whose command is still unbound, not an "
 "ownerless command, and apps/cli stays unexercised here even though it sits inside this cards write scope")

HOST = ("deliverable 1 asks for the flow to run through the one and only host, and that conjunct is NOT_RUN: client_mapping.json lists "
 "host.status and host.configure as PLANNED_IN_W02_03_THEN_W03 owned by W02-03 with an empty rpc_binding, and the sibling CLI gap is "
 "measured as cli.entry_run being the only cli.* key in the v2.4 registry, state UNBOUND, wildcard selectors that do match this card, "
 "and an owner_card naming the already-accepted W03-01 interactive CLI, so there is no registered host path for this card to drive. "
 "What is asserted here is the adapter, the decoder and the shared service reached over its own HTTP handler, which is not the same claim")

CORR = ("the Run identity join is asserted as of round 5 and is not disclosed: W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL launches the worker "
 "under the claimed Run id, task id and lease epoch and requires the settled journal Spec plus the fixture reservation key to agree with that "
 "Run, killed by M21 and M22. What stays unmet is narrower: the service launching the adapter on its own and the domain event ledger behind it, "
 "which runtime qualification blocks (ops/runtime/capabilities.json and the absent pinned executor build; the only Run-keyed rt.Start call outside "
 "tests is behind the exact qualification dispatch marker in internal/domain/runtime_dispatch.go). That narrower duty is carried as an open obligation")

DEFECT = ("superseded reason, kept visible rather than deleted: the round-1 and round-4 text said the service phase claims a Run while the adapter "
 "phase runs a journal-local run id and nothing launches the worker under the domain Run id and lease epoch. That described the tree before round 5 "
 "and is no longer accurate, because W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL now makes the identity join an assertion with two mutants; what remains "
 "open is only the service-launched half quoted above")

REGISTRAR = ("position as of round 2, dated here because this array is append-only and later windows inherit it: W0501-RUN-EVENT-AND-COST-CORRELATION was "
 "disclosed as unmet because the adapter journal and the domain Run never met. From round 5 they meet inside W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL, whose "
 "Run id, task id and lease epoch come from the claimed domain Run and whose ledger reservation key must equal the fixture dispatch key, and M21 and M22 kill it. "
 "Only the service-launched event ledger stays blocked by runtime qualification")

LIMIT_EXTRA = ("one coverage-table entry is scheduling-contingent rather than fixed: under mutant M4 the stale-epoch cancel races the worker launch, so the "
 "Launched clause of W0501-ADAPTER-REVISION-RECORDED can survive or die depending on timing. The fifth reviewer measured the committed five-row killed set five "
 "times out of five while the fourth measured four rows once, so the bucket never moves and no mutant ever survives, but the row list for that one case is not a "
 "fixed table. The receipt also hash-pins the matrix file that its own reproduce step rewrites, so a reviewer that re-runs the matrix must expect the artifact "
 "digest to move and should compare rows rather than digests")

g = io.open(GEN, encoding="utf-8").read()
g = rep_lit(g, "events-and-cost-bound-to-the-Run property is unmet", CORR, "gen.limitations[3]")
g = rep_lit(g, "cli.* commands remain UNBOUND", CLI, "gen.limitations[4]")
g = rep_lit(g, "with the accurate reason", DEFECT, "gen.defects[6].fix")
g = rep_lit(g, "nothing here accepts parent W05 or signs any formal case", LIMIT_EXTRA.rstrip(".") + ", and nothing here accepts parent W05 or signs any formal case", "gen.limitations[last]")

# the -list capture must evidence names, not a digest over a wall-clock line
OLD_CAP = '''        dump(os.path.join(LOGS, key + ".json"),
             {"key": key, "cwd": "REPOSITORY", "argv": [os.path.relpath(GO, REPO).replace("\\\\", "/")] + argv,
              "exit_code": p.returncode, "result": result, "code_revision": head,'''
NEW_CAP = '''        names = sorted(l.strip() for l in text.splitlines() if l.strip().startswith("TestW05"))
        filt = [a for i, a in enumerate(argv) if a == "-run" and i + 1 < len(argv)]
        import re as _re
        selected = sorted(n for n in names for f in filt if _re.match(f, n))
        dump(os.path.join(LOGS, key + ".json"),
             {"key": key, "cwd": "REPOSITORY", "argv": [os.path.relpath(GO, REPO).replace("\\\\", "/")] + argv,
              "test_names_present": names, "selected_by_this_filter": selected,
              "exit_code": p.returncode, "result": result, "code_revision": head,'''
if g.count(OLD_CAP) != 1:
    raise SystemExit("capture anchor hits %d" % g.count(OLD_CAP))
g = g.replace(OLD_CAP, NEW_CAP)
io.open(GEN, "w", encoding="utf-8", newline=NL).write(g)
print("generator patched, capture now records names")

s = io.open(GO, encoding="utf-8").read()
s = rep_lit(s, "cli.* commands UNBOUND with no owning card", HOST, "go.single_host_conjunct")
io.open(GO, "w", encoding="utf-8", newline=NL).write(s)

r = io.open(REG, encoding="utf-8").read()
r = rep_concat(r, "W0501-RUN-EVENT-AND-COST-CORRELATION is disclosed as unmet, not asserted", REGISTRAR, "registrar.disclosed_incidents")
if "ACCEPTED" not in r and "ACCEPT_WITH_RESERVATIONS" in r:
    r = r.replace("ACCEPT_WITH_RESERVATIONS", "ACCEPTED", "ACCEPT_WITH_RESERVATIONS", 1)
    print("registrar allow-list now includes the plain ACCEPTED name")
io.open(REG, "w", encoding="utf-8", newline=NL).write(r)

cp = json.load(io.open(CP, encoding="utf-8-sig"))
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
hits = 0
for o in cp["open_obligations_before_next_card"]:
    if isinstance(o, dict) and o.get("id") == "W05-01-run-correlation":
        o["text"] = ("narrowed at round 5: the Run identity join is asserted (worker launched under the claimed Run id, task id and lease epoch; settled journal "
          "Spec and fixture reservation key required to agree; M21 and M22 kill it). Only the service launching the adapter and the domain event ledger behind it "
          "remain owed, and runtime qualification blocks that half.")
        o["narrowed_at"] = now
        hits += 1
have = set(o.get("id") for o in cp["open_obligations_before_next_card"] if isinstance(o, dict))
NEW = [{"id": "W05-01-r5-" + str(b.get("id")), "card": "W05-01",
        "text": str(b.get("title")) + " | owed: " + str(b.get("fix") or "")[:420],
        "raised_by": str(cp.get("work_in_progress", {}).get("reviewer", "w0501_verifier_r5")), "at": now}
       for b in [json.load(io.open(os.path.join("execution", "v2.4", "receipts", "W05", "W05-01", "independent_review_round5.json"), encoding="utf-8"))["blocking_issues"][0]]]
NEW += [{"id": "W05-01-matrix-scheduling-contingency", "card": "W05-01",
  "text": "under mutant M4 the stale-epoch cancel races the launch, so W0501-ADAPTER-REVISION-RECORDED can survive or die on timing; two reviewers measured different killed sets. Either serialise the launch observation or mark that row as timing-dependent in the coverage table instead of reporting it as a fixed table.",
  "raised_by": "qoder-desktop:/root/w0501_verifier_r5 (RS-01)", "at": now},
 {"id": "W05-01-registrar-does-not-verify-head", "card": "W05-01",
  "text": "register_w0501_accepted.py re-runs nothing and compares no HEAD: it will happily register a receipt whose binding runs were measured on a stale tree. Add a check that the verdicts HEAD, the receipt HEAD and the current non-execution tree agree before it writes, and keep the refusal path measured.",
  "raised_by": "qoder-desktop:/root/w0501_verifier_r5 (finding E)", "at": now}]
cp["open_obligations_before_next_card"] = cp["open_obligations_before_next_card"] + [o for o in NEW if o["id"] not in have]
cp["integrity_events"] = (cp.get("integrity_events") or []) + [{"at": now, "kind": "record_correction",
  "by": "qoder-desktop:/root/construction",
  "event": "The fifth review blocked on propagation: the round-5 assertion made five sentences false and they survived in the receipt, in the disclosure array, in the generator that writes both, in the registrar that would have copied one into the append-only acceptance record, and in the un-narrowed continuation obligation. All five are rewritten to the measured current state, the superseded reason is kept visible rather than deleted, and the direction of the error is stated plainly: it understated what the card now proves. Two instrument defects the same reviewer found are fixed here too - the package listing capture now records the test names and which ones the filter selects instead of digesting a line that contains a clock, and the registrar allow-list was missing the plain ACCEPTED name so a clean acceptance would have been refused.",
  "evidence": ["execution/v2.4/receipts/W05/W05-01/independent_review_round5.json",
               "execution/v2.4/receipts/W05/W05-01/generate_receipt_w0501.py",
               "execution/v2.4/receipts/W05/W05-01/register_w0501_accepted.py"]}]
io.open(CP, "w", encoding="utf-8", newline=NL).write(json.dumps(cp, indent=1, ensure_ascii=False))
print("obligation narrowed:", hits, "| obligations", len(cp["open_obligations_before_next_card"]))
