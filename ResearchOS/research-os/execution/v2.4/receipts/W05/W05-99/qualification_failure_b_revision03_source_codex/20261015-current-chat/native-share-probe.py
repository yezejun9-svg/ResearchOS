import ctypes, os, pathlib, shutil, tempfile
from ctypes import wintypes
root=pathlib.Path(os.environ['TMP'])/'native-share-probe'
root.mkdir(parents=True,exist_ok=True)
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
k.CreateFileW.restype=wintypes.HANDLE
k.CloseHandle.argtypes=[wintypes.HANDLE]
for label,access in [('metadata',0x80|0x20000),('list',0x1|0x80|0x20000),('generic_read',0x80000000|0x20000),('delete',0x10000|0x80|0x20000)]:
    old=root/(label+'-original'); new=root/(label+'-renamed')
    old.mkdir(exist_ok=False)
    h=k.CreateFileW(str(old),access,0x1|0x2,None,3,0x02000000|0x00200000,None)
    invalid=ctypes.c_void_p(-1).value
    if h==invalid: print(label,'OPEN_FAIL',ctypes.get_last_error()); continue
    try:
        try: os.rename(old,new); result='RENAME_SUCCEEDED'
        except OSError as e: result=f'RENAME_REFUSED winerror={e.winerror}'
        print(label,hex(access),result)
    finally: k.CloseHandle(h)
shutil.rmtree(root)
