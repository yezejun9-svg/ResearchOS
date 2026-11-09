import ast,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 p=N/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
refs=json.loads((N/"sourceguard.initial.json").read_bytes())["refs"]
for ref in refs:assert pin(ref["path"])==ref
choice=json.loads((N/"source.integration.choice.json").read_bytes());contract=json.loads((N/"execution-contract.json").read_bytes())
assert pin(N/"source.integration.choice.json")==contract["choice_ref"]
for key in ("worktree","isolation_output","target_output","scratch"):assert not Path(contract[key]).exists()
repls=json.loads((N/"source-replacements.json").read_bytes())
for key in ("prepare","validate"):
 text=(N/(key+"_attach_fixture_two_parent.actual_owned.py")).read_text(encoding="utf-8")
 ast.parse(text)
 for pair in reversed(repls[key]):
  assert text.count(pair["new"])==1
  text=text.replace(pair["new"],pair["old"],1)
 assert text==(N/"base"/(key+".py")).read_text(encoding="utf-8")
assert choice["source_preserved_parent_count"]==54 and choice["source_preserved_nonselected_parent_count"]==52
final=save("sourceguard.seal.json",dict(method="exact_source_pin_recheck",all_unchanged=True,input_count=len(refs),refs=refs,future_actual_paths_absent=True,canonical_read_write=False,actual_Git_Go_SQL_native_model=False))
members={p.relative_to(N).as_posix():pin(p) for p in N.rglob("*") if p.is_file() and p.name not in ("HDF.json","MF.json")}
mf=save("MF.json",dict(schema="researchos.root-two-parent-caller-source-manifest.v1",members=members,authority="NONE",formal_acceptance=False))
hdf=save("HDF.json",dict(schema="researchos.root-two-parent-caller-source-handoff.v1",status="SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL",actor="codex:/root/command_queue_impl",manifest_ref=mf,manifest_member_count=len(members),prepare_ref=pin(N/"prepare_attach_fixture_two_parent.actual_owned.py"),validate_ref=pin(N/"validate_attach_fixture_two_parent.actual_owned.py"),choice_ref=pin(N/"source.integration.choice.json"),contract_ref=pin(N/"execution-contract.json"),report_ref=pin(N/"report.md"),source_guard_ref=final,static_ref=pin(N/"static-preservation.json"),preflight_ref=pin(N/"source-composition-preflight.json"),source_member_count=58,previous_target_parent_count=54,exact_parent_names=choice["exact_parent_names"],other52_parent_sources_preserved_not_executed=True,ordinary_history20_full_release_program_rehearsal_authority="BLOCKED",self_approved=False,formal_acceptance=False,production_ready=False,new_failures=[],failure_counter_reset=False,actual_Git_Go_SQL_native_model=False,Main_canonical_old_Source_writes=False,STOP=True))
assert pin(mf["path"])==mf and pin(hdf["path"])==hdf
for ref in members.values():assert pin(ref["path"])==ref
print(json.dumps(dict(HDF=hdf,MF=mf,members=len(members),guard=final,status="SOURCE_ONLY_SEALED_STOP",actual_Git_Go_SQL_native_model=False)))

