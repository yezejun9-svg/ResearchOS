"""Root compile-only evidence. No target Host or provider execution."""
import sys
sys.dont_write_bytecode = True
import hashlib, json, types, uuid
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
OUT = Path(__file__).resolve().parent
SRC = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_codex/991a41da6cb146d9a5fae91c438f6d07"
TEMP = ROOT / ".local" / ("trusted-host-build-" + uuid.uuid4().hex)
TEMP.mkdir(exist_ok=False)
(TEMP / "profile").mkdir()
(TEMP / "temp").mkdir()
binary = TEMP / "trusted-qualification-host.exe"

def pin_bytes(p, b):
    return {"path": str(p), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

def pin(p):
    return pin_bytes(p, p.read_bytes())

def save(name, obj):
    p = OUT / name
    with p.open("xb") as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return pin(p)

expected = {
    SRC / "main.go": ("ca2ec665c0f770e9ce27e0302e896752d2bd696055f18e54df14628483d30b20", 8556),
    SRC / "hostapi.go": ("da99a21763d8ae99787fd4dd12b2ac9fe9bcb34e8c269be3dcfed01cf17ef19f", 6655),
    SRC / "prepare.go": ("cde3dfe9f9c51fb5dcbdf39a0783c05c85f984266784619a0838033c35db7d23", 14447),
    SRC / "execute.go": ("5b770ecbfd8d3b9990b270a3c7cc1d5988dd841aadcd17f76b28294555fe3877", 22573),
    SRC / "manifest.json": ("7ff68b376bcb46de22632c861194d9a46638759cd5464a3c6a19382c1126d797", 7696),
    ROOT / "internal/host/vault.go": ("5bcf6aed6515bd991e5e7222999994e3d9192a6bd8f5a32b4669d4c67c0a6b50", 12082),
    ROOT / "internal/host/host.go": ("6387df33f531be14d32c439095f9ebcf079fb7ae2c27697c98cdc9a554fb5dc7", 8703),
    ROOT / "apps/control/main.go": ("9a519be38a1c09a819864073eedf0eaf9941c4c75f95ded0c3e89143012da9b1", 12674),
    ROOT / "internal/domain/runtime_qualification.go": ("420aaec664f877806af079d47cf5e5a0cc4950f2cdc42b8ae1dc16ef7a4c5c54", 16400),
    ROOT / "apps/cli/cli_stream.go": ("87bfbd69972e674ae5255455ed26ce82ece167d8bb67155beed0cd52c05b9e6f", 30399),
    ROOT / "execution/toolchains/locked.json": ("0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663", 2145),
}
frozen = {}
for p, (digest, count) in expected.items():
    b = p.read_bytes()
    assert len(b) == count and hashlib.sha256(b).hexdigest() == digest, str(p)
    frozen[p] = b
canon = [ROOT / "execution/v2.4" / (x + ".json") for x in ("checkpoint", "path_ownership", "step_state", "commands")]
canon_before = {p: p.read_bytes() for p in canon}
assert json.loads(canon_before[canon[0]])["revision"] == 342
locked = json.loads(frozen[ROOT / "execution/toolchains/locked.json"])
go = Path(locked["tools"]["go"]["path"])
assert pin(go)["sha256"] == "d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
helper_path = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
helper_bytes = helper_path.read_bytes()
assert len(helper_bytes) == 18901 and hashlib.sha256(helper_bytes).hexdigest() == "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
helper = types.ModuleType("root_trusted_host_build_owned_process")
helper.__file__ = str(helper_path)
exec(compile(helper_bytes, str(helper_path), "exec"), helper.__dict__)
environment = {
    "SystemRoot": "C:/Windows", "WINDIR": "C:/Windows", "ComSpec": "C:/Windows/System32/cmd.exe",
    "PATH": str(go.parent) + ";C:/Windows/System32;C:/Program Files/Git/cmd", "PATHEXT": ".COM;.EXE;.BAT;.CMD",
    "USERPROFILE": str(TEMP / "profile"), "LOCALAPPDATA": str(TEMP / "profile"), "APPDATA": str(TEMP / "profile"),
    "TEMP": str(TEMP / "temp"), "TMP": str(TEMP / "temp"), "GOROOT": str(go.parent.parent),
    "GOPATH": str(ROOT / ".local/gopath"), "GOCACHE": str(ROOT / ".local/gocache"),
    "GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off", "GOWORK": "off",
    "CGO_ENABLED": "0", "GOFLAGS": "-mod=readonly -p=1", "GOMAXPROCS": "2",
}
argv = [str(go), "build", "-trimpath", "-o", str(binary)] + [str(SRC / name) for name in ("main.go", "hostapi.go", "prepare.go", "execute.go")]
before_ref = save("compile.before.json", {"source_and_main": [pin_bytes(p,b) for p,b in frozen.items()],
    "canonical": [pin_bytes(p,b) for p,b in canon_before.items()], "source_only": True})
save("compile.intent.json", {"argv": argv, "cwd": str(ROOT), "public_environment": environment,
    "wall_seconds": 180, "go_ref": pin(go), "owned_process_helper_ref": pin_bytes(helper_path, helper_bytes),
    "before_ref": before_ref, "host_executions_authorized": 0, "provider_requests_authorized": 0,
    "formal_acceptance": False, "runtime_qualification": False})
stdout, stderr = OUT / "compile.stdout.raw", OUT / "compile.stderr.raw"
result, exception = None, None
try:
    with stdout.open("xb") as out, stderr.open("xb") as err:
        result = helper.run_owned(argv, str(ROOT), environment, out, err, 180)
except BaseException as exc:
    exception = repr(exc)
finally:
    unchanged = {str(p): p.read_bytes() == b for p,b in {**frozen, **canon_before}.items()}
    invocation_ref = save("compile.invocation.json", {
        "argv": argv, "cwd": str(ROOT), "result": result, "exception": exception,
        "actual_native_exit": result["actual_exit"] if result else None,
        "stdout_ref": pin(stdout), "stderr_ref": pin(stderr),
        "frozen_inputs_unchanged": unchanged, "target_host_executions": 0, "provider_requests": 0,
        "runtime_qualification": False, "formal_acceptance": False})
    print(json.dumps({"invocation_ref": invocation_ref, "actual_native_exit": result["actual_exit"] if result else None}), flush=True)
assert exception is None and result is not None
assert all(unchanged.values()), "Source/Main/canonical changed during compilation"
assert result["actual_exit"] == 0 and result["error"] is None and not result["timed_out"], "actual Go compile failed"
cleanup = result["job_cleanup"]
assert cleanup["errors"] == [] and cleanup["active_processes_last_observed"] == 0
assert all(cleanup[k] is True for k in ("unnamed_exclusive_job", "kill_on_job_close_configured",
    "assigned_before_resume", "primary_exit_confirmed", "job_idle_confirmed", "handles_closed"))
closed = save("compile.closed.json", {"status": "COMPILED_SOURCE_ONLY", "invocation_ref": invocation_ref,
    "binary_ref": pin(binary), "before_ref": before_ref, "source_and_main_unchanged": True,
    "canonical_unchanged": True, "owned_job_cleanup_confirmed": True,
    "target_host_executions": 0, "provider_requests": 0, "runtime_qualification": False, "formal_acceptance": False})
print(json.dumps({"status": "COMPILED_SOURCE_ONLY", "closed_ref": closed, "binary_ref": pin(binary)}), flush=True)

