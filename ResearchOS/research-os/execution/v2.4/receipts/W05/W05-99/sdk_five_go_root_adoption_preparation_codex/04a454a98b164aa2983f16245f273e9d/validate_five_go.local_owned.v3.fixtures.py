"""Bounded local verification for the five Go changes; no real provider requests."""
import sys
sys.dont_write_bytecode = True
import hashlib, json, os, types, uuid
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
PREP = Path(__file__).resolve().parent
OUT = PREP / "actual-go-validation-v3-fixtures"
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

results = []
cli_binary = OUT / "researchos.exe"
control_binary = OUT / "researchos-control.exe"
results.append(run("build-cli-binary", ["build", "-trimpath", "-o", str(cli_binary), "./apps/cli"], 600))
results.append(run("build-control-binary", ["build", "-trimpath", "-o", str(control_binary), "./apps/control"], 600))
(OUT / "cli-protocol-fixtures").mkdir(exist_ok=False)
(OUT / "host-fixtures").mkdir(exist_ok=False)
env["RESEARCHOS_CLI_PROTOCOL_BINARY"] = str(cli_binary)
env["RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR"] = str(OUT / "cli-protocol-fixtures")
env["RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"] = str(OUT / "host-fixtures")
results.append(run("cli-strict-response-with-compiled-binary", ["test", "-count=1", "-timeout=120s", "-v", "./apps/cli", "-run", "^TestCLIProtocolStrictResponse$"], 180))
results.append(run("host-control", ["test", "-count=1", "-timeout=120s", "-v", "./internal/host", "./apps/control", "-run", "^(TestConfigurationMetadataActualHostWithoutDecrypt|TestW03NativeHostUsesCurrentMuContracts|TestW03PrivateOwnerBootstrap|TestLocalPrincipalCredentialAdministration)$"], 180))
ref = save("validation.closed.json", {"schema": "researchos.sdk-five-go-local-validation.v1", "operations": results, "status": "BINARY_BUILD_CLI_PROTOCOL_AND_HOST_TESTS_COMPLETED", "canonical_unchanged": True, "provider_requests": 0, "formal_acceptance_delta": 0, "test_environment": "TRUSTED_DEVELOPMENT_ONLY", "cli_binary_ref": pin(cli_binary), "control_binary_ref": pin(control_binary), "temporary_root": str(TEMP), "prior_passes_preserved_not_repeated": ["actual-go-validation-v2-readonly/build-packages.invocation.json", "actual-go-validation-v2-readonly/domain-qualification.invocation.json", "six inline CLI tests passed in original v2 stdout"]})
print(json.dumps({"validation_ref": ref}), flush=True)
