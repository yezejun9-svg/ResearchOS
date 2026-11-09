"""Extracted-helper pure IO checks; never import candidate or spawn a child."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v3_source_codex/06f264848e274b198f3e03a1c072e44e/mu_sdk_trial.v3.proposed.py"
NEW = HERE / "mu_sdk_trial.v4.proposed.py"
old_tree, new_tree = ast.parse(OLD.read_text(encoding="utf-8")), ast.parse(NEW.read_text(encoding="utf-8"))
compile(new_tree, str(NEW), "exec", dont_inherit=True)
old_fns = {n.name: n for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_fns = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
assert set(new_fns) - set(old_fns) == {
    "consumed_file_state", "strict_consumed_json", "current_consumed_states",
    "after_child_consumed_states"}
unchanged = sorted(name for name in old_fns if name not in {
    "pin_path", "authorized_child", "validate_input", "consume_once", "command_once"})
assert all(ast.dump(old_fns[name], include_attributes=False) ==
           ast.dump(new_fns[name], include_attributes=False) for name in unchanged)

selected = ("require", "pin_file", "canonical_dir", "consumed_file_state",
            "strict_consumed_json", "current_consumed_states",
            "authorized_child", "after_child_consumed_states", "command_once", "pin_path")
module = ast.fix_missing_locations(ast.Module(body=[new_fns[name] for name in selected], type_ignores=[]))
ns = {
    "Path": Path, "os": os, "stat": stat, "hashlib": hashlib, "json": json,
    "time": time, "MAX_RAW_BYTES": 2 * 1024 * 1024,
    "PROVIDER": "opencode-go", "MODEL": "deepseek-v4.1-flash"}
exec(compile(module, str(NEW), "exec", dont_inherit=True), ns)

def reject(call, part):
    try:
        call()
    except (ValueError, OSError) as exc:
        assert part in str(exc), (part, str(exc))
    else:
        raise AssertionError("unexpected accept: " + part)

with tempfile.TemporaryDirectory(prefix="sdk-v4-pure-", dir=HERE) as tmp:
    root = Path(tmp).resolve(strict=True)
    exe = root / "researchos-cli.exe"
    exe.write_bytes(b"original CLI binary")
    binary_raw = exe.read_bytes()
    binary_ref = {"path": str(exe), "sha256": hashlib.sha256(binary_raw).hexdigest(),
                  "bytes": len(binary_raw)}
    discovery = root / "discovery.json"
    original_discovery = {"url": "http://127.0.0.1:18444", "pid": 123,
                          "data_dir": str(root), "host_instance_id": "host-123456abcdef"}
    discovery.write_bytes(json.dumps(original_discovery).encode())
    config = root / "v24_cli_config.json"
    dstate = ns["consumed_file_state"](str(discovery), root, "discovery")[0]
    absent = ns["consumed_file_state"](str(config), root, "CLI config")[0]
    assert dstate["exists"] and not absent["exists"]
    doc = {"phase": "bootstrap", "cli_binary": binary_ref, "data_root": str(root),
           "discovery_file": str(discovery), "cli_config_file": str(config),
           "initial_discovery_state": dstate, "initial_config_state": absent,
           "_expected_config_state": absent}
    frozen = {"child_argv": {"cli-init": ["cli", "init"], "cli-goal": ["cli", "goal"],
                             "cli-config": ["cli", "config"], "cli-run": ["cli", "run"]},
              "cwd": str(root), "child_environment": {"X": "1"}}
    doc["_sealed_phase_basis"] = frozen
    ns["phase_basis"] = lambda _doc, _mode: frozen
    ns["parse_pinned_json"] = lambda _ref, _label: frozen
    doc["input_basis_ref"] = {"opaque": True}
    args, env = ["cli", "init"], {"X": "1"}
    ns["authorized_child"](doc, "cli-init", args, root, env)
    exe.write_bytes(b"replacement CLI binary")
    reject(lambda: ns["authorized_child"](doc, "cli-init", args, root, env),
           "cli_binary before child pin changed")
    exe.write_bytes(binary_raw)
    discovery.write_bytes(json.dumps({**original_discovery, "url": "http://127.0.0.1:19999"}).encode())
    reject(lambda: ns["authorized_child"](doc, "cli-init", args, root, env),
           "DISCOVERY_CHANGED_BEFORE_CHILD")
    discovery.write_bytes(json.dumps(original_discovery).encode())
    ns["authorized_child"](doc, "cli-init", args, root, env)
    fresh = {"config_revision": 0, "model": "", "settled_run_id": "",
             "workspace_ref": "ws-123", "project_id": "prj-123", "session_id": "",
             "session_revision": 0, "writer_epoch": 0, "updated_by": ""}
    config.write_bytes((json.dumps(fresh) + "\n").encode())
    init_row = {"command": "init", "status": "COMPLETED", "exit_code": 0,
                "project_id": "prj-123", "workspace_ref": "ws-123"}
    transition = ns["after_child_consumed_states"](doc, "cli-init", [init_row])
    assert transition["config_before_state"] == absent
    ns["authorized_child"](doc, "cli-goal", ["cli", "goal"], root, env)
    config.write_bytes((json.dumps({**fresh, "writer_epoch": 99}) + "\n").encode())
    reject(lambda: ns["authorized_child"](doc, "cli-goal", ["cli", "goal"], root, env),
           "CONFIG_CHANGED_BEFORE_CHILD")
    config.write_bytes((json.dumps(fresh) + "\n").encode())
    doc["phase"] = "execute"
    doc["config_revision"] = 0
    doc["initial_config_state"] = doc["_expected_config_state"]
    ns["authorized_child"](doc, "cli-config", ["cli", "config"], root, env)
    altered = {**fresh, "config_revision": 1, "model": "opaque-model-config"}
    config.write_bytes((json.dumps(altered) + "\n").encode())
    config_row = {"command": "config", "status": "COMPLETED", "exit_code": 0,
                  "selected_model": "opencode-go/deepseek-v4.1-flash",
                  "method_sent": "host.configure", "previous_model": "",
                  "config_revision": 1, "model": "opaque-model-config"}
    ns["after_child_consumed_states"](doc, "cli-config", [config_row])
    ns["authorized_child"](doc, "cli-run", ["cli", "run"], root, env)
    doc["_expected_config_state"] = ns["consumed_file_state"](str(config), root, "CLI config")[0]
    doc["_pre_child_config_json"] = fresh
    config.write_bytes((json.dumps({**altered, "project_id": "wrong-project"}) + "\n").encode())
    reject(lambda: ns["after_child_consumed_states"](doc, "cli-config", [config_row]),
           "CLI_CONFIG_POSTIMAGE_NOT_DERIVED")
    reject(lambda: ns["consumed_file_state"](str(root.parent / "foreign.json"), root, "foreign"),
           "outside isolated root")

class Child:
    def poll(self):
        return 1
    def wait(self, timeout=None):
        return 1
    def kill(self):
        raise AssertionError("exited child should never be killed")

class FakeFile:
    def __init__(self, path, close_error):
        self.handle = path.open("xb")
        self.close_error = close_error
    def __enter__(self):
        return self.handle
    def __exit__(self, kind, value, traceback):
        self.handle.close()
        if self.close_error:
            raise OSError("late-close")

class FakePath:
    def __init__(self, path, close_error=False, hash_error=False):
        self.path, self.close_error, self.hash_error = path, close_error, hash_error
    def open(self, mode):
        assert mode == "xb"
        return FakeFile(self.path, self.close_error)
    def is_file(self):
        return self.path.is_file()
    def read_bytes(self):
        if self.hash_error:
            raise OSError("late-hash")
        return self.path.read_bytes()
    def stat(self):
        return self.path.stat()
    def __str__(self):
        return str(self.path)

class FakeDir:
    def __init__(self, path, close_error=False, hash_error=False):
        self.path, self.close_error, self.hash_error = path, close_error, hash_error
    def __truediv__(self, name):
        return FakePath(self.path / name, name.endswith(".stderr.raw") and self.close_error,
                        name.endswith(".stdout.raw") and self.hash_error)

def native_case(close_error=False, hash_error=False):
    with tempfile.TemporaryDirectory(prefix="sdk-v4-native-", dir=HERE) as tmp:
        started = []
        receipts = []
        ns["authorized_child"] = lambda *_: None
        ns["os_job_membership"] = lambda: None
        ns["subprocess"] = SimpleNamespace(
            DEVNULL=object(), Popen=lambda *a, **kw: (started.append(True) or Child()))
        ns["put_json"] = lambda path, value: receipts.append(value)
        ns["guard_deadline"] = lambda *_: None
        outdir = FakeDir(Path(tmp), close_error=close_error, hash_error=hash_error)
        reject(lambda: ns["command_once"]({}, ["cli"], Path(tmp), {}, outdir,
                                         "case", time.monotonic() + 5), "original raw/exit receipt")
        assert len(started) == 1 and len(receipts) == 1
        assert receipts[0]["actual_exit"] == 1
        assert receipts[0]["first_cause"] == "CHILD_NONZERO_EXIT:1"
        if close_error:
            assert any("stream_close:OSError:late-close" in x for x in
                       receipts[0]["secondary_failures"])
        if hash_error:
            assert any("stdout_ref:OSError:late-hash" in x for x in
                       receipts[0]["secondary_failures"])
        reject(lambda: ns["command_once"]({}, ["cli"], Path(tmp), {}, outdir,
                                         "late", time.monotonic() - 1),
               "absolute Root deadline lacks launch/evidence reserve")
        assert len(started) == 1

native_case(close_error=True)
native_case(hash_error=True)
result = {
    "schema": "researchos.mu-sdk-trial-v4-pure-precheck.v1",
    "source_ast_compile": True, "candidate_imported": False,
    "go_cli_sdk_provider_executions": 0, "actual_child_processes": 0,
    "positive": ["original binary and discovery accepted", "CLI init absent-to-exact-config",
                 "CLI config exact revision/model postimage", "next child accepted"],
    "negative": ["same-path executable swap", "discovery URL swap", "config writer swap",
                 "foreign path", "unapproved config postimage",
                 "native1 then stream-close error preserves native first",
                 "native1 then raw-hash error preserves native first",
                 "expired deadline starts zero child"],
    "actual_root_authority": None, "source_acceptance": False,
    "formal_case_accepted_delta": 0
}
with (HERE / "precheck.v4.json").open("xb") as out:
    out.write((json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode())
print(json.dumps(result, ensure_ascii=False))
