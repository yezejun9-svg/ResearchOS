"""Independent source-only review; never launches Go, product, SQLite, or OwnedProcess."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parent.parent / "fresh_main23_programme_builder_source_codex" / "main23b-20261009-01"


def ref(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def save(name: str, value: dict):
    target = HERE / name
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ref(target)


def main():
    contract = json.loads((AUTHOR / "contract.json").read_bytes())
    manifest = json.loads((AUTHOR / "input-manifest.json").read_bytes())
    facts = json.loads((AUTHOR / "source-facts.json").read_bytes())
    source = AUTHOR / "main23_builder.py"
    builder = load_module(source, "independent_main23_builder")
    guard_path = Path(contract["source_guard_ref"]["path"])
    guard_mod = load_module(guard_path, "independent_source_guard")

    controls = []
    def check(name, condition, detail=None):
        controls.append({"name": name, "passed": bool(condition), "detail": detail})

    for key in ("builder_ref", "input_manifest_ref", "base_helper_ref", "source_guard_ref", "owned_job_ref", "go_ref", "toolchain_lock_ref", "source_facts_ref"):
        expected = contract[key]
        actual = ref(Path(expected["path"]))
        check(f"exact-{key}", actual["sha256"] == expected["sha256"] and actual["bytes"] == expected["bytes"])
    kinds = {kind: sum(x["kind"] == kind for x in manifest["items"]) for kind in ("main", "module", "toolchain")}
    check("input-counts", kinds == manifest["counts"] and sum(kinds.values()) == 14670, kinds)
    check("input-bytes", {k: sum(x["ref"]["bytes"] for x in manifest["items"] if x["kind"] == k) for k in kinds} == manifest["bytes"])
    check("three-key-refs", all(set(x["ref"]) == {"path", "sha256", "bytes"} for x in manifest["items"]))
    check("current-main-five-in-input", all(x in [i["ref"] for i in manifest["items"]] for x in contract["current_main_source_refs"]))
    check("current-main-facts-agree", facts["current_main_source_refs"] == contract["current_main_source_refs"])
    check("main-migrations-1-to-23", [Path(x["path"]).name[:4] for x in facts["numbered_migration_refs"]] == [f"{n:04}" for n in range(1, 24)])
    check("main-no-24", not (Path(contract["main_root"]) / "migrations/sqlite/0024_prepared_run_abandonment.sql").exists())
    check("no-shared-gocache", manifest["shared_GOCACHE_files_included"] == 0 and all("/.local/gocache/" not in x["ref"]["path"].replace("\\", "/").lower() for x in manifest["items"]))

    request = {"case_id": "a" * 32, "output_root": contract["output_parent"] + "/fresh-main23-" + "a" * 32}
    projection = builder.compile_request(contract, request, None if False else load_module(Path(contract["base_helper_ref"]["path"]), "independent_base"))
    phases = projection["phases"]
    check("five-go-phases", [p["id"] for p in phases] == ["go-version", "list-declared", "list-export", "build-main23", "inspect-binary"])
    check("exact-go-argv", all(p["argv"][0] == contract["go_ref"]["path"] for p in phases))
    check("compiled-declared", phases[1]["argv"] == [contract["go_ref"]["path"], "list", "-deps", "-compiled", "-json", "./ops/backup"])
    check("compiled-export", phases[2]["argv"] == [contract["go_ref"]["path"], "list", "-deps", "-compiled", "-export", "-json", "./ops/backup"])
    check("build-work-retained", "-work" in phases[3]["argv"] and "-x" in phases[3]["argv"])
    env = builder.environment(contract, projection["paths"])
    check("offline-env", all(env[k] == v for k, v in {"GOPROXY": "off", "GOSUMDB": "off", "GOTOOLCHAIN": "local", "GOENV": "off", "GOWORK": "off", "CGO_ENABLED": "0"}.items()))
    check("unique-cache", env["GOCACHE"] == projection["paths"]["gocache"] and env["GOMODCACHE"] == projection["paths"]["module_cache"])

    class FakeBase:
        @staticmethod
        def closed_job(o):
            return True
    good = {"creation_time_100ns": (1 << 63) + 37, "owned_child_pid": 1013}
    check("exact-uint64-filetime", builder.validate_owned(good, FakeBase()))
    for name, change in [("filetime-float", {"creation_time_100ns": float(1 << 63)}), ("filetime-overflow", {"creation_time_100ns": 1 << 64}), ("pid-float", {"owned_child_pid": 1013.0}), ("pid-overflow", {"owned_child_pid": 1 << 32})]:
        try:
            builder.validate_owned({**good, **change}, FakeBase())
        except builder.BuildBoundaryError:
            check(name, True)
        else:
            check(name, False)

    tree = ast.parse(source.read_bytes())
    run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_registered_build")
    calls = [n for n in ast.walk(run) if isinstance(n, ast.Call)]
    check("one-owned-run-site", sum(isinstance(n.func, ast.Attribute) and n.func.attr == "run_owned" for n in calls) == 1)
    check("registration-before-output", source.read_text(encoding="utf-8").index("root_scope.require_registered") < source.read_text(encoding="utf-8").index("root.mkdir()"))
    check("candidate-unqualified", b'"qualification_ref": None' in source.read_bytes())
    check("cleanup-finally", any(isinstance(n, ast.Try) and n.finalbody for n in ast.walk(run)))

    # Historical go-list is an enumeration hint only. Its package file fields
    # should already be represented in the current exact-byte input inventory.
    old_hint = Path(manifest["module_hint_ref"]["path"])
    hint_data = old_hint.read_bytes()
    check("historical-hint-pin", len(hint_data) == manifest["module_hint_ref"]["bytes"] and hashlib.sha256(hint_data).hexdigest() == manifest["module_hint_ref"]["sha256"])
    packages = builder.parse_json_stream(hint_data)
    manifest_paths = {str(Path(x["ref"]["path"]).resolve()).lower() for x in manifest["items"]}
    by_import = {p.get("ImportPath"): p for p in packages if not p.get("ForTest")}
    target = contract["module_path"] + "/ops/backup"
    needed = set()
    frontier = [target]
    while frontier:
        name = frontier.pop()
        if name in needed:
            continue
        needed.add(name)
        pkg = by_import.get(name)
        if pkg:
            frontier.extend(pkg.get("Imports") or [])
    missing = []
    for pkg in packages:
        if pkg.get("ImportPath") not in needed or pkg.get("ForTest"):
            continue
        folder = Path(pkg.get("Dir", ""))
        for field in builder.FILE_FIELDS:
            for value in pkg.get(field) or []:
                path = Path(value) if Path(value).is_absolute() else folder / value
                if str(path.resolve()).lower() not in manifest_paths:
                    missing.append({"package": pkg.get("ImportPath"), "field": field, "path": str(path)})
    check("historical-go-list-file-closure", target in by_import and not missing, {"packages": len(packages), "needed": len(needed), "missing_count": len(missing), "sample": missing[:20]})

    refs = [i["ref"] for i in manifest["items"]]
    refs += [contract[k] for k in ("builder_ref", "input_manifest_ref", "base_helper_ref", "source_guard_ref", "owned_job_ref", "toolchain_lock_ref")]
    guard = guard_mod.SourceReadGuard(total_cap=512 * 1024 * 1024)
    guard_error = None
    started = time.monotonic()
    try:
        guard.acquire(refs)
    except Exception as exc:
        guard_error = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        guard_audit = guard.close()
    guard_report = {"schema": "researchos.main23-independent-source-guard.v1", "ref_count": len(refs), "byte_sum": sum(x["bytes"] for x in refs), "elapsed_seconds": round(time.monotonic() - started, 3), "error": guard_error, "audit": guard_audit}
    guard_ref = save("source-guard-audit.json", guard_report)
    check("real-source-read-guard", guard_error is None and guard_audit["verification"] == "PASSED" and guard_audit["closed"] is True and guard_audit["retained_handles_count"] == 0 and not guard_audit["errors"], {"ref": guard_ref, "error": guard_error})
    report = {"schema": "researchos.main23-independent-source-controls.v1", "author": "codex:/root/w09_formal_profile_source_impl", "target_ref": ref(source), "controls": controls, "passed": sum(x["passed"] for x in controls), "failed": sum(not x["passed"] for x in controls), "no_go_or_product_or_database_or_owned_process_calls": True}
    save("independent-controls.json", report)
    print(json.dumps({"passed": report["passed"], "failed": report["failed"], "failures": [x for x in controls if not x["passed"]], "guard": {k: guard_report[k] for k in ("ref_count", "byte_sum", "elapsed_seconds", "error")}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
