import hashlib
import json
from pathlib import Path

R = Path("D:/作品集/ResearchOS/research-os")
S = R / "execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009"
RUN = R / "execution/v2.4/receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01"
HERE = Path(__file__).resolve().parent
paths = {
    "commit": S / "ss-append-literal02-actual-root-20261010-01/committed.json",
    "before": S / "ss-append-literal02-actual-root-20261010-01/step_state.before.raw.json",
    "desired": S / "ss-append-literal02-actual-root-20261010-01/step_state.desired.json",
    "intent": S / "ss-append-literal02-actual-root-20261010-01/intent.json",
    "append_guard": S / "ss-append-literal02-actual-root-20261010-01/source-guard.closed.json",
    "derive": RUN / "derive-7f3a638965a04675ac21860b0e09f01e/result.json",
    "precheck": RUN / "check-9482e0c14ee24c5fa7f24855f8dfc27a/result.json",
    "ss": R / "execution/v2.4/step_state.json",
    "cp": R / "execution/v2.4/checkpoint.json",
    "ow": R / "execution/v2.4/path_ownership.json",
    "cm": R / "execution/v2.4/commands.json",
    "index": R / "execution/v2.4/root_delivery_captures/W09/W09-99/index.json",
    "append_audit": S / "w09.literal02-ss-append-actual.actual-audit.root.json",
    "derive_audit": S / "w09.literal02-derive-actual.actual-audit.root.json",
}
def describe(value, depth=0):
    if type(value) is dict:
        if depth >= 2:
            return {"type": "dict", "key_count": len(value), "keys_first_twenty": list(value)[:20]}
        return {key: describe(item, depth + 1) for key, item in value.items()}
    if type(value) is list:
        return {"type": "list", "length": len(value), "first": describe(value[0], depth + 1) if value else None}
    if type(value) is str and len(value) > 500:
        return {"type": "str", "length": len(value)}
    return value
records = {}
for name, path in paths.items():
    raw = path.read_bytes()
    doc = json.loads(raw)
    ref = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    records[name] = {"ref": ref, "shape": describe(doc)}
    if name == "derive":
        records[name]["case_summary"] = {key: describe(value) for key, value in doc.items() if key != "dependency_snapshot"}
    if name in ("append_audit", "derive_audit"):
        original_ref = doc["original_capture_ref"]
        original_path = Path(original_ref["path"])
        original = original_path.read_bytes()
        lines = original.splitlines(keepends=True)
        records[name]["original_pin_exact"] = len(original) == original_ref["bytes"] and hashlib.sha256(original).hexdigest() == original_ref["sha256"]
        entries = [json.loads(line) for line in lines]
        records[name]["original_shape"] = [{"type": entry.get("type"), "timestamp": entry.get("timestamp"), "ordinal": entry.get("ordinal"), "payload_keys": list(entry.get("payload", {})), "payload_type": entry.get("payload", {}).get("type"), "tool_name": entry.get("payload", {}).get("name"), "call_id": entry.get("payload", {}).get("call_id")} for entry in entries]
        last = entries[-1]["payload"]
        records[name]["last_output_prefix"] = str(last.get("output", ""))[:2500]
raw = (json.dumps(records, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
with (HERE / "input-shapes.json").open("xb") as stream:
    stream.write(raw)
print(json.dumps({"input_shapes_ref": {"path": str(HERE / "input-shapes.json"), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}, "records": records}, ensure_ascii=False))
print("ROOT_PYTHON_EXIT=0")
