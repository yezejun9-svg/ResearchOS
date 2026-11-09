import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
B=O.parent.parent
C=B/"mu_sdk_root_coordinator_source_v4_codex/934c2f06dc1946e5aa7d5e04589dfdd2"
A=B/"integration_codex/staged-runtime-prepare-root-59ef355458e14c0082ae8f82d98"
def read(q):return json.loads(Path(q).read_bytes())
def pin(q):
 q=Path(q);raw=q.read_bytes();return dict(path=str(q),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(n,v):
 q=O/n
 with q.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(q)
h=read(C/"handoff.json");p=read(O/"review-inputs.json");lc=read(A/"bootstrap.lifecycle.actual.json")
assert pin(C/"handoff.json")["sha256"]=="2c96eec1d77e1b20eb9fe87dc6a2d2aa1db774182dfaa82509b6a2ae07ff84bd"
actual=[]
for label in ("runtime-prepare","normal-host","cli-goal","finalize-prepare"):
 cl=read(A/(label+".closure.actual.json"));i=cl["identity"];inv=read(cl["invocation_ref"]["path"]);br=read(cl["before_resume_ref"]["path"]);obs=cl["actual_fresh_cleanup"];res=inv["result"]
 assert pin(cl["invocation_ref"]["path"])==cl["invocation_ref"] and pin(cl["before_resume_ref"]["path"])==cl["before_resume_ref"]
 assert type(i["owner_pid"]) is int and i["owner_pid"]==lc["actual_parent_pid"]
 assert type(i["runner_pid"]) is int and i["runner_pid"]==res["owned_child_pid"]
 assert type(i["creation_time_100ns"]) is int and i["creation_time_100ns"]==res["creation_time_100ns"]
 assert br["identity"]==i and br["assigned_before_resume"] is True and br["resumed"] is False
 assert 0<=cl["observed_monotonic_end"]-cl["observed_monotonic_start"]<=2
 assert cl["observed_monotonic_start"]<=obs["observed_monotonic"]<=cl["observed_monotonic_end"]
 assert all(type(obs[k]) is type(i[k]) and obs[k]==i[k] for k in ("run_uuid","owner_pid","runner_pid","creation_time_100ns","job_binding_id"))
 assert all(obs[k] is True for k in ("captured_before_resume","held_job_handle","held_primary_handle","pid_match","creation_match","primary_exit_confirmed"))
 assert type(obs["active_processes"]) is int and obs["active_processes"]==0 and obs["errors"]==[]
 assert cl["watchdog_cleanup"]["duplicate_handle_closed"] is True and cl["watchdog_cleanup"]["errors"]==[]
 pc=cl["duplicate_producer_cleanup"]
 assert all(pc[k] is True for k in ("closed","job_handle_closed","primary_handle_closed")) and pc["errors"]==[]
 expected=0xE0000508 if label=="normal-host" else 0
 assert type(res["actual_exit"]) is int and res["actual_exit"]==expected and res["timed_out"] is False and res["error"] is None and obs["primary_exit_code"]==expected
 actual.append(dict(label=label,identity_cross_binding=True,original_before_resume_flags=True,original_fresh_window=True,all_duplicates_closed=True,actual_exit=expected,closure_ref=pin(A/(label+".closure.actual.json"))))
stop=lc["host_stop"]
assert stop["planned_pre_trial_host_teardown"] is True and stop["actual_TerminateJobObject_return"] is True and stop["requested_exit_code"]==0xE0000508
pure=write("pure-check.json",p["pure"])
four=write("actual-four-closure-interface-check.json",dict(scope="Original receipt interface comparison only",checks=actual,planned_host_teardown_matches=True,Native_WinAPI_SQL_provider_calls=0,formal_acceptance=False))
review=dict(schema="researchos.root-sdk-coordinator-source-review.v1",actor_id="codex:/root/w05_merge_review",candidate_authors=["codex:/root","codex:/root/command_queue_impl"],decision="BLOCKED_SOURCE",source_ref=h["source_ref"],fixed_pins_ref=h["fixed_pins_ref"],source_handoff_ref=pin(C/"handoff.json"),source_manifest_ref=h["manifest_ref"],formal_acceptance=False,execution_authority=False,candidate_module_imported=False,coordinator_methods_executed=False,Native_WinAPI_SQL_provider_calls=0,Main_canonical_writes=0,
blockers=[
dict(id="R01",priority="blocker",lines=[139,142],title="Exact argv comparison rejects successful staged preparation",detail="Binary fixed pin uses forward slashes; actual argv[0] uses backslashes. After path-only normalization finalize still fails because actual -draft-goal-id precedes -receipt.",suggestion="Compare path-valued positions with Windows Path semantics and match the actual caller flag order. Preserve actual receipt bytes.",evidence=pure),
dict(id="R02",priority="blocker",lines=[98,99,117,127,303,306],title="Four owned-job evidence chains are incompletely validated",detail="Normal-host and cli-goal are accepted with only label and closed=true after removing all identity/fresh/duplicate proofs. Preparation closure accepts original before-resume assigned_before_resume=false and resumed=true because it only compares nested identity.",suggestion="Validate all four pinned invocation/before-resume chains with typed original flags, identity/result PID and creation-time binding, lifecycle owner PID, finite fresh-window proof and duplicate closures. Check CLI/preparation exit 0; check Host planned teardown 0xE0000508.",evidence=pure)],
passed_checks=["89 Source/member/fixed/input pins match","All actual prepare receipt schema/tuple/count/seed/native predicates pass after only in-memory argv correction","Both original prepare closures pass typed fresh predicates","Four typed fresh counterexamples reject bool/int substitutions","Separate reviewer checks confirm all four original closures carry complete expected facts","Prior v2 canonical once path and ArtifactRef hash blockers closed","C7/v9 callable interfaces and current Host admit/GO/execute contracts inspected","Shared 300-second deadline, once GO and distinct Source review / execution authority retained"],
scope="Full 542-line coordinator plus dependency and actual receipt interface review",
evidence_refs=[pin(O/"review-inputs.json"),pure,four,pin(O/"seal-review.py")],
new_tool_failures=["WINDOWS_CREATEPROCESS_ERROR_206_DURING_REVIEW_SEAL"],
limitations=["No actual preparation re-run; Root-produced receipts are comparison inputs only","No candidate coordinator, WinAPI, SQL or provider execution","Source review is not qualification, formal acceptance or execution authority"],
nonfailure_observations=["Mixed PowerShell output formatting hid a search; reread as strings","First Python stdout had path encoding corruption; repeated identical pure checks with ASCII JSON"],
stopped=True)
rr=write("review.json",review)
print(json.dumps(dict(review_ref=rr,actual_four_closures=four),ensure_ascii=True))

