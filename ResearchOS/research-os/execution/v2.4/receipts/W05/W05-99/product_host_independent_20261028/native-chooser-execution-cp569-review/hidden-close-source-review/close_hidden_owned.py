"""Root-only normal WM_CLOSE for the one observed hidden owned window.

No launch, retry, kill, or process mutation. The original controller remains alive.
"""
import ctypes,datetime,hashlib,json,sys,time
from pathlib import Path
from ctypes import wintypes as w

def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    scope_path=Path(sys.argv[1]);scope=read(scope_path)
    assert scope['mode']=='ONE_EXACT_HIDDEN_WINDOW_NORMAL_CLOSE' and scope['formal_increment']==0
    for row in scope['bound_files']:assert digest(row['path'])==row['sha256'] and Path(row['path']).stat().st_size==row['bytes']
    out=Path(scope['receipt_root']);out.mkdir(exist_ok=False)
    def save(n,v):
        with (out/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
    u=ctypes.WinDLL('user32',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE];k.GetProcessTimes.argtypes=[w.HANDLE,ctypes.POINTER(w.FILETIME),ctypes.POINTER(w.FILETIME),ctypes.POINTER(w.FILETIME),ctypes.POINTER(w.FILETIME)]
    k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];k.WaitForSingleObject.restype=w.DWORD
    k.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)]
    cb=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    u.EnumWindows.argtypes=[cb,w.LPARAM];u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int];u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    u.IsWindowVisible.argtypes=[w.HWND];u.SendMessageTimeoutW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM,w.UINT,w.UINT,ctypes.POINTER(ctypes.c_size_t)];u.SendMessageTimeoutW.restype=w.LPARAM
    handles={}
    try:
        for role,expected in scope['processes'].items():
            h=k.OpenProcess(0x1000|0x100000,False,expected['pid'])
            if not h:raise ctypes.WinError(ctypes.get_last_error())
            handles[role]=h;created=w.FILETIME();exited=w.FILETIME();kernel=w.FILETIME();user=w.FILETIME()
            if not k.GetProcessTimes(h,ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel),ctypes.byref(user)):raise ctypes.WinError(ctypes.get_last_error())
            ns=(((created.dwHighDateTime<<32)|created.dwLowDateTime)-116444736000000000)*100
            image=ctypes.create_unicode_buffer(32768);size=w.DWORD(len(image))
            if not k.QueryFullProcessImageNameW(h,0,image,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
            assert str(ns)==expected['created_ns'] and Path(image.value).resolve()==Path(expected['image']).resolve()
            assert digest(image.value)==expected['image_sha256'] and k.WaitForSingleObject(h,0)==258
        expected_pid=scope['processes']['electron']['pid'];windows=[]
        @cb
        def visit(hwnd,_):
            pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value==expected_pid:
                title=ctypes.create_unicode_buffer(1024);cls=ctypes.create_unicode_buffer(256)
                u.GetWindowTextW(hwnd,title,1024);u.GetClassNameW(hwnd,cls,256)
                if cls.value=='Chrome_WidgetWin_1' and title.value=='ResearchOS':windows.append({'hwnd':hwnd,'title':title.value,'class':cls.value,'visible':bool(u.IsWindowVisible(hwnd))})
            return True
        assert u.EnumWindows(visit,0)
        assert len(windows)==1 and windows[0]['hwnd']==scope['observed_hwnd']
        save('preflight.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':digest(scope_path),'windows':windows,'processes':scope['processes']})
        hwnd=windows[0]['hwnd'];pid=w.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));assert pid.value==expected_pid
        assert all(k.WaitForSingleObject(h,0)==258 for h in handles.values())
        result=ctypes.c_size_t();sent=u.SendMessageTimeoutW(hwnd,0x0010,0,0,2,5000,ctypes.byref(result))
        last_error=ctypes.get_last_error();save('normal-close-message.json',{'sent':bool(sent),'hwnd':hwnd,'pid':expected_pid,'last_error':last_error,'automatic_retry':False})
        if not sent:raise RuntimeError('NORMAL_CLOSE_MESSAGE_UNCONFIRMED')
        deadline=time.monotonic()+40
        while time.monotonic()<deadline and any(k.WaitForSingleObject(h,0)==258 for h in handles.values()):time.sleep(.2)
        exits={}
        for role,h in handles.items():
            code=w.DWORD();assert k.GetExitCodeProcess(h,ctypes.byref(code));exits[role]={'signalled':k.WaitForSingleObject(h,0)==0,'exit':code.value}
        retired=not Path(scope['witness_path']).exists()
        success=retired and all(v['signalled'] and v['exit']==0 for v in exits.values())
        save('RESULT.json',{'normal_close_confirmed':success,'exit_codes':exits,'witness_retired':retired,'formal_increment':0,'original_diagnostic_failed':True})
        return 0 if success else 2
    except BaseException as e:
        save('UNRESOLVED.json',{'reason':repr(e),'forced_termination':False,'automatic_retry':False,'original_controller_should_remain_alive':True});return 1
    finally:
        for h in handles.values():k.CloseHandle(h)

if __name__=='__main__':sys.exit(main())
