"""Seal actual Root grant/canonical pins and pending original origins before caller preparation."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,argparse
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
a=argparse.ArgumentParser();a.add_argument("--grant-sha256",required=True);a.add_argument("--pending-origin",action="append",default=[]);args=a.parse_args()
scopep=OUT/"scope_registration.json";assert pin(scopep)["sha256"]=="f71b60ad316aa3034ff3da5cd79c6aac4c4e5997425d86e7b84d2f9fc02ec89b"
scope=read(scopep);assert scope["expected_registration"]==[331,159,509]
gp=Path(scope["new_authorization_root"])/"authorization.execute.json";assert pin(gp)["sha256"]==args.grant_sha256
grant=read(gp);assert grant["status"]=="ROOT_REGISTERED_EXECUTION_AUTHORIZED" and grant["actual_registration_completed"] is True and grant["scope_ref"]["sha256"]==pin(scopep)["sha256"]
assert not any(Path(scope[k]).exists() for k in ("new_output_root","new_wrapper_root","new_export_root"))
canonical=[]
for row in grant["canonical_copies"]:
 actual=pin(ROOT/row["canonical_path"]);assert (actual["sha256"],actual["bytes"])==(row["ref"]["sha256"],row["ref"]["bytes"]);canonical.append(actual)
cp=read(ROOT/"execution/v2.4/checkpoint.json");ow=read(ROOT/"execution/v2.4/path_ownership.json")
assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[331,159,509]
late=[]
for raw in args.pending_origin:
 p=Path(raw);ref=pin(p);assert not any(r.get("evidence_ref",{}).get("sha256")==ref["sha256"] for r in cp["failure_counters"])
 late.append({"ref":ref,"original_payload":read(p),"native_NULL_preserved":True})
assert len({r["ref"]["sha256"] for r in late})==len(late)
save("RESUME.authorized.before-caller.snapshot.json",{"schema":"researchos.authorized-before-caller-resume.v2","actor":"codex:/root","actual_registered_tuple":[331,159,509],"known_observed_origin_count":509+len(late),"outside_fixed_cut":late,"live_canonical_refs_equal_actual_grant_copies":canonical,"scope_ref":pin(scopep),"grant_ref":pin(gp),"metadata_tool_observations_ref":pin(OUT/"root-metadata.tool-observations.after-grant.json"),"actual_launch_started":False,"executor_launcher_export_absent":True,"current_formal_acceptance":"0/42","all22parents_effectively_accepted":False,"source_acceptance":False,"formal_increment":0,"counter_reset":False,"immutable_previous_resume_snapshots_changed":False})
save("RESUME.authorized.before-caller.snapshot.manifest.json",{"self_excluded":True,"entries":[pin(OUT/"RESUME.authorized.before-caller.snapshot.json"),pin(__file__)]})
print(json.dumps({"snapshot_ref":pin(OUT/"RESUME.authorized.before-caller.snapshot.json"),"manifest_ref":pin(OUT/"RESUME.authorized.before-caller.snapshot.manifest.json"),"registered_tuple":[331,159,509],"known_observed":509+len(late)},ensure_ascii=False))
