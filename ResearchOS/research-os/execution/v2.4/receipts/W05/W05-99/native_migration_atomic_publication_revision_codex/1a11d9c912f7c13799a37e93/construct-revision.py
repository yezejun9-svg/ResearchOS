"""Source-only revision construction. No controller import or execution."""
import ast, difflib, hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=P.parent.parent/"native_migration_root_controller_source_codex/949c31b5ce9172756b85a2aa388"

def ref(p):
    raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def new_bytes(name,raw):
    with (P/name).open("xb") as stream: stream.write(raw)
def new_json(name,value):
    new_bytes(name,(json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))

assert ref(OLD/"HDF.json")["sha256"]=="3bbd2ae63d8418a919fe485e910238bf330e562e0f72e97f98a190bdfb8d3de9"
assert ref(OLD/"MF.json")["sha256"]=="a6c582433f80e76860e922bd1a51b7dc5874f0003fb402e0fefea36651ce51b6"
manifest=json.loads((OLD/"MF.json").read_bytes())
for name,pin in manifest["members"].items():
    actual=ref(OLD/name)
    assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"]
old_raw=(OLD/"root_native_migration_controller.py").read_bytes()
assert hashlib.sha256(old_raw).hexdigest()=="4880034052986ecf8b7c9c528de7069a81f78b4007c735d27776111beddb5138"
old=old_raw.decode("utf-8").replace("\r\n","\n")
code=old
changes=[]
def replace(before,after):
    global code
    assert code.count(before)==1, repr(before[:100])
    code=code.replace(before,after)
    changes.append({"before":before,"after":after})

replace('''def write_new(path, value):
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return public_ref(path)
''','''def write_new(path, value):
    # Windows rename refuses an existing destination. Do not use os.replace,
    # or run this publisher on a platform whose rename permits replacement.
    if os.name != "nt":
        raise OSError("atomic no-clobber publisher requires Windows")
    path = canonical_path(str(path))
    parent = canonical_path(str(path.parent))
    if not parent.is_dir():
        raise ValueError("existing canonical publication directory required")
    if os.path.lexists(path):
        raise FileExistsError("public destination already exists")
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    temporary = parent/("." + path.name + "." + uuid.uuid4().hex + ".pending")
    created = False
    try:
        with temporary.open("xb") as stream:
            created = True
            if stream.write(raw) != len(raw):
                raise OSError("short public JSON write")
            stream.flush()
            os.fsync(stream.fileno())
        if canonical_path(str(parent)) != parent or not parent.is_dir():
            raise ValueError("publication directory changed")
        # Same-directory publication after close; the OS, not the earlier
        # existence check, enforces no clobber if another writer wins.
        os.rename(temporary, path)
    except BaseException as error:
        if created:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as cleanup_error:
                # Keep the original failure type and the cleanup failure.
                # Never remove the destination or another call's temporary.
                raise error from cleanup_error
        raise
    return public_ref(path)


class PublicationPending(ValueError):
    """An unpinned public producer has not yet published complete JSON."""


def _complete_public_json(path):
    path = canonical_path(str(path))
    try:
        raw = path.read_bytes()
        value = decode(raw)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        # Go still creates final ready/evidence names before Write/Sync/Close.
        # Defer only unpinned publication reads; read_ref remains strict.
        raise PublicationPending("public JSON publication pending") from None
    return {"path":str(path), "sha256":digest(raw), "bytes":len(raw)}, value
''')

replace('''def _phase(c):
    out = c["output"]
    if (out/"06-fixture-retained.ready.json").is_file():
        return "fixture-retained"
    if (out/PHASES["grant"][1]).is_file() and not (out/PHASES["grant"][2]).exists():
        return "grant"
    if (out/PHASES["release"][1]).is_file() and not (out/PHASES["release"][2]).exists():
        return "release"
    return "running"
''','''def _phase(c):
    out = c["output"]
    for phase, name, approval in (
        ("fixture-retained", "06-fixture-retained.ready.json", None),
        ("grant", PHASES["grant"][1], PHASES["grant"][2]),
        ("release", PHASES["release"][1], PHASES["release"][2]),
    ):
        if (out/name).is_file() and (approval is None or not (out/approval).exists()):
            try:
                _complete_public_json(out/name)
            except PublicationPending:
                return "running"
            return phase
    return "running"
''')

replace('''            if stop.is_file():
                value = decode(stop.read_bytes())
                if value == {"Action":"STOP_OWNED_CASE", "ConfigSHA256":config_ref["sha256"]}:
                    cancellation.set()
''','''            if stop.is_file():
                try:
                    _, value = _complete_public_json(stop)
                except PublicationPending:
                    value = None
                if value == {"Action":"STOP_OWNED_CASE", "ConfigSHA256":config_ref["sha256"]}:
                    cancellation.set()
''')
replace('''                value = decode(path.read_bytes())
                if value != {"Action":"OBSERVE_HELD_JOB", "ConfigSHA256":config_ref["sha256"], "RequestID":request_id}:
''','''                try:
                    _, value = _complete_public_json(path)
                except PublicationPending:
                    continue
                if value != {"Action":"OBSERVE_HELD_JOB", "ConfigSHA256":config_ref["sha256"], "RequestID":request_id}:
''')

