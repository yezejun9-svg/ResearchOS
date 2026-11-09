import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99"
paths=[
B/"checkpoint_r357_independent_review_codex/1a11db9e0dff7ad081d6e06d/original-tool-io.json",
B/"integration_codex/root-read-diagnostic-819-native-source-name-07c3c79d/failure-origin.819.json",
B/"integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f/failure-origin.820.closed-qualified.json",
B/"integration_codex/root-inspection-diagnostic-821-sharing-a51cfb0f/failure-origin.821.json",
B/"native_migration_credential_ttl_revision_codex/1a11dd62452c7c895d4e2f51/diagnostic-822.json",
B/"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/failure-origin.823.json",
B/"native_migration_ttl_independent_review_codex/1a11ddd38bb-fa0099f8/diagnostics.json"]
result=[]
for path in paths:
 raw=path.read_bytes();result.append({"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
print(json.dumps(result,ensure_ascii=True),flush=True)
