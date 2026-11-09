"""Read existing build receipts only. Never spawn, import builder, or run CLI."""
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path("D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-03-20261104")
ARTIFACT = ROOT / ".local/cli-v1-artifact-01"
OWNER = Path(__file__).resolve().parent
OUTER = OWNER.parent / "product-v1-owned-verification-20261104"
HEAD = "c4029c0b57599e1aafed6d01ea4034b0cf465ccd"
MANIFEST_SHA = "ef603e5dc373d01a67f5a0d9b6b2c56e82bd03b89f58d3dbb10bfcc6feb5b3b9"
BINARY_SHA = "881e26a2784cab412c21e3f6b3e562d031d9f10479911953a83ef5888a7a4da7"

def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def load(path):
    return json.loads(Path(path).read_bytes())

def check(value, label):
    if not value:
        raise RuntimeError(label)

def regular(path):
    info = path.lstat()
    return stat.S_ISREG(info.st_mode) and not path.is_symlink() and not (info.st_file_attributes & 0x400)

manifest_path = ARTIFACT / "artifact-manifest.json"
check(regular(manifest_path) and sha(manifest_path) == MANIFEST_SHA, "manifest pin")
m = load(manifest_path)
binary = ARTIFACT / "bin/researchos.exe"
check(m["binary"]["path"] == str(binary), "binary path")
check(regular(binary) and binary.stat().st_size == m["binary"]["bytes"] == 20147712, "binary regular size")
check(sha(binary) == m["binary"]["sha256"] == BINARY_SHA, "binary digest")
check(m["qualification"] == "BUILT_NOT_EXECUTED" and m["application_executed"] is False, "qualification")
before_path = ARTIFACT / "receipts/inputs.before.json"
after_path = ARTIFACT / "receipts/inputs.after.json"
check(sha(before_path) == m["inputs_before_sha256"] and sha(after_path) == m["inputs_after_sha256"], "closure receipt pins")
before, after = load(before_path), load(after_path)
for field in ("compiled", "extra", "source"):
    check(before[field] == after[field], "before/after " + field)
check(before["source"] == m["source"] and m["source"]["head"] == HEAD, "source binding")
check(m["source"]["status_sha256"] == hashlib.sha256(b"").hexdigest(), "clean source")
extra = {row["path"]: row for row in before["extra"]}
for path, expected in ((ROOT / "go.mod", m["go_mod_sha256"]),
                       (ROOT / "go.sum", m["go_sum_sha256"]),
                       (ROOT / "apps/desktop/build-development.py", m["build_helper_sha256"]),
                       (OWNER.parent / "product-v1-cli-component-build-01.py", m["recipe_sha256"])):
    row = extra[str(path.resolve(strict=True))]
    check(row["sha256"] == expected and sha(path) == expected and path.stat().st_size == row["bytes"], "extra input " + path.name)
check(m["build_helper_sha256"] == "f571ef6b73b8e7e2ce94113c6749b0aac0a5e1851f59dc7fbb2eafd213690032", "helper pin")
check(m["recipe_sha256"] == "474838a3f75e2ce148943d3cfc92b62f97b7c03922b27366b4857f349081aa3c", "wrapper pin")
check(m["toolchain"]["version"] == "go1.27.1" and m["toolchain"]["go_sha256"] == "d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490", "Go binding")
check(not any(any(mark in key.upper() for mark in ("TOKEN", "SECRET", "PASSWORD", "APIKEY", "API_KEY", "PROXY")) for key in before["effective_environment"]), "no secret environment keys")
command_names = ["source-before-head", "source-before-tree", "source-before-status", "cli-go-list-before",
                 "cli-go-build", "cli-artifact-buildinfo", "cli-go-list-after", "source-after-head", "source-after-tree", "source-after-status"]
commands = []
for name in command_names:
    folder = ARTIFACT / "receipts/commands" / name
    result = load(folder / "result.json")
    check(result["native_exit"] == 0, "command exit " + name)
    for stream in ("stdout", "stderr"):
        check(sha(folder / (stream + ".raw")) == result[stream + "_sha256"], "raw receipt " + name + stream)
    commands.append({"name": name, "native_exit": 0, "result_sha256": sha(folder / "result.json")})
