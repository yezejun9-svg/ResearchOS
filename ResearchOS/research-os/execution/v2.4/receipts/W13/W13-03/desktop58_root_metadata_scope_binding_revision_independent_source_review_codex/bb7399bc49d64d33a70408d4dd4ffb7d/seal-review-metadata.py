import hashlib, json
from pathlib import Path
BASE = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_metadata_scope_binding_revision_independent_source_review_codex/bb7399bc49d64d33a70408d4dd4ffb7d")
FACTS = json.loads("{\"member_checks\":{\"members\":11,\"all_member_hashes_match\":true,\"physical_catalog_exact\":true,\"explicit_source_input_refs_match\":true,\"unchanged_functions_byte_AST\":[\"wip_values\",\"desktop_lease\",\"need\",\"parse\",\"encoded\",\"safe\",\"pin\",\"verify\",\"doc\",\"argref\",\"write\",\"save\",\"now\",\"unchanged_reads\",\"load_module\",\"job_ok\",\"runtime\",\"git_guard\",\"canonical_expected\",\"origins\",\"prepared\",\"registration_review\",\"register\",\"run_registration\",\"seal\",\"main\"],\"builder_assignment_occurrences\":1,\"builder_inverse_equal\":true,\"wrapper_inverse\":[{\"name\":\"scope_builder.py\",\"inverse_equal\":true},{\"name\":\"prepare.py\",\"inverse_equal\":true},{\"name\":\"register.py\",\"inverse_equal\":true},{\"name\":\"run.py\",\"inverse_equal\":true},{\"name\":\"seal.py\",\"inverse_equal\":true},{\"name\":\"grant_preflight.py\",\"inverse_equal\":true}],\"effective_pipeline_blocks\":[{\"old_lines\":[187,187],\"new_lines\":[187,187]},{\"old_lines\":[240,241],\"new_lines\":[240,241]},{\"old_lines\":[255,255],\"new_lines\":[255,268]},{\"old_lines\":[258,258],\"new_lines\":[271,273]},{\"old_lines\":[412,411],\"new_lines\":[427,427]}]},\"inverse_and_purity\":{\"whole_pipeline_inverse_equal\":true,\"inverse_anchor_counts\":[1,1,1,1,1],\"project_scope_calls\":[\"copy.deepcopy\",\"need\",\"aliases.items\",\"s.update\",\"s.update\",\"need\",\"copy.deepcopy\"],\"basis_ref_fields\":[\"scope_template_ref\",\"runtime_resources_ref\",\"compiler_resources_ref\",\"current43_authority_ref\",\"origin_cut_ref\",\"canonical_before_ref\",\"source_inputs_ref\",\"failure_prefix430_ref\"],\"controller_review_ref_in_projection\":false,\"full_scope_equality_expression\":\"scope==project_scope(b,doc(b[scope_template_ref]))\",\"prepare_order\":\"scope doc -> reviewed_scope_match -> gate load -> runtime/drafts\",\"grant_order\":\"scope doc -> reviewed_scope_match -> pf.mkdir -> gate load\",\"unknown_new_fields_status\":\"PROPOSAL_ONLY; no Root grant or canonical permission from this source review\",\"candidate_calls\":0}}")
def raw(p):
    return Path(p).read_bytes()
def ref(p):
    data=raw(p)
    return {"path":str(Path(p).resolve()),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}
def verified(row):
    p=Path(row["path"])
    data=raw(p)
    assert len(data)==row["bytes"] and hashlib.sha256(data).hexdigest()==row["sha256"]
    return data
def save(name, value):
    p=BASE/name
    assert not p.exists()
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return ref(p)
review=json.loads(raw(BASE/"review.json"))
assert review["decision"]=="READY_SOURCE_PREPARATION_ONLY"
assert not (BASE/"handoff.json").exists() and not (BASE/"manifest.json").exists()
author_mf=json.loads(verified(review["author_manifest_ref"]))
assert len(author_mf["entries"])==11
for entry in author_mf["entries"]:
    verified(entry)
verified(review["author_handoff_ref"])
for key,name in (("selected_pipeline_ref","pipeline.readonly.txt"),("selected_builder_ref","builder.readonly.txt")):
    data=verified(review[key])
    dest=BASE/name
    assert not dest.exists()
    dest.write_bytes(data)
verification=save("verification.json",{"schema":"researchos.source-only-static-verification.v1","facts":FACTS,
    "candidate_imports":0,"candidate_executions":0,"target_native_calls":0,"canonical_writes":0,
    "new_tool_failure_origins":[],"new_failure_count":0})
h=save("handoff.json",{
    "schema":"researchos.desktop58-root-metadata-binding-independent-source-review-handoff.v1",
    "reviewer":review["reviewer"],"author":review["author"],"independent":True,
    "decision":review["decision"],"status":"STOPPED","review_ref":ref(BASE/"review.json"),
    "verification_ref":verification,
    "selected_pipeline_ref":review["selected_pipeline_ref"],"selected_builder_ref":review["selected_builder_ref"],
    "author_handoff_ref":review["author_handoff_ref"],"author_manifest_ref":review["author_manifest_ref"],
    "prior_REQUEST_ref":review["prior_REQUEST_ref"],"prior_REQUEST_handoff_ref":review["prior_REQUEST_handoff_ref"],
    "prior_REQUEST_manifest_ref":review["prior_REQUEST_manifest_ref"],
    "closed_findings":["D58-META-R01"],"new_failure_origins":[],"new_failure_count":0,
    "actual_scope_registration_resources_grant":"OPEN","source_acceptance":False,"case_qualification":False,
    "formal_increment":0,"candidate_calls":0,"canonical_writes":0,
    "postseal_annex":{"path":str(BASE/"postseal-tool-observations.annex.json"),"included_in_manifest":False,
                     "reason":"Records the actual metadata sealer and verification observations after manifest creation."}})
members=[ref(p) for p in sorted(BASE.iterdir(),key=lambda p:p.name) if p.is_file()]
mf=save("manifest.json",{"schema":"researchos.independent-source-review-manifest.v1","members":members,
    "count":len(members),"self_excluded":True,"postseal_annex_excluded":True})
print(json.dumps({"review":ref(BASE/"review.json"),"handoff":h,"manifest":mf,"members":len(members),
                  "new_failure_origins":[],"new_failure_count":0,"decision":review["decision"],"status":"STOPPED"},ensure_ascii=False))
