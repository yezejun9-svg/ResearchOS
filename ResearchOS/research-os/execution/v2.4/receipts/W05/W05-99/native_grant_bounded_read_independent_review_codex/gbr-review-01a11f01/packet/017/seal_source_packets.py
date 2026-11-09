import ast,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
G=Path(__file__).parent
Q=G.parents[1]/"native_grant_archive_request_builder_source_codex/gqb-1a11ee4f162766098eda3028b0679f2"
def pin(p):
 raw=p.read_bytes();return {"path":str(p),"sha256":"sha256:"+hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def emit(root,name,value):
 with (root/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode())
for root in (G,Q):
 guard=json.loads((root/"guard.final.json").read_bytes())
 assert [pin(Path(v["path"])) for v in guard["before"]]==guard["before"]
inverse=json.loads((G/"exact-inverse.json").read_bytes())
g=(G/"native_grant_public_pin_archive.py").read_text(encoding="utf-8")
assert g.replace(inverse["new"],inverse["old"]).encode()==Path(inverse["old_helper_ref"]["path"]).read_bytes()
b=(Q/"root_build_grant_archive_request.py").read_text(encoding="utf-8")
gt,bt=ast.parse(g),ast.parse(b)
metadata=json.loads((Q/"source-provenance.json").read_bytes())
for name in metadata["pure_metadata_functions_statically_embedded"]:
 gn=next(n for n in gt.body if isinstance(n,ast.FunctionDef) and n.name==name)
 bn=next(n for n in bt.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(gn,include_attributes=False)==ast.dump(bn,include_attributes=False),name
start=g.index('    config_ref = ref(request["Config"])',g.index("def run("))
end=g.index('    chosen, missing = validate_selection(request["Entries"], allowed)',start)
assert g[start:end] in b
assert "exec(" not in b and "compile(" not in b and "load_helper" not in b and ".read_bytes(" not in b
assert b.count('.open("xb")')==1
gb=json.loads((G/"bounded-controls.results.final.json").read_bytes())
qb=json.loads((Q/"builder-controls.results.final.json").read_bytes())
assert gb["count"]==26 and qb["count"]==45
assert all(c["result"]=="PASS" for c in qb["controls"])
emit(Q,"final-source-checks.json",{"standalone_no_helper_import_exec_call":True,
 "copied_metadata_functions_AST_identical":metadata["pure_metadata_functions_statically_embedded"],
 "copied_run_metadata_block_byte_identical":True,"all_runtime_reads_bounded_expected_plus_one":True,
 "single_exclusive_request_write_site":True,"pure_controls":45,"control_source_ref":pin(G/"pure_source_controls.py"),
 "actual_main_or_compose":False})
emit(G,"final-source-checks.json",{"GPA_R01":"FIXED_IN_SOURCE","whole_inverse":True,
 "remaining_AST_identical":True,"fake_stream_boundary_controls":26,"archive_main":False,"actual_win32_guard":False})
def seal(root,kind,source,controls):
 members=[pin(p) for p in sorted(root.iterdir()) if p.is_file() and p.name not in ("MF.json","HDF.json")]
 emit(root,"MF.json",{"schema":"researchos.source-packet-manifest.v1","members":members,"member_count":len(members),
  "excludes":["MF.json","HDF.json"]})
 hdf={"schema":"researchos."+kind+"-source-handoff.v1","status":"SOURCE_READY_PENDING_INDEPENDENT_REVIEW",
  "source_ref":pin(root/source),"manifest_ref":pin(root/"MF.json"),"manifest_member_count":len(members),
  "report_ref":pin(root/"report.md"),"calling_contract_ref":pin(root/"calling-contract.md"),
  "controls_ref":pin(root/controls),"guard_ref":pin(root/"guard.final.json"),
  "checks_ref":pin(root/"final-source-checks.json"),"origin_counter_ref":pin(root/"OriginCounter.json"),
  "actual_archive_or_builder_main":False,"actual_native_API_SQL_Go_private_model":False,"new_failure_origins":[],
  "parent_next_last_observed":917,"independent_review_required":True,"Root_only_future_execution":True,
  "stop_after_handoff":True}
 if root==Q:
  hdf.update(helper_ref=pin(G/"native_grant_public_pin_archive.py"),fixed_request_path=metadata["request_path"],
   fixed_archive_output_directory=metadata["archive_output_directory"],full_selection_flag="--select-full-current-grant-public-pins",
   root_runtime_request_written=False,archive_directory_created=False)
 else:
  hdf.update(old_helper_ref=inverse["old_helper_ref"],inverse_ref=pin(G/"exact-inverse.json"),
   patch_ref=pin(G/"bounded-read.patch"),only_read_ref_changed=True)
 emit(root,"HDF.json",hdf)
 for value in members:assert pin(Path(value["path"]))==value
 return {"HDF":pin(root/"HDF.json"),"MF":pin(root/"MF.json"),"source":hdf["source_ref"],
  "calling_contract":hdf["calling_contract_ref"],"members":len(members)}
result={"bounded":seal(G,"native-grant-bounded-read","native_grant_public_pin_archive.py","bounded-controls.results.final.json"),
 "builder":seal(Q,"native-grant-inert-request-builder","root_build_grant_archive_request.py","builder-controls.results.final.json")}
for root in (G,Q):
 guard=json.loads((root/"guard.final.json").read_bytes())
 assert [pin(Path(v["path"])) for v in guard["before"]]==guard["before"]
print("GPA_BOUNDED_AND_BUILDER_SEALED "+json.dumps(result,ensure_ascii=True))

