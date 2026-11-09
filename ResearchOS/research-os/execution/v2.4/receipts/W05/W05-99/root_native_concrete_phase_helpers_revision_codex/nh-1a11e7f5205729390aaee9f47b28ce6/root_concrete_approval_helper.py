"""Root caller only: one explicit request -> one concrete approval.
Imports and helper calls never sign, publish to harness, poll, launch children,
read private keys, execute SQL, refresh TTL, or advance another phase.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import re
import types
from datetime import datetime, timezone
from pathlib import Path

GUARD_SHA = "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
PHASES = {
    "release": ("01-release.payload.json", "01-release.ready.json", "01-release.approval.json", "recovery-release.json", "release"),
    "grant": ("02-grant.payload.json", "02-grant.ready.json", "02-grant.approval.json", "current-schema23-to24-grant.json", "migration-grant"),
}
JOB_FLAGS = ("unnamed_exclusive_job", "kill_on_job_close_configured", "assigned_before_resume",
             "primary_exit_confirmed", "job_idle_confirmed", "handles_closed")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate JSON member")
        out[key] = value
    return out

def decode(raw):
    def invalid(value):
        raise ValueError("non-finite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)

def exact(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b

def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def canonical(value):
    require(type(value) is str and value and "\0" not in value, "public absolute path")
    p = Path(value)
    require(p.is_absolute() and str(p.resolve()).casefold() == str(p).casefold(), "canonical path")
    require(not p.is_symlink(), "symlink forbidden")
    return p

def plain(ref):
    require(type(ref) is dict and set(ref) in ({"path", "sha256", "bytes"}, {"role", "path", "sha256", "bytes"}), "exact pin shape")
    require(type(ref["bytes"]) is int and ref["bytes"] >= 0, "exact integer pin length")
    require(type(ref["sha256"]) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", ref["sha256"]), "SHA256 pin")
    canonical(ref["path"])
    return {k: ref[k] for k in ("path", "sha256", "bytes")}

class Inputs:
    def __init__(self):
        self.refs = {}
        self.buffers = {}

    def read(self, ref):
        ref = plain(ref)
        name = Path(ref["path"]).name.casefold()
        require(not (".private." in name or name.endswith((".dpapi", ".key", ".sqlite", ".sqlite-wal", ".sqlite-shm", ".db", ".db-wal", ".db-shm"))), "private key or raw database input forbidden")
        key = ref["path"].casefold()
        require(key not in self.refs or exact(self.refs[key], ref), "conflicting exact pin")
        if key not in self.buffers:
            raw = canonical(ref["path"]).read_bytes()
            require(len(raw) == ref["bytes"] and digest(raw) == ref["sha256"], "public pin mismatch")
            self.refs[key], self.buffers[key] = ref, raw
        return self.buffers[key]

    def obj(self, ref):
        return decode(self.read(ref))

    def observed(self, path):
        p = canonical(str(Path(path).resolve()))
        raw = p.read_bytes()
        ref = dict(path=str(p), sha256=digest(raw), bytes=len(raw))
        self.read(ref)
        return ref

    def close_check(self):
        for ref in self.refs.values():
            raw = canonical(ref["path"]).read_bytes()
            require(len(raw) == ref["bytes"] and digest(raw) == ref["sha256"], "input changed during review")

def guard_closed(g):
    require(g["closed"] is True and g["errors"] == [] and type(g["retained_handles_count"]) is int and g["retained_handles_count"] == 0, "guard not closed")

def native_closed_zero(result):
    require(type(result["actual_exit"]) is int and result["actual_exit"] == 0, "real native exit zero required")
    require(result["error"] is None and result["timed_out"] is False, "native failed/timed out")
    require(type(result["owned_child_pid"]) is int and result["owned_child_pid"] > 0, "exact native PID")
    require(type(result["creation_time_100ns"]) is int and result["creation_time_100ns"] > 0, "exact FILETIME")
    j = result["job_cleanup"]
    require(all(j[k] is True for k in JOB_FLAGS) and type(j["active_processes_last_observed"]) is int and j["active_processes_last_observed"] == 0 and j["errors"] == [], "owned Job not closed")

def validity(payload, phase, now):
    start_key = "not_before_utc" if phase == "release" else "issued_utc"
    issued = datetime.fromisoformat(payload[start_key].replace("Z", "+00:00"))
    expiry = datetime.fromisoformat(payload["expires_utc"].replace("Z", "+00:00"))
    require(issued.tzinfo is not None and expiry.tzinfo is not None, "absolute UTC interval")
    require(issued <= now < expiry, "absolute validity elapsed; no refresh or retry")
    if phase == "grant":
        require((expiry - issued).total_seconds() == 240, "original four-minute interval required")
    return expiry

def signed_payload_exact(raw, payload_raw):
    wrapper = decode(raw)
    require(set(wrapper) == {"payload", "signature"} and type(wrapper["signature"]) is str and bool(wrapper["signature"]), "signed wrapper")
    text = raw.decode("utf-8")
    prefix = '{"payload":'
    require(text.startswith(prefix), "production signed serialization")
    _, end = json.JSONDecoder(object_pairs_hook=pairs).raw_decode(text, len(prefix))
    require(text[len(prefix):end].encode("utf-8") == payload_raw, "signed payload byte mismatch")
    return wrapper

def public_rows(value):
    require(type(value) is dict and value, "whole typed-row digest map")
    for table, row in value.items():
        require(type(table) is str and type(row) is dict and set(row) == {"columns", "row_digests"}, "no raw rows")
        require(type(row["columns"]) is list and all(type(v) is str for v in row["columns"]), "column names only")
        require(type(row["row_digests"]) is list and all(type(v) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", v) for v in row["row_digests"]), "typed digests only")

def jcs_digest(value):
    def ordered(v):
        if type(v) is str:
            v.encode("utf-16-be", errors="strict")
            return v
        if type(v) is list:
            return [ordered(x) for x in v]
        require(type(v) is dict and all(type(k) is str for k in v), "restricted public JCS domain")
        return {k: ordered(v[k]) for k in sorted(v, key=lambda x: x.encode("utf-16-be"))}
    return digest(json.dumps(ordered(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode())

def load_context(request, inputs):
    cfg = inputs.obj(request["Config"])
    require(cfg["Schema"] == "researchos.root-native-migration-controller.v1", "controller schema")
    hc = inputs.obj(cfg["HarnessConfig"])
    require(hc["Schema"] == "researchos.synthetic-native-migration-config.v1" and hc["Case"] == "positive-replay", "only reviewed positive-replay scope")
    require(hc["CaseID"] == request["CaseID"], "explicit fresh case binding")
    require(hc["RootSigningPublicKey"] == request["RootSigningPublicKey"], "explicit root-adoption public key")
    current_phase(cfg, hc, request["Phase"])
    frozen = {}
    for ref in cfg["FrozenInputs"]:
        ref = plain(ref)
        require(ref["path"].casefold() not in frozen, "duplicate FrozenInput")
        frozen[ref["path"].casefold()] = ref
        inputs.read(ref)
    for name in ("ControllerSource", "HarnessConfig", "TestProgram", "ObservedOwnedHelper", "OriginalOwnedHelper", "SourceReadGuard", "CompilerInventory", "BuildInvocation"):
        ref = plain(cfg[name])
        require(exact(frozen.get(ref["path"].casefold()), ref), "config input absent from frozen Source")
    require(cfg["SourceReadGuard"]["sha256"] == "sha256:" + GUARD_SHA, "reviewed guard Source")
    for name in ("RootProgram", "ControlProgram", "BackupProgram", "EnrollmentProgram", "PythonProgram", "BrokerSource", "PrivateStdinHelper"):
        ref = plain(hc[name])
        require(exact(frozen.get(ref["path"].casefold()), ref), "program absent from frozen Source")
    require(canonical(hc["PythonProgram"]["path"]).resolve() == Path(sys.executable).resolve(), "Python runtime pin")
    inv = inputs.obj(cfg["BuildInvocation"]); argv = inv["argv"]
    native_closed_zero(inv["result"])
    require(type(inv["actual_native_exit"]) is int and inv["actual_native_exit"] == 0, "compile actual zero")
    require(argv.count("-o") == 1 and "-c" in argv and "-tags=researchos_native_recovery_harness" in argv, "tagged actual compiler command")
    require(canonical(argv[argv.index("-o") + 1]) == canonical(cfg["TestProgram"]["path"]), "compiled test binary provenance")
    require(canonical(inv["cwd"]) == canonical(hc["BuildRoot"]), "compiler BuildRoot")
    inventory = inputs.obj(cfg["CompilerInventory"])
    require(inventory["build_tag"] == "researchos_native_recovery_harness" and inventory["includes_actual_test_and_embed_inputs"] is True, "actual compiler inventory")
    for ref in inventory["build_inputs"] + inventory["product_inventory"]:
        ref = dict(ref, sha256="sha256:" + ref["sha256"].removeprefix("sha256:"))
        require(exact(frozen.get(ref["path"].casefold()), plain(ref)), "compiler input absent")
    snap = inputs.obj(request["Snapshot"])
    require(snap["schema"] == "researchos.root-native-review-snapshot.v1" and exact(snap["config_ref"], request["Config"]), "snapshot config")
    require(snap["case"] == hc["Case"] and snap["case_id"] == hc["CaseID"] and snap["phase"] == request["Phase"], "snapshot phase/case")
    for key, name in (("harness_config_ref", "HarnessConfig"), ("compiler_inventory_ref", "CompilerInventory"), ("test_build_invocation_ref", "BuildInvocation")):
        require(exact(snap[key], cfg[name]), "snapshot public Source binding")
    guard_closed(snap["snapshot_guard_cleanup"])
    require(snap["root_approval"] is False and snap["sql_read_performed_by_controller"] is False, "snapshot is evidence")
    observation = inputs.obj(snap["observation_ref"])
    require(observation["schema"] == "researchos.root-held-test-job-observation.v1" and exact(observation["config_ref"], request["Config"]) and observation["job_binding_id"] == snap["job_binding_id"], "owned snapshot Job")
    result = observation["result"]
    require(result["resumed"] is True and result["actual_exit"] is None and result["job_cleanup"]["assigned_before_resume"] is True and type(result["job_cleanup"]["active_processes_last_observed"]) is int and result["job_cleanup"]["active_processes_last_observed"] >= 1, "snapshot live Job")
    for ref in snap["evidence_refs"]:
        inputs.read(ref)
    metadata = inputs.obj(request["PublicKeyMetadata"])
    require(metadata["status"] == "OFFLINE_KEYS_CREATED_PUBLIC_ONLY_NOT_AN_ACCEPTED_AUTHORITY", "key metadata status")
    require(metadata["keys"]["issuer"]["public_key_hex"] == request["IssuerPublicKey"] and metadata["keys"]["issuer"]["private_plaintext_logged"] is False, "issuer public metadata")
    require(metadata["keys"]["root-adoption"]["public_key_hex"] == request["RootSigningPublicKey"] and metadata["keys"]["root-adoption"]["private_plaintext_logged"] is False, "root-adoption public metadata")
    # Deliberately never follow private_resource_ref.
    require(re.fullmatch(r"[0-9a-f]{64}", request["IssuerPublicKey"]) and re.fullmatch(r"S-1-[0-9-]+", request["SID"]), "explicit key/SID")
    return cfg, hc, snap

def current_phase(cfg, hc, phase):
    work = canonical(cfg["ControllerDirectory"]); output = canonical(hc["OutputDirectory"])
    require(not (work / "controller.closed.json").exists(), "controller lifecycle already terminal")
    require(not (work / "stop.request.json").exists(), "controller stop requested")
    if phase == "fixture-retained":
        require((output / "06-fixture-retained.ready.json").is_file() and not (output / "06-release-fixture.approval.json").exists(), "retained pause unavailable")
    else:
        require(phase in PHASES and not (output / "06-fixture-retained.ready.json").exists(), "not current live phase")
        require((output / PHASES[phase][1]).is_file() and not (output / PHASES[phase][2]).exists(), "phase consumed/unavailable")
        if phase == "release":
            require(not (output / PHASES["grant"][1]).exists(), "future phase already started")

def release_source_set(hc):
    root = canonical(hc["BuildRoot"])
    directories = ["apps/control", "internal", "adapters", "evaluation", "ops", "migrations/sqlite", "spec/v2.0/contracts"]
    if (root / "vendor").exists():
        directories.append("vendor")
    paths = []
    for relative in directories:
        directory = root / relative
        require(directory.is_dir() and not directory.is_symlink(), "source directory missing/symlink")
        for p in directory.rglob("*"):
            require(not p.is_symlink(), "Source symlink")
            if not p.is_dir():
                require(p.is_file(), "nonregular Source")
                paths.append(p.resolve())
    paths += [root / n for n in ("go.mod", "go.sum", "execution/toolchains/locked.json")]
    paths += [root / n for n in ("go.work", "go.work.sum") if (root / n).exists()]
    return {str(p).casefold(): "source:" + p.relative_to(root).as_posix() for p in paths}

def validate_release(payload, request, cfg, hc, inputs):
    require(payload["schema"] == "researchos.recovery-release.v1" and payload["purpose"] == "RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1", "release contract")
    require(payload["id"] == "synthetic-native-" + hc["CaseID"] and payload["sid"] == request["SID"] and payload["root_signing_public_key"] == request["RootSigningPublicKey"], "release key/SID/case")
    require(exact(payload["root_image"], hc["RootProgram"]) and exact(payload["control_image"], hc["ControlProgram"]) and payload["source_root"] == hc["BuildRoot"], "release program/Source binding")
    expected = release_source_set(hc)
    actual = {}
    for ref in payload["source_files"]:
        inputs.read(ref)
        require(ref["path"].casefold() not in actual, "duplicate release Source")
        actual[ref["path"].casefold()] = ref["role"]
    require(actual == expected, "complete exact release Source inventory")
    validity(payload, "release", datetime.now(timezone.utc))

def concrete(request, inputs, cfg, hc, snap):
    phase = request["Phase"]
    require(phase in PHASES and request["Action"] in ("sign", "publish"), "one selected concrete phase/action")
    current_phase(cfg, hc, phase)
    require(exact(snap["payload_ref"], request["Payload"]), "explicit payload pin")
    payload_raw = inputs.read(request["Payload"]); payload = decode(payload_raw)
    output = canonical(hc["OutputDirectory"]); work = canonical(cfg["ControllerDirectory"])
    require(canonical(request["Payload"]["path"]) == output / PHASES[phase][0], "current payload path")
    destination = canonical(hc["RootProgram"]["path"]).parent / PHASES[phase][3]
    require(canonical(snap["signed_destination"]) == destination and snap["sign_kind"] == PHASES[phase][4], "fixed signed destination/sign kind")
    ready = inputs.obj(snap["ready_ref"])
    require(canonical(snap["ready_ref"]["path"]) == output / PHASES[phase][1], "current ready path")
    require(ready["payload_sha256"] == request["Payload"]["sha256"] and ready["fixed_signed_path"] == str(destination) and ready["sign_kind"] == snap["sign_kind"] and ready["review_required"] is True and ready["synthetic_case"] == "positive-replay", "ready payload binding")
    fixture = inputs.obj(snap["fixture_public_ref"])
    require(fixture["synthetic"] is True and fixture["formal"] is False and fixture["credential_output"] is False and type(fixture["production_db_writes"]) is int and fixture["production_db_writes"] == 0, "public synthetic fixture")
    require(canonical(fixture["root"]).is_relative_to(canonical(cfg["Environment"]["TEMP"])) and canonical(fixture["database"]).parent == canonical(fixture["root"]) and canonical(fixture["database"]).is_file(), "current original fixture absent")
    if phase == "release":
        validate_release(payload, request, cfg, hc, inputs)
    else:
        require(payload["schema"] == "researchos.recovery-migration-grant.v1" and payload["purpose"] == "RESEARCHOS_PREPARED_SCHEMA23_TO24_V1" and payload["stage"] == "APPLY_ORIGINAL", "grant contract")
        require(re.fullmatch(r"[0-9a-f]{64}", payload["nonce"]), "grant nonce")
        require(ready["intentional_negative"] is False and ready["expires_utc"] == payload["expires_utc"], "positive absolute grant expiry")
        signed_release = inputs.obj(request["ReleaseDocument"])
        require(canonical(request["ReleaseDocument"]["path"]) == destination.parent / "recovery-release.json" and request["ReleaseDocument"]["sha256"] == payload["release_sha256"], "exact prior signed release")
        validate_release(signed_release["payload"], request, cfg, hc, inputs)
        b = payload["binding"]
        require(b["plan_id"] == "schema23-to24-prepared-abandonment-v1" and b["owner_root"] == "queue-upgrade-owner" == fixture["owner_root"] and b["project_id"] == fixture["project_id"], "grant owner/project")
        require(b["root"] == fixture["root"] and b["database"] == fixture["database"] and b["root_identity"] == snap["measured_native_ids"]["root"] and b["database_identity"] == snap["measured_native_ids"]["database"], "grant native identity binding")
        rehearsal = inputs.obj(b["rehearsal"])
        for key in ("source_schema_sha256", "target_schema_sha256", "sql_sha256", "original_rows_sha256", "options_sha256", "source_inventory_sha256", "target_inventory_sha256"):
            require(b[key] == rehearsal[key], "grant rehearsal binding: " + key)
        require(b["source_schema_sha256"] == fixture["schema_sha256"] and b["original_rows_sha256"] == fixture["typed_rows_sha256"], "original fixture hashes")
        require(b["source_release_sha256"] == hc["BackupProgram"]["sha256"] and b["target_release_sha256"] == hc["ControlProgram"]["sha256"], "grant programs")
        require(exact(payload["options"], rehearsal["options"]) and payload["options"]["Plan"] == b["plan_id"] and payload["options"]["Source"] == fixture["database"], "grant exact options")
        require(b["backup"]["sha256"] == rehearsal["backup_manifest_sha256"] and b["backup"]["bytes"] == rehearsal["backup_manifest_bytes"], "grant backup binding")
        inputs.read(b["backup"])
        roles = {}
        for ref in payload["pins"]:
            inputs.read(ref)
            require(ref["role"] not in roles, "duplicate grant role")
            roles[ref["role"]] = ref
        require(all(k in roles for k in ("source-program", "target-program", "migration-sql", "encrypted-backup-manifest", "isolated-restore-rehearsal")), "required grant pins")
        require(roles["source-program"]["sha256"] == b["source_release_sha256"] and roles["target-program"]["sha256"] == b["target_release_sha256"] and roles["migration-sql"]["sha256"] == b["sql_sha256"], "dynamic role binding")
        # Snapshot producer measured all recursive RawPins; exact multiset prevents omissions.
        observed = snap["declared_pin_observations"]
        require(all(v["matches"] is True and exact(plain(v["declared"]), v["actual"]) for v in observed), "declared public pin mismatch")
        for v in observed:
            inputs.read(v["actual"])
        rawpins = []
        def walk(v):
            if type(v) is dict:
                if set(v) == {"role", "path", "sha256", "bytes"}:
                    rawpins.append(v)
                else:
                    for child in v.values():
                        walk(child)
            elif type(v) is list:
                for child in v:
                    walk(child)
        walk(payload)
        require(exact(rawpins, [v["declared"] for v in observed]), "full declared public binding")
    validity(payload, phase, datetime.now(timezone.utc))
    approval = dict(Schema="researchos.root-native-concrete-approval.v1",
                    Action="SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD", ConfigSHA256=request["Config"]["sha256"],
                    Snapshot=request["Snapshot"], Payload=request["Payload"], SignedDestination=str(destination), SignKind=snap["sign_kind"])
    if request["Action"] == "sign":
        require(not destination.exists() and not (work / ("sign-" + phase + ".consumed.json")).exists(), "sign already attempted")
    else:
        rec = inputs.obj(request["SigningReceipt"])
        require(rec["schema"] == "researchos.root-review-signing-receipt.v1" and rec["success"] is True and rec["error_type"] is None, "successful actual signer receipt")
        require(exact(rec["config_ref"], request["Config"]) and exact(rec["payload_ref"], request["Payload"]) and rec["phase"] == phase and rec["sign_kind"] == snap["sign_kind"], "signing receipt binding")
        native_closed_zero(rec["result"]); guard_closed(rec["source_guard_cleanup"])
        require(rec["private_path_recorded"] is False and rec["private_key_read_by_controller"] is False and rec["harness_approval_published"] is False, "signer public metadata")
        signing_approval = inputs.obj(rec["approval_ref"])
        require(exact(signing_approval, approval), "receipt binds exact previous sign approval")
        require(exact(rec["signed_ref"], request["SignedDocument"]) and canonical(request["SignedDocument"]["path"]) == destination, "signed destination binding")
        signed_payload_exact(inputs.read(request["SignedDocument"]), payload_raw)
        approval.update(Action="PUBLISH_REVIEWED_SIGNED_DOCUMENT", SignedDocument=request["SignedDocument"], SigningReceipt=request["SigningReceipt"])
    return approval, payload

def retained(request, inputs, cfg, hc, snap):
    require(request["Action"] == "release-fixture" and request["Phase"] == "fixture-retained", "explicit retained release")
    current_phase(cfg, hc, "fixture-retained")
    q = inputs.obj(request["InspectionReceipt"])
    require(q["schema"] == "researchos.root-native-whole-fixture-inspection.v1" and exact(q["config_ref"], request["Config"]) and exact(q["snapshot_ref"], request["Snapshot"]), "Root inspection binding")
    for key in ("fixture_read_complete", "whole_row_schema_review_complete", "transaction_snapshot_complete", "primary_and_WAL_bytes_unchanged", "synthetic_only"):
        require(q[key] is True, "full inspection required")
    require(q["private_credentials_recorded"] is False and q["private_raw_rows_recorded"] is False and q["formal_acceptance"] is False, "public inspection only")
    require(type(q["data_version_before"]) is int and q["data_version_before"] == q["data_version_after"] and exact(q["native_ids"], snap["measured_native_ids"]), "stable whole SQL inspection")
    guard_closed(q["reader_guard_cleanup"]); guard_closed(q["database_guard_cleanup"])
    require(q["database_share_mode"] == "READ_WRITE_SHARED_DELETE_DENIED" and q["immutable_database_claim"] is False, "live SQLite semantics")
    # Inspect only its public DB pin shape; do not open/read/copy SQLite or credentials.
    db = canonical(plain(q["database_ref"])["path"])
    require(db.is_file() and db.is_relative_to(canonical(cfg["Environment"]["TEMP"])), "retained original DB no longer exists")
    public_rows(q["typed_rows"]); require(jcs_digest(q["typed_rows"]) == q["typed_rows_sha256"], "inspection whole-row digest")
    before = inputs.obj(q["before_ref"]); public_rows(before)
    if request["ExpectedFixtureState"] == "unchanged-failed":
        require(q["expected_state_matches"] is False and exact(q["schema_versions"], list(range(1, 24))) and exact(q["typed_rows"], before), "failed fixture not wholly unchanged")
    else:
        require(request["ExpectedFixtureState"] == "migrated" and q["expected_state_matches"] is True and exact(q["schema_versions"], list(range(1, 25))), "expected completed schema")
        after = inputs.obj(q["after_ref"]); public_rows(after)
        require(exact(after, q["typed_rows"]) and q["sqlite_schema_sha256"] == q["expected_target_schema_sha256"] and all(v is True for v in q["original_table_invariants"].values()), "independent target invariants")
        require(set(q["typed_rows"]) - set(before) == {"runtime_prepared_abandonments"} and q["typed_rows"]["runtime_prepared_abandonments"]["row_digests"] == [], "only empty proof table added")
    return dict(Schema="researchos.root-native-fixture-release.v1", Action="RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION",
                ConfigSHA256=request["Config"]["sha256"], Snapshot=request["Snapshot"], InspectionReceipt=request["InspectionReceipt"]), None

def prepare(request, inputs):
    require(request["Schema"] == "researchos.root-single-phase-approval-request.v1", "Root request schema")
    cfg, hc, snap = load_context(request, inputs)
    approval, payload = retained(request, inputs, cfg, hc, snap) if request["Action"] == "release-fixture" else concrete(request, inputs, cfg, hc, snap)
    return approval, payload, cfg, hc

def main():
    require(len(sys.argv) == 4, "REQUEST_PATH REQUEST_SHA256 REQUEST_BYTES")
    ref = dict(path=str(Path(sys.argv[1]).resolve()), sha256=sys.argv[2], bytes=int(sys.argv[3]))
    inputs = Inputs(); request = inputs.obj(ref)
    output = canonical(request["Output"])
    require(not output.exists() and output.parent.is_dir(), "fresh approval output in existing Root directory")
    require(not output.with_name(output.name + ".helper-closure.json").exists(), "fresh helper closure output")
    if request["Action"] in ("sign", "publish"):
        require(request["Phase"] in PHASES, "explicit current phase")
        validity(inputs.obj(request["Payload"]), request["Phase"], datetime.now(timezone.utc))
    # No automatic action. The request pins the current decision inputs and output.
    approval, payload, cfg, hc = prepare(request, inputs)
    protected = [canonical(cfg["ControllerDirectory"]), canonical(hc["OutputDirectory"]), canonical(hc["RootProgram"]["path"]).parent, canonical(hc["BuildRoot"]), canonical(cfg["Environment"]["TEMP"])]
    require(all(not output.is_relative_to(p) for p in protected), "approval output must be separate from native case/product")
    gp = plain(cfg["SourceReadGuard"])
    module = types.ModuleType("root_concrete_helper_guard"); module.__file__ = gp["path"]
    exec(compile(inputs.read(gp), gp["path"], "exec"), module.__dict__)
    self_ref = inputs.observed(Path(__file__).resolve()); inputs.observed(Path(sys.executable).resolve())
    refs = [dict(path=r["path"], sha256=r["sha256"][7:], bytes=r["bytes"]) for r in inputs.refs.values()]
    g = module.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
    g.acquire(refs)
    cleanup = None
    try:
        inputs.close_check()
        current_phase(cfg, hc, request["Phase"])
        if payload is not None:
            validity(payload, request["Phase"], datetime.now(timezone.utc))
        raw = (json.dumps(approval, ensure_ascii=True, indent=2) + "\n").encode()
    finally:
        cleanup = g.close()
    guard_closed(cleanup)
    # Do not publish even an approval artifact if its read guard failed to close.
    inputs.close_check()
    current_phase(cfg, hc, request["Phase"])
    if payload is not None:
        validity(payload, request["Phase"], datetime.now(timezone.utc))
    with output.open("xb") as stream:
        stream.write(raw)
    closure = output.with_name(output.name + ".helper-closure.json")
    with closure.open("xb") as stream:
        stream.write((json.dumps(dict(schema="researchos.root-approval-helper-closure.v1",
            request_ref=ref, approval_ref=dict(path=str(output), sha256=digest(raw), bytes=len(raw)),
            helper_ref=self_ref, source_guard_cleanup=cleanup, no_sign_publish_child_SQL=True,
            TTL_unchanged=True, live_native_identity_recheck_required_by_existing_API=True,
            formal_acceptance=False), ensure_ascii=True, indent=2) + "\n").encode())
    print(json.dumps(dict(approval_ref=dict(path=str(output), sha256=digest(raw), bytes=len(raw)),
                         only_approval_generated=True, actual_native_exit=None, formal_acceptance=False)))

if __name__ == "__main__":
    main()

