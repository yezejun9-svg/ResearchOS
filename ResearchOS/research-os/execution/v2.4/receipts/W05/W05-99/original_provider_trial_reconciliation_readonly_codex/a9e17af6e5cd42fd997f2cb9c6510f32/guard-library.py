import sys
sys.dont_write_bytecode=True
import ctypes
from ctypes import wintypes
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import re
import traceback

Q=Path(__file__).resolve().parent
B=Q.parent.parent
R=B.parent.parent.parent.parent.parent
CP=R/"execution"/"v2.4"/"checkpoint.json"
P=B/"original_provider_public_audit_resource_codex"/"opa-01a11f3f"
CP_HASH="a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994"
CP_BYTES=4489310

def normalize(value):
    value=re.sub(r"\\u([0-9a-fA-F]{4})",lambda m:chr(int(m.group(1),16)),value)
    return str(Path(os.path.normpath(value.replace("\\","/"))))

def public_ref(value):
    if not isinstance(value,dict) or not all(k in value for k in ("path","sha256","bytes")):
        return False
    return isinstance(value["path"],str) and isinstance(value["sha256"],str) and isinstance(value["bytes"],int)

class Guard:
    def __init__(self):
        self.held=[]
        self.records=[]
    def read(self,path,pin=None):
        path=Path(path).resolve()
        api=ctypes.WinDLL("kernel32",use_last_error=True)
        api.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        api.CreateFileW.restype=wintypes.HANDLE
        handle=api.CreateFileW(str(path),0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        fd=msvcrt.open_osfhandle(int(handle),os.O_RDONLY|os.O_BINARY)
        stream=os.fdopen(fd,"rb")
        self.held.append(stream)
        before=os.fstat(stream.fileno())
        raw=stream.read()
        actual={"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
        if pin is not None:
            assert (actual["sha256"],actual["bytes"])==(pin["sha256"].removeprefix("sha256:"),pin["bytes"]),"registered public ref differs"
        self.records.append({"ref":actual,"volume_device_decimal":str(before.st_dev),
            "file_identity_decimal":str(before.st_ino),"mtime_ns_decimal":str(before.st_mtime_ns),
            "guard":"GENERIC_READ + FILE_SHARE_READ only; deny concurrent write/delete",
            "start_fstat":(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns),
            "stream_index":len(self.held)-1})
        return raw,actual
    def close(self):
        results=[]
        try:
            for record in self.records:
                stream=self.held[record["stream_index"]]
                stream.seek(0)
                raw=stream.read()
                after=os.fstat(stream.fileno())
                identity=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                assert identity==record["start_fstat"],"held public Source identity changed"
                assert hashlib.sha256(raw).hexdigest()==record["ref"]["sha256"],"held public Source bytes changed"
                item={k:v for k,v in record.items() if k not in ("start_fstat","stream_index")}
                item["end_identity_and_bytes_equal"]=True
                results.append(item)
        finally:
            for stream in self.held:
                stream.close()
        assert all(stream.closed for stream in self.held)
        return {"schema":"researchos.finite-readonly-source-guard.v1","records":results,
            "all_handles_closed":True,"holding_continues_after_process":False}

def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    with (Q/name).open("xb") as stream:
        assert stream.write(raw)==len(raw)
    return {"path":str(Q/name),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def main():
    guard=Guard()
    finished=False
    try:
        raw,cp_ref=guard.read(CP,{"sha256":CP_HASH,"bytes":CP_BYTES})
        cp=json.loads(raw.decode("utf-8"))
        refs=[]
        cp_public=normalize(str(B))+os.sep
        def walk(value,pointer):
            if public_ref(value):
                path=normalize(value["path"])
                lower=path.casefold()
                if lower.startswith(cp_public.casefold()) and re.search(r"original.?provider|opencode|paid|trial|billing|host.?capt|mu.sdk|musdk|model.resource|request.log",lower):
                    if not re.search(r"credential|dpapi|execute.?claim|private.resource|privateclaim",lower):
                        exact_ref={key:value[key] for key in ("path","sha256","bytes")}
                        refs.append({"checkpoint_pointer":pointer,"registered_ref":exact_ref,
                            "resolved_public_path":path})
            if isinstance(value,dict):
                for key,child in value.items():
                    walk(child,pointer+"/"+str(key).replace("~","~0").replace("/","~1"))
            elif isinstance(value,list):
                for index,child in enumerate(value):
                    walk(child,pointer+"/"+str(index))
        walk(cp,"")
        target=normalize(str(P/"HDF.json")).casefold()
        registered_hdf=[x for x in refs if x["resolved_public_path"].casefold()==target]
        assert registered_hdf,"exact canonical registered HDF ref required"
        pins={(v["registered_ref"]["sha256"],v["registered_ref"]["bytes"]) for v in registered_hdf}
        assert len(pins)==1,"canonical HDF pin variants conflict"
        hraw,href=guard.read(P/"HDF.json",registered_hdf[0]["registered_ref"])
        hdf=json.loads(hraw.decode("utf-8"))
        mraw,mref=guard.read(P/"MF.json")
        mf=json.loads(mraw.decode("utf-8"))
        exact_mf=[v for v in refs if v["resolved_public_path"].casefold()==normalize(str(P/"MF.json")).casefold()]
        if exact_mf:
            for value in exact_mf:
                pin=value["registered_ref"]
                assert (mref["sha256"],mref["bytes"])==(pin["sha256"].removeprefix("sha256:"),pin["bytes"])
        else:
            def hdf_pins(value):
                if public_ref(value) and normalize(value["path"]).casefold()==normalize(str(P/"MF.json")).casefold():
                    return [value]
                if isinstance(value,dict):
                    return [v for child in value.values() for v in hdf_pins(child)]
                if isinstance(value,list):
                    return [v for child in value for v in hdf_pins(child)]
                return []
            hp=hdf_pins(hdf)
            assert hp,"MF must have exact registered CP or HDF pin"
            assert all((p["sha256"].removeprefix("sha256:"),p["bytes"])==(mref["sha256"],mref["bytes"]) for p in hp)
        unique={}
        for item in refs:
            key=(item["resolved_public_path"].casefold(),item["registered_ref"]["sha256"],item["registered_ref"]["bytes"])
            if key not in unique:
                unique[key]=dict(item,checkpoint_pointers=[item["checkpoint_pointer"]])
            else:
                unique[key]["checkpoint_pointers"].append(item["checkpoint_pointer"])
        rows=list(unique.values())
        groups={}
        for item in rows:
            relative=Path(item["resolved_public_path"]).relative_to(B)
            prefix="/".join(relative.parts[:2])
            groups[prefix]=groups.get(prefix,0)+1
        output={"schema":"researchos.original-trial-public-ref-discovery.v1","authority":"NONE",
            "checkpoint_ref":cp_ref,"canonical_public_audit_HDF_ref":href,
            "canonical_public_audit_MF_ref":mref,"HDF_schema":hdf.get("schema"),"MF_schema":mf.get("schema"),
            "MF_members_shape":type(mf.get("members")).__name__,"MF_top_level_keys":sorted(mf),
            "HDF_top_level_keys":sorted(hdf),"registered_relevant_public_refs":rows,
            "groups":groups,"credential_ref":"cred-opencode_go-api_key-1791292735825831100-02e9207a-d97edec4",
            "private_credentials_account_login_database_model_requests_opened":False,
            "paid_requests_topups_account_changes":False}
        discovery_ref=save("discovery.json",output)
        guard_report=guard.close(); finished=True
        guard_ref=save("discovery-source-guard.closed.json",guard_report)
        print(json.dumps({"authority":"NONE","discovery_ref":discovery_ref,"guard_ref":guard_ref,
            "registered_public_ref_count":len(rows),"groups":groups,"HDF_ref":href,"MF_ref":mref,
            "MF_members_shape":output["MF_members_shape"],"HDF_top_level_keys":output["HDF_top_level_keys"],
            "MF_top_level_keys":output["MF_top_level_keys"]},ensure_ascii=False))
    finally:
        if not finished:
            for stream in guard.held:
                stream.close()
