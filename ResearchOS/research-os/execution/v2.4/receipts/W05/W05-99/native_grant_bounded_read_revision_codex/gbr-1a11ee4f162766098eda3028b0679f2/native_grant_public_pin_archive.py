"""Archive explicitly selected existing C12 grant public/opaque bytes only."""
import sys
sys.dont_write_bytecode = True
import collections
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import types

CONFIG_SHA = "sha256:38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256"
CONFIG_BYTES = 1106152
HARNESS_SHA = "sha256:3401b8b2fdfa65f6ba06ecc90a7953215c492b58622dcb99257fe12982fa2995"
HARNESS_BYTES = 2790
CASE_ID = "t12cl149d6f49321"
GUARD_SHA = "sha256:e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
INVENTORY = {'migrations/sqlite/0001_bootstrap.sql': {'sha256': 'sha256:bb87c889e31fd5412b49743d106679f783b6dd21d874fe29d82d18a729ce3dbc', 'bytes': 160}, 'migrations/sqlite/0002_domain.sql': {'sha256': 'sha256:90d6c36100cbfaddf85c23f603b686336d161e43eeeed47c034ab85415b25db4', 'bytes': 6924}, 'migrations/sqlite/0003_context.sql': {'sha256': 'sha256:50aa1579e4233cbb64ac30777e27c55cba29bab7ee0cc221a677f9a420a7159a', 'bytes': 2277}, 'migrations/sqlite/0004_sources.sql': {'sha256': 'sha256:d40152642778d8ea4e21148fd6517bdc8bf4c2582a8d6212b8cfdf7a470dea06', 'bytes': 1284}, 'migrations/sqlite/0005_runtime.sql': {'sha256': 'sha256:f3b9cd4c03f101c22c47a4fd7ad72593babe69de9abcd8a1ee3056fa6c23ade5', 'bytes': 1088}, 'migrations/sqlite/0006_orchestration.sql': {'sha256': 'sha256:cbc9ede2d2e46e1e68ac7120d2a99b29627f2e13b1fc82937e3ed13ac9b2317b', 'bytes': 3061}, 'migrations/sqlite/0007_retrieval.sql': {'sha256': 'sha256:eaa3963a3acdfcc1791982432c42dea9d4dd8f0baf7de51d278fce70bcd626bb', 'bytes': 2037}, 'migrations/sqlite/0008_artifact_uses.sql': {'sha256': 'sha256:adf17ad69203f0e700897a426f2d596496081bd5f3a964cbea8e3db9fc561ee7', 'bytes': 1441}, 'migrations/sqlite/0009_retrieval_root_identity.sql': {'sha256': 'sha256:48219da409abc3f9d353e8d91a71a387ea342e5c13aae711a36c28410b22fb4f', 'bytes': 638}, 'migrations/sqlite/0010_experiments.sql': {'sha256': 'sha256:c197ff792f62a1be5903bb6967175512cb53bdb09ff276e06fa8542822024287', 'bytes': 1581}, 'migrations/sqlite/0011_resources.sql': {'sha256': 'sha256:45c082ae0980af14f5b0be2d5aae02622dcc15c8c566b442077b4c1fb0c9942b', 'bytes': 1926}, 'migrations/sqlite/0012_experiment_execution.sql': {'sha256': 'sha256:c81411769ef2bd3ec1d101f311ce37722036485b8e9d99d45ae9c9be48f088c0', 'bytes': 857}, 'migrations/sqlite/0013_research_cycles.sql': {'sha256': 'sha256:188e0d6fbcffd3901d36109dcd421a21f7ef704574f62cd5c0f8af862c191d1e', 'bytes': 829}, 'migrations/sqlite/0014_remote_access.sql': {'sha256': 'sha256:687b01552260301a8f3f39e92422f16d0b2e310b38f77d1b025566f9a9cfa4d7', 'bytes': 1318}, 'migrations/sqlite/0015_evolution_fixture.sql': {'sha256': 'sha256:d70dd0580e89e2a7940c90ee771b2bd94551a42d8cda7fadfe83b60509852fe9', 'bytes': 4508}, 'migrations/sqlite/0016_runtime_qualification.sql': {'sha256': 'sha256:7fd44c42be4c0753c367fc8361e9990b56e4f9a001a5f443ef62d0d87d05a03f', 'bytes': 1841}, 'migrations/sqlite/0017_runtime_dispatch.sql': {'sha256': 'sha256:e5a2671c25725205bb5306c7fcbab254d53e3ef7a0448a163a41c5ac24a7b558', 'bytes': 1075}, 'migrations/sqlite/0018_intent_planning.sql': {'sha256': 'sha256:7592b2b47d2e305f9ec26937830b5c0606c7d90622401a0b6b80a8c8a67db4e0', 'bytes': 430}, 'migrations/sqlite/0019_evolution_release_operations.sql': {'sha256': 'sha256:54ff6eb7a7ca588df738f5bd68b6f6851d86916cef435abaac15d1f8bd6e131e', 'bytes': 2907}, 'migrations/sqlite/0020_research_cycle_work.sql': {'sha256': 'sha256:3f90bdb0e828cec90bc370f34abed0cf0629dc78dcc01dda250c18cda49e528a', 'bytes': 10771}, 'migrations/sqlite/0021_research_pending_windows.sql': {'sha256': 'sha256:36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32', 'bytes': 584}, 'migrations/sqlite/0022_client_command_queue.sql': {'sha256': 'sha256:e2abcc078bbac1c076736a40249d50c85e25b4c8fd93e975f8528f8f8277abcd', 'bytes': 2535}, 'migrations/sqlite/0023_host_model_configuration.sql': {'sha256': 'sha256:07feef35d8d114f3d31aa99684ce85be9d2fafd2d5090a2c8548789b636cf794', 'bytes': 5408}, 'migrations/sqlite/0024_prepared_run_abandonment.sql': {'sha256': 'sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098', 'bytes': 2933}, 'migrations/sqlite/next_v24_sessions.sql': {'sha256': 'sha256:1ca3930f96f7c2c99e7bc6e668dd5658393264cf1e6bf6352b47fb3de8c7dfe3', 'bytes': 2112}, 'spec/v2.0/contracts/domain.schema.json': {'sha256': 'sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847', 'bytes': 195457}, 'spec/v2.0/contracts/openapi.json': {'sha256': 'sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920', 'bytes': 380696}, 'internal/api/contracts/client.protocol.schema.json': {'sha256': 'sha256:8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b', 'bytes': 161794}, 'internal/api/contracts/domain.schema.json': {'sha256': 'sha256:b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54', 'bytes': 204466}}
ALIAS_ROLE = "migration-sql"
ALIAS_TARGET = "target-inventory:migrations/sqlite/0024_prepared_run_abandonment.sql"
PLAN = "schema23-to24-prepared-abandonment-v1"

