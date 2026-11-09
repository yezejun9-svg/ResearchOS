import sys
sys.dont_write_bytecode = True
import ast
import difflib
import hashlib
import json
import re
import traceback
import types
from pathlib import Path

BASE = Path(__file__).resolve().parent
O = BASE / "revision"
O.mkdir(exist_ok=False)
B = BASE.parent.parent
Q = B / "native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491"
F = B / "t7_actual_failure_independent_review_codex/a765019dd7124e9fb6d389a3c213edbc"
NAME = "native_migration_authority_harness_windows_test.go"
KEY = "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"

def ref(p):
    p = Path(p)
    raw = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def exact(p, sha, size):
    a = ref(p)
    assert a["sha256"] == sha and a["bytes"] == size, str(p)
    return a
def walk(o):
    if isinstance(o, dict):
        if {"path", "sha256", "bytes"}.issubset(o):
            yield {k: o[k] for k in ("path", "sha256", "bytes")}
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)
def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    p = O / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        f.write(raw)
    return ref(p)

def main():
    anchor = [
        exact(Q/"HDF.json", "e9dab1b8ca436384733a256501aa21ca2a1b3429859a80368810cc65b741ed2b", 7028),
        exact(Q/"MF.json", "c3f3e98bee9a3f2879b1cf07ca49927f9c894bed4534aaa38f2775d514bec301", 10617),
        exact(F/"HDF.json", "a84a3656a1211a300f376ce0ede1ef474131808d16bd6b828db6eb4492fc7480", 3835),
        exact(F/"MF.json", "f4a2122f965b2f608cfa5b5aa0e3f5c0d71684f92824e1f548006ed58e0f38aa", 46297),
    ]
    guard_ref = exact(F/"inputs/sources/source_read_guard.py", "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", 11404)
    module = types.ModuleType("review_source_guard")
    exec(compile(Path(guard_ref["path"]).read_bytes(), guard_ref["path"], "exec"), module.__dict__)
    guards = []
    observations = []
    refs = list(anchor) + [guard_ref]
    bootstrap = module.SourceReadGuard()
    guards.append(bootstrap)
    bootstrap.acquire(refs)
    source_mf = json.loads(bootstrap.get_buffer(str(Q/"MF.json")))
    failure_mf = json.loads(bootstrap.get_buffer(str(F/"MF.json")))
    selected_failure = {
        "report.md", "final-verification.json", "guard-closure-checks.json",
        "inputs/sources/root_native_migration_controller.py",
        "inputs/final-runtime/test.invocation.json",
        "inputs/final-facts/00-rehearsal/invocation.json",
        "inputs/final-facts/00-rehearsal/stderr.raw",
    }
    refs += list(walk(source_mf["members"]))
    refs += [x for x in walk(failure_mf["members"]) if any(Path(x["path"]) == F/n for n in selected_failure)]
    refs.append(ref(B/"integration_codex/root-metadata-diagnostic-843-filetime-precision/failure-origin.843.json"))
    stage = module.SourceReadGuard()
    guards.append(stage)
    stage.acquire(refs)
    pins = json.loads(stage.get_buffer(str(Q/"source-pins.json")))
    refs += list(walk(pins))
    unique = {}
    for r in refs:
        k = str(Path(r["path"])).lower()
        assert k not in unique or unique[k]["sha256"] == r["sha256"]
        unique[k] = r
    refs = list(unique.values())
    closure = module.SourceReadGuard()
    guards.append(closure)
    closure.acquire(refs)
    try:
        def data(p):
            return closure.get_buffer(str(p))
        def obj(p):
            return json.loads(data(p))
        for i, r in enumerate(refs):
            p = O/"public-inputs"/(str(i).zfill(3)+"-"+Path(r["path"]).name)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("xb") as f:
                f.write(data(r["path"]))
        base_raw = data(pins["base_ref"]["path"])
        candidate_raw = data(pins["candidate_ref"]["path"])
        base = base_raw.decode("utf-8")
        candidate = candidate_raw.decode("utf-8")
        marker = "\n\n// Root supplies this public proof root only to the fixed harness process."
        assert candidate.count(marker) == 1
        head, addition = candidate.split(marker, 1)
        insertion = '\tpublicEnvironment, err := nativeHarnessBrokerPublicEnvironment(\n\t\tos.Getenv("' + KEY + '"),\n\t\tmap[string]string{"SystemRoot": os.Getenv("SystemRoot"), "WINDIR": os.Getenv("WINDIR"), "TEMP": os.Getenv("TEMP"), "TMP": os.Getenv("TMP")})\n\tif err != nil {\n\t\tt.Fatal(err)\n\t}\n'
        assert head.count(insertion) == 1
        head = head.replace(insertion, "", 1)
        new = "\t\tEnvironment:     publicEnvironment,"
        old = '\t\tEnvironment:     map[string]string{"SystemRoot": os.Getenv("SystemRoot"), "WINDIR": os.Getenv("WINDIR")},'
        assert head.count(new) == 1
        head = head.replace(new, old, 1)
        new = '\tcommand.Env = []string{"SystemRoot=" + publicEnvironment["SystemRoot"], "WINDIR=" + publicEnvironment["WINDIR"], "TEMP=" + publicEnvironment["TEMP"], "TMP=" + publicEnvironment["TMP"]}'
        old = '\tcommand.Env = []string{"SystemRoot=" + os.Getenv("SystemRoot"), "WINDIR=" + os.Getenv("WINDIR")}'
        assert head.count(new) == 1
        head = head.replace(new, old, 1)
        assert head.encode("utf-8") == base_raw, "exact inverse"
        counts = [len(re.findall(r"\bt\.(?:Fatalf?|Errorf?|FailNow|Fail)\s*\(", s)) for s in (base, candidate)]
        assert counts == [84, 90], counts
        names = re.findall(r"^func (Test\w+)\(", candidate, re.M)
        assert names == ["TestNativeMigrationAuthorityHarness", "TestNativeHarnessBrokerIsolatedTempEnvironment", "TestNativeHarnessBrokerTempBoundaryComparison"]
        envpart = candidate.split("func TestNativeHarnessBrokerIsolatedTempEnvironment(",1)[1].split("func TestNativeHarnessBrokerTempBoundaryComparison(",1)[0]
        pathpart = candidate.split("func TestNativeHarnessBrokerTempBoundaryComparison(",1)[1]
        leaves = [re.findall(r'^\t\t\{"([^"]+)"', s, re.M) for s in (envpart,pathpart)]
        assert list(map(len, leaves)) == [18,10]
        assert leaves[0]+leaves[1] == obj(Q/"public-environment-contract.json")["new_component_leaf_names"]
        assert "os.Environ" not in candidate
        assert base.count("15*time.Minute") == candidate.count("15*time.Minute") == 2
        assert "TimeoutSeconds: 180" in base
        previous = obj(F/"HDF.json")
        assert previous["native_positive_accepted"] is False
        origin = obj(pins["original835_public_refs"]["failure835_ref"]["path"])
        harness = obj(F/"inputs/final-runtime/test.invocation.json")
        rehearsal = obj(F/"inputs/final-facts/00-rehearsal/invocation.json")
        times = {
            "harness_reported_in_origin835": str(origin["native_harness_creation_time_100ns"]),
            "harness_native_observed": str(harness["result"]["creation_time_100ns"]),
            "rehearsal_reported_in_origin835": str(origin["native_rehearsal_creation_time_100ns"]),
            "rehearsal_native_observed": str(rehearsal["Result"]["creation_time_100ns"]),
        }
        assert times == {
            "harness_reported_in_origin835": "134359787460741280",
            "harness_native_observed": "134359787460741284",
            "rehearsal_reported_in_origin835": "134359787476336020",
            "rehearsal_native_observed": "134359787476336016",
        }
        failed841 = obj(Q/"failure-origin.841.json")
        assert failed841["actual_outer_exit"] == 1 and failed841["actual_Python_exit"] is None and failed841["ROOT_PYTHON_EXIT_marker"] is None and failed841["inferred_Python_exit"] == 1
        controller = data(F/"inputs/sources/root_native_migration_controller.py").decode("utf-8")
        assert KEY not in controller
        assert 'env = dict(c["cfg"]["Environment"])' in controller
        report = {
            "schema": "researchos.independent-temp-source-review.v1",
            "decision": "SOURCE_ACCEPTED_WITH_ROOT_EXECUTION_PREREQUISITES",
            "authority": "NONE", "formal_acceptance": False,
            "source_member_count": len(source_mf["members"]), "held_public_ref_count": len(refs),
            "candidate_ref": pins["candidate_ref"], "base_ref": pins["base_ref"],
            "exact_inverse_recovers_entire_T7_bytes": True,
            "assertion_counts_original_candidate": counts,
            "original_nine_cases_all_other_bytes_unchanged": True,
            "TTL15min_grant4min_CWD_Schema_pins_privatepipe_180s_sign_release_preserved": True,
            "test_names": names, "local_fs_env_leaf_names": leaves[0], "pure_windows_comparison_leaf_names": leaves[1],
            "component_regex": "^(TestNativeHarnessBrokerIsolatedTempEnvironment|TestNativeHarnessBrokerTempBoundaryComparison)$",
            "leaf_execution": "NOT_RUN", "real_junction_execution": "NOT_RUN",
            "windows_source_review": [
                "windows build tag and existing fmt/os/filepath/strings/reflect imports permit helper references",
                "Stat error short circuits info.IsDir; nonempty absolute existing directories are mandatory",
                "EvalSymlinks resolves all five paths; Windows lower-case Clean+Rel rejects sibling/parent/other-volume escape",
                "TEMP and TMP are checked both lexically and physically under proof root",
                "physical proof root is rejected both inside and containing either supplied system directory",
                "forwarded map and command.Env contain precisely SystemRoot/WINDIR/TEMP/TMP",
                "proof root comes only from harness getenv with no config or inferred fallback; trust requires Root frozen launch environment",
                "18 local fs/env subtests and 10 pure comparison subtests are directly reachable under exact selectors",
                "fixture SystemRoot/WINDIR are synthetic directories; labels do not assert real junction execution",
            ],
            "Root_prerequisites": [
                "Fresh reviewed controller source must allow exact proof key in ENV_KEYS; old controller rejects it",
                "Fresh fixed frozen cfg.Environment must supply proof root and TEMP/TMP explicitly, with real SystemRoot/WINDIR",
                "Freeze and own isolated directory resources throughout run; source path checks alone do not hold directory handles",
                "Review compile/input/resource pins, run two exact component parents and verify all 28 leaves",
                "Only then one fresh positive native case under Root jobs and manual sign/release; no historical attempt replay",
                "Independently review actual outcome before any native or formal acceptance",
            ],
            "historical_FILETIME_qualification": times,
            "reported_FILETIME_values_accepted_as_native": False,
            "failure841": {"actual_outer": 1, "marked_python": None, "inferred_python": 1, "native": None},
            "old_failure_SQL_cleanup_acceptance_is_not_positive": True,
            "CP360_or_CP361_product_acceptance": False,
            "Go_gofmt_SQL_native_model_network_private_read": False,
            "Main_T7_author_canonical_writes": False,
            "new_mechanical_errors": 1,
        }
        write("source-check.json", report)
        write("input-pins.json", refs)
        drift = [r["path"] for r in refs if ref(r["path"]) != r]
        assert not drift
        write("no-drift.json", {"checked": len(refs), "drift": drift})
    finally:
        for g in reversed(guards):
            observations.append(g.close())
        write("guard-closure.json", observations)
    assert all(x["verification"] == "PASSED" and x["closed"] and x["retained_handles_count"] == 0 and not x["errors"] for x in observations)
    print(json.dumps({"decision": report["decision"], "source_checks": ref(O/"source-check.json"), "held_public_refs": len(refs), "all_guards_closed": True}, ensure_ascii=False))
code = 0
try:
    main()
except Exception:
    traceback.print_exc()
    code = 1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
