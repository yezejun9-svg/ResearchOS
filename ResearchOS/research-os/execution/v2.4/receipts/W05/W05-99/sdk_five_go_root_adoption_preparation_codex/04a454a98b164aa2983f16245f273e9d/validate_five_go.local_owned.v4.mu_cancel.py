"""Bounded local verification for the five Go changes; no real provider requests."""
import sys
sys.dont_write_bytecode = True
import hashlib, json, os, types, uuid
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
PREP = Path(__file__).resolve().parent
OUT = PREP / "actual-go-validation-v4-mu-cancel"
OUT.mkdir(exist_ok=False)
TEMP = ROOT / ".local" / ("sdk-five-go-validation-" + uuid.uuid4().hex)
TEMP.mkdir(exist_ok=False)
(TEMP / "temp").mkdir()
(TEMP / "profile").mkdir()
lock_path = ROOT / "execution/toolchains/locked.json"
raw = lock_path.read_bytes()
assert len(raw) == 2145 and hashlib.sha256(raw).hexdigest() == "0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663"
lock = json.loads(raw)
go = Path(lock["tools"]["go"]["path"])
assert hashlib.sha256(go.read_bytes()).hexdigest() == lock["tools"]["go"]["sha256"]
helper_path = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
raw = helper_path.read_bytes()
assert len(raw) == 18901 and hashlib.sha256(raw).hexdigest() == "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
helper = types.ModuleType("sdk5_root_owned_process")
helper.__file__ = str(helper_path)
exec(compile(raw, str(helper_path), "exec"), helper.__dict__)
env = {
    "SystemRoot": "C:/Windows", "WINDIR": "C:/Windows", "ComSpec": "C:/Windows/System32/cmd.exe",
    "PATH": str(go.parent) + ";C:/nvm4w/nodejs;C:/Windows/System32;C:/Program Files/Git/cmd",
    "PATHEXT": ".COM;.EXE;.BAT;.CMD",
    "USERPROFILE": str(TEMP / "profile"), "LOCALAPPDATA": str(TEMP / "profile"),
    "APPDATA": str(TEMP / "profile"), "TEMP": str(TEMP / "temp"), "TMP": str(TEMP / "temp"),
    "GOROOT": str(go.parent.parent), "GOPATH": str(ROOT / ".local/gopath"),
    "GOCACHE": str(ROOT / ".local/gocache"), "GOTOOLCHAIN": "local", "GOPROXY": "off",
    "GOSUMDB": "off", "GOWORK": "off", "CGO_ENABLED": "0",
    "GOFLAGS": "-mod=readonly -p=1", "GOMAXPROCS": "2",
    "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1", "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "nul", "GIT_TERMINAL_PROMPT": "0",
}
prep = json.loads((PREP / "preparation.json").read_bytes())
expected = [(ROOT / x["target"], (Path(x["prepared_ref"]["path"])).read_bytes()) for x in prep["mapping"]]
assert all(p.read_bytes() == b for p, b in expected)
canon = [ROOT / "execution/v2.4" / (x + ".json") for x in ("checkpoint", "path_ownership", "step_state", "commands")]
canon_before = [p.read_bytes() for p in canon]
assert json.loads(canon_before[0])["revision"] == 340

def pin(p):
    b = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

def save(name, obj):
    p = OUT / name
    with p.open("xb") as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return pin(p)

def run(name, args, timeout):
    assert all(p.read_bytes() == b for p, b in expected)
    assert [p.read_bytes() for p in canon] == canon_before
    argv = [str(go)] + args
    stdout, stderr = OUT / (name + ".stdout.raw"), OUT / (name + ".stderr.raw")
    result, error = None, None
    save(name + ".intent.json", {"argv": argv, "cwd": str(ROOT), "public_environment": env,
        "wall_seconds": timeout, "provider_requests_authorized": 0, "formal_acceptance": False})
    try:
        with stdout.open("xb") as out, stderr.open("xb") as err:
            result = helper.run_owned(argv, str(ROOT), env, out, err, timeout)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        ref = save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "environment": env,
            "result": result, "exception": error, "actual_native_exit": result["actual_exit"] if result else None,
            "stdout_ref": pin(stdout) if stdout.exists() else None, "stderr_ref": pin(stderr) if stderr.exists() else None,
            "source_qualification": False, "formal_acceptance": False})
        print(json.dumps({"operation": name, "invocation_ref": ref,
            "actual_native_exit": result["actual_exit"] if result else None}), flush=True)
    assert result["actual_exit"] == 0 and result["error"] is None and not result["timed_out"], "local Go operation failed: " + name
    cleanup = result["job_cleanup"]
    assert cleanup["errors"] == [] and cleanup["active_processes_last_observed"] == 0
    assert all(cleanup[k] is True for k in ("unnamed_exclusive_job", "kill_on_job_close_configured",
        "assigned_before_resume", "primary_exit_confirmed", "job_idle_confirmed", "handles_closed"))
    assert [p.read_bytes() for p in canon] == canon_before
    assert all(p.read_bytes() == b for p, b in expected)
    return ref

