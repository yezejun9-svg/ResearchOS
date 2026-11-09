import sys,json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return {"path":str(p),"sha256":"sha256:"+hashlib.sha256(b).hexdigest(),"bytes":len(b)}
CP=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-controller-config-root-1791508950616/controller.public.config.json")
SN=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-controller-config-root-1791508950616/controller-runtime/review-snapshot-fixture-retained-412f004bdb68481b83dc94781cdfc5d2.json")
IP=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-positive-root-api-1791509017626/inspection-positive.json")
assert pin(CP)["sha256"]=="sha256:19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af"
assert pin(SN)["sha256"]=="sha256:51d509ce0f9ea57b532222791ba406bf0e2cf5901a4c31dff1c0676a69c886d8"
assert pin(IP)["sha256"]=="sha256:7dfe6d48b8bfb560a31ea7830a22497440e2f62a1a27a3b325b54a37038d3409"
snap=json.loads(SN.read_bytes());q=json.loads(IP.read_bytes())
assert q["fixture_read_complete"] and q["whole_row_schema_review_complete"] and q["transaction_snapshot_complete"] and q["primary_and_WAL_bytes_unchanged"]
assert q["data_version_before"]==q["data_version_after"] and q["schema_versions"]==list(range(1,24))
assert q["expected_state_matches"] is False and not q["private_credentials_recorded"] and not q["private_raw_rows_recorded"]
assert q["native_ids"]==snap["measured_native_ids"]
before=Path(q["before_ref"]["path"]);assert pin(before)==q["before_ref"]
assert q["typed_rows"]==json.loads(before.read_bytes()),"Failed broker preflight baseline must be whole-row unchanged"
assert all(q[k]["closed"] and q[k]["retained_handles_count"]==0 and not q[k]["errors"] for k in ("reader_guard_cleanup","database_guard_cleanup"))
approval={"Schema":"researchos.root-native-fixture-release.v1","Action":"RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION","ConfigSHA256":pin(CP)["sha256"],"Snapshot":pin(SN),"InspectionReceipt":pin(IP)}
p=O/"root-specific-fixture-release-approval.json"
with p.open("xb") as f:f.write((json.dumps(approval,ensure_ascii=True,indent=2)+"\n").encode())
print(json.dumps({"approval_ref":pin(p),"failed_fixture_whole_SQL_matches_before":True,"native_positive_accepted":False}))
