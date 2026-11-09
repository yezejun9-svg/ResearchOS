"""Operate an observed Windows folder dialog using its standard edit and OK controls."""
import argparse, ctypes, datetime, json
from ctypes import wintypes as w
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--title',required=True);p.add_argument('--folder',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
u=ctypes.WinDLL('user32',use_last_error=True);u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int];u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int];u.GetDlgCtrlID.argtypes=[w.HWND];u.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.SendMessageW.restype=w.LPARAM;u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
CB=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM);wins=[];children=[]
def enum(h,l):
    pid=w.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(pid));b=ctypes.create_unicode_buffer(512);u.GetWindowTextW(h,b,512)
    if pid.value==a.pid and b.value==a.title and u.IsWindowVisible(h):wins.append(h)
    return True
u.EnumWindows(CB(enum),0);assert len(wins)==1,wins
def child(h,l):
    b=ctypes.create_unicode_buffer(256);u.GetClassNameW(h,b,256);children.append((h,u.GetDlgCtrlID(h),b.value));return True
u.EnumChildWindows(wins[0],CB(child),0)
edit=[h for h,i,c in children if i==1152 and c=='Edit'];ok=[h for h,i,c in children if i==1 and c=='Button'];assert len(edit)==len(ok)==1
assert Path(a.folder).is_dir()
b=ctypes.create_unicode_buffer(a.folder);u.SendMessageW(edit[0],0xC,0,ctypes.addressof(b))
readback=ctypes.create_unicode_buffer(4096);u.SendMessageW(edit[0],0xD,4096,ctypes.addressof(readback));assert readback.value==a.folder
assert u.PostMessageW(ok[0],0xF5,0,0)
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':a.pid,'dialog':wins[0],'title':a.title,'edit_control':edit[0],'ok_control':ok[0],'folder':a.folder,'native_readback_matches':True,'action':'native folder dialog OK','direct_application_API':False}
with Path(a.receipt).open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps(r))
