import sys,json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller.public.config.json"
S=B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller-runtime/review-snapshot-grant-966f1d5d2bde46e88a30d1ec34e1e628.json"
GP=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def pin(p):
 p=Path(p).resolve();r=p.read_bytes();return dict(path=str(p),sha256="sha256:"+hashlib.sha256(r).hexdigest(),bytes=len(r))
def verify(v):
 q=pin(v["path"]);assert(q["sha256"],q["bytes"])==(v["sha256"],v["bytes"]);return q
sr=pin(S);assert(sr["sha256"],sr["bytes"])==("sha256:07809f00455194cdbeb748a69e253b92dc62b439dc96022395ff95b5a8bc0acf",102366)
snap=json.loads(S.read_bytes());cr=verify(snap["config_ref"]);cfg=json.loads(C.read_bytes());hc=json.loads(Path(cfg["HarnessConfig"]["path"]).read_bytes())
assert cr==pin(C) and snap["case_id"]=="t10b4c239054ab67" and snap["phase"]=="grant" and snap["sign_kind"]=="migration-grant"
pr=verify(snap["payload_ref"]);payload=json.loads(Path(pr["path"]).read_bytes());binding=payload["binding"]
assert payload["schema"]=="researchos.recovery-migration-grant.v1" and payload["purpose"]=="RESEARCHOS_PREPARED_SCHEMA23_TO24_V1" and payload["stage"]=="APPLY_ORIGINAL"
assert payload["release_sha256"]=="sha256:2382bbca3fee118b79f2e35fa339d61df1587b58faf22f8c423be991c9e16b0a"
assert len(payload["nonce"])==64 and all(x in "0123456789abcdef" for x in payload["nonce"])
assert binding["plan_id"]=="schema23-to24-prepared-abandonment-v1" and binding["owner_root"]=="queue-upgrade-owner"
assert binding["root_identity"]==snap["measured_native_ids"]["root"] and binding["database_identity"]==snap["measured_native_ids"]["database"]
assert Path(binding["root"]).resolve().is_relative_to(Path(cfg["Environment"]["TEMP"]).resolve()) and Path(binding["database"]).resolve().parent==Path(binding["root"]).resolve()
assert binding["source_schema_sha256"]=="sha256:64af7b608a633263a06ba6e0432809de03cd350a665ca8b247bcbfe34b0b755f"
assert binding["target_schema_sha256"]=="sha256:41223fcb381b49228a86b943a8e385e0de500381bda96118518badfce77a25c0"
assert binding["sql_sha256"]=="sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098"
assert binding["original_rows_sha256"]=="sha256:f85d72860491b4735b920591f5f61158cdd59f45776d3d461b4a0fe388edc894"
assert binding["target_release_sha256"]==hc["ControlProgram"]["sha256"] and payload["options"]["Plan"]==binding["plan_id"]
issued=datetime.fromisoformat(payload["issued_utc"].replace("Z","+00:00"));expiry=datetime.fromisoformat(payload["expires_utc"].replace("Z","+00:00"))
assert (expiry-issued).total_seconds()==240 and issued<=datetime.now(timezone.utc)<expiry
refs=[sr,cr,pr,pin(GP),pin(__file__),pin(sys.executable),verify(cfg["HarnessConfig"])]
def collect(value):
 if isinstance(value,dict):
  if {"path","sha256","bytes"}.issubset(value):refs.append(verify(value))
  else:
   for x in value.values():collect(x)
 elif isinstance(value,list):
  for x in value:collect(x)
collect(payload);refs += [verify(v) for v in snap["evidence_refs"]]
assert pin(GP)["sha256"]=="sha256:e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
gm=types.ModuleType("root_grant_review_guard");gm.__file__=str(GP);exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
refs=list({v["path"].casefold():v for v in refs}.values());g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire([dict(path=v["path"],sha256=v["sha256"].removeprefix("sha256:"),bytes=v["bytes"]) for v in refs])
try:
 a=dict(Schema="researchos.root-native-concrete-approval.v1",Action="SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD",ConfigSHA256=cr["sha256"],Snapshot=sr,Payload=pr,SignedDestination=snap["signed_destination"],SignKind="migration-grant")
 p=O/"grant.sign.approval.json"
 with p.open("xb") as f:f.write((json.dumps(a,ensure_ascii=True,indent=2)+"\n").encode())
 print(json.dumps(dict(approval_ref=pin(p),payload_ref=pr,binding_keys=list(binding),absolute_expiry=payload["expires_utc"],no_TTL_refresh=True,held_public_refs=len(refs))),flush=True)
finally:
 cleanup=g.close()
 with (O/"grant-sign-approval.guard-closure.json").open("xb") as f:f.write((json.dumps(cleanup,ensure_ascii=True,indent=2)+"\n").encode())
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0


