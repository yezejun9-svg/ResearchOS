from pathlib import Path
import json,hashlib,os,time
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
P=R/'execution/v2.4/receipts/W13/W13-03';E=P/'desktop_exact15_integration_executor_codex/8792799f829a23452ae5d89a59e1b0cf';L=E.with_name(E.name+'-outer');A=P/'desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf'
checks=[];cache={};checked=[]
def ck(v,n): checks.append({'check':n,'passed':bool(v)})
def absolute(p):
 p=Path(p);return p if p.is_absolute() else R/p
def pin(p):
 p=absolute(p);h=hashlib.sha256();size=0
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b);size+=len(b)
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':size}
def verify(x):
 p=absolute(x['path']);key=str(p).casefold()
 if key not in cache:cache[key]=pin(p)
 q=cache[key];ck((q['sha256'],q['bytes'])==(x['sha256'],x['bytes']),'pin '+str(p));return p
def load(p):return json.loads(absolute(p).read_bytes())
def doc(x):return load(verify(x))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(O/n)
def exact(p,sha,size=None):
 q=pin(p);ck(q['sha256']==sha and (size is None or q['bytes']==size),'external fixed '+str(p));return q
def manifest(p,sha):
 ref=exact(p,sha);d=load(p);rows=d['entries'];ck(d['count']==len(rows),'MF count '+str(p));seen=set()
 for x in rows:
  q=verify(x);k=str(q).casefold();ck(k not in seen and q.is_relative_to(p.parent),'MF unique/local '+str(q));seen.add(k)
 return ref,seen
