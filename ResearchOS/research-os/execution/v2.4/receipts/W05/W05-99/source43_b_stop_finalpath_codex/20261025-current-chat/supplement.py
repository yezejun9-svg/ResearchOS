import hashlib
import json
import pathlib
from datetime import datetime, timezone

here = pathlib.Path(__file__).resolve().parent
fixture_root = pathlib.Path(r"C:\Users\yqyyds\.codex\researchos-fixture-cache\source43-b-stop-finalpath-20261025")


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def recorded_command(number):
    folder = next(p for p in here.iterdir() if p.is_dir() and p.name.startswith(number + "-"))
    files = {name: identity(folder / name) for name in ("recipe.json", "invocation.json", "stdout.raw", "stderr.raw", "exit.json")}
    recipe = json.loads((folder / "recipe.json").read_text(encoding="utf-8"))
    invocation = json.loads((folder / "invocation.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "exit.json").read_text(encoding="utf-8"))
    return {"id": folder.name, "files": files, "recipe": recipe, "invocation": invocation,
            "raw_stdout_utf8": (folder / "stdout.raw").read_text(encoding="utf-8"),
            "raw_stderr_utf8": (folder / "stderr.raw").read_text(encoding="utf-8"), "result": result}


def main():
    final_path = here / "FINAL-manifest.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    assert final["status"] == "AUTHOR_FROZEN_PENDING_INDEPENDENT_REVIEW"
    commands = [recorded_command(x) for x in ("049", "050", "051", "052")]
    assert all(item["result"]["exit"] == 0 for item in commands)
    status_path = here / "051-current-source-status/stdout.raw"
    assert status_path.read_bytes() == b""
    head, tree = (here / "052-current-head-tree/stdout.raw").read_text(encoding="utf-8").splitlines()
    assert head == final["source_commit"] and tree == final["source_tree"]
    fixtures = [identity(fixture_root / name) for name in ("owned-stop-fixture.exe", "ownedcorestop.test.exe", "ownedops.test.exe")]
    data = {
        "schema": "researchos.source43-post-final-supplement.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_final": identity(final_path),
        "source_commit": head,
        "source_tree": tree,
        "source_clean": True,
        "source_state_receipts": ["051-current-source-status", "052-current-head-tree"],
        "post_final_commands": commands,
        "cleanup_scope": {"receipt": "050-cleanup-owned-d-temp", "removed_exact_task_owned_root": r"D:\作品集\ResearchOS\research-os\.local\source43-b-stop-finalpath-20261025-tmp", "other_root_deleted": False},
        "retained_c_fixture": {"root": str(fixture_root), "files": fixtures},
        "diagnostic_ledger_delta": {"new_failures_after_final": 0, "new_entries": [], "prior_ledger_unchanged": identity(here / "diagnostic-ledger.json")},
        "authority": {"actual": False, "formal_increment": 0, "self_acceptance": False, "main_imported": False},
        "index_boundary": "This supplement binds 049/050 and current read-only 051/052. Its own 053 result is bound by FINAL-supplement-seal.json; 054 self-result is excluded to avoid recursive hashing."
    }
    output = here / "FINAL-supplement.json"
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"supplement": identity(output), "final": identity(final_path), "source_commit": head, "source_tree": tree}, ensure_ascii=False))


if __name__ == "__main__":
    main()
