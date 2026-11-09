"""Turn the case requirements into a work order per owner card, and name the orphans.

The endgame is 22 parents and 42 formal cases, so what matters is not a list of cases but who has to do each one and
what is missing. Every plan step carries `affected_formal_cases`, and `formal_case_requirements.json` records whether
a case has a selector and whether its frozen ids are named by a program. Joining them answers, per card:
  - which formal cases this card is responsible for;
  - the exact command a reviewer should run once the case is ready;
  - the specific gap: no selector, ids nobody can emit yet, or ids that exist and merely need the selector run;
  - and, importantly, cases no card claims - an orphan cannot be accepted by anyone, so it has to be assigned before
    the 42-case gate can close at all.

Read-only: it executes nothing, which keeps it safe to run while an independent reviewer holds the tree.
"""
import io, json, os

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

plan = json.load(io.open(os.path.join(SPEC, "contracts", "execution.plan.json"), encoding="utf-8-sig"))
st = json.load(io.open("execution/v2.4/step_state.json", encoding="utf-8-sig"))
req = json.load(io.open("execution/v2.4/formal_case_requirements.json", encoding="utf-8-sig"))

recs = st["steps"] if isinstance(st["steps"], list) else list(st["steps"].values())
status = {r.get("id"): r.get("status") for r in recs if isinstance(r, dict) and r.get("id")}
case_req = {r["case_id"]: r for r in req["rows"]}

claims = {}
for s in plan.get("steps") or []:
    sid = s.get("id")
    for cid in (s.get("affected_formal_cases") or []):
        claims.setdefault(cid, []).append(sid)

by_card = {}
orphans = []
for cid, owners in sorted(claims.items()):
    r = case_req.get(cid, {})
    gap = r.get("class", "not_in_the_case_list_at_all")
    for owner in owners:
        by_card.setdefault(owner, []).append({"case_id": cid, "gap": gap,
                                             "expected_assertion_ids": r.get("expected_assertion_ids"),
                                             "registered_selectors": r.get("registered_selectors"),
                                             "ids_absent_from_the_tree": r.get("ids_absent_from_the_tree"),
                                             "command": " ".join(r.get("argv_template") or []) or "no argv in the plan",
                                             "owner_card_status": status.get(owner, "not_started")})
    if not owners:
        orphans.append(cid)

unclaimed_cases = [c for c in case_req if c not in claims]

rows = []
for card, items in sorted(by_card.items()):
    rows.append({"card": card, "card_status": status.get(card, "not_started"),
                 "cases": len(items),
                 "cases_close_to_ready": [i["case_id"] for i in items
                                         if i["gap"] == "selector_and_every_id_named_by_a_program"],
                 "cases_needing_emitters": [i["case_id"] for i in items
                                            if i["gap"] in ("selector_and_only_some_ids_named",
                                                            "selector_but_ids_live_only_in_a_manifest")],
                 "cases_needing_a_selector": [i["case_id"] for i in items if i["gap"] == "no_registered_selector"],
                 "detail": items})

out = {"record": "per-card work orders for the 42 formal cases, joined from the plan and the case requirements",
       "generated_by": "execution/v2.4/formal_case_work_orders.py",
       "cards_owning_cases": len(rows),
       "cases_claimed_by_a_card": len(claims),
       "cases_no_card_claims": unclaimed_cases,
       "cards_all_accepted": [r["card"] for r in rows if r["card_status"] == "ACCEPTED"],
       "nearest_to_ready": sorted({c for r in rows for c in r["cases_close_to_ready"]}),
       "reading": "a case is accepted only by its owning card's selector reporting the frozen ids at the required "
                  "mode, so a case with no owner is structurally unacceptable until the plan assigns one; that is "
                  "recorded here rather than discovered at the gate",
       "cards": rows}
io.open("execution/v2.4/formal_case_work_orders.json", "w", encoding="utf-8", newline=NL).write(
    json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({"cards_owning_cases": len(rows), "cases_claimed": len(claims),
                  "cases_no_card_claims": unclaimed_cases,
                  "nearest_to_ready": out["nearest_to_ready"],
                  "cards_already_accepted": out["cards_all_accepted"]}, indent=1, ensure_ascii=False))
