"""Hold and release finite Source inputs; never acquire Canon or live run state."""
import hashlib
import json
from pathlib import Path
import types

N = Path(__file__).resolve().parent
OLD = N.parent / "fullw09-20261010-02"
REVIEW = N.parent.parent / "full_w09_main_native_producer_independent_source_review_codex" / "review-fullw09-20261010-02"

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

choice = json.loads((N / "source.choice.json").read_bytes())
guard_ref = choice["common"]["guard_ref"]
assert pin(guard_ref["path"]) == guard_ref
module = types.ModuleType("full_w09_v3_source_guard")
module.__file__ = guard_ref["path"]
exec(compile(Path(guard_ref["path"]).read_bytes(), module.__file__, "exec"), module.__dict__)

names = (
    "full_w09_runtime.source.py", "runtime-overrides.source.py",
    "full_w09_launcher.source.py", "prepare_full_w09.source.py",
    "run_full_w09.source.py", "source.choice.json",
    "root-calling-contract.json", "compiler-source-blueprint.json",
    "build_v3.py", "source-v3-rebase.json", "source_guard_v3.py",
)
refs = [pin(N / name) for name in names]
refs += [pin(OLD / "HDF.json"), pin(OLD / "MF.json"), pin(OLD / "peer-audit-controls.json"),
         pin(REVIEW / "HDF.json"), pin(REVIEW / "MF.json"), pin(REVIEW / "source-review-decision.json")]
held = module.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=512 * 1024 * 1024)
try:
    held.acquire(refs)
finally:
    closed = held.close()
assert closed.get("closed") is True and closed.get("retained_handles_count") == 0 and not closed.get("errors")

record = {
    "schema": "researchos.fullw09-v3-source-guard-closure.v1",
    "scope": "FINITE_SOURCE_INPUTS_ONLY",
    "held_input_refs": refs,
    "guard_ref": guard_ref,
    "cleanup": closed,
    "Canon_handles": 0,
    "Native_calls": 0,
    "Go_calls": 0,
    "prepare_run_calls": 0,
    "formal_acceptance": False,
}
path = N / "source-guard.closed.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"ref": pin(path), "held_inputs": len(refs), "retained_handles": closed["retained_handles_count"]}, ensure_ascii=False))
