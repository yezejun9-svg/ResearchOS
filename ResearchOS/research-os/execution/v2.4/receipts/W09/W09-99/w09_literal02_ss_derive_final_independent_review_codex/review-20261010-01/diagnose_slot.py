import hashlib
import json
from pathlib import Path
R = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
decision = json.loads((HERE / "decision.json").read_bytes())
guard = json.loads((HERE / "SourceGuard.closed.json").read_bytes())
cp_path = R / "execution/v2.4/checkpoint.json"
raw = cp_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != "f7a2027f5fe21fe5b0524d1731eba7304327e067f0ea937489b234e07dc2983e":
    raise ValueError("CP398 pin mismatch")
cp = json.loads(raw)
hits = []
def find(value, pointer=""):
    if type(value) is dict:
        for key, child in value.items():
            child_pointer = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            if key == "w09_root_delivery_capture_index_ref":
                hits.append({"pointer": child_pointer, "parent_type": type(value).__name__, "value": child})
            find(child, child_pointer)
    elif type(value) is list:
        for index, child in enumerate(value):
            find(child, pointer + "/" + str(index))
find(cp)
result = {"original1262": {"actual_outer_exit": 1, "actual_python_exit": 1, "checks_passed_count": len(decision["checks"]), "last_passed_check": decision["checks"][-1], "original_error": decision["primary_error"], "SourceGuard_closed": guard["closed"], "retained_handles_count": guard["retained_handles_count"], "errors": guard["errors"]}, "cp_artifacts_actual_type": type(cp["artifacts"]).__name__, "actual_slot_hits": hits}
data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
with (HERE / "slot-diagnosis.json").open("xb") as stream:
    stream.write(data)
print(json.dumps({"diagnosis_ref": {"path": str(HERE / "slot-diagnosis.json"), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}, "result": result}, ensure_ascii=False))
print("ROOT_PYTHON_EXIT=0")
