"""Prepare a fresh Root request from completed, independently reviewed inputs."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys, types, uuid
R=Path("D:/作品集/ResearchOS/research-os")
V=R/"execution/v2.4"
W=V/"receipts/W09/W09-99"
N=Path(__file__).resolve().parent
REG=W/"w09_nf4_root_registration_source_codex/register-20261010-02"
AUTHOR="codex:/root/attach_restore_independent_review"
entry=REG/"register_w09_adoption.source.py"
raw=entry.read_bytes()
assert len(raw)==31679 and hashlib.sha256(raw).hexdigest()=="eccd6415f1531a3def1573f158ed915648d07d1a80dc21b34c6f43bcdedf5323"
api=types.ModuleType("root_nf5_reviewed_registrar")
api.__file__=str(entry)
exec(compile(raw,api.__file__,"exec"),api.__dict__)
pin=api.pin
inputs=api.doc(pin(sys.argv[1]))
assert inputs["schema"]=="researchos.root-nf5-preparation-inputs.v1" and inputs["issued_by"]=="codex:/root"
assert inputs["formal_acceptance"] is False
source=api.doc(pin(REG/"input-pins.json"))
current=[pin(p) for p in api.CANON]
cp=api.doc(current[0])
assert cp["revision"]==377 and cp["work_in_progress"]["root_next_failure_ordinal_live"]==1134
pending=inputs["pending_ref"]
pending_value=api.doc(pending)
assert pending_value["current_canonical_refs"]==current
assert [x["ordinal"] for x in pending_value["pending"]]==list(range(1134,pending_value["next_original_failure_ordinal"]))
assert pending_value["issued_by"]=="codex:/root" and pending_value["counter_reset"] is False
pr=inputs["producer_review_refs"]
rr=inputs["registrar_review_refs"]
assert set(pr)==set(rr)=={"hdf","mf","decision"}
pd=api.doc(pr["decision"])
rd=api.doc(rr["decision"])
assert pd["decision"]=="SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE"
assert rd["decision"]=="SOURCE_ACCEPTED_FOR_ROOT_NF4_REGISTRATION"
assert pd["actor_id"]==rd["actor_id"]!="codex:/root" and pd["actor_id"]!=AUTHOR
old_path=N/"w09.native-scopes-ad02.0b3e193c2c04437eadcea7a0bee5164b.request.actual.root.json"
old=api.doc(pin(old_path))
start=datetime.now(timezone.utc)
def lease(minutes):
    return dict(lease_id=uuid.uuid4().hex,lease_issued_at=start.isoformat(),
                lease_expires_at=(start+timedelta(minutes=minutes)).isoformat())
cid=uuid.uuid4().hex
parent=api.OUTPUT_BASE
assert parent.parent==W
if not parent.exists():
    api.path_checked(str(parent),True)
    parent.mkdir()
api.path_checked(str(parent))
out=parent/cid
assert not out.exists()
peers=dict(source["peer_audit_refs"])
peers["producer-author"]=pin(N/"w09.nf5-source-author.actual-audit.root.json")
peers["producer-review"]=inputs["producer_review_audit_ref"]
q=dict(old,generation="fullw09-20261010-05",created_utc=start.isoformat(),case_id=cid,output_root=str(out),
       before_canonical_refs=current,pending_ref=pending,
       source_handoff_ref=pin(REG/"HDF.json"),source_manifest_ref=pin(REG/"MF.json"),
       source_review_handoff_ref=rr["hdf"],source_review_manifest_ref=rr["mf"],source_review_decision_ref=rr["decision"],
       source_author_audit_ref=pin(N/"w09.nf5-registrar-author.actual-audit.root.json"),
       source_review_audit_ref=inputs["registrar_review_audit_ref"],
       producer_review_handoff_ref=pr["hdf"],producer_review_manifest_ref=pr["mf"],producer_review_decision_ref=pr["decision"],
       reviewed_source_audits_ref=source["refs"]["peer_audits"],reviewed_source_audit_refs=peers,
       lease=lease(55),native_leases={key:lease(50) for key in ("W09-G01","W09-G02","A06","C19")},
       main_profile_ref=pin(V/"formal_profile_w09.py"),formal_index_ref=pin(V/"formal_case_index.py"))
assert set(q)==api.REQUEST_FIELDS
api.require(all(q[k] is False for k in ("formal_acceptance","parent_acceptance","formal_dispatcher","automatic_retry")),"ROOT_FALSE_GRANTS")
ref=api.save(N/("w09.nf5-registration."+cid+".request.actual.root.json"),q)
print(json.dumps(dict(request_ref=ref,case_id=cid,generation=q["generation"],current_canonical_refs=current,
                      runtime_not_invoked=True,canonical_unchanged=True,formal_acceptance=False),ensure_ascii=False))
