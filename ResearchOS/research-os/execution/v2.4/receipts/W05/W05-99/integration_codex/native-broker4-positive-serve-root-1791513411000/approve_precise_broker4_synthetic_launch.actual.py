import sys,json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
C=B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller.public.config.json"
SP=O/"serve_one_positive_broker4.actual_owned.py";AP=B/"integration_codex/native-broker4-positive-root-api-1791513411000/root_public_api_broker4.actual.py"
GP=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
Z=Path(sys.argv[1]).resolve()
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def check(p,h,n):
 q=pin(p);assert(q["sha256"],q["bytes"])==(h,n);return q
hr=check(Z/"HDF.json",sys.argv[2],int(sys.argv[3]));mr=check(Z/"MF.json",sys.argv[4],int(sys.argv[5]))
cr=check(C,"48c06dc2c88326a98cd785b364d6daf5fad363292a7a4f97fd209938d54273b2",1178613)
sr=check(SP,"31295d5c366b9671e3e3b293ee80111d9b4ac2db22c667ca83c8567907148f06",5857)
ar=check(AP,"6eeae42516cdb6cad02f09555747c103e4e736c0ca4752dfe210a66c975fb04b",14698)
gpr=check(GP,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404)
cfg=json.loads(C.read_bytes());hcpath=Path(cfg["HarnessConfig"]["path"]);hcr=check(hcpath,cfg["HarnessConfig"]["sha256"].removeprefix("sha256:"),cfg["HarnessConfig"]["bytes"])
canonical=R/"execution/v2.4/checkpoint.json";assert pin(canonical)["sha256"]=="84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b"
gm=types.ModuleType("root_t10_launch_guard");gm.__file__=str(GP);exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire([hr,mr,cr,sr,ar,gpr,hcr,pin(__file__),pin(sys.executable)])
try:
 hd=json.loads(g.get_buffer(str((Z/"HDF.json").resolve())))
 assert hd.get("decision",hd.get("status"))=="COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL"
 hc=json.loads(g.get_buffer(str(hcpath.resolve())))
 assert hc["Case"]=="positive-replay" and hc["CaseID"]=="t10b4c239054ab67"
 assert hc["BrokerSource"]["role"]=="broker-source" and hc["BrokerSource"]["sha256"]=="sha256:70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c" and hc["BrokerSource"]["bytes"]==8562
 assert not Path(cfg["ControllerDirectory"]).exists() and not Path(hc["OutputDirectory"]).exists()
 for p in (SP,AP):compile(g.get_buffer(str(p.resolve())),str(p),"exec")
 approval=dict(schema="researchos.root-precise-synthetic-native-launch-approval.v1",action="LAUNCH_ONE_FRESH_MANUALLY_REVIEWED_SYNTHETIC_POSITIVE",approved_at=datetime.now(timezone.utc).isoformat(),approved_by="codex:/root",config_ref=cr,serve_ref=sr,api_ref=ar,independent_review_handoff_ref=hr,independent_review_manifest_ref=mr,case=hc["Case"],case_id=hc["CaseID"],native_case_launch_limit=1,auto_approve_signing=False,auto_refresh_TTL=False,original_trial_touched=False,formal_acceptance=False)
 with (O/"root-precise-launch-approval.json").open("xb") as f:f.write((json.dumps(approval,ensure_ascii=True,indent=2)+"\n").encode())
 print(json.dumps(dict(root_precise_approval_ref=pin(O/"root-precise-launch-approval.json"))),flush=True)
finally:
 cleanup=g.close()
 with (O/"launch-approval-guard.cleanup.json").open("xb") as f:f.write((json.dumps(cleanup,ensure_ascii=True,indent=2)+"\n").encode())
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0


