"""Seal the independent, Source-only review without touching Canon or execution."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

here = Path(__file__).resolve().parent
source = here.parent.parent / "fresh_main23_root_caller_registration_source_codex" / "main23root-20261009-01"

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write_new(name, value):
    path = here / name
    with path.open("xb") as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return ref(path)

def read(path):
    return json.loads(Path(path).read_bytes())

def main():
    author_hdf_ref = ref(source / "HDF.json")
    author_mf_ref = ref(source / "MF.json")
    author = read(source / "HDF.json")
    assert author["manifest_ref"] == author_mf_ref
    assert author["caller_ref"] == author["registrar_ref"] == ref(source / "main23_root.source.py")
    controls_ref = ref(here / "source-review-controls.json")
    controls = read(controls_ref["path"])
    assert [x["result"] for x in controls["controls"]] == ["PASS", "REPRODUCED", "REPRODUCED"]
    successful_capture_ref = ref(here / "source-controls-actual-fullhostpair.jsonl")
    successful_binding_ref = ref(here / "source-controls-actual-fullhostpair.binding.json")
    failure_capture_ref = ref(here / "actual-failed-tool-pair-1022.jsonl")
    failure_binding_ref = ref(here / "actual-failed-tool-pair-1022.binding.json")
    for binding_ref, capture_ref in ((successful_binding_ref, successful_capture_ref), (failure_binding_ref, failure_capture_ref)):
        binding = read(binding_ref["path"])
        assert Path(binding["capture_ref"]["path"]) == Path(capture_ref["path"])
        assert binding["capture_ref"]["sha256"] == capture_ref["sha256"]
        assert binding["capture_ref"]["bytes"] == capture_ref["bytes"]
        lines = Path(capture_ref["path"]).read_bytes().splitlines(keepends=True)
        assert [hashlib.sha256(x).hexdigest() for x in lines] == binding["original_line_sha256"]
        assert [len(x) for x in lines] == binding["source_line_bytes"]
        assert len(lines) == 4
    findings = {
        "schema": "researchos.main23-root-independent-source-findings.v1",
        "source_ref": author["caller_ref"],
        "source_author": author["source_author"],
        "review_author": "codex:/root/w09_formal_profile_source_impl",
        "scope": "Pure Source chain and negative fixtures. No Canon, Native, Go, SQLite, Main23 child or model execution.",
        "controls_ref": controls_ref,
        "findings": [
            {
                "id": "R1", "severity": "BLOCKER", "lines": [176, 190],
                "boundary": "External Root hostpair acceptance",
                "observation": "validate_root_capture accepts when each expected SHA appears anywhere in JSON-serialized output. It does not require the expected path and bytes or a typed ref to be present, nor correlate output content with the claimed operation.",
                "reproduction": "A 3-row session/call/output fixture whose output contains only three digests, no ref paths or sizes, returns True. This same validator gates the review witness, postreview live capture and activation capture.",
                "required_change": "Parse the actual tool result as a typed evidence object; bind each complete exact path/sha256/bytes ref and operation/call context, and use the raw tool timestamps rather than only self-declared binding timestamps. Reject digest-only output."
            },
            {
                "id": "R2", "severity": "BLOCKER", "lines": [348, 365],
                "boundary": "Independent runtime resource qualification",
                "observation": "runtime_closure checks independent_non_author and review_author strings copied across qualification and decision files but does not bind that decision to an actual external reviewer capture or reviewer-authored manifest. Both are inputs to the Root request.",
                "reproduction": "A pure fixture with an invented non-author reviewer string and matching resource_refs is accepted by runtime_closure. File I/O was replaced only to isolate the decision predicate; this is a Source-logic reproduction, not a live filesystem exploit.",
                "required_change": "Require a pinned, reviewer-authored decision/HDF/MF and an external Root hostpair witnessing those exact refs before any registration or build phase uses the qualified runtime closure."
            }
        ],
        "positive_controls": [
            "Author HDF, MF and all 12 manifest members match their actual pinned bytes.",
            "The source calls for fresh post-public371 Canon refs and a separate output root.",
            "The review did not start the builder or modify Canon."
        ]
    }
    findings_ref = write_new("source-findings.json", findings)
    now = datetime.now(timezone.utc).isoformat()
    decision = {
        "schema": "researchos.main23-root-independent-source-decision.v1",
        "verdict": "SOURCE_CHANGES_REQUIRED",
        "reviewed_utc": now,
        "review_author": "codex:/root/w09_formal_profile_source_impl",
        "source_author": author["source_author"],
        "independent_non_author": True,
        "author_hdf_ref": author_hdf_ref,
        "author_mf_ref": author_mf_ref,
        "caller_ref": author["caller_ref"],
        "registrar_ref": author["registrar_ref"],
        "calling_contract_ref": author["contract_ref"],
        "findings_ref": findings_ref,
        "controls_ref": controls_ref,
        "actual_controls_capture_ref": successful_capture_ref,
        "actual_controls_binding_ref": successful_binding_ref,
        "actual_failed_command_capture_ref": failure_capture_ref,
        "actual_failed_command_binding_ref": failure_binding_ref,
        "blocking_findings": ["R1", "R2"],
        "source_accepted_for_root_registration": False,
        "execution_grant": False,
        "formal_acceptance": False,
        "candidate_program_ref": None,
        "qualification_ref": None,
        "actual_build": False,
        "owned_jobs_started": 0,
        "Go_processes": 0,
        "native_calls": 0,
        "sqlite_calls": 0,
        "model_calls": 0
    }
    decision_ref = write_new("source-decision.json", decision)
    members = [ref(p) for p in here.iterdir() if p.is_file() and p.name not in ("MF.json", "HDF.json")]
    members.sort(key=lambda x: x["path"].lower())
    manifest_ref = write_new("MF.json", {"schema": "researchos.main23-root-independent-source-manifest.v1", "members": members, "complete_namespace_members_excluding_hdf_mf": True, "formal_acceptance": False})
    hdf_ref = write_new("HDF.json", {
        "schema": "researchos.main23-root-independent-source-handoff.v1",
        "status": "SOURCE_CHANGES_REQUIRED",
        "created_utc": now,
        "review_author": decision["review_author"],
        "source_author": decision["source_author"],
        "independent_non_author": True,
        "author_hdf_ref": author_hdf_ref,
        "author_mf_ref": author_mf_ref,
        "source_caller_ref": author["caller_ref"],
        "manifest_ref": manifest_ref,
        "decision_ref": decision_ref,
        "findings_ref": findings_ref,
        "controls_ref": controls_ref,
        "actual_controls_capture_ref": successful_capture_ref,
        "actual_controls_binding_ref": successful_binding_ref,
        "blocking_findings": ["R1", "R2"],
        "source_accepted_for_root_registration": False,
        "execution_grant": False,
        "formal_acceptance": False,
        "actual_build": False
    })
    assert all(member == ref(member["path"]) for member in read(manifest_ref["path"])["members"])
    print(json.dumps({"HDF": hdf_ref, "MF": manifest_ref, "decision": decision_ref, "findings": findings_ref, "members": len(members)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
