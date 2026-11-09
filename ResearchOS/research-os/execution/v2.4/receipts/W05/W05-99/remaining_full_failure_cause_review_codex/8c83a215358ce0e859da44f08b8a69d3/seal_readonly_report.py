import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

report = json.loads((OUT / "report.json").read_text(encoding="utf-8"))
assert report["authority"] == "NONE" and report["formal_acceptance"] is False
assert report["remaining_failed_node_count"] == 21
assert report["remaining_leaf_failed_node_count"] == 17
assert report["parent_repeat_count"] == 4
assert report["cause_count"] == 8
assert len(report["skipped_nodes"]) == 4 and all(item["acceptance"] == "NOT_ACCEPTED" for item in report["skipped_nodes"])
assert report["source_pair_count"] == report["source_actual_compiler_match_count"] == 29
assert report["source_Main_byte_equal_count"] == 26 and report["source_Main_diff_count"] == 3
assert pin(OUT / "source-pins.json") == report["source_pins_ref"]
assert pin(OUT / "Main-to-T3-deltas.patch") == report["Main_to_T3_delta_ref"]
assert report["new_failure_origins"] == [pin(OUT / "failure-origin.801.json")]
io = json.loads((OUT / "original-tool-io.json").read_text(encoding="utf-8"))
assert not io["missing_stored_keys"]
members = {str(path.relative_to(OUT)).replace("\\", "/"): pin(path) for path in sorted(OUT.rglob("*")) if path.is_file()}
manifest = {
    "schema": "researchos.readonly-cause-report-manifest.v1",
    "status": "READONLY_DIAGNOSIS_COMPLETE_PENDING_ROOT_DECISION",
    "authority": "NONE",
    "formal_acceptance": False,
    "members": members,
    "member_count": len(members),
    "report_ref": pin(OUT / "report.json"),
    "report_md_ref": pin(OUT / "report.md"),
    "source_pins_ref": pin(OUT / "source-pins.json"),
    "original_tool_io_ref": pin(OUT / "original-tool-io.json"),
    "failure_origins": [pin(OUT / "failure-origin.801.json")],
    "post_seal_exclusions": ["seal-tool-io.json", "seal-tool-io.ref.json"],
}
with (OUT / "manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
for rel, expected in members.items():
    assert pin(OUT / rel) == expected, "member drift: " + rel
print(json.dumps({
    "namespace": str(OUT),
    "member_count": len(members),
    "member_drift": 0,
    "authority": "NONE",
    "report": pin(OUT / "report.json"),
    "report_md": pin(OUT / "report.md"),
    "manifest": pin(OUT / "manifest.json"),
    "source_pins": pin(OUT / "source-pins.json"),
    "original_tool_io": pin(OUT / "original-tool-io.json"),
    "failure801": pin(OUT / "failure-origin.801.json"),
    "failure801_full_request": pin(OUT / "failure-request-input.801.js")
}, ensure_ascii=False))

