import sys,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parents[2]
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
p=O/"checkpoint.execution.facts.json";v=json.loads(p.read_bytes())
d=B/"current_attach_q5_leg2_actual_independent_review_codex/current_target_actual_review_01"
h=pin(d/"HDF.json");m=pin(d/"MF.json")
assert (h["sha256"],h["bytes"])==("fa3f93fa63d5e6bff90db55a3f4b5b95ebfe6bb8e29c2cccd1dd2e3654c92328",4212)
assert (m["sha256"],m["bytes"])==("04171870faf1e2611751d5b99178717198787e74474b682f1f1ddd8fed8040e0",39070)
review=dict(name=str(d),handoff_ref=h,manifest_ref=m,formal_acceptance=False)
v["reviews"].append(review);v["work_in_progress"]["mu_sdk_r362"]["reviews"].append(review)
v["work_in_progress"]["status"]="ROOT_CURRENT_TARGET_FAILED_CLOSED_LIMITED_ACTUAL_REVIEW_ACCEPTED_BROKER4_SOURCE_APPROVED_BOUNDARY_ACTUAL_NEXT"
w=v["work_in_progress"]["mu_sdk_r362"];w["T9_target_actual"]["independent_actual_review"]="ACCEPTED_LIMITED_ACTUAL_PASSED_FAILED_ORIGINALS_AND_CLOSURE"
w["T9_target_actual"]["child_pass_terminal_count"]=10;w["T9_target_actual"]["child_jsonl_event_count"]=68;w["T9_target_actual"]["exact_child_native_pid_and_exit_observed"]=False
v["next_action"]=v["work_in_progress"]["next_action"]="Root pure17 public BR4 boundaries actual; fresh current-context broker-source HC/CFG/prelaunch review then one bounded native positive. Two ATT3 fixture Source repairs in progress. Historical ordinary upgrade and shared SQL old24 compatibility branches blocked; original paid business open."
v["checkpoint_note"]=v["checkpoint_note"].replace("unaccepted pending independent review","limited actual originals and closure independently accepted; target remains failed").replace("Broker4 Source sealed pending review","Broker4 Source independently approved; pure17 actual pending")
with (O/"checkpoint.execution.facts.current.json").open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
print(json.dumps(pin(O/"checkpoint.execution.facts.current.json")));print("ROOT_PYTHON_EXIT=0")


