"""Reconstruct overwritten source-only seal bytes in this separate annex."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
SOURCE = ROOT / "execution/v2.4/receipts/W09/W09-99/w09_evidence_revision_source_preparation_codex/fdbee1676fd64d8b9a93ce81076c6c4c"


def checked_write(name, raw, expected_sha, expected_size):
    actual_sha = hashlib.sha256(raw).hexdigest()
    assert (actual_sha, len(raw)) == (expected_sha, expected_size), (name, actual_sha, len(raw))
    path = HERE / name
    with path.open("xb") as file:
        file.write(raw)
    return {"sha256": actual_sha, "bytes": len(raw),
            "path": str(path.relative_to(ROOT)).replace("\\", "/")}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


report = (SOURCE / "report.v4.json").read_text(encoding="utf-8")
report = report.replace('"failure_origins_new": 2,', '"failure_origins_new": 1,')
report = report.replace(
    '"failure_origin_note": "Two independent read-only rg paths failed once: a literal Windows wildcard and an absent guessed source file. Original bridges emitted only stderr text, so wrapper exit fields remain NULL in failure-origin-01/02.json; neither input was retried.",',
    '"failure_origin_note": "A read-only rg query used a literal Windows wildcard path and failed once. Original bridge emitted only stderr text, so wrapper exit fields remain NULL in failure-origin-01.json; no retry of that input.",')
report = report.replace(
    '"root_cut": "Fourth cut48->580 unchanged; these source findings after cut are pending observed581/582 registration by Root.",',
    '"root_cut": "Fourth cut48->580 unchanged; this source finding after cut is pending observed581 registration by Root.",')
old_report = checked_write("report.prior-seal.json", report.encode(),
                           "3204a3053e7bbc805418df4cd229ea943f266d345400eecfd0540e046db65ab0", 2500)

sealer = (SOURCE / "seal_packet.py").read_text(encoding="utf-8")
sealer = sealer.replace('"failure_origin_refs": [pin(HERE / "failure-origin-01.json"), pin(HERE / "failure-origin-02.json")],',
                        '"failure_origin_ref": pin(HERE / "failure-origin-01.json"),')
old_sealer_raw = sealer.encode()
old_sealer = checked_write("seal_packet.prior-seal.py.txt", old_sealer_raw,
                           hashlib.sha256(old_sealer_raw).hexdigest(), len(old_sealer_raw))

manifest = json.loads((SOURCE / "manifest.json").read_bytes())
assert manifest["member_count"] == 36
members = []
for member in manifest["members"]:
    name = Path(member["path"]).name
    if name == "failure-origin-02.json":
        continue
    if name == "report.v4.json":
        member.update(sha256=old_report["sha256"], bytes=old_report["bytes"])
    if name == "seal_packet.py":
        member.update(sha256=old_sealer["sha256"], bytes=old_sealer["bytes"])
    members.append(member)
manifest["members"] = members
manifest["member_count"] = 35
old_manifest = checked_write("manifest.prior-seal.json", encoded(manifest),
                             "f72e09bea8ff99356276d896bbf8c24a5b124650fb82f077bd512dbdcc7356f0", 10209)

handoff = json.loads((SOURCE / "handoff.json").read_bytes())
assert "failure_origin_refs" in handoff
handoff["failure_origin_ref"] = handoff.pop("failure_origin_refs")[0]
handoff["report_ref"].update(sha256=old_report["sha256"], bytes=old_report["bytes"])
handoff["manifest_ref"].update(sha256=old_manifest["sha256"], bytes=old_manifest["bytes"])
old_handoff = checked_write("handoff.prior-seal.json", encoded(handoff),
                            "a26de8bc7888fe333e14be08728d3ddff737385ad3b1be4afc1a37226d8668ea", 3434)
print(json.dumps({"status": "PRIOR_SEAL_BYTES_RECOVERED", "refs": [old_report, old_sealer,
                    old_manifest, old_handoff]}, ensure_ascii=False))
