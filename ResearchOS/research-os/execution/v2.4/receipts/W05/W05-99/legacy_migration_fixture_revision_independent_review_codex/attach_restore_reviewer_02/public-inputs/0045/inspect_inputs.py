import sys
sys.dont_write_bytecode = True
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent
OLD = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9")
REVIEW = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_independent_review_codex/4ec609adce7346a9b8fe61e898a8a15e")
def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def verify(item):
    actual = ref(item["path"])
    assert actual["sha256"] == item["sha256"] and actual["bytes"] == item["bytes"], "pin mismatch: " + item["path"]
def copy_file(source, target):
    target = Q / target
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as f:
        f.write(Path(source).read_bytes())
    return {"source_ref": ref(source), "snapshot_ref": ref(target)}
def selected_lines(path, anchors, before=1, after=30):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    indices = set()
    for i, line in enumerate(lines):
        if any(anchor in line for anchor in anchors):
            indices.update(range(max(0, i-before), min(len(lines), i+after+1)))
    return [{"line": i+1, "text": lines[i]} for i in sorted(indices)]
def main():
    meta = json.loads((Q / "review-metadata-verification.json").read_text(encoding="utf-8"))
    hdf = meta["HDF"]
    for item in meta["refs"].values():
        verify(item)
    review_mf = json.loads((REVIEW / "MF.json").read_text(encoding="utf-8"))
    for item in review_mf["members"]:
        verify(item)
    for key in ["subject", "subject_manifest", "report", "findings", "verification", "input_pins", "author_postseal"]:
        verify(hdf[key])
    old_mf = json.loads((OLD / "MANIFEST.json").read_text(encoding="utf-8"))
    for item in old_mf["members"]:
        verify(item)
    snapshots = []
    for name in ["report.md", "findings.json", "static-verification.json", "input-pins.json"]:
        snapshots.append(copy_file(REVIEW / name, "inputs/review/" + name))
    for name in ["domain_test.go", "context_test.go"]:
        source = REVIEW / "inputs/dependencies" / name
        snapshots.append(copy_file(source, "inputs/dependencies/" + name))
    for name in ["HANDOFF.json", "MANIFEST.json", "inspection.json", "verification.json",
                 "construction.json", "migration-resources.json", "historical20-resource-entry.json",
                 "source-pins.json", "case-mapping.json", "contract-excerpts.json", "failure-origin.833.json"]:
        snapshots.append(copy_file(OLD / name, "inputs/previous-source/" + name))
    old_hdf = json.loads((OLD / "HANDOFF.json").read_text(encoding="utf-8"))
    for item in old_hdf["candidate_members"]:
        source = Path(item["path"])
        relative = source.relative_to(OLD).as_posix()
        snapshots.append(copy_file(source, "inputs/previous-source/" + relative))
    source_pins = {
        "authority": "NONE",
        "review_HDF_ref": meta["refs"]["HDF.json"],
        "review_MF_ref": meta["refs"]["MF.json"],
        "previous_HDF_ref": hdf["subject"],
        "previous_MF_ref": hdf["subject_manifest"],
        "verified_review_members": len(review_mf["members"]),
        "verified_previous_members": len(old_mf["members"]),
        "review_status": hdf["status"],
        "review_report_ref": hdf["report"],
        "review_findings_ref": hdf["findings"],
        "snapshots": snapshots,
    }
    (Q / "input-pins.json").write_text(json.dumps(source_pins, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = {
        "authority": "NONE",
        "review": (REVIEW / "report.md").read_text(encoding="utf-8"),
        "finding": json.loads((REVIEW / "findings.json").read_text(encoding="utf-8")),
        "rollback_and_helper_callsite_lines": selected_lines(OLD / "candidate-root/internal/domain/client_session_bootstrap_test.go",
            ["func TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction"], 1, 32),
        "helper_source": (OLD / "candidate-root/internal/domain/legacy_migration_fixture_test.go").read_text(encoding="utf-8"),
        "setup_lines": selected_lines(REVIEW / "inputs/dependencies/domain_test.go", ["func setup("], 1, 58),
        "contextFixture_lines": selected_lines(REVIEW / "inputs/dependencies/context_test.go", ["func contextFixture("], 1, 20),
        "verified_review_members": len(review_mf["members"]),
        "verified_previous_members": len(old_mf["members"]),
    }
    (Q / "inspection.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
exit_code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    exit_code = 1
finally:
    print("ROOT_PYTHON_EXIT=" + str(exit_code))
sys.exit(exit_code)

