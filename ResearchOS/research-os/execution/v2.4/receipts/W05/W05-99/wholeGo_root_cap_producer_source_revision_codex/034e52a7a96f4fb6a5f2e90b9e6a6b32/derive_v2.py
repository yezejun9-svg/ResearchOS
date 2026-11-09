"""Pure IO/AST minimal revision; does not import or execute the producer."""
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
old = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_preparation_codex/a378e6d62865446ab78312d5efabb458/wholego_cap_metadata.proposed.py")
old_raw = old.read_bytes()
original = old_raw.decode("utf-8")
before = '''    heartbeat_path = canonical(meter["heartbeat_path"])
    heartbeat = unique_json(heartbeat_path.read_bytes())
    require(heartbeat.get("schema") == "researchos.current58-whole-go-meter-heartbeat.v1" and
            heartbeat.get("run_uuid") == uuid and heartbeat.get("active") is True and
            type(heartbeat.get("observed_unix")) in (int, float), "ACTIVE_HEARTBEAT_OPEN")
    age = time.time() - heartbeat["observed_unix"]
    require(0 <= age <= 5, "METER_HEARTBEAT_STALE")'''
after = '''    heartbeat_path = canonical(meter["heartbeat_path"])
    require(ROOT in heartbeat_path.parents, "METER_HEARTBEAT_FOREIGN")
    heartbeat = unique_json(heartbeat_path.read_bytes())
    require(heartbeat.get("schema") == "researchos.current58-whole-go-meter-heartbeat.v1" and
            heartbeat.get("run_uuid") == uuid and heartbeat.get("active") is True and
            type(heartbeat.get("monotonic_tick")) in (int, float), "ACTIVE_HEARTBEAT_OPEN")
    age = time.monotonic() - heartbeat["monotonic_tick"]
    require(0 <= age <= 5, "METER_HEARTBEAT_STALE")'''
assert original.count(before) == 1
revised = original.replace(before, after)
ast.parse(revised)
compile(revised, str(here / "wholego_cap_metadata.v2.proposed.py"), "exec", dont_inherit=True)
with (here / "wholego_cap_metadata.v2.proposed.py").open("xb") as out:
    out.write(revised.encode("utf-8"))
def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
inverse = {"schema": "researchos.current58-whole-go-cap-producer-source-inverse.v2",
           "old_ref": pin(old), "new_ref": pin(here / "wholego_cap_metadata.v2.proposed.py"),
           "exact_old_block": before, "exact_new_block": after,
           "reverse_rule": "Replace the one exact_new_block with exact_old_block; all other bytes unchanged.",
           "main_modified": False}
with (here / "source-inverse.json").open("xb") as out:
    out.write((json.dumps(inverse, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"new_ref": inverse["new_ref"], "inverse_ref": pin(here / "source-inverse.json")}, ensure_ascii=False))
