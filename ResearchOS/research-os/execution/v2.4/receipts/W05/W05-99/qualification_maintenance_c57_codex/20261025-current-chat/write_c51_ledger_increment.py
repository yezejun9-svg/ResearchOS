import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
current = root / "C51-DIAGNOSTIC-LEDGER.jsonl"
reconstructed = root / "C51-DIAGNOSTIC-LEDGER-RECONSTRUCTED-86.jsonl"
old_hash = "ee17964a2dec0902a1cbbefc3f227a2953054e5a175d6914a58c179bdecee939"
current_hash = "a203004e23dd3b26d4508a7680808a0e083bec924f93f6359f3e08698829c6e7"
if hashlib.sha256(current.read_bytes()).hexdigest() != current_hash or len(current.read_bytes().splitlines()) != 89:
    raise RuntimeError("current 89-line derived ledger changed")
if hashlib.sha256(reconstructed.read_bytes()).hexdigest() != old_hash or len(reconstructed.read_bytes().splitlines()) != 86:
    raise RuntimeError("reconstructed 86-line ledger did not match prior declared hash")

incident = {
    "schema": "researchos.c51-ledger-rewrite-incident.v1",
    "status": "DERIVED_LEDGER_REWRITE_ERROR_RECONSTRUCTED_SEPARATELY",
    "observed_by": "Root audit049",
    "original_declared_86_sha256": old_hash,
    "reconstructed_86": {"path": reconstructed.name, "sha256": old_hash, "derivation": "initial generator clauses recovered from this chat and original unchanged raw command receipts"},
    "current_89": {"path": current.name, "sha256": current_hash, "lines": 89, "preserved": True},
    "cause": "Regenerating for numbered 050-052 added source_version_note:null to all older numbered events and changed the shared environment expression, so the original 86-line prefix was rewritten.",
    "native_source_record_policy": "No raw command, stdout, stderr, native exit, or older derived ledger file was altered to fabricate history.",
    "subsequent_policy": "New diagnostics use new suffixed increment files; both existing derived ledger versions remain unchanged.",
}
with (root / "C51-LEDGER-REWRITE-INCIDENT.json").open("x", encoding="utf-8") as file:
    file.write(json.dumps(incident, ensure_ascii=False, indent=2) + "\n")

files = []
for suffix in ("recipe.txt", "stdout.raw", "stderr.raw", "native-exit.txt"):
    path = root / ("053-c51-patch-check." + suffix)
    raw = path.read_bytes()
    files.append({"name": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
if (root / "053-c51-patch-check.native-exit.txt").read_text(encoding="ascii").strip() != "0":
    raise RuntimeError("053 native exit differs")
increment = {"schema": "researchos.c51-diagnostic-increment.v1", "kind": "numbered_command", "ordinal": 53,
             "action": "read-only git apply --cached --check --whitespace=error on C51 patch", "native_exit": 0,
             "files": files, "previous_derived_ledger": current.name, "previous_sha256": current_hash}
with (root / "C51-DIAGNOSTIC-INCREMENT-053.jsonl").open("x", encoding="utf-8") as file:
    file.write(json.dumps(increment, ensure_ascii=False, sort_keys=True) + "\n")
print(json.dumps({"incident_sha256": hashlib.sha256((root / "C51-LEDGER-REWRITE-INCIDENT.json").read_bytes()).hexdigest(),
                  "increment_sha256": hashlib.sha256((root / "C51-DIAGNOSTIC-INCREMENT-053.jsonl").read_bytes()).hexdigest()}))
