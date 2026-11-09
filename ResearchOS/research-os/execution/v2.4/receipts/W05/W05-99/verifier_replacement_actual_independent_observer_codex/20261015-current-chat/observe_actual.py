import pathlib,sqlite3,ctypes,json,hashlib,base64,struct,os,sys,re,subprocess,datetime
from ctypes import wintypes
E=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/verifier-replacement-20261014'
D=R/'.local/live/current-chat-normal-desktop-first-use-20261012/data'
SOURCE=W/'internal/host/runtime_verifier_replacement_windows.go'
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];k.CreateFileW.restype=wintypes.HANDLE
k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
class INFO(ctypes.Structure):
 _fields_=[('attributes',wintypes.DWORD),('creation',wintypes.FILETIME),('access',wintypes.FILETIME),('write',wintypes.FILETIME),('volume',wintypes.DWORD),('sizehigh',wintypes.DWORD),('sizelow',wintypes.DWORD),('links',wintypes.DWORD),('high',wintypes.DWORD),('low',wintypes.DWORD)]
k.GetFileInformationByHandle.argtypes=[wintypes.HANDLE,ctypes.POINTER(INFO)];k.GetFileInformationByHandle.restype=wintypes.BOOL
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def digest(v):return 'sha256:'+sha(canon(v))
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def openread(path,exclusive=False):
 h=k.CreateFileW(str(path),0x80000000,0 if exclusive else 1,None,3,0x00200000|0x02000000,None)
 if h==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 return h
def fileid(h):
 i=INFO()
 if not k.GetFileInformationByHandle(h,ctypes.byref(i)):raise ctypes.WinError(ctypes.get_last_error())
 assert not i.attributes&0x400,'reparse target'
 return {'Volume':i.volume,'IndexHigh':i.high,'IndexLow':i.low,'links':i.links,'attributes':i.attributes}
def metadata():
 out={}
 for root,dirs,files in os.walk(D,followlinks=False):
  for name in sorted(dirs+files):
   p=pathlib.Path(root)/name;s=p.lstat();rel=p.relative_to(D).as_posix()
   out[rel]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'attributes':s.st_file_attributes,'inode':s.st_ino,'directory':p.is_dir()}
   if s.st_file_attributes&0x400 and name in dirs:dirs.remove(name)
 return out
def typed(v):
 if v is None:return ['null',None]
 if isinstance(v,bytes):return ['blob',base64.b64encode(v).decode('ascii')]
 if isinstance(v,str):return ['text',base64.b64encode(v.encode('utf-8')).decode('ascii')]
 if isinstance(v,int):return ['integer',str(v)]
 if isinstance(v,float):return ['real',struct.pack('>d',v).hex()]
 raise TypeError(type(v))
def rowdigest(rows):
 hashes=sorted(sha(canon([typed(v) for v in row])) for row in rows)
 return {'row_count':len(hashes),'typed_row_multiset_sha256':sha(('\n'.join(hashes)+'\n').encode())}
