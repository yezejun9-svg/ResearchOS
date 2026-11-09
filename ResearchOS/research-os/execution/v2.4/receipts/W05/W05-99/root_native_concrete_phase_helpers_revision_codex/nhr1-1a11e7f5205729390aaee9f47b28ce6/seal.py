import ast,json,hashlib
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
 with (N/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(N/n)
r=json.loads((N/"source-replacements.json").read_bytes());candidate=(N/"root_concrete_approval_helper.py").read_text(encoding="utf-8")
inverse=candidate.replace(r["new_call"],r["old_call"],1).replace(r["new_helper"],"",1)
assert inverse.encode()==(N/"base/root_concrete_approval_helper.py").read_bytes()
ast.parse(candidate)
guard=json.loads((N/"sourceguard.final.json").read_bytes())
for ref in guard["refs"]:
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"].removeprefix("sha256:") and actual["bytes"]==ref["bytes"]
prov=save("provenance.json",dict(finding="NHR-001",base_helper=pin(N/"base/root_concrete_approval_helper.py"),new_helper=pin(N/"root_concrete_approval_helper.py"),only_existing_call_changed="retained: plain(q.database_ref) -> inspection_database_ref(q.database_ref)",new_pure_function="inspection_database_ref",exact_inverse_bytes=True,all_other_AST_functions_classes_unchanged=True,no_global_normalization=True,ordinary_receipt_bare_SHA256=True,public_RawPin_prefixed_SHA256_unchanged=True,archive_exact_copy=True,source_controls=40))
members={p.relative_to(N).as_posix():pin(p) for p in N.rglob("*") if p.is_file() and p.name not in ("HDF.json","MF.json")}
mf=save("MF.json",dict(schema="researchos.root-concrete-helper-NHR001-revision-manifest.v1",members=members,authority="NONE",formal_acceptance=False))
hdf=save("HDF.json",dict(schema="researchos.root-concrete-helper-NHR001-revision-handoff.v1",status="SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW",actor="codex:/root/command_queue_impl",finding="NHR-001",manifest_ref=mf,manifest_member_count=len(members),helper_ref=pin(N/"root_concrete_approval_helper.py"),archive_ref=pin(N/"public_evidence_archive.py"),provenance_ref=prov,report_ref=pin(N/"report.md"),static_ref=pin(N/"static-preservation.json"),controls_ref=pin(N/"source-controls.json"),guard_ref=pin(N/"sourceguard.final.json"),old27_controls_preserved=True,new13_contract_controls=True,public_RawPin_unchanged=True,actual_API_entrypoint_native_Go_SQL_Git_model=False,approval_generated=False,private_or_database_read=False,new_failures=[],failure_counter_reset=False,Main_canonical_old_Source_write=False,self_approved=False,formal_acceptance=False,STOP=True))
for ref in members.values():assert pin(ref["path"])==ref
print(json.dumps(dict(HDF=hdf,MF=mf,members=len(members),helper=pin(N/"root_concrete_approval_helper.py"),status="SOURCE_ONLY_SEALED_STOP",native_exit=None)))

