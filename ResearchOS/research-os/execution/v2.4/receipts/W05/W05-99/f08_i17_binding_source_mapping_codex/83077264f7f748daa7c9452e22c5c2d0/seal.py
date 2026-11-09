from pathlib import Path
import hashlib,json
OWN=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_i17_binding_source_mapping_codex/83077264f7f748daa7c9452e22c5c2d0")
def ref(p):
    raw=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def save(name,obj):
    p=OWN/name
    if p.exists():raise RuntimeError("new-only output exists")
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
before=json.loads((OWN/"selected-inputs.before.json").read_bytes())
after=[]
for r in before:
    actual=ref(Path(r["source"]["path"]));copied=ref(Path(r["copy"]["path"]))
    same=all(actual[k]==r["source"][k] for k in ["path","sha256","bytes"])
    if not same or any(copied[k]!=r["copy"][k] for k in ["path","sha256","bytes"]):
        raise RuntimeError("selected public source drift")
    after.append({"role":r["role"],"source":actual,"copy":copied,"equal":True})
extra=json.loads((OWN/"producer-additional.before.json").read_bytes())
actual=ref(Path(extra["source"]["path"]));copied=ref(Path(extra["copy_path"]))
if any(actual[k]!=extra["source"][k] for k in ["path","sha256","bytes"]) or actual["sha256"]!=copied["sha256"] or actual["bytes"]!=copied["bytes"]:
    raise RuntimeError("additional public journal drift")
after.append({"role":"main_journal_additional","source":actual,"copy":copied,"equal":True})
save("selected-inputs.after.json",after)
origin_manifest=ref(OWN/"origins.json")
save("handoff.json",{
 "schema":"researchos.f08.i17.source_mapping.handoff.v1",
 "actor":"/root/f08_whole_scope_review","independent_non_author":True,"status":"STOPPED",
 "verdict":"REQUEST_CHANGES_FOR_I17_BINDING_ONLY",
 "mapping_ref":ref(OWN/"mapping.json"),"review_ref":ref(OWN/"REVIEW.md"),
 "selected_before_ref":ref(OWN/"selected-inputs.before.json"),
 "selected_after_ref":ref(OWN/"selected-inputs.after.json"),
 "extra_producer_before_ref":ref(OWN/"producer-additional.before.json"),
 "source_locators_ref":ref(OWN/"source.locators.json"),
 "evidence_excerpts_ref":ref(OWN/"evidence.excerpts.json"),
 "observed_status_ref":ref(OWN/"observed.status.json"),
 "commands_original_ref":ref(OWN/"commands.original.json"),
 "commands_supplement_ref":ref(OWN/"commands.supplement.json"),
 "new_origins_ref":origin_manifest,
 "new_origins":[{"tool_chunk":"b9d4f8","outer_exit":1,"native_exit":None},{"tool_chunk":"bafc93","outer_exit":1,"native_exit":None},{"tool_chunk":"427f1a","outer_exit":1,"native_exit":1}],
 "new_origin_count":3,"failed_original_inputs_rerun":False,"failure_counts_reset_or_written":False,
 "old_fd09_sealed_receipt_or_cleanup_written":False,
 "selected_public_sources_actual_rehashed":35,"before_after_drift_count":0,
 "next_root_source_preparation":["type corruption expectation as actual CALLBACK_ERROR; do not convert to0","ResearchOS domain-owned real3 integration harness with explicit selector module/directory coordination","independent complete pretransition raw fixtures and actual v5 action/34source/DDL bindings"],
 "i17_should_remain":"FATAL_OPEN pending real source/layout/vectors/DDL binding and independent review",
 "other_driver17_should_not_be_blocked":True,
 "current_tests":"NOT_RUN","build_go_ast_compile_verified":False,
 "main_source_adoption":False,"sql24_installation_permitted":False,"complete_three_callbacks":False,
 "writes":{"own_new_namespace":True,"Main":False,"canonical":False,"cache":False,"module":False,"author_packages":False,"old_receipts":False},
 "forbidden_go_sql_driver_http_node_sdk_model_calls":0,
 "full_backend_original_output_claimed":False,
 "manifest_path":(OWN/"manifest.json").as_posix(),
 "stop":"No further writes after seal command"
})
members=[ref(p) for p in sorted(OWN.rglob("*")) if p.is_file() and p.name!="manifest.json"]
save("manifest.json",{"schema":"researchos.readonly.receipt.manifest.v1","status":"SEALED_STOPPED","own_namespace":OWN.as_posix(),"members":members,"member_count":len(members),"self_excluded":True})
for m in members:
    now=ref(Path(m["path"]))
    if now!=m:raise RuntimeError("own seal member drift")
print(json.dumps({"status":"STOPPED","members":len(members),"members_plus_manifest":len(members)+1,"selected_public_sources_rehashed":len(after),"input_drift":0,"new_origins":3,"handoff":ref(OWN/"handoff.json"),"manifest":ref(OWN/"manifest.json"),"mapping":ref(OWN/"mapping.json"),"review":ref(OWN/"REVIEW.md"),"origins":origin_manifest},ensure_ascii=False))