def require(condition, message):
    if not condition:
        raise ValueError(message)

def pairs(items):
    out = {}
    for k, v in items:
        require(k not in out, "duplicate JSON member")
        out[k] = v
    return out

def decode(raw):
    def bad(value):
        raise ValueError("nonfinite JSON")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad)

def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def canonical(value, resolve=True):
    require(type(value) is str and value, "absolute local path")
    regular = value.replace("/", "\\")
    drive, tail = ntpath.splitdrive(regular)
    require(re.fullmatch("[A-Za-z]:", drive) and tail.startswith("\\") and
            not tail.startswith("\\\\") and ":" not in tail and
            all(ord(c) >= 32 for c in regular), "local path boundary")
    parts = tail[1:].split("\\")
    require(all(p and p not in (".", "..") and not p.endswith((" ", ".")) and
                not re.match(r"(?i)^(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", p)
                for p in parts), "regular path components")
    key = ntpath.normcase(ntpath.normpath(regular))
    if resolve:
        require(ntpath.normcase(str(Path(value).resolve()).replace("/", "\\")) == key,
                "path alias/reparse mismatch")
    return key

def inside(value, root):
    a, b = canonical(value), canonical(root)
    return a == b or a.startswith(b + "\\")

def exact(value, fields):
    require(type(value) is dict and set(value) == set(fields), "exact object shape")
    return value

def ref(value):
    exact(value, ("path", "sha256", "bytes"))
    canonical(value["path"])
    require(type(value["sha256"]) is str and re.fullmatch("sha256:[0-9a-f]{64}", value["sha256"]),
            "prefixed lowercase digest")
    require(type(value["bytes"]) is int and 0 <= value["bytes"] <= 128 * 1024 * 1024, "bounded integer bytes")
    return value

