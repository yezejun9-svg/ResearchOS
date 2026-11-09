"""Run fresh 070e-bound validator and four serial Desktop fixture entrypoints."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012")
BUILD = SOURCE / ".local/builds/approved-readlane-combined-20261012"
RAW = SOURCE / ".local/receipts/approved-readlane-combined-20261012"
HERE = Path(__file__).resolve().parent
NODE = Path(r"C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe")
ELECTRON = Path(r"D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist/electron.exe")
COMMIT = "070e6cda24ec2fadca104873534febcedfb7ddc0"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def run(name, argv, cwd, env, timeout):
    out, err = RAW / (name + ".stdout.raw"), RAW / (name + ".stderr.raw")
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with out.open("xb") as stdout, err.open("xb") as stderr:
        try:
            code = subprocess.run([str(a) for a in argv], cwd=cwd, env=env,
                                  stdout=stdout, stderr=stderr, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    row = {"argv": [str(a) for a in argv], "cwd": str(cwd), "started_at": start,
           "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "exit": code, "stdout": str(out), "stdout_sha256": sha(out),
           "stderr": str(err), "stderr_sha256": sha(err),
           "selected_environment": {key: env[key] for key in (
               "RESEARCHOS_DESKTOP_WIRE_ROOT", "RESEARCHOS_DESKTOP_CASE_RECEIPT",
               "RESEARCHOS_DESKTOP_ELECTRON", "TEMP", "TMP") if key in env}}
    save(RAW / (name + ".invocation.json"), row)
    if code:
        save(HERE / "stopped.json", {"first_unexpected": row, "formal_acceptance": False,
             "action": "Stop and inspect raw; no automatic retry or output replacement"})
        raise SystemExit(code)
    return row

def summary(row, expected):
    output = Path(row["stdout"]).read_text(encoding="utf-8")
    counts = {}
    for key in ("tests", "pass", "fail", "skipped", "cancelled"):
        hits = re.findall(r"^[#ℹ]\s+" + key + r"\s+(\d+)\s*$", output, re.M)
        if len(hits) != 1:
            raise RuntimeError(f"{row['stdout']}: exact {key} summary missing: {hits}")
        counts[key] = int(hits[0])
    if counts != {"tests": expected, "pass": expected, "fail": 0, "skipped": 0, "cancelled": 0}:
        raise RuntimeError(f"{row['stdout']}: unexpected summary {counts}")
    if len(re.findall(r"^✔ ", output, re.M)) != expected or "✖ " in output:
        raise RuntimeError(f"{row['stdout']}: leaf/pass mismatch")
    return counts, output

def main():
    assert not (HERE / "stopped.json").exists() and not (HERE / "bound-tests.json").exists()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == COMMIT
    assert subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=SOURCE) == b""
    result = json.loads((RAW / "result.json").read_bytes())
    assert result["status"] == "BUILT_NOT_TESTED" and result["drift"] == []
    env = os.environ.copy()
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(BUILD / "apps/desktop"),
               RESEARCHOS_DESKTOP_ELECTRON=str(ELECTRON))
    validator = run("attempt01-validator-test", [BUILD / "validator.test.exe", "-test.v"],
                    SOURCE / "apps/desktop/validator", env, 120)
    validator_output = Path(validator["stdout"]).read_text(encoding="utf-8")
    if not re.search(r"^PASS$", validator_output, re.M) or re.search(r"^--- FAIL:|^FAIL$", validator_output, re.M):
        save(HERE / "stopped.json", {"first_unexpected": validator, "cause": "Validator Go PASS marker missing"})
        raise SystemExit("validator test output mismatch")
    cases = [
        ("coding", "tests/ui/desktop/coding-authorization-boundary.test.mjs", 21),
        ("management", "tests/ui/desktop/desktop-management-boundary.test.mjs", 11),
        ("react", "tests/ui/desktop/w13-react.test.js", 5),
        ("http-qualification-renderer", "tests/ui/desktop/http-wire-boundary.test.mjs", 216),
    ]
    rows = []
    for name, file, expected in cases:
        case = RAW / "cases" / ("attempt01-" + name)
        temp = case / "temp"
        temp.mkdir(parents=True, exist_ok=False)
        case_env = {**env, "RESEARCHOS_DESKTOP_CASE_RECEIPT": str(case),
                    "TEMP": str(temp), "TMP": str(temp)}
        row = run("attempt01-" + name,
                  [NODE, "--test", "--test-concurrency=1", file], SOURCE, case_env, 450)
        try:
            counts, output = summary(row, expected)
            if name == "http-qualification-renderer":
                prefix_counts = {"desktop-http": len(re.findall(r"^✔ desktop-http/", output, re.M)),
                                 "qualification-lane": len(re.findall(r"^✔ qualification-lane/", output, re.M)),
                                 "desktop-renderer": len(re.findall(r"^✔ desktop-renderer/", output, re.M))}
                if prefix_counts != {"desktop-http": 180, "qualification-lane": 34, "desktop-renderer": 2}:
                    raise RuntimeError(f"HTTP/qualification/renderer roster mismatch: {prefix_counts}")
                for label in ("desktop-renderer/react-roundtrip", "desktop-renderer/legacy-roundtrip"):
                    if "✔ " + label not in output:
                        raise RuntimeError("Renderer leaf missing: " + label)
            else:
                prefix_counts = None
        except Exception as exc:
            save(HERE / "stopped.json", {"first_unexpected": row, "cause": str(exc),
                 "formal_acceptance": False, "action": "Stop without overwriting raw"})
            raise
        rows.append({"name": name, "source_file": file, "counts": counts,
                     "prefix_counts": prefix_counts, "invocation": row})
    assert sum(row["counts"]["pass"] for row in rows) == 253
    save(HERE / "bound-tests.json", {
        "schema": "researchos.cp444-readlane-source-bound-local-tests.v1",
        "status": "LOCAL_FIXTURE_PASS_NOT_PRODUCT_ACCEPTANCE", "source_commit": COMMIT,
        "build_input_digest": result["build_input_digest"],
        "build_input_count": len(json.loads((RAW / "inputs.before.json").read_bytes())),
        "build_drift": [], "validator_invocation": validator,
        "desktop_entrypoints": rows, "unique_desktop_tests": 253,
        "model_calls": 0, "actual_first_use": False,
        "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "LOCAL_FIXTURE_PASS", "desktop_counts": [r["counts"] for r in rows],
                      "unique_desktop_tests": 253}, ensure_ascii=False))

if __name__ == "__main__":
    main()
