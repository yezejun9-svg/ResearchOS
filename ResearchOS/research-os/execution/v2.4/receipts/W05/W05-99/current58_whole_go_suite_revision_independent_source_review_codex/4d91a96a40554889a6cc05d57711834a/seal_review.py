from pathlib import Path
import hashlib,json,ast
OUT=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_revision_independent_source_review_codex/4d91a96a40554889a6cc05d57711834a")
assert OUT.resolve()==OUT and OUT.name=="4d91a96a40554889a6cc05d57711834a"
def pin(path):
    data=path.read_bytes()
    return {"path":str(path).replace("\\","/"),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
def verify(ref):
    now=pin(Path(ref["path"]))
    assert now["sha256"]==ref["sha256"] and now["bytes"]==ref["bytes"],ref["path"]
    return now
def exclusive_copy(before,after):
    raw=(OUT/before).read_bytes()
    with (OUT/after).open("xb") as stream:stream.write(raw)
    assert (OUT/after).read_bytes()==raw
    return pin(OUT/after)
def put(name,value):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    with (OUT/name).open("xb") as stream:stream.write(raw)
    return pin(OUT/name)
draft=json.loads((OUT/"review.json").read_bytes())
assert draft["actor_id"]=="codex:/root/f08_whole_scope_review" and draft["decision"]=="REQUEST_CHANGES"
frozen=[verify(ref) for ref in draft["reviewed_inputs"].values()]
selected_review=exclusive_copy("review.json","review.final.json")
selected_report=exclusive_copy("REPORT.md","REPORT.final.md")
selected_audit=exclusive_copy("audit.json","audit.final.json")
names=["review.final.json","REPORT.final.md","audit.final.json","review.json","REPORT.md","audit.json","tool-observations.original.json","tool-observations.construction.json","seal_review.py"]
members=[pin(OUT/name) for name in names]
mf=put("manifest.json",{"schema":"researchos.current58-whole-go-revision-independent-review-manifest.v1","namespace":str(OUT).replace("\\","/"),"stage":"SOURCE_PREPARATION_ONLY","decision":"REQUEST_CHANGES","member_count":len(members),"members":members,"source_acceptance":False,"whole58_qualified":False,"formal_case_accepted_delta":0,"candidate_executed":False,"new_tool_failure_origins":0})
handoff=put("handoff.json",{"schema":"researchos.current58-whole-go-revision-independent-review-handoff.v1","status":"STOPPED","actor_id":draft["actor_id"],"decision":"REQUEST_CHANGES","requested_changes":draft["requested_changes"],"review_ref":selected_review,"report_ref":selected_report,"audit_ref":selected_audit,"manifest_ref":mf,"selected_review_report_audit_manifest_handoff_creation":"xb; no existing file overwritten","construction_drafts_preserved":[pin(OUT/n) for n in ["review.json","REPORT.md","audit.json"]],"frozen_input_refs":frozen,"build_verified":False,"candidate_executed":False,"Go_Node_model_Git_CAS_calls":0,"canonical_changed":False,"source_acceptance":False,"whole58_qualified":False,"formal_case_accepted_delta":0,"new_tool_failure_origins":0,"author_origins_inherited_not_recounted":["e31944","73eee6"],"next":"New immutable author revision for R1/R2/R3, independent static re-review; actual Root literals, source/cap review, registration/lease/grant and native qualification remain OPEN."})
for ref in frozen:verify(ref)
for ref in members:assert pin(Path(ref["path"]))==ref
print(json.dumps({"status":"STOPPED","decision":"REQUEST_CHANGES","review":selected_review,"report":selected_report,"audit":selected_audit,"manifest":mf,"handoff":handoff,"members":len(members),"all_frozen_pins_verified":len(frozen),"new_tool_failure_origins":0},ensure_ascii=False))
