"""Root-only migration controller. Importing starts no child and opens no key.

Root supplies exact public pins. Signing is an explicit API, with the issuer
DPAPI path supplied only as a runtime argument; it is never saved or printed.
"""
import ctypes
from ctypes import wintypes
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import sys
import threading
import time
import uuid

CASES = {
    "positive-replay", "missing-native-channel", "wrong-purpose",
    "mismatched-database", "release-pin-mismatch", "expired-grant",
    "missing-dynamic-pin", "wrong-owner", "lease-occupied",
}
ENV_KEYS = {
    "SystemRoot", "WINDIR", "ComSpec", "PATH", "PATHEXT", "USERPROFILE",
    "LOCALAPPDATA", "APPDATA", "TEMP", "TMP", "GOROOT", "GOPATH",
    "GOCACHE", "GOTOOLCHAIN", "GOPROXY", "GOSUMDB", "GOWORK",
    "CGO_ENABLED", "GOFLAGS", "GOMAXPROCS", "RESEARCHOS_GO",
    "RESEARCHOS_CONFIGURATION_OLD_CONTROL", "RESEARCHOS_CONFIGURATION_TARGET_PROGRAM",
    "RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL", "RESEARCHOS_CONFIGURATION_OLD_ROOT",
    "RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER",
    "RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_SHA256",
    "RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_ROOT", "RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE",
}
PHASES = {
    "release": ("01-release.payload.json", "01-release.ready.json", "01-release.approval.json",
                "recovery-release.json", "release-signed"),
    "grant": ("02-grant.payload.json", "02-grant.ready.json", "02-grant.approval.json",
              "current-schema23-to24-grant.json", "grant-signed-and-invoke"),
}

def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result

def decode(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)

def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def canonical_path(value):
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError("absolute public path required")
    path = Path(value)
    if not path.is_absolute() or str(path.resolve()).casefold() != str(path).casefold():
        raise ValueError("canonical public path required")
    return path

def public_ref(path):
    path = canonical_path(str(path))
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}

def path_key(value):
    return str(canonical_path(value)).casefold()

def require_ref(value):
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "bytes"}:
        raise ValueError("exact public reference shape required")
    if isinstance(value["bytes"], bool) or not isinstance(value["bytes"], int) or value["bytes"] < 0:
        raise ValueError("public reference length")
    path = canonical_path(value["path"])
    actual = public_ref(path)
    if (path_key(actual["path"]) != path_key(value["path"]) or
        actual["sha256"] != value["sha256"] or actual["bytes"] != value["bytes"]):
        raise ValueError("public reference changed")
    return path

def from_raw_pin(value):
    if not isinstance(value, dict) or set(value) != {"role", "path", "sha256", "bytes"}:
        raise ValueError("public RawPin shape required")
    return {key: value[key] for key in ("path", "sha256", "bytes")}

def read_ref(value):
    path = require_ref(value)
    raw = path.read_bytes()
    if digest(raw) != value["sha256"] or len(raw) != value["bytes"]:
        raise ValueError("public read changed")
    return raw

def write_new(path, value):
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return public_ref(path)

def load_public_module(pin, label):
    raw = read_ref(pin)
    name = "researchos_root_" + label + "_" + pin["sha256"][7:23]
    module = type(sys)(name)
    module.__file__ = pin["path"]
    sys.modules[name] = module
    exec(compile(raw, pin["path"], "exec", dont_inherit=True), module.__dict__)
    return module

def _plain_guard_refs(refs):
    result = []
    for value in refs:
        if (not isinstance(value,dict) or set(value)!={"path","sha256","bytes"} or
            not isinstance(value["sha256"],str) or not value["sha256"].startswith("sha256:")):
            raise ValueError("guard public reference shape")
        canonical_path(value["path"])
        result.append({"path": value["path"], "sha256": value["sha256"].removeprefix("sha256:"),
                       "bytes": value["bytes"]})
    return result

