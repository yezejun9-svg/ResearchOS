from pathlib import Path
import json,hashlib,stat
from datetime import datetime,timezone
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,d):
 p=O/n;assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");return pin(p)
def read(ref):
 p=Path(ref["path"]);assert pin(p)==ref;return p.read_bytes()
p=json.loads((O/"native-packet.public-index.json.input.json").read_bytes());T=Path(p["consumer_source_root"])
r=json.loads(read(p["original_report_ref"]));t=json.loads(read(p["original_tool_run_ref"]));vm=r["version_manifest"]
checks=json.loads((O/"checks.json").read_bytes());frag=json.loads((O/"actual-v7-fragment-replay.json").read_bytes());guards=json.loads((O/"runtime-guard-and-overlay.live-verification.json").read_bytes())
assert checks["summary"]["decision"]=="QUALIFIED" and checks["summary"]["failed_checks"]==0 and frag["decision"]==guards["decision"]=="PASS"
for rel,digest in vm["source_sha256"].items():assert "sha256:"+pin(T/rel)["sha256"]==digest
relative=O.relative_to(R);D=T/relative;assert not D.exists()
for parent in [T,*T.parents]:assert not parent.is_symlink() and not parent.is_junction() and not (getattr(parent.lstat(),"st_file_attributes",0)&stat.FILE_ATTRIBUTE_REPARSE_POINT)
for piece in relative.parts:
 path=T/Path(*relative.parts[:relative.parts.index(piece)+1])
 if path.exists():assert not path.is_symlink() and not path.is_junction()
D.mkdir(parents=True,exist_ok=False)
assert not D.is_relative_to(Path(p["original_report_ref"]["path"]).parent)
readiness="QUALIFIED_PENDING_ROOT_ACTUAL_CONSUMPTION"
review={"schema":"researchos.w09-independent-mode-review.v1","actor_id":"codex:/root/native_temp_independent_review","actor_role":"INDEPENDENT_NON_AUTHOR","producer_id":"codex:/root","run_id":r["run_id"],"report_sha256":p["original_report_ref"]["sha256"],"source_sha256":vm["source_sha256"],"go_executable":r["go_executable"],"run_os":vm["os"],"run_os_release":vm["os_release"],"decision":"QUALIFIED","qualified_scope":"ACTUAL_COMPONENT_NATIVE_FIXTURE_MODE_ONLY","reviewed_at":datetime.now(timezone.utc).isoformat(),"input_origin":"OWNED_TEMP_DIR","fixture_temp_root":checks["summary"]["fixture_temp_root"],"same_original_tool_run":t,"evidence_summary":checks["summary"],"consumer_readiness":readiness,"v7_actual_parser_review_ref":pin(O/"actual-v7-fragment-replay.json"),"runtime_live_pin_review_ref":pin(O/"runtime-guard-and-overlay.live-verification.json"),"limits":{"formal_AcceptanceReceipt":False,"formal_case_accepted_delta":0,"Main_adoption":False,"new_consumer_execution_grant":False,"consumer_executed_by_reviewer":False,"author_of_six_sources":False,"caller_author":False,"Root_native_executor":False,"qualification_does_not_authorize_consumer_execution_or_waive_source_pin_gate":True,"new_source_bytes_require_fresh_current_source_report_closure":True},"origin_review_namespace":str(O),"old_v6_packet_and_failure_927_unchanged":True}
reviewpin=save("mode-review.json",review);reviewrel={**reviewpin,"path":(relative/"mode-review.json").as_posix()}
for route,name in [("test.research.fixture","mode-decision.research-fixture.json"),("test.retrieval","mode-decision.retrieval.json")]:
 d={"schema":"researchos.w09-mode-decision.v2","route":[route,"W09","","C19"],"mode":"FIXTURE","run_id":r["run_id"],"report_ref":t["report_ref"],"report_sha256":p["original_report_ref"]["sha256"],"stdout_sha256":t["stdout_sha256"],"source_sha256":vm["source_sha256"],"go_executable":r["go_executable"],"producer_id":"codex:/root","reviewer_id":review["actor_id"],"reviewer_role":"INDEPENDENT_NON_AUTHOR","decision":"QUALIFIED","input_origin":"OWNED_TEMP_DIR","independent_review_ref":reviewrel,"tool_run_ref":Path(p["original_tool_run_ref"]["path"]).relative_to(T).as_posix(),"tool_run_sha256":p["original_tool_run_ref"]["sha256"],"consumer_readiness":readiness,"formal_acceptance":False,"formal_case_accepted_delta":0,"execution_grant":False,"scope":"This fresh Source21 and current original run passed actual FIXTURE qualification. Pure v7 parser replay equals the actual report. Root consumer execution and independent consumer verification remain pending."};save(name,d)
copies=[]
for name in ["mode-review.json","mode-decision.research-fixture.json","mode-decision.retrieval.json"]:
 origin=O/name;dest=D/name
 with dest.open("xb") as f:f.write(origin.read_bytes())
 assert dest.read_bytes()==origin.read_bytes();copies.append({"original_ref":pin(origin),"candidate_copy_ref":pin(dest),"candidate_relative_path":dest.relative_to(T).as_posix(),"identical_bytes":True})
assert len(list(D.iterdir()))==3 and not any(x.is_symlink() or x.is_junction() for x in D.iterdir())
read(p["original_report_ref"]);read(p["original_tool_run_ref"])
for rel,digest in vm["source_sha256"].items():assert "sha256:"+pin(T/rel)["sha256"]==digest
for ref in next(x["document"] for x in json.loads((O/"producer-inputs.read.json").read_bytes()) if x["key"]=="canonical-pre")["refs"]:read(ref)
save("candidate-copy-provenance.json",{"status":"EXACT_THREE_PUBLIC_JSON_COPIES","copies":copies,"candidate_review_namespace":str(D),"outside_original_producer_run":True,"original_report_tool_source21_and_four_canon_unchanged":True,"execution_grant":False,"formal_acceptance":False})
print(json.dumps({"decision":"QUALIFIED","consumer_readiness":readiness,"copies":copies},ensure_ascii=False))
