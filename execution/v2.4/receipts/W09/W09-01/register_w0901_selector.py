"""Register the W09-01 verification selector in the shared v2.4 command registry (rev 20 -> 21).

Guards, in the order the earlier rounds demanded: the key must be absent (idempotence, including under --dry-run), the
registry revision and plan hash must be what was measured, every pre-existing key's serialised form must be
byte-identical after the edit, the file must keep its byte convention (UTF-8 without BOM, indent=1, ensure_ascii=False,
no trailing newline), and the staged file is re-read and re-verified before os.replace. The selectors claim ONLY
task_id W09 / check_id W09-01; W09-02 and W09-99 appear in the plan for this key and are deliberately not claimed.
"""
import json
import os
import sys

REG = os.path.join("execution", "v2.4", "commands.json")
EXPECTED_REVISION = 20
EXPECTED_PLAN = "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17"
KEY = "test.retrieval"
TEMPLATE_KEY = "test.domain"


def fail(message):
    sys.stderr.write("REFUSED: %s\n" % message)
    raise SystemExit(2)


def main():
    dry = "--apply" not in sys.argv
    raw = open(REG, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        fail("registry carries a BOM; the measured convention is UTF-8 without one")
    if raw.endswith(b"\n"):
        fail("registry ends with a newline; the measured convention has none")
    before = json.loads(raw.decode("utf-8"))
    if KEY in before["commands"]:
        fail("%s already registered at revision %s" % (KEY, before["revision"]))
    if before["revision"] != EXPECTED_REVISION:
        fail("registry revision is %s, expected %s (another writer moved it)" % (before["revision"], EXPECTED_REVISION))
    if before["plan_sha256"] != EXPECTED_PLAN:
        fail("plan_sha256 mismatch, refusing to write against a different plan")
    template = before["commands"].get(TEMPLATE_KEY)
    if not template:
        fail("template key %s is gone" % TEMPLATE_KEY)

    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in before["commands"].items()}
    entry = {
        "state": "BOUND",
        "executable_tool": "python",
        "cwd": template["cwd"],
        "platforms": list(template["platforms"]),
        "required_env": [],
        "allowed_env": list(template["allowed_env"]),
        "fixed_env": dict(template["fixed_env"]),
        "tool_env": {},
        "timeout_seconds": template["timeout_seconds"],
        "argv": ["-X", "utf8", "tests/evidence/check/main.py"],
        "selectors": {"task_id": ["W09"], "check_id": ["W09-01"]},
        "assertion_field": "assertion_ids",
        "owner_card": "W09-01",
        "note": (
            "registered by W09-01: check_id W09-01 is served by tests/evidence/check/main.py, which drives the real "
            "domain evidence and retrieval path through go test -json over internal/domain and reports the W0901-* "
            "roster it observes; it reads RESEARCHOS_TASK_ID / RESEARCHOS_CHECK_ID as injected by the dispatcher and "
            "answers no other binding, asserted by its own routing rows plus a depth-capped self-probe. This key did "
            "not exist before this card and the plan also lists it for W09-02 and W09-99: those selectors are NOT "
            "claimed here, and dispatching them resolves the key and is refused on the selector check. argv, env and "
            "timeout are copied from the accepted test.domain entry so the toolchain is the same locked one; the "
            "handler resolves go from execution/toolchains/locked.json and refuses a PATH fallback."
        ),
        "expected_artifacts": [
            "tests/evidence/check/main.py",
            "internal/domain/evidence_w0901_test.go",
            "internal/domain/retrieval.go",
            "internal/domain/retrieval_local.go",
            "adapters/retrieval/local.go",
        ],
    }
    after = json.loads(json.dumps(before, ensure_ascii=False))
    after["commands"][KEY] = entry
    after["revision"] = EXPECTED_REVISION + 1
    for name, serialised in snapshot.items():
        if json.dumps(after["commands"][name], ensure_ascii=False, sort_keys=True) != serialised:
            fail("pre-existing selector %s changed" % name)
    if len(after["commands"]) != len(snapshot) + 1:
        fail("command count moved by more than one")
    blob = json.dumps(after, ensure_ascii=False, indent=1).encode("utf-8")

    if dry:
        sys.stdout.write(json.dumps({"dry_run": True, "key_added": KEY, "revision": after["revision"],
                                     "argv": entry["argv"], "selectors": entry["selectors"],
                                     "would_write_bytes": len(blob)}, ensure_ascii=False) + "\n")
        return
    tmp = REG + ".w0901.tmp"
    with open(tmp, "wb") as handle:
        handle.write(blob)
    check = json.loads(open(tmp, "rb").read().decode("utf-8"))
    if check["revision"] != EXPECTED_REVISION + 1 or KEY not in check["commands"]:
        fail("staged file does not round-trip the intended edit")
    for name, serialised in snapshot.items():
        if json.dumps(check["commands"][name], ensure_ascii=False, sort_keys=True) != serialised:
            fail("staged file rewrites pre-existing selector %s" % name)
    os.replace(tmp, REG)
    sys.stdout.write(json.dumps({"written": True, "revision": after["revision"], "key_added": KEY,
                                 "pre_existing_untouched": len(snapshot), "bytes": len(blob)},
                                ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
