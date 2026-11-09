import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent/"failure-origin.845.json"
b=p.read_bytes()
print(json.dumps({"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)},ensure_ascii=True))