def rawpin(value):
    exact(value, ("role", "path", "sha256", "bytes"))
    require(type(value["role"]) is str and value["role"], "RawPin role")
    ref({k:value[k] for k in ("path", "sha256", "bytes")})
    return value

def plain(value):
    rawpin(value)
    return {k:value[k] for k in ("path", "sha256", "bytes")}

def same(a, b):
    return type(a) is type(b) and (set(a) == set(b) and all(same(a[k], b[k]) for k in a)
        if type(a) is dict else len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if type(a) is list else a == b)

def read_ref(value):
    ref(value)
    with Path(value["path"]).open("rb") as stream:
        raw = stream.read(value["bytes"] + 1)
    require(len(raw) == value["bytes"], "input pin mismatch")
    require(digest(raw) == value["sha256"], "input pin mismatch")
    return raw

def counter(values):
    return collections.Counter(json.dumps(v, sort_keys=True, separators=(",", ":")) for v in values)

def inventory_roles():
    return {prefix + name for prefix, count in (("source-inventory:", 23), ("target-inventory:", 24))
            for name in INVENTORY if not name.startswith("migrations/sqlite/0024_") or count == 24}

def validate_grant(payload, cfg, hc):
    require(payload.get("schema") == "researchos.recovery-migration-grant.v1" and
            payload.get("purpose") == "RESEARCHOS_PREPARED_SCHEMA23_TO24_V1" and
            payload.get("stage") == "APPLY_ORIGINAL", "concrete migration payload")
    binding, options = payload["binding"], payload["options"]
    require(binding["plan_id"] == PLAN and options["Plan"] == PLAN, "fixed migration plan")
    temp = cfg["Environment"]["TEMP"]
    roots = {p: options[k] for p, k in (("source-inventory:", "SourceRoot"), ("target-inventory:", "TargetRoot"))}
    for root in (*roots.values(), options["Snapshot"], options["Destination"]):
        require(inside(root, temp) and canonical(root) != canonical(temp), "current TEMP child")
    require(canonical(roots["source-inventory:"]) != canonical(roots["target-inventory:"]), "separate release roots")
    require(type(payload["pins"]) is list, "explicit grant pin list")
    pins = {}
    paths = {}
    inventories = inventory_roles()
    selected = {}
    for pin in payload["pins"]:
        rawpin(pin)
        role, path = pin["role"], pin["path"]
        require(role not in pins, "duplicate grant role")
        key = canonical(path)
        if key in paths:
            previous = paths[key]
            require({role, previous["role"]} == {ALIAS_ROLE, ALIAS_TARGET} and
                    same(plain(pin), plain(previous)), "undeclared duplicate grant path")
        paths[key] = pin
        pins[role] = pin
        if role in inventories:
            prefix, relative = role.split(":", 1)
            expected = str(Path(roots[prefix + ":"]) / Path(relative))
            require(canonical(path) == canonical(expected), "inventory root/path binding")
            require(pin["sha256"] == INVENTORY[relative]["sha256"] and
                    pin["bytes"] == INVENTORY[relative]["bytes"], "fixed release inventory bytes")
            selected[role] = pin
        elif role in ("encrypted-backup-manifest", "isolated-restore-rehearsal"):
            key, directory, name = ("backup", "Snapshot", "manifest.json") if role == "encrypted-backup-manifest" else (
                "rehearsal", "Destination", "prepared-abandonment-rehearsal.json")
            require(same(pin, binding[key]) and canonical(path) == canonical(str(Path(options[directory]) / name)),
                    "backup/rehearsal binding")
            selected[role] = pin
        elif role.startswith("encrypted-backup-payload:"):
            name = role.split(":", 1)[1]
            require(re.fullmatch("[A-Za-z0-9_][A-Za-z0-9_.-]*\\.enc", name) and
                    canonical(path) == canonical(str(Path(options["Snapshot"]) / name)), "opaque ciphertext name/path")
            selected[role] = pin
        elif role in ("source-program", "target-program"):
            field = "BackupProgram" if role == "source-program" else "ControlProgram"
            require(same(plain(pin), plain(hc[field])), "resident program binding")
        elif role == ALIAS_ROLE:
            pass
        elif role.startswith("fixture-evidence:"):
            name = role.split(":", 1)[1]
            require(name in ("before.rows.json", "fixture.public.json", "00-rehearsal/invocation.json",
                "00-rehearsal/stdout.raw", "00-rehearsal/stderr.raw") and
                canonical(path) == canonical(str(Path(hc["OutputDirectory"]) / Path(name))), "fixed fixture evidence")
        else:
            raise ValueError("unsupported grant pin role")
    required = inventories | {"encrypted-backup-manifest", "isolated-restore-rehearsal", "source-program",
        "target-program", ALIAS_ROLE} | {"fixture-evidence:" + n for n in (
        "before.rows.json", "fixture.public.json", "00-rehearsal/invocation.json",
        "00-rehearsal/stdout.raw", "00-rehearsal/stderr.raw")}
    require(required <= set(pins), "incomplete producer grant pin inventory")
    require(any(r.startswith("encrypted-backup-payload:") for r in selected), "ciphertext pins required")
    require(same(plain(pins[ALIAS_ROLE]), plain(pins[ALIAS_TARGET])), "declared migration SQL alias")
    for pin in selected.values():
        require(inside(pin["path"], temp), "selected original outside current TEMP")
    return pins, selected