def _guard(context, refs):
    guard = context["guard_module"].SourceReadGuard(
        per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    guard.acquire(_plain_guard_refs(refs))
    return guard

def context(config_ref):
    raw = read_ref(config_ref)
    cfg = decode(raw)
    expected = {"Schema", "ControllerDirectory", "ControllerSource", "HarnessConfig",
                "TestProgram", "ObservedOwnedHelper", "OriginalOwnedHelper", "SourceReadGuard",
                "CompilerInventory", "BuildInvocation", "FrozenInputs", "Environment"}
    if set(cfg) != expected or cfg["Schema"] != "researchos.root-native-migration-controller.v1":
        raise ValueError("controller public configuration shape")
    for key in ("ControllerSource", "HarnessConfig", "TestProgram", "ObservedOwnedHelper",
                "OriginalOwnedHelper", "SourceReadGuard", "CompilerInventory", "BuildInvocation"):
        require_ref(cfg[key])
    if Path(cfg["ControllerSource"]["path"]).resolve() != Path(__file__).resolve():
        raise ValueError("controller Source identity")
    if not isinstance(cfg["FrozenInputs"], list) or not cfg["FrozenInputs"]:
        raise ValueError("frozen public input inventory required")
    # The persistent server verifies this whole inventory once on retained
    # handles. Polling does not re-read all compiler input contents.
    _plain_guard_refs(cfg["FrozenInputs"])
    frozen = {path_key(value["path"]): value for value in cfg["FrozenInputs"]}
    if len(frozen)!=len(cfg["FrozenInputs"]):
        raise ValueError("duplicate frozen public input path")
    for key in ("ControllerSource", "HarnessConfig", "TestProgram", "ObservedOwnedHelper",
                "OriginalOwnedHelper", "SourceReadGuard", "CompilerInventory", "BuildInvocation"):
        if frozen.get(path_key(cfg[key]["path"])) != cfg[key]:
            raise ValueError("required controller input absent from frozen inventory")
    hc = decode(read_ref(cfg["HarnessConfig"]))
    if hc["Schema"] != "researchos.synthetic-native-migration-config.v1" or hc["Case"] not in CASES:
        raise ValueError("migration harness case")
    for key in ("RootProgram", "ControlProgram", "BackupProgram", "EnrollmentProgram",
                "PythonProgram", "BrokerSource", "PrivateStdinHelper"):
        ref = from_raw_pin(hc[key])
        require_ref(ref)
        if frozen.get(path_key(ref["path"])) != ref:
            raise ValueError("harness program/source absent from frozen inventory")
    if Path(hc["PythonProgram"]["path"]).resolve() != Path(sys.executable).resolve():
        raise ValueError("actual Python runtime differs")
    work = canonical_path(cfg["ControllerDirectory"])
    output = canonical_path(hc["OutputDirectory"])
    build = canonical_path(hc["BuildRoot"])
    build_invocation = decode(read_ref(cfg["BuildInvocation"]))
    build_argv = build_invocation["argv"]
    if (build_argv.count("-o") != 1 or "-c" not in build_argv or
        "-tags=researchos_native_recovery_harness" not in build_argv or
        path_key(build_argv[build_argv.index("-o")+1]) != path_key(cfg["TestProgram"]["path"]) or
        path_key(build_invocation["cwd"]) != path_key(str(build)) or
        build_invocation.get("actual_native_exit") != 0 or
        not _closed_native(build_invocation["result"])):
        raise ValueError("actual test compilation provenance differs")
    inventory = decode(read_ref(cfg["CompilerInventory"]))
    if (inventory["build_tag"] != "researchos_native_recovery_harness" or
        inventory["includes_actual_test_and_embed_inputs"] is not True):
        raise ValueError("tagged compiler inventory required")
    for item in inventory["build_inputs"] + inventory["product_inventory"]:
        expected = {"path":item["path"],"sha256":"sha256:"+item["sha256"].removeprefix("sha256:"),"bytes":item["bytes"]}
        if frozen.get(path_key(expected["path"])) != expected:
            raise ValueError("selected compiler/product input absent from frozen inventory")
    if work == output or work in output.parents or output in work.parents:
        raise ValueError("controller and harness outputs must be disjoint")
    env = cfg["Environment"]
    if not isinstance(env, dict) or not set(env).issubset(ENV_KEYS):
        raise ValueError("environment must contain only reviewed public keys")
    if any(not isinstance(v, str) or "\0" in v for v in env.values()):
        raise ValueError("public environment values")
    if not {"SystemRoot", "WINDIR", "TEMP", "TMP"}.issubset(env):
        raise ValueError("public Windows/temp environment required")
    for prefix in ("RootProgram", "ControlProgram"):
        if not Path(hc[prefix]["path"]).is_file():
            raise ValueError("case program missing")
    if Path(hc["RootProgram"]["path"]).parent != Path(hc["ControlProgram"]["path"]).parent:
        raise ValueError("case programs must share fresh fixed-file namespace")
    guard_module = load_public_module(cfg["SourceReadGuard"], "guard")
    observed = load_public_module(cfg["ObservedOwnedHelper"], "observed_owned")
    original = load_public_module(cfg["OriginalOwnedHelper"], "original_owned")
    # Inventory the modules actually loaded by this fresh Python controller.
    for path in original.runtime_resource_paths():
        if path_key(path) not in frozen:
            raise ValueError("loaded runtime module absent from Root frozen inventory")
    return {"config_ref":config_ref, "cfg":cfg, "hc":hc, "work":work, "output":output,
            "build":build, "guard_module":guard_module, "observed":observed, "original":original}

def _phase(c):
    out = c["output"]
    if (out/"06-fixture-retained.ready.json").is_file():
        return "fixture-retained"
    if (out/PHASES["grant"][1]).is_file() and not (out/PHASES["grant"][2]).exists():
        return "grant"
    if (out/PHASES["release"][1]).is_file() and not (out/PHASES["release"][2]).exists():
        return "release"
    return "running"

def _closed_native(result):
    job = result["job_cleanup"]
    return (result["actual_exit"] is not None and job["assigned_before_resume"]
            and job["unnamed_exclusive_job"] and job["kill_on_job_close_configured"]
            and job["primary_exit_confirmed"] and job["job_idle_confirmed"]
            and job["active_processes_last_observed"] == 0
            and job["handles_closed"] and not job["errors"])

def serve(config_ref):
    """Blocking Root-owned lifetime. No approvals or signing are generated."""
    c = context(config_ref)
    if c["work"].exists() or c["output"].exists():
        raise ValueError("fresh controller and harness output paths required")
    root_dir = Path(c["hc"]["RootProgram"]["path"]).parent
    if any((root_dir/name).exists() for name in
           ("recovery-release.json", "current-schema23-to24-grant.json", "consumed-schema23-to24-grants")):
        raise ValueError("fresh case fixed-file namespace required")
    c["work"].mkdir(parents=False)
    source_guard = None
    cancellation = threading.Event()
    requests = queue.Queue()
    result_holder = {}
    binding_id = uuid.uuid4().hex
    owner_pid = os.getpid()
    thread = None
    source_cleanup = None
    error_type = None
    try:
        source_guard = _guard(c, [config_ref] + c["cfg"]["FrozenInputs"])
        started_ref = write_new(c["work"]/"controller.started.json", {
            "schema":"researchos.root-native-controller-started.v1", "config_ref":config_ref,
            "case":c["hc"]["Case"], "case_id":c["hc"]["CaseID"], "owner_pid":owner_pid,
            "job_binding_id":binding_id, "case_deadline_seconds":1260,
            "controller_does_not_approve":True})
        def observed(event, observed_result):
            proof = {"schema":"researchos.root-held-test-job-observation.v1", "event":event,
                     "config_ref":config_ref, "job_binding_id":binding_id, "owner_pid":owner_pid,
                     "held_job_handle":True, "held_primary_handle":True,
                     "observed_monotonic":time.monotonic(), "result":observed_result}
            if event in ("assigned-before-resume", "resumed"):
                write_new(c["work"]/("test."+event+".json"), proof)
            if event == "live":
                while True:
                    try:
                        request_id = requests.get_nowait()
                    except queue.Empty:
                        break
                    response = dict(proof)
                    response["request_id"] = request_id
                    response["phase"] = _phase(c)
                    write_new(c["work"]/("observe-"+request_id+".response.json"), response)
        def worker():
            try:
                env = dict(c["cfg"]["Environment"])
                env["RESEARCHOS_NATIVE_MIGRATION_HARNESS_CONFIG"] = c["cfg"]["HarnessConfig"]["path"]
                argv = [c["cfg"]["TestProgram"]["path"],
                        "-test.run=^TestNativeMigrationAuthorityHarness$", "-test.count=1", "-test.timeout=25m"]
                with (c["work"]/"test.stdout.raw").open("xb") as stdout, (c["work"]/"test.stderr.raw").open("xb") as stderr:
                    result = c["observed"].run_owned_observed(
                        argv, str(c["build"]/"internal/domain"), env, stdout, stderr, 1260,
                        creation_flags=0x08000000, on_observation=observed,
                        cancel_requested=cancellation.is_set)
                result_holder["result"] = result
                result_holder["invocation_ref"] = write_new(c["work"]/"test.invocation.json", {
                    "schema":"researchos.root-native-harness-invocation.v1",
                    "config_ref":config_ref, "job_binding_id":binding_id, "argv":argv,
                    "cwd":str(c["build"]/"internal/domain"), "public_environment":env,
                    "result":result, "stdout_ref":public_ref(c["work"]/"test.stdout.raw"),
                    "stderr_ref":public_ref(c["work"]/"test.stderr.raw"),
                    "same_owned_job_for_all_harness_pauses":True})
            except BaseException as exc:
                result_holder["worker_error_type"] = type(exc).__name__
        thread = threading.Thread(target=worker, name="root-owned-native-harness", daemon=False)
        thread.start()
        seen = set()
        deadline = time.monotonic() + 1270
        while thread.is_alive():
            stop = c["work"]/"stop.request.json"
            if stop.is_file():
                value = decode(stop.read_bytes())
                if value == {"Action":"STOP_OWNED_CASE", "ConfigSHA256":config_ref["sha256"]}:
                    cancellation.set()
            for path in c["work"].glob("observe-*.request.json"):
                request_id = path.name.removeprefix("observe-").removesuffix(".request.json")
                if path.name in seen or len(request_id) != 32 or any(x not in "0123456789abcdef" for x in request_id):
                    continue
                value = decode(path.read_bytes())
                if value != {"Action":"OBSERVE_HELD_JOB", "ConfigSHA256":config_ref["sha256"], "RequestID":request_id}:
                    raise ValueError("public observation request differs")
                seen.add(path.name)
                requests.put(request_id)
            if time.monotonic() >= deadline:
                cancellation.set()
            time.sleep(0.1)
    except BaseException as exc:
        error_type = type(exc).__name__
    finally:
        if thread is not None and thread.is_alive():
            cancellation.set()
            thread.join(timeout=12)
        alive = thread is not None and thread.is_alive()
        # Do not release source handles while an unconfirmed child may use them.
        if source_guard is not None and not alive:
            source_cleanup = source_guard.close()
        result = result_holder.get("result")
        closed = (not alive and result is not None and _closed_native(result)
                  and source_cleanup is not None and source_cleanup["closed"]
                  and not source_cleanup["errors"])
        successful = (closed and result["actual_exit"] == 0 and result["error"] is None
                      and not result["timed_out"] and error_type is None
                      and "worker_error_type" not in result_holder)
        closed_ref = write_new(c["work"]/"controller.closed.json", {
            "schema":"researchos.root-native-controller-closed.v1", "config_ref":config_ref,
            "case":c["hc"]["Case"], "case_id":c["hc"]["CaseID"], "job_binding_id":binding_id,
            "job_and_guards_closed":closed, "harness_test_exit_zero":successful,
            "native_acceptance":"PENDING_ROOT_INDEPENDENT_REVIEW",
            "worker_still_alive":alive, "error_type":error_type,
            "worker_error_type":result_holder.get("worker_error_type"),
            "invocation_ref":result_holder.get("invocation_ref"), "source_guard_cleanup":source_cleanup,
            "fixture_release_approval_exists":(c["output"]/"06-release-fixture.approval.json").is_file()})
    return closed_ref

def poll(config_ref, timeout=5.0):
    """Ask the live helper to observe its own held process/Job handles."""
    c = context(config_ref)
    if (c["work"]/"controller.closed.json").is_file():
        return public_ref(c["work"]/"controller.closed.json")
    if not (c["work"]/"controller.started.json").is_file():
        raise ValueError("controller not started")
    request_id = uuid.uuid4().hex
    write_new(c["work"]/("observe-"+request_id+".request.json"), {
        "Action":"OBSERVE_HELD_JOB", "ConfigSHA256":config_ref["sha256"], "RequestID":request_id})
    end = time.monotonic() + min(max(float(timeout), 0.1), 10.0)
    target = c["work"]/("observe-"+request_id+".response.json")
    while time.monotonic() < end:
        if target.is_file():
            raw = target.read_bytes()
            try:
                decode(raw)
            except (ValueError, UnicodeError):
                time.sleep(0.05)
                continue
            return public_ref(target)
        if (c["work"]/"controller.closed.json").is_file():
            return public_ref(c["work"]/"controller.closed.json")
        time.sleep(0.05)
    raise TimeoutError("owned Job observation not received")

def stop(config_ref):
    c = context(config_ref)
    return write_new(c["work"]/"stop.request.json", {
        "Action":"STOP_OWNED_CASE", "ConfigSHA256":config_ref["sha256"]})

def _live_observation(config_ref):
    proof_ref = poll(config_ref)
    proof = decode(read_ref(proof_ref))
    if proof.get("schema") != "researchos.root-held-test-job-observation.v1":
        raise ValueError("owned test process is already closed")
    result = proof["result"]
    if (not result["resumed"] or result["actual_exit"] is not None or
        not result["job_cleanup"]["assigned_before_resume"] or
        result["job_cleanup"]["active_processes_last_observed"] < 1):
        raise ValueError("no current held live test Job")
    return proof_ref, proof

def native_file_id(path, directory):
    """Read an actual Windows file identity without SQL or changing contents."""
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    class INFO(ctypes.Structure):
        _fields_ = [("attributes",wintypes.DWORD),("creation",wintypes.FILETIME),
                    ("access",wintypes.FILETIME),("write",wintypes.FILETIME),
                    ("volume",wintypes.DWORD),("size_high",wintypes.DWORD),
                    ("size_low",wintypes.DWORD),("links",wintypes.DWORD),
                    ("index_high",wintypes.DWORD),("index_low",wintypes.DWORD)]
    api.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,
                               wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE,ctypes.POINTER(INFO)]
    api.GetFileInformationByHandle.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    flags = 0x00200000 | (0x02000000 if directory else 0)
    handle = api.CreateFileW(str(canonical_path(str(path))),0x80,3,None,3,flags,None)
    if handle in (None,ctypes.c_void_p(-1).value):
        raise OSError("native identity open failed")
    try:
        info = INFO()
        if not api.GetFileInformationByHandle(handle,ctypes.byref(info)):
            raise OSError("native identity observation failed")
        if bool(info.attributes & 0x10) != directory:
            raise ValueError("native identity file kind")
        return "%08x:%08x:%08x" % (info.volume,info.index_high,info.index_low)
    finally:
        if not api.CloseHandle(handle):
            raise OSError("native identity handle close failed")

