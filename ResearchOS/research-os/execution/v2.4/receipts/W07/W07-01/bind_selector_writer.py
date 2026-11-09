"""Bind test.sources.live for W07-01 with the same guards that bound test.orchestration and test.ui.recovery.

Measured before any byte is written: the key must be genuinely absent; the writer must reproduce the current file
byte-for-byte on a no-op re-dump; every other selector's parsed value must be identical afterwards; and the key
order must be the old list plus the new key at the end. Anything else aborts.
"""
import copy
import io
import json
import os
import sys

ROOT = r"D:/作品集/ResearchOS/research-os"
PATH = os.path.join(ROOT, "execution/v2.4/commands.json")
STATE = os.path.join(ROOT, "execution/v2.4/step_state.json")
KEY = "test.sources.live"
TEMPLATE = "test.ui.recovery"
DRY = "--apply" not in sys.argv

raw = io.open(PATH, "rb").read()
text = raw.decode("utf-8-sig")
doc = json.loads(text)
tail = "\n" if text.endswith("\n") else ""

evidence = [e["path"] for r in json.loads(io.open(STATE, encoding="utf-8-sig").read())["steps"] for e in r.get("evidence", [])]
assert not [p for p in evidence if p.endswith("commands.json")], "commands.json is hash-registered evidence; do not edit"
assert KEY not in doc["commands"], "%s already exists; the append would be a reroute" % KEY
assert text.splitlines()[1].startswith(" "), "unexpected indentation"
assert json.dumps(doc, indent=1, ensure_ascii=False) + tail == text, "a no-op re-dump does not reproduce the bytes"

entry = copy.deepcopy(doc["commands"][TEMPLATE])
argv = [a for a in entry["argv"] if a != os.path.join("tests", "ui", "continuity", "check", "main.py")]
argv.append("tests/sources/check/main.py")
entry["argv"] = argv
entry["selectors"] = {"task_id": ["W07"], "check_id": ["W07-01"], "case_id": ["A05"]}
entry["owner_card"] = "W07-01"
entry["timeout_seconds"] = 1800
entry["scope"] = ("W07 real public GitHub and arXiv reads plus the reused adapter contract; the X kind needs an "
                  "authorized BrowserAct tool and is disclosed rather than simulated")
entry["note"] = ("registered by W07-01: check_id W07-01 is served by tests/sources/check/main.py, which grades the "
                 "reused adapter suite per card action, builds and runs the live probe for GITHUB and PAPER in a "
                 "fresh database per run, reads the authoritative SourceCursor back out of domain_objects and "
                 "domain_versions, and runs an unreachable-endpoint control. Every other selector this key "
                 "resolves - W07-02, the parent gate's W07-G02/W07-H07, and case A05 - is forwarded unchanged to "
                 "ops/ci/sources.py, which owns those rows and refuses what it does not recognise; the routing "
                 "decision itself is asserted as W0701-ROUTING-TRUTH-TABLE so binding this card cannot shadow "
                 "another card's selector.")
fixed = dict(entry.get("fixed_env") or {})
fixed.pop("RESEARCHOS_EXECUTOR_ID", None)
entry["fixed_env"] = fixed

after = copy.deepcopy(doc)
after["commands"][KEY] = entry
out = json.dumps(after, indent=1, ensure_ascii=False) + tail
parsed = json.loads(out)
assert [k for k in doc["commands"] if parsed["commands"].get(k) != doc["commands"][k]] == [], "other selectors changed"
assert list(parsed["commands"]) == list(doc["commands"]) + [KEY], "only an append is allowed"
print("TEMPLATE_KEYS", sorted(entry))
print("KEYS", len(doc["commands"]), "->", len(parsed["commands"]), "| BYTE_DELTA", len(out.encode("utf-8")) - len(raw))
if DRY:
    print("DRY RUN - nothing written")
    raise SystemExit(0)
tmp = PATH + ".w0701.tmp"
io.open(tmp, "w", encoding="utf-8", newline="\n").write(out)
os.replace(tmp, PATH)
print("APPLIED", KEY)
