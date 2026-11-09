"""Task86: finite AD02 Source delta; no actual registration/product entry."""
import ast,copy,hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent;W=D.parent.parent
S=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02';O=S.parent/'adopt-20261010-01'
OLD_REVIEW=D.parent/'review-adopt-20261010-01';R=W.parents[4]
ACTOR='codex:/root/full_w09_source_review';AUTHOR='codex:/root/backup_regression_resources'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT_LOG=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
checks=[]
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def note(name,ok,**details):
 value=dict(name=name,passed=bool(ok),**details);checks.append(value)
 with (D/'checks.progress.jsonl').open('ab') as f:f.write((json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n').encode())
def reject(name,fn,code):
 try:fn()
 except ValueError as e:note(name,code in str(e),observed=str(e),Source_fixture_only=True)
 else:note(name,False,observed='UNEXPECTED_ALLOW')
def docs(v):
 out=[]
 if type(v) is dict:
  out.append(v)
  for x in v.values():out.extend(docs(x))
 elif type(v) is list:
  for x in v:out.extend(docs(x))
 elif type(v) is str:
  try:out.extend(docs(json.loads(v)))
  except (ValueError,TypeError):pass
 return out
def actual_author():
 offsets=[0,282210739,282210873];lines=[];size=ROOT_LOG.stat().st_size
 with ROOT_LOG.open('rb') as f:
  for x in offsets:f.seek(x);lines.append(f.readline())
 header,metadata,last=[json.loads(x) for x in lines]
 text=last['payload']['content'][0]['text'];prefix='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/backup_regression_resources\nPayload:\n'
 value=json.loads(text[len(prefix):]) if text.startswith(prefix) else None
 note('real Backup Final full HDF and adjacent backend identity',header['payload']['id']==ROOT_THREAD and metadata['type']=='inter_agent_communication_metadata' and metadata['ordinal']+1==last['ordinal']==63971 and metadata['timestamp']==last['timestamp']=='2026-10-09T20:20:06.855Z' and last['metadata']['client_authored'] is False and last['payload']['author']==AUTHOR.removeprefix('codex:') and last['payload']['recipient']=='/root' and value['HDF']['sha256']==pin(S/'HDF.json')['sha256'] and value['MF']['sha256']==pin(S/'MF.json')['sha256'])
 with (D/'actual-Backup-author.raw.jsonl').open('xb') as f:f.write(b''.join(lines))
 return save('actual-Backup-author.observation.json',dict(schema='researchos.independent-actual-peer-observation.v1',observed_by=ACTOR,peer_actor=AUTHOR,root_thread_id=ROOT_THREAD,source_audit_path=str(ROOT_LOG),source_prefix_size_observed=size,
  source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],original_capture_ref=pin(D/'actual-Backup-author.raw.jsonl'),message_id=last['payload']['id'],received_at=last['timestamp'],issued_by_Root=False,Root_witness=False,execution_grant=False,formal_acceptance=False))
def original1109():
 size=ROOT_LOG.stat().st_size;calls={};matches=[]
 with ROOT_LOG.open('rb') as f:
  header=f.readline();start=max(0,size-32*1024*1024);f.seek(start)
  if start:f.readline()
  while f.tell()<size:
   offset=f.tell();raw=f.readline();row=json.loads(raw);p=row.get('payload',{})
   if p.get('type')=='custom_tool_call':calls[p['call_id']]=(offset,raw,row)
   elif p.get('type')=='custom_tool_call_output':
    host=[x for x in docs(p.get('output')) if x.get('chunk_id')=='b312e8']
    if host:matches.append((calls[p['call_id']],(offset,raw,row),host))
 note('actual Root original1109 unique complete failed host preserved',len(matches)==1 and len(matches[0][2])==1 and matches[0][2][0]['exit_code']==1 and 'ROOT_ACTUAL_PYTHON_EXIT=1' in matches[0][2][0]['output'])
 call,last,host=matches[0];lines=[header,call[1],last[1]]
 with (D/'original-Root1109.raw.jsonl').open('xb') as f:f.write(b''.join(lines))
 return save('original-Root1109.observation.json',dict(schema='researchos.independent-original-Root-host-observation.v1',observed_by=ACTOR,Root_assigned_original=1109,source_audit_path=str(ROOT_LOG),source_prefix_size_observed=size,
  source_line_offsets=[0,call[0],last[0]],source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],original_capture_ref=pin(D/'original-Root1109.raw.jsonl'),original_call_id=call[2]['payload']['call_id'],actual_chunk_id='b312e8',actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,new_original_failure=False,counter_reset=False,execution_grant=False,formal_acceptance=False))
