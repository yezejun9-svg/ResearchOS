"""Refresh the w0402Roster block in place from the ok()/skip() literals actually in the file.

Idempotent: replaces the existing block rather than inserting a second copy, so it can be re-run
after every edit that adds or renames an assertion id.
"""
import io
import re
import sys

P = "tests/context/check/w0402.go"
START = "var w0402Roster = []string{"

src = io.open(P, encoding="utf-8").read()
body = src
start = body.index(START)
end = body.index("\n}\n", start) + len("\n}\n")
old_block = body[start:end]

# scan everything except the roster block itself
scan_target = body[:start] + body[end:]
ids = []
for m in re.finditer(r'\b(?:ok|skip)\(\s*"([A-Z0-9][A-Z0-9\-]*)"', scan_target):
    if m.group(1) not in ids:
        ids.append(m.group(1))
if not ids:
    sys.exit("no assertion ids found; the scan pattern is wrong")

ctx = sorted(i for i in ids if i.startswith("CTX-"))
chg = sorted(i for i in ids if i.startswith("CHG-"))
# the floor's own two ids are deliberately outside the roster they police
floor = sorted(i for i in ids if i.startswith("W0402-"))
other = [i for i in ids if not i.startswith(("CTX-", "CHG-", "W0402-"))]
if other:
    sys.exit("unexpected id prefixes in w0402.go: %r" % other)
if len(floor) != 2:
    sys.exit("expected exactly 2 W0402- floor ids, found %r" % floor)

lines = [START, "\t// contextPhase"]
lines += ['\t"%s",' % i for i in ctx]
lines += ["\t// changePhase"]
lines += ['\t"%s",' % i for i in chg]
lines += ["}", ""]
new_block = "\n".join(lines)

out = body[:start] + new_block + body[end:]
io.open(P, "w", encoding="utf-8", newline="\n").write(out)

old_ids = set(re.findall(r'"([A-Z0-9][A-Z0-9\-]*)",', old_block))
new_ids = set(ctx) | set(chg)
print("roster: %d -> %d ids (%d CTX, %d CHG)" % (len(old_ids), len(new_ids), len(ctx), len(chg)))
print("added:  ", sorted(new_ids - old_ids))
print("removed:", sorted(old_ids - new_ids))
