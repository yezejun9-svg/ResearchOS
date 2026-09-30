import sys
sys.dont_write_bytecode=True
import base64,datetime,hashlib,importlib.util,io,json,pathlib,subprocess
from http.client import HTTPResponse
ROOT=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
OUT=pathlib.Path(__file__).resolve().parent
RUN="107a8c43-c34a-405a-900e-8164a90931d9"
REV="9bdec8fdfb41329b72ad130c1ac63c6a2a4e50c1"
PACK=ROOT/"execution/receipts/W17"/RUN
PRIOR=ROOT/"execution/verifier/W17/c22-6d070c8"
checks=[]
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def lines(p):return [json.loads(s) for s in p.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(value,label):
 if not value:raise AssertionError(label)
 checks.append(label)
def hashed(p,h):
 check(p.resolve().is_relative_to(ROOT.resolve()),"path-in-project:"+str(p))
 check(sha(p)==h.removeprefix("sha256:"),"hash:"+str(p.relative_to(ROOT)))
def canonical(value):
 def inspect(v):
  if isinstance(v,float):raise ValueError("Receipt JCS subset disallows floats")
  if isinstance(v,dict):
   for k,w in v.items():
    if any(ord(c)>65535 for c in k):raise ValueError("Receipt JCS subset disallows non-BMP keys")
    inspect(w)
  if isinstance(v,list):
   for w in v:inspect(w)
 inspect(value)
 return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT)
def blobmap(rev,names):
 names=list(names);stream=io.BytesIO(subprocess.run(["git","cat-file","--batch"],input="".join(rev+":"+n+"\n" for n in names).encode(),cwd=ROOT,stdout=subprocess.PIPE,check=True).stdout);blobs={}
 for name in names:
  header=stream.readline().split();check(len(header)==3 and header[1]==b"blob","git-blob:"+name)
  body=stream.read(int(header[2]));check(stream.read(1)==b"\n","git-boundary:"+name)
  blobs[name]=body
 return blobs
receipt=load(PACK/"receipt.json");case=load(PACK/"C22.json");manifest=load(PACK/"artifacts.json");before=load(PACK/"environment-before.json")
expected_jcs="sha256:56628cf50f79880ec3cd496ba9a42543538db93b5d52caf5080fccbce0a7d8bb"
check(receipt["receipt_hash"]==expected_jcs=="sha256:"+hashlib.sha256(canonical({k:v for k,v in receipt.items() if k!="receipt_hash"})).hexdigest(),"frozen-executor-receipt-JCS")
check(receipt["task_id"]=="W17" and receipt["run_id"]==RUN and receipt["code_revision"]==REV and receipt["executor_identity"]=="codex:/root" and receipt["verifier_identity"] is None,"executor-binding")
check(receipt["project_id"]==load(ROOT/"execution/project_identity.json")["project_id"],"project-identity")
check(receipt["status"]=="EXECUTION_REPORTED" and receipt["owned_acceptance_status"]=="PENDING_INDEPENDENT_VERIFIER","no-executor-self-acceptance")
hashed(PACK/"artifacts.json",receipt["artifact_manifest_hash"])
check(manifest["run_id"]==RUN and manifest["task_id"]=="W17" and len(manifest["files"])==197,"artifact-manifest-binding")
check(len({r["path"] for r in manifest["files"]})==197,"artifact-manifest-no-duplicates")
for row in manifest["files"]:hashed(ROOT/row["path"],row["sha256"])
check(set(receipt["owned_acceptance_evidence"])=={"C22"},"only-C22-owned-case")
hashed(ROOT/receipt["owned_acceptance_evidence"]["C22"]["path"],receipt["owned_acceptance_evidence"]["C22"]["sha256"])
version=case["version_manifest"];source=version["source_sha256"]
check(len(source)==320 and set(source)==set(receipt["verified_source_paths"]),"exact-320-source-inventory")
check(source==before["source_sha256"] and version["git_head"]==before["git_head"]==REV,"pre-post-source-equality")
check(before["tracked_source_clean"] and not before["tracked_status_porcelain"],"tracked-source-clean-preflight")
hashed(ROOT/version["preflight_reference"]["path"],version["preflight_reference"]["sha256"])
for category in ("input_snapshots","lock_files","policy_versions"):
 for row in version[category]:hashed(ROOT/row["path"],row["sha256"])
