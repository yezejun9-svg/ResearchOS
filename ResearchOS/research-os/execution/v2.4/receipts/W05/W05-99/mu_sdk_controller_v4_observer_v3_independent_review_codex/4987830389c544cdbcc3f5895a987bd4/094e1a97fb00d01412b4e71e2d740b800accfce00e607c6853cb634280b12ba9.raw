"""Two canonical JSON files under mandatory Windows file sharing ownership.

Both existing files remain exclusively open across read, compare and write.
The durable intent records both before and after documents. A failed write
leaves its exact partial state for Root reconciliation; no inverse is automatic.
"""
import ctypes, hashlib, json, os, uuid
from ctypes import wintypes
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
PATHS=(ROOT/"execution/v2.4/checkpoint.json",ROOT/"execution/v2.4/path_ownership.json")
MAX_BYTES=16*1024*1024
def pin_raw(path,raw):
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode()
def exclusive(path,raw):
    with Path(path).open("xb") as out:
        out.write(raw);out.flush();os.fsync(out.fileno())
    return pin_raw(path,raw)
def update_pair(expected_refs,transform,journal_dir,operation):
    if os.name!="nt":raise RuntimeError("Windows mandatory file ownership required")
    if len(expected_refs)!=2 or any(Path(ref["path"])!=path for ref,path in zip(expected_refs,PATHS)):
        raise RuntimeError("exact canonical pair required")
    journal_dir=Path(journal_dir)
    if not journal_dir.is_absolute() or not journal_dir.is_dir():raise RuntimeError("existing absolute transaction journal required")
    if operation not in ("activate","close"):raise RuntimeError("unknown canonical transaction")
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    HANDLE=ctypes.c_void_p;DWORD=wintypes.DWORD;BOOL=wintypes.BOOL
    def bind(name,args,result):
        f=getattr(k,name);f.argtypes=args;f.restype=result;return f
    create=bind("CreateFileW",[wintypes.LPCWSTR,DWORD,DWORD,ctypes.c_void_p,DWORD,DWORD,HANDLE],HANDLE)
    close=bind("CloseHandle",[HANDLE],BOOL)
    size=bind("GetFileSizeEx",[HANDLE,ctypes.POINTER(ctypes.c_longlong)],BOOL)
    seek=bind("SetFilePointerEx",[HANDLE,ctypes.c_longlong,ctypes.POINTER(ctypes.c_longlong),DWORD],BOOL)
    read=bind("ReadFile",[HANDLE,ctypes.c_void_p,DWORD,ctypes.POINTER(DWORD),ctypes.c_void_p],BOOL)
    write=bind("WriteFile",[HANDLE,ctypes.c_void_p,DWORD,ctypes.POINTER(DWORD),ctypes.c_void_p],BOOL)
    end=bind("SetEndOfFile",[HANDLE],BOOL);flush=bind("FlushFileBuffers",[HANDLE],BOOL)
    final_path=bind("GetFinalPathNameByHandleW",[HANDLE,wintypes.LPWSTR,DWORD,DWORD],DWORD)
    handles=[];before=[];after=[];error=None;written=[];journal=journal_dir/(operation+".transaction."+uuid.uuid4().hex)
    def checked(ok):
        if not ok:raise ctypes.WinError(ctypes.get_last_error())
    def raw_read(handle):
        length=ctypes.c_longlong();checked(size(handle,ctypes.byref(length)))
        if not 0<length.value<=MAX_BYTES:raise RuntimeError("canonical length outside bounded range")
        checked(seek(handle,0,None,0));chunks=[];remaining=length.value
        while remaining:
            count=min(remaining,1024*1024);buf=ctypes.create_string_buffer(count);got=DWORD()
            checked(read(handle,buf,count,ctypes.byref(got),None))
            if got.value==0:raise RuntimeError("canonical short read")
            chunks.append(buf.raw[:got.value]);remaining-=got.value
        return b"".join(chunks)
    try:
        # shareMode=0 denies another reader, writer, delete or atomic replacement
        # until both handles close. No check-then-replace window exists.
        for path in PATHS:
            handle=create(str(path),0x80000000|0x40000000,0,None,3,0x80,None)
            if handle==ctypes.c_void_p(-1).value or not handle:raise ctypes.WinError(ctypes.get_last_error())
            handles.append(handle)
            name=ctypes.create_unicode_buffer(32768);length=final_path(handle,name,len(name),0)
            if not 0<length<len(name):raise ctypes.WinError(ctypes.get_last_error())
            normalized=name.value.removeprefix("\\\\?\\")
            if Path(normalized)!=path:raise RuntimeError("canonical handle resolved outside exact target")
        before=[raw_read(h) for h in handles]
        if [pin_raw(p,b) for p,b in zip(PATHS,before)]!=expected_refs:
            raise RuntimeError("canonical expected bytes changed under exclusive ownership")
        result=transform(*[json.loads(b) for b in before])
        if type(result) not in (tuple,list) or len(result)!=2:raise RuntimeError("canonical transform must return pair")
        after=[encoded(v) for v in result]
        if any(len(b)>MAX_BYTES for b in after):raise RuntimeError("canonical output exceeds cap")
        journal.mkdir()
        before_refs=[exclusive(journal/(str(i)+".before.json"),b) for i,b in enumerate(before)]
        after_refs=[exclusive(journal/(str(i)+".after.proposed.json"),b) for i,b in enumerate(after)]
        exclusive(journal/"intent.json",encoded({"schema":"researchos.canonical-owned-pair-intent.v1",
            "before_refs":before_refs,"after_refs":after_refs,"expected_refs":expected_refs,
            "mandatory_share_mode":0,"automatic_inverse":False}))
        for i,(handle,raw) in enumerate(zip(handles,after)):
            checked(seek(handle,0,None,0));offset=0
            while offset<len(raw):
                chunk=raw[offset:offset+1024*1024];buf=ctypes.create_string_buffer(chunk);done=DWORD()
                checked(write(handle,buf,len(chunk),ctypes.byref(done),None))
                if done.value==0:raise RuntimeError("canonical short write")
                offset+=done.value
            checked(end(handle));checked(flush(handle));written.append(i)
        if [raw_read(h) for h in handles]!=after:raise RuntimeError("canonical owned write verification failed")
        refs=[pin_raw(p,b) for p,b in zip(PATHS,after)]
        exclusive(journal/"committed.json",encoded({"schema":"researchos.canonical-owned-pair-committed.v1",
            "after_refs":refs,"written_indices":written,"both_verified_while_exclusively_held":True}))
        return {"checkpoint_ref":refs[0],"ownership_ref":refs[1],"transaction_journal":str(journal)}
    except BaseException as exc:
        error=repr(exc)
        if journal.is_dir():
            partial=[]
            for handle,path in zip(handles,PATHS):
                try:partial.append(pin_raw(path,raw_read(handle)))
                except BaseException as read_error:partial.append({"path":str(path),"observation_error":repr(read_error)})
            exclusive(journal/"failed.partial.json",encoded({"exception":error,"written_indices":written,
                "observed_partial_refs":partial,"automatic_inverse":False,"requires_root_reconciliation":True}))
        raise
    finally:
        failures=[]
        for handle in reversed(handles):
            if not close(handle):failures.append(ctypes.get_last_error())
        if failures:raise RuntimeError("canonical ownership handle close failure: "+repr(failures))
