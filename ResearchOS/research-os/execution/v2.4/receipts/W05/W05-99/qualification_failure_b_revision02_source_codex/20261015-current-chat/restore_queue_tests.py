import hashlib
import subprocess
from pathlib import Path

tree = Path(r"D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015")
target = tree / "internal/domain/runtime_command_queue_windows_test.go"
current = target.read_bytes()
anchor = b"func TestQualificationBrokerDrainRequiresEveryAdmittedCompletion"
position = current.find(anchor)
if position < 0 or current.count(anchor) != 1:
    raise SystemExit("registry test anchor unavailable")
base = subprocess.run(
    ["git", "show", "f48fca0e4013bda19913a34d91da0cd23157a08b:internal/domain/runtime_command_queue_windows_test.go"],
    cwd=tree, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
).stdout
for name in [b"TestRuntimeClientQueueActualMuSameProcess", b"TestRuntimeClientQueueActualMuCancelUnknownEffect", b"TestRuntimeClientQueueGoalCancelClaimOrdering", b"func testRuntimeClientQueueActual"]:
    if name not in base:
        raise SystemExit("old queue test/helper missing in base")
if anchor in base:
    raise SystemExit("registry anchor unexpectedly in base")
combined = base.rstrip(b"\r\n") + b"\n\n" + current[position:]
target.write_bytes(combined)
print("old_sha256=" + hashlib.sha256(base).hexdigest() + " combined_sha256=" + hashlib.sha256(combined).hexdigest() + " old_bytes=" + str(len(base)) + " combined_bytes=" + str(len(combined)))
