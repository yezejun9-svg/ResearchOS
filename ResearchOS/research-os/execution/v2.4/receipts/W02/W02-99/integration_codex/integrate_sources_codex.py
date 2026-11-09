"""Integrate only the frozen W02 receipt-contained implementation."""
from pathlib import Path
import hashlib
import json
import subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
REV="b2f8f0d60ca7cd5728c9cab47f22dd9eda602df6"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
prefix="execution/v2.4/receipts/W02/W02-99/"
names=subprocess.check_output(["git","diff-tree","--no-commit-id","--name-only","-r",REV],cwd=ROOT,text=True).splitlines()
assert len(names)==313 and all(name.startswith(prefix) for name in names)
assert not any(name.startswith(prefix+"integration_codex/") or name.startswith(prefix+"independent-review-codex/") for name in names)
protected=["execution/v2.4/commands.json","execution/commands.json","execution/v2.4/path_ownership.json","execution/path_ownership.json","execution/v2.4/checkpoint.json","execution/v2.4/step_state.json","apps/cli/build_check.py","ops/ci/build.py","execution/command_dispatcher/dispatch.py"]
before={name:sha(ROOT / name) for name in protected}
result=subprocess.run(["git","cherry-pick",REV],cwd=ROOT,capture_output=True)
(HERE / "cherry_pick.stdout.txt").write_bytes(result.stdout)
(HERE / "cherry_pick.stderr.txt").write_bytes(result.stderr)
assert result.returncode==0,result.stderr.decode("utf-8","replace")
assert before=={name:sha(ROOT / name) for name in protected}
assert sha(ROOT / (prefix+"dispatch_parent.py"))=="4d8e4f843cd7cea15e21eb250c732a5553a33cb8b23a54cc109d21335ee1681b"
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
(HERE / "source_integration_codex.json").write_text(json.dumps(dict(status="PASS_SOURCE_INTEGRATION",worker_commit=REV,main_commit=head,owned_files=313,protected_hashes_unchanged=before,product_source_changes=0,registry_changes=0,card_accepted=False),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status="PASS",main_commit=head,owned_files=313,product_changes=0,card_accepted=False)))
