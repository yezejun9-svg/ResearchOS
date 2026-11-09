import ctypes,json,pathlib
from ctypes import wintypes as w
adv=ctypes.WinDLL('advapi32',use_last_error=True);ker=ctypes.WinDLL('kernel32',use_last_error=True)
adv.GetNamedSecurityInfoW.argtypes=[w.LPWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
adv.GetNamedSecurityInfoW.restype=w.DWORD
adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes=[ctypes.c_void_p,w.DWORD,w.DWORD,ctypes.POINTER(w.LPWSTR),ctypes.POINTER(w.DWORD)]
adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype=w.BOOL
ker.LocalFree.argtypes=[ctypes.c_void_p]
C=pathlib.Path('C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015')
records=[]
for p in [*reversed(C.parents),C,C/'fixture-r4.exe',C/'fixture-parent-r4.exe',C/'supervisor-review-v2.exe']:
 sd=ctypes.c_void_p();ret=adv.GetNamedSecurityInfoW(str(p),1,5,None,None,None,None,ctypes.byref(sd))
 if ret:raise OSError(ret,'GetNamedSecurityInfoW',str(p))
 s=w.LPWSTR()
 try:
  if not adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(sd,1,5,ctypes.byref(s),None):raise ctypes.WinError(ctypes.get_last_error())
  records.append({'path':str(p),'native_sddl':s.value})
 finally:
  if s:ker.LocalFree(ctypes.cast(s,ctypes.c_void_p))
  ker.LocalFree(sd)
raw=json.dumps(records,ensure_ascii=False,indent=2);print(raw)
(pathlib.Path(__file__).resolve().parent/'native-prepositive-acl.json').write_text(raw,encoding='utf-8')
