from pathlib import Path
import hashlib
import json
import sys

directory = Path(__file__).parent / (sys.argv[1] if len(sys.argv) > 1 else "final_selected")
source = directory / "stdout.jsonl"
cases = {
    "draft": "TestW05CLIRealLocalGoalDraftBindingFixture",
    "blocked_replay_cas": "TestW05CLIRealLocalGoalBlockedAndReplayBindingFixture",
}
buffers = {name: bytearray() for name in cases}
counts = {name: 0 for name in cases}
for line in source.read_bytes().splitlines(keepends=True):
    event = json.loads(line)
    test = event.get("Test", "")
    for name, prefix in cases.items():
        if test == prefix or test.startswith(prefix + "/"):
            buffers[name].extend(line)
            counts[name] += 1
index = {"source": "stdout.jsonl", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "cases": {}}
for name, raw in buffers.items():
    if not raw:
        raise SystemExit("no events for " + name)
    path = directory / (name + ".jsonl")
    path.write_bytes(raw)
    index["cases"][name] = {"path": path.name, "test": cases[name], "events": counts[name], "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
(directory / "per-test-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
