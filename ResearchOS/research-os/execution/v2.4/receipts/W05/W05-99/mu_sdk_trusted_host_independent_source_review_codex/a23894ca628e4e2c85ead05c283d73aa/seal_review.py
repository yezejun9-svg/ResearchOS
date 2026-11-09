from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
 raw=p.read_bytes();return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
i=json.loads((O/"intake.json").read_text(encoding="utf-8"))
for ref in i["files"]:
 actual=meta(Path(ref["path"]))
 assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"],ref["path"]
 snap=meta(O/ref["snapshot"]);assert snap["sha256"]==ref["sha256"] and snap["bytes"]==ref["bytes"]
m={"schema":"researchos.independent-host-source-review-manifest.v1","decision":"REQUEST_CHANGES","blocking_findings":["R1","R2","R3","R4"],"suggestions":["S1"],"source_and_main_recheck":"PASS","candidate_execution":"NOT_RUN","files":[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p.name!="manifest.json"]}
(O/"manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"files":len(m["files"]),"handoff":meta(O/"HANDOFF.md"),"review":meta(O/"REVIEW.md"),"manifest":meta(O/"manifest.json")},ensure_ascii=False))

