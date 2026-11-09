from pathlib import Path
import hashlib
import json
import shutil

archive = Path(__file__).parent
repo = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-normal-home-binding-20261105")
contract = Path(r"D:\作品集\ResearchOS\research-os\execution\product-v1\contracts\native-normal-home-binding.v1.json")
scope = Path(r"D:\作品集\ResearchOS\research-os\execution\product-v1\receipts\single-harness-20261104\native-normal-home-binding\scope.json")
files = [
    "adapters/runtime/codex_qualification_windows.go",
    "adapters/runtime/codex_qualification_capture_windows.go",
    "adapters/runtime/codex_qualification_windows_test.go",
    "adapters/runtime/codex_qualification_capture_windows_test.go",
]
baseline_sha = {
    "adapters/runtime/codex_qualification_windows.go": "7af3347a194a66455f962d38fc1918b0752a30ca4138ef46734ebd2fdc20bd24",
    "adapters/runtime/codex_qualification_capture_windows.go": "a664f9c24feaf752ba784bb370d3a650d81232f8e449ccb45ca6138a16f9eb59",
    "adapters/runtime/codex_qualification_windows_test.go": "05a6c3d789fe1522877108407b8545eee0f2c514a432b846ae805876437752e1",
    "adapters/runtime/codex_qualification_capture_windows_test.go": "1accac663ea2fb583b807253c7bf16b8190a28bafb3c4902aaa8cd9864995fc5",
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

candidate = archive / "candidate"
candidate.mkdir(exist_ok=True)
for rel in files:
    name = Path(rel).name
    source = repo / rel
    baseline = archive / "baseline" / name
    if sha(baseline) != baseline_sha[rel]:
        raise RuntimeError(f"baseline drift: {rel}")
    shutil.copyfile(source, candidate / name)

shutil.copyfile(contract, archive / "contract.json")
shutil.copyfile(scope, archive / "scope.json")
if sha(archive / "contract.json") != "a5c0bd2a3910646cef88f373fc836b4bd43328402056d05935b4ddfed24a1ae0":
    raise RuntimeError("contract drift")

diagnostics = {
    "source_head": "998fc6330ba735056cd31f8ebf68dd50a8251c1b",
    "leased_worktree": str(repo),
    "leased_source_files": files,
    "static_checks": {"git_diff_check": "passed", "git_status": "only exact four leased files modified"},
    "formatter": "Repository-pinned .local/tools/go1.27.1/go/bin/gofmt.exe ran successfully on the exact four leased files. An initial PATH gofmt lookup failed before Root supplied this location.",
    "not_run_by_author": ["Go tests", "Go build", "Native", "App", "helper", "model", "metadata CLI", "probe", "setup", "ACL or network action"],
    "test_regex_for_root": "^(TestQualificationNormalHome(Spelling|EarlyGateAcceptsSlashEquivalentProfile|EarlyGateRejectsChangedOrEmptyProfile|IntentSpelling)|TestQualificationPrelaunchIntentProvenanceAndMutation|TestQualificationPrelaunchQueriedJobDurableBeforeLaunch)$",
    "fixture_scope_note": "The early-gate positive Go fixture calls existing PrivateDirectory only on a synthetic t.TempDir root and stops at a deliberately mismatched helper digest before collector launch. Root alone decides and runs the registered Go-only fixture scope.",
    "original_flow01": {"task": "c9fc3e4dc1ea5d34a0ca003a983b43c6", "run": "a46af22fb058915f9f7119b2d7d73f8f", "status": "FAILED", "outer_status": "TIMED_OUT_STOPPED", "replay": "forbidden"},
    "limits": "Pure path spelling tests cannot establish filesystem reparse safety; production exactReal and private directory checks remain in place. No readiness or product acceptance is claimed.",
}
(archive / "diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

selection = {
    "repo_root": str(repo),
    "source_head": "998fc6330ba735056cd31f8ebf68dd50a8251c1b",
    "files": [
        {"path": rel, "baseline": f"baseline/{Path(rel).name}", "candidate": f"candidate/{Path(rel).name}", "baseline_sha256": baseline_sha[rel], "candidate_sha256": sha(candidate / Path(rel).name)}
        for rel in files
    ],
    "patches": {"forward": "forward.patch", "inverse": "inverse.patch"},
}
(archive / "archive-file-list.json").write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

manifest = {
    "schema": "researchos.native-normal-home-binding-source-archive.v1",
    "archive": str(archive),
    "files": {p.relative_to(archive).as_posix(): sha(p) for p in sorted(archive.rglob("*")) if p.is_file() and p.name != "manifest.json"},
}
(archive / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"archive": str(archive), "candidate_sha256": {rel: sha(candidate / Path(rel).name) for rel in files}, "patch_sha256": {p: sha(archive / p) for p in ("forward.patch", "inverse.patch")}}, ensure_ascii=False))
