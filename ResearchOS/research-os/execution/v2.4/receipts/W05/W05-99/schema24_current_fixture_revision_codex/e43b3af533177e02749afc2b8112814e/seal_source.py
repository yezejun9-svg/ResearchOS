import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409")
SOURCE_FILES = [
    "internal/domain/backup_command_queue_test.go",
    "internal/domain/backup_host_configuration_test.go",
    "internal/domain/client_configuration_test.go",
]
DEPENDENCIES = [
    "internal/domain/domain_test.go",
    "internal/domain/backup_configuration_upgrade_test.go",
    "internal/domain/backup_prepared_abandonment_upgrade.go",
]

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write_json(name, obj):
    raw = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with (OUT / name).open("xb") as stream:
        stream.write(raw)

base_refs = json.loads((OUT / "base-refs.json").read_text(encoding="utf-8"))
source_refs = json.loads((OUT / "source-refs.json").read_text(encoding="utf-8"))
assert sorted(base_refs) == sorted(SOURCE_FILES)
assert sorted(source_refs) == sorted(SOURCE_FILES)
assert sorted(str(p.relative_to(OUT / "candidate-root")).replace("\\", "/") for p in (OUT / "candidate-root").rglob("*") if p.is_file()) == sorted(SOURCE_FILES)
for rel in SOURCE_FILES:
    assert pin(BASE / rel) == base_refs[rel], "base drift at seal: " + rel
    source_actual = pin(OUT / "candidate-root" / rel)
    source_expected = {key: source_refs[rel][key] for key in ["path", "sha256", "bytes"]}
    assert source_actual == source_expected, "source drift at seal: " + rel
static = json.loads((OUT / "static-evidence.json").read_text(encoding="utf-8"))
assert len(static["checks"]) == 9 and all(item["result"] is True for item in static["checks"])
assert static["source_file_count"] == 3
dependency_refs = {rel: pin(BASE / rel) for rel in DEPENDENCIES}
write_json("dependency-refs.json", dependency_refs)
members = {
    str(p.relative_to(OUT)).replace("\\", "/"): pin(p)
    for p in sorted(OUT.rglob("*"))
    if p.is_file()
}
assert not {"MF.json", "HDF.json"}.intersection(members)
manifest_sources = {"candidate-root/" + rel: source_refs[rel] for rel in SOURCE_FILES}
write_json("MF.json", {
    "schema": "researchos.source-manifest.v1",
    "formal": False,
    "authority": "NONE",
    "members": members,
    "member_count": len(members),
    "source_refs": manifest_sources,
    "base_refs": list(base_refs.values()),
    "dependency_refs": dependency_refs,
    "closure_exclusions": ["MF.json", "HDF.json", "seal-tool-io.json", "seal-tool-io.ref.json"],
})
write_json("HDF.json", {
    "schema": "researchos.schema24-current-fixture-revision-handoff.v1",
    "status": "SOURCE_IMPLEMENTED_PENDING_ROOT_TESTS_AND_INDEPENDENT_REVIEW",
    "sourceStatus": "EXECUTION_REPORTED",
    "formal": False,
    "production_ready": False,
    "authority": "NONE",
    "execution_authority": False,
    "author_role": "SOURCE_AUTHOR_ONLY",
    "task_id": "W05/W05-99",
    "base_root": str(BASE),
    "source_root": str(OUT / "candidate-root"),
    "source_file_count": 3,
    "source_refs": manifest_sources,
    "base_refs": base_refs,
    "base_refs_ref": pin(OUT / "base-refs.json"),
    "dependency_refs": dependency_refs,
    "dependency_refs_ref": pin(OUT / "dependency-refs.json"),
    "manifest_ref": pin(OUT / "MF.json"),
    "contract_ref": pin(OUT / "CONTRACT.md"),
    "construction_input_ref": pin(OUT / "construction-input.json"),
    "constructor_ref": pin(OUT / "construct_source.py"),
    "patch_ref": pin(OUT / "revision.patch"),
    "static_evidence_ref": pin(OUT / "static-evidence.json"),
    "original_tool_io_ref": pin(OUT / "original-tool-io.json"),
    "seal_invocation_ref": pin(OUT / "seal-input.json"),
    "seal_receipt_paths": [str(OUT / "seal-tool-io.json"), str(OUT / "seal-tool-io.ref.json")],
    "source_delta": {
        "backup_command_queue_test.go": "Current exact release24 (25 SQL inputs including additive); continuous count/max/emptyQueue/SQL22 and full historical22 remain.",
        "client_configuration_test.go": "Only actual_Service_New expected version23 becomes24; both fixed22-to23 branches and all other bytes remain.",
        "backup_host_configuration_test.go": "Original parent has current24/historical23 real New subcases; full original body shared with only explicit Restore supported-version parameter."
    },
    "static_check_count": 9,
    "input_drift_count": 0,
    "historical23_scope": "Production New and current public API initialized using fixed schema23 numbered/additive inventory and matching contracts. No frozen historical executable or native acceptance claim.",
    "actual_author_execution": {
        "python_metadata_source_writes": True,
        "go": False,
        "gofmt": False,
        "tests": False,
        "sql": False,
        "native": False,
        "git": False,
        "provider": False,
        "original_database": False,
        "private_credentials": False,
        "Main_write": False,
        "T3_write": False,
        "canonical_write": False
    },
    "failure_origins": [],
    "failure_counter_reset": False,
    "composition_note": "Compose only these three complete files onto Root's separately pinned full T3 composition in a new isolated test root. This author package changes no production Source and no independent native fixture Source.",
    "remaining_gates": [
        "Root format/build in a new isolated composition.",
        "Root closed actual tests for the three affected parent tests, current24/historical23 PublicReplay subcases, and retained fixed22 branches.",
        "Root completed necessary historical/full offline regression and native validation receipts.",
        "Another agent independent Source delta and closed actual-result review.",
        "Existing project-wide acceptance of all22 parent tasks and42 formal cases."
    ]
})
for relative, expected in members.items():
    assert pin(OUT / relative) == expected, "manifest member drift: " + relative
handoff = json.loads((OUT / "HDF.json").read_text(encoding="utf-8"))
assert pin(OUT / "MF.json") == handoff["manifest_ref"]
print(json.dumps({
    "namespace": str(OUT),
    "source_root": str(OUT / "candidate-root"),
    "member_count": len(members),
    "source_count": len(manifest_sources),
    "source_refs": manifest_sources,
    "base_drift": 0,
    "member_drift": 0,
    "authority": "NONE",
    "HDF": pin(OUT / "HDF.json"),
    "MF": pin(OUT / "MF.json"),
    "patch": pin(OUT / "revision.patch"),
    "original_tool_io": pin(OUT / "original-tool-io.json"),
    "static_evidence": pin(OUT / "static-evidence.json"),
    "base_refs": pin(OUT / "base-refs.json")
}, ensure_ascii=False))

