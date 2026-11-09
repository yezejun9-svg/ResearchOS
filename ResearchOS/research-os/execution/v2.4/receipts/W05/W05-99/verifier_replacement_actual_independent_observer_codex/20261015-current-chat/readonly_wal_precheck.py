import pathlib,sqlite3,ctypes,json,hashlib,shutil,tempfile
from ctypes import wintypes
E=pathlib.Path(__file__).resolve().parent
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];k.CreateFileW.restype=wintypes.HANDLE
k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'purpose':'isolated fixture only, verify readonly WAL reader under OS deny-write handles','sqlite_version':sqlite3.sqlite_version,'attempts':[]}
with tempfile.TemporaryDirectory(prefix='observer-wal-fixture-',dir=E) as temp:
 root=pathlib.Path(temp);original=root/'original.sqlite';copy=root/'copy.sqlite'
 writer=sqlite3.connect(original);writer.execute('PRAGMA journal_mode=WAL');writer.execute('CREATE TABLE x(value TEXT)');writer.commit();writer.execute("INSERT INTO x VALUES('only-in-wal')");writer.commit()
 for suffix in ['', '-wal', '-shm']:shutil.copyfile(str(original)+suffix,str(copy)+suffix)
 writer.close()
 before={s:pin(pathlib.Path(str(copy)+s)) for s in ['', '-wal','-shm']}
 handles=[]
 try:
  for suffix in ['', '-wal','-shm']:
   h=k.CreateFileW(str(copy)+suffix,0x80000000,1,None,3,0x00200000,None)
   if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
   handles.append(h)
  try:
   conn=sqlite3.connect(copy.as_uri()+'?mode=ro',uri=True);conn.execute('PRAGMA query_only=ON');conn.execute('BEGIN')
   rows=conn.execute('SELECT value FROM x').fetchall();conn.rollback();conn.close()
   result['attempts'].append({'mode':'ro','deny_write_handles':True,'rows':rows,'success':rows==[('only-in-wal',)]})
  except Exception as e:result['attempts'].append({'mode':'ro','deny_write_handles':True,'error':repr(e),'success':False})
 finally:
  for h in handles:k.CloseHandle(h)
 after={s:pin(pathlib.Path(str(copy)+s)) for s in ['', '-wal','-shm']};result.update(before=before,after=after,unchanged=before==after)
with (E/'00-readonly-wal-precheck.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
