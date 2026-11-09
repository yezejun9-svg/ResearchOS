import json,hashlib
from pathlib import Path
p=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-broker4-controller-config-root-1791513411000/harness-facts/01-release.payload.json")
raw=p.read_bytes();assert(hashlib.sha256(raw).hexdigest(),len(raw))==("80bcdf1f5c798dc9014d5c374c5af5d9148f37e666852a57999f45ee7385702c",181961)
v=json.loads(raw);out={"keys":list(v)}
for k,x in v.items():
 if isinstance(x,dict):out[k+"_keys"]=list(x)
 elif isinstance(x,list):out[k+"_count"]=len(x)
 else:out[k]=x
print(json.dumps(out,ensure_ascii=True));print("ROOT_PYTHON_EXIT=0")


