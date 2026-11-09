"""Interpret immutable Node 24 raw summary after parser-format mismatch."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012")
BUILD = ROOT / ".local/builds/approved-combined-first-use-20261012"
RAW = ROOT / ".local/receipts/approved-combined-first-use-20261012"
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_bytes())

def put(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def main():
    assert not (HERE / "bound-verification.json").exists()
    build = load(RAW / "result.json")
    assert build["status"] == "BUILT_NOT_TESTED" and build["drift"] == []
    names = ("cb-control-build", "cb-verifier-build", "cb-validator-test-cwd-corrected", "cb-desktop-suite-app-root")
    rows = [load(RAW / (name + ".invocation.json")) for name in names]
    assert all(row["exit"] == 0 for row in rows)
    assert all(sha(Path(row["stdout"])) == row["stdout_sha256"] and
               sha(Path(row["stderr"])) == row["stderr_sha256"] for row in rows)
    validator = (RAW / "cb-validator-test-cwd-corrected.stdout").read_text(encoding="utf-8")
    assert re.search(r"^PASS$", validator, re.M) and not re.search(r"^--- FAIL:|^FAIL$", validator, re.M)
    raw = RAW / "cb-desktop-suite-app-root.stdout"
    output = raw.read_text(encoding="utf-8")
    counts = {}
    for key in ("tests", "pass", "fail", "skipped", "cancelled"):
        values = re.findall(r"^[#ℹ]\s+" + key + r"\s+(\d+)\s*$", output, re.M)
        assert len(values) == 1, (key, values)
        counts[key] = int(values[0])
    assert counts == {"tests": 219, "pass": 219, "fail": 0, "skipped": 0, "cancelled": 0}, counts
    assert len(re.findall(r"^✔ ", output, re.M)) == counts["pass"]
    assert "✖ " not in output
    for name in ("desktop-renderer/react-roundtrip", "desktop-renderer/legacy-roundtrip",
                 "first use consumes native choice, registers and bootstraps before saving real IDs"):
        assert "✔ " + name in output
    put(HERE / "bound-verification.json", {
        "status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS",
        "source_commit": "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8",
        "source_main_tree_equal": True,
        "build_input_digest": build["build_input_digest"],
        "build_input_count": len(load(RAW / "inputs.before.json")),
        "build_drift": build["drift"], "desktop_counts": counts,
        "desktop_raw_sha256": sha(raw), "validator_raw_sha256": sha(RAW / "cb-validator-test-cwd-corrected.stdout"),
        "control_sha256": sha(BUILD / "control.exe"), "verifier_sha256": sha(BUILD / "runtime-verifier.exe"),
        "validator_sha256": build["binary_sha256"], "invocations": rows,
        "failed_attempts_preserved": [str(HERE / "stopped.json"),
                                      str(HERE / "cb-desktop-suite-cwd-corrected.stopped.json")],
        "parser_format_mismatch_preserved": str(HERE / "cb-desktop-suite-app-root.stopped.json"),
        "parser_correction": "Read Unicode Node 24 ℹ summary from immutable raw; no test rerun",
        "model_calls": 0, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "desktop_counts": counts,
                      "control_sha256": sha(BUILD / "control.exe"),
                      "verifier_sha256": sha(BUILD / "runtime-verifier.exe")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