def source_hosts(h):
 index=doc(h['actual_source_host_pairs_ref']['path']);records=[]
 for entry in index['captures']:
  b=doc(entry['binding_ref']['path']);raw=Path(entry['raw_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True)
  assert pin(entry['raw_ref']['path'])==entry['raw_ref'] and pin(entry['binding_ref']['path'])==entry['binding_ref']
  assert len(lines)==3 and [len(x) for x in lines]==b['source_line_bytes'] and [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256']
  with Path(b['source_audit_path']).open('rb') as f:
   for offset,line in zip(b['source_line_offsets'],lines):f.seek(offset);assert f.read(len(line))==line
  rows=[json.loads(x) for x in lines];assert rows[0]['payload']['id']==h['source_thread_id'] and rows[1]['payload']['call_id']==rows[2]['payload']['call_id']==b['original_call_id']
  records.append(dict(raw_ref=entry['raw_ref'],binding_ref=entry['binding_ref'],original_three_lines_verified=True))
 note('all11 author actual source pairs full original offsets/bytes',len(records)==11 and index['actual_source_author']==AUTHOR)
 return records
def main():
 h=doc(S/'HDF.json');mf=doc(S/'MF.json');p=doc(h['input_pins_ref']['path']);reg=module(h['caller_ref']['path'],'AD02_Source_registrar');core=module(h['core_ref']['path'],'AD02_Source_core');gm=module(p['refs']['guard']['path'],'AD02_guard')
 href=pin(S/'HDF.json');mref=pin(S/'MF.json');bindings={k:h[k] for k in ('caller_ref','core_ref','main_pair_ref','contract_ref')}
 refs=[href,mref,*mf['members'],h['base_hdf_ref'],h['base_manifest_ref'],h['reused_old_68_controls_ref'],*h['original_failure_refs'],*[pin(OLD_REVIEW/x) for x in ('HDF.json','MF.json','Source-decision.json')]]
 unique={str(Path(x['path'])).casefold():dict(x,path=str(Path(x['path']))) for x in refs}
 assert not set(unique)&{str(x).casefold() for x in reg.CANON}
 g=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  g.acquire(list(unique.values()));note('complete41 new members held; no liveCanon',len(mf['members'])==41,held_ref_count=len(unique),live_Canon_held=0)
  note('HDF MF source and contributor identities exact',h['actor_id']==mf['source_author']==reg.AUTHOR==core.AUTHOR==AUTHOR and h['original_contributor']==mf['original_contributor']=='codex:/root/native_temp_independent_review' and h['manifest_ref']==mref)
  for k,ref in bindings.items():note('new self binding '+k,reg.pin(ref['path'])==ref and ref in mf['members'])
  old=(O/'register_w09_adoption.source.py').read_bytes();new=(S/'register_w09_adoption.source.py').read_bytes();ol=old.splitlines(keepends=True);nl=new.splitlines(keepends=True);changed=[i for i,(a,b) in enumerate(zip(ol,nl)) if a!=b];inverse=list(nl)
  for i in changed:inverse[i]=ol[i]
  note('Caller exactly author14/path47; inverse whole bytes',changed==[13,46] and len(ol)==len(nl) and b''.join(inverse)==old,changed_source_lines=[i+1 for i in changed])
  oldc=(O/'adoption_core.source.py').read_bytes();newc=(S/'adoption_core.source.py').read_bytes();a=oldc.splitlines(keepends=True);b=newc.splitlines(keepends=True);ci=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y];restored=list(b)
  for i in ci:restored[i]=a[i]
  note('Core only author6; inverse whole bytes',ci==[5] and len(a)==len(b) and b''.join(restored)==oldc)
  note('Main pair and input pins full bytes unchanged',(S/'main_pair_bytes.source.py').read_bytes()==(O/'main_pair_bytes.source.py').read_bytes() and (S/'input-pins.json').read_bytes()==(O/'input-pins.json').read_bytes())
  for path in (reg.R,reg.R/'.local',S):note('actual legal local path '+path.name,reg.path_checked(str(path))==path)
  choice=doc(p['refs']['NF_choice']['path'])
  for selector,row in choice['selectors'].items():
   path=Path(row['scratch_root']);note('actual chosen absent local scratch '+selector,reg.path_checked(str(path),absent=True)==path,scratch_created=False)
  reject('UNC rejected',lambda:reg.path_checked('\\\\host\\share\\file'),'ABSOLUTE_LOCAL_PATH')
  reject('device prefix rejected',lambda:reg.path_checked('\\\\.\\C:\\file'),'ABSOLUTE_LOCAL_PATH')
  reject('extended prefix rejected',lambda:reg.path_checked('\\\\?\\C:\\file'),'ABSOLUTE_LOCAL_PATH')
  reject('ADS rejected',lambda:reg.path_checked(str(S/'file')+':stream'),'REGULAR_LOCAL_PATH')
  reject('relative rejected',lambda:reg.path_checked('.local/file'),'ABSOLUTE_LOCAL_PATH')
  reject('traversal rejected',lambda:reg.path_checked(str(S/'..'/'file')),'NO_PATH_TRAVERSAL')
  reject('NUL rejected',lambda:reg.path_checked(str(S)+'\x00'),'ABSOLUTE_LOCAL_PATH')
  reject('bool rejected',lambda:reg.path_checked(True),'ABSOLUTE_LOCAL_PATH')
  tree=ast.parse(new);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='path_checked')
  class ReparseFixture:
   def __init__(self,value,mode):self.value=value;self.mode=mode;self.parts=('D:\\','Source-fixture');self.parents=()
   def __str__(self):return self.value
   def absolute(self):return self
   def exists(self):return True
   def is_symlink(self):return self.mode=='symlink'
   def is_junction(self):return self.mode=='junction'
   def stat(self):return types.SimpleNamespace(st_file_attributes=0x400 if self.mode=='reparse-attribute' else 0)
  for mode in ('symlink','junction','reparse-attribute'):
   env=reg.__dict__.copy();env['Path']=lambda value,mode=mode:ReparseFixture(value,mode);exec(compile(ast.Module(body=[fn],type_ignores=[]),'<Source reparse condition fixture>','exec'),env)
   reject('reparse condition '+mode,lambda env=env:env['path_checked']('D:\\Source-fixture'),'NO_REPARSE_PATH')
  note('all authority/stage/counter/TP/lease code unchanged',b''.join(inverse)==old and b''.join(restored)==oldc,old68_reexecuted=False,Task78_controls_reexecuted=False,Q_NF3_controls_reexecuted=False,registrar_request_field_count=len(reg.REQUEST_FIELDS))
  for ref in h['source_guard_refs']:
   value=doc(ref['path']);note('author guard closed0 '+Path(ref['path']).name,value['closed'] and value['retained_handles_count']==0 and not value['errors'])
  prior=doc(OLD_REVIEW/'Source-decision.json');note('actual prior Task78 accepted Source reused',prior['decision']=='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION' and prior['source_handoff_ref']==h['base_hdf_ref'],prior_review_ref=pin(OLD_REVIEW/'Source-decision.json'))
  control=doc(h['controls_ref']['path']);note('author25 and old68 evidence reused',h['controls_passed']==25 and h['controls_failed']==0 and control.get('failed')==0 and doc(h['reused_old_68_controls_ref']['path'])['passed']==68)
  decision=dict(schema='researchos.w09-root-adoption-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,source_author_id=AUTHOR,source_handoff_ref=href,source_manifest_ref=mref,**bindings,actual_executed=False,formal_acceptance=False,execution_grant=False)
  note('new nonauthor review interface accepts exact Backup selfrefs',core.validate_own_review(decision,href,mref,bindings)==ACTOR,Source_interface_fixture_only=True,Root_witness_created=False)
  for label,change in [('old Native author',{'source_author_id':'codex:/root/native_temp_independent_review'}),('Backup self-review',{'actor_id':AUTHOR}),('Root review',{'actor_id':core.ROOT}),('grant',{'execution_grant':True}),('old HDF',{'source_handoff_ref':h['base_hdf_ref']})]:
   candidate=dict(decision,**change);reject('own review rejects '+label,lambda candidate=candidate:core.validate_own_review(candidate,href,mref,bindings),'OWN_NONAUTHOR_REVIEW_NO_GRANT')
  author=actual_author();failure=original1109();hosts=source_hosts(h)
  note('original1090 remains immutable with unknown exits',doc(h['original_failure_refs'][0]['path'])['ordinal']==1090,original_failure_refs=h['original_failure_refs'],original1109_observation_ref=failure)
  result=save('finite-delta-controls.json',dict(schema='researchos.w09-adoption-independent-delta-review.v1',actor_id=ACTOR,source_author=AUTHOR,source_handoff_ref=href,source_manifest_ref=mref,passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks,
   actual_author_observation_ref=author,original1109_observation_ref=failure,author_host_originals=hosts,prior_Task78_decision_ref=pin(OLD_REVIEW/'Source-decision.json'),old68_reexecuted=False,Task78_controls_reexecuted=False,author25_reexecuted=False,Q_NF3_controls_reexecuted=False,
   Source_fixture_only=True,RootScope_lease_grant_written=False,actual_product_calls=0,live_Canon_held=0,execution_grant=False,formal_acceptance=False))
 finally:
  closed=g.close();guard_ref=save('independent-delta-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 assert all(x['passed'] for x in checks),'INDEPENDENT_DELTA_CHECK_FAILED'
 print(json.dumps(dict(result_ref=result,guard_ref=guard_ref,passed=len(checks),failed=0,closed0=True,actual_product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
if __name__=='__main__':main()
