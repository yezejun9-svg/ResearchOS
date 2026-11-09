"""Bind test.ui.recovery for W13-02 the way W13-01/W06-01/W05-02 bound their own selectors.

Safety order, all of it measured before any byte is written:
  1. commands.json must not be a hash-registered evidence file (an accepted card's pinned bytes are never edited);
  2. the key must be genuinely absent, so nothing existing can be rerouted by the append;
  3. a no-op re-dump must reproduce the current bytes exactly - if it does not, this writer would rewrite the
     whole shared file and the script aborts instead;
  4. every other key's parsed value is compared before/after and must be identical.
"""
import copy
import io
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__) + "/..")) if False else r"D:/作品集/ResearchOS/research-os"
PATH = os.path.join(ROOT, "execution/v2.4/commands.json")
STATE = os.path.join(ROOT, "execution/v2.4/step_state.json")
KEY = "test.ui.recovery"
TEMPLATE = "test.ui.routes"
DRY = "--apply" not in sys.argv

raw = io.open(PATH, "rb").read()
doc = json.loads(raw.decode("utf-8-sig"))

evidence = [e["path"] for r in json.loads(io.open(STATE, encoding="utf-8-sig").read())["steps"] for e in r.get("evidence", [])]
pinned = [p for p in evidence if p.endswith("commands.json")]
assert pinned == [], "commands.json is hash-registered evidence at %s - stop, do not edit" % pinned
assert KEY not in doc["commands"], "%s already exists; the append would be a reroute" % KEY

indent = doc.get("schema_version") and 1
text = raw.decode("utf-8-sig")
detect = 1 if text.splitlines()[1].startswith(" ") else None
assert detect == 1, "unexpected indentation %r; this writer only reproduces indent=1 files" % detect

tail = "\n" if text.endswith("\n") else ""
replay = json.dumps(doc, indent=detect, ensure_ascii=False) + tail
if replay.encode("utf-8") != raw:
    before, after = text, replay
    probe = sum(1 for a, b in zip(before.splitlines(), after.splitlines()) if a != b)
    print("LINES_DIFFERING", probe, "LEN", len(before), len(after))
    print("first diff:", next((i for i, (a, b) in enumerate(zip(before.splitlines(), after.splitlines())) if a != b), None))
    raise SystemExit("refusing to write: a no-op re-dump does not reproduce the current bytes")

after_doc = copy.deepcopy(doc)
entry = copy.deepcopy(doc["commands"][TEMPLATE])
argv = list(entry["argv"])
argv = [a for a in argv if a not in ("tests/ui/check/main.py",)]
argv.append(os.path.join("tests", "ui", "continuity", "check", "main.py").replace("\\", "/"))
entry["argv"] = argv
entry["selectors"] = {"task_id": ["W13"], "check_id": ["W13-02"], "case_id": ["C26"]}
entry["owner_card"] = "W13-02"
entry["note"] = ("registered by W13-02: check_id W13-02 is served by tests/ui/continuity/check/main.py, which runs "
                 "the pinned-node two-surface protocol probe (apps/desktop/main/lib/v2.js against "
                 "apps/web/src/v2client.js, tables also compared to the frozen client.protocol.schema.json) and a "
                 "real-browser producer probe against the built bundle with a recording stub host. case_id C26 is "
                 "forwarded unchanged to ops/ci/ui.py --phase recovery with the same selector environment, so "
                 "binding this card cannot shadow an accepted case row.")
entry["fixed_env"] = dict(entry.get("fixed_env") or {})
# Do not clone W13-01's pinned executor identity onto this card's runs: the construction identity belongs to the
# dispatcher's caller, not to a registry row copied from another card.
entry["fixed_env"].pop("RESEARCHOS_EXECUTOR_ID", None)
for field in ("selectors", "checks", "cases", "task_id", "notes", "purpose", "description", "forward"):
    if field in entry:
        print("TEMPLATE_FIELD", field, json.dumps(entry[field], ensure_ascii=False)[:220])
after_doc["commands"][KEY] = entry
after_doc.setdefault("revision", after_doc.get("revision"))

out = json.dumps(after_doc, indent=detect, ensure_ascii=False) + tail
parsed = json.loads(out)
changed = [k for k in doc["commands"] if parsed["commands"].get(k) != doc["commands"][k]]
assert changed == [], "the append would alter other selectors: %s" % changed
assert list(parsed["commands"]) == list(doc["commands"]) + [KEY], "key order changed; only an append is allowed"
print("TEMPLATE_ENTRY", json.dumps(entry, ensure_ascii=False)[:1200])
print("KEYS_BEFORE", len(doc["commands"]), "KEYS_AFTER", len(parsed["commands"]))
print("BYTE_DELTA", len(out.encode("utf-8")) - len(raw))
if DRY:
    print("DRY RUN - nothing written. Re-run with --apply")
    raise SystemExit(0)

tmp = PATH + ".w1302.tmp"
io.open(tmp, "w", encoding="utf-8", newline="\n").write(out)
os.replace(tmp, PATH)
print("APPLIED", KEY)
