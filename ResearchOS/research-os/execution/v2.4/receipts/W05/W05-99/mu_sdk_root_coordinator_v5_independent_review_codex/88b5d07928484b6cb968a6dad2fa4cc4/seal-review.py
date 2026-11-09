import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parent.parent
C=B/"mu_sdk_root_coordinator_source_v5_codex/14882883e85f4e849eb087a01800e22d"
P=B/"mu_sdk_root_coordinator_v4_independent_review_codex/a576a6bb513846a4b4636de1ca6eda54"
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def put(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(p)
h=json.loads((C/"handoff.json").read_bytes());inputs=json.loads((O/"review-evidence.json").read_bytes())
assert pin(C/"handoff.json")["sha256"]=="79dd8422fc9550d2076facad33842ad2203cd5a508c9a9af2e8dc2e629aace01"
for r in (h["source_ref"],h["fixed_pins_ref"],h["manifest_ref"]):assert pin(r["path"])==r
review=dict(schema="researchos.root-sdk-coordinator-source-review.v1",actor_id="codex:/root/w05_merge_review",decision="READY_SOURCE_ONLY",source_ref=h["source_ref"],fixed_pins_ref=h["fixed_pins_ref"],source_handoff_ref=pin(C/"handoff.json"),source_manifest_ref=h["manifest_ref"],prior_independent_review_ref=pin(P/"review.json"),candidate_authors=["codex:/root","codex:/root/command_queue_impl"],formal_acceptance=False,execution_authority=False,review_scope="Independent C5 delta from the completed C4 full Source review; exact R01/R02 fixes and unchanged execution methods",closed_findings=[
dict(id="R01",status="CLOSED",evidence="Unmodified actual prepare-runtime and finalize-prepare receipts pass. Only path-valued argv positions use absolute Windows Path equality; flag order, values and length remain exact. Actual finalize order is preserved."),
dict(id="R02",status="CLOSED",evidence="All four original closures are required; lifecycle continuation records equal pinned originals; before-resume flags are strict booleans; owner/PID/creation/native exit bind to original lifecycle and invocation; finite typed fresh proof and watchdog/producer duplicates are checked. Original Host planned 0xE0000508 exit is distinguished from the three successful exit-zero commands.")
],verification=inputs["pure_result"],source_guard_review="The loader collects staged caller plus all four closure, invocation and original before-resume refs. open adds them to the acquired Source guard and revalidates; prepare binds preparation invocation refs and revalidates the chain. No newly consumed nested file is omitted.",evidence_refs=[pin(O/"review-evidence.json"),pin(O/"seal-review.py")],new_tool_failures=[],limits=["READY_SOURCE_ONLY is not Root execution authority, runtime qualification or formal acceptance.","Actual staged receipts were read as Root-produced inputs; no preparation or candidate process was rerun.","Original C4 blocked review remains intact and is superseded only for these fixed Source findings."],candidate_module_imported=False,coordinator_methods_executed=False,Native_WinAPI_SQL_provider_calls=0,Main_canonical_writes=0,stopped=True)
rr=put("review.json",review)
assert review["schema"]=="researchos.root-sdk-coordinator-source-review.v1" and review["decision"]=="READY_SOURCE_ONLY" and review["actor_id"] not in {"codex:/root","codex:/root/command_queue_impl","",None} and review["formal_acceptance"] is False
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mf=put("manifest.json",dict(schema="researchos.independent-review-packet-manifest.v1",actor_id=review["actor_id"],members=members,member_count=len(members),excludes_self_and_handoff=True))
hd=put("handoff.json",dict(schema="researchos.root-coordinator-independent-review-handoff.v1",actor_id=review["actor_id"],decision=review["decision"],review_ref=rr,manifest_ref=mf,source_ref=h["source_ref"],fixed_pins_ref=h["fixed_pins_ref"],closed_findings=["R01","R02"],new_tool_failures=[],formal_acceptance=False,execution_authority=False,stopped=True))
assert all(pin(r["path"])==r for r in members)
print(json.dumps(dict(handoff_ref=hd,manifest_ref=mf,review_ref=rr,members_verified=len(members)),ensure_ascii=True))

