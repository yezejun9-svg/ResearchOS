"""One-shot Source-only correction of relocated proposal pin comparison."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
sealer_path = P / "make_packet_v4.py"
ledger_path = P / "original-failure-ledger.json"
failure_path = P / "original-tool-failures-v4.md"
before = sealer_path.read_bytes()
old = b'assert pin(after) == prior_mf["target_after"]["execution/v2.4/formal_case_index.py"]\n'
new = (b'prior_index_ref = prior_mf["target_after"]["execution/v2.4/formal_case_index.py"]\n'
       b'assert pin(Path(prior_index_ref["path"])) == prior_index_ref\n'
       b'assert {key: pin(after)[key] for key in ("sha256", "bytes")} == {\n'
       b'    key: prior_index_ref[key] for key in ("sha256", "bytes")}\n')
assert before.count(old) == 1
candidate = before.replace(old, new, 1)
member_old = b'    "original-failure-ledger.json", "apply_v4_source.py", "add_v4_controls.py", "make_packet_v4.py",\n'
member_new = (b'    "original-failure-ledger.json", "original-tool-failures-v4.md",\n'
              b'    "apply_v4_source.py", "add_v4_controls.py", "fix_sealer_ref_v4.py", "make_packet_v4.py",\n')
assert candidate.count(member_old) == 1
candidate = candidate.replace(member_old, member_new, 1)
ast.parse(candidate, filename=str(sealer_path))

ledger_before = ledger_path.read_bytes()
ledger = json.loads(ledger_before)
assert ledger["new_original_failures_this_v4_source_packet"] == []
failure_raw = failure_path.read_bytes()
ledger["new_original_failures_this_v4_source_packet"] = [{
    "root_global_ordinal": 985,
    "path": str(failure_path.resolve(strict=True)),
    "sha256": hashlib.sha256(failure_raw).hexdigest(),
    "bytes": len(failure_raw),
    "outer_exit": 1,
    "python_exit": 1,
    "native_go_dispatcher_model_exits": None,
}]
ledger_candidate = (json.dumps(ledger, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
assert sealer_path.read_bytes() == before and ledger_path.read_bytes() == ledger_before
sealer_path.write_bytes(candidate)
ledger_path.write_bytes(ledger_candidate)
assert sealer_path.read_bytes() == candidate and ledger_path.read_bytes() == ledger_candidate
print("V4_RELOCATED_PIN_AND_ORIGIN_LEDGER_AST_PASS")
