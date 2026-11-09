import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent
B = Q.parent.parent
S = B/"native_migration_harness_error_revision_codex"/"e57c696eaf418862f0eb721ec8c8"
F = B/"integration_codex"/"native-temp-failed-root-release-1791509915469"/"failure-origin.868.json"

def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path":str(path), "sha256":hashlib.sha256(raw).hexdigest(), "bytes":len(raw)}

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
    with (Q/name).open("xb") as stream:
        assert stream.write(raw) == len(raw)

def main():
    hdf_ref, mf_ref = ref(S/"HDF.json"), ref(S/"MF.json")
    hdf = json.loads((S/"HDF.json").read_text(encoding="utf-8"))
    mf = json.loads((S/"MF.json").read_text(encoding="utf-8"))
    assert isinstance(mf["members"], dict), "actual base MF members shape"
    members = []
    for name, pin in mf["members"].items():
        relative = Path(name)
        assert not relative.is_absolute() and ".." not in relative.parts
        actual = ref(S/relative)
        assert (actual["sha256"],actual["bytes"]) == (pin["sha256"],pin["bytes"]), "base MF member differs"
        members.append(dict(actual, relative_path=name))
    base_ref = ref(S/"root_only_native_broker.py")
    assert (base_ref["sha256"],base_ref["bytes"]) == ("5f3b4e957d85aeb091a2a801d72bcbf2afb2135c42e0a0a86fc740ff9f99750e",6201)
    assert "root_only_native_broker.py" in mf["members"]
    source = (S/"root_only_native_broker.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    failure_ref = ref(F)
    assert (failure_ref["sha256"],failure_ref["bytes"]) == ("d545edd01777e2866398e07c718da61c36d17f1cbd4b68647c7a16dc3309acdf",2714)
    failure = json.loads(F.read_text(encoding="utf-8"))
    assert failure["ordinal"] == 868
    snapshots = []
    target = Q/"inputs"/"base"
    target.mkdir(parents=True, exist_ok=False)
    for name in ("HDF.json","MF.json","root_only_native_broker.py","CONTRACT.md",
                 "guard-cases.json","program-provenance.json","revision-input-pins.json"):
        raw = (S/name).read_bytes()
        with (target/name).open("xb") as stream:
            assert stream.write(raw) == len(raw)
        snapshots.append({"source_ref":ref(S/name),"snapshot_ref":ref(target/name)})
    history = Q/"inputs"/"history"
    history.mkdir(exist_ok=False)
    with (history/"failure-origin.868.json").open("xb") as stream:
        raw = F.read_bytes()
        assert stream.write(raw) == len(raw)
    snapshots.append({"source_ref":failure_ref,"snapshot_ref":ref(history/"failure-origin.868.json")})
    result = {"authority":"NONE","formal_acceptance":False,
        "base_HDF_ref":hdf_ref,"base_MF_ref":mf_ref,"base_ref":base_ref,
        "actual_base_MF_shape":"dict keyed by relative member path",
        "all_base_MF_member_refs_verified":members,"actual_base_member_count":len(members),
        "base_HDF_schema":hdf.get("schema"),"base_MF_schema":mf.get("schema"),
        "failure868_ref":failure_ref,"snapshots":snapshots,
        "original_trial_private_files_read":False,"new_mechanical_errors":0,
        "broker_imported_or_main_called":False,"Go_SQL_native_pipe_crypto_model_execution":None}
    save("inspection.json", result)
    print(json.dumps({"authority":"NONE","base_HDF_ref":hdf_ref,"base_MF_ref":mf_ref,
        "base_ref":base_ref,"actual_base_member_count":len(members),
        "top_level_nodes":[{"name":node.name,"line":node.lineno,"end_line":node.end_lineno}
            for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))],
        "full_pinned_public_broker_source":source,
        "failure868_public_receipt":failure,
        "broker_executed":False}, ensure_ascii=False))

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
