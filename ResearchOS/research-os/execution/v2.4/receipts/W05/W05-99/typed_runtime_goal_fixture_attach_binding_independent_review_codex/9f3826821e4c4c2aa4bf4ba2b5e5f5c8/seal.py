from pathlib import Path
import hashlib,json,types
O=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_attach_binding_independent_review_codex/9f3826821e4c4c2aa4bf4ba2b5e5f5c8")
def pin(p):
 b=p.read_bytes()
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(p,x):
 with p.open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
refs=json.loads((O/"input-pins.json").read_text(encoding="utf-8"))
guardref=next(r for r in refs if r["path"].endswith("source_read_guard.py") and "source_read_guard_revision_v2_codex" in r["path"])
raw=Path(guardref["path"]).read_bytes()
assert len(raw)==guardref["bytes"] and hashlib.sha256(raw).hexdigest()==guardref["sha256"]
mod=types.ModuleType("verified_source_guard");exec(compile(raw,guardref["path"],"exec"),mod.__dict__)
g=mod.SourceReadGuard()
try:
 g.acquire(refs)
 copies=json.loads((O/"input-copy-index.json").read_text(encoding="utf-8"))
 for row in copies:
  assert Path(row["copy"]["path"]).read_bytes()==g.get_buffer(row["source"]["path"])
 print("FINAL_INPUTS_MATCH",len(refs),"COPIES_MATCH",len(copies))
finally:
 closure=g.close()
 save(O/"sourceguard.final.json",closure)
 assert closure["verification"]=="PASSED" and closure["closed"] and not closure["errors"] and closure["retained_handles_count"]==0
exclusions=["HDF.json","MF.json","postseal-tool-io.json"]
members={str(p.relative_to(O)).replace("\\","/"):pin(p) for p in sorted(O.rglob("*")) if p.is_file() and p.name not in exclusions}
mf={"schema":"researchos.q5-source-independent-review-manifest.v1","authority":"NONE","formal_acceptance":False,"members":members,"exclusions":exclusions,"reason":"HDF pins MF; own seal/verification tool output necessarily excluded and independently pinned in final delivery"}
save(O/"MF.json",mf)
hdf={"schema":"researchos.q5-source-independent-review-handoff.v1","decision":"SOURCE_ONLY_APPROVE_NO_NEW_SOURCE_BLOCKER","verdict":"APPROVE","actor":"codex:/root/typed_fixture_source_review","authority":"NONE","formal_acceptance":False,"production_ready":False,"build_verified":False,"tests_executed":False,"STOP":True,"namespace":str(O),
"subject_hdf":next(r for r in refs if r["path"].endswith("HDF.json") and "attach_binding_revision_codex" in r["path"]),
"subject_manifest":next(r for r in refs if r["path"].endswith("MF.json") and "attach_binding_revision_codex" in r["path"]),
"manifest_ref":pin(O/"MF.json"),"manifest_member_count":len(members),"report_ref":pin(O/"report.md"),"static_checks_ref":pin(O/"static-independent-checks.json"),"sourceguard_final_ref":pin(O/"sourceguard.final.json"),"input_refs_count":len(refs),"input_copies_count":len(copies),"original_tool_io_ref":pin(O/"tool-io.json"),"mechanical_failures":[{"ordinal":848,"outer":0,"markedPython":1,"native":None,"ref":pin(O/"failure-origin.848.json")},{"ordinal":852,"outer":0,"markedPython":1,"native":None,"ref":pin(O/"failure-origin.852.json")}],"inherited845_counted_again":False,"failure_counter_reset":False,
"original_totals":{"calls":181,"tests":20,"assertion_or_error_if":196,"strict_t_assertion_if":190},"unchanged_helper_prefix_bytes":24950,"Goal_byte_equal":True,"new_negative_modes":[17,7],"critical":[],"important":[],"suggestions":[{"id":"Q5-SUG-001","file":"runtime_typed_client_fixture_windows_test.go","line":867,"description":"Optional future high-int64 full snapshot projection regression; current >2^53 tuple test is not end-to-end JSON evidence."}],
"remaining_open":["separate legacy ACK expectation correction","active asynchronous takeover","historical cached ACK terminal reconciliation","true fresh restore positive","shared TEXT-dependent whole-chain acceptance","fresh isolated build and original/new actual tests and descendant closure"]}
save(O/"HDF.json",hdf)
print(json.dumps({"HDF":pin(O/"HDF.json"),"MF":pin(O/"MF.json"),"member_count":len(members),"report":pin(O/"report.md"),"guard":pin(O/"sourceguard.final.json"),"failures":[pin(O/"failure-origin.848.json"),pin(O/"failure-origin.852.json")]},ensure_ascii=False,indent=2))