def validate_selection(entries, allowed):
    require(type(entries) is list and entries, "nonempty explicit selection")
    chosen, paths = {}, set()
    for entry in entries:
        rawpin(entry)
        role, key = entry["role"], canonical(entry["path"])
        require(role in allowed and same(entry, allowed[role]), "selection not exact allowed grant RawPin")
        require(role not in chosen and key not in paths, "duplicate selected role/path")
        chosen[role] = entry
        paths.add(key)
    return chosen, sorted(set(allowed) - set(chosen))

def lifecycle(cfg, hc):
    require(not (Path(cfg["ControllerDirectory"]) / "controller.closed.json").exists(), "controller already closed")
    require(not (Path(hc["OutputDirectory"]) / "06-release-fixture.approval.json").exists(), "fixture release already requested")

def output_boundary(output, cfg, hc, inputs):
    path = Path(output)
    canonical(output)
    require(path.parent.is_dir() and not os.path.lexists(path), "fresh output with existing parent")
    protected = [cfg["ControllerDirectory"], hc["OutputDirectory"], hc["BuildRoot"], cfg["Environment"]["TEMP"]]
    protected += [str(Path(hc[k]["path"]).parent) for k in
                  ("RootProgram", "ControlProgram", "BackupProgram", "EnrollmentProgram", "PythonProgram")]
    protected += [str(Path(cfg["TestProgram"]["path"]).parent)]
    require(not any(inside(output, p) or inside(p, output) for p in protected), "output overlaps protected scope")
    require(not any(inside(r["path"], output) for r in inputs), "output overlaps frozen input")
    # Root receipts only; no canonical product/code output destination.
    receipt_root = str(Path(cfg["HarnessConfig"]["path"]).parents[2])
    require(inside(output, receipt_root) and canonical(output) != canonical(receipt_root), "Root receipt output only")
    return path

def emit_new(path, data):
    canonical(str(path))
    require(not os.path.lexists(path), "exclusive output")
    with path.open("xb") as stream:
        require(stream.write(data) == len(data), "short archive write")
        stream.flush()
        os.fsync(stream.fileno())
    require(path.read_bytes() == data, "archive bytes differ")
    return {"path":str(path), "sha256":digest(data), "bytes":len(data)}