replace('''            raw = target.read_bytes()
            try:
                decode(raw)
            except (ValueError, UnicodeError):
                time.sleep(0.05)
                continue
            return public_ref(target)
''','''            try:
                response_ref, _ = _complete_public_json(target)
            except PublicationPending:
                time.sleep(0.05)
                continue
            return response_ref
''')

replace('''    refs = [public_ref(c["output"]/name) for name in files if (c["output"]/name).is_file()]
    fixture_path = c["output"]/"fixture.public.json"
    if fixture_path.is_file():
        fixture = decode(fixture_path.read_bytes())
''','''    refs = [_complete_public_json(c["output"]/name)[0]
            for name in files if (c["output"]/name).is_file()]
    fixture_path = c["output"]/"fixture.public.json"
    if fixture_path.is_file():
        fixture_ref, fixture = _complete_public_json(fixture_path)
''')
replace('''        retained = decode(fixture_path.read_bytes())
        fixture = {"database":retained["database"],"root":str(Path(retained["database"]).parent)}
''','''        fixture_ref, retained = _complete_public_json(fixture_path)
        fixture = {"database":retained["database"],"root":str(Path(retained["database"]).parent)}
''')
replace('''        payload_ref = public_ref(c["output"]/PHASES[phase][0])
        ready_ref = public_ref(c["output"]/PHASES[phase][1])
        payload = decode(read_ref(payload_ref))
        ready = decode(read_ref(ready_ref))
''','''        payload_ref, payload = _complete_public_json(c["output"]/PHASES[phase][0])
        ready_ref, ready = _complete_public_json(c["output"]/PHASES[phase][1])
''')
replace('''                "fixture_public_ref":public_ref(fixture_path),''','''                "fixture_public_ref":fixture_ref,''')
replace('''        snap["ready_ref"] != public_ref(c["output"]/PHASES[phase][1])):''','''        snap["ready_ref"] != _complete_public_json(c["output"]/PHASES[phase][1])[0]):''')
replace('''    current_payload = public_ref(c["output"]/PHASES[phase][0])''','''    current_payload = _complete_public_json(c["output"]/PHASES[phase][0])[0]''')

# Inverse checks preserve every original raw byte, including CRLF.
inverse=code
for item in reversed(changes):
    assert inverse.count(item["after"])==1
    inverse=inverse.replace(item["after"],item["before"])
assert inverse.replace("\n","\r\n").encode("utf-8")==old_raw
new_bytes("root_native_migration_controller.py",code.replace("\n","\r\n").encode("utf-8"))
for name in ("windows_owned_observed.py","root-controller-api.json"):
    new_bytes(name,(OLD/name).read_bytes())
assert ref(P/"windows_owned_observed.py")["sha256"]=="fe102f02de5aa966945ef88218e412f1988509168705d03a8660dab8b282d4e3"
new_json("controller-inverse-changes.json",changes)
new_bytes("controller-atomic-publication.patch","".join(difflib.unified_diff(
    old.splitlines(keepends=True),code.splitlines(keepends=True),
    fromfile="949c/root_native_migration_controller.py",
    tofile="atomic-revision/root_native_migration_controller.py")).encode("utf-8"))

amendment="""
## Atomic publication and incomplete producer reads (this revision)

This appendix supersedes the old direct-final-path O_EXCL publication description.
All controller public JSON writers, including observe/stop requests, responses,
started/closed observations, snapshots, signing-consumed markers, receipts and
Go phase/fixture approvals, use the same Windows-only write_new implementation.
The caller already selected the output from the validated controller/harness
context. write_new additionally requires a canonical absolute destination and
existing canonical parent directory. It creates a unique same-directory hidden
.pending filename with O_EXCL, writes every serialized byte, flushes, fsyncs and
closes before os.rename. Windows os.rename refuses an existing destination,
including a destination created after the preliminary check. os.replace is
never used. Non-Windows execution is refused. This is atomic visibility, not a
promise of directory metadata durability across power loss.

Pending names cannot match observe-*.request.json or any fixed Go approval name.
Failed publication raises its original error; only the temporary path that
this call successfully created and closed is removed. Existing destinations
and other calls' pending paths are never deleted. If that cleanup fails, the
original publication error is raised with the cleanup error as its cause; that
one residual pending file remains for Root inspection. The public serve/worker
failure receipts retain the original exception type as before. Other API
callers must retain their failed invocation/exception type; there is no retry
or overwriting of a final name. No source-author runtime failure was synthesized
to claim these semantics were dynamically verified.

The e57c Go producer is unchanged: nativeHarnessWrite marshals a complete JSON
value, creates its final path with O_EXCL, then performs Write/Sync/Close.
Unpinned Go ready/evidence reads now derive JSON and its hash/length from the
same complete byte buffer. Missing files, incomplete UTF-8 or JSON syntax
produce PublicationPending. Duplicate keys and other semantic/contract errors
are not silently accepted. _phase reports running while the highest eligible
ready file is incomplete, without cancelling the owned Job or falling back to
an earlier phase. snapshot exits with no artifact/approval if its required
public JSON is still pending; Root can call it again after publication.
This does not extend any existing deadline, nonce or grant interval.
Requests are not marked seen or enqueued until complete JSON passes the
existing exact Action/config/nonce equality. A pending request/stop read does
not cancel the case. Responses return a ref to the exact parsed byte buffer.

Ready/evidence syntax completion is only a read-completion condition. It is
never Root approval, signer authority, fsync/Close success evidence, or a
replacement for the existing held-input guard and exact hash checks.
All pinned read_ref behavior, concrete approval equality, fixed signed paths,
same held-Job binding, native identities and <=240-second grant limits are
unchanged. Snapshot evidence is still verified under the existing guard.
No Go producer, native binary, schema or observer helper was changed.
The seven public API signatures and API JSON are byte-identical to 949c.

Only source construction, AST/static/inverse/metadata checks were performed.
Root must independently review this revision and run actual public
observe/cancel/timeout and concurrent publication checks before proceeding to
any Owner-bearing or private signing operation. The complete earlier contract,
including its scope and private boundary, otherwise remains in force.
"""
new_bytes("CONTRACT.md",(OLD/"CONTRACT.md").read_bytes()+amendment.encode("utf-8"))

