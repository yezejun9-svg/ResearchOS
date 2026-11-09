import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
if sys.flags.optimize != 0: raise RuntimeError('Optimized Python prohibited')
ROOT=Path.cwd().resolve();OUT=Path(__file__).resolve().parent
BASE=ROOT/'execution/v2.4';NAMES=['checkpoint','ownership','step_state','commands'];CANON=[BASE/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
READS={};ordinal=0

def digest(raw):return hashlib.sha256(raw).hexdigest()
def save(name,obj):
 p=OUT/name
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
def pin(row):
 p=ROOT/row['path'];raw=p.read_bytes();assert digest(raw)==row['sha256'] and ('bytes' not in row or len(raw)==row['bytes']);READS[p]=raw;return raw
def gitcall(args,stdin=None):
 global ordinal
 ordinal+=1;name='integration-git-'+str(ordinal).zfill(2);argv=[git,*args];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (OUT/(name+'.stdout.raw')).open('xb') as o,(OUT/(name+'.stderr.raw')).open('xb') as e:p=subprocess.run(argv,cwd=ROOT,input=stdin,stdout=o,stderr=e,env=env)
 raw=(OUT/(name+'.stdout.raw')).read_bytes();err=(OUT/(name+'.stderr.raw')).read_bytes()
 save(name+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_exit':p.returncode,'stdin_sha256':None if stdin is None else digest(stdin),'stdout_sha256':digest(raw),'stderr_sha256':digest(err),'automatic_retry':False})
 if p.returncode!=0:raise RuntimeError('Git invocation nonzero, preserve originals: '+name)
 return raw

def tree(raw):
 result={}
 for row in raw.split(b'\0'):
  if not row:continue
  info,path=row.split(b'\t',1);result[path.decode('utf-8')]=info
 return result

def canon_guard():assert all(p.read_bytes()==raw for p,raw in before.items())
def original_source_guard():
 for row in scope['original_main38']:
  p=ROOT/row['path']
  if row['sha256'] is None:assert not p.exists(),str(p)
  else:assert p.is_file() and digest(p.read_bytes())==row['sha256'],str(p)
def resource_guard(label):
 rows=resources['rows']
 for row in rows:
  raw=Path(row['path']).read_bytes();assert len(raw)==row['bytes'] and digest(raw)==row['sha256'],row['path']
 return save('protected.'+label+'.audit.json',{'protected_vector_ref':scope['protected_resources_ref'],'count':len(rows),'all_sha256_and_lengths_match':True,'actual_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_repair_or_rebuild':False})
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_bytes())['tools'];git=lock['git']['path']
assert Path(sys.executable).resolve()==Path(lock['python']['path']).resolve() and digest(Path(sys.executable).read_bytes())==lock['python']['sha256'];assert digest(Path(git).read_bytes())==lock['git']['sha256']
env={k:v for k,v in os.environ.items() if k.upper() not in {'PYTHONPATH','PYTHONOPTIMIZE'}}
handoff=json.loads((OUT/'handoff-r306-running.json').read_bytes());before={}
for key,path in zip(NAMES,CANON):
 row=handoff[key];assert path==ROOT/row['path'];before[path]=pin(row)
cp=json.loads(before[CANON[0]]);ow=json.loads(before[CANON[1]]);assert [cp['revision'],ow['revision']]==[306,134]
scope_ref=cp['work_in_progress']['configuration_handler_main_integration_scope_ref'];scope=json.loads(pin(scope_ref));assert scope['status']=='AUTHORIZED_BY_CAS306_ONLY_NOT_EXECUTED'
assert scope['executor_sha256']==digest(Path(__file__).read_bytes())
review=json.loads(pin(scope['handler_final_review_ref']));assert review['decision']=='SOURCE_READY_HANDLER38_WITH_DECLARED_OPEN_PRODUCT_GATES' and review['candidate']==scope['candidate']
resources=json.loads(pin(scope['protected_resources_ref']));assert resources['count']==len(resources['rows'])
candidate=scope['candidate'];parent=scope['required_main_parent'];paths=scope['source38_paths'];assert len(paths)==len(set(paths))==38
phase='PREFLIGHT_NOT_MUTATED';intent_ref=None
try:
 canon_guard();assert gitcall(['rev-parse','HEAD']).decode().strip()==parent==cp['head'];assert gitcall(['rev-list','--parents','-n','1',candidate]).decode().split()==[candidate,parent]
 status=gitcall(['status','--porcelain=v1','--untracked-files=no']);assert digest(status)==scope['git_status_sha256'];assert len(status.splitlines())==13 and sum(v[:2]==b' D' for v in status.splitlines())==11
 assert gitcall(['diff','--cached','--name-only','-z'])==b'';delta=gitcall(['diff-tree','--no-commit-id','--name-only','-r','-z',candidate]);assert set(p.decode() for p in delta.split(b'\0') if p)==set(paths)
 pre_tree=tree(gitcall(['ls-tree','-r','-z',parent]));target_tree=tree(gitcall(['ls-tree','-r','-z',candidate]));assert {p:b for p,b in pre_tree.items() if p not in paths}=={p:b for p,b in target_tree.items() if p not in paths}
 original_source_guard();assert sum(v['sha256'] is None for v in scope['original_main38'])==8
 expected_sources={row['path']:row['sha256'] for row in scope['candidate38']};assert set(expected_sources)==set(paths)
 for path in paths:assert digest(gitcall(['show',candidate+':'+path]))==expected_sources[path]
 attrs=gitcall(['check-attr','-z','--all','--stdin'],('\n'.join(paths)+'\n').encode()).split(b'\0');assert attrs[-1]==b'';attrs=attrs[:-1];assert len(attrs)==114
 assert {(attrs[i].decode(),attrs[i+1].decode(),attrs[i+2].decode()) for i in range(0,len(attrs),3)}=={(p,'text','unset') for p in paths}
 protected_before_ref=resource_guard('before-operation')
 canon_guard();original_source_guard();assert gitcall(['rev-parse','HEAD']).decode().strip()==parent;assert gitcall(['status','--porcelain=v1','--untracked-files=no'])==status;assert gitcall(['diff','--cached','--name-only','-z'])==b''
 hooks=OUT/'empty-hooks';hooks.mkdir(exist_ok=False);assert not list(hooks.iterdir())
 original_refs=[]
 for key,path in zip(NAMES,CANON):
  dest=OUT/('integration.'+key+'.original.json')
  with dest.open('xb') as f:f.write(before[path])
  original_refs.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':digest(before[path]),'bytes':len(before[path])})
 with (OUT/'integration.git-status.original.raw').open('xb') as f:f.write(status)
 argv=['-c','core.hooksPath='+str(hooks),'merge','--ff-only','--no-autostash',candidate]
 intent_ref=save('integration.intent.json',{'scope_ref':scope_ref,'canonical_original_refs':original_refs,'parent':parent,'candidate':candidate,'actual_future_argv':[git,*argv],'paths':paths,'protected_before_ref':protected_before_ref,'current_source_writer':'codex:/root','no_rollback_reset_stash_clean_autoretry':True,'formal_increment':0})
 canon_guard();original_source_guard();assert not list(hooks.iterdir());assert gitcall(['rev-parse','HEAD']).decode().strip()==parent;assert gitcall(['status','--porcelain=v1','--untracked-files=no'])==status;assert gitcall(['diff','--cached','--name-only','-z'])==b''
 phase='PINNED_FAST_FORWARD_STARTED';gitcall(argv);phase='PINNED_FAST_FORWARD_EXIT0'
 assert gitcall(['rev-parse','HEAD']).decode().strip()==candidate;assert gitcall(['diff','--cached','--name-only','-z'])==b'';assert gitcall(['status','--porcelain=v1','--untracked-files=no'])==status
 for path in paths:assert digest((ROOT/path).read_bytes())==expected_sources[path]
 actual_tree=tree(gitcall(['ls-tree','-r','-z','HEAD']));assert actual_tree==target_tree;assert {p:b for p,b in actual_tree.items() if p not in paths}=={p:b for p,b in pre_tree.items() if p not in paths}
 canon_guard();protected_after_ref=resource_guard('after-operation');canon_guard();assert gitcall(['status','--porcelain=v1','--untracked-files=no'])==status;assert gitcall(['rev-parse','HEAD']).decode().strip()==candidate
 result=save('integration.result.json',{'decision':'EXACT38_PINNED_PRODUCT_COMMIT_INTEGRATED_MAIN_METADATA_FOLLOWUP_REQUIRED','parent':parent,'Main_head':candidate,'source38':len(paths),'canonical_bytes_unchanged':True,'old11_git_deletions_and_status_preserved':True,'index_empty':True,'outside38_tracked_tree_unchanged':True,'protected_before_ref':protected_before_ref,'protected_after_ref':protected_after_ref,'intent_ref':intent_ref,'go_SQL_Node_model_calls':0,'formal_increment':0,'current_CP_head_is_preintegration_parent_by_design':True,'automatic_retry':False})
 print(json.dumps({'result_ref':result,'Main_head':candidate,'source38':38,'canonical_followup_required':True},ensure_ascii=True))
except BaseException as e:
 save('integration.exception.json',{'phase':phase,'error':repr(e),'intent_ref':intent_ref,'canonical_sha256':{p.name:digest(p.read_bytes()) for p in CANON},'automatic_retry':False,'rollback_or_reset':False})
 raise
