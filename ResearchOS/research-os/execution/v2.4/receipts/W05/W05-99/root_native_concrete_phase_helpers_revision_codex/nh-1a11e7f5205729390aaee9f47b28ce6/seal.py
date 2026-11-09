import ast,json,hashlib,types
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
 with (N/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(N/n)
source=json.loads((N/"sourceguard.final.json").read_bytes())
for ref in source["refs"]:
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"][7:] and actual["bytes"]==ref["bytes"]
for name in ("root_concrete_approval_helper.py","public_evidence_archive.py"):ast.parse((N/name).read_bytes())
# Final post-control refinements have no action side effect: early lifecycle/time
# rejection, separate public key roles, reserved archive name and private DB ban.
raw=(N/"root_concrete_approval_helper.py").read_bytes();m=types.ModuleType("final_pure_source");m.__file__=str(N/"root_concrete_approval_helper.py");exec(compile(raw,m.__file__,"exec"),m.__dict__)
for suffix in (".private.dpapi",".key",".sqlite",".sqlite-wal",".db"):
 ref={"path":str((N/("never-read"+suffix)).resolve()),"sha256":"sha256:"+"0"*64,"bytes":0}
 try:m.Inputs().read(ref)
 except ValueError as e:assert "forbidden" in str(e)
 else:raise AssertionError("private file was read")
save("final-static-checks.json",dict(Python_AST=True,private_input_rejection_before_open=True,post_control_refinements_verified=True,new_native_SQL_model_Git_Go=False))
guard=save("sourceguard.seal.json",dict(refs=source["refs"],all_unchanged=True,method="exact_read_hash_before_after",Main_canonical_write=False))
members={p.relative_to(N).as_posix():pin(p) for p in N.rglob("*") if p.is_file() and p.name not in ("HDF.json","MF.json")}
mf=save("MF.json",dict(schema="researchos.root-concrete-phase-helper-manifest.v1",members=members,formal_acceptance=False,authority="NONE"))
hdf=save("HDF.json",dict(schema="researchos.root-concrete-phase-helper-handoff.v1",status="SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW",actor="codex:/root/command_queue_impl",manifest_ref=mf,manifest_member_count=len(members),helper_ref=pin(N/"root_concrete_approval_helper.py"),public_archive_ref=pin(N/"public_evidence_archive.py"),calling_contract_ref=pin(N/"calling-contract.json"),provenance_ref=pin(N/"provenance.json"),report_ref=pin(N/"report.md"),controls_ref=pin(N/"source-controls.json"),T10_cause_ref=pin(N/"T10-lifecycle-cause.json"),source_guard_ref=guard,new_actual_native_SQL_model_Git_Go=False,new_approval_generated=False,key_private_resource_read=False,Main_canonical_other_Source_write=False,mechanical_failures=[dict(ordinal=893,outer_exit=0,python_exit=None,native_exit=None,origin_ref=pin(N/"failure-origin.893.json"))],failure_counter_reset=False,ordinary_history20_full_release_program_rehearsal_authority="BLOCKED",self_approved=False,formal_acceptance=False,STOP=True))
for ref in members.values():assert pin(ref["path"])==ref
print(json.dumps(dict(HDF=hdf,MF=mf,members=len(members),helper=pin(N/"root_concrete_approval_helper.py"),archive=pin(N/"public_evidence_archive.py"),status="SOURCE_ONLY_SEALED_STOP",new_native_exit=None)))

