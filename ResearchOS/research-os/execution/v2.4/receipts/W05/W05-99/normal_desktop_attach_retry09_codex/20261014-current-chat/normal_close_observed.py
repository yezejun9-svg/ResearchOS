"""Request ordinary close of an exact observed Desktop window; never kill."""
import argparse, ctypes, datetime, json
from ctypes import wintypes as w
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--pid',required=True,type=int);p.add_argument('--hwnd',required=True,type=int);p.add_argument('--receipt',required=True);a=p.parse_args()
u=ctypes.WinDLL('user32',use_last_error=True)
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
u.IsWindowVisible.argtypes=[w.HWND]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
pid=w.DWORD();u.GetWindowThreadProcessId(a.hwnd,ctypes.byref(pid))
title=ctypes.create_unicode_buffer(512);u.GetWindowTextW(a.hwnd,title,512)
assert pid.value==a.pid and title.value=='ResearchOS' and u.IsWindowVisible(a.hwnd)
out=Path(a.receipt);assert not out.exists()
assert u.PostMessageW(a.hwnd,0x10,0,0)
with out.open('x',encoding='utf8') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'normal WM_CLOSE','hwnd':a.hwnd,'pid':a.pid,'title':title.value,'process_kill':False,'actual_wait_status':'SEPARATE_OWNED_LAUNCHER_REQUIRED'},f,ensure_ascii=False,indent=2)
print(json.dumps({'normal_close_requested':a.pid,'receipt':str(out)}))
