from pathlib import Path
import hashlib,json
ROOT=Path("D:/作品集/ResearchOS/research-os")
OUT=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_evidence_revision_independent_source_review_codex/29754be17e2e49f183866442b9c2f92b")
assert OUT.resolve()==OUT and OUT.name=="29754be17e2e49f183866442b9c2f92b"
def pin(path):
    raw=path.read_bytes()
    return {"path":str(path).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def exact(ref):
    actual=pin(Path(ref["path"]))
    assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"],ref["path"]
    return actual
def put(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")
    with (OUT/name).open("xb") as file:file.write(raw)
    return pin(OUT/name)
review=json.loads((OUT/"review.json").read_bytes())
assert review["decision"]=="REQUEST_CHANGES" and review["actor_id"]=="codex:/root/f08_whole_scope_review"
assert review["tool_failure_origins_new"]==0
verified=[exact(r) for r in review["reviewed_inputs"]+review["selected_source_refs"]]
names=["REPORT.md","audit.json","review.json","seal_review.py","tool-observations.original.json","tool-observations.additional.json","tool-observations.documents-write.json"]
members=[pin(OUT/name) for name in names]
manifest=put("manifest.json",{"schema":"researchos.w09-v4-independent-source-review-manifest.v1","namespace":str(OUT).replace("\\","/"),"member_count":len(members),"members":members,"stage":"SOURCE_PREPARATION_ONLY","decision":"REQUEST_CHANGES","formal_accepted_delta":0,"candidate_executed":False,"new_tool_failure_origins":0})
handoff=put("handoff.json",{"schema":"researchos.w09-v4-independent-source-review-handoff.v1","status":"STOPPED","decision":"REQUEST_CHANGES","actor_id":review["actor_id"],"review_ref":pin(OUT/"review.json"),"report_ref":pin(OUT/"REPORT.md"),"audit_ref":pin(OUT/"audit.json"),"manifest_ref":manifest,"reviewed_input_refs":verified,"candidate_executed":False,"build_verified":False,"canonical_changed":False,"formal_accepted_delta":0,"new_tool_failure_origins":0,"author_origins_inherited_not_recounted":[581,582,583,584],"earliest_seal_history":"UNRECOVERED_OPEN","next":"Root author fixes in new immutable namespace; fresh independent source review before any integration/execution."})
for r in members:assert pin(Path(r["path"]))==r
for r in verified:assert pin(Path(r["path"]))==r
print(json.dumps({"status":"STOPPED","decision":"REQUEST_CHANGES","review":pin(OUT/"review.json"),"report":pin(OUT/"REPORT.md"),"audit":pin(OUT/"audit.json"),"manifest":manifest,"handoff":handoff,"members":len(members),"frozen_refs_reverified":len(verified),"new_origins":0},ensure_ascii=False))