def job(j,label):
 c=j['job_cleanup'];ck(j['actual_exit']==0 and not j['timed_out'] and j['error'] is None and j['resumed'] is True,'native zero '+label)
 ck(j['owned_child_pid']>0 and j['creation_time_100ns']>0 and c['errors']==[] and c['active_processes_last_observed']==0 and all(c[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']),'owned cleanup '+label)
def tree(p):
 result={}
 for raw in p.read_bytes().split(b'\0'):
  if not raw:continue
  left,name=raw.split(b'\t',1);mode,kind,blob=left.decode().split();result[name.decode()]={'mode':mode,'kind':kind,'blob':blob}
 return result
em,es=manifest(E/'manifest.json','b5e7f6baf227e5c8e4b9b4149016750552202953f093ecfdfb04f209858cd63b')
lm,ls=manifest(L/'manifest.json','a694f7177986a502d3d63b726661465a44b21edf00b06ea965c16b3213deeca1')
completed_ref=exact(E/'completed.json','a2230043b88ceabf268a9f006c28c553273e61cd5e544de0963091cd3b9aea8b',1801);c=load(E/'completed.json');s=doc(c['scope_ref']);g=doc(c['grant_ref']);intent=load(E/'source-transaction.intent.json')
exact(E/'source-transaction.intent.json','e5f205210e7a6c22f9852806b022a688a2d0fa9d44720a51226935cdbc810b11',3541)
ck(c['parent']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856' and c['actual_new_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7','actual head pair')
ck(c['apply_attempts']==c['commit_attempts']==1 and c['Git_steps']==43 and c['canonical_writes']==0 and c['compile_SQL_HTTP_models']==0 and c['source_acceptance'] is False and c['formal_increment']==0,'bounded completion claims')
lock=doc(s['toolchain_lock_ref']);invocations=[]
for p in sorted(E.glob('*.invocation.json')):
 d=load(p);invocations.append(d);job(d['process_observation'],p.name);ck(d['actual_native_exit']==0 and d['wrapper_error'] is None and d['automatic_retry'] is False,'Git wrapper '+p.name)
 ck(Path(d['cwd'])==R and Path(d['argv'][0])==Path(lock['tools']['git']['path']),'Git path/cwd '+p.name)
 ck(str(p).casefold() in es and str(p.with_name(p.name.replace('.invocation.json','.stdout.raw'))).casefold() in es and str(p.with_name(p.name.replace('.invocation.json','.stderr.raw'))).casefold() in es,'raw streams sealed '+p.name)
ck(len(invocations)==43,'43 actual Git invocations')
ck(sum('commit' in x['argv'] for x in invocations)==1 and sum('apply' in x['argv'] and '--check' not in x['argv'] for x in invocations)==1,'one mutating apply and commit')
outer=load(L/'invocation.final.json');owned=load(L/'owned-result.json');job(owned['owned_result'],'source controller');ck(outer['owned_result']==owned['owned_result'] and outer['actual_native_controller_exit']==0 and outer['current_phase_native_exit'] is None and outer['first_error'] is None and outer['secondary_errors']==[],'outer nullable facts')
ck(outer['argv'][1:5]==['-I','-S','-X','utf8'] and Path(outer['argv'][5])==Path(s['controller_ref']['path']) and outer['argv'][6:]==['--scope',c['scope_ref']['path'],'--scope-sha256',c['scope_ref']['sha256'],'--grant',c['grant_ref']['path'],'--grant-sha256',c['grant_ref']['sha256'] and set(outer['environment'])=={'COMSPEC','PATHEXT','SYSTEMROOT','WINDIR'},'exact child argv/public env')
new=tree(E/'tree-after.stdout.raw');old=tree(E/'tree-live-cli43.stdout.raw');base=tree(E/'tree-original-base.stdout.raw');desktop=tree(E/'tree-final-desktop.stdout.raw');paths=c['source_paths'];exact15=doc(intent['exact15_ref']);ck(len(exact15)==len(paths)==15 and {x['path'] for x in exact15}==set(paths),'exact15 roster')
delta={k for k in new.keys()|old.keys() if new.get(k)!=old.get(k)};union={k for k in new.keys()|base.keys() if new.get(k)!=base.get(k)};prior={k for k in old.keys()|base.keys() if old.get(k)!=base.get(k)}
ck(delta==set(paths) and len(prior)==43 and len(union)==58 and not prior.intersection(paths),'whole tree exact15 disjoint43 union58')
for row in exact15:
 name=row['path'];b=(R/name).read_bytes();ck(new[name]==desktop[name]==row['after_git'],'actual tree source blob '+name);ck(hashlib.sha256(b).hexdigest()==row['after_sha256'] and len(b)==row['after_bytes'],'actual Main source '+name)
 ck(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==new[name]['blob'],'actual Git blob '+name)
 ck(verify(row['final_blob_ref']).read_bytes()==b,'source candidate exactbytes '+name)
for n in ['delta-after','staged-paths']:ck(set((E/(n+'.stdout.raw')).read_text(encoding='utf-8').splitlines())==set(paths),'saved exact paths '+n)
ck((E/'commit-parent.stdout.raw').read_text().strip()==c['actual_new_commit']+' '+c['parent'],'saved commit parent')
ck((R/'.git/HEAD').read_text().strip()=='ref: refs/heads/main' and (R/'.git/refs/heads/main').read_text().strip()==c['actual_new_commit'],'direct Main HEAD')
ck((E/'index-after.stdout.raw').read_bytes()==b'' and (E/'status-after.stdout.raw').read_bytes()==verify(s['status_ref']).read_bytes(),'saved final index/status')
ck(all(not os.path.lexists(R/x) for x in s['old_deleted_paths']),'11 old deletions remain absent')
ck((E/'exact15.patch').read_bytes()==(E/'patch-from-source.stdout.raw').read_bytes()==verify(intent['patch_ref']).read_bytes(),'patch original byteexact')
for x in g['canonical_copies']:ck((R/x['canonical_path']).read_bytes()==verify(x['ref']).read_bytes(),'live canonical unchanged '+x['canonical_path'])
protected=doc(intent['protected_vector_ref']);ck(len(protected)==6983,'protected count6983')
for x in protected:verify(x)
vectors={}
for label,root in [('inner',E),('outer',L)]:
 before=load(root/'immutable-inputs.before.json');after=load(root/'immutable-inputs.after.json');bm={str(absolute(x['path'])).casefold():x for x in before};am={str(absolute(x['path'])).casefold():x for x in after};ck(len(bm)==len(before) and len(am)==len(after),'vector paths unique '+label);ck(all(am.get(k)==v for k,v in bm.items()),'immutable exact prefix '+label)
 for x in after:verify(x)
 vectors[label]={'before':len(before),'after':len(after),'additions':[v for k,v in am.items() if k not in bm]}
catalog=doc(s['runtime_resources_ref']);print('RUNTIME_CATALOG_SHAPE',type(catalog).__name__, list(catalog) if isinstance(catalog,dict) else len(catalog),flush=True)
save('audit.partial.json',{'checks':checks,'vectors':vectors,'failed':[x for x in checks if not x['passed']],'verified_unique_files':len(cache)})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'verified_unique_files':len(cache),'vectors':vectors},ensure_ascii=False))
