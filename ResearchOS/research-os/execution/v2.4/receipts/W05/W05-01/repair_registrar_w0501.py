"""Repair register_w0501_accepted.py precisely: replace ONE stale disclosed_incident string run and add the
missing registrable name. Line-bounded, because an earlier attempt keyed on 'the next line starts with a
quote' and swallowed the closing entry of the enclosing dict, which broke the file's syntax.
"""
import io

P = r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-01/register_w0501_accepted.py"
NL = chr(10)
Q = chr(34)

lines = io.open(P, encoding="utf-8").read().split(NL)
start = [i for i, l in enumerate(lines) if "W0501-RUN-EVENT-AND-COST-CORRELATION is disclosed as unmet" in l]
assert len(start) == 1, start
a = start[0]

def is_segment(l):
    t = l.strip()
    return t.startswith(Q) and (t.endswith(Q) or t.endswith(Q + ",")) and "}" not in t and "]" not in t

b = a
# a segment of a continued string ends with a bare quote and no comma; a finished list entry ends with quote-comma
while b + 1 < len(lines) and not lines[b].strip().endswith(Q + ","):
    b += 1
    if lines[b].strip().endswith("}") or lines[b].strip().endswith("]"):
        raise SystemExit("span ran past the list entry at line %d" % (b + 1))
assert b - a < 6, "span too long: %d lines" % (b - a)
span = lines[a:b + 1]
assert 1 <= len(span) <= 4, [len(span)] + [s[:60] for s in span]
assert all(is_segment(s) for s in span), span

new = ("   " + Q + "position as of round 2, dated here because this array is append-only and later windows inherit it: "
 "W0501-RUN-EVENT-AND-COST-CORRELATION was disclosed as unmet because the adapter journal and the domain Run never met. "
 "From round 5 they meet inside W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL, whose Run id, task id and lease epoch come from the "
 "claimed domain Run and whose ledger reservation key must equal the fixture dispatch key, and M21 and M22 kill it. Only the "
 "service-launched event ledger stays blocked by runtime qualification" + Q + ",")
lines[a:b + 1] = [new]
s = NL.join(lines)

old_accepts = Q + "ACCEPT_WITH_RESERVATIONS" + Q + ")"
assert s.count(old_accepts) == 1, s.count(old_accepts)
s = s.replace(old_accepts, Q + "ACCEPTED" + Q + ", " + Q + "ACCEPT_WITH_RESERVATIONS" + Q + ")")
assert Q + "ACCEPTED" + Q + ", " in s

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("registrar repaired: span of %d line(s) replaced, ACCEPTED added to ACCEPTS" % len(span))
