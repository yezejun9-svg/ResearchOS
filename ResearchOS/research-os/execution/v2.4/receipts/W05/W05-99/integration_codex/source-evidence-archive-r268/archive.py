"""Archive sealed public evidence only; leave source and old deletions untouched."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
COMMITS = ["6eb611b11364ba25a9560ba54c1b54f3a549eb32", "0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837", "890d4c164bffad73e562ceacfdc216820d0313fd", "c571781e9703bc7a96fa63629e0cc3bee7f3deec"]


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write(enc(value))


def run(name, argv):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in (("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)):
        with (OUT / (name + "." + suffix)).open("xb") as stream:
            stream.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": started,
         "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": proc.returncode,
         "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
    assert proc.returncode == 0, (name, proc.returncode)
    return proc.stdout


def main():
    assert run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip() == "4ba293847072069cd99154e5054f6ef4ae2b92e1"
    assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
    cp = json.loads((ROOT / "execution/v2.4/checkpoint.json").read_bytes())
    own = json.loads((ROOT / "execution/v2.4/path_ownership.json").read_bytes())
    assert cp["revision"] == 268 and own["revision"] == 96 and len(cp["failure_counters"]) == 198
    selected = {ROOT / "execution/v2.4/checkpoint.json", ROOT / "execution/v2.4/path_ownership.json", Path(__file__).resolve(), OUT / "driver.py"}
    prefixes = [
        "integration_codex/cli-read-interrupt-scope-r266", "integration_codex/cli-read-causal-scope-r267",
        "integration_codex/vendor-resource-scope-r268", "integration_codex/continuation-observations-r266",
        "cli_read_interrupt_executor_codex", "cli_read_interrupt_scope_review_codex",
        "cli_read_interrupt_cause_scope_review_codex", "cli_read_interrupt_source_precheck_codex", "cli_interrupt_readonly_codex",
        "provider_binding_executor_scope_codex/79c9c61c276a42e1962556af982dc51d",
        "provider_binding_scope_review_codex/e350f920-2862-4dc3-906e-c6e1044e63ec",
        "provider_live_execution_plan_codex/a5033fb5de8840369dbd6fe6cf08f7d0",
        "provider_live_plan_review_codex/9c160a80-7639-46fe-af30-44bc1bb8bffa",
        "provider_budget_resource_readonly_codex/budget-4d5e48bb6b764a34ac537990b10290f2",
        "host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644",
        "streaming_repaired_source_review_codex/5455e415-03a4-466e-9cd1-0b0b5e691d87",
        "streaming_signed_zero_source_review_codex/4bb6828c-89ea-4a19-b0ed-e3b07da94b8a",
        "vendor_resource_restore_scope_review_codex/62dec05a93654b1ab199f3777eb172e5",
        "vendor_resource_restore_executor_codex/restore-r268",
        "vendor_resource_restore_independent_review_codex/cc65c5e5-9b17-4c0d-9add-e560b1850a09",
        "provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-native-read",
        "provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-capture",
        "provider_resource_intake_codex/20261006-opencode-go/deepseek-model-limit-cached-success",
        "provider_resource_intake_codex/20261006-opencode-go/public-docs-20261006T1408",
    ]
    for prefix in prefixes:
        parent = ROOT / (BASE + prefix)
        assert parent.is_dir(), str(parent)
        for path in parent.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                selected.add(path)
    previous = ROOT / (BASE + "integration_codex/source-evidence-archive-r265")
    for name in ["stage.invocation.json", "stage.stdout.raw", "stage.stderr.raw", "commit.invocation.json", "commit.stdout.raw", "commit.stderr.raw", "completed.json"]:
        selected.add(previous / name)
    # Any already-copied immutable candidate receipts must be archived before cherry-pick.
    for index, commit in enumerate(COMMITS):
        names = run(f"candidate-{index}-paths", ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit]).decode().split("\0")
        for name in names:
            if not name.startswith(BASE):
                continue
            path = ROOT / name
            if path.is_file():
                expected = run(f"candidate-{index}-existing-{hashlib.sha256(name.encode()).hexdigest()[:16]}", ["git", "show", commit + ":" + name])
                assert path.read_bytes() == expected, name
                selected.add(path)
    # Preserve actual read-only tool errors in this continuation without inventing stdout.
    save("root-observations.json", {"schema": "researchos.root.actual-tool-observations.v1", "actor": "codex:/root", "formal_increment": 0,
         "observations": [
           {"origin_key": "W05-99/root/r268-resume-scope-filename-read", "tool_chunk": "0f4123", "actual_aggregate_exit": 1, "actual_attempts": 1, "failed_path": BASE + "integration_codex/vendor-resource-scope-r268/scope.json", "actual_corrected_path": BASE + "integration_codex/vendor-resource-scope-r268/scope_registration.json", "source_mutation": False},
           {"origin_key": "W05-99/root/r268-console-evidence-locator", "tool_chunk": "e8b878", "actual_aggregate_exit": 0, "actual_rg_error": "os error 2", "actual_attempts": 1, "failed_path": BASE + "cli_read_interrupt_console_readonly_codex", "actual_corrected_path": BASE + "cli_interrupt_readonly_codex", "source_mutation": False}
         ]})
    selected.add(OUT / "root-observations.json")
    # Restrict staging to public files whose actual bytes differ from current index.
    index_raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)
    index = {}
    for row in index_raw.split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            mode, oid, stage = meta.split()
            assert stage == b"0"
            index[name.decode()] = oid.decode()
    files = []
    for path in sorted(selected):
        assert path.is_file()
        relative = path.relative_to(ROOT).as_posix()
        assert relative.startswith("execution/v2.4/") and path.suffix != ".zip"
        raw = path.read_bytes()
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if index.get(relative) == oid:
            continue
        files.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    save("manifest.json", {"schema": "researchos.root.public-source-evidence-archive.v1", "actor": "codex:/root",
         "checkpoint": 268, "ownership": 96, "failure_origins": 198, "files": files, "source_integration": False, "formal_increment": 0})
    names = [x["path"] for x in files] + [(OUT / "manifest.json").relative_to(ROOT).as_posix()]
    pathspec = OUT / "pathspec.nul"
    pathspec.write_bytes(b"\0".join(x.encode() for x in names) + b"\0")
    run("stage", ["git", "--literal-pathspecs", "add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul"])
    pathspec.unlink()
    staged = set(x for x in subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT).decode().split("\0") if x)
    assert staged == set(names), (len(staged), len(names))
    for file in files:
        raw = subprocess.check_output(["git", "show", ":" + file["path"]], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == file["sha256"], file["path"]
    run("commit", ["git", "commit", "-m", "chore(execution): preserve causal read repair and reviewed stream composition evidence"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    changed = set(x for x in subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head], cwd=ROOT).decode().split("\0") if x)
    assert changed == staged
    result = {"actual_exit": 0, "head": head, "actual_changed_paths": len(changed), "source_integration": False, "formal_increment": 0, "old_deletions_not_staged": True}
    save("completed.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
