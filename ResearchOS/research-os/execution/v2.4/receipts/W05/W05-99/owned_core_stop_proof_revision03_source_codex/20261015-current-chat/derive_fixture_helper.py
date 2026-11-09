"""Derive an isolated CP516 fixture harness from the frozen CP508 recipe."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
old = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\owned_core_stop_anchor_revision02_source_codex\20261015-current-chat\fixture_e2e_r2.py")
new = root / "fixture_e2e_r3.py"
old_raw = old.read_bytes()
before = new.read_bytes()
if before != old_raw:
    raise SystemExit("initial helper copy diverged from frozen source")
source = before.decode("utf-8")
for old_text, new_text in (
    ("owned-core-stop-anchor-r2-20261015", "owned-core-stop-proof-r3-20261015"),
    ("owned-core-stop-20261015-tmp", "owned-core-stop-proof-r3-20261015-tmp"),
    ("fixture-r2.exe", "fixture-r3.exe"),
):
    if old_text not in source:
        raise SystemExit("required harness token absent: " + old_text)
    source = source.replace(old_text, new_text)
new_raw = source.encode("utf-8")
new.write_bytes(new_raw)
(root / "helper-lineage-initial.json").write_text(json.dumps({
    "source_path": str(old), "source_sha256": hashlib.sha256(old_raw).hexdigest(),
    "derived_path": str(new), "derived_initial_sha256": hashlib.sha256(new_raw).hexdigest(),
    "replacements": ["worktree", "task temporary root", "fixture exe name"]
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(hashlib.sha256(new_raw).hexdigest())
