"""Bind REST validation to the exact schema the unmodified fixture loads. Pure byte/JSON IO."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,copy,hashlib,difflib
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/cli43_transport_binding_preparation_codex/2c271a22fbb34123a65d799e854b9d24"
LEGACY=ROOT/"spec/v2.0/contracts/domain.schema.json"
EXPORTED=ROOT/".local/cli43-export-b802270f725f47dc86f9ec829a60931a/spec/v2.0/contracts/domain.schema.json"
CATALOG=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r330-b802270f725f47dc86f9ec829a60931a/source-inputs.json"
hp=OLD/"cli43_receipt_instrumentation_test.go.proposed.txt";pp=OLD/"instrumentation-plan.proposed.json";tp=OLD/"cli_sessions_test.instrumented.go.proposed.txt"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
inputs=[hp,pp,tp,LEGACY,EXPORTED,CATALOG,ROOT/"apps/cli/cli_sessions_test.go",ROOT/"internal/api/contracts/domain.schema.json",ROOT/"internal/domain/contracts.go",ROOT/"internal/domain/contracts_persistence_v24.go"]
before=[pin(p) for p in inputs];save("inputs.before.json",before)
assert before[0]["sha256"]=="9d021333686cb9405e68105c6c7725ccf18d58120643148c1f36e55d66a36664"
assert before[1]["sha256"]=="a3cc0c799dc51c584f51cf54f76931b337a6266933617fb7f9437f1297724352"
assert before[2]["sha256"]=="6dbcdcc0fc12b2bd00a69f724cbe1f9598761fe467157273c6709344b1a1f29e"
assert before[3]["sha256"]==before[4]["sha256"]=="b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847"
catalog=json.loads(CATALOG.read_bytes());matches=[r for r in catalog["files"] if Path(r["path"])==LEGACY]
assert len(matches)==1 and matches[0]==pin(LEGACY)
legacy=json.loads(LEGACY.read_bytes());assert legacy["$defs"]["ProjectBinding"]["properties"]["route"]["enum"]==["PAPERCLIP","THIN_CORE"]
fixture=(ROOT/"apps/cli/cli_sessions_test.go").read_bytes().decode()
assert 'domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")' in fixture
old=hp.read_bytes().decode();text=old
changes=[
('filepath.Join("..","..","internal","api","contracts","domain.schema.json")','filepath.Join("..","..","spec","v2.0","contracts","domain.schema.json")'),
("b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54","b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847")]
for a,b in changes:assert text.count(a)==1;text=text.replace(a,b,1)
inverse=text
for a,b in reversed(changes):assert inverse.count(b)==1;inverse=inverse.replace(b,a,1)
assert inverse.encode()==hp.read_bytes()
newp=OUT/"cli43_receipt_instrumentation_test.go.proposed.txt"
with newp.open("xb") as f:f.write(text.encode())
oldplan=json.loads(pp.read_bytes());plan=copy.deepcopy(oldplan);plan["additional_file_ref"]=pin(newp)
back=copy.deepcopy(plan);back["additional_file_ref"]=oldplan["additional_file_ref"]
assert (json.dumps(back,ensure_ascii=False,indent=2)+"\n").encode()==pp.read_bytes()
save("instrumentation-plan.proposed.json",plan)
save("helper.exact-edits.json",[{"old":a,"new":b} for a,b in changes])
with (OUT/"helper.diff").open("xb") as f:f.write("".join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile="old-fixed-api-embed",tofile="actual-fixture-legacy")).encode())
after=[pin(p) for p in inputs];save("inputs.after.json",after);assert after==before
save("static-checks.json",{"helper_whole_byte_inverse":True,"plan_whole_byte_inverse":True,"schema_in_original_597_source_inputs":True,"actual_prior_export_schema_bytes_equal_Main":True,"unmodified_fixture_contract_path_matches_helper":True,"Goal_Task_FULL_schema_and_THIN_CORE_checks_not_relaxed":True,"POST_ClientProtocolDocument_unchanged":True,"test_transport_facts_and_all_business_assertions_unchanged":True,"Go_gofmt_SQL_HTTP_SDK_MODEL_calls":0,"counter_reset":False})
save("handoff.json",{"schema":"researchos.cli43.actual-fixture-schema-preparation.v1","actor":"codex:/root","status":"SOURCE_PREPARATION_ONLY","helper_ref":pin(newp),"instrumentation_plan_ref":pin(OUT/"instrumentation-plan.proposed.json"),"unchanged_instrumented_test_ref":pin(tp),"instrumented_source_ref":pin(tp),"old_helper_ref":pin(hp),"old_plan_ref":pin(pp),"actual_fixture_contract_schema_ref":pin(LEGACY),"prior_export_same_legacy_schema_ref":pin(EXPORTED),"original_source_catalog_ref":pin(CATALOG),"changed_values_only":["GET schema input path","GET exact legacy raw SHA"],"whole_byte_inverses":True,"business_assertions_changed":False,"schema_weakened_or_project_route_changed":False,"POST_protocol_API_embed_changed":False,"HTTP_budget_timeout_or_Python_validator_changed":False,"requires":["non-author source review against exact fixture domain.New and schema enums","new Root scope/CAS/grant","fresh compile and one execution","independent actual qualification"],"source_acceptance":False,"formal_increment":0,"Go_SQL_HTTP_SDK_MODEL_calls":0,"counter_reset":False})
save("manifest.json",{"self_excluded":True,"members":[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="manifest.json"]})
print(json.dumps({"helper_ref":pin(newp),"plan_ref":pin(OUT/"instrumentation-plan.proposed.json"),"handoff_ref":pin(OUT/"handoff.json"),"manifest_ref":pin(OUT/"manifest.json"),"target_calls":0},ensure_ascii=False))
