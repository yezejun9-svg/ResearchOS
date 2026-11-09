"""Freeze the exact committed R2 source and existing append-only command evidence."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys


BASE_525 = "525a9c923a8761a9491070123de3c94aa5618d71"
BASE_MAIN = "4f4023c956f84d65743f39ce77d6c8899a21ada1"
ALLOWED = {
    "internal/runtimepolicy/qualification_projection.go",
    "internal/runtimepolicy/qualification_projection_test.go",
    "internal/domain/runtime_broker_windows.go",
    "internal/domain/runtime_drain_windows.go",
    "internal/domain/runtime_drain_windows_test.go",
    "internal/domain/runtime_model_verification_test.go",
    "internal/domain/runtime_model_windows_test.go",
    "internal/domain/runtime_qualification_projection_test.go",
    "internal/domain/runtime_qualification_projection_windows_test.go",
    "adapters/runtime/qualification_projection_windows_test.go",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    root = Path(sys.argv[1]).resolve()
    receipts = Path(sys.argv[2]).resolve()
    prefix = ["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0"]

    def git(*args):
        call = prefix + list(args)
        outcome = subprocess.run(call, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if outcome.returncode:
            raise RuntimeError(f"git {args}: exit={outcome.returncode} stderr={outcome.stderr!r}")
        return outcome.stdout

    head = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    branch = git("branch", "--show-current").decode().strip()
    status = git("status", "--porcelain=v1").decode()
    changed = git("diff", "--name-only", BASE_525, "HEAD").decode().splitlines()
    if status or set(changed) != ALLOWED:
        raise RuntimeError(f"source not frozen, status={status!r}, changed={changed!r}")
    patches = {}
    for name, base in (("r2-diff-from-525.binary.patch", BASE_525), ("r2-full-diff-from-4f.binary.patch", BASE_MAIN)):
        raw = git("diff", "--binary", base, "HEAD", "--", *sorted(ALLOWED))
        path = receipts / name
        with path.open("xb") as stream:
            stream.write(raw)
        patches[name] = {"sha256": sha(raw), "bytes": len(raw)}
    sources = []
    for relative in sorted(changed):
        raw = (root / relative).read_bytes()
        sources.append({"path": relative, "sha256": sha(raw), "bytes": len(raw)})
    command_results = []
    for result_path in sorted(receipts.glob("r2-*.result.json")):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        command_path = receipts / (result_path.stem.removesuffix(".result") + ".command.json")
        command = json.loads(command_path.read_text(encoding="utf-8")) if command_path.exists() else None
        command_results.append({"tag": result_path.name.removesuffix(".result.json"), "native_exit": result["native_exit"], "stdout_sha256": result["stdout_sha256"], "stdout_bytes": result["stdout_bytes"], "stderr_sha256": result["stderr_sha256"], "stderr_bytes": result["stderr_bytes"], "command_sha256": sha(command_path.read_bytes()) if command is not None else None})
    target_events = [json.loads(line) for line in (receipts / "r2-final-targeted.stdout.raw").read_text(encoding="utf-8").splitlines() if line.strip()]
    test_actions = {action: sum(1 for item in target_events if item.get("Test") and item.get("Action") == action) for action in ("pass", "fail", "skip")}
    package_actions = [{"package": item.get("Package"), "action": item.get("Action"), "elapsed": item.get("Elapsed")} for item in target_events if not item.get("Test") and item.get("Action") in ("pass", "fail", "skip")]
    bundle = Path("D:/作品集/ResearchOS/research-os/.local/builds/current-chat-runtime-assets-20261012/mu-worker.mjs")
    go = Path("D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe")
    manifest = {
        "schema": "researchos.qualification-projection-A-r2-source-manifest.v1",
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "base_commit": BASE_525,
        "main_base_commit": BASE_MAIN,
        "commit": head,
        "tree": tree,
        "branch": branch,
        "worktree": str(root),
        "source_paths": sources,
        "patches": patches,
        "go_binary": {"path": str(go), "sha256": sha(go.read_bytes())},
        "frozen_worker_bundle": {"path": str(bundle), "sha256_after": sha(bundle.read_bytes())},
        "targeted_test": {"command_tag": "r2-final-targeted", "test_actions_including_subtests": test_actions, "package_actions": package_actions},
        "build": {"command_tag": "r2-final-build", "native_exit": json.loads((receipts / "r2-final-build.result.json").read_text(encoding="utf-8"))["native_exit"]},
        "f03_entry_evidence": {
            "brokerEffect": "r2-consumer-causes.stdout.raw: unmodified first dispatch reaches loopback provider after PREPARED; 30 mutations reject before new effect, ledger or provider call and no worker observation",
            "completedLocalUnknownCost": "r2-consumer-causes.stdout.raw: unmodified first dispatch passes; 30 mutations reject without changing UNKNOWN ledger or effect history",
            "normal_legacy_host_wire": "r2-original-hostwire02.stdout.raw: legacy brokerEffect entry and bounded normal brokerModel entry preserve original 8/4 body; normal full session remains historically unproved",
            "fixture_boundary": "new isolated Begin/Task/Run/Plan; TEMP trigger suppresses auto dispatch INSERT; first durable dispatch row seeded from captured manifest. UNKNOWN cost fixture synthesizes append-only effect stages for invalid source rows"
        },
        "capture_gap_ledger": "capture-gap-ledger.json",
        "recorded_commands": command_results,
        "limitations": ["No actual model, product data, Core stop, installed package or formal case execution", "Normal Mu full-session known base failure is not counted as PASS", "Independent review pending; source author pass is not acceptance"],
        "formal_case_increment": 0
    }
    output = receipts / "source-manifest.revision02.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"manifest": str(output), "sha256": sha(output.read_bytes()), "commit": head, "tree": tree, "paths": len(changed), "test_actions": test_actions, "packages": package_actions, "commands": len(command_results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
