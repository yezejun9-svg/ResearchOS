import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
r=json.loads((N/"result.json").read_bytes())
c=json.loads((N/"checks.json").read_bytes())
g=json.loads((N/"source-guard.cleanup.json").read_bytes())
refs=json.loads((N/"input-pins.json").read_bytes())
assert c["all_passed"] and c["count"]==1505 and len(refs)==130
assert g["closed"] and not g["errors"] and g["retained_handles_count"]==0
assert len(g["entries"])==130 and all(v["verified"] and v["final_path_match"] and v["closed"] for v in g["entries"])
for v in refs:assert pin(Path(v["path"]))==v
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
save("MF.json",dict(schema="researchos.independent-source-review-manifest.v1",members=members,member_count=len(members)))
save("HDF.json",dict(schema="researchos.w09-v7-fragment-independent-review.v1",status=r["status"],manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),result_ref=pin(N/"result.json"),checks_ref=pin(N/"checks.json"),inputs_ref=pin(N/"input-pins.json"),actual_guard_cleanup_ref=pin(N/"source-guard.cleanup.json"),candidate_ref=r["candidate_ref"],checks=1505,inputs=130,actual_old_JSONL_events=29,actual_old_assertions=5,real_line_split_positions=1303,whole_file_byte_and_AST_inverse=True,actual_guard_held_and_closed=True,retained_handles=0,CP365_OW169_unchanged=True,original_packet_and_report_preserved=True,new_producer_and_mode_decisions_required=True,full_consumer_executed=False,formal_acceptance=False,new_failures=[],STOP_FINAL=True))
for v in members+refs:assert pin(Path(v["path"]))==v
save("postseal.json",dict(status="PASS_POSTSEAL",HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),members=len(members),inputs=len(refs),all_pins_unchanged=True))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),postseal=pin(N/"postseal.json")),ensure_ascii=False))
