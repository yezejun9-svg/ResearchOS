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
P=B/"original_provider_public_audit_resource_codex"/"opa-01a11f3f"
OPAQUE="cred-opencode_go-api_key-1791292735825831100-02e9207a-d97edec4"
spec=importlib.util.spec_from_file_location("trial_readonly_finite_guard",Q/"guard-library.py")
util=importlib.util.module_from_spec(spec)
spec.loader.exec_module(util)
REDACTIONS=[]

def safe(value,pointer=""):
    if isinstance(value,dict):
        result={}
        for key,child in value.items():
            lower=str(key).casefold()
            if re.search(r"api.?key|authorization|bearer|private.?input|private.?buffer|secret.?value|password|credential.?value|access.?token",lower):
                REDACTIONS.append(pointer+"/"+str(key))
                result[key]="PRIVATE_VALUE_NOT_EXPORTED"
            elif "credential" in lower and isinstance(child,str) and child!=OPAQUE:
                REDACTIONS.append(pointer+"/"+str(key))
                result[key]="OPAQUE_OTHER_CREDENTIAL_NOT_EXPORTED"
            else:
                result[key]=safe(child,pointer+"/"+str(key))
        return result
    if isinstance(value,list):
        return [safe(child,pointer+"/"+str(index)) for index,child in enumerate(value)]
    if isinstance(value,str):
        if re.search(r"sk-[A-Za-z0-9]{8,}|Bearer\s+[A-Za-z0-9._-]{8,}",value):
            REDACTIONS.append(pointer)
            return "AUTH_TEXT_NOT_EXPORTED"
        if re.search(r"dpapi|execute.?claim|private.resource|credential-store|credentials[\\/]",value,re.I):
            REDACTIONS.append(pointer)
            return "PRIVATE_RESOURCE_REFERENCE_NOT_EXPORTED_OR_OPENED"
        return value
    return value

def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    with (Q/name).open("xb") as stream:
        assert stream.write(raw)==len(raw)
    return {"path":str(Q/name),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def main():
    discovery=json.loads((Q/"discovery.json").read_text(encoding="utf-8"))
    guard=util.Guard(); closed=False
    documents=[]
    try:
        selected=[]
        for row in discovery["registered_relevant_public_refs"]:
            path=row["resolved_public_path"]
            if ("integration_codex"+os.sep+"root-model-trial-v5-870ecc93e109c85ee985e1566ff"+os.sep in path
                or "model_trial_failure745_component_review_codex"+os.sep in path):
                if Path(path).name!="failure-origin.746.json":
                    selected.append((Path(path).name,row["registered_ref"],row["checkpoint_pointers"]))
        assert len(selected)==4,"actual Original Root trial + independent handoff/business pins expected"
        hraw,href=guard.read(P/"HDF.json",discovery["canonical_public_audit_HDF_ref"])
        hdf=json.loads(hraw.decode("utf-8"))
        mraw,mref=guard.read(P/"MF.json",discovery["canonical_public_audit_MF_ref"])
        mf=json.loads(mraw.decode("utf-8"))
        assert isinstance(mf["members"],list)
        member_refs=[]
        for member in mf["members"]:
            if util.public_ref(member):
                member_refs.append({key:member[key] for key in ("path","sha256","bytes")})
            elif util.public_ref(member.get("ref")):
                member_refs.append({key:member["ref"][key] for key in ("path","sha256","bytes")})
        assert member_refs,"actual public MF reference shape"
        for field in ("report_ref","result_ref","sources_ref"):
            pin=hdf[field]
            assert util.public_ref(pin)
            assert any((util.normalize(v["path"]).casefold(),v["sha256"].removeprefix("sha256:"),v["bytes"])==
                       (util.normalize(pin["path"]).casefold(),pin["sha256"].removeprefix("sha256:"),pin["bytes"])
                       for v in member_refs),"public HDF selected ref must match MF"
            selected.append((field,pin,["OPA_HDF/"+field]))
        assoc=[]
        for label,pin,pointers in selected:
            path=Path(util.normalize(pin["path"]))
            assert str(path).casefold().startswith(str(B).casefold()+os.sep)
            assert not re.search(r"credential|dpapi|execute.?claim|private.resource",str(path),re.I)
            raw,actual=guard.read(path,pin)
            text=raw.decode("utf-8")
            if path.suffix.casefold()==".json":
                obj=json.loads(text)
                projection=safe(obj)
                def walk(value,pointer):
                    if util.public_ref(value):
                        public_path=util.normalize(value["path"])
                        if public_path.casefold().startswith(str(B).casefold()+os.sep):
                            if not re.search(r"credential|dpapi|execute.?claim|private.resource",public_path,re.I):
                                assoc.append({"parent_ref":actual,"pointer":pointer,
                                    "ref":{key:value[key] for key in ("path","sha256","bytes")},
                                    "resolved_public_path":public_path})
                    if isinstance(value,dict):
                        for key,child in value.items():
                            walk(child,pointer+"/"+str(key))
                    elif isinstance(value,list):
                        for index,child in enumerate(value):
                            walk(child,pointer+"/"+str(index))
                walk(obj,"")
            else:
                projection={"public_report_text":safe(text)}
            output_ref=save("projection-"+label.replace(".","-")+".json",
                {"source_ref":actual,"source_pointers":pointers,"projection":projection,
                 "raw_Source_copied":False,"redactions_apply_to_private_or_auth_text":True})
            documents.append({"label":label,"source_ref":actual,"projection_ref":output_ref})
        cp_raw,cp_ref=guard.read(util.CP,{"sha256":util.CP_HASH,"bytes":util.CP_BYTES})
        cp=json.loads(cp_raw.decode("utf-8"))
        selected_wip={}
        for key,value in cp.get("work_in_progress",{}).items():
            if re.search(r"actual_model_trial|billing|provider_audit|provider_account|original_provider",str(key),re.I):
                selected_wip[key]=safe(value,"/work_in_progress/"+str(key))
        wip_ref=save("checkpoint-account-trial-scope.projection.json",{
            "checkpoint_ref":cp_ref,"work_in_progress_selected":selected_wip,"raw_checkpoint_copied":False})
        result_ref=save("associated-public-records.json",{"authority":"NONE","documents":documents,
            "associated_public_refs":assoc,"public_audit_member_refs":member_refs,
            "checkpoint_scope_projection_ref":wip_ref,"redacted_JSON_pointers":sorted(set(REDACTIONS)),
            "credential_ref":OPAQUE,"raw_trial_documents_copied":False,
            "private_credentials_claims_account_model_requests_opened":False})
        guard_report=guard.close(); closed=True
        closed_ref=save("associated-source-guard.closed.json",guard_report)
        print(json.dumps({"authority":"NONE","associated_records_ref":result_ref,
            "source_guard_closed_ref":closed_ref,"documents":documents,
            "associated_public_ref_count":len(assoc),"OPA_actual_MF_member_count":len(member_refs),
            "checkpoint_scope_ref":wip_ref,"redaction_count":len(REDACTIONS)},ensure_ascii=False))
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
