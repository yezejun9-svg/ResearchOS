"""Append check_id W07-02 to the test.sources.live selector roster, with before/after proof.

The roster is the only thing this changes. The dispatch layer refuses a selector that is not listed - measured, the
first W07-02 run returned NOT_IMPLEMENTED with zero assertions and never launched the child - so the card cannot be
verified without it. The guards below are the 旧例 for this shared append point, because a bad edit here silently
reroutes other cards' selectors.
"""
import hashlib
import io
import json
import os

# repo/execution/v2.4/receipts/W07/W07-02/script.py -> five levels up is the repository root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
P = os.path.join(ROOT, "execution", "v2.4", "commands.json")
KEY, NEW_CHECK = "test.sources.live", "W07-02"

raw = io.open(P, encoding="utf-8").read()
tail = "\n" if raw.endswith("\n") else ""
data = json.loads(raw)
assert json.dumps(data, indent=1, ensure_ascii=False) + tail == raw, "registry does not round-trip; abort"
cmds = data.get("commands") or data
assert KEY in cmds, "the key this card builds on is missing"
before_state = json.dumps(cmds, indent=1, ensure_ascii=False, sort_keys=True)
before_order = list(cmds.keys())
before_argv = json.dumps(cmds[KEY]["argv"], ensure_ascii=False)
rev_before = data.get("revision")

sel = cmds[KEY]["selectors"]
assert NEW_CHECK not in sel["check_id"], "W07-02 is already registered"
assert sel["check_id"] == ["W07-01"], json.dumps(sel, ensure_ascii=False)
old_list = list(sel["check_id"])
sel["check_id"] = old_list + [NEW_CHECK]
data["revision"] = (rev_before + 1) if isinstance(rev_before, int) else rev_before
cmds[KEY]["note"] = (cmds[KEY].get("note", "") +
                     " | extended by W07-02: check_id W07-02 is served by the same program, which routes that card "
                     "to tests/sources/check/main_w0702.py because ops/ci/sources.py whitelists only W07-G01, "
                     "W07-G02 and an empty check id (measured: forwarding a card id refuses with unbound W07 "
                     "selection). argv, env and timeout are unchanged.")

out = json.dumps(data, indent=1, ensure_ascii=False) + tail
after = json.loads(out)
after_cmds = after.get("commands") or after
original = json.loads(raw)
original_cmds = original.get("commands") or original
assert json.dumps(after_cmds[KEY]["argv"], ensure_ascii=False) == before_argv, "argv moved"
assert list(after_cmds.keys()) == before_order, "key order changed"
assert after_cmds[KEY]["selectors"]["check_id"] == old_list + [NEW_CHECK], "not append-only"
assert json.dumps({k: v for k, v in after_cmds.items() if k != KEY}, sort_keys=True, ensure_ascii=False) == \
       json.dumps({k: v for k, v in original_cmds.items() if k != KEY}, sort_keys=True, ensure_ascii=False), \
       "another selector changed"
assert len(after_cmds) == len(original_cmds), "a key appeared or disappeared"

tmp = P + ".t.tmp"
io.open(tmp, "w", encoding="utf-8", newline="\n").write(out)
os.replace(tmp, P)

final = json.loads(io.open(P, encoding="utf-8").read())
final_cmds = final.get("commands") or final
print("revision", rev_before, "->", final.get("revision"), "| keys", len(final_cmds))
print("check_id roster now", final_cmds[KEY]["selectors"]["check_id"])
print("argv unchanged", json.dumps(final_cmds[KEY]["argv"], ensure_ascii=False) == before_argv)
print("sha256 before", hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],
      "| after", hashlib.sha256(io.open(P, "rb").read()).hexdigest()[:16])
