import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).parent
B=N.parents[1]
R1=B/"historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check"
def pin(p):
 raw=p.read_bytes()
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def emit(name,value):
 with (N/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode())
guard=json.loads((N/"guard.final.json").read_bytes())
assert [pin(Path(v["path"])) for v in guard["before"]]==guard["before"]
correction=json.loads((N/"exact-inverse.json").read_bytes())
new=Path(correction["new_test_ref"]["path"]).read_bytes()
inverse=new.decode("utf-8")
for edit in reversed(correction["edits"]):
 assert inverse.count(edit["new"])==1
 inverse=inverse.replace(edit["new"],edit["old"])
assert inverse.encode()==Path(correction["old_test_ref"]["path"]).read_bytes()
candidates=[pin(p) for p in sorted((N/"candidate-root").rglob("*.go"))]
assert len(candidates)==5
for v in candidates:
 p=Path(v["path"])
 if p.name!="backup_history20_upgrade_test.go":
  assert p.read_bytes()==(R1/"candidate-root"/p.relative_to(N/"candidate-root")).read_bytes()
members=[pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in ("HDF.json","MF.json")]
emit("MF.json",{"schema":"researchos.source-packet-manifest.v1","members":members,"member_count":len(members),
 "excludes":["HDF.json","MF.json"]})
hdf={"schema":"researchos.historical20-test-r2-source-handoff.v1",
 "status":"H20R2_SOURCE_FIXED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_RUNTIME",
 "candidate_root":str(N/"candidate-root"),"candidate_files":candidates,
 "old_handoff_ref":pin(R1/"HDF.json"),"old_manifest_ref":pin(R1/"MF.json"),
 "manifest_ref":pin(N/"MF.json"),"manifest_member_count":len(members),
 "report_ref":pin(N/"report.md"),"contract_ref":pin(N/"validation-contract.md"),
 "inverse_ref":pin(N/"exact-inverse.json"),"patch_ref":pin(N/"test-only.patch"),
 "checks_ref":pin(N/"source-controls.json"),"guard_ref":pin(N/"guard.final.json"),
 "origin_counter_ref":pin(N/"OriginCounter.json"),"actual914_provenance_ref":pin(N/"actual914-provenance.json"),
 "only_test_source_changed":True,"other4_candidates_byte_equal":True,"baseline66_pins_unchanged":True,
 "R1_correct_key_policy_checks_preserved":True,"five_parents_four_leaves_nine_terminals_preserved":True,
 "new_validation_caller_prepared":False,"Go_SQL_Git_native_private_model_executed":False,
 "Main_adopted":False,"overall20_to24":"OPEN","formal_acceptance":False,"stop_after_handoff":True}
emit("HDF.json",hdf)
for v in members:assert pin(Path(v["path"]))==v
assert [pin(Path(v["path"])) for v in guard["before"]]==guard["before"]
print("H20R2_SOURCE_SEALED "+json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),
 "test":correction["new_test_ref"],"member_count":len(members),"source_inputs_unchanged":len(guard["before"]),
 "actual_native_exit":None},ensure_ascii=True))

