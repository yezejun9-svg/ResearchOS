"""Which formal cases could actually be accepted today, and which are only nominally reachable?

The spec binds every formal case to an exact assertion-id list - C01 requires C01-01..C01-05 - and its binding note
says the selector "must report its frozen assertion IDs at the required mode, not an aggregate empty PASS". So the
question is not only "is there a selector naming C01" but "could anything in this tree emit C01-01 .. C01-05".

Three kinds of evidence are separated deliberately, because conflating them is how a card once claimed a property
it never tested:
  - registered selector: some entry in execution/v2.4/commands.json lists the case in a selector;
  - expected-manifest: the id appears only in an expected-*.json list, which the v2.0-era harnesses compare
    against after running tests - it records intent, not capability;
  - named by a program: the id appears in code (.py/.go/.js/.ts) rather than only in a manifest, so some program
    could in principle emit it. Even then, emitting it at the required mode needs the selector actually run, which
    this script deliberately does not do (it is read-only so it can run while an independent reviewer holds the
    tree).

Classes, in decreasing order of readiness: a selector plus every id named by a program; a selector with some ids
named; a selector whose ids live only in a manifest; no selector at all; or the plan itself lists no ids.
"""
import io, json, os, re

NL = chr(10)
SKIP_DIRS = ("node_modules", "__pycache__", ".git")
CODE_EXT = (".py", ".go", ".js", ".ts")
DOC_EXT = (".json", ".html", ".md")


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
SCAN_ROOTS = ["tests", "ops", "adapters", "apps", "internal"]

plan = json.load(io.open(os.path.join(SPEC, "contracts", "execution.plan.json"), encoding="utf-8-sig"))
reg = json.load(io.open("execution/v2.4/commands.json", encoding="utf-8-sig"))

cases, seen = [], set()


def walk(o):
    if isinstance(o, dict):
        cid = o.get("case_id")
        if isinstance(cid, str) and cid.strip() and cid not in seen:
            seen.add(cid)
            cases.append(o)
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)


walk(plan)

# Pre-scan: which ids appear in code at all, and which only inside an expected-manifest. Two passes over the tree,
# built once, so a per-case loop does not re-read thousands of files.
code_ids, manifest_ids = {}, {}
for root in SCAN_ROOTS:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in CODE_EXT and ext not in DOC_EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > 2_000_000:
                    continue
                text = io.open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            found = set(re.findall(r"\b(?:C|A)\d{2}-\d{2}\b", text))
            target = manifest_ids if (ext == ".json" and "expected" in fn) else code_ids
            for aid in found:
                target.setdefault(aid, []).append(p.replace("\\", "/"))


def texts(sel):
    if isinstance(sel, str):
        return [sel]
    if isinstance(sel, dict):
        return [json.dumps(sel, ensure_ascii=False)]
    if isinstance(sel, list):
        return [t for x in sel for t in texts(x)]
    return []


selector_index = {}
for name, entry in (reg.get("commands") or {}).items():
    for t in texts(entry.get("selectors")):
        for c in set(re.findall(r"\b(?:C|A)\d{2}\b", t)):
            selector_index.setdefault(c, set()).add(name)

rows, classes = [], {}
for c in cases:
    cid = c["case_id"]
    expected = list(c.get("expected_assertion_ids") or [])
    named = [a for a in expected if a in code_ids]
    manifest_only = [a for a in expected if a not in code_ids and a in manifest_ids]
    nowhere = [a for a in expected if a not in code_ids and a not in manifest_ids]
    if not expected:
        cls = "plan_lists_no_expected_assertion_ids"
    elif cid not in selector_index:
        cls = "no_registered_selector"
    elif len(named) == len(expected):
        cls = "selector_and_every_id_named_by_a_program"
    elif named:
        cls = "selector_and_only_some_ids_named"
    else:
        cls = "selector_but_ids_live_only_in_a_manifest"
    classes[cls] = classes.get(cls, 0) + 1
    rows.append({"case_id": cid, "task_id": c.get("task_id"), "command_key": c.get("key"),
                 "argv_template": c.get("argv_template"), "binding": c.get("binding"),
                 "expected_assertion_ids": expected,
                 "registered_selectors": sorted(selector_index.get(cid, set())),
                 "ids_named_by_a_program": named,
                 "ids_only_in_a_manifest": manifest_only,
                 "ids_absent_from_the_tree": nowhere,
                 "first_program_naming_each_id": dict((a, code_ids[a][0]) for a in named),
                 "class": cls})

out = {"record": "formal-case acceptance prerequisites, computed statically from the plan, the registry and the source tree",
       "generated_by": "execution/v2.4/formal_case_requirements.py",
       "rule_from_the_spec": "a formal case is accepted when its exact selector reports the frozen assertion-id list "
                             "at the required mode; an aggregate PASS or an empty id set does not count",
       "registry_revision": reg.get("revision"), "cases_total": len(rows), "classes": classes,
       "caveat": "naming an id in a program is not the same as emitting it at the required mode - that needs the "
                 "selector run and its report compared to the frozen list. What this establishes is the shape of "
                 "the remaining work per case, not a claim that any case is accepted",
       "rows": rows}
io.open("execution/v2.4/formal_case_requirements.json", "w", encoding="utf-8", newline=NL).write(
    json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({"cases_total": len(rows), "classes": classes}, indent=1, ensure_ascii=False))
for cls in sorted(classes):
    print(cls, "->", [r["case_id"] for r in rows if r["class"] == cls][:14])
