from pathlib import Path
import json,hashlib,os,stat,subprocess,datetime,sys
sys.stdout.reconfigure(encoding='utf-8');o=Path(__file__).parent;r=o.parents[6];b=r/'execution/v2.4/receipts/W05/W05-99/vendor_resource_restore_executor_codex/restore-r268';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p):return {'path':str(p.relative_to(r)).replace('\\','/'),'sha256':h(p)}
def write(n,x):(o/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result=load(b/'result.json');scope=load(r/result['scope_ref']['path']);manifest=load(r/'third_party/mu.MANIFEST.json');before=load(b/'vendor.before.json');after=load(b/'vendor.after.json');bm={x['path']:x for x in before};am={x['path']:x for x in after};paths=set(scope['exact_resource_paths']);errors=[]
if h(b/'result.json')!='84899509ba9b011f1f61d57ba6d155231f5330a480c000f5558bf007100e794f':errors.append('result hash')
refs=[]
def walk(x):
 if isinstance(x,dict):
  if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):
   p=r/x['path'];refs.append(ref(p))
   if h(p)!=x['sha256']:errors.append(['reference',x['path']])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(result);walk(scope)
rows=[]
for p,expected in sorted(manifest['entries'].items()):
 f=r/p;info=f.lstat();sha=h(f);match=sha==expected['sha256'] and info.st_size==expected['size'];regular=stat.S_ISREG(info.st_mode) and not (getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT)
 rows.append({'path':p,'sha256':sha,'size':info.st_size,'match':match,'regular_nonreparse':regular})
 if not match or not regular:errors.append(['current_vendor',p])
 if am[p]['sha256']!=sha or am[p]['expected_sha256']!=expected['sha256'] or am[p]['expected_size']!=expected['size']:errors.append(['after_manifest',p])
 if p not in paths and bm[p]!=am[p]:errors.append(['existing_drift',p])
write('vendor_current.json',rows)
inv=[]
for p in sorted(b.glob('*.invocation.json')):
 x=load(p);stem=p.name[:-len('.invocation.json')];stdout=b/(stem+'.stdout.raw');stderr=b/(stem+'.stderr.raw');ok=x['actual_exit']==0 and h(stdout)==x['stdout_sha256'] and h(stderr)==x['stderr_sha256'];inv.append({'invocation':ref(p),'argv':x['argv'],'exit':x['actual_exit'],'raw_valid':ok,'stdout':ref(stdout),'stderr':ref(stderr)})
 if not ok:errors.append(['invocation',p.name])
env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};env['GIT_NO_REPLACE_OBJECTS']='1';gitcalls=[]
def git(name,args):
 argv=['git','--no-replace-objects',*args];x=subprocess.run(argv,cwd=r,env=env,capture_output=True);(o/(name+'.stdout.raw')).write_bytes(x.stdout);(o/(name+'.stderr.raw')).write_bytes(x.stderr);v={'argv':argv,'cwd':str(r),'exit':x.returncode,'stdout':ref(o/(name+'.stdout.raw')),'stderr':ref(o/(name+'.stderr.raw'))};gitcalls.append(v)
 if x.returncode:errors.append(['git',name,x.returncode])
 return x.stdout
assets=[]
for i,a in enumerate(scope['resources']):
 raw=git('asset-'+str(i),['show',scope['base_head']+':'+a['path']]);sha=hashlib.sha256(raw).hexdigest();assets.append({'path':a['path'],'sha256':sha,'equal_scope_manifest_current_and_execution_blob':sha==a['expected_sha256']==h(r/a['path'])==h(b/f'asset-{i}-original.stdout.raw'),'git_oid_from_bytes':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),'scope_oid':a['git']['blob_oid']})
 if not assets[-1]['equal_scope_manifest_current_and_execution_blob']or assets[-1]['git_oid_from_bytes']!=a['git']['blob_oid']:errors.append(['asset',a['path']])
head=git('head-current',['rev-parse','HEAD']).decode().strip();status=git('status-current',['status','--short','--untracked-files=no']).decode();oldstatus=(b/'status-before.stdout.raw').read_text(encoding='utf-8');newstatus=(b/'status-after.stdout.raw').read_text(encoding='utf-8');remaining=[x for x in newstatus.splitlines()if x.startswith(' D ')];same_deletions=set(x for x in status.splitlines()if x.startswith(' D '))==set(remaining)
inputs=load(b/'public-inputs.before.json');inputs_after=load(b/'public-inputs.after.json');current_input=[{'path':x['path'],'sha256':h(r/x['path']),'bytes':(r/x['path']).stat().st_size}for x in inputs]
mirror=r/'third_party/mu/node_modules/@earendil-works/pi-coding-agent/docs/images/exy.png';target=r/'third_party/mu/packages/coding-agent/docs/images/exy.png';mirror_ok=mirror.resolve(strict=True)==target.resolve(strict=True) and h(mirror)==h(target)
audit={'actual_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':ref(b/'result.json'),'scope':ref(r/result['scope_ref']['path']),'proposal':scope['proposal_ref'],'original_manifest':ref(r/'third_party/mu.MANIFEST.json'),'manifest_files':manifest['files'],'all_entries':len(rows),'unique_before':len(bm),'unique_after':len(am),'actual_before_missing':sorted(x['path']for x in before if x['status']=='MISSING'),'all_current_match':all(x['match']and x['regular_nonreparse']for x in rows),'existing_5077_exact_before_after':all(bm[p]==am[p]for p in bm if p not in paths),'current_input_equal_original':inputs==inputs_after==current_input,'assets':assets,'invocations':inv,'read_refs':refs,'head_current':head,'remaining_deletions':remaining,'remaining_deletions_unchanged':same_deletions,'mirror_same_resolved_path':mirror_ok,'git_calls':gitcalls,'errors':errors}
write('audit.json',audit);print(json.dumps({k:v for k,v in audit.items()if k not in ['invocations','read_refs','git_calls']},ensure_ascii=False))
