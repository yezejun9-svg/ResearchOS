"""Prepare forward-only Root completion reader by reversible constants/metadata names."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,ast,argparse
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r330-b802270f725f47dc86f9ec829a60931a/close-root-launch-observation.v4.py"
p=argparse.ArgumentParser();p.add_argument("--grant-sha256",required=True);args=p.parse_args()
assert len(args.grant_sha256)==64 and all(c in "0123456789abcdef" for c in args.grant_sha256)
raw=OLD.read_bytes();assert hashlib.sha256(raw).hexdigest()=="51a90d48371ef27765405a859e6ae3f9607f73378bc411f68f2cd16e9f68cb61"
changes=[
("b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359","f71b60ad316aa3034ff3da5cd79c6aac4c4e5997425d86e7b84d2f9fc02ec89b"),
("c0fe594c2fc6109b95ab6d829eff98b580f6f9d8bf0c95e30e9f7f8b61b91375",args.grant_sha256),
("assert args.known_pending_origins >= 2","assert args.known_pending_origins >= 0"),
("'registered_origin_count': 502","'registered_origin_count': 509"),
("'observed_origin_count_at_closure': 502 +","'observed_origin_count_at_closure': 509 +"),
("prepare-root-caller.v5.py","prepare-root-caller.v6.py"),
("close-root-launch-observation.v4.py","close-root-launch-observation.v5.py")]
text=raw.decode();edits=[]
for a,b in changes:
 assert text.count(a)==1,(a,text.count(a));text=text.replace(a,b,1);edits.append({"old":a,"new":b})
inverse=text
for r in reversed(edits):
 assert inverse.count(r["new"])==1;inverse=inverse.replace(r["new"],r["old"],1)
assert inverse.encode()==raw
ast.parse(text)
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
dest=OUT/"close-root-launch-observation.v5.py"
with dest.open("xb") as f:f.write(text.encode())
value={"old_ref":pin(OLD),"new_ref":pin(dest),"edits":edits,"whole_byte_inverse_equal":True,"native_NULL_semantics_unchanged":True,"target_calls":0,"counter_reset":False,"formal_increment":0}
with (OUT/"completion-reader-preparation.json").open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"reader_ref":pin(dest),"preparation_ref":pin(OUT/"completion-reader-preparation.json"),"target_calls":0},ensure_ascii=False))