hashed(ROOT/"spec/v2.0/PACKAGE_MANIFEST.json",version["spec_manifest_sha256"])
hashed(ROOT/"spec/v2.0/contracts/tasks.json",version["task_gates_sha256"])
hashed(ROOT/"execution/route.json",receipt["route_revision"])
for name,h in source.items():hashed(ROOT/name,h)
blobs=blobmap(REV,source)
for name,h in source.items():check(hashlib.sha256(blobs[name]).hexdigest()==h,"fixed-Git-source:"+name)
priorindex=load(PRIOR/"index.json")
hashed(PRIOR/"index.json","7c5a8c76c572b6fc7d2ae48849f774d2e19e62d06ef84922e0bd0c4d61f694dd")
for row in priorindex["files"]:hashed(PRIOR/row["path"],row["sha256"])
prior=load(PRIOR/"review.json")
check(prior["verdict"]=="PASS_C22_FIXTURE_READY_FOR_FORMAL" and not prior["blocking_P1_findings"],"prior-independent-fixture-verdict")
check(prior["validation"]["unique_passing_behavior_assertions"]==156 and len(prior["harness_attempts"])==4,"prior-failures-and-limits-retained")
contract=next(c for c in load(ROOT/"spec/v2.0/contracts/acceptance.json")["cases"] if c["id"]=="C22")
task=next(t for t in load(ROOT/"spec/v2.0/contracts/tasks.json")["tasks"] if t["task_id"]=="W17")
gate=next(g for g in task["task_gate_checks"] if g["check_id"]=="W17-G03")
check(contract["mode"]=="FIXTURE" and contract["final_owner_task"]=="W17" and gate["mode"]=="FIXTURE","frozen-owner-and-mode")
check([a["assertion_id"] for a in case["assertion_results"]]==[a["id"] for a in contract["assertions"]],"frozen-case-complete")
check(case["global_evidence_id"]=="GLOBAL_EVIDENCE_V1" and case["status"]=="EXECUTION_REPORTED_PENDING_INDEPENDENT_ACCEPTANCE","GLOBAL-binding")
check(case["run_receipt"]["run_id"]==RUN and case["run_receipt"]["case_id"]=="C22" and case["run_receipt"]["environment_mode"]==case["run_receipt"]["actual_runtime_scope"]=="FIXTURE","GLOBAL-run-selector")
check(case["run_receipt"]["executor_identity"]=="codex:/root" and case["run_receipt"]["independent_verifier_identity"]=="codex:/root/evolution_verifier","GLOBAL-identities")
check(case["acceptance_receipt"]=={"status":"PENDING_INDEPENDENT_VERIFIER","reference":"execution/verifier/W17/"+RUN+".json"},"GLOBAL-acceptance-pending")
spec=importlib.util.spec_from_file_location("readonly_c22_formal",ROOT/"tests/security/c22_fixture.py");runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
inventory=load(ROOT/"tests/security/c22_expected.json");ids=runner.validate_inventory(inventory)
registry=load(ROOT/"execution/commands.json")["commands"]
expected_runs={"7bc5d8f0-3124-4d44-9741-234c7cdd1fc8":("test.security","C22",""),"95c702ee-5d73-4433-be8a-40dbdc8ce574":("test.evaluation.security","C22",""),"f2bc0cc7-9bd3-4f2e-a7f9-ca7dbe2422cc":("test.security","","W17-G03")}
runs=[];report_rows={};native_sids=[];control_ids=[];source_run_counts=[]
check(len(receipt["verification_results"])==3,"exact-three-registered-runs")
for result in receipt["verification_results"]:
 invref=result["actual_invocation_reference"];inv=load(ROOT/invref)
 key,caseid,checkid=expected_runs[inv["invocation_id"]]
 check(inv["command_key"]==key and inv["selectors"]=={"task_id":"W17","case_id":caseid,"check_id":checkid},"invocation-selector:"+inv["invocation_id"])
 check(inv["status"]=="PASS" and inv["exit_code"]==inv["child_exit_code"]==0 and inv["code_revision"]==REV,"invocation-executed:"+inv["invocation_id"])
 check(len(inv["assertion_ids"])==137 and set(inv["assertion_ids"])==set(ids),"invocation-assertion-inventory")
 hashed(ROOT/"execution/commands.json",inv["registered_command_revision"])
 hashed(ROOT/"execution/toolchains/locked.json",inv["toolchain_revision"])
 hashed(ROOT/"execution/command_dispatcher/dispatch.py",inv["dispatcher_sha256"])
 check(inv["argv"][1:]==registry[key]["argv"] and pathlib.Path(inv["cwd"]).resolve()==ROOT and inv["timeout_seconds"]==registry[key]["timeout_seconds"],"registered-argv-cwd-timeout")
 for row in inv["input_versions"]:hashed(ROOT/row["path"],row["sha256"])
 for field in ("stdout","stderr"):hashed(ROOT/inv[field]["path"],inv[field]["sha256"])
 check(result["command_key"]==key and result["status"]==result["actual_dispatch_status"]=="PASS" and result["mode"]=="FIXTURE" and result["exit_code"]==0,"construction-verification-result")
 check(result["registered_command_revision"]==inv["registered_command_revision"] and result["assertion_ids"]==inv["assertion_ids"],"construction-invocation-reconciliation")
 check(result["started_at"]==inv["started_at"] and result["ended_at"]==inv["ended_at"] and result["stdout_reference"]==inv["stdout"]["path"] and result["stderr_reference"]==inv["stderr"]["path"],"construction-invocation-times-raw")
 for path in result["raw_evidence_references"]:
  row=next(r for r in manifest["files"] if r["path"]==path)
  hashed(ROOT/path,row["sha256"])
 stdout=lines(ROOT/inv["stdout"]["path"])[-1]
 check(stdout["status"]=="PASS" and stdout["assertions"]==137 and set(stdout["assertion_ids"])==set(ids),"dispatcher-child-summary")
 directory=pathlib.Path(stdout["receipt"]).parent
 check(directory.resolve().is_relative_to((ROOT/"execution/receipts/W17/c22").resolve()),"native-report-owned-path")
 report=load(directory/"report.json")
 check(report["source_commit"]==REV and report["task_id"]=="W17" and report["case_id"]==(caseid or None) and report["check_id"]==(checkid or None) and report["covered_case"]=="C22" and report["mode"]=="FIXTURE","native-report-selector-binding")
 check(report["status"]=="PASS" and report["exit_code"]==0 and report["execution_status"]=="EXECUTION_REPORTED" and report["independent_acceptance"]=="PENDING","native-report-not-self-accepted")
 for field in ("real_provider_called","formal_holdout_accessed","actual_product_database_accessed","protected_service_accessed","LIVE_qualified","BOUNDED_AUTO_granted"):check(report[field] is False,"scope-false:"+field)
 index=load(directory/"evidence-index.json");check(index["source_commit"]==REV,"report-index-source")
 for name,h in index["files"].items():hashed(directory/name,h)
 for name,h in report["evidence_hashes"].items():hashed(directory/name,h)
 sm=load(directory/"source-manifest.json");check(sm["source_commit"]==REV,"run-source-manifest-source")
 missing={name:h for name,h in sm["files"].items() if name not in blobs}
 if missing:blobs.update(blobmap(REV,missing))
 for name,h in sm["files"].items():
  hashed(ROOT/name,h);check(hashlib.sha256(blobs[name]).hexdigest()==h.removeprefix("sha256:"),"run-Git-source:"+name)
 check(sha(pathlib.Path(sm["go"]["path"]))==sm["go"]["sha256"].removeprefix("sha256:"),"locked-Go-binary")
 source_run_counts.append(len(sm["files"]))
 events=lines(directory/"go.stdout.jsonl");records=lines(directory/"audit.jsonl")
 validated=runner.validate_evidence(directory,events,inventory)
 check(validated["assertions"]==report["assertions"] and validated["scan"]==report["scan"] and validated["http_count"]==report["http_count"]==304,"raw-reported-semantics")
 check(load(directory/"permission-matrix.json")==validated["permission_matrix"] and load(directory/"native-matrix.json")==validated["native_matrix"] and load(directory/"marker-scan.json")==validated["scan"],"derived-matrices-match-raw")
 http=[r for r in records if r.get("record_type")=="http"]
 for row in http:
  check(row["raw_request"].splitlines()[0]==f'{row["method"]} {row["path"]} HTTP/1.1',"HTTP-wire-request")
  class Sock:
   def makefile(self,*args):return io.BytesIO(row["raw_response"].encode())
  response=HTTPResponse(Sock());response.begin();body=response.read()
  check(response.status==row["status"] and body.decode()==row["response_body"],"HTTP-wire-response")
  if row["audience"]=="AUTHORIZED_CONTROL" and row["status"]==200 and row["path"].endswith("/content"):
   check(response.getheader("Cache-Control")=="no-store","authorized-no-store")
 for row in validated["native_matrix"]:native_sids.append(row["sid"])
 for phase in ("before-restart","after-restart","missing-provider"):control_ids.append(load(directory/(phase+"-control-ready.json"))["pid"])
 report_rows[invref]={a["assertion_id"]:a for a in report["assertions"]}
 runs.append({"command_key":key,"invocation_id":inv["invocation_id"],"invocation_reference":invref,"case_id":caseid or None,"check_id":checkid or None,"assertions":137,"actual_HTTP_requests":304,"native_processes":4,"control_plane_processes":3,"report":str((directory/"report.json").relative_to(ROOT)).replace("\\","/"),"report_sha256":sha(directory/"report.json"),"scan":validated["scan"]})
