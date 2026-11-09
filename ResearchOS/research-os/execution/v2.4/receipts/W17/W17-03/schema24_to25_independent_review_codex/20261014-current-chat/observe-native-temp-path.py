import ctypes,json,os
k=ctypes.WinDLL('kernel32',use_last_error=True);out={'present_environment_names':sorted(os.environ),'no_filesystem_writes':True}
for name in ['GetTempPathW','GetTempPath2W']:
 try:fn=getattr(k,name)
 except AttributeError:out[name]={'available':False};continue
 fn.argtypes=[ctypes.c_uint32,ctypes.c_wchar_p];fn.restype=ctypes.c_uint32;b=ctypes.create_unicode_buffer(32768);n=fn(len(b),b);out[name]={'available':True,'return_length':n,'path':b.value,'win32_error':ctypes.get_last_error() if n==0 else 0}
print(json.dumps(out,ensure_ascii=True))
