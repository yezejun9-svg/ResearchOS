"""Read-only registry snapshot before root serial parent-selector integration."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
v24_path=ROOT / "execution/v2.4/commands.json"
legacy_path=ROOT / "execution/commands.json"
current=json.loads(v24_path.read_bytes())
legacy=json.loads(legacy_path.read_bytes())
target=HERE / "binding_baseline_codex.json"
assert not target.exists()
assert current["revision"] == 34 and len(current["commands"]) == 31
record=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), actor="codex:/root", status="READ_ONLY_PRE_BINDING_BASELINE", source_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(), commands_revision=34, v24_registry_sha256=sha(v24_path), legacy_registry_sha256=sha(legacy_path), v24_decoded_commands=current["commands"], original_v24_build_entry=current["commands"]["build.check"], original_legacy_build_entry=legacy["commands"]["build.check"], protected_source_hashes={name:sha(ROOT / name) for name in ["execution/command_dispatcher/dispatch.py", "apps/cli/build_check.py", "ops/ci/build.py", "execution/toolchains/locked.json", "execution/v2.4/client_mapping.json"]}, intended_mutation="Root may change only v24 build.check entry to current strict parent bridge and compatibility superset; other30 existing v24 decodedentries, original legacy registry and handlers remain unchanged.", new_tests_gui_provider_service_calls=0)
target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status="PASS",baseline_sha256=sha(target),old_v24_entries=31,legacy_bytes_preserved=True)))
