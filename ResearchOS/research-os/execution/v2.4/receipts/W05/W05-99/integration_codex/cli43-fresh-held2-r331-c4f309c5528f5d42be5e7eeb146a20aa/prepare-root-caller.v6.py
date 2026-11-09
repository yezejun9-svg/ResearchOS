"""Source-only caller preparation from immutable actual r330 caller; two constants only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,ast,hashlib,json
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r330-b802270f725f47dc86f9ec829a60931a/root-launch-once.v2.py"
OLD_SCOPE=b"b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359"
OLD_GRANT=b"c0fe594c2fc6109b95ab6d829eff98b580f6f9d8bf0c95e30e9f7f8b61b91375"
NEW_SCOPE=b"f71b60ad316aa3034ff3da5cd79c6aac4c4e5997425d86e7b84d2f9fc02ec89b"
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
p=argparse.ArgumentParser();p.add_argument("--grant-sha256",required=True);p.add_argument("--snapshot-sha256",required=True);args=p.parse_args()
assert all(len(v)==64 and all(c in "0123456789abcdef" for c in v) for v in (args.grant_sha256,args.snapshot_sha256))
sp=OUT/"scope_registration.json";assert pin(sp)["sha256"]==NEW_SCOPE.decode()
scope=read(sp);assert scope["expected_registration"]==[331,159,509]
gp=Path(scope["new_authorization_root"])/"authorization.execute.json";assert pin(gp)["sha256"]==args.grant_sha256
grant=read(gp);assert grant["actual_registration_completed"] is True and grant["status"]=="ROOT_REGISTERED_EXECUTION_AUTHORIZED" and grant["scope_ref"]["sha256"]==NEW_SCOPE.decode()
assert not any(Path(scope[k]).exists() for k in ("new_output_root","new_wrapper_root","new_export_root"))
assert not any((OUT/n).exists() for n in ("root-launch.intent.json","root-launch.stdout.raw","root-launch.stderr.raw","root-launch.invocation.json","root-launch-once.v2.py"))
snap=OUT/"RESUME.authorized.before-caller.snapshot.json";assert pin(snap)["sha256"]==args.snapshot_sha256
snapshot=read(snap);late=snapshot["outside_fixed_cut"];assert snapshot["known_observed_origin_count"]==509+len(late) and snapshot["actual_registered_tuple"]==[331,159,509] and snapshot["actual_launch_started"] is False
for row in late:assert pin(row["ref"]["path"])==row["ref"]
canonical=[]
for row in grant["canonical_copies"]:
 actual=pin(ROOT/row["canonical_path"]);assert (actual["sha256"],actual["bytes"])==(row["ref"]["sha256"],row["ref"]["bytes"]);canonical.append(actual)
assert canonical==snapshot["live_canonical_refs_equal_actual_grant_copies"]
assert pin(OLD)["sha256"]=="6dc45827cbf010382c638c39a86f08b9b7202e02a4bb4e901ea733035b9deba4"
old=OLD.read_bytes();assert old.count(OLD_SCOPE)==old.count(OLD_GRANT)==1
newg=args.grant_sha256.encode();new=old.replace(OLD_SCOPE,NEW_SCOPE).replace(OLD_GRANT,newg)
assert new.replace(NEW_SCOPE,OLD_SCOPE).replace(newg,OLD_GRANT)==old
ast.parse(new.decode())
with (OUT/"root-launch-once.v2.py").open("xb") as f:f.write(new)
save("root-caller-preparation.json",{"actor":"codex:/root","source_only":True,"old_caller_ref":pin(OLD),"new_caller_ref":pin(OUT/"root-launch-once.v2.py"),"preparer_ref":pin(__file__),"scope_ref":pin(sp),"grant_ref":pin(gp),"changed_constants_only":["SCOPE_SHA","GRANT_SHA"],"whole_byte_inverse_equal":True,"AST_parsed_without_execution":True,"executor_launcher_export_absent":True,"launch_outputs_absent":True,"canonical_refs_equal_actual_grant_copies":canonical,"launcher_executed":False,"Go_SQL_SDK_Model_HTTP_calls":0,"automatic_retry":False,"counter_reset":False,"formal_increment":0,"registered_origin_count":509,"observed_origin_count_at_snapshot":509+len(late),"late_origins_outside_sealed_registration_cut_at_snapshot":late,"late_origins_snapshot_ref":pin(snap),"late_origin_note":"Original outer/native NULLs and all historical counters preserved; no additional retries."})
print(json.dumps({"caller_ref":pin(OUT/"root-launch-once.v2.py"),"preparation_ref":pin(OUT/"root-caller-preparation.json"),"scope_ref":pin(sp),"grant_ref":pin(gp)},ensure_ascii=False))