check(len(set(native_sids))==12,"12-fresh-AppContainer-SIDs")
case_refs={r["invocation_reference"] for r in runs if r["case_id"]=="C22"}
check({r["reference"] for r in case["command_receipt"]}==case_refs and sorted(r["command_key"] for r in case["command_receipt"])==sorted(contract["command_keys"]),"both-frozen-required-commands")
for row in case["command_receipt"]:
 inv=load(ROOT/row["reference"]);hashed(ROOT/row["reference"],row["sha256"])
 for field in ("command_key","argv","cwd","environment_names","exit_code","stdout","stderr","registered_command_revision","code_revision"):check(row[field]==inv[field],"GLOBAL-command:"+field)
for frozen,actual in zip(contract["assertions"],case["assertion_results"]):
 check(actual["expected"]==frozen["expected"] and actual["status"]=="PASS" and len(actual["actual"])==2,"frozen-expected:"+frozen["id"])
 check({r["invocation_reference"] for r in actual["actual"]}==case_refs,"frozen-assertion-both-runs")
 for row in actual["actual"]:
  check({k:v for k,v in row.items() if k!="invocation_reference"}==report_rows[row["invocation_reference"]][frozen["id"]],"GLOBAL-actual-exact-raw:"+frozen["id"])
 for raw in actual["raw_evidence"]:hashed(ROOT/raw["path"],raw["sha256"])
