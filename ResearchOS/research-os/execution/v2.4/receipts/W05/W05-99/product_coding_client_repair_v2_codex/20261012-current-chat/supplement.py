"""Seal the later full Desktop boundary run as an append-only receipt supplement."""
import hashlib
import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
raw = here / "raw"
c_root = pathlib.Path(r"C:\Users\yqyyds\.codex\researchos-build-worktrees\coding-client-v2-20261012")
c_cases = c_root / ".local/builds/product-coding-client-repair-v2-20261012-bound-tests"
d_cases = raw / "c-bound-all-desktop-cases"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def census(files):
    entries = []
    for path in sorted(files):
        entries.append((path.relative_to(here).as_posix(), sha(path), path.stat().st_size))
    digest = hashlib.sha256("".join(f"{name}\t{sum_}\t{size}\n" for name, sum_, size in entries).encode()).hexdigest()
    return len(entries), sum(size for _, _, size in entries), digest


parent = json.loads((here / "manifest.json").read_text(encoding="utf-8"))
prior = [p for p in raw.rglob("*") if p.is_file() and not p.relative_to(raw).as_posix().startswith("c-bound-all-desktop")]
assert census(prior) == (parent["raw_files"], parent["raw_bytes"], parent["raw_census_sha256"])
assert sha(here / "manifest.json") == "44379f527ddaf8935888c64470489c36820470e7ab8a6e3d5047b9dcb41c694a"

case_files = sorted(path for path in d_cases.rglob("*") if path.is_file())
assert len(case_files) == 1663
for path in case_files:
    assert sha(path) == sha(c_cases / path.relative_to(d_cases))
count, size, case_digest = census(case_files)
assert size == 185325030

name = "c-bound-all-desktop"
invocation = json.loads((raw / f"{name}.invocation.json").read_text(encoding="utf-8"))
assert invocation["exit"] == 0 and pathlib.Path(invocation["cwd"]).resolve() == c_root.resolve()
assert sha(raw / f"{name}.stdout") == invocation["stdout_sha256"]
assert sha(raw / f"{name}.stderr") == invocation["stderr_sha256"]
stdout = (raw / f"{name}.stdout").read_text(encoding="utf-8")
assert "ℹ tests 211" in stdout and "ℹ pass 211" in stdout and "ℹ fail 0" in stdout

supplement = {
    "schema": "researchos.w05.desktop-coding-client-repair-v2-supplement/1",
    "parent_manifest_sha256": sha(here / "manifest.json"),
    "candidate_commit": parent["candidate_commit"],
    "build_input_digest": parent["build_input_digest"],
    "run": "C-bound complete Desktop boundary suite",
    "run_invocation_sha256": sha(raw / f"{name}.invocation.json"),
    "stdout_sha256": sha(raw / f"{name}.stdout"),
    "stderr_sha256": sha(raw / f"{name}.stderr"),
    "case_files": count,
    "case_bytes": size,
    "case_census_sha256": case_digest,
    "bound_resource_root": str(c_root / ".local/builds/product-coding-client-repair-v2-20261012/apps/desktop"),
    "bound_case_root": str(c_cases),
    "electron": r"D:\作品集\ResearchOS\research-os\apps\desktop\node_modules\electron\dist\electron.exe",
    "tests": 211,
    "passed": 211,
    "failed": 0,
    "evidence_class": "SOURCE_BOUND_SYNTHETIC_DESKTOP_TESTS",
    "formal_acceptance_delta": 0,
    "parent_acceptance_delta": 0,
}
with (here / "supplement-01.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(supplement, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"supplement_sha256": sha(here / "supplement-01.json"), "case_files": count, "case_bytes": size}))
