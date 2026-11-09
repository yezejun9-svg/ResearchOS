"""Source-only Bridge03 two-finding repair; no bridge/runtime stage invocation."""
import ast,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'bridge-20261010-02';W=N.parent.parent
R=Path('D:/作品集/ResearchOS/research-os')
REVIEW=W/'w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-02'
PARENT=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
RP=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
subject=OLD/'w09_root_bridge.source.py'
assert ref(subject)['sha256']=='007dc1ffd8b446cdd164e3f822adf2fb4c41d1c41f18eb568d0d9d18756dfd2d'
assert ref(REVIEW/'HDF.json')['sha256']=='2be5bcd6c86aed41a3017a3b60bc04834497fece30db0ff3688c48a33c7c4583'
assert ref(REVIEW/'MF.json')['sha256']=='b7d5fadf9156d29d593266c5c723a7101c1a499f15a4f9734ec40b0b602de814'
assert ref(REVIEW/'decision.json')['sha256']=='a4ef7f94c0b801a2140321892aa7af009148608a0a567155fad91db00ce1ed82'
resource=ref(RP/'physical-C-native-v5-resource-parents.closed.root.json')
audit=ref(RP/'w09.physical-C-native-v5-resource-parent.actual-audit.root.json')
marker=ref(PARENT/'RESOURCE_OWNER.json')
assert (resource['sha256'],resource['bytes'])==('b85a53b28b489526cf7e7e68acb784ae0661283bea88b5e8c03e152e924ad698',2199)
assert (audit['sha256'],audit['bytes'])==('a5cd6eaa9c8880bfa9148cb9235fe92fc75f5af651ed2f045f6182962364751b',1103)
inputs=[ref(OLD/n) for n in ('HDF.json','MF.json','w09_root_bridge.source.py','ROOT_CALL_CONTRACT.md','delta-controls.json')]
inputs += [ref(REVIEW/n) for n in ('HDF.json','MF.json','decision.json','finite-review-controls.json')]
inputs += [resource,audit,marker,doc(Path(audit['path']))['original_capture_ref'],
 ref(R/'execution/v2.4/formal_profile_w09.py'),ref(R/'ops/ci/w09_evidence_closure.py'),ref(R/'execution/v2.4/formal_case_index.py')]
