from pathlib import Path
import hashlib,json
OWN=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_independent_source_review_codex/86a653e6772140f1b85f472613ef6d81")
def ref(p):
 raw=p.read_bytes()
 return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def save(n,d):
 p=OWN/n
 if p.exists():raise RuntimeError("new-only output exists")
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
before=json.loads((OWN/"inputs.before.json").read_bytes())
after=[]
for row in before:
 a=ref(Path(row["actual"]["path"]));c=ref(Path(row["copy"]["path"]))
 if a!=row["actual"] or c!=row["copy"]:raise RuntimeError("input or copy drift")
 after.append({"roles":row["roles"],"source":a,"copy":c,"equal":True})
save("inputs.after.json",after)
save("origins.json",{"schema":"researchos.source_review.origins.v1","new_origins":[],"new_nonzero_metadata_commands":0,"findings_are_static_not_execution_origins":True,"old_history_or_failure_counters_written":False})
save("handoff.json",{
 "schema":"researchos.driver18.execution_preparation.independent_handoff.v1",
 "actor":"/root/f08_whole_scope_review","non_author":True,"status":"STOPPED",
 "verdict":"REQUEST_CHANGES","critical":["D18-C01 controller255–258 catches its own SystemExit(0), always exit1"],"important":["D18-I01 controller143/150 retains full600/750 despite less than3300 remaining"],
 "review_ref":ref(OWN/"REVIEW.md"),"source_review_ref":ref(OWN/"source-review.json"),
 "before_ref":ref(OWN/"inputs.before.json"),"after_ref":ref(OWN/"inputs.after.json"),
 "author_packet_verification_ref":ref(OWN/"packet-verification.json"),
 "command_refs":[ref(OWN/"commands.original.json"),ref(OWN/"commands.supplement.json")],
 "origins_ref":ref(OWN/"origins.json"),"new_origins":[],"new_origin_count":0,"counter_reset":False,
 "selected_actual_input_refs":len(after),"source_copy_drift":0,"author_manifest_actual_rehashed":34,"author_manifest_plus_self":35,
 "prior_driver18_fullfork_ZIP_acceptance_changed":False,"full1899_rehashed":False,
 "next_minimum":["new author candidate compute main() exit code inside try, exit outside catch","pass bounded remaining inner deadline to owned native helper, reserve cleanup5 and save effective timeout","retain roster,I16,I18,explicitUNBOUND gate behavior; reseal refs and independent rereview before Root takeup"],
 "Root_authority_resources":"OPEN actual separately reviewed adapter, source/resource lease and fresh immutable prepare->execute grants required",
 "source_acceptance":False,"actual_target_execution":0,"compiled_or_Go_AST_verified":False,"all18":"NOT_RUN","I17":"FATAL_OPEN_or_explicit_OPEN_NOT_AUTHORIZED","SQL24_permission":False,"formal_increment":0,
 "only_own_new_namespace_writes":True,"Main_canonical_cache_module_old_package_writes":0,
 "manifest_path":(OWN/"manifest.json").as_posix(),
 "stop":"no further writes after sealing"
})
members=[ref(p) for p in sorted(OWN.rglob("*")) if p.is_file() and p.name!="manifest.json"]
save("manifest.json",{"schema":"researchos.independent_review.manifest.v1","members":members,"member_count":len(members),"excluded_only_self":True,"status":"SEALED_STOPPED"})
for r in members:
 if ref(Path(r["path"]))!=r:raise RuntimeError("receipt member drift")
print(json.dumps({"status":"STOPPED","verdict":"REQUEST_CHANGES","members":len(members),"members_plus_self":len(members)+1,"selected_refs":len(after),"drift":0,"new_origins":0,"handoff":ref(OWN/"handoff.json"),"manifest":ref(OWN/"manifest.json"),"review":ref(OWN/"REVIEW.md"),"source_review":ref(OWN/"source-review.json"),"origins":ref(OWN/"origins.json")},ensure_ascii=False))
