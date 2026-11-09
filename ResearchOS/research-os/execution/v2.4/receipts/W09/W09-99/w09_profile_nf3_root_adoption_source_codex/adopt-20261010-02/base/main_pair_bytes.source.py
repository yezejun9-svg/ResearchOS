"""Future exact two-target Main adoption. Import performs no filesystem action.

This is separate from, and never changes, the accepted CP/OW transaction module.
Only the fixed profile and commands files can be opened for writing. Both remain
under shareMode=0 for the expected-byte comparison, durable intent, write and
readback. Failure preserves partial bytes; rollback and retry are never automatic.
"""
import ctypes
from ctypes import wintypes
import hashlib,json,os
from pathlib import Path

ROOT=Path(r'D:/作品集/ResearchOS/research-os')
TARGETS=(ROOT/'execution/v2.4/formal_profile_w09.py',ROOT/'execution/v2.4/commands.json')
MAX=16*1024*1024

def require(ok,code):
    if not ok:raise ValueError(code)

def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def pin_raw(path,raw):return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def write_new(path,raw):
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin_raw(path,raw)

def validate_pair_spec(expected_refs,after_bytes):
    require(type(expected_refs) in (tuple,list) and len(expected_refs)==2,'EXACT_TWO_EXPECTED_REFS')
    for ref,path in zip(expected_refs,TARGETS):
        require(type(ref) is dict and set(ref)=={'path','sha256','bytes'} and ref['path']==str(path)
                and type(ref['bytes']) is int and 0<ref['bytes']<=MAX
                and type(ref['sha256']) is str and len(ref['sha256'])==64
                and all(c in '0123456789abcdef' for c in ref['sha256']),'FIXED_MAIN_TARGET_REF')
    require(type(after_bytes) in (tuple,list) and len(after_bytes)==2
            and all(type(raw) is bytes and 0<len(raw)<=MAX for raw in after_bytes),'EXACT_TWO_AFTER_BYTES')

def intent_document(expected_refs,before_archive_refs,after_archive_refs):
    return dict(schema='researchos.w09-main-owned-bytes-intent.v1',expected_refs=expected_refs,
        before_archive_refs=before_archive_refs,after_archive_refs=after_archive_refs,
        target_order=[str(p) for p in TARGETS],mandatory_share_mode=0,
        complete_before_after_archives=True,automatic_inverse=False,automatic_retry=False)

def partial_document(primary,written,observations,secondary):
    return dict(schema='researchos.w09-main-owned-bytes-partial.v1',primary_exception=primary,
        written_indices=written,observed_partial=observations,secondary_errors=secondary,
        automatic_inverse=False,automatic_retry=False,requires_root_reconciliation=True)

class PairWriteFailure(RuntimeError):
    def __init__(self,primary,secondary,journal):
        self.primary=primary;self.secondary=secondary;self.journal=str(journal)
        super().__init__('MAIN_PAIR_FAILED_NO_AUTOMATIC_RETRY: '+repr(primary)+'; secondary='+repr(secondary))

