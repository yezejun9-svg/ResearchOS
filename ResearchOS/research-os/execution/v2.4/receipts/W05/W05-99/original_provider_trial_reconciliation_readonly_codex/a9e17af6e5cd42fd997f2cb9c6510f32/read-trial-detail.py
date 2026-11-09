import sys
sys.dont_write_bytecode=True
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import traceback

Q=Path(__file__).resolve().parent
B=Q.parent.parent
OPAQUE="cred-opencode_go-api_key-1791292735825831100-02e9207a-d97edec4"
spec=importlib.util.spec_from_file_location("trial_readonly_metadata_guard",Q/"guard-library.py")
util=importlib.util.module_from_spec(spec)
spec.loader.exec_module(util)

def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    with (Q/name).open("xb") as stream:
        assert stream.write(raw)==len(raw)
    return {"path":str(Q/name),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def metadata(value,pointer="",rows=None,refs=None):
    rows=[] if rows is None else rows
    refs=[] if refs is None else refs
    if util.public_ref(value):
        path=util.normalize(value["path"])
        if path.casefold().startswith(str(B).casefold()+os.sep) and not re.search(r"credential|dpapi|private|execute.?claim",path,re.I):
            refs.append({"pointer":pointer,"ref":{k:value[k] for k in ("path","sha256","bytes")},"resolved_public_path":path})
        return rows,refs
    if isinstance(value,dict):
        for key,child in value.items():
            lower=str(key).casefold()
            if re.search(r"password|authorization|bearer|secret|api.?key|private|lease.?token|execute.?claim",lower):
                if isinstance(child,(bool,int)) or child is None:
                    rows.append({"pointer":pointer+"/"+str(key),"value":child,"metadata_only":True})
                continue
            if "credential" in lower and isinstance(child,str):
                rows.append({"pointer":pointer+"/"+str(key),"matches_expected_opaque_ref":child==OPAQUE,
                    "opaque_ref":OPAQUE if child==OPAQUE else None})
                continue
            metadata(child,pointer+"/"+str(key),rows,refs)
    elif isinstance(value,list):
        for index,child in enumerate(value):
            metadata(child,pointer+"/"+str(index),rows,refs)
    else:
        if isinstance(value,str):
            if re.search(r"sk-[A-Za-z0-9]{8,}|Bearer\s+\S+|dpapi|privateclaim|credential-store|lease.?token",value,re.I):
                return rows,refs
            if len(value)>1800:
                return rows,refs
        if isinstance(value,int) and abs(value)>2**53:
            value=str(value)
        rows.append({"pointer":pointer,"value":value})
    return rows,refs

def main():
    assoc=json.loads((Q/"associated-public-records.json").read_text(encoding="utf-8"))
    allowed={"runtime-profile.actual-sealed.json","input.model-trial.actual.json","host.ready.json",
             "host.admitted.json","host-go.authority.json","root-host-go.json","host-go.once.json",
             "host-job.probe.json","host-job.contract.json","review.json","evidence-checks.json"}
    selected={}
    for item in assoc["associated_public_refs"]:
        path=item["resolved_public_path"]
        if Path(path).name in allowed and (
            "root-model-trial-v5" in path or "model_trial_failure745_component_review_codex" in path):
            selected[path.casefold()]=item
    assert {"runtime-profile.actual-sealed.json","input.model-trial.actual.json","review.json"}.issubset(
        {Path(item["resolved_public_path"]).name for item in selected.values()})
    guard=util.Guard(); closed=False
    documents=[]
    try:
        for item in selected.values():
            raw,pin=guard.read(item["resolved_public_path"],item["ref"])
            obj=json.loads(raw.decode("utf-8"))
            rows,refs=metadata(obj)
            documents.append({"source_ref":pin,"parent_ref":item["parent_ref"],"parent_pointer":item["pointer"],
                "safe_metadata":rows,"discovered_public_refs":refs,"raw_document_copied":False})
        result_ref=save("trial-detail-safe-metadata.json",{
            "authority":"NONE","documents":documents,"credential_ref":OPAQUE,
            "no_secret_or_private_values_exported":True,"privatefiles_databases_accounts_model_requests_opened":False})
        report=guard.close(); closed=True
        close_ref=save("trial-detail-source-guard.closed.json",report)
        print(json.dumps({"authority":"NONE","result_ref":result_ref,"source_guard_closed_ref":close_ref,
            "documents":[{"source_ref":x["source_ref"],"safe_metadata":x["safe_metadata"],
                "discovered_public_refs":x["discovered_public_refs"]} for x in documents]},ensure_ascii=False))
    finally:
        if not closed:
            for stream in guard.held:
                stream.close()

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
