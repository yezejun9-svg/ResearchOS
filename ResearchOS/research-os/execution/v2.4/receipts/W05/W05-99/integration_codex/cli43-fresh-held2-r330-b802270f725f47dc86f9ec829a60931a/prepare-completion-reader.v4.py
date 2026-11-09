"""Prepare a forward-only completion reader from immutable r329 source; pure byte/AST IO."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,ast
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/close-root-launch-observation.v3.py"
raw=OLD.read_bytes();assert hashlib.sha256(raw).hexdigest()=="ea68bdc60eb31dc07e101e177a0cd318206550bbe82cbdcd074a6aeb5fcf2a04"
changes=[
("90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0","b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359"),
("55efa0fbd05a9776fa2fcf5c12f360c8846cd39695c4c0f34a9fea7813631221","c0fe594c2fc6109b95ab6d829eff98b580f6f9d8bf0c95e30e9f7f8b61b91375"),
("assert args.known_pending_origins >= 3","assert args.known_pending_origins >= 2"),
("'registered_origin_count': 481","'registered_origin_count': 502"),
("'observed_origin_count_at_closure': 481 +","'observed_origin_count_at_closure': 502 +"),
("prepare-root-caller.v4.py","prepare-root-caller.v5.py"),
("close-root-launch-observation.v3.py","close-root-launch-observation.v4.py")]
text=raw.decode();facts=[]
for a,b in changes:
 assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b,1);facts.append({"old":a,"new":b})
inverse=text
for c in reversed(facts):
 assert inverse.count(c["new"])==1;inverse=inverse.replace(c["new"],c["old"],1)
assert inverse.encode()==raw
ast.parse(text)
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
new=OUT/"close-root-launch-observation.v4.py"
with new.open("xb") as f:f.write(text.encode())
value={"old_ref":pin(OLD),"new_ref":pin(new),"edits":facts,"whole_byte_inverse_equal":True,"native_NULL_semantics_unchanged":True,"target_calls":0,"counter_reset":False,"formal_increment":0}
with (OUT/"completion-reader-preparation.json").open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"reader_ref":pin(new),"preparation_ref":pin(OUT/"completion-reader-preparation.json"),"target_calls":0},ensure_ascii=False))
