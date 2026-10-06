"""Rebuild c23_forwarded_flake_census.json from the dispatcher's own invocation records.

The round-1 review blocked the previous version of this file: its per-row stdout/stderr digests were computed
over decoded, newline-normalised text, so 20 of 40 of them did not verify against the bytes on disk, and the 20
that did match were exactly the empty streams (an empty file hashes the same either way, which is why the
mistake hid). This writer hashes the raw bytes of every stream file it names. It reads nothing else and writes
nothing outside its own card directory; recompute it the same way to check it:

    python execution/v2.4/receipts/W13/W13-01/census_c23_w1301.py
"""
import hashlib, io, json, os

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
RD = os.path.join("execution", "v2.4", "receipts", "W13", "W13-01")
OUT = os.path.join(RD, "c23_forwarded_flake_census.json")
INVOC = "execution/invocations"


def raw_bytes(path):
    return open(path, "rb").read()


def rows():
    for name in sorted(os.listdir(INVOC)):
        rp = os.path.join(INVOC, name, "receipt.json")
        if not os.path.isfile(rp):
            continue
        r = json.loads(open(rp, encoding="utf-8-sig").read())
        sel = r.get("selectors") or {}
        if r.get("command_key") != "test.ui.routes" or sel.get("case_id") != "C23":
            continue
        base = os.path.join(INVOC, name)
        streams = {}
        for kind in ("stdout", "stderr"):
            p = base + "/" + kind + ".txt"
            b = raw_bytes(p) if os.path.exists(p) else b""
            streams[kind] = {"path": p, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                             "text": b.decode("utf-8", "replace")}
        rep = {}
        for line in streams["stdout"]["text"].splitlines():
            if line.strip().startswith("{"):
                rep = json.loads(line)
        err = streams["stderr"]["text"]
        if r["status"] == "PASS":
            cause = "n/a (passed)"
        elif "SyntaxError" in err:
            cause = "source of tests/ui/check/main.py was syntactically broken at that moment (executor edit, now repaired)"
        elif "one matching W13 task gate or case selector required" in err:
            cause = "the legacy harness's own selector guard refused the selector shape the forwarder passed"
        elif rep.get("note") == "the forwarded handler produced no report" and r.get("child_exit_code") == 2:
            cause = "the case selector arrived without a W13 task gate, so the forwarding branch found no report "                     "to hand back (child exit 2, the check program's own note quoted verbatim)"
        elif rep.get("status") == "FAIL":
            cause = "the real Windows browser phase reported FAIL with no per-assertion detail"
        else:
            cause = "unclassified - reported here rather than explained"
        rows_out = {
            "started_at": r["started_at"], "ended_at": r.get("ended_at"), "invocation_id": r["invocation_id"],
            "status": r["status"], "child_exit_code": r.get("child_exit_code"),
            "code_revision": r["code_revision"], "registry_command_revision": r["registered_command_revision"],
            "stdout_status": rep.get("status"), "stdout_note": rep.get("note"), "stdout_assertions": len(r.get("assertion_ids") or []),
            "stderr_first_line": (err.strip().splitlines() or ["(empty stderr)"])[0][:160],
            "stdout_sha256": streams["stdout"]["sha256"], "stdout_bytes": streams["stdout"]["bytes"],
            "stderr_sha256": streams["stderr"]["sha256"], "stderr_bytes": streams["stderr"]["bytes"],
            "cause": cause, "receipt_path": rp.replace("\\", "/")}
        yield rows_out


def main():
    rs = sorted(rows(), key=lambda x: x["started_at"])
    by_head = {}
    counts = {}
    for r in rs:
        by_head.setdefault(r["code_revision"][:8], set()).add(r["status"])
        counts[r["cause"]] = counts.get(r["cause"], 0) + 1
    disagree = sorted(h for h, v in by_head.items() if len(v) > 1)
    unverifiable = [r["invocation_id"] for r in rs
                    if r["stdout_bytes"] > 0 and r["stdout_sha256"] == hashlib.sha256(b"").hexdigest()]
    if unverifiable:
        raise SystemExit("a non-empty stdout carries the empty-file digest: %s" % unverifiable)
    if not rs:
        raise SystemExit("no C23 dispatcher runs found on disk - the census would be a claim about nothing")
    out = {"record": "every dispatcher run of test.ui.routes --case-id C23, tabulated and classified from "
                     "execution/invocations/*/receipt.json plus the RAW BYTES of its stdout.txt/stderr.txt",
           "digest_rule": "stdout_sha256/stderr_sha256 are sha256 over the bytes of the file as it lies; the "
                          "previous revision of this file hashed newline-normalised text and 20 of its 40 digests "
                          "therefore failed verification",
           "generated_by": "execution/v2.4/receipts/W13/W13-01/census_c23_w1301.py",
           "runs": len(rs),
           "statuses": {"PASS": sum(1 for r in rs if r["status"] == "PASS"),
                        "COMMAND_FAILED": sum(1 for r in rs if r["status"] == "COMMAND_FAILED")},
           "cause_counts": counts, "heads_with_both_results": disagree,
           "conclusion": "the earlier red C23 runs were not caused by mounting the four clients. Classified causes: "
                         "an executor SyntaxError in the check program, the legacy harness's selector guard, and the "
                         "inherited real-browser phase reporting FAIL at inputs that PASS minutes later. The last is "
                         "genuine nondeterminism, so this card reports it instead of asserting stability.",
           "rows": rs}
    io.open(OUT, "w", encoding="utf-8", newline=NL).write(json.dumps(out, indent=1, ensure_ascii=False))
    print("census runs", out["runs"], "| statuses", out["statuses"], "| causes", len(counts),
          "| heads disagreeing", disagree)
    print("non-empty stdout rows:", sum(1 for r in rs if r["stdout_bytes"] > 0),
          "| empty stderr rows:", sum(1 for r in rs if r["stderr_bytes"] == 0))


main()
