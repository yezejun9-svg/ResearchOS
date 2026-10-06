"""Archive sealed public evidence only; leave source and old deletions untouched."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
COMMITS = []


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
    assert run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip() == "1c7d7d8af69fbb523586e0e3a874cff5f17a3c00"
    assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
    cp = json.loads((ROOT / "execution/v2.4/checkpoint.json").read_bytes())
    own = json.loads((ROOT / "execution/v2.4/path_ownership.json").read_bytes())
    assert cp["revision"] == 274 and own["revision"] == 102 and len(cp["failure_counters"]) == 223
    selected = {ROOT / "execution/v2.4/checkpoint.json", ROOT / "execution/v2.4/path_ownership.json", Path(__file__).resolve(), OUT / "driver.py"}
    prefixes = [
        "integration_codex/main-cli-source-integration-r272",
        "integration_codex/main-cli-adoption-r273",
        "integration_codex/provider-zero-model-scope-r274",
        "provider_binding_failure_chain_independent_review_codex/7c23e2f1-71af-4ac7-88f7-75c94710e327",
        "cancel_finalization_upgrade_scope_readonly_codex/78f08cbbf58d4e21ab51c605801103d9",
        "integration_codex/provider-binding-scope-r269",
        "integration_codex/configuration-upgrade-scope-r270",
        "integration_codex/configuration-schema-mirror-scope-r271",
        "integration_codex/cli-source-adoption-r272",
        "integration_codex/configuration-handler-readonly-r270",
        "integration_codex/handoff-resume-r271",
        "integration_codex/task-packet-r271",
        "integration_codex/main-stream-source-integration-r268",
        "integration_codex/current-status-r269",
        "main_stream_composition_independent_review_codex/c22da050-5fd2-4394-932c-5a5534360295",
        "host_configuration_upgrade_scope_review_codex/2c7bb855-7562-41b6-8c8e-5456f9fc81dc",
        "host_configuration_schema_mirror_scope_review_codex/98cce1a4-5b1a-4361-8fb7-4d6b979481df",
        "cancel_finalization_scope_readonly_codex/4e3160d75a2a444cb048798da12f567a",
        "cli_read_interrupt_executor_codex",
        "cli_read_interrupt_source_review_codex/c5dc6318-b068-4630-81ee-21ae287b842d",
        "provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63",
    ]
    for prefix in prefixes:
        parent = ROOT / (BASE + prefix)
        assert parent.is_dir(), str(parent)
        for path in parent.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                selected.add(path)
    previous = ROOT / (BASE + "integration_codex/source-evidence-archive-r272")
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
         "checkpoint": 274, "ownership": 102, "failure_origins": 223, "files": files, "source_integration": False, "formal_increment": 0})
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
    run("commit", ["git", "commit", "-m", "chore(execution): preserve integrated CLI proof and independent provider diagnostic scope"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    changed = set(x for x in subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head], cwd=ROOT).decode().split("\0") if x)
    assert changed == staged
    result = {"actual_exit": 0, "head": head, "actual_changed_paths": len(changed), "source_integration": False, "formal_increment": 0, "old_deletions_not_staged": True}
    save("completed.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
