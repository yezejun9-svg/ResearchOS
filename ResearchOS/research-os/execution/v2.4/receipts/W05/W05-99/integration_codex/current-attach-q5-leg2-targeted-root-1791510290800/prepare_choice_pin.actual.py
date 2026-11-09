import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent/"source.integration.choice.json"
S=P.parent/"validate_current_attach_q5_legacy.actual_owned.py"
compile(S.read_bytes(),str(S),"exec")
b=P.read_bytes();print(json.dumps({"path":str(P),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}))
