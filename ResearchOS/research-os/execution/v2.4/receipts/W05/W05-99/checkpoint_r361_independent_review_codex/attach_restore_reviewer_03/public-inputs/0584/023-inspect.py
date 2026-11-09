import sys
sys.dont_write_bytecode = True
import hashlib
import json
import traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
S=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/native_migration_credential_ttl_revision_codex/1a11dd62452c7c895d4e2f51")
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-compile-root-458f017f3c294bb6")
T=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-ttl-c54ba9df088e45ea94adb56457af2979")
NAME="native_migration_authority_harness_windows_test.go"
def ref(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
def copy(p,relative):
    dest=Q/relative; dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("xb") as f: f.write(Path(p).read_bytes())
    return {"source_ref":ref(p),"snapshot_ref":ref(dest)}
def main():
    hdf=json.loads((S/"HDF.json").read_text(encoding="utf-8"))
    mf=json.loads((S/"MF.json").read_text(encoding="utf-8"))
    checked=[]
    for relative,item in mf["members"].items():
        actual=ref(S/relative)
        assert actual["sha256"]==item["sha256"] and actual["bytes"]==item["bytes"], "TTL source member differs: "+relative
        checked.append({"relative_path":relative,"declared_path":item["path"],"actual_ref":actual})
    assert ref(S/"MF.json")["sha256"]==hdf["manifest_ref"]["sha256"]
    assert ref(S/"MF.json")["bytes"]==hdf["manifest_ref"]["bytes"]
    source=T/"internal/domain"/NAME
    base=ref(source)
    ttl_equals_formatted_T7 = base["sha256"]==hdf["source_ref"]["sha256"] and base["bytes"]==hdf["source_ref"]["bytes"]
    closed=json.loads((C/"validation.closed.json").read_text(encoding="utf-8"))
    formatted=json.loads((C/"formatted.source-members.json").read_text(encoding="utf-8"))
    inventory=json.loads((C/"actual-tagged-compiler-input-inventory.json").read_text(encoding="utf-8"))
    closed_ref_records=[x for x in walk(closed) if "sha256" in x and "bytes" in x]
    binding={}
    for name in ["formatted.source-members.json","actual-tagged-compiler-input-inventory.json"]:
        actual=ref(C/name)
        matches=[x for x in closed_ref_records if x.get("sha256")==actual["sha256"] and x.get("bytes")==actual["bytes"]]
        binding[name]={"actual_ref":actual,"closed_matching_refs":matches}
    def matching_source_rows(obj):
        return [x for x in walk(obj) if x.get("sha256")==base["sha256"] and x.get("bytes")==base["bytes"]]
    fm=matching_source_rows(formatted); cm=matching_source_rows(inventory)
    snapshots=[]
    for name in ["HDF.json","MF.json","CONTRACT.md","static-evidence.json","public-input-pins.json"]:
        snapshots.append(copy(S/name,"inputs/ttl-source/"+name))
    for name in ["validation.closed.json","formatted.source-members.json","actual-tagged-compiler-input-inventory.json"]:
        snapshots.append(copy(C/name,"inputs/compile/"+name))
    snapshots.append(copy(source,"inputs/T7/"+NAME))
    backup=T/"internal/domain/backup_prepared_abandonment_upgrade.go"
    snapshots.append(copy(backup,"inputs/T7/backup_prepared_abandonment_upgrade.go"))
    lines=source.read_text(encoding="utf-8").splitlines()
    indices=set()
    for n,line in enumerate(lines):
        if any(anchor in line for anchor in ["TEMP","TMP","SystemRoot","publicEnvironment","Environment","func nativeHarnessBroker","type nativeHarness"]):
            indices.update(range(max(0,n-3),min(len(lines),n+21)))
    backup_lines=backup.read_text(encoding="utf-8").splitlines()
    bi=set()
    for n,line in enumerate(backup_lines):
        if "MkdirTemp" in line: bi.update(range(max(0,n-7),min(len(backup_lines),n+8)))
    output={"authority":"NONE","base_ref":base,"TTL_HDF_ref":ref(S/"HDF.json"),"TTL_MF_ref":ref(S/"MF.json"),"TTL_candidate_equals_formatted_T7":ttl_equals_formatted_T7,
            "TTL_member_checks":checked,"compile_closed_ref":ref(C/"validation.closed.json"),
            "compile_closed_top_keys":list(closed),"compile_closed_scalar_fields":{k:v for k,v in closed.items() if not isinstance(v,(dict,list))},
            "compile_bindings":binding,"formatted_source_matches":fm,"compiler_inventory_source_matches":cm,
            "snapshots":snapshots,
            "Source_contract_lines":[{"line":n+1,"text":lines[n]} for n in sorted(indices)],
            "backup_MkdirTemp_lines":[{"line":n+1,"text":backup_lines[n]} for n in sorted(bi)],
            "Go_SQL_native_model_execution":None,"mechanical_failures_this_branch":0}
    (Q/"inspection.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in output.items() if k not in ["snapshots","TTL_member_checks"]},ensure_ascii=False))
code=0
try: main()
except Exception:
    traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