def quote(s):return '"'+s.replace('"','""')+'"'
def processes(label):
 ps=r'''$ErrorActionPreference='Stop'; $rows=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(researchos-control|control|runtime-verifier|electron|ResearchOS)\.exe$'} | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate); ConvertTo-Json -InputObject $rows -Depth 4 -Compress'''
 argv=[r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-NonInteractive','-Command',ps]
 env={key:val for key,val in os.environ.items() if key.upper() in {'SYSTEMROOT','WINDIR','PATH','COMSPEC','TEMP','TMP'}}
 t=now();p=subprocess.run(argv,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 raw=p.stdout.decode('utf-8-sig');rows=json.loads(raw) if raw.strip() else []
 save(E/(label+'-processes.json'),{'at':t,'argv':argv,'environment_allowlist':env,'native_exit':p.returncode,'rows':rows,'stderr_sha256':sha(p.stderr)})
 assert p.returncode==0 and not rows, 'matching Core/Desktop/verifier process exists'
 return rows
def observe(label):
 begin=now();processes(label)
 src=SOURCE.read_text(encoding='utf-8');block=src.split('var replacementCensusSQL = [4]string{',1)[1].split('\n}',1)[0];queries=re.findall(r'`([^`]+)`',block);assert len(queries)==4
 handles=[];conn=None
 beforemeta=metadata();paths=[D/'researchos.sqlite',D/'researchos.sqlite-wal',D/'researchos.sqlite-shm',D/'host/host_state.json',D/'host/runtime-verifier-installation.json']
 handles.append(openread(D/'coordinator.lock',True))
 try:
  for p in [D,D/'host']:
   h=openread(p);handles.append(h)
  ids=[fileid(handles[1]),fileid(handles[2])]
  for p in paths:
   if p.exists():
    h=openread(p);handles.append(h)
    if p.name=='researchos.sqlite':ids.append(fileid(h))
  before={str(p.relative_to(D)):pin(p) for p in paths if p.is_file()}
  state_raw=(D/'host/host_state.json').read_bytes();state=json.loads(state_raw)
  reg_raw=(D/'host/runtime-verifier-installation.json').read_bytes();reg=json.loads(reg_raw)
  # Only the expressly public registration bytes are retained; state secrets/hash fields are not emitted.
  with (E/(label+'-registration.raw.json')).open('xb') as f:f.write(reg_raw)
  conn=sqlite3.connect((D/'researchos.sqlite').as_uri()+'?mode=ro',uri=True,timeout=5)
  conn.execute('PRAGMA query_only=ON');assert conn.execute('PRAGMA query_only').fetchone()==(1,)
  conn.execute('BEGIN')
  schema=conn.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name').fetchall()
  tables={}
  for kind,name,*_ in schema:
   if kind!='table':continue
   columns=conn.execute('PRAGMA table_xinfo('+quote(name)+')').fetchall()
   names=[c[1] for c in columns]
   rows=conn.execute('SELECT '+','.join(quote(n) for n in names)+' FROM '+quote(name))
   tables[name]={'schema_xinfo_sha256':sha(canon([[typed(v) for v in c] for c in columns])),**rowdigest(rows)}
  schema_summary=rowdigest(schema)
  versions=conn.execute('SELECT max(version),count(DISTINCT version),min(version) FROM schema_migrations').fetchone();assert versions==(24,24,1),versions
  census=[conn.execute(q).fetchone()[0] for q in queries]
  principals=conn.execute('SELECT id,roles,revoked,can_create_project FROM auth_principals ORDER BY id').fetchall()
  lineage=conn.execute('SELECT principal,root,parent FROM orchestration_identity ORDER BY principal').fetchall()
  grants=conn.execute('SELECT principal,project,task,run,restricted FROM auth_grants ORDER BY principal,project,task,run,restricted').fetchall()
  owner=state['principal_id'];hostid='host-'+sha((str(D/'host')+'|'+state['principal_ref']).encode())[:12]
  service='local-verifier-root-'+digest([hostid,'researchos.runtime-qualification-verifier.v1'])[7:31]
  assert reg['owner_principal']==owner and reg['owner_host']==hostid and reg['service_root']==service
  own=[p for p in principals if 'OWNER' in json.loads(p[1]) and p[2]==0];assert len(own)==1 and own[0][0]==owner
  ps={p[0]:p for p in principals};ls={l[0]:l for l in lineage};gs={}
  for g in grants:gs.setdefault(g[0],[]).append(g)
  reserved=[]
  for pid,roles,revoked,create in principals:
   if not pid.startswith('local-verifier-'):continue
   l=ls.get(pid);g=gs.get(pid,[]);assert l and json.loads(roles)==['VERIFIER'] and create==0
   if pid.startswith('local-verifier-root-'):
    assert l[1]==pid and l[2] is None and not g
   else:
    assert l[1] in ps and l[2]==l[1] and len(g)==1
    gg=g[0];assert gg[1] and gg[2]=='' and gg[3]=='' and gg[4]==0
    assert pid=='local-verifier-'+digest([l[1],gg[1]])[7:39]
   if l[1]==service:assert revoked==0
   reserved.append({'principal':pid,'root':l[1],'parent':l[2],'revoked':revoked,'roles':json.loads(roles),'grant_count':len(g),'grant_typed_hash':rowdigest(g)})
  for l in lineage:
   if l[0].startswith('local-verifier-'):assert l[0] in ps
  for g in grants:
   if g[0].startswith('local-verifier-'):assert g[0] in ps
  semantic={'owner':owner,'host_id':hostid,'service_root':service,'reserved':reserved,'current_root_child_count':sum(x['root']==service and x['principal']!=service for x in reserved),'auth_principals':rowdigest(principals),'orchestration_identity':rowdigest(lineage),'auth_grants':rowdigest(grants)}
  conn.rollback();conn.close();conn=None
  after={str(p.relative_to(D)):pin(p) for p in paths if p.is_file()};assert before==after,'observer changed allowed file bytes'
  aftermeta=metadata();assert beforemeta==aftermeta,'data metadata changed during observation'
  journals={};jr=D/'host/runtime-verifier-replacements'
  if jr.exists():
   for p in sorted(jr.rglob('*')):
    if p.is_file():journals[p.relative_to(jr).as_posix()]=pin(p)
  result={'schema':'researchos.actual-replacement-readonly-observation/1','phase':label,'started_at':begin,'ended_at':now(),'data_root':str(D),'sqlite_version':sqlite3.sqlite_version,'uri_mode':'ro','query_only':1,'transaction':'BEGIN then ROLLBACK','native_deny_write_handles':True,'native_existing_coordinator_exclusive_read_handle_obtained':True,'public_file_ids':ids,'source_census_file':pin(SOURCE),'census_query_sha256':[sha(q.encode()) for q in queries],'schema_version_summary':versions,'global_census':census,'db_schema':schema_summary,'tables':tables,'identity':semantic,'public_state_fields':{key:state[key] for key in ['version','principal_ref','principal_id','host_instance_id']},'public_files':before,'public_registration_copy':pin(E/(label+'-registration.raw.json')),'data_metadata_only':beforemeta,'maintenance_journal':journals,'observer_mutation_detected':False,'private_file_contents_read':False,'schema_migration_performed':False,'formal_increment':0}
  save(E/(label+'.json'),result)
 finally:
  if conn is not None:conn.rollback();conn.close()
  for h in reversed(handles):k.CloseHandle(h)
 # Confirm the observer left no exclusive handle behind, using only existing file read access.
 probe=openread(D/'coordinator.lock',True);k.CloseHandle(probe)
 save(E/(label+'-closed.json'),{'at':now(),'all_observer_handles_closed':True,'existing_coordinator_exclusive_read_reopen_succeeded':True,'no_product_lease_created':True})
 print(json.dumps({'phase':label,'receipt':pin(E/(label+'.json')),'census':census,'tables':len(tables),'children':semantic['current_root_child_count'],'schema':versions,'handles_closed':True},ensure_ascii=False))
if __name__=='__main__':
 label=sys.argv[1]
 started=now()
 try:observe(label)
 except Exception as error:
  save(E/(label+'-failure.json'),{'started_at':started,'ended_at':now(),'error':repr(error),'argv':sys.argv,'no_commit_or_recover':True})
  raise
