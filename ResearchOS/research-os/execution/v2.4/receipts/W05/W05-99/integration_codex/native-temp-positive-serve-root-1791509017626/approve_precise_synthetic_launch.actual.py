import sys,json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
Z=B/"native_temp_prelaunch_actual_independent_review_codex/b5bf0ed767204b69a82b86acff0e23f1"
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def module(p,b):
 m=types.ModuleType("root_launch_guard");m.__file__=str(p);exec(compile(b,str(p),"exec"),m.__dict__);return m
assert pin(Z/"HDF.json")["sha256"]=="0659037dfc6759e0de7d0994b166f6430a2dd8f92d3a2cc99c9cff3f3667fc24"
assert pin(Z/"MF.json")["sha256"]=="ec5f88f86d098eae397cd55c289460a591c5c3991684091882948e7d4d700526"
C=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-controller-config-root-1791508950616/controller.public.config.json");assert pin(C)["sha256"]=="19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af" and pin(C)["bytes"]==1163646
SP=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-positive-serve-root-1791509017626/serve_one_positive_temp.actual_owned.py");AP=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-positive-root-api-1791509017626/root_public_api_temp.actual.py")
GP=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
assert pin(GP)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
gm=module(GP,GP.read_bytes());refs=[pin(p) for p in (Z/"HDF.json",Z/"MF.json",C,SP,AP,GP,Path(__file__))]
g=gm.SourceReadGuard();g.acquire(refs)
try:
 hd=json.loads(g.get_buffer(str((Z/"HDF.json").resolve())))
 assert hd["decision"]=="COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL"
 cfg=json.loads(g.get_buffer(str(C.resolve())))
 assert not Path(cfg["ControllerDirectory"]).exists()
 hc=json.loads(Path(cfg["HarnessConfig"]["path"]).read_bytes());assert hc["Case"]=="positive-replay" and not Path(hc["OutputDirectory"]).exists()
 for p in (SP,AP):compile(g.get_buffer(str(p.resolve())),str(p),"exec")
 approval={"schema":"researchos.root-precise-synthetic-native-launch-approval.v1","action":"LAUNCH_ONE_FRESH_MANUALLY_REVIEWED_SYNTHETIC_POSITIVE","approved_at":datetime.now(timezone.utc).isoformat(),"approved_by":"codex:/root","config_ref":pin(C),"serve_ref":pin(SP),"api_ref":pin(AP),"independent_review_handoff_ref":pin(Z/"HDF.json"),"independent_review_manifest_ref":pin(Z/"MF.json"),"case":hc["Case"],"case_id":hc["CaseID"],"native_case_launch_limit":1,"auto_approve_signing":False,"auto_refresh_TTL":False,"original_trial_touched":False,"formal_acceptance":False}
 p=O/"root-precise-launch-approval.json"
 with p.open("xb") as f:f.write((json.dumps(approval,ensure_ascii=True,indent=2)+"\n").encode())
 print(json.dumps({"root_precise_approval_ref":pin(p),"serve_ref":pin(SP),"api_ref":pin(AP)}))
finally:
 c=g.close()
 with (O/"launch-approval-guard.cleanup.json").open("xb") as f:f.write((json.dumps(c,ensure_ascii=True,indent=2)+"\n").encode())
 assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