def run(request_ref):
    request_raw = read_ref(request_ref)
    request = decode(request_raw)
    exact(request, ("Schema", "HelperSource", "Config", "Snapshot", "Payload", "OutputDirectory", "Entries"))
    require(request["Schema"] == "researchos.native-grant-public-pin-archive-request.v1", "request schema")
    helper = ref(request["HelperSource"])
    require(canonical(helper["path"]) == canonical(str(Path(__file__).resolve())), "current helper source")
    config_ref = ref(request["Config"])
    require(config_ref["sha256"] == CONFIG_SHA and config_ref["bytes"] == CONFIG_BYTES, "current fixed C12 config")
    cfg = decode(read_ref(config_ref))
    require(cfg["Schema"] == "researchos.root-native-migration-controller.v1", "config schema")
    hc_ref = ref(cfg["HarnessConfig"])
    require(hc_ref["sha256"] == HARNESS_SHA and hc_ref["bytes"] == HARNESS_BYTES, "current fixed harness config")
    hc = decode(read_ref(hc_ref))
    require(hc["CaseID"] == CASE_ID and hc["Case"] == "positive-replay", "current fixed case")
    snap_ref, payload_ref = ref(request["Snapshot"]), ref(request["Payload"])
    require(canonical(str(Path(snap_ref["path"]).parent)) == canonical(cfg["ControllerDirectory"]) and
            re.fullmatch("review-snapshot-grant-[0-9a-f]{32}\\.json", Path(snap_ref["path"]).name), "grant snapshot location")
    require(canonical(payload_ref["path"]) == canonical(str(Path(hc["OutputDirectory"]) / "02-grant.payload.json")),
            "fixed current payload path")
    snap, payload = decode(read_ref(snap_ref)), decode(read_ref(payload_ref))
    require(snap["schema"] == "researchos.root-native-review-snapshot.v1" and snap["phase"] == "grant" and
            snap["sign_kind"] == "migration-grant" and snap["case_id"] == CASE_ID and
            snap["case"] == hc["Case"] and same(snap["config_ref"], config_ref) and
            same(snap["harness_config_ref"], hc_ref) and same(snap["payload_ref"], payload_ref) and
            snap["root_approval"] is False, "snapshot current concrete binding")
    require(snap["snapshot_guard_cleanup"]["closed"] is True and not snap["snapshot_guard_cleanup"]["errors"],
            "snapshot guard cleanup")
    ready_ref, observation_ref = ref(snap["ready_ref"]), ref(snap["observation_ref"])
    require(canonical(ready_ref["path"]) == canonical(str(Path(hc["OutputDirectory"]) / "02-grant.ready.json")),
            "fixed readiness path")
    require(canonical(str(Path(observation_ref["path"]).parent)) == canonical(cfg["ControllerDirectory"]) and
            re.fullmatch("observe-[0-9a-f]{32}\\.response\\.json", Path(observation_ref["path"]).name),
            "observation location")
    ready, observed = decode(read_ref(ready_ref)), decode(read_ref(observation_ref))
    require(ready["payload_sha256"] == payload_ref["sha256"] and ready["sign_kind"] == "migration-grant" and
            ready["fixed_signed_path"] == snap["signed_destination"] and
            canonical(ready["fixed_signed_path"]) == canonical(str(Path(hc["RootProgram"]["path"]).parent / "current-schema23-to24-grant.json")), "ready payload binding")
    require(observed["schema"] == "researchos.root-held-test-job-observation.v1" and
            observed["job_binding_id"] == snap["job_binding_id"] and same(observed["config_ref"], config_ref) and
            observed["held_job_handle"] is True and observed["held_primary_handle"] is True and
            observed["phase"] == "grant" and
            observed["result"]["job_cleanup"]["assigned_before_resume"] is True and
            type(observed["result"]["job_cleanup"]["active_processes_last_observed"]) is int and
            observed["result"]["job_cleanup"]["active_processes_last_observed"] >= 1 and
            observed["result"]["resumed"] is True and observed["result"]["actual_exit"] is None,
            "snapshot held-job observation")
    pins, allowed = validate_grant(payload, cfg, hc)
    observations = snap["declared_pin_observations"]
    require(type(observations) is list, "declared observations")
    for item in observations:
        exact(item, ("declared", "actual", "matches"))
        require(item["matches"] is True and same(plain(item["declared"]), ref(item["actual"])),
                "declared pin mismatch")
    require(counter([x["declared"] for x in observations]) == counter(
        [payload["binding"]["backup"], payload["binding"]["rehearsal"]] + payload["pins"]), "snapshot declared closure")
    evidence = [ref(r) for r in snap["evidence_refs"]]
    require(len({canonical(r["path"]) for r in evidence}) == len(evidence), "unique snapshot evidence paths")
    require(all(any(same(plain(pin), r) for r in evidence) for pin in pins.values()), "snapshot evidence pin closure")
    chosen, missing = validate_selection(request["Entries"], allowed)
    guard_ref = ref(cfg["SourceReadGuard"])
    require(guard_ref["sha256"] == GUARD_SHA and guard_ref["bytes"] == 11404, "fixed guard Source")
    guard_raw = read_ref(guard_ref)
    module = types.ModuleType("grant_archive_read_guard")
    exec(compile(guard_raw, guard_ref["path"], "exec"), module.__dict__)
    refs = [request_ref, helper, config_ref, hc_ref, snap_ref, payload_ref, ready_ref, observation_ref, guard_ref]
    # The backup manifest is the one fixed public metadata dependency, even in partial mode.
    backup_ref = plain(allowed["encrypted-backup-manifest"])
    refs += [backup_ref] + [plain(p) for p in chosen.values()]
    output = output_boundary(request["OutputDirectory"], cfg, hc, refs)
    frozen = {}
    for r in refs:
        key = canonical(r["path"])
        require(key not in frozen or same(r, frozen[key]), "conflicting frozen pin")
        frozen[key] = r
    guard = module.SourceReadGuard()
    result = None
    try:
        guard.acquire([{**r, "sha256":r["sha256"][7:]} for r in frozen.values()])
        for r in frozen.values():
            require(read_ref(r) == guard.get_buffer(r["path"]), "frozen public input drift")
        manifest = decode(guard.get_buffer(backup_ref["path"]))
        names = [f["name"] + ".enc" for f in manifest["files"]]
        require(len(names) == len(set(names)) and names and
                all(re.fullmatch("[A-Za-z0-9_][A-Za-z0-9_.-]*\\.enc", n) for n in names),
                "backup ciphertext inventory names")
        require({"encrypted-backup-payload:" + n for n in names} ==
                {r for r in allowed if r.startswith("encrypted-backup-payload:")}, "backup ciphertext closure")
        lifecycle(cfg, hc)
        output_boundary(str(output), cfg, hc, refs)
        output.mkdir()
        members = []
        for index, (role, pin) in enumerate(sorted(chosen.items())):
            opaque = role.startswith("encrypted-backup-payload:")
            suffix = ".enc" if opaque else Path(pin["path"]).suffix
            target = output / ("%03d" % index + suffix)
            require(canonical(str(output)) == canonical(request["OutputDirectory"]), "output path drift")
            data = guard.get_buffer(pin["path"])
            archived = emit_new(target, data)
            members.append({"role":role, "kind":"opaque-ciphertext" if opaque else "public-bytes",
                "name":Path(pin["path"]).name, "original_ref":plain(pin), "archived_ref":archived})
        lifecycle(cfg, hc)
        for r in frozen.values():
            read_ref(r)
        alias = next((m for m in members if m["role"] == ALIAS_TARGET), None)
        result = {"schema":"researchos.native-grant-public-pin-archive.v1",
            "request_ref":request_ref, "config_ref":config_ref, "snapshot_ref":snap_ref, "payload_ref":payload_ref,
            "case_id":CASE_ID, "closure":"FULL_TEMP_PIN_CLOSURE" if not missing else "PARTIAL",
            "missing_roles":missing, "source_inventory_count":28, "target_inventory_count":29,
            "required_unique_temp_pin_count":len(allowed), "archived_unique_count":len(members),
            "members":members, "role_aliases":[] if alias is None else [{
                "role":ALIAS_ROLE, "target_role":ALIAS_TARGET, "original_ref":plain(pins[ALIAS_ROLE]),
                "archived_ref":alias["archived_ref"]}],
            "copied_raw_bytes_only":True, "recursive_reference_follow":False, "signature_verified":False,
            "grant_freshness_or_authority_claim":False, "original_owner_acceptance":False,
            "nine_cases_acceptance":False, "formal_42_acceptance":False}
    finally:
        cleanup = guard.close()
    require(cleanup["closed"] is True and not cleanup["errors"] and cleanup["verification"] == "PASSED",
            "archive source guard close/verification")
    result["source_guard_cleanup"] = cleanup
    return emit_new(output / "archive.public.manifest.json",
                    (json.dumps(result, ensure_ascii=True, indent=2) + "\n").encode("utf-8"))

def main():
    require(len(sys.argv) == 4, "REQUEST_PATH REQUEST_SHA256 REQUEST_BYTES")
    require(re.fullmatch("0|[1-9][0-9]*", sys.argv[3]), "decimal request byte count")
    result = run({"path":sys.argv[1], "sha256":sys.argv[2], "bytes":int(sys.argv[3])})
    print("GRANT_PUBLIC_ARCHIVE_OK " + json.dumps(result, ensure_ascii=True))

if __name__ == "__main__":
    main()
