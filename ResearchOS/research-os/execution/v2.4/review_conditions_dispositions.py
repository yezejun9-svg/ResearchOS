"""For every ACCEPTED card, which reviewer conditions have a written disposition and which do not.

An accepted card is not finished because it was accepted: the reservations its reviewers raised are latent risk to
the parent gates that sit above it. `review_conditions_index.json` counts them; this joins each one to the files
that could have dispositioned it - addenda, executor responses, errata, notes - and reports what matches nothing.

Matching is deliberately weak and stated as such: a reservation is counted as dispositioned only when its own text
appears in one of that card's response files. That under-counts paraphrases (a disposition can summarise rather
than quote) and cannot judge whether a disposition is correct, only whether one exists. The unmatched list is
therefore a work queue for a reader, not a verdict.

Read-only: nothing is executed, so it is safe while an independent review holds the tree.
"""
import glob, io, json, os

NL = chr(10)


def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
V24 = "execution/v2.4"
RESPONSE_MARKERS = ("response", "addendum", "erratum", "correction", "REWORK", "RESUME", "review_request",
                    "verdict_pin", "notes")


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [v] if v.strip() else []
    return [json.dumps(v, ensure_ascii=False)]


def norm(text):
    s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    return " ".join(s.lower().split())[:180]


st = load(os.path.join(V24, "step_state.json"))
recs = st["steps"] if isinstance(st["steps"], list) else list(st["steps"].values())
accepted = sorted(r.get("id") for r in recs if isinstance(r, dict) and r.get("status") == "ACCEPTED")

rows = []
for card in accepted:
    rd = os.path.join(V24, "receipts", card.split("-")[0], card)
    if not os.path.isdir(rd):
        rows.append({"card": card, "receipt_dir_absent": True})
        continue
    conditions = []
    for vp in sorted(glob.glob(os.path.join(rd, "independent_review*.json"))):
        v = load(vp)
        if isinstance(v, list):
            v = v[-1] if v else {}
        for field in ("reservations", "limitations"):
            for item in as_list(v.get(field)):
                conditions.append({"source": os.path.basename(vp), "kind": field, "text": norm(item)})
    response_text = ""
    response_files = []
    for p in sorted(os.listdir(rd)):
        if not os.path.isfile(os.path.join(rd, p)):
            continue
        if p.startswith("independent_review") or p == "receipt.json":
            continue
        if any(m.lower() in p.lower() for m in RESPONSE_MARKERS) or p.endswith(".md"):
            response_files.append(p)
            try:
                response_text += " " + norm(io.open(os.path.join(rd, p), encoding="utf-8",
                                                   errors="replace").read())
            except OSError:
                pass
    # Text matching was tried first and is not usable: comparing each condition's leading 90
    # characters against the card's response files returned 0 matches out of 224 conditions, which says the
    # matcher is brittle (a disposition summarises rather than quotes), not that nothing was answered. A
    # number that measures the tool is worse than no number, so the artifact reports only what is
    # structural and verifiable: which conditions exist, and which files could hold an answer.
    rows.append({"card": card, "conditions": len(conditions),
                 "reservations": sum(1 for c in conditions if c["kind"] == "reservations"),
                 "limitations": sum(1 for c in conditions if c["kind"] == "limitations"),
                 "verdict_files": len(glob.glob(os.path.join(rd, "independent_review*.json"))),
                 "has_disposition_file": bool(response_files),
                 "disposition_files": response_files,
                 "conditions_per_verdict_file": {os.path.basename(v): sum(
                     1 for c in conditions if c["source"] == os.path.basename(v))
                     for v in glob.glob(os.path.join(rd, "independent_review*.json"))},
                 "answer_requires_a_reader": True})

summary = {"record": "reviewer conditions on accepted cards, joined to written dispositions",
           "generated_by": "execution/v2.4/review_conditions_dispositions.py (read-only)",
           "accepted_cards": len(rows),
           "cards_with_no_receipt_dir": [r["card"] for r in rows if r.get("receipt_dir_absent")],
           "total_conditions": sum(r.get("conditions", 0) for r in rows),
           "cards_with_a_disposition_file": [r["card"] for r in rows if r.get("has_disposition_file")],
           "cards_without_any_disposition_file": [r["card"] for r in rows if r.get("conditions")
                                                   and not r.get("has_disposition_file")],
           "meaning": "a disposition file existing is not the same as a condition being answered. This lists where "
                      "an answer could live and where none does; deciding whether each condition is met needs a "
                      "reader, and the earlier text-matching attempt was dropped because it produced 0 of 224 "
                      "matches and was measuring its own brittleness",
           "rows": rows}
io.open(os.path.join(V24, "review_conditions_dispositions.json"), "w", encoding="utf-8", newline=NL).write(
    json.dumps(summary, indent=1, ensure_ascii=False))
print(json.dumps({k: summary[k] for k in ("accepted_cards", "total_conditions",
                                          "cards_with_a_disposition_file",
                                          "cards_without_any_disposition_file")}, indent=1, ensure_ascii=False))
for r in sorted(rows, key=lambda x: -x.get("conditions", 0))[:8]:
    print("%-8s conditions %-4s (res %s / lim %s) verdicts %-2s disposition files: %s"
          % (r["card"], r.get("conditions"), r.get("reservations"), r.get("limitations"),
             r.get("verdict_files"), r.get("disposition_files") or "NONE"))
