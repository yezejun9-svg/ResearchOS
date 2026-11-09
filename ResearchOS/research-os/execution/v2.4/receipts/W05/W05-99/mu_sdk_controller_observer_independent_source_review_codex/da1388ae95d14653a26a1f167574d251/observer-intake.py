import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_job_observer_source_codex/8cf71287160941f3b841945dc02be134")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
expected={"handoff.json":("c360d417200a3ddba076a022494b1d1e028f025d74174a75fa486bab1b94c9d7",1572),"manifest.json":("b55317c49d092422b07854c8ee43d10fd9fd9c4b7bde40d600e03e3fa23e3de6",4547),"mu_sdk_job_observer.proposed.py":("b062be8b68d1b31b658ba79a20c890ce895009fc135c80ae8d33ed5b78d01fd0",27673)}
for n,(sha,size) in expected.items():assert pin(B/n)["sha256"]==sha and pin(B/n)["bytes"]==size
m=json.loads((B/"manifest.json").read_bytes());refs=[pin(B/"handoff.json"),pin(B/"manifest.json")]+m["members"]
rows=[]
for ref in refs:
 p=Path(ref["path"]);assert pin(p)==ref
 raw=p.read_bytes();snap=O/(ref["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(raw)
 assert snap.read_bytes()==raw
 rows.append({"source_ref":ref,"snapshot_ref":pin(snap)})
for row in rows:assert pin(Path(row["source_ref"]["path"]))==row["source_ref"]
(O/"observer-intake.json").write_text(json.dumps({"rows":rows,"drift":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"inputs":len(rows),"drift":0,"source_ref":pin(B/"mu_sdk_job_observer.proposed.py")},ensure_ascii=False))