def _walk_pins(value):
    if isinstance(value, dict):
        if set(value) == {"role","path","sha256","bytes"}:
            yield value
        else:
            for child in value.values():
                yield from _walk_pins(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_pins(child)

def snapshot(config_ref):
    """Create a public review artifact. It is never an approval."""
    c = context(config_ref)
    observed_ref, observed = _live_observation(config_ref)
    phase = _phase(c)
    if phase not in ("release","grant","fixture-retained"):
        raise ValueError("no concrete review pause")
    files = ["before.rows.json","fixture.public.json","rehearsal.public.json"]
    if phase == "fixture-retained":
        files += ["06-fixture-retained.ready.json"]
        for optional in ("after.rows.json","05-case.result.json","03-live-lease.public.json",
                         "03-live-lease.closed.json"):
            if (c["output"]/optional).is_file():
                files.append(optional)
    else:
        files += list(PHASES[phase][:2])
    refs = [public_ref(c["output"]/name) for name in files if (c["output"]/name).is_file()]
    fixture_path = c["output"]/"fixture.public.json"
    if fixture_path.is_file():
        fixture = decode(fixture_path.read_bytes())
    elif phase == "fixture-retained":
        # Early fixture assertions may fail before the normal public summary.
        # The Go cleanup hold still publishes the actual database path.
        fixture_path = c["output"]/"06-fixture-retained.ready.json"
        retained = decode(fixture_path.read_bytes())
        fixture = {"database":retained["database"],"root":str(Path(retained["database"]).parent)}
    else:
        raise ValueError("fixture public identity required")
    measured = {"root":native_file_id(fixture["root"],True),
                "database":native_file_id(fixture["database"],False)}
    declared = []
    payload_ref = None
    ready_ref = None
    sign_kind = None
    target = None
    if phase in PHASES:
        payload_ref = public_ref(c["output"]/PHASES[phase][0])
        ready_ref = public_ref(c["output"]/PHASES[phase][1])
        payload = decode(read_ref(payload_ref))
        ready = decode(read_ref(ready_ref))
        sign_kind = "release" if phase == "release" else ("grant" if c["hc"]["Case"] == "wrong-purpose" else "migration-grant")
        target = str(Path(c["hc"]["RootProgram"]["path"]).parent/PHASES[phase][3])
        if ready["payload_sha256"] != payload_ref["sha256"] or ready["sign_kind"] != sign_kind or Path(ready["fixed_signed_path"]) != Path(target):
            raise ValueError("phase readiness differs from concrete payload")
        for pin in _walk_pins(payload):
            actual = public_ref(pin["path"])
            declared.append({"declared":pin,"actual":actual,
                             "matches":actual == from_raw_pin(pin)})
            refs.append(actual)
    unique = {r["path"].casefold():r for r in refs}
    evidence = list(unique.values())
    phase_guard = _guard(c, evidence + [observed_ref])
    try:
        if _phase(c) != phase:
            raise ValueError("review phase moved")
        snap = {"schema":"researchos.root-native-review-snapshot.v1",
                "config_ref":config_ref, "harness_config_ref":c["cfg"]["HarnessConfig"],
                "case":c["hc"]["Case"], "case_id":c["hc"]["CaseID"], "phase":phase,
                "observation_ref":observed_ref, "job_binding_id":observed["job_binding_id"],
                "payload_ref":payload_ref, "ready_ref":ready_ref, "sign_kind":sign_kind,
                "signed_destination":target, "evidence_refs":evidence,
                "declared_pin_observations":declared, "measured_native_ids":measured,
                "fixture_public_ref":public_ref(fixture_path),
                "compiler_inventory_ref":c["cfg"]["CompilerInventory"],
                "test_build_invocation_ref":c["cfg"]["BuildInvocation"],
                "root_approval":False,"sql_read_performed_by_controller":False,
                "created_utc":dt.datetime.now(dt.timezone.utc).isoformat()}
    finally:
        cleanup = phase_guard.close()
    if not cleanup["closed"] or cleanup["errors"]:
        raise RuntimeError("review snapshot guard did not close")
    snap["snapshot_guard_cleanup"] = cleanup
    return write_new(c["work"]/("review-snapshot-"+phase+"-"+uuid.uuid4().hex+".json"),snap)

def _approval(config_ref, approval_ref, action):
    c = context(config_ref)
    approval = decode(read_ref(approval_ref))
    required = {"Schema","Action","ConfigSHA256","Snapshot","Payload","SignedDestination","SignKind"}
    if action == "PUBLISH_REVIEWED_SIGNED_DOCUMENT":
        required |= {"SignedDocument","SigningReceipt"}
    if set(approval) != required or approval["Schema"] != "researchos.root-native-concrete-approval.v1" or approval["Action"] != action:
        raise ValueError("concrete Root approval shape/action")
    if approval["ConfigSHA256"] != config_ref["sha256"]:
        raise ValueError("Root approval config mismatch")
    snap = decode(read_ref(approval["Snapshot"]))
    phase = snap["phase"]
    if phase not in PHASES or snap["config_ref"] != config_ref or _phase(c) != phase:
        raise ValueError("Root approval wrong current phase")
    expected_kind = "release" if phase == "release" else ("grant" if c["hc"]["Case"] == "wrong-purpose" else "migration-grant")
    expected_destination = Path(c["hc"]["RootProgram"]["path"]).parent/PHASES[phase][3]
    if (snap["case"] != c["hc"]["Case"] or snap["case_id"] != c["hc"]["CaseID"] or
        approval["SignKind"] != expected_kind or Path(approval["SignedDestination"]) != expected_destination or
        snap["harness_config_ref"] != c["cfg"]["HarnessConfig"] or
        snap["ready_ref"] != public_ref(c["output"]/PHASES[phase][1])):
        raise ValueError("Root approval differs from fixed case contract")
    if (approval["Payload"] != snap["payload_ref"] or
        approval["SignedDestination"] != snap["signed_destination"] or
        approval["SignKind"] != snap["sign_kind"]):
        raise ValueError("Root approval differs from exact reviewed snapshot")
    current_payload = public_ref(c["output"]/PHASES[phase][0])
    if current_payload != approval["Payload"]:
        raise ValueError("Root approved payload changed")
    _, observation = _live_observation(config_ref)
    if observation["job_binding_id"] != snap["job_binding_id"]:
        raise ValueError("owned Job changed across review pause")
    fixture = decode(read_ref(snap["fixture_public_ref"]))
    if snap["measured_native_ids"] != {"root":native_file_id(fixture["root"],True),
                                       "database":native_file_id(fixture["database"],False)}:
        raise ValueError("fixture native identities changed since review")
    payload = decode(read_ref(approval["Payload"]))
    if phase == "grant":
        issued = dt.datetime.fromisoformat(payload["issued_utc"].replace("Z","+00:00"))
        expires = dt.datetime.fromisoformat(payload["expires_utc"].replace("Z","+00:00"))
        now = dt.datetime.now(dt.timezone.utc)
        if issued.tzinfo is None or expires.tzinfo is None or not 0 < (expires-issued).total_seconds() <= 240:
            raise ValueError("grant absolute interval exceeds four minutes")
        if c["hc"]["Case"] == "expired-grant":
            if not expires < now:
                raise ValueError("expired negative no longer describes an expired grant")
        elif not issued <= now < expires:
            raise ValueError("grant absolute validity elapsed; no extension or retry")
    return c, approval, snap, phase

def _signed_payload_exact(signed_raw, payload_raw):
    value = decode(signed_raw)
    if set(value) != {"payload","signature"} or not isinstance(value["signature"],str) or not value["signature"]:
        raise ValueError("signed document wrapper")
    # Production encoded(signedDocument) writes payload first without whitespace.
    prefix = '{"payload":'
    text = signed_raw.decode("utf-8")
    if not text.startswith(prefix):
        raise ValueError("production signed wrapper serialization changed")
    decoder = json.JSONDecoder(object_pairs_hook=_pairs)
    _, end = decoder.raw_decode(text,len(prefix))
    if text[len(prefix):end].encode("utf-8") != payload_raw:
        raise ValueError("signed payload bytes differ")
    return True

def sign_reviewed(config_ref, approval_ref, issuer_dpapi_path_runtime):
    """Root only. Never read/store/print issuer path; pass it to genuine CLI."""
    c, approval, snap, phase = _approval(config_ref,approval_ref,"SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD")
    if not isinstance(issuer_dpapi_path_runtime,str) or not issuer_dpapi_path_runtime or "\0" in issuer_dpapi_path_runtime:
        raise ValueError("runtime issuer argument required")
    destination = Path(approval["SignedDestination"])
    if destination.exists():
        raise ValueError("signed output already exists; no retry/overwrite")
    guard = _guard(c, [config_ref,approval_ref,approval["Snapshot"],
                      from_raw_pin(c["hc"]["EnrollmentProgram"]),c["cfg"]["OriginalOwnedHelper"],
                      c["cfg"]["SourceReadGuard"],c["cfg"]["ControllerSource"]]+snap["evidence_refs"])
    receipt_path = c["work"]/("sign-"+phase+".receipt.json")
    result = None
    signed_ref = None
    error_type = None
    cleanup = None
    try:
        # This consumes exactly one concrete approval. A failed attempt remains
        # consumed; Root must inspect it rather than silently repeat signing.
        write_new(c["work"]/("sign-"+phase+".consumed.json"),{"approval_ref":approval_ref,
                   "payload_ref":approval["Payload"],"one_attempt":True})
        argv = [c["hc"]["EnrollmentProgram"]["path"],"sign-reviewed",approval["SignKind"],
                issuer_dpapi_path_runtime,approval["Payload"]["path"],str(destination)]
        with open(os.devnull,"wb") as stdout, open(os.devnull,"wb") as stderr:
            result = c["original"].run_owned(argv,str(c["build"]),
                       {"SystemRoot":c["cfg"]["Environment"]["SystemRoot"],
                        "WINDIR":c["cfg"]["Environment"]["WINDIR"]},
                       stdout,stderr,30,creation_flags=0x08000000)
        argv[3] = ""
        issuer_dpapi_path_runtime = ""
        if not _closed_native(result) or result["actual_exit"] != 0 or result["error"] is not None or result["timed_out"]:
            raise RuntimeError("reviewed signer failed or did not close")
        signed_raw = destination.read_bytes()
        _signed_payload_exact(signed_raw,read_ref(approval["Payload"]))
        signed_ref = public_ref(destination)
    except BaseException as exc:
        error_type = type(exc).__name__
    finally:
        issuer_dpapi_path_runtime = ""
        cleanup = guard.close()
    success = signed_ref is not None and error_type is None and cleanup["closed"] and not cleanup["errors"]
    receipt = write_new(receipt_path,{"schema":"researchos.root-review-signing-receipt.v1",
          "config_ref":config_ref,"approval_ref":approval_ref,"payload_ref":approval["Payload"],
          "phase":phase,"sign_kind":approval["SignKind"],"signed_ref":signed_ref,
          "result":result,"source_guard_cleanup":cleanup,"success":success,"error_type":error_type,
          "private_path_recorded":False,"private_key_read_by_controller":False,
          "signer_stdout_stderr":"NUL_DISCARDED_TO_PREVENT_PRIVATE_PATH_ERROR_DISCLOSURE",
          "harness_approval_published":False})
    if not success:
        raise RuntimeError("signing attempt not accepted; inspect public signing receipt")
    return receipt

def publish_signed(config_ref, approval_ref):
    """Separate Root decision after inspecting actual signed bytes/receipt."""
    c, approval, snap, phase = _approval(config_ref,approval_ref,"PUBLISH_REVIEWED_SIGNED_DOCUMENT")
    signed_raw = read_ref(approval["SignedDocument"])
    receipt = decode(read_ref(approval["SigningReceipt"]))
    if (receipt["config_ref"] != config_ref or not receipt["success"] or
        receipt["signed_ref"] != approval["SignedDocument"] or receipt["payload_ref"] != approval["Payload"]):
        raise ValueError("reviewed signing receipt does not bind signed document")
    if Path(approval["SignedDocument"]["path"]) != Path(approval["SignedDestination"]):
        raise ValueError("signed document path differs")
    _signed_payload_exact(signed_raw,read_ref(approval["Payload"]))
    guard = _guard(c,[config_ref,approval_ref,approval["Snapshot"],approval["SignedDocument"],
                      approval["SigningReceipt"]]+snap["evidence_refs"])
    try:
        target = c["output"]/PHASES[phase][2]
        published = write_new(target,{"Action":PHASES[phase][4],
                       "PayloadSHA256":approval["Payload"]["sha256"],
                       "SignedSHA256":approval["SignedDocument"]["sha256"]})
    finally:
        cleanup = guard.close()
    write_new(c["work"]/("publish-"+phase+".receipt.json"),{
        "approval_ref":approval_ref,"published_ref":published,"source_guard_cleanup":cleanup})
    if not cleanup["closed"] or cleanup["errors"]:
        raise RuntimeError("publish guard close incomplete")
    return published

def release_fixture(config_ref, approval_ref):
    """Requires Root's independent inspection artifact before final cleanup."""
    c = context(config_ref)
    approval = decode(read_ref(approval_ref))
    if set(approval) != {"Schema","Action","ConfigSHA256","Snapshot","InspectionReceipt"} or \
       approval["Schema"] != "researchos.root-native-fixture-release.v1" or \
       approval["Action"] != "RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION" or \
       approval["ConfigSHA256"] != config_ref["sha256"]:
        raise ValueError("Root fixture release approval shape")
    snap = decode(read_ref(approval["Snapshot"]))
    inspection = decode(read_ref(approval["InspectionReceipt"]))
    if (snap["config_ref"] != config_ref or snap["phase"] != "fixture-retained" or
        _phase(c) != "fixture-retained" or inspection.get("config_ref") != config_ref or
        inspection.get("snapshot_ref") != approval["Snapshot"] or
        inspection.get("fixture_read_complete") is not True or
        inspection.get("whole_row_schema_review_complete") is not True or
        inspection.get("private_credentials_recorded") is not False):
        raise ValueError("independent fixture inspection not complete")
    _, observation = _live_observation(config_ref)
    if observation["job_binding_id"] != snap["job_binding_id"]:
        raise ValueError("held fixture Job differs")
    guard = _guard(c,[config_ref,approval_ref,approval["Snapshot"],approval["InspectionReceipt"]]+snap["evidence_refs"])
    try:
        published = write_new(c["output"]/"06-release-fixture.approval.json",{"Action":"release-fixture"})
    finally:
        cleanup = guard.close()
    write_new(c["work"]/"fixture-release.receipt.json",{
        "approval_ref":approval_ref,"inspection_ref":approval["InspectionReceipt"],
        "published_ref":published,"source_guard_cleanup":cleanup})
    if not cleanup["closed"] or cleanup["errors"]:
        raise RuntimeError("release guard close incomplete")
    return published

def main():
    # Public-only CLI. Private signing is intentionally an API-only operation.
    try:
        if len(sys.argv) != 5 or sys.argv[1] not in {"serve","poll","snapshot","stop"}:
            raise ValueError("public controller CLI arguments")
        action,path,sha = sys.argv[1:4]
        size = int(sys.argv[4])
        config_ref={"path":path,"sha256":sha,"bytes":size}
        result={"serve":serve,"poll":poll,"snapshot":snapshot,"stop":stop}[action](config_ref)
        print(json.dumps({"public_ref":result},ensure_ascii=True),flush=True)
        if action == "serve":
            closed = decode(read_ref(result))
            if not closed["job_and_guards_closed"] or not closed["harness_test_exit_zero"]:
                return 1
        return 0
    except BaseException as exc:
        # Do not echo exception text or argv from any Root runtime.
        print(json.dumps({"error_type":type(exc).__name__,"operation_failed":True}),file=sys.stderr,flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

