from pathlib import Path
import hashlib,json,types
O=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/session_expired_writer_attach_fixture_independent_review_codex/5f3e09c72caf4d1991adf5174a87b19e")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(p,v):
 with p.open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((O/"input-pins.json").read_text(encoding="utf-8"))
gr=next(r for r in refs if "source_read_guard_revision_v2_codex" in r["path"] and r["path"].endswith("source_read_guard.py"))
raw=Path(gr["path"]).read_bytes();assert len(raw)==gr["bytes"] and hashlib.sha256(raw).hexdigest()==gr["sha256"]
module=types.ModuleType("verified_guard");exec(compile(raw,gr["path"],"exec"),module.__dict__)
guard=module.SourceReadGuard()
try:
 guard.acquire(refs)
 copies=json.loads((O/"input-copy-index.json").read_text(encoding="utf-8"))
 for row in copies:assert Path(row["copy"]["path"]).read_bytes()==guard.get_buffer(row["source"]["path"])
finally:
 closure=guard.close();save(O/"sourceguard.final.json",closure)
 assert closure["verification"]=="PASSED" and closure["closed"] and closure["retained_handles_count"]==0 and not closure["errors"]
exclude=["HDF.json","MF.json","postseal-tool-io.json"]
members={str(p.relative_to(O)).replace("\\","/"):pin(p) for p in sorted(O.rglob("*")) if p.is_file() and p.name not in exclude}
save(O/"MF.json",{"schema":"researchos.expired-writer-source-independent-review-manifest.v1","authority":"NONE","formal_acceptance":False,"members":members,"exclusions":exclude})
subject=next(r for r in refs if "session_expired_writer_attach_fixture_revision_codex" in r["path"] and r["path"].endswith("HDF.json"))
hdf={"schema":"researchos.expired-writer-source-independent-review-handoff.v1","decision":"SOURCE_ONLY_APPROVE_NO_NEW_SOURCE_BLOCKER","verdict":"APPROVE","authority":"NONE","formal_acceptance":False,"production_ready":False,"build_verified":False,"test_actual":"OPEN_PENDING_ROOT_EXECUTION","actor":"codex:/root/typed_fixture_source_review","namespace":str(O),"STOP":True,"subject_hdf":subject,"manifest_ref":pin(O/"MF.json"),"manifest_member_count":len(members),"report_ref":pin(O/"report.md"),"static_checks_ref":pin(O/"static-independent-checks.json"),"guard_ref":pin(O/"sourceguard.final.json"),"input_count":len(refs),"input_copy_count":len(copies),"original_io_ref":pin(O/"tool-io.json"),"critical":[],"important":[],"suggestions":[],"mechanical_failures":[{"ordinal":857,"outer":0,"markedPython":1,"native":None,"ref":pin(O/"failure-origin.857.json")}],"inherited_failures":[853,854,855],"inherited_failures_counted_again":False,"failure_counter_reset":False,"scope":"one legacy test body; no production edit or actual runtime acceptance","open":["Root isolated composition/build/original-test execution","fresh restore positive","shared TEXT whole-chain","active asynchronous takeover","historical cached ACK reconciliation"]}
save(O/"HDF.json",hdf)
print(json.dumps({"HDF":pin(O/"HDF.json"),"MF":pin(O/"MF.json"),"members":len(members),"report":pin(O/"report.md"),"guard":pin(O/"sourceguard.final.json"),"failure":pin(O/"failure-origin.857.json"),"input_count":len(refs),"copies":len(copies),"guard_closed":True},ensure_ascii=False,indent=2))

