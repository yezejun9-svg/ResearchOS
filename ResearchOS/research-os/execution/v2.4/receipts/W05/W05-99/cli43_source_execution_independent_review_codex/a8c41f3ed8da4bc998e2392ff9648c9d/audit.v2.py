from pathlib import Path
import json, hashlib, os, subprocess, datetime, traceback
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99'
O=Path(__file__).resolve().parent
E=P/'cli_exact8_integration_executor_codex/9f85939ef58d497895485094712d3672'
L=P/'cli_exact8_integration_root_launcher_codex/2ad2a87d8f3b4051b9931e69b30b8726'
G=P/'cli_exact8_integration_root_grant_codex/9f85939ef58d497895485094712d3672'
N=P/'integration_codex/cli-exact8-source-integration-r323'
checks=[]; reads={}; cache={}; gitcalls=[]
def ck(name,value):
    checks.append({'check':name,'passed':bool(value)})
    if not value: raise RuntimeError(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def path(s):
    p=Path(s);return p if p.is_absolute() else R/p
def raw(p):
    p=path(p);k=str(p.resolve());s=p.stat();sig=(s.st_size,s.st_mtime_ns)
    if k in cache and cache[k][0]==sig:return cache[k][1]
    b=p.read_bytes();t=p.stat();ck('stable-read:'+k,sig==(t.st_size,t.st_mtime_ns))
    cache[k]=(sig,b);reads[k]={'path':k,'sha256':sha(b),'bytes':len(b)};return b
def ref(p):
    p=path(p);b=raw(p);return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':sha(b),'bytes':len(b)}
def verify(r):
    b=raw(r['path']);ck('pin:'+r['path'],(sha(b),len(b))==(r['sha256'],r['bytes']));return b
def obj(p):return json.loads(raw(p))
def walkrefs(v):
    if isinstance(v,dict):
        if {'path','sha256','bytes'} <= v.keys():verify(v)
        for x in v.values():walkrefs(x)
    elif isinstance(v,list):
        for x in v:walkrefs(x)
def save(name,v):
    with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def manifest(p):
    m=obj(p);entries=m['entries'];ck('unique-manifest:'+str(p),len({str(path(x['path']).resolve()).casefold() for x in entries})==len(entries))
    for x in entries:verify(x)
    return len(entries)
def maprefs(rows):
    d={}
    for r in rows:
        k=str(path(r['path']).resolve()).casefold();ck('unique-vector:'+k,k not in d);d[k]=(r['sha256'],r['bytes'])
    return d
def owned(d,label):
    ck(label+':exit',d['actual_exit']==0 and d['error'] is None and d['timed_out'] is False and d['resumed'] is True)
    c=d['job_cleanup'];ck(label+':cleanup',all(c[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and c['errors']==[] and c['active_processes_last_observed']==0)
    ck(label+':identity',type(d['owned_child_pid']) is int and d['owned_child_pid']>0 and type(d['creation_time_100ns']) is int and d['creation_time_100ns']>0)
def tree(b):
    d={}
    for row in b.split(b'\0'):
        if not row:continue
        h,p=row.split(b'\t',1);mode,kind,blob=h.decode('ascii').split();name=p.decode('utf-8')
        ck('tree-unique:'+name,name not in d);d[name]={'mode':mode,'kind':kind,'blob':blob}
    return d
def git(label,args):
    argv=[lock['tools']['git']['path'],'--no-optional-locks',*args]
    env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_TERMINAL_PROMPT='0')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    c=subprocess.run(argv,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    (O/(label+'.stdout.raw')).write_bytes(c.stdout);(O/(label+'.stderr.raw')).write_bytes(c.stderr)
    i={'argv':argv,'cwd':str(R),'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_exit':c.returncode,'readonly':True,'stdout_ref':ref(O/(label+'.stdout.raw')),'stderr_ref':ref(O/(label+'.stderr.raw'))};save(label+'.invocation.json',i);gitcalls.append(i)
    ck('readonly-Git:'+label,c.returncode==0);return c.stdout
try:
    scope=obj(N/'scope_registration.json');completed=obj(E/'completed.json');grant=obj(G/'grant.json');intent=obj(E/'source-transaction.intent.json');reg=obj(N/'registration-audit.json')
    ck('scope exact pin',sha(raw(N/'scope_registration.json'))=='52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71')
    counts={str(d.relative_to(R)):manifest(d/'manifest.json') for d in [E,L,G,N]}
    for v in [scope,completed,grant,intent,reg]:walkrefs(v)
    ck('actual registration',reg['before']==[322,150,425] and reg['after']==[323,151,425] and reg['actual_registration_exit']==0 and reg['source_acceptance'] is False and reg['formal_increment']==0)
    reginv=obj(N/'invocation.json');ck('registration native0',reginv['actual_exit']==0)
    ck('registration raw streams',sha(raw(N/'stdout.raw'))==reginv['stdout_sha256'] and sha(raw(N/'stderr.raw'))==reginv['stderr_sha256'])
    walkrefs(reginv)
    canonical=[]
    for item in grant['canonical_copies']:
        b=verify(item['ref']);ck('current canonical byte match:'+item['canonical_path'],raw(item['canonical_path'])==b)
        f=O/('canonical.before.'+Path(item['canonical_path']).name);f.write_bytes(b);canonical.append({'canonical_path':item['canonical_path'],'copy_ref':ref(f),'original_ref':item['ref']})
    cp=obj('execution/v2.4/checkpoint.json');ow=obj('execution/v2.4/path_ownership.json')
    ck('actual tuple pending forward head',(cp['revision'],ow['revision'],len(cp['failure_counters']))==(323,151,425) and cp['head']==scope['base'])
    ck('425 unchanged prefix',cp['failure_counters']==obj(N/'checkpoint.original.json')['failure_counters'])
    ck('grant scope independent actor',grant['actor']=='codex:/root' and grant['actual_registration_completed'] is True and grant['operation_uuid']==scope['operation_uuid'] and grant['scope_ref']==completed['scope_ref'])
    review=json.loads(verify(grant['controller_review_ref']));ck('independent controller review',review['reviewer']=='codex:/root/w05_merge_review' and review['decision']=='READY_FOR_ROOT_EXACT8_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES' and review['actual_integration_executed'] is False)
    ck('new source result boundary',completed['parent']==scope['base'] and completed['source_candidate']==scope['candidate'] and completed['actual_new_commit']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856' and completed['apply_attempts']==1 and completed['commit_attempts']==1 and completed['Git_steps']==32 and completed['unique_combined_paths']==43 and completed['canonical_writes']==0 and completed['compile_SQL_HTTP_models']==0 and completed['formal_increment']==0 and completed['source_acceptance'] is False)
    before=obj(E/'immutable-inputs.before.json');after=obj(E/'immutable-inputs.after.json');bm=maprefs(before);am=maprefs(after)
    ck('7266 initial retained exactly in7271',len(bm)==7266 and len(am)==7271 and all(am.get(k)==v for k,v in bm.items()))
    for x in after:verify(x)
    additions=[x for x in after if str(path(x['path']).resolve()).casefold() not in bm]
    prepared=obj(N/'prepared_refs.json');pm=maprefs(prepared['verified_refs'])
    attribute_proof=json.loads(verify(scope['root_attributes_proof_ref']));walkrefs(attribute_proof)
    transitive=maprefs([attribute_proof['base_tree_ref'],attribute_proof['cli_tree_ref']])
    direct_add=[x for x in additions if str(path(x['path']).resolve()).casefold() in pm]
    transitive_add=[x for x in additions if str(path(x['path']).resolve()).casefold() not in pm]
    ck('three additions direct prepared and two exact transitive tree pins',len(direct_add)==3 and len(transitive_add)==2 and all(pm.get(str(path(x['path']).resolve()).casefold())==(x['sha256'],x['bytes']) for x in direct_add) and {str(path(x['path']).resolve()).casefold():(x['sha256'],x['bytes']) for x in transitive_add}==transitive)
    ck('transitive root attribute exact source commits',attribute_proof['base_commit']==scope['base'] and attribute_proof['cli_commit']==scope['candidate'])
    protected=json.loads(verify(scope['protected_source_vector_ref']));ck('protected6839',len(protected)==6839)
    for x in protected:
        verify(x);ck('protected frozen before application:'+x['path'],bm.get(str(path(x['path']).resolve()).casefold())==(x['sha256'],x['bytes']))
    # Existing code review establishes resource policy; actual recorded observations bind it here.
    for f in ['runtime.before.json','runtime.preapply.json','runtime.precommit.json','runtime.after.json']:
        rows=obj(E/f)
        for x in rows:verify(x)
        ck('controller runtime stable:'+f,maprefs(rows)==maprefs(obj(E/'runtime.before.json')))
    for f in ['runtime.before.json','runtime.after.json']:
        d=obj(L/f);ck('Python point-time boundary:'+f,d['measurement']=='POINT_IN_TIME_NOT_LIFECYCLE' and d['transient_load_absence_proven'] is False)
        for x in d['files']:verify(x)
    ck('launcher runtime equal',maprefs(obj(L/'runtime.before.json')['files'])==maprefs(obj(L/'runtime.after.json')['files']))
    for x in obj(L/'inputs.before.json'):verify(x)
    for label in ['grant-preflight','source-only-integration']:
        d=obj(L/(label+'.owned-result.json'));owned(d['result'],'Python:'+label);ck('Python wrapper clean:'+label,d['wrapper_error'] is None and d['actual_native_exit']==0)
        inv=obj(L/(label+'.invocation.json'));ck('Python flags and cwd:'+label,inv['argv'][1:5]==['-I','-S','-X','utf8'] and Path(inv['cwd']).resolve()==R.resolve() and inv['automatic_retry'] is False)
    ck('controller raw actual args',obj(L/'source-only-integration.invocation.json')['argv'][5]==scope['controller_ref']['path'])
    native=[]
    for f in sorted(E.glob('*.invocation.json')):
        d=obj(f);owned(d['process_observation'],f.name);ck('Git raw exit:'+f.name,d['actual_native_exit']==0 and d['wrapper_error'] is None and d['automatic_retry'] is False)
        ck('Git fixed cwd/env:'+f.name,Path(d['cwd']).resolve()==R.resolve() and d['environment']['GIT_NO_REPLACE_OBJECTS']=='1' and d['environment']['GIT_OPTIONAL_LOCKS']=='0')
        native.append({'name':f.name,'ref':ref(f),'argv':d['argv'],'pid':d['process_observation']['owned_child_pid'],'creation_time_100ns':d['process_observation']['creation_time_100ns']})
    ck('32 unique native jobs',len(native)==32 and len({(x['pid'],x['creation_time_100ns']) for x in native})==32)
    ck('one actual apply and commit',sum('apply' in x['argv'] and '--check' not in x['argv'] for x in native)==1 and sum('commit' in x['argv'] for x in native)==1)
    exact=json.loads(verify(scope['exact8_ref']));paths=[x['path'] for x in exact];ck('exact8 roster',len(set(paths))==8 and paths==completed['source_paths'])
    patch=verify(scope['patch_ref']);ck('exact saved patch three ways',patch==raw(E/'exact8.patch')==raw(E/'patch-from-source.stdout.raw'))
    patchpaths=[x.split(b' b/',1)[1].decode('utf-8') for x in patch.splitlines() if x.startswith(b'diff --git a/')]
    ck('patch only8',patchpaths==paths)
    base=tree(raw(E/'tree-base.stdout.raw'));parenttree=tree(raw(E/'tree-cli-parent.stdout.raw'));aftertree=tree(raw(E/'tree-after.stdout.raw'));expected=dict(base)
    for i,x in enumerate(exact,1):
        ck('base and candidate parent preimage:'+x['path'],base[x['path']]==x['a5_preimage'] and parenttree[x['path']]==x['cli_parent_preimage'] and x['a5_preimage']==x['cli_parent_preimage'])
        b=raw(E/('staged-blob-'+str(i)+'.stdout.raw'));ck('staged exact bytes and Git blob:'+x['path'],sha(b)==x['after_sha256'] and len(b)==x['after_bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['after_git']['blob'])
        ck('current worktree exact:'+x['path'],raw(x['path'])==b);expected[x['path']]=x['after_git']
    ck('complete recorded tree only8',aftertree==expected)
    ck('recorded index empty',raw(E/'index-after.stdout.raw')==b'')
    ck('recorded old status unchanged',raw(E/'status-before.stdout.raw')==raw(E/'status-after.stdout.raw')==verify(scope['status_ref']))
    lock=json.loads(verify(scope['toolchain_lock_ref']));gitpin=lock['tools']['git'];ck('actual locked Git',sha(raw(gitpin['path']))==gitpin['sha256'])
    actualhead=git('current-head',['rev-parse','HEAD']).decode().strip();ck('current actual newhead',actualhead==completed['actual_new_commit'])
    ck('current empty index',git('current-index',['diff','--cached','--name-only'])==b'')
    ck('current status exact13',git('current-status',['status','--porcelain=v1','--untracked-files=no'])==verify(scope['status_ref']))
    actualtree=tree(git('current-tree',['ls-tree','-r','-z',actualhead]));ck('current complete Git tree matches recorded',actualtree==aftertree)
    ck('current parent onlya5',git('current-parent',['rev-list','--parents','-n','1',actualhead]).decode().strip().split()==[actualhead,scope['base']])
    delta=git('current-delta',['diff-tree','--no-commit-id','--name-only','-r',scope['base'],actualhead]).decode().splitlines();ck('current delta only8',delta==paths)
    union=git('current-union',['diff-tree','--no-commit-id','--name-only','-r','2cdb0d43d5a600eef13c8f1735946a9adf52d079',actualhead]).decode().splitlines();ck('combined exact43 source paths',len(union)==43 and len(set(union))==43 and all(not x.startswith('execution/') for x in union))
    outer=P/'integration_codex/cli43-post-integration-r324/outer-completion.json';outerdata=obj(outer);known=obj(outer.parent/'tool-completion.13b080.known-fields.json')
    ck('outer observation pins',sha(raw(outer))=='de347277754507f5686f4a9918d29fba41387725ec8d100a1089d13192249f91' and sha(raw(outer.parent/'tool-completion.13b080.known-fields.json'))=='156b63eaa744989763c847a09a25706a38b30692180f3527cf547885e26483f6')
    for item in canonical:ck('canonical after audit unchanged:'+item['canonical_path'],raw(item['canonical_path'])==raw(item['copy_ref']['path']))
    save('read-audit.json',{'checks':checks,'check_count':len(checks),'failed':[],'inputs':list(reads.values()),'manifest_counts':counts,'immutable_before_count':len(before),'immutable_after_count':len(after),'additional_refs_bound_in_prepared':additions,'protected_count':len(protected),'actual_executor_Git_invocations':native,'independent_readonly_Git':gitcalls,'canonical_copies':canonical,'source43_paths':union,'outer_observation':outerdata,'known_tool_fields':known,'target_execution':False,'product_calls':0,'canonical_source_index_writes':0})
    print(json.dumps({'checks':len(checks),'failed':0,'manifest_counts':counts,'inputs':len(reads),'independent_readonly_Git':len(gitcalls),'actual32_native0':len(native),'source43':len(union)},ensure_ascii=True))
except BaseException as e:
    save('audit.failure.json',{'error':type(e).__name__+': '+str(e),'trace':traceback.format_exc(),'checks':checks,'inputs':list(reads.values()),'git_invocations':gitcalls,'actual_target_execution':False,'product_calls':0})
    raise
