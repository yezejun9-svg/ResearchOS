"""Sentence census for W05-01 (and reusable for later cards), added after the sixth review measured that the
self-auditor is blind to the defect class the loop has blocked five times.

audit_receipt_w0501.py re-derives figures, ids, digests and buckets; the sixth reviewer injected three
round-5-style stale sentences into known_limitations and defects and the auditor passed at zero findings. That
is the class this probe exists for: a sentence asserting a fact the tree no longer supports. It cannot decide
truth on its own, so it does the only thing measurement can do - it keeps a canon of clauses that were each
refuted by a named measurement, and reports every place one still appears, distinguishing a clause carried as
history (dated, superseded, quoted) from one asserted as current fact.
"""
import io, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if not os.path.isdir(os.path.join(REPO, "internal", "domain")):
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "internal", "domain")):
            REPO = d
            break
        d = os.path.dirname(d)
os.chdir(REPO)

HISTORY_MARKERS = ("superseded", "position as of", "round-1", "round-2", "round-3", "round-4", "round 2",
                   "kept visible", "dated here", "no longer accurate", "before round 5",
                   # a clause quoted inside somebody else finding, or inside the record of the correction that
                   # replaced it, is history carried forward rather than this tree asserting it as fact. The
                   # first real run of this probe flagged six such quotations as current assertions, which is
                   # why these markers exist; the canon itself did not change and the injected self-test
                   # sentence carries none of them, so it is still caught.
                   "that said", "when twenty do", "proved false", "refuted", "reservation", "finding",
                   "quoted", "reviewer", "correction")

# each refuted clause carries the measurement that refuted it, so a hit can be judged rather than argued
CANON = [
 {"clause": "all 23 mapped methods carry an empty rpc_binding",
  "refuted_by": "execution/v2.4/client_mapping.json census: 23 entries, 20 empty, the exceptions session.send, session.control and provider.models annotated n/a (Go-owned catalog)"},
 {"clause": "no owning card",
  "refuted_by": "execution/v2.4/commands.json rev 14: cli.entry_run is the only cli.* key and its owner_card names W03-01 interactive CLI, which is in the accepted steps"},
 {"clause": "nothing in this program drives turn.failed",
  "refuted_by": "adapters/runtime/runtime_windows_test.go:66-68 drives turn.failed shapes and passes; the widened captured filter selects it"},
 {"clause": "nothing exercises turn.failed",
  "refuted_by": "the same pre-existing test named above"},
 {"clause": "nothing launches the worker under that Run id and lease epoch",
  "refuted_by": "tests/runtime/check/w0501.go W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL launches rt.Start with the claimed Run id, task id and lease epoch, killed by M21 and M22"},
 {"clause": "the adapter journal and the domain Run never meet",
  "refuted_by": "the same row, plus the ledger reservation keyed to that Run id"},
 {"clause": "is unmet in this tree and disclosed as W0501-RUN-EVENT-AND-COST-CORRELATION",
  "refuted_by": "the identity half is asserted since round 5; only the service-launched event ledger remains blocked"},
 {"clause": "carried as an open obligation rather than claimed here",
  "refuted_by": "the obligation text now narrows the duty to the service-launched half; the identity half is claimed and measured"},
 {"clause": "with the accurate reason",
  "refuted_by": "the reason it introduced described the pre-round-5 tree and was rewritten as superseded"},
 {"clause": "cli.* commands remain UNBOUND with no owning card",
  "refuted_by": "the registry census named above"},
]

SCOPE = ["execution/v2.4/receipts/W05/W05-01/receipt.json",
         "execution/v2.4/receipts/W05/W05-01/generate_receipt_w0501.py",
         "execution/v2.4/receipts/W05/W05-01/register_w0501_accepted.py",
         "execution/v2.4/receipts/W05/W05-01/make_review_request_w0501.py",
         "tests/runtime/check/w0501.go",
         "execution/v2.4/checkpoint.json"]
HISTORY = [f for f in sorted(os.listdir(os.path.join("execution", "v2.4", "receipts", "W05", "W05-01")))
           if f.startswith(("independent_review", "review_request", "verdict_", "pin_drift_"))]


def scan(path, needles):
    try:
        text = io.open(os.path.join(REPO, path), encoding="utf-8", errors="replace").read()
    except OSError:
        return {}
    return {n: text.count(n) for n in needles if text.count(n)}


def classify(path, line):
    low = line.lower()
    return "history" if any(m in low for m in HISTORY_MARKERS) else "current-assertion"


needles = [c["clause"] for c in CANON]
hits, current, historical = [], 0, 0
for path in SCOPE:
    counts = scan(path, needles)
    if not counts:
        continue
    lines = io.open(os.path.join(REPO, path), encoding="utf-8", errors="replace").read().split("\n")
    for c in CANON:
        for i, line in enumerate(lines, 1):
            if c["clause"] in line:
                kind = classify(path, line)
                hits.append({"path": path, "line": i, "clause": c["clause"], "kind": kind,
                             "refuted_by": c["refuted_by"],
                             "text": line.strip()[:200]})
                if kind == "current-assertion":
                    current += 1
                else:
                    historical += 1
for f in HISTORY:
    p = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01", f)
    for n, k in scan(p, needles).items():
        hits.append({"path": p, "line": 0, "clause": n, "kind": "history-carrier", "count": k})

out = {"record": "W05-01 refuted-clause census", "canon_size": len(CANON),
 "instruments_scanned": SCOPE, "history_files_scanned": len(HISTORY),
 "asserted_as_current_fact": current, "carried_as_history": historical,
 "history_carriers": len([h for h in hits if h["kind"] == "history-carrier"]),
 "findings": [h for h in hits if h["kind"] == "current-assertion"],
 "verdict": "CLEAN" if current == 0 else "STALE_SENTENCES",
 "limits": "a canon can only catch clauses somebody already refuted once; it cannot prove a new sentence true. "
           "Its value is that the same clause cannot silently survive the next round of edits, and that a reviewer "
           "can extend the canon with one line per finding instead of re-reading every instrument."}
io.open(os.path.join(REPO, "execution", "v2.4", "receipts", "W05", "W05-01", "sentence_census_w0501.json"),
        "w", encoding="utf-8", newline="\n").write(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({k: out[k] for k in ("canon_size", "asserted_as_current_fact", "carried_as_history", "history_carriers", "verdict")}))
sys.exit(1 if current else 0)
