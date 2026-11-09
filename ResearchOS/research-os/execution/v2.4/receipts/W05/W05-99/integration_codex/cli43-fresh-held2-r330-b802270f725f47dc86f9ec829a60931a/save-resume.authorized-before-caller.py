"""Actual authorized before-caller resume; read-only canonical check, exclusive new receipt."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,hashlib,datetime
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent;BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(name,v):
 with (OUT/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
parser=argparse.ArgumentParser();parser.add_argument("--grant-sha256",required=True);args=parser.parse_args()
scopep=OUT/"scope_registration.json";assert pin(scopep)["sha256"]=="b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359"
scope=read(scopep);gp=Path(scope["new_authorization_root"])/"authorization.execute.json";assert pin(gp)["sha256"]==args.grant_sha256
grant=read(gp);assert grant["status"]=="ROOT_REGISTERED_EXECUTION_AUTHORIZED" and grant["actual_registration_completed"] is True and grant["binding"]["expected_registration"]==[330,158,502]
canon=[]
for row in grant["canonical_copies"]:
 actual=pin(ROOT/row["canonical_path"]);assert (actual["sha256"],actual["bytes"])==(row["ref"]["sha256"],row["ref"]["bytes"]);canon.append(actual)
cp=read(ROOT/"execution/v2.4/checkpoint.json");ow=read(ROOT/"execution/v2.4/path_ownership.json");assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[330,158,502]
assert not any(Path(scope[k]).exists() for k in ("new_output_root","new_wrapper_root","new_export_root")) and not (OUT/"root-launch.intent.json").exists()
prevp=BASE/"integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/RESUME.transport-preparation.snapshot.json";prev=read(prevp)
late=[]
for p in (prevp.parent/"failure-origin.task-packet-path-guess.json",OUT/"failure-origin.c873de.json"):
 original=read(p);assert original["outer_exit"]==1 and original["native_exit"] is None
 late.append({"origin":p.stem,"ref":pin(p),"actual_outer_exit":1,"actual_native_exit":None,"original_payload_unchanged":True})
snapshot={"schema":"researchos.root-resume.authorized.v2","actor":"codex:/root","snapshot_stage":"R330_REGISTERED_SEALED_AUTHORIZED_NOT_EXECUTED_BEFORE_CALLER","at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"actual_registered_tuple":[330,158,502],"live_canonical_refs_equal_actual_grant_copies":canon,"current_head_by_actual_registration_and_grant":cp["head"],"scope_ref":pin(scopep),"binding_ref":pin(OUT/"binding.json"),"grant_ref":pin(gp),"grant_driver_manifest_ref":pin(OUT/"grant-driver.manifest.json"),"run_driver_manifest_ref":pin(OUT/"registration-run-driver.manifest.json"),"seal_driver_manifest_ref":pin(OUT/"registration-seal-driver.manifest.json"),"actual_metadata_tool_observations_ref":pin(OUT/"root-metadata.tool-observations.after-grant.json"),"previous_immutable_snapshot_ref":pin(prevp),"fixed_cut_ref":pin(OUT/"failure-origins.cut.json"),"fixed_cut_origins":21,"outside_fixed_cut":late,"known_observed_origin_count":504,"fresh_case_qualification":False,"source_branches":{"transport_candidate":"SOURCE_REVIEWED_NOT_NATIVE_QUALIFIED","driver18_root_adapter_handoff_ref":pin(BASE/"f08_driver18_root_binding_preparation_codex/a03c54991b5b44f9bdb6743d8b78b0c9/handoff.json"),"driver18_partial17":"NOT_RUN; native resources/CAS/grant producer still OPEN","I17":"new66ec R01/R02 static reviewed, actual producer/callback/SQL NOT_RUN","Desktop15":"HOLD_PENDING_FRESH43_ACTUAL_QUALIFICATION"},"completion_gate":{"parents_required":22,"formal_required":42,"all_must_be_effectively_accepted":True,"formal_current_accepted_last_verified":0},"cleanup_pending":prev["cleanup_pending"],"credential_policy":prev["credential_policy"],"next_action":"Prepare new caller from immutable r329 two constants; nonauthor review; invoke new scope/grant once; preserve actual observations and request independent qualification.","formal_increment":0,"source_acceptance":False,"canonical_writes":0,"automatic_retry":False,"counter_reset":False}
save("RESUME.authorized.before-caller.snapshot.json",snapshot)
save("RESUME.authorized.before-caller.snapshot.manifest.json",{"self_excluded":True,"members":[pin(OUT/"save-resume.authorized-before-caller.py"),pin(OUT/"RESUME.authorized.before-caller.snapshot.json")]})
print(json.dumps({"snapshot_ref":pin(OUT/"RESUME.authorized.before-caller.snapshot.json"),"manifest_ref":pin(OUT/"RESUME.authorized.before-caller.snapshot.manifest.json"),"actual_tuple":[330,158,502],"observed":504},ensure_ascii=False))
