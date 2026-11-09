import sys,json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller.public.config.json"
P=B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller-runtime/review-snapshot-release-4ac4b921ce4446f89115b2971dba47bd.json"
GP=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256="sha256:"+hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v["path"]);assert(q["sha256"],q["bytes"])==(v["sha256"],v["bytes"]);return q
sr=pin(P);assert (sr["sha256"],sr["bytes"])==("sha256:0840169e2cd3d543908623edebbc377ea009822d4d6b8e1c393cd7b725048dbb",705453)
snap=json.loads(P.read_bytes());cfg=json.loads(C.read_bytes());hc=json.loads(Path(cfg["HarnessConfig"]["path"]).read_bytes())
cr=verify(snap["config_ref"]);assert cr==pin(C) and snap["case_id"]=="t10b4c239054ab67" and snap["phase"]==snap["sign_kind"]=="release"
pr=verify(snap["payload_ref"]);assert(pr["sha256"],pr["bytes"])==("sha256:80bcdf1f5c798dc9014d5c374c5af5d9148f37e666852a57999f45ee7385702c",181961)
payload=json.loads(Path(pr["path"]).read_bytes())
assert payload["schema"]=="researchos.recovery-release.v1" and payload["purpose"]=="RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1"
assert payload["id"]=="synthetic-native-t10b4c239054ab67" and payload["sid"]=="S-1-5-21-2314176124-1781180693-2759285857-1001"
assert payload["root_signing_public_key"]=="d5d735ecd3296beb4ee68d59da4f7503d7db34b310e0642d9f8b19c5c454e4b5"
assert payload["root_image"]==hc["RootProgram"] and payload["control_image"]==hc["ControlProgram"] and payload["source_root"]==hc["BuildRoot"]
assert len(payload["source_files"])==599
for v in payload["source_files"]:
 p=Path(v["path"]).resolve();root=Path(hc["BuildRoot"]).resolve();assert p.is_relative_to(root) and v["role"]=="source:"+p.relative_to(root).as_posix()
before=datetime.fromisoformat(payload["not_before_utc"].replace("Z","+00:00"));expiry=datetime.fromisoformat(payload["expires_utc"].replace("Z","+00:00"))
assert before<=datetime.now(timezone.utc)<expiry
assert pin(GP)["sha256"]=="sha256:e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
gm=types.ModuleType("root_release_review_guard");gm.__file__=str(GP);exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
refs=[sr,cr,pr,pin(GP),pin(__file__),pin(sys.executable),verify(cfg["HarnessConfig"]),verify(payload["root_image"]),verify(payload["control_image"])]
refs += [verify(v) for v in payload["source_files"]]
g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire([dict(path=v["path"],sha256=v["sha256"].removeprefix("sha256:"),bytes=v["bytes"]) for v in refs])
try:
 assert json.loads(g.get_buffer(str(P.resolve())))==snap
 approval=dict(Schema="researchos.root-native-concrete-approval.v1",Action="SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD",ConfigSHA256=cr["sha256"],Snapshot=sr,Payload=pr,SignedDestination=snap["signed_destination"],SignKind="release")
 p=O/"release.sign.approval.json"
 with p.open("xb") as f:f.write((json.dumps(approval,ensure_ascii=True,indent=2)+"\n").encode())
 print(json.dumps(dict(approval_ref=pin(p),source_refs_held=len(refs),payload_expiry_unchanged=True)),flush=True)
finally:
 cleanup=g.close()
 with (O/"release-sign-approval.guard-closure.json").open("xb") as f:f.write((json.dumps(cleanup,ensure_ascii=True,indent=2)+"\n").encode())
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0