def replace_exact_pair(expected_refs,after_bytes,journal_dir,validate_while_owned):
    """Only Root's already-registered caller may invoke this future write branch."""
    require(os.name=='nt','WINDOWS_MANDATORY_OWNERSHIP_REQUIRED')
    validate_pair_spec(expected_refs,after_bytes)
    require(callable(validate_while_owned),'OWNED_BOUNDARY_CALLBACK_REQUIRED')
    journal=Path(journal_dir)
    require(journal.is_absolute() and journal.parent.is_dir() and not journal.exists(),'FRESH_EXACT_MAIN_JOURNAL')
    for path in (*TARGETS,journal.parent):
        for ancestor in (path,*path.parents):
            require(not ancestor.is_symlink() and not ancestor.is_junction(),'NO_REPARSE_MAIN_TARGET')
        require(path.resolve(strict=True)==path,'NO_MAIN_PATH_ALIAS')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    HANDLE=ctypes.c_void_p;DWORD=wintypes.DWORD;BOOL=wintypes.BOOL
    def bind(name,args,result):
        f=getattr(kernel,name);f.argtypes=args;f.restype=result;return f
    create=bind('CreateFileW',[wintypes.LPCWSTR,DWORD,DWORD,ctypes.c_void_p,DWORD,DWORD,HANDLE],HANDLE)
    close=bind('CloseHandle',[HANDLE],BOOL)
    length=bind('GetFileSizeEx',[HANDLE,ctypes.POINTER(ctypes.c_longlong)],BOOL)
    seek=bind('SetFilePointerEx',[HANDLE,ctypes.c_longlong,ctypes.POINTER(ctypes.c_longlong),DWORD],BOOL)
    read=bind('ReadFile',[HANDLE,ctypes.c_void_p,DWORD,ctypes.POINTER(DWORD),ctypes.c_void_p],BOOL)
    write=bind('WriteFile',[HANDLE,ctypes.c_void_p,DWORD,ctypes.POINTER(DWORD),ctypes.c_void_p],BOOL)
    end=bind('SetEndOfFile',[HANDLE],BOOL);flush=bind('FlushFileBuffers',[HANDLE],BOOL)
    final=bind('GetFinalPathNameByHandleW',[HANDLE,wintypes.LPWSTR,DWORD,DWORD],DWORD)
    def checked(ok):
        if not ok:raise ctypes.WinError(ctypes.get_last_error())
    def read_owned(handle):
        n=ctypes.c_longlong();checked(length(handle,ctypes.byref(n)));require(0<=n.value<=MAX,'BOUNDED_OWNED_LENGTH')
        checked(seek(handle,0,None,0));left=n.value;out=[]
        while left:
            count=min(left,1024*1024);buf=ctypes.create_string_buffer(count);got=DWORD()
            checked(read(handle,buf,count,ctypes.byref(got),None));require(0<got.value<=count,'OWNED_SHORT_READ')
            out.append(buf.raw[:got.value]);left-=got.value
        return b''.join(out)
    handles=[];written=[];primary=None;secondary=[];result=None
    try:
        for path in TARGETS:
            handle=create(str(path),0x80000000|0x40000000,0,None,3,0x80,None)
            if not handle or handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
            handles.append(handle)
            name=ctypes.create_unicode_buffer(32768);got=final(handle,name,len(name),0)
            require(0<got<len(name) and Path(name.value.removeprefix('\\\\?\\'))==path,'EXACT_OWNED_MAIN_TARGET')
        before=[read_owned(h) for h in handles]
        require([pin_raw(p,b) for p,b in zip(TARGETS,before)]==list(expected_refs),'MAIN_EXPECTED_BYTES_DRIFT_UNDER_OWNERSHIP')
        # The callback rechecks the Root lease/current Canon and exact reviewed delta.
        validate_while_owned(before,after_bytes)
        journal.mkdir()
        before_refs=[write_new(journal/(str(i)+'.before.raw'),raw) for i,raw in enumerate(before)]
        after_refs=[write_new(journal/(str(i)+'.after.proposed.raw'),raw) for i,raw in enumerate(after_bytes)]
        write_new(journal/'intent.json',encoded(intent_document(expected_refs,before_refs,after_refs)))
        for i,(handle,raw) in enumerate(zip(handles,after_bytes)):
            checked(seek(handle,0,None,0));offset=0
            while offset<len(raw):
                part=raw[offset:offset+1024*1024];buf=ctypes.create_string_buffer(part);done=DWORD()
                checked(write(handle,buf,len(part),ctypes.byref(done),None));require(0<done.value<=len(part),'OWNED_SHORT_WRITE')
                offset+=done.value
            checked(end(handle));checked(flush(handle));written.append(i)
        require([read_owned(h) for h in handles]==list(after_bytes),'MAIN_READBACK_DRIFT')
        result=dict(after_refs=[pin_raw(p,b) for p,b in zip(TARGETS,after_bytes)],journal_dir=str(journal),
                    both_verified_while_exclusively_held=True,automatic_inverse=False)
        write_new(journal/'committed.while-owned.json',encoded(result))
    except BaseException as exc:
        primary=exc
        if journal.is_dir():
            observed=[]
            for i,(handle,path) in enumerate(zip(handles,TARGETS)):
                try:
                    raw=read_owned(handle);copy_ref=write_new(journal/(str(i)+'.partial.raw'),raw)
                    observed.append(dict(target_ref=pin_raw(path,raw),partial_archive_ref=copy_ref))
                except BaseException as e:observed.append(dict(path=str(path),observation_error=repr(e)))
            try:write_new(journal/'failed.partial.json',encoded(partial_document(repr(primary),written,observed,secondary)))
            except BaseException as e:secondary.append(dict(phase='partial-journal-publication',error=repr(e)))
    finally:
        for handle in reversed(handles):
            try:
                if not close(handle):raise ctypes.WinError(ctypes.get_last_error())
            except BaseException as e:secondary.append(dict(phase='CloseHandle',error=repr(e)))
        if journal.is_dir():
            try:write_new(journal/'ownership.closed.json',encoded(dict(handles_acquired=len(handles),
                close_errors=secondary,primary_exception=None if primary is None else repr(primary),
                all_handles_closed=not any(x['phase']=='CloseHandle' for x in secondary))))
            except BaseException as e:secondary.append(dict(phase='close-receipt-publication',error=repr(e)))
    if primary is not None or secondary:raise PairWriteFailure(primary,secondary,journal) from primary
    return result
