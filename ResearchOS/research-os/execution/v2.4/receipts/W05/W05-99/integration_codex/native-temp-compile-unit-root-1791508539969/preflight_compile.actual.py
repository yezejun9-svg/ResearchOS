import hashlib,json
from pathlib import Path
P=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-compile-unit-root-1791508539969/validate_native_temp_compile_units.actual_owned.py")
raw=P.read_bytes()
compile(raw,str(P),"exec")
base=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-compile-root-458f017f3c294bb6/validate_native_ttl_compile.actual_owned.py")
assert hashlib.sha256(base.read_bytes()).hexdigest()==hashlib.sha256(Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-compile-root-458f017f3c294bb6/validate_native_ttl_compile.actual_owned.py").read_bytes()).hexdigest()
print(json.dumps({"status":"SCRIPT_SYNTAX_VALID_NO_ACTUAL_EXECUTION","script_ref":{"path":str(P),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}}))