tree=ast.parse(code,filename=str(P/"root_native_migration_controller.py"))
oldtree=ast.parse(old)
funcs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
oldfuncs={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changed={name for name in oldfuncs if ast.dump(oldfuncs[name])!=ast.dump(funcs[name])}
assert changed=={"write_new","_phase","serve","poll","snapshot","_approval"}
for name in ("context","read_ref","require_ref","native_file_id","_signed_payload_exact",
             "sign_reviewed","publish_signed","release_fixture","stop","_live_observation"):
    assert ast.dump(oldfuncs[name])==ast.dump(funcs[name])
publisher=ast.get_source_segment(code,funcs["write_new"])
readcomplete=ast.get_source_segment(code,funcs["_complete_public_json"])
checks={
    "controller_ast_parse":True,
    "inverse_recovers_all_original_raw_bytes":True,
    "observer_byte_equal_949":(P/"windows_owned_observed.py").read_bytes()==(OLD/"windows_owned_observed.py").read_bytes(),
    "api_file_byte_equal_949":(P/"root-controller-api.json").read_bytes()==(OLD/"root-controller-api.json").read_bytes(),
    "changed_existing_functions_exact":sorted(changed),
    "windows_only_no_replace":'os.name != "nt"' in publisher and "os.replace(" not in code,
    "same_parent_pending_xb":'temporary = parent/' in publisher and 'temporary.open("xb")' in publisher,
    "close_before_rename":publisher.index("os.rename(")>publisher.index('if canonical_path(str(parent))'),
    "flush_fsync_before_rename":publisher.index("stream.flush()")<publisher.index("os.fsync(")<publisher.index("os.rename("),
    "owned_temp_cleanup_only":'if created:' in publisher and 'temporary.unlink(missing_ok=True)' in publisher,
    "no_final_destination_delete":'path.unlink(' not in code and 'os.remove(' not in code,
    "buffer_ref_same_as_decoded_bytes":'value = decode(raw)' in readcomplete and '"sha256":digest(raw), "bytes":len(raw)' in readcomplete,
    "pending_catch_narrow":'except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError)' in readcomplete,
    "original_pin_verification_ast_unchanged":True,
    "sign_publish_release_body_ast_unchanged":True,
    "go_binary_or_producer_changes":False,
    "controller_imported_or_executed":False,
    "native_sql_private_signing_model_calls":False,
}
assert all(v for k,v in checks.items() if k not in {
    "go_binary_or_producer_changes","controller_imported_or_executed","native_sql_private_signing_model_calls"})
new_json("static-evidence.json",{"schema":"researchos.native-controller-atomic-static.v1","checks":checks,
    "test_scope":"AST and static inverse only; no function execution or concurrency test",
    "prior_manifest_members_reverified":len(manifest["members"])})
new_json("public-input-pins.json",{
    "schema":"researchos.native-controller-atomic-inputs.v1",
    "inputs":[ref(OLD/name) for name in (
        "HDF.json","MF.json","root_native_migration_controller.py","windows_owned_observed.py",
        "CONTRACT.md","root-controller-api.json","public-input-pins.json","static-evidence.json")],
    "old_manifest_all_members_reverified":True,
    "historical_20_external_inputs_reexecuted":False,
    "go_producer_reference":ref(P.parent.parent/"native_migration_harness_error_revision_codex/e57c696eaf418862f0eb721ec8c8/candidate-root/internal/domain/native_migration_authority_harness_windows_test.go"),
    "review_origin":"Root assigned actual direct-final JSON publication race; prior package remains immutable",
    "no_new_mechanical_failure_observed_during_construction":True})
print(json.dumps({"source_root":str(P),"controller":ref(P/"root_native_migration_controller.py"),
 "observer":ref(P/"windows_owned_observed.py"),"changed_functions":sorted(changed),
 "inverse_raw_equal":True,"prior_members_reverified":len(manifest["members"])},ensure_ascii=True))

