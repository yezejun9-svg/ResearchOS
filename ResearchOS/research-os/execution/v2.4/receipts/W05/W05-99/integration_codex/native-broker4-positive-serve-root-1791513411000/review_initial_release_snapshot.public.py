import json,hashlib
from pathlib import Path
P=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-broker4-controller-config-root-1791513411000/controller-runtime/review-snapshot-release-4ac4b921ce4446f89115b2971dba47bd.json")
raw=P.read_bytes();assert(hashlib.sha256(raw).hexdigest(),len(raw))==("0840169e2cd3d543908623edebbc377ea009822d4d6b8e1c393cd7b725048dbb",705453)
v=json.loads(raw);out={"snapshot_keys":list(v)}
for key in ("phase","sign_kind","payload_ref","payload_sha256","document_destination","phase_ready_ref","measured_native_ids","current_live_test_observation"):
 if key in v:out[key]=v[key]
for key,value in v.items():
 if isinstance(value,dict):out[key+"_keys"]=list(value)
for key in ("payload","public_payload"):
 if key in v and isinstance(v[key],dict):
  out[key+"_summary"]={k:v[key][k] for k in v[key] if not isinstance(v[key][k],(dict,list))};out[key+"_keys"]=list(v[key])
print(json.dumps(out,ensure_ascii=True));print("ROOT_PYTHON_EXIT=0")


