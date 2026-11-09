import json,hashlib,ast
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
 with (N/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(N/n)
candidate=(N/"root_native_migration_controller.py").read_bytes();text=candidate.decode()
for r in reversed(json.loads((N/"source-replacements.json").read_bytes())):
 assert text.count(r["new"])==1;text=text.replace(r["new"],r["old"],1)
assert text.encode()==(N/"base/root_native_migration_controller.py").read_bytes()
ast.parse(candidate)
for r in json.loads((N/"sourceguard.final.json").read_bytes())["refs"]:assert pin(r["path"])==r
members={p.relative_to(N).as_posix():pin(p) for p in N.rglob("*") if p.is_file() and p.name not in ("HDF.json","MF.json")}
mf=save("MF.json",dict(schema="researchos.native-controller-retained-window-manifest.v1",members=members,authority="NONE",formal_acceptance=False))
hdf=save("HDF.json",dict(schema="researchos.native-controller-retained-window-handoff.v1",status="SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ACTUAL",actor="codex:/root/command_queue_impl",manifest_ref=mf,manifest_member_count=len(members),source_ref=pin(N/"root_native_migration_controller.py"),base_ref=pin(N/"base/root_native_migration_controller.py"),report_ref=pin(N/"report.md"),controls_ref=pin(N/"deadline-coordination-controls.json"),prerequisites_ref=pin(N/"prerequisites.json"),source_guard_ref=pin(N/"sourceguard.final.json"),only_three_constants_changed=True,exact_inverse_original_bytes=True,all_other_AST_unchanged=True,new_case_deadline_seconds=1560,new_owned_seconds=1560,new_loop_seconds=1570,Go25_main20_cleanup4_grant4_privatebroker180_unchanged=True,Root_new_Config_FrozenInputs_and_non_author_review_required=True,actual_API_native_Go_SQL_Git_model=False,new_mechanical_failures=[],failure_counter_reset=False,Main_canonical_old_Source_write=False,self_approved=False,formal_acceptance=False,native_retention_qualified=False,STOP=True))
for ref in members.values():assert pin(ref["path"])==ref
print(json.dumps(dict(HDF=hdf,MF=mf,members=len(members),candidate=pin(N/"root_native_migration_controller.py"),status="SOURCE_ONLY_SEALED_STOP",native_exit=None)))