info_path = ARTIFACT / "receipts/commands/cli-artifact-buildinfo/stdout.raw"
check(sha(info_path) == m["buildinfo_stdout_sha256"], "PE buildinfo hash")
info = info_path.read_text(encoding="utf-8")
for line in ("\tpath\tresearchos.local/research-os/apps/cli", "\tbuild\tvcs.revision=" + HEAD,
             "\tbuild\tvcs.modified=false", "\tbuild\tGOOS=windows", "\tbuild\tGOARCH=amd64", "\tbuild\tCGO_ENABLED=0"):
    check(line in info.splitlines(), "buildinfo " + line)
check(info.splitlines()[0] == str(binary) + ": go1.27.1", "buildinfo binary/version")
recipe = load(info_path.parent / "recipe.json")
check(recipe["argv"][1:] == ["version", "-m", str(binary)], "metadata-only recipe")
producer = load(ARTIFACT / "receipts/result.json")
check(producer["status"] == "BUILT_NOT_EXECUTED" and producer["native_exit"] == 0 and producer["build_inputs_unchanged"] is True, "producer status")
check(producer["artifact_manifest_sha256"] == MANIFEST_SHA and producer["binary_sha256"] == BINARY_SHA, "producer pins")
for field in ("application_executions", "native_host_operations", "model_requests", "formal_increment"):
    check(producer[field] == 0, "producer non-execution " + field)
check(producer["help_executed"] is False, "help not run")
scope_path = OUTER / "scopes/product-v1-cli-build-01.json"
outer_path = OUTER / "runs/product-v1-cli-build-01/RESULT.json"
scope, outer = load(scope_path), load(outer_path)
check(outer["scope_sha256"] == sha(scope_path) and outer["scope_id"] == scope["scope_id"] == "product-v1-cli-build-01", "outer scope binding")
check(outer["status"] == "COMPLETED_OWNED_JOB_STOPPED" and outer["root_exit_code"] == 0, "outer status")
for field in ("stop_proved", "root_signaled", "job_active_zero", "job_assigned", "resumed"):
    check(outer[field] is True, "outer " + field)
check(not outer["errors"] and not outer["timed_out"] and not outer["input_drift"] and not outer["raw_limit_exceeded"], "outer errors/drift")
check(outer["terminate_job_attempts"] == outer["terminate_original_root_attempts"] == 0, "no forced termination")
report = {"schema": "researchos.cli-component-artifact-independent-review/1",
          "decision": "APPROVED_BUILT_NOT_EXECUTED", "blocking_findings": [],
          "manifest_sha256": MANIFEST_SHA, "binary": m["binary"], "source": m["source"],
          "input_closure": {"before_sha256": sha(before_path), "after_sha256": sha(after_path),
                            "before_after_fields_equal": ["compiled", "extra", "source"],
                            "package_count": before["compiled"]["package_count"],
                            "tool_count": before["compiled"]["tool_count"],
                            "compiled_file_count": len(before["compiled"]["files"]),
                            "extra_file_count": len(before["extra"]),
                            "scope": "Persisted pre/post closure equality and receipt digests independently checked; not a new compilation or a rehash of every original compiled source."},
          "buildinfo": {"sha256": sha(info_path), "source_revision": HEAD, "vcs_modified": False,
                        "Go": "go1.27.1", "GOOS": "windows", "GOARCH": "amd64", "CGO_ENABLED": "0",
                        "observation": "Existing metadata stdout and exact go version -m recipe read; binary not executed."},
          "commands": commands,
          "outer": {"scope_sha256": sha(scope_path), "result_sha256": sha(outer_path), "status": outer["status"],
                    "stop_proved": True, "root_exit_code": 0, "root_signaled": True, "job_active_zero": True,
                    "terminate_job_attempts": 0, "terminate_original_root_attempts": 0},
          "review_side_effects": {"application_executions": 0, "Host_operations": 0, "model_requests": 0,
                                 "D_writes": 0, "new_build_or_Go_execution": 0, "credentials_or_old_DB_reads": 0},
          "runtime_qualification": False, "business_acceptance": False, "formal_increment": 0,
          "note": "Build-only acceptance. CLI harness help and same-Host operations require separate exact Root scope."}
target = OWNER / "after-build-report.json"
with target.open("x", encoding="utf-8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"decision": report["decision"], "report": str(target), "report_sha256": sha(target),
                  "package_count": report["input_closure"]["package_count"],
                  "compiled_file_count": report["input_closure"]["compiled_file_count"]}))
