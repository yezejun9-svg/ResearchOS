"""Archive closed public evidence and canonical checkpoint with exact pathspec."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
PREFIXES = [
    "integration_codex/configuration-main-scope-r282",
    "integration_codex/configuration-main-integration-r282",
    "integration_codex/provider-epoch-causal-correction-r283",
    "integration_codex/configuration-main-closure-r284",
    "integration_codex/provider-typed-route-scope-r285",
    "main_configuration_composition_independent_review_codex/c34b6453-73e7-42ad-8ac0-511231cf78ab",
    "provider_binding_executor_codex/causal-repair-481c0dc455c643f5a2e70b7178c97fe2",
    "provider_binding_executor_codex/epoch-correction-69a52b78d491456792bf394b01629e02",
    "provider_inventory_epoch_cause_review_codex/fa6d4045-d881-41bb-b220-ef0066de934a",
    "provider_inventory_route_cause_review_codex/acde0511-095b-434e-890a-fc433561221a",
    "provider_inventory_route_cause_review_codex/byte-limit-supplement-da6c6277-c38c-49ad-9428-8eba35f590ba",
    "host_configuration_handler_scope_review_codex/9ed5cfb6464049598ee2229a07049b84",
    "host_configuration_handler_scope_revision_codex/8f972b92afae45c5ac96ca679d623975",
    "cancel_finalization_design_review_codex/88e5846a108640eda9db9ddfaa8bc156",
]


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write((json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode())


def run(n, argv):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in [("stdout.raw", p.stdout), ("stderr.raw", p.stderr)]:
        with (OUT / (n + "." + suffix)).open("xb") as f:
            f.write(raw)
    save(n + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": p.returncode, "stdout_sha256": hashlib.sha256(p.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(p.stderr).hexdigest()})
    assert p.returncode == 0, (n, p.returncode)
    return p.stdout


def main():
    before = run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip()
    assert before == "1b3cda2ee974916f864b9a0af988076d01ca65bd"
    assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
    cp = json.loads((ROOT / "execution/v2.4/checkpoint.json").read_bytes())
    ow = json.loads((ROOT / "execution/v2.4/path_ownership.json").read_bytes())
    assert cp["revision"] == 285 and ow["revision"] == 113 and len(cp["failure_counters"]) == 245
    selected = {ROOT / "execution/v2.4/checkpoint.json", ROOT / "execution/v2.4/path_ownership.json", Path(__file__).resolve(), OUT / "driver.py"}
    for prefix in PREFIXES:
        directory = ROOT / (BASE + prefix)
        assert directory.is_dir(), prefix
        selected.update(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    prior = ROOT / (BASE + "integration_codex/source-evidence-archive-r281")
    for n in ["stage.invocation.json", "stage.stdout.raw", "stage.stderr.raw", "commit.invocation.json", "commit.stdout.raw", "commit.stderr.raw", "completed.json", "execution.invocation.json", "execution.stdout.raw", "execution.stderr.raw"]:
        selected.add(prior / n)
    index = {}
    for row in subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT).split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            mode, oid, stage = meta.split()
            assert stage == b"0"
            index[name.decode()] = oid.decode()
    files = []
    for p in sorted(selected):
        assert p.is_file() and p.resolve().is_relative_to((ROOT / "execution/v2.4").resolve())
        relative = p.relative_to(ROOT).as_posix()
        assert p.suffix != ".zip"
        raw = p.read_bytes()
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if index.get(relative) != oid:
            files.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "git_blob_oid": oid})
    save("manifest.json", {"schema": "researchos.root.exact-public-evidence-archive.v1", "checkpoint": 285, "ownership": 113, "failure_origins": 245, "files": files, "source_changed": False, "formal_increment": 0})
    names = [r["path"] for r in files] + [(OUT / "manifest.json").relative_to(ROOT).as_posix()]
    pathspec = OUT / "pathspec.nul"
    with pathspec.open("xb") as f:
        f.write(b"\0".join(n.encode() for n in names) + b"\0")
    run("stage", ["git", "--literal-pathspecs", "add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul"])
    pathspec.unlink()
    staged = {n for n in subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT).decode().split("\0") if n}
    assert staged == set(names)
    current = {}
    for row in subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT).split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            current[name.decode()] = meta.split()[1].decode()
    for r in files:
        assert current[r["path"]] == r["git_blob_oid"]
        assert hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest() == r["sha256"]
    run("commit", ["git", "commit", "-m", "chore(execution): preserve current configuration proof and typed route failure chain"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    changed = {n for n in subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head], cwd=ROOT).decode().split("\0") if n}
    assert changed == staged and all(n.startswith("execution/v2.4/") for n in changed)
    save("completed.json", {"actual_exit": 0, "head": head, "prior_head": before, "changed_paths": len(changed), "source_changed": False, "formal_increment": 0, "old_deletions_not_staged": True})
    print(json.dumps({"head": head, "public_paths_archived": len(changed), "source_changed": False, "formal_increment": 0}))


if __name__ == "__main__":
    main()
