import hashlib
import json
import pathlib
import subprocess

evidence = pathlib.Path(__file__).resolve().parent
repo = evidence.parents[3]

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def file_entry(path, root):
    raw = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "sha256": digest(raw), "bytes": len(raw)}

entries = [file_entry(p, evidence) for p in sorted(evidence.rglob("*")) if p.is_file() and p.name != "evidence-index.json"]
sources = []
paths = [
    "AGENTS.md", "internal/domain/backup.go", "internal/domain/backup_upgrade.go",
    "internal/domain/backup_recovery.go", "internal/domain/backup_migration.go",
    "internal/domain/store.go", "internal/domain/qualification_live.go",
    "internal/domain/backup_upgrade_test.go", "internal/store/sqlite.go",
    "ops/backup/main.go", "ops/backup/README.md",
    "adapters/protectedstore/frozen_provider_windows.go", "adapters/protectedstore/provider.go",
    "adapters/retrieval/local.go", "migrations/sqlite/0014_remote_access.sql",
    "internal/domain/backup_upgrade_path_windows.go", "internal/domain/backup_upgrade_path_other.go",
    "internal/domain/backup_upgrade_path_windows_test.go"
]
for revision in ["bb09e50e5bdc0c51ecba009022865cb4185e4ef6", "5719167c404902ad2d0e5da6c6624361b10f4a2c"]:
    for path in paths:
        result = subprocess.run(["git", "show", revision + ":" + path], cwd=repo, capture_output=True)
        if result.returncode:
            if revision.startswith("bb09e50") and "backup_upgrade_path_" in path:
                continue
            raise RuntimeError(result.stderr.decode())
        sources.append({"revision": revision, "path": path, "git_blob_sha256": digest(result.stdout), "bytes": len(result.stdout)})

external = []
for relative in [
    ".local/worktrees/protected-upgrade/execution/receipts/W17/local-upgrade/3c73ee2b-1779-42a0-89f6-2efd331e617f",
    ".local/worktrees/protected-upgrade/execution/receipts/W17/local-upgrade/fix-f56f5f72-7eef-4ea1-9db4-404036ba1112",
]:
    external.extend(file_entry(p, repo) for p in sorted((repo / relative).iterdir()) if p.is_file())
for relative in ["execution/verifier/W17/migration-boundary/design.md", "execution/readiness/w17-local-upgrade/20260930T142007Z/plan.json"]:
    external.append(file_entry(repo / relative, repo))

document = {
    "schema": "researchos.independent-evidence-index.v1",
    "source_revision": "5719167c404902ad2d0e5da6c6624361b10f4a2c",
    "base_revision": "bb09e50e5bdc0c51ecba009022865cb4185e4ef6",
    "local_files": entries,
    "reviewed_source_blobs": sources,
    "external_readonly_evidence": external,
    "index_self_hash": "Excluded to avoid self-reference; returned to coordinator separately."
}
(evidence / "evidence-index.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"indexed_local_files": len(entries), "source_blobs": len(sources), "external_files": len(external), "index_sha256": digest((evidence / "evidence-index.json").read_bytes()), "review_sha256": digest((evidence / "review.json").read_bytes())}))
