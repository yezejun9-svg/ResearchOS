"""Seal own Source proposal only, with immutable inputs; never adopt or execute."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94")
def pin(p):
 raw=p.read_bytes();return {"path":str(p).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(ref):
 p=Path(ref["path"])
 if not p.is_absolute():p=ROOT/p
 a=pin(p)
 if a["sha256"]!=ref["sha256"] or a["bytes"]!=ref["bytes"]:raise ValueError("Immutable source pin drift:"+ref["path"])
 return a
def put(name,d):
 with (BASE/name).open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(BASE/name)
report=json.loads((BASE/"report.json").read_bytes())
for key in ("basis_request_ref","basis_source_handoff_ref","basis_source_manifest_ref","inverse_ref","controls_ref"):verify(report[key])
oldmf=json.loads((ROOT/report["basis_source_manifest_ref"]["path"]).read_bytes())
for r in oldmf["members"]:verify(r)
for ref in report["source_pins"].values():verify(ref);ast.parse(Path(ref["path"]).read_bytes())
basis_main=put("public-source-basis.actual.json",{"schema":"researchos.a04-source-public-basis.v1","members":[pin(ROOT/name) for name in ("apps/cli/cli_stream.go","internal/domain/store.go","internal/store/sqlite.go","internal/domain/contracts.go","internal/host/contract.go","internal/domain/client_protocol_journal.go")],"native_or_sql_execution":False,"read_limit":"The larger public Go text search was tool-truncated; no full-output claim."})
members=[pin(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json","postseal-tool-observations.original.json")]
mf=put("manifest.json",{"schema":"researchos.a04-source-revision-manifest.v1","author_id":"codex:/root/f08_whole_scope_review","status":"SEALED_SOURCE_PROPOSAL_WITH_OPEN","member_count":len(members),"members":members,"self_included":False,"handoff_external":True,"postseal_original_tool_io_external":True})
hdf=put("handoff.json",{"schema":"researchos.a04-source-revision-handoff.v1","author_id":"codex:/root/f08_whole_scope_review","status":"STOPPED","decision":"SOURCE_PROPOSAL_WITH_OPEN_FOR_NONAUTHOR_REVIEW","source_pins":report["source_pins"],"report_ref":pin(BASE/"report.json"),"contract_proposal_ref":pin(BASE/"evidence-contract.proposed.json"),"inverse_ref":report["inverse_ref"],"controls_ref":report["controls_ref"],"manifest_ref":mf,"original_tool_io_ref":pin(BASE/"tool-observations.original.json"),"public_source_basis_ref":basis_main,"basis_request_ref":report["basis_request_ref"],"basis_source_handoff_ref":report["basis_source_handoff_ref"],"independent_review_ref":None,"required_next_actor":"Root-selected w05 non-author; author cannot sign this Source accepted.","open_requirements":report["open_requirements"],"r3_full_implementation_complete":False,"current_dispatcher_can_qualify_a04":False,"main_adopted":False,"actual_root_authority":None,"root_grant_approved":False,"full_candidate_entrypoints_executed":0,"sql_native_model_calls":0,"new_tool_failure_origin_refs":[],"new_tool_failure_count":0,"canonical_writes":0,"source_acceptance":False,"formal_case_accepted_delta":0,"postseal_original_io_annex":"postseal-tool-observations.original.json; external to MF, no circular self-hash."})
print(json.dumps({"handoff_ref":hdf,"manifest_ref":mf,"report_ref":pin(BASE/"report.json"),"member_count":len(members),"status":"SOURCE_PROPOSAL_WITH_OPEN","new_tool_failures":0,"selected_source_refs":report["source_pins"]},ensure_ascii=False))

