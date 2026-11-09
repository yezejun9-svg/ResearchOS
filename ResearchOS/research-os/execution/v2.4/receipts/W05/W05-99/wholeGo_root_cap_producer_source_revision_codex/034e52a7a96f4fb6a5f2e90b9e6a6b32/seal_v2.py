import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent
oldroot = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_preparation_codex/a378e6d62865446ab78312d5efabb458")

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def put(name, doc):
    p = root / name
    with p.open("xb") as out:
        out.write((json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return pin(p)

source = root / "wholego_cap_metadata.v2.proposed.py"
text = source.read_text(encoding="utf-8")
ast.parse(text)
compile(text, str(source), "exec", dont_inherit=True)
inverse = json.loads((root / "source-inverse.json").read_text(encoding="utf-8"))
assert inverse["new_ref"] == pin(source)
assert inverse["old_ref"] == pin(oldroot / "wholego_cap_metadata.proposed.py")
assert inverse["exact_old_block"] not in text
assert text.count(inverse["exact_new_block"]) == 1
assert (text.replace(inverse["exact_new_block"], inverse["exact_old_block"]) ==
        (oldroot / "wholego_cap_metadata.proposed.py").read_text(encoding="utf-8"))
old_hdf = pin(oldroot / "handoff.json")
old_report = pin(oldroot / "report.json")
report = put("report.json", {"schema": "researchos.current58-whole-go-cap-producer-source-revision-report.v2",
    "stage": "SOURCE_PREPARATION_ONLY", "supersedes_source_ref": inverse["old_ref"],
    "supersedes_handoff_ref": old_hdf, "selected_source_ref": pin(source),
    "source_inverse_ref": pin(root / "source-inverse.json"),
    "delta": "Match selected gate rev4 heartbeat ABI: require same-root path, monotonic_tick, time.monotonic() age <=5s; remove unsupported observed_unix wall clock key.",
    "old_source_report_ref": old_report,
    "static_checks": {"python_ast": "PASS", "whole_byte_inverse": "PASS", "target_go_cli_model_calls": 0},
    "actual_authority": None, "source_acceptance": False, "whole58_test_suite_qualified": False,
    "formal_case_accepted_delta": 0, "new_tool_failure_origins": []})
members = [pin(p) for p in sorted(root.iterdir()) if p.is_file() and p.name not in {"manifest.json", "handoff.json"}]
manifest = put("manifest.json", {"schema": "researchos.current58-whole-go-cap-producer-revision-manifest.v2",
                          "members": members, "member_count": len(members), "source_acceptance": False})
handoff = put("handoff.json", {"schema": "researchos.current58-whole-go-cap-producer-revision-handoff.v2",
    "status": "STOPPED_SOURCE_PREPARATION_ONLY", "source_ref": pin(source), "report_ref": report,
    "manifest_ref": manifest, "source_inverse_ref": pin(root / "source-inverse.json"),
    "prior_handoff_ref": old_hdf, "old_source_do_not_adopt": True,
    "Root_next": "Independent review selected v2 source; retain old packet for provenance. No execution grant or suite/formal qualification is implied.",
    "formal_case_accepted_delta": 0})
print(json.dumps({"report": report, "manifest": manifest, "handoff": handoff}, ensure_ascii=False))
