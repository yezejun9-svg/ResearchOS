import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
S=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/native_migration_atomic_publication_revision_codex/1a11d9c912f7c13799a37e93")
E=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491")
def ref(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def snapshot(p,relative):
    dest=Q/relative; dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("xb") as f: f.write(Path(p).read_bytes())
    return {"source_ref":ref(p),"snapshot_ref":ref(dest)}
def main():
    hdf=json.loads((S/"HDF.json").read_text(encoding="utf-8")); mf=json.loads((S/"MF.json").read_text(encoding="utf-8"))
    refs=[]
    for relative,item in mf["members"].items():
        actual=ref(S/relative)
        assert (actual["sha256"],actual["bytes"])==(item["sha256"],item["bytes"]),"CTL2 MF mismatch: "+relative
        refs.append(actual)
    assert (ref(S/"MF.json")["sha256"],ref(S/"MF.json")["bytes"])==(hdf["manifest_ref"]["sha256"],hdf["manifest_ref"]["bytes"])
    source=S/"root_native_migration_controller.py"
    assert (ref(source)["sha256"],ref(source)["bytes"])==("14cba01f91b7d9f322243c0df041a29337c422f72ea96214337047522dec8c83",40404)
    for name,digest,length in [("HDF.json","e9dab1b8ca436384733a256501aa21ca2a1b3429859a80368810cc65b741ed2b",7028),
                               ("MF.json","c3f3e98bee9a3f2879b1cf07ca49927f9c894bed4534aaa38f2775d514bec301",10617)]:
        actual=ref(E/name); assert (actual["sha256"],actual["bytes"])==(digest,length)
    text=source.read_text(encoding="utf-8"); lines=text.splitlines(); tree=ast.parse(text)
    selected=[]
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
            segment=ast.get_source_segment(text,n)
            if any(x in segment for x in ["ENV_KEYS","Environment","DataRoot","SourceGuard","source_guard"]):
                selected.append({"name":n.name,"line":n.lineno,"end_line":n.end_lineno,
                                 "source":segment})
    global_lines=[{"line":n+1,"text":line} for n,line in enumerate(lines[:130])]
    snapshots=[]
    for name in ["HDF.json","MF.json","CONTRACT.md","root-controller-api.json","root_native_migration_controller.py","windows_owned_observed.py","public-input-pins.json"]:
        snapshots.append(snapshot(S/name,"inputs/CTL2/"+name))
    for name in ["HDF.json","MF.json","CONTRACT.md","public-environment-contract.json"]:
        snapshots.append(snapshot(E/name,"inputs/EnvSource/"+name))
    output={"authority":"NONE","CTL2_HDF_ref":ref(S/"HDF.json"),"CTL2_MF_ref":ref(S/"MF.json"),
            "base_controller_ref":ref(source),"CTL2_member_refs_verified":refs,
            "EnvSource_HDF_ref":ref(E/"HDF.json"),"EnvSource_MF_ref":ref(E/"MF.json"),
            "snapshots":snapshots,"globals":global_lines,"selected_source_nodes":selected,
            "controller_observer_imported":False,"Go_native_SQL_crypto_model_execution":None}
    (Q/"inspection.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    shown={k:v for k,v in output.items() if k not in ["snapshots","CTL2_member_refs_verified","selected_source_nodes"]}
    shown["selected_source_node_index"]=[{k:v for k,v in n.items() if k!="source"} for n in selected]
    indices=set()
    for n,line in enumerate(lines):
        if "ENV_KEYS" in line or "Environment" in line or "DataRoot" in line:
            indices.update(range(max(0,n-3),min(len(lines),n+12)))
    shown["context_environment_windows"]=[{"line":n+1,"text":lines[n]} for n in sorted(indices)]
    print(json.dumps(shown,ensure_ascii=False))
code=0
try: main()
except Exception: traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

