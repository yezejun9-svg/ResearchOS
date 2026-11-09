import hashlib
import json
import pathlib
import re


ROOT = pathlib.Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_maintenance_c57_codex\20261025-current-chat")
OUT = ROOT / "C51-DIAGNOSTIC-LEDGER-RECONSTRUCTED-86.jsonl"


def file_ref(path):
    raw = path.read_bytes()
    return {"name": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


events = []
for number in range(1, 18):
    prefix = f"{number:03d}"
    files = sorted(path for path in ROOT.iterdir() if path.is_file() and
                   (path.name.startswith(prefix + ".") or path.name.startswith(prefix + "-")))
    events.append({
        "schema": "researchos.c51-diagnostic-event.v1", "kind": "early_numbered_command",
        "ordinal": number, "native_exit_persisted": False, "native_exit": None,
        "files": [file_ref(path) for path in sorted(set(files))],
        "capture_gap": "early run did not persist a separate numeric exit file; do not infer one from raw output",
        "cause": "009 package-wide go fmt formatted 20 out-of-scope files; exact HEAD-byte restore and 40-pin verification are recorded in FORMAT-DIAGNOSTIC.md" if number == 9 else None,
    })

interim = (ROOT / "INTERIM-C57-TEST-LEDGER.md").read_text(encoding="utf-8")
for number, target, observed in re.findall(r"^\| (\d+) \| (.*?) \| (.*?) \|$", interim, flags=re.MULTILINE):
    events.append({
        "schema": "researchos.c51-diagnostic-event.v1", "kind": "interim_tool_observation",
        "ordinal": int(number), "description": target, "observed_exit_text": observed,
        "native_exit_persisted": False, "native_exit": None,
        "evidence": "INTERIM-C57-TEST-LEDGER.md",
        "capture_gap": "tool result was observed, but recipe/raw/exit were not redirected at invocation; later numbered receipts are separate evidence",
        "counting_policy": "diagnostic only; overlapping numbered commands do not add another failure count",
    })

causes = {
    19: "initial store fixture missing the schema24 barrier; fixed and rerun at 020",
    32: "clean isolated 085b baseline reproduces old schema22 handler/fixture mismatch; 033 repairs exact old-state fixture",
    39: "legacy CLI test expected late Host error, but new shared reader rejects incomplete replacement journal at root lease; exact earlier error expectation corrected at 047",
}
for number in range(18, 50):
    prefix = f"{number:03d}-"
    files = sorted(path for path in ROOT.iterdir() if path.is_file() and path.name.startswith(prefix))
    exit_files = [path for path in files if path.name.endswith((".exit.txt", ".native-exit.txt"))]
    if len(exit_files) != 1:
        raise RuntimeError(f"expected one numeric exit capture for {number}: {exit_files}")
    exit_text = exit_files[0].read_text(encoding="utf-8").strip()
    if exit_text not in {"0", "1"}:
        raise RuntimeError(f"unexpected native exit {number}: {exit_text!r}")
    events.append({
        "schema": "researchos.c51-diagnostic-event.v1", "kind": "numbered_command",
        "ordinal": number, "native_exit_persisted": True, "native_exit": int(exit_text),
        "files": [file_ref(path) for path in files],
        "environment_scope": "TEMP/TMP/GOTMPDIR not explicitly within registered own fixture root; diagnostic" if 34 <= number <= 41 else
                             "registered own fixture root explicit" if 42 <= number <= 49 else "not independently captured in these fields",
        "cause": causes.get(number),
    })

OUT.write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events), encoding="utf-8")
print(json.dumps({"events": len(events), "numbered": 32, "interim": len(events) - 49,
                  "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(), "path": str(OUT)}))
