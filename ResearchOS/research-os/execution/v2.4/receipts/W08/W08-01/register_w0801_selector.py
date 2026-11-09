"""Register the W08-01 verification selector in the shared v2.4 command registry.

Guards, in order: the key must be absent (idempotence, including under --dry-run), the registry revision and plan
hash must be what was measured, every pre-existing key's serialised form must be byte-identical after the edit, and
the file must keep its byte convention (UTF-8 without BOM, indent=1, ensure_ascii=False, no trailing newline).
"""
import json
import os
import sys

REG = "execution/v2.4/commands.json"
EXPECTED_REVISION = 19
EXPECTED_PLAN = "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17"
KEY = "test.research.fixture"


def fail(message):
    sys.stderr.write("REFUSED: %s\n" % message)
    raise SystemExit(2)


def main():
    dry = "--dry-run" in sys.argv[1:]
    raw = open(REG, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        fail("registry carries a BOM; the measured convention is UTF-8 without one")
    if raw.endswith(b"\n"):
        fail("registry ends with a newline; the measured convention has none")
    before = json.loads(raw.decode("utf-8"))

    if KEY in before["commands"]:
        fail("%s already registered at revision %s - refusing to overwrite" % (KEY, before["revision"]))
    if before["revision"] != EXPECTED_REVISION:
        fail("registry revision is %s, expected %s (another writer moved it)" % (before["revision"], EXPECTED_REVISION))
    if before["plan_sha256"] != EXPECTED_PLAN:
        fail("plan_sha256 mismatch, refusing to write against a different plan")

    template = before["commands"]["test.domain"]
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in before["commands"].items()}

    entry = {
        "state": "BOUND",
        "executable_tool": template["executable_tool"],
        "cwd": template["cwd"],
        "platforms": list(template["platforms"]),
        "required_env": [],
        "allowed_env": list(template["allowed_env"]),
        "fixed_env": dict(template["fixed_env"]),
        "tool_env": {},
        "timeout_seconds": template["timeout_seconds"],
        "argv": ["run", "./tests/research/check"],
        "selectors": {"task_id": ["W08"], "check_id": ["W08-01"]},
        "assertion_field": "assertion_ids",
        "owner_card": "W08-01",
        "note": (
            "registered by W08-01: check_id W08-01 is served by tests/research/check/main.go, which drives the "
            "production HTTP+SQLite handler for the frozen ReuseDecisionPayload guard, the four-stage projection, the "
            "durable record path and the J01 judge-before-reusing gate. The program reads RESEARCHOS_TASK_ID / "
            "RESEARCHOS_CHECK_ID, which the dispatcher injects from the selectors, and refuses any binding other than "
            "W08/W08-01 as assertion W0801-ROUTING-TRUTH-TABLE. This key did not exist before this card: the plan "
            "lists it for W08-01, W08-02, W08-99 and W09-99, and those selectors are NOT claimed here - dispatching "
            "them resolves the key and is refused on the selector check, which is asserted in the receipt rather "
            "than assumed. argv, env and timeout are copied from the accepted test.domain entry so the toolchain is "
            "the same locked one."
        ),
        "expected_artifacts": [
            "tests/research/check/main.go",
            "internal/domain/adoption.go",
            "internal/api/contracts/client.protocol.schema.json",
        ],
    }

    after = json.loads(json.dumps(before, ensure_ascii=False))
    after["commands"][KEY] = entry
    after["revision"] = EXPECTED_REVISION + 1

    for name, serialised in snapshot.items():
        if json.dumps(after["commands"][name], ensure_ascii=False, sort_keys=True) != serialised:
            fail("pre-existing selector %s changed; aborting" % name)
    if len(after["commands"]) != len(snapshot) + 1:
        fail("command count moved by more than one")

    blob = json.dumps(after, ensure_ascii=False, indent=1).encode("utf-8")

    if dry:
        sys.stdout.write(json.dumps({"dry_run": True, "would_write_bytes": len(blob),
                                     "key_added": KEY, "revision": after["revision"],
                                     "selectors": entry["selectors"]}, ensure_ascii=False) + "\n")
        return

    tmp = REG + ".w0801.tmp"
    with open(tmp, "wb") as handle:
        handle.write(blob)
    check = json.loads(open(tmp, "rb").read().decode("utf-8"))
    if check["revision"] != EXPECTED_REVISION + 1 or KEY not in check["commands"]:
        fail("staged file does not round-trip the intended edit")
    if len(check["commands"]) != len(snapshot) + 1:
        fail("staged file changes the selector roster")
    for name, serialised in snapshot.items():
        if json.dumps(check["commands"][name], ensure_ascii=False, sort_keys=True) != serialised:
            fail("staged file rewrites pre-existing selector %s" % name)
    os.replace(tmp, REG)
    sys.stdout.write(json.dumps({"written": True, "revision": after["revision"], "key_added": KEY,
                                 "bytes": len(blob), "pre_existing_untouched": len(snapshot)},
                                ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