guardpath=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
raw=guardpath.read_bytes();assert hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
gm=types.ModuleType('bridge3_source_guard');gm.__file__=str(guardpath);exec(compile(raw,str(guardpath),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(total_cap=256*1024*1024);guard.acquire(inputs)
original=subject.read_bytes();source=original.decode();changes=[]
def change(a,b):
 global source
 assert source.count(a)==1,('EXACT_ONE_CHANGE',a[:120])
 source=source.replace(a,b);changes.append(dict(before=a,after=b))
helper='''
def environment_directory(value):
    """Only the fixed physical C parent is admissible as shared TEMP/TMP."""
    need(type(value) is str and value == str(PUBLIC_TEMP), "EXACT_SHARED_TEMP_PARENT")
    path = Path(value)
    need(path.is_absolute() and path.resolve(strict=True) == path, "ENVIRONMENT_PATH_ALIAS")
    for entry in (path, *path.parents):
        stat = entry.lstat()
        need(entry.is_dir() and not entry.is_symlink() and not entry.is_junction()
             and not (getattr(stat, "st_file_attributes", 0) & 0x400), "ENVIRONMENT_REPARSE")
    return path

def require_process_temp():
    """Fail before Main import or verification; never reset tempfile's cache."""
    parent = environment_directory(os.environ.get("TEMP"))
    need(environment_directory(os.environ.get("TMP")) == parent, "SAME_TEMP_TMP")
    import tempfile
    need(str(Path(tempfile.gettempdir())) == str(parent), "ACTUAL_PROCESS_TEMP_CACHE")
    return parent

def resource_environment():
    """Exact fixed resource metadata is read separately from general repo refs."""
    parent = environment_directory(str(PUBLIC_TEMP))
    resource = document(RESOURCE_PARENT_REF)
    need(resource["actor_id"] == ROOT_ACTOR and resource["resource_scope_only"] is True
         and resource["execution_grant"] is False and resource["RootScope_issued"] is False
         and resource["Native_calls"] == 0
         and resource["exact_parent_paths"] == [str(parent.parent), str(parent)]
         and resource["resource_owner_marker_ref"] == RESOURCE_OWNER_REF, "ROOT_RESOURCE_ONLY")
    marker = parent / "RESOURCE_OWNER.json"
    stat = marker.lstat()
    need(marker.resolve(strict=True) == marker and not marker.is_symlink() and not marker.is_junction()
         and not (getattr(stat, "st_file_attributes", 0) & 0x400), "RESOURCE_MARKER_ALIAS")
    raw = marker.read_bytes()
    need(RESOURCE_OWNER_REF == {"path":str(marker), "sha256":sha(raw), "bytes":len(raw)}, "RESOURCE_MARKER_PIN")
    need(decode(raw) == {"schema":"researchos.w09-native-private-resource-owner.v1",
         "project_id":"aede0678-7308-43dc-b9f2-cfe3d90cfdfb",
         "repository_root":str(ROOT), "scratch_parent":str(parent)}, "PROJECT_RESOURCE_OWNER")
    identity_ref = resource["project_identity_ref"]
    need(document(identity_ref)["project_id"] == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", "RESOURCE_PROJECT_IDENTITY")
    audit = document(RESOURCE_AUDIT_REF)
    need(audit["schema"] == "researchos.w09-native-producer.actual-audit.v1"
         and audit["actor_id"] == ROOT_ACTOR and audit["Root_thread_id"] == THREAD
         and audit["source_audit_path"] == ROOT_RESOURCE_AUDIT_PATH
         and audit["binding_sha256"] == RESOURCE_PARENT_REF["sha256"], "ROOT_RESOURCE_ACTUAL_BINDING")
    lines = checked(audit["original_capture_ref"]).splitlines(keepends=True)
    need(len(lines) == 3 and all(line.endswith(b"\\n") for line in lines), "THREE_RESOURCE_ORIGINAL_LINES")
    header, call, result = [decode(line) for line in lines]
    first, last = call.get("payload", {}), result.get("payload", {})
    need(header.get("type") == "session_meta" and header.get("ordinal") == 0
         and header.get("payload", {}).get("id") == THREAD
         and call.get("type") == result.get("type") == "response_item"
         and type(call.get("ordinal")) is int and type(result.get("ordinal")) is int
         and 0 < call["ordinal"] < result["ordinal"]
         and first.get("type") in ("function_call", "custom_tool_call")
         and last.get("type") in ("function_call_output", "custom_tool_call_output")
         and type(first.get("call_id")) is str and bool(first["call_id"])
         and first["call_id"] == last.get("call_id")
         and RESOURCE_PARENT_REF["sha256"] in lines[1].decode("utf-8")+lines[2].decode("utf-8"),
         "ROOT_RESOURCE_ACTUAL_TOOL_PAIR")
    offsets, digests = audit["source_line_offsets"], audit["original_line_sha256"]
    size = audit["source_prefix_size_observed"]
    need(type(offsets) is list and len(offsets) == 3 and offsets == sorted(set(offsets))
         and offsets[0] == 0 and all(type(x) is int and x >= 0 for x in offsets)
         and type(digests) is list and len(digests) == 3 and type(size) is int and size > 0,
         "RESOURCE_AUDIT_RANGES")
    ranges = []
    with Path(ROOT_RESOURCE_AUDIT_PATH).open("rb") as stream:
        for offset, digest, line in zip(offsets, digests, lines):
            need(offset+len(line) <= size and sha(line) == digest, "RESOURCE_AUDIT_DIGEST")
            stream.seek(offset)
            need(stream.read(len(line)) == line, "ACTUAL_ROOT_RESOURCE_BYTES")
            ranges.append({"path":ROOT_RESOURCE_AUDIT_PATH,"offset":offset,"bytes":len(line),"sha256":digest})
    return {"refs":[RESOURCE_PARENT_REF, RESOURCE_AUDIT_REF, RESOURCE_OWNER_REF,
                    identity_ref, audit["original_capture_ref"]], "audit_ranges":ranges}

def environment_request(req):
    need(req["bridge_temp_parent"] == str(PUBLIC_TEMP)
         and req["resource_parent_ref"] == RESOURCE_PARENT_REF
         and req["resource_audit_ref"] == RESOURCE_AUDIT_REF
         and req["resource_owner_sha256"] == RESOURCE_OWNER_REF["sha256"], "ROOT_REQUEST_RESOURCE_BINDING")
    require_process_temp()
    return resource_environment()

'''
launcher='''"""One finite consumer process: validate environment, then execute unchanged dispatcher."""
import hashlib
from pathlib import Path
import sys
import types

def main(args):
    if len(args) != 5:
        raise ValueError("SOURCE_PIN_AND_EXACT_ROUTE_REQUIRED")
    source = Path(__file__).resolve().parent / "w09_root_bridge.source.py"
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args[0] or len(raw) != int(args[1]):
        raise ValueError("BRIDGE_SOURCE_PIN")
    bridge = types.ModuleType("bridge03_consumer_environment")
    bridge.__file__ = str(source)
    exec(compile(raw, str(source), "exec"), bridge.__dict__)
    route = tuple(args[2:])
    bridge.need(route in bridge.ROUTES, "EXACT_CONSUMER_ROUTE")
    bridge.require_process_temp()
    bridge.resource_environment()
    dispatcher = bridge.ROOT / "execution/command_dispatcher/dispatch.py"
    observed = bridge.pin(dispatcher)
    bridge.need((observed["sha256"], observed["bytes"]) == bridge.TRUSTED[
        "execution/command_dispatcher/dispatch.py"], "PINNED_MAIN_DISPATCHER")
    # Dispatch retains its exact module/file and product argv; no Main bytes change.
    sys.argv = [str(dispatcher), route[0], "--task-id", "W09",
                "--check-id" if route[1] else "--case-id", route[1] or route[2], "--spec", "v2.4"]
    sys.path.insert(0, str(dispatcher.parent))
    import runpy
    runpy.run_path(str(dispatcher), run_name="__main__")

if __name__ == "__main__":
    main(sys.argv[1:])
'''
try:
 constants='\nAUTHOR_BACKEND = "/root/attach_restore_independent_review"\nBRIDGE_GENERATION = "bridge-20261010-03"\nPUBLIC_TEMP = Path(r"C:\\Users\\yqyyds\\.researchos\\w09-native-v5")\n'
 constants+='RESOURCE_PARENT_REF = '+repr(resource)+'\nRESOURCE_AUDIT_REF = '+repr(audit)+'\nRESOURCE_OWNER_REF = '+repr(marker)+'\n'
 constants+='ROOT_RESOURCE_AUDIT_PATH = '+repr(doc(Path(audit['path']))['source_audit_path'])+'\n'
 change('AUTHOR = "codex:/root/attach_restore_independent_review"\n','AUTHOR = "codex:/root/attach_restore_independent_review"\n'+constants)
 change('def engine():\n',helper+'\ndef engine():\n')
 change('review.get("reviewer_id") not in {AUTHOR, ROOT_ACTOR}','review.get("reviewer_id") not in {AUTHOR, AUTHOR_BACKEND, ROOT_ACTOR, "/root"}')
 change('    checked(req["bridge_source_ref"])\n    proof = req["source_review_audit"]\n','''    checked(req["bridge_source_ref"])
    need(AUTHOR == "codex:" + AUTHOR_BACKEND, "FIXED_SOURCE_BACKEND_IDENTITY")
    need(physical(req["consumer_launcher_ref"]["path"]) == HERE / "consumer_launch.source.py"
         and review.get("consumer_launcher_ref") == req["consumer_launcher_ref"], "REVIEWED_CONSUMER_LAUNCHER")
    checked(req["consumer_launcher_ref"])
    need(physical(req["source_hdf_ref"]["path"]) == HERE / "HDF.json"
         and physical(req["source_mf_ref"]["path"]) == HERE / "MF.json"
         and review.get("source_hdf_ref") == req["source_hdf_ref"]
         and review.get("source_mf_ref") == req["source_mf_ref"], "SOURCE_PACKAGE_REVIEW_BINDING")
    handoff, manifest = document(req["source_hdf_ref"]), document(req["source_mf_ref"])
    need(handoff["source_ref"] == req["bridge_source_ref"]
         and handoff["consumer_launcher_ref"] == req["consumer_launcher_ref"]
         and handoff["source_author"] == AUTHOR and handoff["source_author_backend"] == AUTHOR_BACKEND
         and req["bridge_source_ref"] in manifest["members"]
         and req["consumer_launcher_ref"] in manifest["members"], "SOURCE_PACKAGE_MEMBERS")
    proof = req["source_review_audit"]
''')
 change('    cp, ow, ss, cm = current4(req["current4"])\n','    environment = environment_request(req)\n    cp, ow, ss, cm = current4(req["current4"])\n')
 change('    api, reader, profile = engine()\n    source_review(req, api, reader, profile)\n','    api, reader, profile = engine()\n    reader.w09_audit_ranges.extend(environment["audit_ranges"])\n    source_review(req, api, reader, profile)\n')
 change('"source_actor": AUTHOR, "source_ref": req["bridge_source_ref"],','"source_actor": AUTHOR_BACKEND, "source_author_canonical": AUTHOR,\n              "generation": BRIDGE_GENERATION, "source_ref": req["bridge_source_ref"],\n              "source_hdf_ref": req["source_hdf_ref"], "source_mf_ref": req["source_mf_ref"],\n              "bridge_temp_parent": req["bridge_temp_parent"],\n              "resource_parent_ref": req["resource_parent_ref"], "resource_audit_ref": req["resource_audit_ref"],\n              "resource_owner_sha256": req["resource_owner_sha256"],')
 change('VERIFIER and AUTHOR in registry["roles"]["source_authors"]','VERIFIER and AUTHOR_BACKEND in registry["roles"]["source_authors"]\n         and AUTHOR not in registry["roles"]["source_authors"]')
 change('        for key in ("TEMP","TMP","USERPROFILE","LOCALAPPDATA","APPDATA"):\n','''        environment_request(req)
        for key in ("TEMP","TMP"):
            env[key] = str(environment_directory(req["isolated_environment"][key]))
        for key in ("USERPROFILE","LOCALAPPDATA","APPDATA"):
''')
 change('''        argv = [python["path"],"-I","-S","-B","-X","utf8",str(ROOT/"execution/command_dispatcher/dispatch.py"),
                route[0],"--task-id","W09","--check-id" if route[1] else "--case-id",route[1] or route[2],"--spec","v2.4"]
''','''        checked(req["consumer_launcher_ref"])
        argv = [python["path"],"-I","-S","-B","-X","utf8",str(HERE/"consumer_launch.source.py"),
                req["bridge_source_ref"]["sha256"],str(req["bridge_source_ref"]["bytes"]),*route]
''')
 change('    args=parser.parse_args(argv)\n    req,out,eng=root_request(','    args=parser.parse_args(argv)\n    require_process_temp()\n    req,out,eng=root_request(')
 change('        authority_snapshot = snapshot(eng[0],eng[1])\n','''        resource = environment_request(req)
        eng[1].w09_audit_ranges.extend(resource["audit_ranges"])
        # This single exact C marker is resource metadata, never a general checked/ref path.
        refs[RESOURCE_OWNER_REF["path"]] = dict(RESOURCE_OWNER_REF)
        for resource_ref in resource["refs"]:
            if resource_ref == RESOURCE_OWNER_REF:
                continue
            raw = checked(resource_ref)
            refs[str(physical(resource_ref["path"]))] = {"path":str(physical(resource_ref["path"])),
                "sha256":resource_ref["sha256"],"bytes":len(raw)}
        authority_snapshot = snapshot(eng[0],eng[1])
''')
 change('        result=STAGES[args.stage](req,out,eng)\n','        environment_request(req)\n        result=STAGES[args.stage](req,out,eng)\n')
 restored=source
 for edit in reversed(changes):
  assert restored.count(edit['after'])==1
  restored=restored.replace(edit['after'],edit['before'])
 assert restored.encode()==original,'COMPLETE_EXACT_SOURCE_INVERSE'
 ast.parse(source);ast.parse(launcher)
 (N/'w09_root_bridge.source.py').write_bytes(source.encode())
 (N/'consumer_launch.source.py').write_text(launcher,encoding='utf-8',newline='\n')
 put(N/'exact-inverse.json',dict(base_ref=ref(subject),source_ref=ref(N/'w09_root_bridge.source.py'),changes=changes,
  complete_original_byte_inverse=True,added_launcher_ref=ref(N/'consumer_launch.source.py')))
 put(N/'source-inputs.json',dict(references=inputs,task98_decision_ref=ref(REVIEW/'decision.json'),
  fixes=['BRIDGE-ROLE-001','BRIDGE-TEMP-002'],resource_parent_ref=resource,resource_audit_ref=audit,resource_owner_ref=marker))
finally:
 closed=guard.close();put(N/'source-guard.closed.json',closed)
 assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
print(json.dumps(dict(status='BRIDGE03_SOURCE_BUILT',source_ref=ref(N/'w09_root_bridge.source.py'),launcher_ref=ref(N/'consumer_launch.source.py'),changes=len(changes)),ensure_ascii=False))

