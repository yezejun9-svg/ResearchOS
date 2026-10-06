"""Verify retained actual outputs, accounting for the isolated pre-S6 baseline."""
import json
from pathlib import Path
from qualify import OUT, ROOT, MAIN, GO, digest, ref, save, packages

gaps_path = MAIN / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-2881cfa84dd64156b59d12795e6375a2/capture-coverage-gaps.json"
gaps = json.loads(gaps_path.read_text(encoding="utf-8"))["missing_from_capture_required_by_profile"]
assert len(gaps) == 27
result = json.loads((OUT / "final-fixture-collector.stdout").read_text(encoding="utf-8"))
assert result["status"] == "PASS"
proof_path = ROOT / result["product_proof_ref"]["path"]
capture = proof_path.parent
snapshot = json.loads((capture / "source-before.json").read_text(encoding="utf-8"))
assert snapshot == json.loads((capture / "source-after.json").read_text(encoding="utf-8"))
assert all(value == "sha256:" + digest(ROOT / name) for name, value in snapshot.items())
required = set(); selected = set()
for p in packages((capture / "go-list.stdout").read_text(encoding="utf-8")):
    directory = Path(p.get("Dir", "")).resolve()
    if directory.is_relative_to(ROOT):
        selected.update((directory / n).relative_to(ROOT).as_posix() for field in ("GoFiles", "CgoFiles", "EmbedFiles") for n in p.get(field, []))
        if directory.relative_to(ROOT).parts[:1] != (".local",):
            required.update(f.relative_to(ROOT).as_posix() for f in directory.glob("*.go") if f.is_file())
assert (required | selected).issubset(snapshot)
absent = [name for name in gaps if not (ROOT / name).exists()]
assert absent == ["adapters/runtime/bridge_control_windows_test.go"]
assert set(gaps) - set(absent) <= snapshot.keys()
main_packages = {}; environments = {}
for mode in ("fixture", "live"):
    environments[mode] = json.loads((OUT / (mode + "-go-env.stdout")).read_text(encoding="utf-8"))
    main_packages[mode] = list(packages((OUT / (mode + "-go-list.stdout")).read_text(encoding="utf-8")))
    for stem in (mode + "-go-env", mode + "-go-list"):
        inv = json.loads((OUT / (stem + ".invocation.json")).read_text(encoding="utf-8"))
        assert inv["exit_code"] == 0
        for key in ("stdout_ref", "stderr_ref"):
            assert digest(Path(inv[key]["path"])) == inv[key]["sha256"]
assert environments["fixture"] == environments["live"]
def inventory(rows):
    return sorted((p.get("ImportPath"), p.get("Dir"), p.get("GoFiles", []), p.get("EmbedFiles", [])) for p in rows)
assert inventory(main_packages["fixture"]) == inventory(main_packages["live"])
assert Path(environments["fixture"]["GOPATH"]) == MAIN / ".local/gopath"
assert Path(environments["fixture"]["GOCACHE"]) == MAIN / ".local/gocache"
assert Path(environments["fixture"]["GOMODCACHE"]) == MAIN / ".local/gopath/pkg/mod"
main_dirs = {Path(p.get("Dir", "")).resolve() for p in main_packages["fixture"]}
assert all((MAIN / n).parent in main_dirs and (MAIN / n).is_file() for n in gaps)
save(OUT / "historical-27-gaps.json", {"original_ref": ref(gaps_path), "paths": gaps,
     "isolated_capture_count": 26, "absent_from_isolated_pre_S6_baseline": absent,
     "main_all_27_current_in_actual_package_directories": [ref(MAIN / n) for n in gaps],
     "main_collector_capture_after_integration": "REQUIRED_NOT_RUN"})
before = json.loads((OUT / "candidate-source-before.json").read_text(encoding="utf-8"))
after = {name: digest(ROOT / name) for name in before}
save(OUT / "candidate-source-after.json", after)
assert before == after
fixture_events = [json.loads(line) for line in (capture / "fixture.stdout").read_text(encoding="utf-8").splitlines() if line.strip()]
assert not any(event.get("Action") in {"fail", "skip"} for event in fixture_events)
assert len(result["fixture"]["passed"]) == 37 and not result["fixture"]["missing"]
proof = json.loads(proof_path.read_text(encoding="utf-8"))
assert len(proof["h07_invocations"][0]["db_snapshots"]) == 13
qualification = {"status": "CANDIDATE_FIXTURE_QUALIFIED", "formal_acceptance": "NOT_ISSUED", "public_source_capture": "NOT_RUN",
    "effective_go_environment": environments, "actual_dependency_inventories_equal": True,
    "local_complete_go_inputs": len(required), "host_unselected_local_go_inputs": sorted(required-selected),
    "captured_source_count": len(snapshot), "historical_gaps": {"count": 27, "captured_in_isolated_baseline": 26, "only_in_integrated_S6_main": absent},
    "fixture_required_pass": 37, "go_test_top_level_pass": sum(event.get("Action") == "pass" and "Test" in event and "/" not in event["Test"] for event in fixture_events),
    "parent_tests_pass": 8, "typed_h07_snapshots": 13, "fail": 0, "skip": 0,
    "source_before_equals_after_and_current": True, "proof_ref": ref(proof_path), "candidate_sources": after, "go_ref": ref(GO),
    "required_followup": "Root integrates reviewed candidate, then fresh MAIN LIVE and native dispatches; previous c495/1614 captures remain historical"}
save(OUT / "qualification.json", qualification)
print(json.dumps(qualification, ensure_ascii=False))
