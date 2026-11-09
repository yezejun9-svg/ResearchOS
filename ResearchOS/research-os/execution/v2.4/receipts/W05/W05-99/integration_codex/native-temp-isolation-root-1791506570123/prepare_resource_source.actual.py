import sys,json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os")
old=R/"execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-isolation-root-29cb40af6a46453a/prepare_native_ttl_isolation.actual_owned.py"
old_guard=json.loads(old.with_name("source-guard.cleanup.actual.json").read_bytes())
refs=[ref for ref in old_guard["entries"] if Path(ref["path"]).resolve()==old.resolve()]
assert len(refs)==1 and refs[0]["closed"] and refs[0]["verified"]
raw=old.read_bytes();assert hashlib.sha256(raw).hexdigest()==refs[0]["sha256"] and len(raw)==refs[0]["bytes"]
changes=[
(b"codex-w0599-native-ttl-c54ba9df088e45ea94adb56457af2979",b"codex-w0599-native-temp-1791506570123"),
(b'["revision"]==358',b'["revision"]==360'),
(b'370c3b73f630a952a80c9082b27ed09e28278cc79bdf65bfbe453c317cb42064',b'685545935a0da0bf576eb28ada59f453beb9d26628af4f656faf18f94d336d56'),
(b"revision=358",b"revision=360")]
new=raw
for a,b in changes:
 assert new.count(a)==1;new=new.replace(a,b)
inverse=new
for a,b in reversed(changes):
 assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==raw
out=Path(__file__).resolve().parent/"prepare_native_temp_isolation.actual_owned.py"
with out.open("xb") as f:f.write(new)
proof=dict(schema="researchos.root-resource-template-inverse.v1",base_ref=refs[0],source_ref=dict(path=str(out),sha256=hashlib.sha256(new).hexdigest(),bytes=len(new)),exact_inverse=True,changes=4,formal_acceptance=False)
with out.with_name("isolation-source.template.proof.json").open("xb") as f:f.write((json.dumps(proof,ensure_ascii=True,indent=2)+"\n").encode())
print(json.dumps(dict(source_ref=proof["source_ref"],exact_inverse=True)),flush=True)
