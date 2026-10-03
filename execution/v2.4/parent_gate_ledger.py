"""Build the 22-parent gate ledger from the plan, the step state, the registry and the checkpoint.

The objective is not "accept cards" but "all 22 parent tasks and all 42 formal cases validly accepted", so this
computes, per parent, exactly how far that is and what stands in the way - without executing anything, which makes
it safe to run while an independent reviewer holds the tree.

Inputs (all read-only):
  - spec contracts/execution.plan.json      -> the DAG: parents, their cards, dependencies, formal cases
  - execution/v2.4/step_state.json          -> which cards are ACCEPTED and by whom
  - execution/v2.4/commands.json            -> which formal case a selector can actually reach
  - execution/v2.4/checkpoint.json          -> blocked resources and outstanding obligations

A parent is shown as it is, not as hoped: a parent with one unaccepted card is NOT gateable, and a formal case is
counted only when a v2.4 selector names it. Reachable is not accepted.
"""
import collections, io, json, os, re

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
SPEC = r"D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4"
V24 = "execution/v2.4"


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


plan = load(os.path.join(SPEC, "contracts", "execution.plan.json"))
st = load(os.path.join(V24, "step_state.json"))
reg = load(os.path.join(V24, "commands.json"))
cp = load(os.path.join(V24, "checkpoint.json"))

recs = st["steps"] if isinstance(st["steps"], list) else list(st["steps"].values())
status = {r.get("id"): r.get("status") for r in recs if isinstance(r, dict) and r.get("id")}

steps = plan.get("steps") or []
parents = collections.OrderedDict()
cards_of = collections.defaultdict(list)
for s in steps:
    sid = s.get("step_id") or s.get("id") or ""
    if not sid:
        continue
    parent = s.get("parent_task") or sid.split("-")[0]
    parents.setdefault(parent, {"kind": "parent", "cards": []})
    parents[parent]["cards"].append(sid)
    cards_of[sid] = s

# formal cases, and which v2.4 command key can reach them
case_owner, case_list = {}, []


def walk(o, path=None):
    if isinstance(o, dict):
        cid = o.get("case_id")
        if isinstance(cid, str) and cid.strip():
            if cid not in case_owner:
                case_owner[cid] = o.get("task_id") or o.get("owner_card") or ""
                case_list.append(cid)
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)


walk(plan)


def texts(sel):
    if isinstance(sel, str):
        return [sel]
    if isinstance(sel, dict):
        return [json.dumps(sel, ensure_ascii=False)]
    if isinstance(sel, list):
        return [t for x in sel for t in texts(x)]
    return []


reachable = collections.defaultdict(set)
for name, entry in (reg.get("commands") or {}).items():
    for t in texts(entry.get("selectors")):
        for cid in set(re.findall(r"\b(?:C|A)\d{2}\b", t)):
            reachable[cid].add(name)

blocked_resources = {}
for b in (cp.get("blocked_resources") or []):
    if isinstance(b, dict):
        blocked_resources[b.get("resource") or b.get("id") or "?"] = b
    elif isinstance(b, str):
        blocked_resources[b] = {"note": "recorded as a bare name"}

ledger = collections.OrderedDict()
for parent, info in parents.items():
    cards = sorted(set(info["cards"]))
    acc = [c for c in cards if status.get(c) == "ACCEPTED"]
    rep = [c for c in cards if c in status and status[c] != "ACCEPTED"]
    untracked = [c for c in cards if c not in status]
    cases = [c for c in case_list if case_owner.get(c) == parent]
    ledger[parent] = {
        "cards_total": len(cards), "cards_accepted": len(acc),
        "cards_reported_not_accepted": rep, "cards_untracked": untracked,
        "all_cards_accepted": bool(cards) and len(acc) == len(cards),
        "formal_cases": cases,
        "formal_cases_reachable": [c for c in cases if reachable.get(c)],
        "formal_cases_unreachable": [c for c in cases if not reachable.get(c)],
        "formal_cases_accepted": [],
    }

accepted_parents = [p for p, v in ledger.items() if v["all_cards_accepted"]]
summary = {
    "generated_by": "execution/v2.4/parent_gate_ledger.py (read-only; nothing executed)",
    "registry_revision": reg.get("revision"),
    "cards_accepted": sum(1 for s in status.values() if s == "ACCEPTED"),
    "cards_total_in_plan": sum(v["cards_total"] for v in ledger.values()),
    "parents_total": len(ledger),
    "parents_with_every_card_accepted": accepted_parents,
    "formal_cases_total": len(case_list),
    "formal_cases_reachable_by_a_selector": [c for c in case_list if reachable.get(c)],
    "formal_cases_unreachable": [c for c in case_list if not reachable.get(c)],
    "blocked_resources": sorted(blocked_resources),
    "reading": "no parent is gateable until every one of its cards is ACCEPTED, and a formal case counts only when "
               "it is both reachable by a registered selector and accepted by its owning card; both columns are "
               "reported separately so a green-looking parent count cannot hide an unreachable case",
    "parents": ledger,
}
io.open(os.path.join(V24, "parent_gate_ledger.json"), "w", encoding="utf-8", newline=NL).write(
    json.dumps(summary, indent=1, ensure_ascii=False))
print(json.dumps({k: summary[k] for k in ("registry_revision", "cards_accepted", "cards_total_in_plan",
                                          "parents_total", "parents_with_every_card_accepted",
                                          "formal_cases_total")}, indent=1, ensure_ascii=False))
print("reachable cases:", len(summary["formal_cases_reachable_by_a_selector"]),
      "| unreachable:", len(summary["formal_cases_unreachable"]))
print("blocked resources:", summary["blocked_resources"])
worst = sorted(ledger.items(), key=lambda kv: kv[1]["cards_accepted"] - kv[1]["cards_total"])[:6]
for p, v in worst:
    print("%s cards %d/%d | reported-not-accepted %s | cases %d, unreachable %d"
          % (p, v["cards_accepted"], v["cards_total"], v["cards_reported_not_accepted"],
             len(v["formal_cases"]), len(v["formal_cases_unreachable"])))
