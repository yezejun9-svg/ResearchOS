import hashlib
import json
import pathlib
import sys

repo = pathlib.Path(r"D:\作品集\ResearchOS\research-os")
scope_path = repo / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp529/source43-resume-scope.json"
worktree = repo / ".local/worktrees/source43-b-stop-finalpath-20261015"
scope = json.loads(scope_path.read_text(encoding="utf-8"))

def digest(path):
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def main():
    mode = sys.argv[1]
    if mode == "pins":
        mismatches = []
        for name, pin in scope["mechanical_source41_pins"].items():
            got = digest(worktree / name)
            if got["sha256"] != pin["sha256"] or got["bytes"] != pin["bytes"]:
                mismatches.append({"path": name, "expected": pin, "actual": got})
        print(json.dumps({"count": len(scope["mechanical_source41_pins"]), "mismatches": mismatches}, ensure_ascii=False, indent=2))
        return int(bool(mismatches))
    if mode == "manifest":
        data = {name: digest(worktree / name) for name in scope["source_allowlist"]}
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    if mode == "names":
        actual = [line.split("\t", 1)[1] for line in pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if "\t" in line]
        expected = scope["source_allowlist"]
        print(json.dumps({"actual_count": len(actual), "expected_count": len(expected), "missing": sorted(set(expected)-set(actual)), "extra": sorted(set(actual)-set(expected)), "duplicates": len(actual)-len(set(actual))}, ensure_ascii=False, indent=2))
        return int(set(actual) != set(expected) or len(actual) != len(expected))
    if mode == "scopehash":
        print(json.dumps(digest(scope_path), indent=2))
        return 0
    if mode == "show":
        print(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
        return 0
    if mode == "slice":
        lines = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
        lo, hi = int(sys.argv[3]), int(sys.argv[4])
        for i in range(lo, min(hi, len(lines)) + 1):
            print(f"{i}: {lines[i-1]}")
        return 0
    if mode == "gojson":
        events = [json.loads(line) for line in pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if line.startswith("{")]
        for event in events:
            if event.get("Action") in ("fail", "skip"):
                print(json.dumps(event, ensure_ascii=False))
                if event.get("Test"):
                    for detail in events:
                        if detail.get("Action") == "output" and detail.get("Test") == event["Test"]:
                            print(detail.get("Output", "").rstrip())
        print(json.dumps({"runs": sum(e.get("Action") == "run" for e in events), "test_passes": sum(e.get("Action") == "pass" and bool(e.get("Test")) for e in events), "test_fails": sum(e.get("Action") == "fail" and bool(e.get("Test")) for e in events), "skips": sum(e.get("Action") == "skip" for e in events)}, ensure_ascii=False))
        return 0
    if mode == "gocases":
        events = [json.loads(line) for line in pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if line.startswith("{")]
        prefix = sys.argv[3]
        for event in events:
            if event.get("Action") in ("pass", "fail", "skip") and event.get("Test", "").startswith(prefix):
                print(f"{event['Action']} {event['Test']}")
        return 0
    raise SystemExit(f"unknown mode: {mode}")

if __name__ == "__main__":
    raise SystemExit(main())
