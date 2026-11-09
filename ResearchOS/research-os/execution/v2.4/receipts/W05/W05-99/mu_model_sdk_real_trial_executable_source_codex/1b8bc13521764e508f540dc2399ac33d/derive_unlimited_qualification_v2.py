"""Derive the selected no-duplicate-ledger candidate from v1, pure IO."""
import difflib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent
main = Path(r"D:\作品集\ResearchOS\research-os\internal\domain\runtime_qualification.go")
before = main.read_text(encoding="utf-8")
draft = (root / "runtime_qualification.unlimited.proposed.go").read_text(encoding="utf-8")
old = '''		_, err = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": requestID, "provider_event_id": requestID, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": Now()})
		return err
'''
new = '''		// The actual MODEL effect records UNKNOWN/money=nil in brokerEffect.
		// Do not create a second unresolved qualification-dispatch liability.
		return nil
'''
if draft.count(old) != 1:
    print(f"SOURCE_DRIFT matching old block={draft.count(old)}")
    raise SystemExit(0)
selected = draft.replace(old, new, 1)
with (root / "runtime_qualification.unlimited.v2.proposed.go").open("xb") as f:
    f.write(selected.encode("utf-8"))
diff = "".join(difflib.unified_diff(before.splitlines(True), selected.splitlines(True),
                                    fromfile="a/internal/domain/runtime_qualification.go",
                                    tofile="b/internal/domain/runtime_qualification.go"))
with (root / "runtime_qualification.unlimited.v2.patch").open("xb") as f:
    f.write(diff.encode("utf-8"))
print(f"SOURCE_V2_DERIVED bytes={len(selected.encode('utf-8'))}")
