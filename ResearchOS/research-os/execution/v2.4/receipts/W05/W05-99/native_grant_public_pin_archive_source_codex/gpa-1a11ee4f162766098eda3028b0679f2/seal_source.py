import ast, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).parent
def pin(path):
 raw=path.read_bytes()
 return {"path":str(path),"sha256":"sha256:"+hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def emit(name,value):
 with (N/name).open("xb") as stream:
  stream.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
inputs=json.loads((N/"source-inputs.before.json").read_bytes())
after=[pin(Path(v["path"])) for v in inputs]
assert inputs==after
assert json.loads((N/"source-inputs.after.json").read_bytes())==inputs
source=(N/"native_grant_public_pin_archive.py").read_bytes()
tree=ast.parse(source)
assert b"__INVENTORY__" not in source
controls=json.loads((N/"pure-controls.results.json").read_bytes())
assert controls["count"]==41 and all(c["result"]=="PASS" for c in controls["controls"])
assert controls["native"] is False and controls["sql"] is False and controls["archive_run_called"] is False
failure=json.loads((N/"failure-origin.915.json").read_bytes())
assert len(failure["original_input"])==8729
assert failure["outer_exit"] is None and failure["python_exit"] is None and failure["native_exit"] is None
emit("guard.final.json",{"schema":"researchos.source-input-pin-recheck.v1","inputs":inputs,"after":after,
 "unchanged":True,"original_guard_count":len(inputs),"win32_guard_was_executed":False,
 "source_hash_verification_only":True,"canonical_or_frozen_inputs_written":False})
emit("source-checks.json",{"ast":"PASS","controls":41,"source_inventory":28,"target_inventory":29,
 "inventory_relative_files":29,"actual_archive_run":False,"actual_native":False,"actual_sql":False,
 "new_failure_ordinals":[915],"parent_next_readonly":916})
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("HDF.json","MF.json")]
emit("MF.json",{"schema":"researchos.source-packet-manifest.v1","members":members,"member_count":len(members),
 "excludes":["MF.json","HDF.json"],"member_sha256_format":"prefixed-lowercase"})
hdf={"schema":"researchos.native-grant-public-pin-archive-source-handoff.v1",
 "status":"SOURCE_IMPLEMENTED_PENDING_NONAUTHOR_REVIEW",
 "helper_ref":pin(N/"native_grant_public_pin_archive.py"),"manifest_ref":pin(N/"MF.json"),
 "manifest_member_count":len(members),"report_ref":pin(N/"report.md"),"contract_ref":pin(N/"calling-contract.md"),
 "controls_ref":pin(N/"pure-controls.results.json"),"guard_ref":pin(N/"guard.final.json"),
 "origin_counter_ref":pin(N/"OriginCounter.json"),"failure_origins":[pin(N/"failure-origin.915.json")],
 "inventory_count_correction":{"old_wrong_source":27,"old_wrong_target":28,"actual_source":28,"actual_target":29},
 "native_api_sql_private_model_executed":False,"archive_entrypoint_executed":False,
 "pure_source_controls_passed":41,"original_owner_nine_cases_formal42_acceptance":False,
 "stop_after_handoff":True}
emit("HDF.json",hdf)
for r in members:
 assert pin(Path(r["path"]))==r
assert [pin(Path(v["path"])) for v in inputs]==inputs
print("GPA_SOURCE_SEALED "+json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),
 "helper":hdf["helper_ref"],"failure915":hdf["failure_origins"][0],
 "member_count":len(members),"controls":41,"native_exit":None},ensure_ascii=True))

