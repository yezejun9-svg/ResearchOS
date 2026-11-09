"""Read-only verify the two isolated renderer raws and emit append-only formal seal."""
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012")
PACKAGE = Path(r"C:/Users/yqyyds/.codex/researchos-resource-cache/normal-readlane-combined-91218bdd-20261012")
RAW = SOURCE / ".local/receipts/approved-readlane-renderer-supplement-20261012"
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}

def load(path):
    return json.loads(path.read_bytes())

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def check_ref(row):
    path = Path(row["path"])
    assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], path

def main():
    verify_path = HERE / "renderer-supplement-verification.json"
    manifest_path = HERE / "renderer-supplement-manifest.json"
    assert not verify_path.exists() and not manifest_path.exists()
    report_path = HERE / "renderer-supplement-report.json"
    report = load(report_path)
    original_path = HERE / "manifest.json"
    composition_path = HERE / "composition.json"
    assert sha(original_path) == "3c71b1c94b830166ddd57506d01da0b5453fe3df79acf7b25c2756110bce9574"
    assert sha(composition_path) == "2fb90c81c223f53cb7cb7f8a7d088dcceed18acc551575e38691feb9b5be889f"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE).decode().strip() == report["source_commit"]
    assert subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=SOURCE) == b""
    assert len(report["cases"]) == 2 and [x["kind"] for x in report["cases"]] == ["react", "legacy"]
    census = load(RAW / "census.json")
    expected = {row["path"]: row for row in census["members"]}
    actual = {path.relative_to(RAW).as_posix(): path for path in RAW.rglob("*") if path.is_file() and path.name != "census.json"}
    assert census["self_excluded"] is True and len(expected) == len(actual) == census["member_count"]
    assert set(expected) == set(actual)
    for relative, path in actual.items():
        assert sha(path) == expected[relative]["sha256"] and path.stat().st_size == expected[relative]["bytes"]
    observed = {}
    for item in report["cases"]:
        kind = item["kind"]
        for key in ("case_report", "native_invocation", "native_stdout", "native_stderr"):
            check_ref(item[key])
        case = load(Path(item["case_report"]["path"]))
        check_ref(case["node_invocation"])
        check_ref(case["native_process_observations"])
        node = load(Path(case["node_invocation"]["path"]))
        native = load(Path(item["native_invocation"]["path"]))
        process = load(Path(case["native_process_observations"]["path"]))
        assert node["exit"] == native["exit"] == item["numeric_native_exit"] == 0
        assert native["pid"] == item["native_pid"] == case["native_pid"]
        assert native["actualargv"][-1] == "--renderer-case=" + kind
        assert node["selected_environment"]["RESEARCHOS_DESKTOP_WIRE_ROOT"] == str(PACKAGE / "apps/desktop")
        assert case["package_validator_sha256"] == report["package_validator_sha256"]
        assert any(row["pid"] == native["pid"] and row["creation_time_utc"] == item["native_creation"]["creation_time_utc"] for row in process["rows"])
        assert case["node_counts"]["pass"] == 1 and case["node_counts"]["fail"] == 0
        observed[kind] = {"node_exit": node["exit"], "native_exit": native["exit"],
                          "native_pid": native["pid"], "native_creation_time_utc": item["native_creation"]["creation_time_utc"],
                          "native_invocation": item["native_invocation"],
                          "native_stdout": item["native_stdout"], "native_stderr": item["native_stderr"]}
    assert observed["react"]["native_pid"] != observed["legacy"]["native_pid"]
    composition = load(composition_path)
    package_rows = {row["path"]: row for row in composition["package_files"]}
    package_actual = {path.relative_to(PACKAGE).as_posix(): path for path in PACKAGE.rglob("*") if path.is_file()}
    assert len(package_rows) == len(package_actual) == 58 and set(package_rows) == set(package_actual)
    assert all(sha(path) == package_rows[relative]["sha256"] and path.stat().st_size == package_rows[relative]["bytes"] for relative, path in package_actual.items())
    verify = {"schema": "researchos.cp444-renderer-supplement-verification.v1",
              "status": "TWO_DISTINCT_NATIVE_RENDERER_EXITS_ZERO",
              "raw_census": ref(RAW / "census.json"), "raw_members_verified": len(actual),
              "original_manifest": ref(original_path), "package_composition": ref(composition_path),
              "package_members_verified": len(package_actual),
              "package_validator_sha256": report["package_validator_sha256"],
              "renderer_cases": observed, "source_clean": True,
              "full_253_rerun": False, "ordinary_gui_launch": False,
              "formal_increment": 0, "parent_acceptance": False}
    save(verify_path, verify)
    save(manifest_path, {
        "schema": "researchos.cp444-append-only-renderer-supplement-manifest.v1",
        "status": "RENDERER_NATIVE_RAW_GAP_SUPPLEMENTED_PENDING_INDEPENDENT_REVIEW",
        "original_manifest": ref(original_path), "original_composition": ref(composition_path),
        "original_shared_raw_limitation": report["original_shared_raw_limitation"],
        "supplement_report": ref(report_path), "supplement_verification": ref(verify_path),
        "raw_census": ref(RAW / "census.json"),
        "source_commit": report["source_commit"], "source_tree": report["source_tree"],
        "source_vector": report["source_vector"], "package_root": str(PACKAGE),
        "package_validator_sha256": report["package_validator_sha256"],
        "renderer_cases": observed,
        "full_253_rerun": False, "ordinary_gui_launch": False,
        "model_calls": 0, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"manifest": ref(manifest_path), "report": ref(report_path),
                      "react_native": observed["react"]["native_invocation"],
                      "legacy_native": observed["legacy"]["native_invocation"],
                      "raw_census": ref(RAW / "census.json")}, ensure_ascii=True))

if __name__ == "__main__":
    main()
