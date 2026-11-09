"""Freeze a bounded r5 author candidate without claiming independent acceptance."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
WT = Path.cwd().resolve()
REPO = WT.parents[2]
BASE = "ab308912117dac59cadd5aa2e75b46a418e41b6b"
MAIN = "4f4023c956f84d65743f39ce77d6c8899a21ada1"
EXPECTED = [
    "internal/store/owned_stop_barrier_windows.go",
    "internal/store/owned_stop_barrier_windows_test.go",
]
SCOPE = REPO / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp521/owned-core-stop-effect-state-r5-source-scope.json"
IMAGE_ROOT = Path("C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-effect-state-r5-20261015")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    done = subprocess.run(["git", *args], cwd=WT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if done.returncode:
        raise RuntimeError((args, done.returncode, done.stderr.decode(errors="replace")))
    return done.stdout


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


head = run("rev-parse", "HEAD").decode().strip()
assert run("status", "--porcelain") == b""
tree = run("rev-parse", "HEAD^{tree}").decode().strip()
paths = run("diff", "--name-only", BASE, head).decode().splitlines()
whole_paths = run("diff", "--name-only", MAIN, head).decode().splitlines()
assert paths == EXPECTED, paths
assert len(whole_paths) == 19 and set(EXPECTED).issubset(whole_paths), whole_paths
assert sha(SCOPE) == "f90762847f45c4c742c1865ac441c16f85d3de9b353be47a0270313651d11397"

cases = {}
for case_dir in sorted(ROOT.glob("fixture-e2e-*")):
    result_path = case_dir / "case-result.json"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("mode") in ("r5_missing", "r5_null", "positive"):
            assert result["mode"] not in cases
            cases[result["mode"]] = {"path": str(result_path), "sha256": sha(result_path), "result": result}
assert set(cases) == {"r5_missing", "r5_null", "positive"}, cases.keys()
for mode in ("r5_missing", "r5_null"):
    result = cases[mode]["result"]
    assert result["preflight_eligibility"] == "STOP_UNAVAILABLE"
    assert result["preflight_safety"]["non_model_effects"] == 1
    assert result["preflight_safety"]["confirmed_model_effects"] == 1
    assert result["zero_stop_attempt"] and result["core_alive"]
    assert result["stop_grant_built"] is False and result["native_signal_count"] == 0
positive = cases["positive"]["result"]
assert positive["result"]["state"] == "STOPPED_LEASE_VERIFIED"
assert positive["result"]["native"]["terminate_calls"] == 1
assert positive["result"]["native"]["exit_code"] == 1381191507
assert positive["result"]["postflight"]["quick_check"] == "ok"

OUT = ROOT / ("candidate-" + head[:8] + "-final")
OUT.mkdir(exist_ok=False)
patch_argv = [
    ["git", "diff", "--binary", "--full-index", BASE, head],
    ["git", "diff", "--binary", "--full-index", MAIN, head],
]
patches = {}
for name, argv in zip(("delta-ab308912-to-r5.patch", "whole19-Main4f-to-r5.patch"), patch_argv):
    path = OUT / name
    path.write_bytes(run(*argv[1:]))
    patches[name] = {"path": str(path), "sha256": sha(path), "argv": argv}

captures = []
for folder in sorted((ROOT / "command-captures").iterdir()):
    before, after = folder / "before.json", folder / "after.json"
    if not before.exists() or not after.exists():
        continue
    b, a = json.loads(before.read_text(encoding="utf-8")), json.loads(after.read_text(encoding="utf-8"))
    captures.append({
        "directory": str(folder),
        "before_sha256": sha(before), "after_sha256": sha(after),
        "stdout_sha256": sha(folder / "stdout.bin"), "stderr_sha256": sha(folder / "stderr.bin"),
        "native_exit": a["native_exit"], "argv": b["argv"], "cwd": b["cwd"],
        "allowlist_env": b["allowlist_env"],
    })
write_json(OUT / "command-index.json", captures)

failure_rows = []
for item in captures:
    label = Path(item["directory"]).name
    if item["native_exit"] != 0 or sha(Path(item["directory"]) / "stderr.bin") != hashlib.sha256(b"").hexdigest():
        cls = "EXPECTED_NEGATIVE_CLI" if "binary-cannot" in label else "DIAGNOSTIC_RETAINED"
        failure_rows.append({"directory": item["directory"], "native_exit": item["native_exit"], "classification": cls, "stderr_sha256": item["stderr_sha256"]})
write_json(OUT / "failure-ledger.json", {
    "rows": failure_rows,
    "native_nonzero_count": sum(row["native_exit"] != 0 for row in failure_rows),
    "diagnostic_count": sum(row["classification"] == "DIAGNOSTIC_RETAINED" for row in failure_rows),
    "known_unlogged_shell_reads": 1,
    "unlogged_shell_read_description": "After context reset, one direct read of own run_logged.py preceded reuse of the existing recipe; read-only, no Source or fixture mutation.",
    "copy_hash_probe": "Copy of reviewer harness succeeded, but appended Get-FileHash command failed to resolve in that PowerShell process; raw stderr retained. Later source and fixture hashes are pinned separately.",
    "older_failure_records_preserved": True,
})

tests = {
    "store_package": "PASS: go test ./internal/store -count=1; full package, raw command capture",
    "finite_matrix": "PASS: 16 latest effect state cases with real schema24 and reserved barrier; prior focused raw command capture",
    "compiled_preflight_missing": {k: v for k, v in cases["r5_missing"].items() if k != "result"},
    "compiled_preflight_null": {k: v for k, v in cases["r5_null"].items() if k != "result"},
    "compiled_positive_two_grants": {k: v for k, v in cases["positive"].items() if k != "result"},
    "positive_native": positive["result"]["native"],
    "positive_postflight": positive["result"]["postflight"],
    "positive_readonly_replay": "PASS: fixture_e2e_r5 positive checks immutable inspect and repeat commit",
}
write_json(OUT / "test-matrix.json", tests)
source_pins = {p: {"bytes": (WT / p).stat().st_size, "sha256": sha(WT / p)} for p in whole_paths}
write_json(OUT / "manifest.json", {
    "schema": "researchos.owned-core-stop-effect-state-revision05-author-candidate.v1",
    "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "status": "AUTHOR_CANDIDATE_NOT_INDEPENDENTLY_ACCEPTED",
    "formal_increment": 0, "actual_core_touched": False,
    "source_base_commit": BASE, "source_commit": head, "source_tree": tree,
    "main_base_commit": MAIN, "changed_paths": paths, "whole19_paths": whole_paths,
    "source_pins": source_pins, "scope": {"path": str(SCOPE), "sha256": sha(SCOPE)},
    "patches": patches,
    "command_index": {"path": str(OUT / "command-index.json"), "sha256": sha(OUT / "command-index.json"), "completed_count": len(captures)},
    "failure_ledger": {"path": str(OUT / "failure-ledger.json"), "sha256": sha(OUT / "failure-ledger.json"), "rows": len(failure_rows)},
    "test_matrix": {"path": str(OUT / "test-matrix.json"), "sha256": sha(OUT / "test-matrix.json")},
    "fixture_results": {mode: {k: v for k, v in data.items() if k != "result"} for mode, data in cases.items()},
    "compiled_executable_sha256": {"preflight": positive["preflight_executable_sha256"], "stop": positive["stop_executable_sha256"]},
    "fixture_executable_sha256": sha(IMAGE_ROOT / "fixture-r5.exe"),
    "parent_helper_executable_sha256": sha(IMAGE_ROOT / "fixture-parent-r5.exe"),
    "limits": [
        "This is an author candidate; independent Source/Main review remains required.",
        "Historical worker/verifier receipts in CLI fixtures are synthetic; only task-owned copied Core native stop is freshly observed.",
        "No actual Core/data root or formal case is operated; no full post-intent cancellation/foreign SID/power-loss/deeper snapshot qualification.",
        "Finite latest effect state matrix does not certify all deeper historical audit semantics or malformed JSON encoding branches.",
    ],
})
print(json.dumps({"manifest": str(OUT / "manifest.json"), "manifest_sha256": sha(OUT / "manifest.json"), "commit": head, "tree": tree, "commands": len(captures), "failure_rows": len(failure_rows)}, ensure_ascii=False))