node = Path(lock["tools"]["node"]["path"])
assert hashlib.sha256(node.read_bytes()).hexdigest() == lock["tools"]["node"]["sha256"]
git = Path(lock["tools"]["git"]["path"])
assert hashlib.sha256(git.read_bytes()).hexdigest() == lock["tools"]["git"]["sha256"]
build_script = ROOT / "adapters/runtime/mu/build.mjs"
bundle = TEMP / "mu-worker.mjs"
save("mu-bundle-build.intent.json", {"argv": [str(node), str(build_script), str(bundle)], "cwd": str(ROOT), "public_environment": env, "wall_seconds": 180, "provider_requests": 0, "build_script_ref": pin(build_script), "worker_source_ref": pin(ROOT / "adapters/runtime/mu/worker.mjs")})
result, error = None, None
stdout, stderr = OUT / "mu-bundle-build.stdout.raw", OUT / "mu-bundle-build.stderr.raw"
try:
    with stdout.open("xb") as out, stderr.open("xb") as err:
        result = helper.run_owned([str(node), str(build_script), str(bundle)], str(ROOT), env, out, err, 180)
except BaseException as exc:
    error = repr(exc)
    raise
finally:
    source_result = save("mu-bundle-build.invocation.json", {"result": result, "exception": error, "actual_native_exit": result["actual_exit"] if result else None, "stdout_ref": pin(stdout) if stdout.exists() else None, "stderr_ref": pin(stderr) if stderr.exists() else None})
    print(json.dumps({"operation": "mu-bundle-build", "invocation_ref": source_result, "actual_native_exit": result["actual_exit"] if result else None}), flush=True)
assert result["actual_exit"] == 0 and result["error"] is None and not result["timed_out"]
cleanup = result["job_cleanup"]
assert cleanup["errors"] == [] and cleanup["active_processes_last_observed"] == 0
assert all(cleanup[k] is True for k in ("unnamed_exclusive_job", "kill_on_job_close_configured", "assigned_before_resume", "primary_exit_confirmed", "job_idle_confirmed", "handles_closed"))
metadata = json.loads(bundle.with_name(bundle.name + ".build.json").read_bytes())
assert metadata["source_sha256"] == pin(ROOT / "adapters/runtime/mu/worker.mjs")["sha256"]
assert metadata["bundle_sha256"] == pin(bundle)["sha256"] and metadata["bundle_bytes"] == pin(bundle)["bytes"]
assert metadata["mu_commit"] == "8dfebe36508ac0c2508735bb866756dab9283e74" and metadata["vendored_files_verified"] == 5083
assert metadata["sdk_version"] == metadata["ai_version"] == "0.87.1" and metadata["esbuild_version"] == "0.28.2"
for source, name in [(bundle, "mu-worker.frozen.mjs"), (bundle.with_name(bundle.name + ".build.json"), "mu-worker.build.original.json")]:
    with (OUT / name).open("xb") as f:
        f.write(source.read_bytes())
env["RESEARCHOS_MU_BUNDLE"] = str(OUT / "mu-worker.frozen.mjs")
cancel = run("mu-typed-cancel-actual-bundle", ["test", "-count=1", "-timeout=90s", "-v", "./internal/domain", "-run", "^TestRuntimeMuTypedCancelStopsTransport$"], 120)
log = (OUT / "mu-typed-cancel-actual-bundle.stdout.raw").read_text(encoding="utf-8")
assert "--- PASS: TestRuntimeMuTypedCancelStopsTransport" in log and "--- SKIP:" not in log
assert "MU_CANCEL inflight_HTTP_stopped=true sandbox_stopped=true provider_calls=1" in log
ref = save("cancel.validation.closed.json", {"schema": "researchos.mu-sdk-local-cancel-validation.v1", "case_id": "TestRuntimeMuTypedCancelStopsTransport", "measurement_mode": "LOCAL_HTTP_FIXTURE_WITH_ACTUAL_CURRENT_MU_BUNDLE", "native_exit": 0, "actual_external_provider_requests": 0, "local_fixture_requests": 1, "invocation_refs": [source_result, cancel], "bundle_ref": pin(OUT / "mu-worker.frozen.mjs"), "bundle_metadata_ref": pin(OUT / "mu-worker.build.original.json"), "canonical_unchanged": True, "formal_acceptance_delta": 0})
print(json.dumps({"cancel_validation_ref": ref}), flush=True)
