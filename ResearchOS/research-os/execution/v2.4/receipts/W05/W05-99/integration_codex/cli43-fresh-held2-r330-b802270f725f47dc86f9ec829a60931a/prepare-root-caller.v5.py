"""Source-only caller preparation from r329 bytes; actual grant/snapshot must already exist."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,ast,hashlib,json
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/root-launch-once.v2.py"
OLD_SCOPE=b"90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0"
OLD_GRANT=b"55efa0fbd05a9776fa2fcf5c12f360c8846cd39695c4c0f34a9fea7813631221"
NEW_SCOPE=b"b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359"
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(name,v):
 with (OUT/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
parser=argparse.ArgumentParser();parser.add_argument("--grant-sha256",required=True);parser.add_argument("--snapshot-sha256",required=True);args=parser.parse_args()
assert all(len(v)==64 and all(c in "0123456789abcdef" for c in v) for v in (args.grant_sha256,args.snapshot_sha256))
scope_path=OUT/"scope_registration.json";assert pin(scope_path)["sha256"]==NEW_SCOPE.decode()
scope=read(scope_path);assert scope["expected_registration"]==[330,158,502]
grant_path=Path(scope["new_authorization_root"])/"authorization.execute.json"
assert pin(grant_path)["sha256"]==args.grant_sha256
grant=read(grant_path);assert grant["actual_registration_completed"] is True and grant["status"]=="ROOT_REGISTERED_EXECUTION_AUTHORIZED" and grant["scope_ref"]["sha256"]==NEW_SCOPE.decode()
assert not any(Path(scope[k]).exists() for k in ("new_output_root","new_wrapper_root","new_export_root"))
assert not any((OUT/n).exists() for n in ("root-launch.intent.json","root-launch.stdout.raw","root-launch.stderr.raw","root-launch.invocation.json","root-launch-once.v2.py"))
snapshot_path=OUT/"RESUME.authorized.before-caller.snapshot.json";assert pin(snapshot_path)["sha256"]==args.snapshot_sha256
snapshot=read(snapshot_path);late=snapshot["outside_fixed_cut"];assert len(late)==2 and snapshot["known_observed_origin_count"]==504 and snapshot["actual_registered_tuple"]==[330,158,502]
for row in late:assert pin(row["ref"]["path"])==row["ref"]
canon=[]
for row in grant["canonical_copies"]:
 actual=pin(ROOT/row["canonical_path"]);assert (actual["sha256"],actual["bytes"])==(row["ref"]["sha256"],row["ref"]["bytes"]);canon.append(actual)
assert canon==snapshot["live_canonical_refs_equal_actual_grant_copies"]
assert pin(OLD)["sha256"]=="524996a0cde5f78f651c733b8e45c9b6ed48f11dabac628a8846e6bc458f0875"
old=OLD.read_bytes();assert old.count(OLD_SCOPE)==old.count(OLD_GRANT)==1
new_grant=args.grant_sha256.encode();new=old.replace(OLD_SCOPE,NEW_SCOPE).replace(OLD_GRANT,new_grant)
assert new.replace(NEW_SCOPE,OLD_SCOPE).replace(new_grant,OLD_GRANT)==old
ast.parse(new.decode(),filename="root-launch-once.v2.py")
with (OUT/"root-launch-once.v2.py").open("xb") as f:f.write(new)
save("root-caller-preparation.json",{"actor":"codex:/root","source_only":True,"old_caller_ref":pin(OLD),"new_caller_ref":pin(OUT/"root-launch-once.v2.py"),"preparer_ref":pin(__file__),"scope_ref":pin(scope_path),"grant_ref":pin(grant_path),"changed_constants_only":["SCOPE_SHA","GRANT_SHA"],"whole_byte_inverse_equal":True,"AST_parsed_without_execution":True,"executor_launcher_export_absent":True,"launch_outputs_absent":True,"canonical_refs_equal_actual_grant_copies":canon,"launcher_executed":False,"Go_SQL_SDK_Model_HTTP_calls":0,"automatic_retry":False,"counter_reset":False,"formal_increment":0,"registered_origin_count":502,"observed_origin_count_at_snapshot":504,"late_origins_outside_sealed_registration_cut_at_snapshot":late,"late_origins_snapshot_ref":pin(snapshot_path),"late_origin_note":"Two actual read-only diagnostic origins remain outside fixed cut. Original outer/native NULLs and all historical counters preserved; no additional retries."})
print(json.dumps({"caller_ref":pin(OUT/"root-launch-once.v2.py"),"preparation_ref":pin(OUT/"root-caller-preparation.json"),"scope_ref":pin(scope_path),"grant_ref":pin(grant_path)},ensure_ascii=False))
