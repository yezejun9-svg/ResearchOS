import hashlib,json
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_commit_binding_independent_review_codex/f04a0b572d2141b4b2a2f45dbd885394"
P=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d";G=P/"owned-git-five-go-commit"
pins={};checks=[];jobs=[]
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();x={"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};pins[x["path"]]=x;return x
def read(p):pin(p);return path(p).read_bytes()
def j(p):return json.loads(read(p))
def ck(n,v):checks.append({"name":n,"passed":bool(v)})
def verify(r):
 q=pin(r["path"]);ck("pin:"+r["path"],q["sha256"]==r["sha256"] and q["bytes"]==r["bytes"]);return read(r["path"])
def save(n,d):
 with (O/n).open("x",encoding="utf8",newline="\n") as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write("\n")
 return pin(O/n)
closed=j(G/"commit.closed.json");pre=j(G/"precommit.verified.json");prep=j(P/"preparation.json");rawio=j(P/"root-owned-git-commit.original-tool-io.json")
ck("actual_outer_python0",rawio["result"]["exit_code"]==rawio["actual_python_exit"]==0 and rawio["result"]["output"].splitlines()[-1]=="ACTUAL_PYTHON_EXIT=0")
printed=json.loads(rawio["result"]["output"].splitlines()[0]);verify(printed["commit_ref"])
ck("exact_reported_head",printed["new_head"]==closed["new_head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and closed["old_head"]==prep["old_head"]=="e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7")
ck("exact17operations",len(list(G.glob("*.invocation.json")))==printed["owned_git_operations"]==closed["owned_git_operations"]==17)
outs={}
for i in range(1,18):
 iv=j(G/f"{i:02d}-git.invocation.json");intent=j(G/f"{i:02d}-git.intent.json");r=iv["result"];c=r["job_cleanup"]
 ck("argv_intent:"+str(i),iv["argv"]==intent["argv"])
 ck("native0:"+str(i),r["actual_exit"]==iv["actual_native_exit"]==0 and type(r["actual_exit"]) is int and iv["exception"] is None and r["error"] is None and r["resumed"] is True and r["timed_out"] is False)
 ck("jobidentity:"+str(i),type(r["creation_time_100ns"]) is int and r["creation_time_100ns"]>0 and type(r["owned_child_pid"]) is int and r["owned_child_pid"]>0)
 ck("cleanup:"+str(i),c["errors"]==[] and c["active_processes_last_observed"]==0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")))
 outs[i]=verify(iv["stdout_ref"]);verify(iv["stderr_ref"])
 jobs.append({"sequence":i,"argv":iv["argv"],"invocation_ref":pin(G/f"{i:02d}-git.invocation.json"),"pid":r["owned_child_pid"],"birth_100ns_decimal":str(r["creation_time_100ns"]),"actual_native_exit":0})
files=closed["files"];ck("exact_target_set",files==[r["target"] for r in prep["mapping"]]==pre["files"])
ck("old_new_parent_originals",outs[1].decode().strip()==closed["old_head"] and outs[13].decode().strip()==closed["new_head"] and outs[14].decode().strip()==closed["old_head"] and outs[2].decode().strip()=="main")
ck("initial_final_index_empty",outs[4]==outs[16]==b"")
ck("staged_exact_five",{s.decode() for s in outs[11].split(b"\0") if s}==set(files))
ck("committed_exact_five",{s.decode() for s in outs[15].split(b"\0") if s}==set(files))
for idx,row in enumerate(prep["mapping"],5):
 ck("original_head_equals_backup:"+row["target"],outs[idx]==verify(row["backup_ref"]))
 verify(row["prepared_ref"]);verify(row["proposal_ref"])
 ck("postcommit_main_equals_precommit_tested_proposal:"+row["target"],read(R/row["target"])==read(row["prepared_ref"]["path"])==read(row["proposal_ref"]["path"]))
for r in pre["frozen_source_refs"]+pre["canonical_refs"]:verify(r)
def status(b):return {s[3:].decode():s[:2].decode() for s in b.split(b"\0") if s}
before=status(outs[3]);after=status(outs[17]);oldother={k:v for k,v in before.items() if k not in files}
ck("same13protected_dirty",after==oldother==pre["preserved_dirty"] and len(after)==13 and sum(x==" D" for x in after.values())==11)
ck("target_clean_after_commit",all(f not in after for f in files))
ck("nul_status_hash",verify(closed["status_ref"])==outs[17])
cancel=j(R/"execution/v2.4/receipts/W05/W05-99/sdk_typed_cancel_actual_independent_review_codex/b8612c056c734cd2b2b299cfba761338/review.json")
local=j(R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_actual_independent_review_codex/4ab278baefdd49c5a0e3f4b08a1b7d97/review.json")
def comparable(rs):return {path(r["path"]).resolve():(r["sha256"],r["bytes"]) for r in rs}
ck("commit_before_after_exact_previously_tested_five",comparable(cancel["main_five_refs"])==comparable(local["main_refs"])==comparable(pre["frozen_source_refs"]))
ck("same_four_canonical",comparable(cancel["canonical_refs"])==comparable(pre["canonical_refs"]))
cp,ow=[j(pre["canonical_refs"][i]["path"]) for i in (0,1)]
ck("canonical_oldhead_intentionally_pending_update",[cp["revision"],ow["revision"],len(cp["failure_counters"])]==[340,168,672] and cp["head"]==closed["old_head"])
read(P/"commit_five_go.owned.py")
assert not [x for x in checks if not x["passed"]], [x for x in checks if not x["passed"]]
review={"schema":"researchos.sdk-five-go-actual-commit-binding-independent-review.v1","reviewer_id":"codex:/root/w05_merge_review","executor_id":"codex:/root","decision":"VERIFIED_FIVE_GO_COMMIT_OF_IDENTICAL_LOCALLY_TESTED_BYTES","checks":checks,"failed_checks":[],"new_head":closed["new_head"],"parent_head":closed["old_head"],"commit_ref":pin(G/"commit.closed.json"),"original_root_tool_io_ref":pin(P/"root-owned-git-commit.original-tool-io.json"),"owned_git_jobs":jobs,"precommit_ref":pin(G/"precommit.verified.json"),"main_five_refs":pre["frozen_source_refs"],"canonical_refs":pre["canonical_refs"],"canonical_tuple":[340,168,672],"canonical_head_still_parent_pending_root_metadata_update":True,"local_build_tests_review_ref":pin(R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_actual_independent_review_codex/4ab278baefdd49c5a0e3f4b08a1b7d97/review.json"),"typed_cancel_review_ref":pin(R/"execution/v2.4/receipts/W05/W05-99/sdk_typed_cancel_actual_independent_review_codex/b8612c056c734cd2b2b299cfba761338/review.json"),"binding_basis":"Actual original Git parent/new-head, staged+committed path lists and empty final index show exactly the five files were committed. Precommit, current, and both prior actual reviews have identical complete bytes for all five. Tests occurred before this commit on those same bytes; no rerun was performed.","protected_old_dirty_rows":13,"protected_deletions":11,"status_nul_sha256":closed["status_ref"]["sha256"],"note_status_format":"This commit used porcelain -z. Its NUL-delimited hash differs from prior LF-delimited Git status; entries are preserved.","source_runtime_qualification":False,"formal_acceptance_delta":0,"reviewer_native_git_calls":0,"reviewer_main_canonical_writes":0,"new_tool_failures":0,"pins":list(pins.values()),"original_tool_io_ref":pin(O/"original-tool-io.json")}
rr=save("review.json",review);m=save("manifest.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root/w05_merge_review","members":[pin(f) for f in sorted(O.iterdir()) if f.is_file()],"self_excluded":True,"handoff_excluded":True})
h=save("handoff.json",{"schema":"researchos.sdk-five-go-commit-binding-handoff.v1","decision":review["decision"],"review_ref":rr,"manifest_ref":m,"checks":len(checks),"failed_checks":[],"new_head":closed["new_head"],"formal_acceptance_delta":0})
print(json.dumps({"review_ref":rr,"manifest_ref":m,"handoff_ref":h,"checks":len(checks),"pins":len(pins)},ensure_ascii=False))
