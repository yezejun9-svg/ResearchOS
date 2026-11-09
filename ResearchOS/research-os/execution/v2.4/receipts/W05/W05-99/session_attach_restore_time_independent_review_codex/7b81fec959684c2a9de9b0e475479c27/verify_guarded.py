from pathlib import Path
import json,hashlib,sys,types,re,itertools,datetime
O=Path(__file__).resolve().parent;B=O.parent.parent
A=B/'session_attach_restore_time_revision_codex/att3-1a11e02f790732395c39325fbb4668d'
Q=B/'session_attach_restore_independent_review_codex/attach_restore_independent_review'
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1')
OLD=B/'session_attach_restore_revision_codex/1a11e02f790732395c39325fbb4668d'
CON=B/'session_attach_contract_independent_review_codex/1688da4518bf4469a11f38ac324b238e/contract-evidence/22_CLIENT_INTERFACE_DETAILS.md'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def j(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def dump(name,v):(O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def refs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=set(v):yield {k:v[k] for k in ('path','sha256','bytes')}
  for x in v.values():yield from refs(x)
 elif isinstance(v,list):
  for x in v:yield from refs(x)
refs_by_path={}
def add(ref,origin):
 ref=dict(path=str(Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
 key=ref['path'].casefold()
 if key in refs_by_path:
  if refs_by_path[key]['ref']!=ref:raise ValueError('conflicting exact pins for '+ref['path'])
  refs_by_path[key]['origins'].append(origin)
 else:refs_by_path[key]=dict(ref=ref,origins=[origin])
anchors=[(A/'HDF.json','028d441d592cff04167ae92c742f401a1bc8230cce873b08428064f0698b03b8',6615),(A/'MF.json','4ecc03cd01ef131592ee4f899b8a2f2f5776b42a3ec6e22889fa57e88b09ac2e',5789),(Q/'HDF.json','d3a211c8e4df71abc55c604ecf05e1f670f0f9e065e520277934843dd080a877',4570),(Q/'MF.json','2789162e47ddc0db851446f65b6d62f811c9541460f0fa787ff81d103ccbbeb5',4229)]
for p,sha,size in anchors:
 actual=pin(p)
 if actual['sha256']!=sha or actual['bytes']!=size:raise ValueError('entry fingerprint mismatch')
 add(dict(path=str(p),sha256=sha,bytes=size),'Root entry anchor before JSON decode')
for p in (A/'HDF.json',A/'MF.json',A/'public-input-pins.json',Q/'HDF.json',Q/'MF.json'):
 for ref in refs(j(p)):add(ref,'frozen receipt '+str(p))
for d in (A,Q):
 for p in sorted(d.rglob('*')):
  if p.is_file():add(pin(p),'enumerated public immutable package')
for p in (CON,T/'internal/domain/v24_sessions.go',G,Path(__file__),Path(sys.executable)):
 add(pin(p),'supplemental independent source/runtime input')
guard_raw=G.read_bytes()
if hashlib.sha256(guard_raw).hexdigest()!='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' or len(guard_raw)!=11404:raise ValueError('guard implementation differs')
gm=types.ModuleType('att3_independent_source_guard');gm.__file__=str(G);sys.modules[gm.__name__]=gm
exec(compile(guard_raw,str(G),'exec'),gm.__dict__)
for module in list(sys.modules.values()):
 for field in ('__file__','__cached__'):
  p=getattr(module,field,None)
  if p and Path(p).is_file():add(pin(Path(p)),'loaded reviewer Python runtime')
allrefs=[x['ref'] for x in refs_by_path.values()]
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
result=None
try:
 guard.acquire(allrefs)
 if guard.get_buffer(str(G))!=guard_raw:raise ValueError('guard buffer mismatch')
 def held(p):return guard.get_buffer(str(p))
 def js(p):return json.loads(held(p).decode('utf-8-sig'))
 def txt(p):return held(p).decode('utf-8-sig')
 copies=[]
 for index,entry in enumerate(refs_by_path.values()):
  p=Path(entry['ref']['path'])
  if p.is_relative_to(B) or p.is_relative_to(T):
   dest=O/'input-copies'/('%04d-'%index+p.name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(held(p))
   copies.append(dict(original=entry['ref'],copy=pin(dest)))
 dump('input-copy-index.json',copies)
 dump('input-pins.json',list(refs_by_path.values()))
 current=txt(A/'candidate-root/internal/domain/client_protocol.go')
 old=txt(OLD/'candidate-root/internal/domain/client_protocol.go')
 replacements=js(A/'production-replacements.json')
 reverse=current
 replacement_checks=[]
 for part in reversed(replacements):
  after,before=part['after'],part['before'];count=reverse.count(after)
  replacement_checks.append(dict(count=count,recorded_position=part['position'],actual_position=reverse.find(after),before_bytes=len(before.encode()),after_bytes=len(after.encode())))
  if count==1:reverse=reverse.replace(after,before,1)
 start=current.index('// clientAttachRestoreTime')
 stop=current.index('// journal appends',start)
 helper=current[start:stop]
 old_start=old.index('// clientAttachRestoreState')
 old_stop=old.index('// journal appends',old_start)
 outside_equal=current[:start]==old[:old_start] and current[stop:]==old[old_stop:]
 tests=[]
 for name in ('client_protocol_attach_contract_windows_test.go','client_protocol_attach_restore_windows_test.go'):
  a=held(A/'candidate-root/internal/domain'/name);b=held(OLD/'candidate-root/internal/domain'/name)
  tests.append(dict(file=name,byte_equal=a==b,test_names=re.findall(r'^func (Test\w+)\(',a.decode(),re.M)))
 newtests=txt(A/'candidate-root/internal/domain/client_protocol_attach_restore_time_windows_test.go')
 def instant(s):
  m=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)',s)
  if not m:raise ValueError('unsupported static time vector')
  base=datetime.datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)
  sec=int(base.timestamp());nano=int((m[2] or '').ljust(9,'0') or '0')
  if m[3]!='Z':
   offset=(int(m[3][1:3])*60+int(m[3][4:]))*60
   sec-=offset if m[3][0]=='+' else -offset
  return sec*1000000000+nano
 vectors=[]
 for older,newer in [('2026-10-09T00:00:00.1Z','2026-10-09T00:00:00.11Z'),('2026-10-09T00:00:00Z','2026-10-09T00:00:00.000000001Z'),('2026-10-09T08:00:00.1+08:00','2026-10-09T00:00:00.11Z')]:
  for seq in ([(older,True),(newer,False)],[(newer,False),(older,True)]):
   latest=None;valid=False
   for stamp,ok in seq:
    at=instant(stamp)
    if latest is None or at>latest:latest=at;valid=ok
    elif at==latest:valid=valid and ok
   vectors.append(dict(older=older,newer=newer,input=seq,older_before_newer=instant(older)<instant(newer),text_order_wrong=older>newer,translated_latest_rejects=not valid,translated_latest_is_actual_max=latest==max(instant(x[0]) for x in seq)))
 ties=[]
 for seq in itertools.permutations([('2026-10-09T00:00:00.1Z',True),('2026-10-09T08:00:00.100+08:00',False)]):
  latest=None;valid=False
  for stamp,ok in seq:
   at=instant(stamp)
   if latest is None or at>latest:latest=at;valid=ok
   elif at==latest:valid=valid and ok
  ties.append(dict(input=seq,translated_rejects=not valid))
 dump('timestamp-independent-evidence.json',dict(authority='NONE',kind='PYTHON_EXACT_NANOSECOND_VECTORS_AND_TRANSLATED_ALGORITHM_NOT_GO_OR_SQL_EXECUTION',vectors=vectors,ties=ties))
 result=dict(authority='NONE',formal_acceptance=False,reference_count=len(allrefs),copied_public_inputs=len(copies),ATT3_manifest_member_count=len(js(A/'MF.json')['members']),previous_review_manifest_member_count=len(js(Q/'MF.json')['members']),production_inverse_exact=reverse==old,replacement_checks=replacement_checks,all_code_outside_restore_helper_byte_equal=outside_equal,old_tests=tests,new_test_names=re.findall(r'^func (Test\w+)\(',newtests,re.M),old_negative_modes=10,old_negative_clients_per_mode=2,new_negative_modes=4,new_negative_clients_per_mode=2,helper_writes=bool(re.search(r'\b(?:INSERT|UPDATE|DELETE|ALTER|DROP)\b',helper)),helper_has_TEXT_MAX='max(restored_at)' in helper,helper_has_time_ORDER_BY='ORDER BY' in helper,old_rejection_001_static_eliminated=current.index('renewAfterRestore, restoreReady, err := clientAttachRestoreState')<current.index('if renewAfterRestore && sess.writerClientID'),old_rejection_002_static_eliminated=all(x['translated_latest_rejects'] and x['translated_latest_is_actual_max'] for x in vectors) and all(x['translated_rejects'] for x in ties),all_handoff_rows_scanned='recovered = true' in helper and 'return true, true, nil' not in helper[helper.index('events, err :='):],fresh_positive='BLOCKED/PENDING_ROOT_RESOURCE',existing_shared_TEXT_dependencies_unchanged=['client_session_fence.go:71','backup_recovery.go:236','runtime.go:121'],Go_SQL_native_model_network_execution=False,new_mechanical_failures=[842],prior_failures_not_reset=True)
 dump('static-checks.json',result)
finally:
 cleanup=guard.close();dump('sourceguard.final.json',cleanup)
print(json.dumps(dict(static=result,guard=dict(entries=len(cleanup['entries']),verification=cleanup['verification'],closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],errors=cleanup['errors'],failure=cleanup['failure'])),ensure_ascii=False))

