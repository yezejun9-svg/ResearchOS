import sys
sys.dont_write_bytecode=True
import hashlib,json,os,uuid
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");P=Path(__file__).resolve().parent;O=P/"checkpoint-after-five-go";O.mkdir(exist_ok=False)
def pin(p):
 p=Path(p);x=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(x).hexdigest(),"bytes":len(x)}
def save(n,v):
 p=O/n;p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode());return pin(p)
cp=R/"execution/v2.4/checkpoint.json";raw=cp.read_bytes();assert hashlib.sha256(raw).hexdigest()=="8a35b3cf00236a7bcefe731a10aae367aae2c65411d9f7056c16f1be9f32a2c8"
c=json.loads(raw);assert c["revision"]==340 and c["head"]=="e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7" and len(c["failure_counters"])==672
others=[R/"execution/v2.4"/(x+".json") for x in ("path_ownership","step_state","commands")];other_raw=[x.read_bytes() for x in others]
refs=[
(673,R/"execution/v2.4/receipts/W13/W13-03/desktop58_scope7_lease_close_independent_review_codex/5f9649408a574b57b960916cd986f452/failure-origin.673.original.json"),
(674,R/"execution/v2.4/receipts/W05/W05-99/a04_formal_profile_binding_independent_review_codex/70ca957e1f4b4d7fb4223159361c86e4/failure.origin.f05575.json"),
(675,P/"failure-origin.675.actual-go-build.original.json"),
(676,P/"failure-origin.676.actual-cli-snapshot.original.json"),
(677,R/"execution/v2.4/receipts/W05/W05-99/a04_formal_profile_json_identity_revision_codex/90e455115bf34f81bd29e601debf511a/failure-origin.9691d9.json"),
(678,P/"failure-origin.678.cancel-prerequisite-search.original.json"),
(679,R/"execution/v2.4/receipts/W05/W05-99/sdk_typed_cancel_actual_independent_review_codex/b8612c056c734cd2b2b299cfba761338/failure-origin.679.original.json")]
# Resolve the actual immutable first reference from the existing Source-close receipt inventory.
if not refs[0][1].is_file():
 candidates=list((R/"execution/v2.4/receipts").glob("**/5f9649408a574b57b960916cd986f452/failure-origin.673.original.json"))
 assert len(candidates)==1;refs[0]=(673,candidates[0])
actual=[{"ordinal":n,"evidence_ref":pin(p)} for n,p in refs];assert [x["ordinal"] for x in actual]==list(range(673,680))
before_path=O/"checkpoint.before.json";before_path.write_bytes(raw)
commit=pin(P/"owned-git-five-go-commit/commit.closed.json");assert commit["sha256"]=="3c200d9f4e360b14d149e8b631c8b11bb10ea03c996789af202335e78f11e35b"
commit_doc=json.loads(Path(commit["path"]).read_bytes());assert commit_doc["new_head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and commit_doc["preserved_dirty_count"]==13
reviews=[
R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_actual_independent_review_codex/4ab278baefdd49c5a0e3f4b08a1b7d97/review.json",
R/"execution/v2.4/receipts/W05/W05-99/sdk_typed_cancel_actual_independent_review_codex/b8612c056c734cd2b2b299cfba761338/review.json",
R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_commit_binding_independent_review_codex/f04a0b572d2141b4b2a2f45dbd885394/review.json"]
for path,sha in zip(reviews,["9157f15c2587756853c3ccaa7f53aa285897c7206e89c82c34f98dac9dc6e0ca","554a59f8def876630680b586d5bb8387621ecd1288d5655386d3dafb70a7de85","151fbea9df747892f8308148f12346704452ab8ef3db9b23a5b531243fb1daa3"]):assert pin(path)["sha256"]==sha
new_origins=[x["evidence_ref"]["sha256"] for x in actual];assert len(set(new_origins))==7
old_origins={x.get("origin_key") for x in c["failure_counters"]};assert not old_origins.intersection(new_origins)
for x in actual:c["failure_counters"].append({"origin_key":x["evidence_ref"]["sha256"],"evidence_ref":x["evidence_ref"],"original_payload":{"immutable_actual_tool_io_ref":x["evidence_ref"],"observed_ordinal":x["ordinal"]},"counter_reset":False,"counted_once":True,"automatic_retry":False})
now=datetime.now(timezone.utc).isoformat();c["expected_previous_revision"]=340;c["revision"]=341;c["head"]=commit_doc["new_head"];c["updated_at"]=now;c["updated_by"]="codex:/root"
w=c["work_in_progress"];w.update({"mu_sdk_five_go_state":"ACTUAL_MAIN_COMMIT_LOCAL_VALIDATION_INDEPENDENTLY_REVIEWED","mu_sdk_five_go_head":commit_doc["new_head"],"mu_sdk_five_go_commit_ref":commit,"mu_sdk_five_go_local_independent_review_refs":[pin(x) for x in reviews],"mu_sdk_local_pass_top_level":22,"mu_sdk_local_typed_cancel_skipped":False,"mu_sdk_actual_provider_calls_after_local_validation":0,"mu_sdk_live_trial_state":"SOURCE_COMMIT_REBINDING_PREPARATION_NO_ACTIVE_GRANT","mu_sdk_runtime_qualification":False,"r341_observed_failure_count":679,"r341_registered_failure_count":679,"mu_sdk_next_action":"Finish new immutable runner commit/cancel binding and non-author review; Root prepare isolated controller/registration, bootstrap, then one bounded LIVE qualification and ordinary read-tool model trial."})
c["note"]="Root integrated and independently reviewed five Go changes; actual owned Git commit adc460c2138528f163f7fdab5e8d81dde157b7fb. 21 local top-level PASS plus one actual-current-Mu typed cancel PASS. No real provider calls, runtime qualification, or formal acceptance. Immutable late failure origins673-679 appended once; prior672 unchanged. Old13dirty paths preserved. W05-99 remains current."
new=(json.dumps(c,ensure_ascii=False,indent=2)+"\n").encode();(O/"checkpoint.after.proposed.json").write_bytes(new)
save("prepared.json",{"before_ref":pin(before_path),"after_ref":pin(O/"checkpoint.after.proposed.json"),"unchanged_other_refs":[pin(x) for x in others],"new_failure_refs":actual,"commit_ref":commit,"independent_review_refs":[pin(x) for x in reviews],"no_acceptance_granted":True})
assert cp.read_bytes()==raw and [x.read_bytes() for x in others]==other_raw
tmp=cp.with_name(cp.name+".r341."+uuid.uuid4().hex);tmp.write_bytes(new);os.replace(tmp,cp)
assert cp.read_bytes()==new and [x.read_bytes() for x in others]==other_raw
ref=save("checkpoint.closed.json",{"checkpoint_ref":pin(cp),"revision":341,"ownership_revision":json.loads(other_raw[0])["revision"],"registered_failure_count":679,"observed_failure_count":679,"head":commit_doc["new_head"],"current_step":"W05-99","step_state_unchanged":True,"no_formal_acceptance":True})
print(json.dumps({"checkpoint_closed_ref":ref,"checkpoint_ref":pin(cp),"registered_failure_count":679}),flush=True)
