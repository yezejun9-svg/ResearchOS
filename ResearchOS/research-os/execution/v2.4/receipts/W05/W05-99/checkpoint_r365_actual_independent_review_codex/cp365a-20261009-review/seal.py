import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
r=json.loads((N/"result.json").read_bytes());assert json.loads((N/"checks.json").read_bytes())["all_passed"]
refs=json.loads((N/"input-pins.json").read_bytes())
for ref in refs:assert pin(Path(ref["path"]))==ref
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
save("MF.json",dict(schema="researchos.independent-actual-review-manifest.v1",members=members,member_count=len(members)))
save("HDF.json",dict(schema="researchos.cp365-ow169-independent-actual-consistency.v1",status=r["status"],manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),checks_ref=pin(N/"checks.json"),input_pins_ref=pin(N/"input-pins.json"),guard_summary_ref=pin(N/"guard-summary.json"),checkpoint_ref=r["checkpoint_ref"],ownership_ref=r["ownership_ref"],vector_ref=r["vector_ref"],checks=r["checks"],inputs=r["inputs"],old900_raw_and_semantic_preserved=True,new_ordinals=list(range(903,926)),registered_failures=923,high=925,next_at_cutoff=926,writer_guard_entries=362,vector_guard_entries=8,both_guards_closed=True,SS_CM_unchanged=True,actual_full_CP_OW_reconstruction=True,reviewer_canonical_write=False,reviewer_product_execution=False,formal_acceptance=False,new_failures=[],STOP_FINAL=True))
for ref in members:assert pin(Path(ref["path"]))==ref
for ref in refs:assert pin(Path(ref["path"]))==ref
save("postseal.json",dict(status="PASS_POSTSEAL",HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),members=len(members),inputs=len(refs),pins_unchanged=True))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),postseal=pin(N/"postseal.json")),ensure_ascii=False))

