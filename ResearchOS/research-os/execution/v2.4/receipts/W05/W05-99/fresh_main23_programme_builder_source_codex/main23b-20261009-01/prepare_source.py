"""Author-time bounded Source inventory; never executes Go or product code."""
from pathlib import Path
import hashlib
import json
import re

O = Path(__file__).resolve().parent
R = Path("D:/作品集/ResearchOS/research-os")
B = R / "execution/v2.4/receipts/W05/W05-99"
G = R / ".local/tools/go1.27.1/go"
M = R / ".local/gopath/pkg/mod"
SCOPES = ["internal", "adapters", "apps/control", "ops", "evaluation", "migrations", "contracts", "spec/v2.0/contracts"]
HINT = B / "main_configuration_composition_independent_review_codex/c34b6453-73e7-42ad-8ac0-511231cf78ab/go-list.stdout.raw"
OLD_BUILDER = B / "host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/build.py"
BASE = B / "genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v2/public22_runner.py"
GUARD = B / "source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
JOB = B / "integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"


def ref(path):
    data = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write(name, value):
    with (O / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write("\n")
    return ref(O / name)


def checked_file(path):
    assert path.is_file() and not path.is_symlink() and not path.is_junction(), str(path)
    assert path.stat().st_size <= 128 * 1024 * 1024, str(path)
    return path


main_files = {R / "go.mod", R / "go.sum"}
for scope in SCOPES:
    folder = R / scope
    assert folder.is_dir(), str(folder)
    for file in folder.rglob("*"):
        if file.is_file() and not any(p in ("__pycache__", ".git", "node_modules") for p in file.relative_to(folder).parts):
            main_files.add(checked_file(file))

raw = HINT.read_text(encoding="utf-8"); decoder = json.JSONDecoder(); packages = []
while raw.strip():
    raw = raw.lstrip(); package, end = decoder.raw_decode(raw); packages.append(package); raw = raw[end:]
module_files, module_dirs = set(), set()
for package in packages:
    if not package.get("Dir"):
        continue
    folder = Path(package["Dir"])
    if not folder.is_relative_to(M):
        continue
    module_dirs.add(folder)
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in (".go", ".s", ".h", ".c", ".cc", ".cpp", ".m", ".f", ".syso", ".swig", ".swigcxx"):
            module_files.add(checked_file(file))
    for key in ["EmbedFiles", "TestEmbedFiles", "XTestEmbedFiles"]:
        for name in package.get(key, []):
            module_files.add(checked_file(folder / name))
    if package.get("Module", {}).get("GoMod"):
        module_files.add(checked_file(Path(package["Module"]["GoMod"])))

go_mod = (R / "go.mod").read_text(encoding="utf-8")
versions = dict(re.findall(r"^\s*([A-Za-z0-9._~!/+\-]+)\s+(v[^\s]+)", go_mod, re.M))
assert len(versions) >= 15 and "replace " not in go_mod
metadata_candidates = set()
for line in (R / "go.sum").read_text(encoding="utf-8").splitlines():
    module, version, _ = line.split()
    metadata_candidates.add((module, version.removesuffix("/go.mod")))
for module, version in versions.items():
    assert not any(c.isupper() for c in module), "Explicit escaped module-path support required"
    folder = M / (module + "@" + version)
    module_files.add(checked_file(folder / "go.mod"))
    for suffix in [".mod", ".info", ".ziphash"]:
        module_files.add(checked_file(M / "cache/download" / module / "@v" / (version + suffix)))
for module, version in metadata_candidates:
    for suffix in [".mod", ".info"]:
        file = M / "cache/download" / module / "@v" / (version + suffix)
        if file.is_file():
            module_files.add(checked_file(file))

tool_files = {G / "bin/go.exe", G / "VERSION", G / "go.env"}
for scope in ["src", "pkg/tool", "pkg/include", "lib"]:
    tool_files.update(checked_file(p) for p in (G / scope).rglob("*") if p.is_file())
lockpath = R / "execution/toolchains/locked.json"
lock = json.loads(lockpath.read_text(encoding="utf-8-sig"))
go_ref = ref(G / "bin/go.exe")
assert lock["tools"]["go"]["sha256"] == go_ref["sha256"]
assert lock["tools"]["go"]["version_output"] == "go version go1.27.1 windows/amd64"
assert (G / "VERSION").read_text().splitlines()[0] == "go1.27.1"
assert re.search(r"^go 1\.27\.1$", go_mod, re.M)

items = []
for kind, root, files in [("main", R, main_files), ("module", M, module_files), ("toolchain", G, tool_files)]:
    for file in sorted(files):
        items.append({"kind": kind, "relative_path": file.relative_to(root).as_posix(), "ref": ref(file)})
assert sum(x["ref"]["bytes"] for x in items) < 500 * 1024 * 1024
assert sum(x["ref"]["bytes"] for x in items if x["kind"] in ("main", "module")) < 250 * 1024 * 1024
manifest = write("input-manifest.json", {"schema": "researchos.current-main23-source-inputs.v1", "items": items,
    "source_kind": "CURRENT_MAIN_BYTE_PINS_NOT_GIT_COMMIT_RELEASE", "main_scopes": SCOPES,
    "module_hint_ref": ref(HINT), "hint_role": "Enumeration hint only; all current bytes independently hashed, future Go list must close exactly over frozen copies",
    "dependency_package_dirs": [p.as_posix() for p in sorted(module_dirs)],
    "shared_GOCACHE_files_included": 0, "module_zip_archives_copied": 0,
    "counts": {k: sum(x["kind"] == k for x in items) for k in ["main", "module", "toolchain"]},
    "bytes": {k: sum(x["ref"]["bytes"] for x in items if x["kind"] == k) for k in ["main", "module", "toolchain"]}})

current_refs = [ref(R / name) for name in ["ops/backup/main.go", "internal/domain/backup.go", "internal/domain/backup_upgrade.go", "internal/domain/backup_configuration_upgrade.go", "internal/domain/backup_host_configuration.go"]]
public_contract = json.loads((BASE.parent / "contract.json").read_bytes())
assert current_refs == public_contract["current_main_source_refs"]
numbered = sorted((R / "migrations/sqlite").glob("0*.sql"))
assert [int(p.name[:4]) for p in numbered] == list(range(1, 24))
absent = ["internal/domain/backup_prepared_abandonment_upgrade.go", "migrations/sqlite/0024_prepared_run_abandonment.sql"]
assert all(not (R / p).exists() for p in absent)
facts = write("source-facts.json", {"schema": "researchos.current-main23-builder-source-facts.v1", "current_main_source_refs": current_refs,
    "numbered_migration_refs": [ref(p) for p in numbered], "main_public_plan": "schema22-to23-host-model-configuration-v1",
    "main23to24": "BLOCKED_MAIN_NOT_ADOPTED", "absent_main_paths": absent, "schema21": "OPEN", "full20to24": "OPEN",
    "go_ref": go_ref, "toolchain_lock_ref": ref(lockpath), "go_version_ref": ref(G / "VERSION"),
    "old_main23_candidate_binding": "REJECTED_SOURCE_DRIFT", "old_main23_candidate": public_contract["main23_candidate_only"],
    "drift": public_contract["main23_candidate_drift"], "old22_builder_ref": ref(OLD_BUILDER),
    "old22_builder_direct_reuse": "NOT_SUITABLE_AS_NEW_REGISTERED_BUILDER; ordinary subprocess and inherited environment",
    "historical_main_builder_ref": ref(HINT.parent / "run.py"),
    "historical_main_builder_direct_reuse": "NOT_SUITABLE_AS_NEW_REGISTERED_BUILDER; ordinary subprocess and inherited environment",
    "public22_v2_source_acceptance_ref": ref(B / "public22_runner_independent_source_review_codex/pub22r-20261009-02/source-decision.json"),
    "Go_invocations_during_Source_preparation": 0, "product_invocations": 0, "SQLite_calls": 0, "native_API_calls": 0})
contract = {"schema": "researchos.current-main23-builder-contract.v1", "status": "SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION",
    "source_author": "codex:/root/native_temp_independent_review", "builder_ref": ref(O / "main23_builder.py"), "schema_version": 23,
    "main_root": R.as_posix(), "main_scopes": SCOPES, "goroot": G.as_posix(), "module_path": "researchos.local/research-os",
    "module_versions": versions, "go_ref": go_ref, "toolchain_lock_ref": ref(lockpath), "input_manifest_ref": manifest,
    "base_helper_ref": ref(BASE), "source_guard_ref": ref(GUARD), "owned_job_ref": ref(JOB), "source_facts_ref": facts,
    "current_main_source_refs": current_refs, "output_parent": (B / "integration_codex").as_posix(),
    "entry": "main23_builder.run_registered_build(contract_ref, request_ref, live_root_scope)",
    "request_fields": ["case_id", "output_root"], "exact_output_basename": "fresh-main23-<32lowerhex>",
    "Root_caller_interface": ["require_registered(contract_ref, request_ref, source_author=...)", "require_phase(phase, request_ref, output_root)", "receipt_context()"],
    "Root_require_registered_must_enforce": ["live owner/scope/lease and current canonical registration",
        "non-author Source review covering all exact builder, helper, contract and source-input refs",
        "this leaf, helpers and bootstrap contract held before leaf entry",
        "caller Python/runtime/loaded-native resource closure qualified and held through final Job and guard cleanup",
        "qualified Go1.27.1 toolchain and Windows load dependencies bound; no mutable command-resolution PATH",
        "fresh unused exact output directory reserved to this case",
        "full original Root wrapper/tool request and raw response captured without IEEE-754 numeric conversion",
        "Root persists returned failure state if build.closed.json cannot be published and assigns original failure ordinal; never automatic retry"],
    "phases": ["prepare", "go-version", "list-declared", "list-export", "build-main23", "inspect-binary"],
    "execution_limits": {"Go_processes_maximum": 5, "version_timeout_seconds": 30, "list_declared_timeout_seconds": 120, "export_and_build_timeout_seconds_each": 600,
        "raw_output_bytes_each_postcompletion": 16777216, "toolchain_and_source_guard_bytes": 536870912, "frozen_copy_guard_bytes": 268435456},
    "GOCACHE_policy": "Unique initially empty GOCACHE; no shared cache copying. Retain and pin go-list export records plus before/after build cache vectors.",
    "module_cache_policy": "Copy only exact declared Source inventory into unique sparse GOMODCACHE; GOPROXY/GOSUMDB off; no automatic additions. Additional empty .lock files are recorded and allowed; new module inputs fail closed.",
    "source_policy": "Verify current Main inventory and exact Source pins before every Go phase; hold original refs and readonly frozen copies; go list closure must name only pre-held inputs; capture before/after exact vectors.",
    "process_policy": "Pinned Windows OwnedProcess only; suspended primary assigned to unnamed typed Job before resume; Python int FILETIME in 1..2**64-1; exact uint32 PID; primary exit plus Job idle/closed. Individual descendant exits remain unknown null.",
    "output_contract": {"candidate": ["program_ref", "provenance_ref", "source_refs", "qualification_ref=null"],
        "qualification": "Independent non-author review of actual build provenance followed by Root binding is required. Builder never emits its own accepted qualification.",
        "public22_end23_binding": ["program_ref", "qualification_ref from independent actual review", "source_refs exactly matching current Main five refs"]},
    "schema21": "OPEN", "full20to24": "OPEN", "main23to24": "BLOCKED_MAIN_NOT_ADOPTED", "formal_acceptance": False}
contract_ref = write("contract.json", contract)
print(json.dumps({"input_manifest_ref": manifest, "contract_ref": contract_ref, "source_facts_ref": facts, "items": len(items), "counts": json.loads((O / "input-manifest.json").read_bytes())["counts"], "Go_processes": 0}))
