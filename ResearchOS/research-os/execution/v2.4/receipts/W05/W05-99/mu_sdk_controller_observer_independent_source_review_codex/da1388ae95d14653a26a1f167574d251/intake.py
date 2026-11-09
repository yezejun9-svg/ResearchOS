import ast,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed")
def pin(p):
 r=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(r).hexdigest(),"bytes":len(r)}
H=B/"handoff.json";M=B/"manifest.json"
assert pin(H)["sha256"]=="6bf92b38135179e14a9b96f7a4d3e0d32dd9fcf9fb435d3f73f904e6827ec5ff" and pin(H)["bytes"]==2281
assert pin(M)["sha256"]=="de6dff5bf204d33723e6e1236a9522c43524ba2191ab425ae337990a253f67bd" and pin(M)["bytes"]==2544
manifest=json.loads(M.read_bytes());refs=[pin(H),pin(M)]+manifest["members"]
runner=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb/mu_sdk_trial.v8.proposed.py")
refs += [pin(runner),json.loads((B/"report.json").read_bytes())["derived_owned_base_ref"]]
assert refs[-2]["sha256"].startswith("5b112a") and refs[-2]["bytes"]==90096
rows=[]
for r in refs:
 p=Path(r["path"]);assert pin(p)==r
 raw=p.read_bytes();out=O/(r["sha256"]+".raw")
 if not out.exists():out.write_bytes(raw)
 assert out.read_bytes()==raw
 rows.append({"source_ref":r,"snapshot_ref":pin(out)})
for r in rows:assert pin(Path(r["source_ref"]["path"]))==r["source_ref"]
(O/"intake.json").write_text(json.dumps({"rows":rows,"input_drift":0,"candidate_imported":False,"candidate_executed":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"inputs":len(rows),"drift":0,"runner_ref":refs[-2],"owned_base_ref":refs[-1]},ensure_ascii=False))

