"""Freeze the r4 author candidate; never assert independent acceptance."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path(r"D:\作品集\ResearchOS\research-os")
WT = REPO / ".local" / "worktrees" / "owned-core-stop-authority-r4-20261015"
BASE = "2816daacdb2c08ae8ee1d62c91bcd3f571d40737"
MAIN = "4f4023c956f84d65743f39ce77d6c8899a21ada1"
HEAD = "ab308912117dac59cadd5aa2e75b46a418e41b6b"
EXPECTED = [
    "ops/supervisor/owned_core_handle_windows.go",
    "ops/supervisor/owned_core_handle_windows_test.go",
]
SCOPE = REPO / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp518/owned-core-stop-authority-r4-source-scope.json"
AMENDMENT = REPO / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp518/owned-stop-r4-fixture-location-amendment01.json"
CASE = ROOT / "fixture-e2e-20261015T132047341758Z" / "case-result.json"
OUT = ROOT / "candidate-ab308912-final2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    proc = subprocess.run(["git", *args], cwd=WT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError((args, proc.returncode, proc.stderr.decode(errors="replace")))
    return proc.stdout


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


assert run("rev-parse", "HEAD").decode().strip() == HEAD
assert run("status", "--porcelain") == b""
tree = run("rev-parse", "HEAD^{tree}").decode().strip()
paths = run("diff", "--name-only", BASE, HEAD).decode().splitlines()
whole_paths = run("diff", "--name-only", MAIN, HEAD).decode().splitlines()
assert paths == EXPECTED, paths
assert len(whole_paths) == 19 and set(EXPECTED).issubset(whole_paths), whole_paths
assert sha(SCOPE) == "feffa1558e54771edbe1411e27a8e7f17ea8fb067a5ebb95dc806811b5337d00"
assert sha(AMENDMENT) == "de78514256033961034f459aa37090c3bd6f1e14136cbc189db7a8e8739f055a"
positive = json.loads(CASE.read_text(encoding="utf-8"))
assert positive["result"]["state"] == "STOPPED_LEASE_VERIFIED"
assert positive["result"]["native"]["terminate_calls"] == 1
assert positive["result"]["native"]["exit_code"] == 1381191507
assert positive["result"]["postflight"]["quick_check"] == "ok"
assert positive["result"]["postflight"]["tables"] == 87
assert positive["result"]["postflight"]["rows"] == 35

OUT.mkdir(exist_ok=False)
for name, old in [("delta-2816-to-ab308912.patch", BASE), ("whole19-Main4f-to-ab308912.patch", MAIN)]:
    (OUT / name).write_bytes(run("diff", "--binary", old, HEAD))

captures = []
for folder in sorted((ROOT / "command-captures").iterdir()):
    before = folder / "before.json"
    after = folder / "after.json"
    if not before.exists() or not after.exists():
        continue  # The enclosing freeze command cannot index its own after record.
    b, a = json.loads(before.read_text(encoding="utf-8")), json.loads(after.read_text(encoding="utf-8"))
    captures.append({
        "directory": str(folder),
        "before_sha256": sha(before),
        "after_sha256": sha(after),
        "stdout_sha256": sha(folder / "stdout.bin"),
        "stderr_sha256": sha(folder / "stderr.bin"),
        "native_exit": a["native_exit"],
        "argv": b["argv"],
        "cwd": b["cwd"],
        "allowlist_env": b["allowlist_env"],
    })
write_json(OUT / "command-index.json", captures)

expected_nonzero = {"preflight-binary-cannot-commit", "stop-binary-cannot-preflight"}
failures = []
for item in captures:
    if item["native_exit"] == 0:
        continue
    label = Path(item["directory"]).name
    classification = "EXPECTED_NEGATIVE_CLI" if any(x in label for x in expected_nonzero) else "DIAGNOSTIC_RETAINED"
    failures.append({"directory": item["directory"], "native_exit": item["native_exit"], "classification": classification})
write_json(OUT / "failure-ledger.json", {
    "total_nonzero": len(failures),
    "expected_negative_cli": sum(x["classification"] == "EXPECTED_NEGATIVE_CLI" for x in failures),
    "diagnostics": sum(x["classification"] == "DIAGNOSTIC_RETAINED" for x in failures),
    "bootstrap_capture_location_deviation": "Initial bootstrap capture written to adjacent similarly named receipt root; raw files copied into official root, originals retained. One copy collision and retry retained. No Source counter reset.",
    "known_unlogged_shell_reads": 0,
    "failures": failures,
})

tests = {
    "owner_and_ace_unit": "PASS in r4-all-owned-supervisor-cuts raw stdout",
    "copied_parent_child_safe_acl": "PASS in r4-all-owned-supervisor-cuts; C private installation",
    "copied_parent_child_direct_inherited_unsafe_acl": "PASS five rejection subcases in r4-all-owned-supervisor-cuts",
    "untrusted_D_installation": "REJECTED before signal in r4-all-owned-supervisor-cuts",
    "retained_directory_writer": "GENERIC_WRITE directory handle OPENED; selected ancestor rename denied; raw stdout retained",
    "retained_selected_path": "Selected ancestor/final rename, final remove/write/same-name replacement denied; same-handle ACL drift rejected",
    "reparse_hardlink_wrong_parent": "PASS in r4-all-owned-supervisor-cuts",
    "two_compiled_grants": "PASS: real preflight and STOP CLI on task-owned C parent/child + nonempty SQLite",
    "one_native_stop": positive["result"]["native"],
    "postflight": positive["result"]["postflight"],
    "replay": "PASS: fixture_e2e_r4 positive runs immutable inspect and repeat commit",
}
write_json(OUT / "test-matrix.json", tests)

source_pins = {p: {"bytes": (WT / p).stat().st_size, "sha256": sha(WT / p)} for p in whole_paths}
write_json(OUT / "manifest.json", {
    "schema": "researchos.owned-core-stop-authority-revision04-author-candidate.v1",
    "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "status": "AUTHOR_CANDIDATE_NOT_INDEPENDENTLY_ACCEPTED",
    "formal_increment": 0,
    "actual_core_touched": False,
    "source_base_commit": BASE,
    "source_commit": HEAD,
    "source_tree": tree,
    "main_base_commit": MAIN,
    "changed_paths": paths,
    "whole19_paths": whole_paths,
    "source_pins": source_pins,
    "scope": {"path": str(SCOPE), "sha256": sha(SCOPE)},
    "fixture_location_amendment": {"path": str(AMENDMENT), "sha256": sha(AMENDMENT)},
    "r4_delta_patch": {"path": str(OUT / "delta-2816-to-ab308912.patch"), "sha256": sha(OUT / "delta-2816-to-ab308912.patch")},
    "whole19_patch": {"path": str(OUT / "whole19-Main4f-to-ab308912.patch"), "sha256": sha(OUT / "whole19-Main4f-to-ab308912.patch")},
    "command_index": {"path": str(OUT / "command-index.json"), "sha256": sha(OUT / "command-index.json"), "completed_count": len(captures)},
    "failure_ledger": {"path": str(OUT / "failure-ledger.json"), "sha256": sha(OUT / "failure-ledger.json"), "nonzero_count": len(failures)},
    "test_matrix": {"path": str(OUT / "test-matrix.json"), "sha256": sha(OUT / "test-matrix.json")},
    "threat_model": {"path": str(ROOT / "selected-image-path-threat-model.md"), "sha256": sha(ROOT / "selected-image-path-threat-model.md")},
    "positive_case_result": {"path": str(CASE), "sha256": sha(CASE)},
    "compiled_executable_sha256": {"preflight": positive["preflight_executable_sha256"], "stop": positive["stop_executable_sha256"]},
    "fixture_executable_sha256": sha(Path(r"C:\Users\yqyyds\.codex\researchos-fixture-cache\owned-core-stop-authority-r4-20261015\fixture-r4.exe")),
    "parent_helper_executable_sha256": sha(Path(r"C:\Users\yqyyds\.codex\researchos-fixture-cache\owned-core-stop-authority-r4-20261015\fixture-parent-r4.exe")),
    "limits": [
        "Full Commit cancellation after its own durable intent remains an integration limit.",
        "True foreign-user SID execution and a hostile concurrent filesystem race were not executed.",
        "No actual Core, current data root, power loss, or formal cases exercised.",
        "Author is not independent Source reviewer or acceptance authority.",
    ],
})
print(json.dumps({"manifest": str(OUT / "manifest.json"), "manifest_sha256": sha(OUT / "manifest.json"), "commands": len(captures), "nonzero": len(failures), "commit": HEAD}, ensure_ascii=False))
