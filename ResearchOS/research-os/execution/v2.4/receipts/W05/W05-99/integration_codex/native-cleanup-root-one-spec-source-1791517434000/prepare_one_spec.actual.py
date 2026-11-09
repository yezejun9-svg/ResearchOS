"""Prepare exactly one inert C12 specification from an explicitly pinned snapshot."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,re
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99"
C=B/"integration_codex/native-cleanup-controller-source-root-1791517434000/controller.public.config.json"
Q=B/"integration_codex/native-cleanup-manual-requests-root-1791517434000"
P=R/".local/native-cleanup-compile-env-1791516889000/programs"
AP=B/"integration_codex/native-cleanup-positive-root-api-1791517434000"
META=B/"integration_codex/recoveryauthority-key-provision-root-9b42b8e7072a40b1/key-provision.closed.json"
refs=[]
def pin(p,bare=False):
 p=Path(p).resolve();assert p.is_file() and not p.is_symlink()
 assert p.suffix.lower()==".json" and not any(x in p.name.lower() for x in (".private.",".dpapi",".key",".sqlite"))
 raw=p.read_bytes();v=dict(path=str(p),sha256=("" if bare else "sha256:")+hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 refs.append((v,bare));return v
def checked(v,bare=False):
 assert set(v)=={"path","sha256","bytes"} and type(v["bytes"]) is int and v["bytes"]>=0
 assert re.fullmatch("[0-9a-f]{64}" if bare else "sha256:[0-9a-f]{64}",v["sha256"])
 observed=pin(v["path"],bare);assert observed==v;return json.loads(Path(v["path"]).read_bytes())
assert len(sys.argv) in (7,8),"Mode Action Phase SnapshotPath SnapshotSHA256 SnapshotBytes [ExpectedFixtureState]"
mode,action,phase=sys.argv[1:4]
assert mode in ("helper-request","api-arguments")
assert (phase in ("release","grant") and action in ("sign","publish")) or (phase=="fixture-retained" and action in ("inspect","release-fixture"))
assert not (mode=="helper-request" and action=="inspect")
assert (len(sys.argv)==8)==(mode=="helper-request" and action=="release-fixture")
if len(sys.argv)==8:assert sys.argv[7] in ("migrated","unchanged-failed")
config=dict(path=str(C.resolve()),sha256="sha256:38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256",bytes=1106152)
cfg=checked(config);hc=checked(cfg["HarnessConfig"])
assert hc["CaseID"]=="t12cl149d6f49321" and Path(hc["RootProgram"]["path"]).parent==P
assert Q.is_dir()
for parent in (Path(cfg["ControllerDirectory"]),Path(hc["OutputDirectory"]),Path(hc["BuildRoot"]),Path(cfg["Environment"]["TEMP"]),P):
 assert not Q.is_relative_to(parent) and not parent.is_relative_to(Q)
snapshot=dict(path=str(Path(sys.argv[4]).resolve()),sha256=sys.argv[5],bytes=int(sys.argv[6]))
snap=checked(snapshot);assert snap["config_ref"]==config and snap["case_id"]==hc["CaseID"] and snap["phase"]==phase
spec=dict(Schema="researchos.c12-one-root-request-preparation.v1",Mode=mode,Action=action,Phase=phase,Config=config,Snapshot=snapshot)
if mode=="helper-request":
 metadata=dict(path=str(META.resolve()),sha256="sha256:873953117beb0f5730674d130e49c18502b6e5821ea37f5658af3c80f1e7d5fe",bytes=2375)
 checked(metadata) # Public metadata only; contained private references are never followed.
 spec.update(PublicKeyMetadata=metadata,SID="S-1-5-21-2314176124-1781180693-2759285857-1001",IssuerPublicKey="936929c4ad26612ee75cc4ad5a6dc2d8c0f898bf974bb9c01e8e5140ee207bdf",RootSigningPublicKey="d5d735ecd3296beb4ee68d59da4f7503d7db34b310e0642d9f8b19c5c454e4b5")
 if action=="release-fixture":
  spec.update(InspectionReceipt=pin(AP/"inspection-positive.json",True),ExpectedFixtureState=sys.argv[7])
 else:
  spec["Payload"]=snap["payload_ref"];checked(spec["Payload"])
  if phase=="grant":spec["ReleaseDocument"]=pin(P/"recovery-release.json")
  if action=="publish":
   receipt=pin(Path(cfg["ControllerDirectory"])/("sign-"+phase+".receipt.json"));signed=checked(receipt)
   assert signed["success"] is True and signed["phase"]==phase and signed["config_ref"]==config and signed["payload_ref"]==snap["payload_ref"]
   spec.update(SigningReceipt=receipt,SignedDocument=signed["signed_ref"]);checked(spec["SignedDocument"])
elif action!="inspect":
 spec["Approval"]=pin(Q/("approval."+phase+"."+action+".json"));checked(spec["Approval"])
for v,bare in list(refs):assert pin(v["path"],bare)==v
dest=Q/("spec."+mode+"."+phase+"."+action+".json")
with dest.open("xb") as f:f.write((json.dumps(spec,ensure_ascii=True,indent=2)+"\n").encode())
print(json.dumps(dict(spec_ref=pin(dest),mode=mode,action=action,phase=phase,execute=False,approvals_generated=0,signatures=0,private_references_followed=0,formal_acceptance=False)))