check(len(case["supplemental_assertions"])==274,"exact-274-supplemental-records")
for row in case["supplemental_assertions"]:
 check(row["invocation_reference"] in case_refs and {k:v for k,v in row.items() if k!="invocation_reference"}==report_rows[row["invocation_reference"]][row["assertion_id"]],"supplemental-exact-raw")
negative=load(ROOT/"execution/receipts/W17/c22/selector-integration/negative-selectors.json")
check(len(negative["cases"])==7 and all(r["exit_code"]==1 and r["stdout"]["status"]=="FAIL" and r["stdout"]["assertions"]==0 and r["stdout"]["receipt"] is None for r in negative["cases"]),"seven-selector-negative-evidence")
before_registry=json.loads(git("show",REV+"^:execution/commands.json"))
after_registry=load(ROOT/"execution/commands.json")
changed=[key for key in set(before_registry["commands"])|set(after_registry["commands"]) if before_registry["commands"].get(key)!=after_registry["commands"].get(key)]
check(set(changed)=={"test.security","test.evaluation.security"},"only-two-command-semantic-deltas")
unchanged=["internal/domain/protected_artifacts.go","internal/domain/auth.go","internal/domain/protected_c22_test.go","ops/protected_fixture/main_windows.go","ops/experiment_sandbox/sandbox_windows.go","adapters/protectedstore/canary_windows.go","tests/security/c22_expected.json"]
old=blobmap("6d070c8aeb9aa11c4fc48ced8048aa99ba45c84a",unchanged)
for name in unchanged:check(old[name]==blobs[name],"prior-security-implementation-identical:"+name)
summary={"status":"PASS","scope":"Formal C22 FIXTURE and W17-G03 only","task_id":"W17","case_id":"C22","run_id":RUN,"source_revision":REV,"executor_receipt_jcs_hash":receipt["receipt_hash"],"executor_receipt_sha256":sha(PACK/"receipt.json"),"global_case_sha256":sha(PACK/"C22.json"),"artifact_manifest_sha256":sha(PACK/"artifacts.json"),"manifest_files":197,"source_hashes_verified":320,"run_source_manifest_counts":source_run_counts,"prior_independent_review_files_verified":len(priorindex["files"]),"prior_independent_review_verified":True,"known_prior_harness_failures_preserved":True,"checks_passed":len(checks),"registered_runs":runs,"raw_assertion_instances":411,"actual_HTTP_requests":912,"fresh_AppContainer_SIDs":12,"control_plane_process_launches":9,"selector_negative_results_verified":7,"new_product_test_runs":0,"new_external_or_protected_access":False,"whole_stage_accepted":False,"A10_accepted":False,"A11_accepted":False}
save("audit-report.json",summary);save("audit-checks.json",checks)
save("route-and-boundary-review.json",{"executed_revision":REV,"command_semantic_deltas":sorted(changed),"strict_selector":"W17 and exactly one of C22 or W17-G03; FIXTURE only; no args","unchanged_security_sources":unchanged,"S1_compatibility":"S1 relationKind only remaps RuntimeRegistration.qualification_ids to AcceptanceReceipt. Normal Qualification and protected Artifact role/restricted checks remain. Three current-main C22 runs cover schema16 and common visibility paths.","new_confirmed_findings":[],"current_main_head":git("rev-parse","HEAD").decode().strip(),"source_drift":False,"prior_probe_limits":prior["harness_attempts"]})
print(json.dumps(summary,ensure_ascii=False))

