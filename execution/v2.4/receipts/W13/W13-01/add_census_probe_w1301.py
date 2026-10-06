"""Add the missing probe to audit_receipt_w1301.py: verify the census digests against the bytes on disk.

The round-1 review found that this auditor exited 0 without ever recomputing the stream digests the census
quotes, which made "0 inconsistencies" mean less than it appeared to. The new probe (a) checks every row's
stdout/stderr digest against sha256 over the file bytes, (b) requires at least one non-empty stdout so the probe
cannot be satisfied by empty files alone - the old bug survived precisely because empty streams hash identically
under either rule - and (c) runs a positive control: a deliberately falsified row must be reported as
mismatching, otherwise the probe proves nothing.
"""
import io, os

NL = chr(10)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, *[".."] * 5))
P = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01", "audit_receipt_w1301.py")
s = io.open(P, encoding="utf-8").read()

probe = '''# 9 - the census digests must verify against the bytes on disk, not against a re-encoded copy of them.
# This probe exists because the round-1 review found the auditor skipped it while claiming the census.
cen_rows = load(os.path.join(RD, "c23_forwarded_flake_census.json"))["rows"]
non_empty_stdout = 0
for row in cen_rows:
    base = os.path.dirname(row["receipt_path"])
    for kind, field in (("stdout", "stdout_sha256"), ("stderr", "stderr_sha256")):
        p = os.path.join(base, kind + ".txt")
        b = open(p, "rb").read() if os.path.exists(p) else b""
        chk(hashlib.sha256(b).hexdigest() == row[field],
            "census row %s: %s digest does not verify against the raw bytes" % (row["invocation_id"][:8], kind))
        if kind == "stdout" and len(b) > 0:
            non_empty_stdout += 1
            if "stdout_bytes" in row:
                chk(row["stdout_bytes"] == len(b), "census row %s reports %s stdout bytes, the file holds %d"
                    % (row["invocation_id"][:8], row.get("stdout_bytes"), len(b)))
chk(non_empty_stdout > 0, "every census stdout is empty, so the digest check above could not detect an "
                          "encoding mistake - the original bug hid behind empty files")


def census_digests_verify(rows):
    """True only when every named stream hashes the same as the recorded digest."""
    for row in rows:
        base = os.path.dirname(row["receipt_path"])
        for kind, field in (("stdout", "stdout_sha256"), ("stderr", "stderr_sha256")):
            p = os.path.join(base, kind + ".txt")
            b = open(p, "rb").read() if os.path.exists(p) else b""
            if hashlib.sha256(b).hexdigest() != row[field]:
                return False
    return True


tampered = [dict(r) for r in cen_rows]
tampered[0]["stdout_sha256"] = hashlib.sha256(b"not the recorded bytes").hexdigest()
chk(not census_digests_verify(tampered),
    "positive control failed: the census probe accepts a falsified digest, so it proves nothing")
chk(census_digests_verify(cen_rows), "the census on disk does not verify even though the row loop above said it did")

'''

anchor = 'print(json.dumps({"receipt": os.path.relpath'
assert s.count(anchor) == 1, "final print not found in the auditor"
s = s.replace(anchor, probe + anchor, 1)
io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("auditor gained the census-digest probe plus a positive control")
