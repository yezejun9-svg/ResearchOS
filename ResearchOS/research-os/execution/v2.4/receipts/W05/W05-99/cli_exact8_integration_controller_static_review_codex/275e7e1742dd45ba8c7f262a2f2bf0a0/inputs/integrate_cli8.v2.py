"""PREPARATION ONLY: new Root grant and actual closed Main38 are required. No action on import."""
import sys
sys.dont_write_bytecode=True
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
import types
import time

ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE='a5d6d16ffaf129de0361470c3a1570228bd259a2'
CLI='b98738ac093ea55bb8700cfa724ddd9e6b2a1251'
CLI_PARENT='22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
CANON=['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']]
READS={}
DEADLINE=None
HASHED_BYTES=0


def budget():
    require(DEADLINE is not None and time.monotonic()<DEADLINE,'Controller900s observation deadline')


def raw_file(p):
    global HASHED_BYTES
    budget()
    require(p.stat().st_size<=256*1024*1024,'Per-file256MiB read bound')
    chunks=[]
    with p.open('rb') as f:
        while True:
            budget();chunk=f.read(1024*1024)
            if not chunk:break
            HASHED_BYTES+=len(chunk)
            require(HASHED_BYTES<=32*1024**3,'32GiB cumulative hash/read bound')
            chunks.append(chunk)
    return b''.join(chunks)

def require(value, message):
    if not value:
        raise RuntimeError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def parse(raw):
    def pairs(items):
        result = {}
        for k,v in items:
            require(k not in result,'Duplicate JSON key')
            result[k]=v
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON: '+value)
    return json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=pairs,parse_constant=invalid)


def path(value):
    p=Path(value)
    return p if p.is_absolute() else ROOT/p


def bounded(value, existing=True):
    p=path(value)
    require('..' not in p.parts and p.is_relative_to(ROOT) and p!=ROOT,'Repository path boundary')
    require(p.resolve(strict=existing)==p.absolute(),'Path alias')
    cursor=p
    while True:
        if os.path.lexists(cursor):
            require(not cursor.is_symlink() and not(getattr(os.lstat(cursor),'st_file_attributes',0)&0x400),
                    'Reparse/symlink: '+str(cursor))
        if cursor.parent==cursor:
            break
        cursor=cursor.parent
    return p


def read(value):
    p=path(value)
    raw=raw_file(p)
    row={'path':str(p.absolute()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    k=os.path.normcase(str(p.absolute()))
    require(k not in READS or READS[k]==row,'Immutable input drift: '+str(p))
    READS[k]=row
    return raw


def ref(value):
    p=path(value);read(p)
    return dict(READS[os.path.normcase(str(p.absolute()))])


def verify(item):
    require(isinstance(item,dict) and {'path','sha256','bytes'}<=set(item),'Invalid reference')
    raw=read(item['path'])
    require(type(item['bytes']) is int and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],
            'Hash/size mismatch: '+str(item['path']))
    return raw


def document(item):
    return parse(verify(item))


def save(out,name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (out/name).open('xb') as f:
        f.write(raw)


def job_ok(result):
    require(isinstance(result,dict) and result.get('actual_exit')==0 and result.get('error') is None and
            result.get('timed_out') is False and result.get('resumed') is True,'Owned native process failed')
    require(type(result.get('owned_child_pid')) is int and result['owned_child_pid']>0 and
            type(result.get('creation_time_100ns')) is int and result['creation_time_100ns']>0,'Process identity absent')
    c=result.get('job_cleanup') or {}
    require(c.get('errors')==[] and all(c.get(k) is True for k in ['assigned_before_resume',
            'kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']),
            'Owned Job not fully closed')


def grant_check(scope,sref,grant):
    require(scope['status']=='ROOT_REGISTERED_CLI8_SOURCE_COMMIT_ONCE' and scope['owner']=='codex:/root',
            'Preparation is not executable')
    expected=scope['expected_registration'];before=scope['expected_before_registration']
    require(isinstance(expected,list) and isinstance(before,list) and len(expected)==len(before)==3 and
            all(type(x) is int for x in expected+before) and expected[0]>321 and expected[1]>149 and
            expected[0]==before[0]+1 and expected[1]==before[1]+1 and expected[2]>=before[2]>=421,
            'Explicit future Root registration after321 required')
    require(grant['schema']=='researchos.cli8-source-integration-grant.v1' and grant['actor']=='codex:/root' and
            grant['actual_registration_completed'] is True and grant['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and
            grant['scope_ref']==sref and grant['automatic_retry'] is False and grant['operation_uuid']==scope['operation_uuid'],
            'Actual once Root grant missing')
    require(scope['base']==BASE and scope['candidate']==CLI and scope['candidate_parent']==CLI_PARENT and
            scope['exact_paths']==8 and scope['union_paths']==43 and scope['commit_cap']==1 and scope['apply_cap']==1 and
            scope['product_tests_HTTP_SQL_models']==0 and scope['git_step_cap']==64,'Frozen operation bounds')
    require(bounded(scope['controller_ref']['path'])==Path(__file__).resolve() and
            hashlib.sha256(read(__file__)).hexdigest()==scope['controller_ref']['sha256'],'Controller exact bytes')
    review=document(grant['controller_review_ref'])
    require(review['schema']=='researchos.cli8-source-integration-controller-review.v1' and
            review['reviewer']!='codex:/root/command_queue_impl' and
            review['decision']=='READY_FOR_ROOT_EXACT8_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES' and
            review['requested_changes']==[] and review['actual_integration_executed'] is False and
            review['scope_sha256']==sref['sha256'] and review['controller_sha256']==scope['controller_ref']['sha256'],
            'New independent controller/scope review absent')
    copies=grant['canonical_copies'];require([x['canonical_path'] for x in copies]==CANON,'Canonical4 order')
    docs=[]
    for item in copies:
        require(bounded(item['ref']['path'])!=ROOT/item['canonical_path'],'Immutable copied canonical required')
        b=verify(item['ref']);require(b==raw_file(ROOT/item['canonical_path']),'Current canonical mismatch')
        docs.append(parse(b))
    cp,ow=docs[:2]
    require(cp['head']==BASE and [cp['revision'],ow['revision'],len(cp['failure_counters'])]==expected,
            'Main38 actual head must already be registered')
    require(cp['work_in_progress']['cli_exact8_source_integration_scope_ref']==sref and
            cp['work_in_progress']['cli_exact8_source_integration_controller_review_ref']==grant['controller_review_ref'],
            'CP lacks exact CLI integration authority')
    prior=document(scope['preparation_cp_ref'])
    require(cp['failure_counters'][:len(prior['failure_counters'])]==prior['failure_counters'],'Old failures changed')
    reg=bounded(scope['registration_namespace']);require('r'+str(expected[0]) in reg.name and
            reg.is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex'),'Registration namespace')
    rr=grant['registration_refs'];listed={}
    names={'manifest':'manifest.json','audit':'registration-audit.json','invocation':'invocation.json',
           'intent':'canonical-write.intent.json','verified':'canonical-write.verified.json'}
    for k,name in names.items():require(bounded(rr[k]['path'])==reg/name,'Registration exact location')
    mf=document(rr['manifest']);require(mf['count']==len(mf['entries']),'Registration manifest count')
    for item in mf['entries']:
        p=bounded(item['path']);require(p.is_relative_to(reg) and str(p) not in listed,'Registration manifest boundary')
        verify(item);listed[str(p)]=item
    for k in ['audit','invocation','intent','verified']:
        require(listed.get(str(bounded(rr[k]['path'])))==rr[k],'Unsealed actual registration')
    audit,inv,intent,done=[document(rr[k]) for k in ['audit','invocation','intent','verified']]
    require(audit['actor']=='codex:/root' and audit['before']==before and audit['after']==expected and
            audit['actual_registration_exit']==0 and audit['invocation_ref']==rr['invocation'] and
            audit['intent_ref']==rr['intent'] and audit['verified_ref']==rr['verified'],'Actual new CAS not closed')
    require(inv['actor']=='codex:/root' and inv['actual_exit']==0 and inv['automatic_retry'] is False and
            inv['counter_reset'] is False,'Registration invocation')
    independent=document(inv['review_ref'])
    require(independent['schema']=='researchos.root-registration-source-review.v1' and independent['reviewer']!='codex:/root' and
            independent['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and independent['requested_changes']==[] and
            independent['expected_before']==before and independent['expected_after']==expected and
            independent['actual_registration_executed'] is False,'Registration not independently reviewed')
    for k,name in [('register_sha256','register.py'),('wrapper_sha256','run.py'),
                   ('prepared_refs_sha256','prepared_refs.json'),('audit_sha256','audit.json')]:
        require(ref(reg/name)['sha256']==independent[k] and str(reg/name) in listed,'Registration code pin')
    require(inv['runner_sha256']==independent['register_sha256'] and inv['wrapper_sha256']==independent['wrapper_sha256'],
            'Actual registration scripts differ')
    for stream in ['stdout','stderr']:
        require(ref(reg/(stream+'.raw'))['sha256']==inv[stream+'_sha256'] and str(reg/(stream+'.raw')) in listed,
                'Registration original output absent')
    require([done['checkpoint'],done['ownership'],done['failure_origins']]==expected and done['intent_ref']==rr['intent'] and
            intent['Main_head']==BASE and intent['transition']=={'checkpoint':[before[0],expected[0]],
            'ownership':[before[1],expected[1]],'failures':[before[2],expected[2]]},'Registration verified head/transition')
    require([x['path'] for x in intent['metadata']]==CANON[:2] and [x['path'] for x in intent['unchanged']]==CANON[2:],
            'Metadata scope changed')
    for i,item in enumerate(intent['metadata']):
        require(verify(item['desired_ref'])==verify(copies[i]['ref']),'Desired canonical mismatch')
        verify(item['original_ref'])
        committed=document(listed[str(reg/('canonical-write.'+Path(item['path']).stem+'.done.json'))])
        require(committed['sha256']==item['desired_ref']['sha256'],'Canonical commit incomplete')
    for i,item in enumerate(intent['unchanged'],2):require(copies[i]['ref']['sha256']==item['sha256'],'ST/CM drift')
    # Main38 closed execution cannot be replaced by old source reviews or a plan.
    m38=document(scope['main38_completed_ref']);m38manifest=document(scope['main38_manifest_ref'])
    require(m38['status']=='EXACT38_SOURCE_ONLY_FAST_FORWARD_COMPLETE_PENDING_COMBINED_VALIDATION' and
            m38['actual_head']==BASE and m38['unique_paths']==38 and m38['merge_attempts']==1 and
            m38['canonical_writes']==0,'Actual Main38 completion missing')
    require(m38manifest['count']==len(m38manifest['entries']),'Main38 seal count')
    sealed={}
    for item in m38manifest['entries']:
        key=str(bounded(item['path']))
        require(key not in sealed,'Duplicate Main38 manifest path')
        verify(item);sealed[key]=item
    linked=sealed.get(str(bounded(scope['main38_completed_ref']['path'])))
    require(linked is not None and linked['sha256']==scope['main38_completed_ref']['sha256'] and
            linked['bytes']==scope['main38_completed_ref']['bytes'],'Main38 completion unsealed')
    post=document(scope['main38_post_registration_audit_ref'])
    require(post['schema']=='researchos.main38-post-integration-registration-audit.v1' and post['actor']=='codex:/root' and
            post['completed_ref']==scope['main38_completed_ref'] and post['manifest_ref']==scope['main38_manifest_ref'] and
            post['registered_head']==BASE and post['actual_registration_exit']==0,'Main38 forward registration absent')
    # Exact implementation of this later Root audit must be independently reviewed before final grant.
    rootreview=document(scope['main38_execution_review_ref'])
    require(rootreview['schema']=='researchos.main38-closed-execution-review.v1' and rootreview['reviewer']!='codex:/root' and
            rootreview['decision']=='EXACT38_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED' and rootreview['requested_changes']==[] and
            rootreview['completed_ref']==scope['main38_completed_ref'] and rootreview['manifest_ref']==scope['main38_manifest_ref'] and
            rootreview['post_registration_audit_ref']==scope['main38_post_registration_audit_ref'],
            'Actual Main38 closure independent review required')
    for item in scope['historical_evidence_refs']:verify(item)
    return copies


def tree(raw):
    result={}
    for line in raw.split(b'\0'):
        if line:
            header,name=line.split(b'\t',1);mode,kind,blob=header.decode('ascii').split()
            key=name.decode('utf-8',errors='strict');require(key not in result,'Duplicate Git tree path')
            result[key]={'mode':mode,'kind':kind,'blob':blob}
    return result


def execute(args):
    raw=read(args.scope);require(hashlib.sha256(raw).hexdigest()==args.scope_sha256,'Scope SHA')
    scope=parse(raw);sref=ref(args.scope)
    raw=read(args.grant);require(hashlib.sha256(raw).hexdigest()==args.grant_sha256,'Grant SHA')
    grant=parse(raw);require(bounded(grant['scope_ref']['path'])==bounded(args.scope),'Grant scope path')
    sref['path']=grant['scope_ref']['path'];copies=grant_check(scope,sref,grant)
    require(bounded(ROOT/'.git').is_dir(),'Main must use its original non-aliased Git directory')
    tools=document(scope['toolchain_lock_ref'])['tools']
    require(Path(sys.executable).absolute()==Path(tools['python']['path']).absolute(),'Actual Python path')
    for name in ['python','git']:
        require(hashlib.sha256(read(tools[name]['path'])).hexdigest()==tools[name]['sha256'],'Pinned executable bytes')
    exact=document(scope['exact8_ref']);require(len(exact)==8 and len({x['path'] for x in exact})==8,'Exact8')
    protected=document(scope['protected_source_vector_ref'])
    require(protected and not {str(ROOT/x['path']) for x in exact}&{str(path(x['path'])) for x in protected},
            'Protected-source vector overlaps owned8')
    out=bounded(scope['new_output_root'],False)
    require(out.parent==ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_integration_executor_codex' and
            out.name==scope['operation_uuid'] and len(out.name)==32 and all(c in '0123456789abcdef' for c in out.name) and
            not os.path.lexists(out),'New exclusive execution leaf')
    out.mkdir();phase='PRE_NATIVE';last=None;applied=False;commit_attempted=False;steps=0
    try:
        hr=scope['owned_process_helper_ref'];require(hr['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad','Job helper pin')
        helper=types.ModuleType('cli8_owned_job');helper.__file__=str(path(hr['path']))
        exec(compile(verify(hr),helper.__file__,'exec'),helper.__dict__)
        hooks=out/'empty-hooks';hooks.mkdir()
        env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']}
        env.update(PATH='C:/Windows/System32;C:/Windows',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',
                   GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',
                   PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
        prefix=[tools['git']['path'],'-c','core.hooksPath='+str(hooks),'-c','core.fsmonitor=false',
                '-c','core.untrackedCache=false','-c','core.attributesFile='+os.devnull,'-c','core.autocrlf=false',
                '-c','core.eol=lf','-c','gc.auto=0','-c','maintenance.auto=false','-c','submodule.recurse=false']
        def run(name,argv,timeout=30):
            nonlocal phase,last,steps
            budget();steps+=1;require(steps<=64,'Git64 step cap');phase=name;last=None;error=None;start=now()
            try:
                with (out/(name+'.stdout.raw')).open('xb') as so,(out/(name+'.stderr.raw')).open('xb') as se:
                    last=helper.run_owned(prefix+argv,str(ROOT),env,so,se,timeout)
            except BaseException as exc:error=repr(exc)
            finally:
                save(out,name+'.invocation.json',{'argv':prefix+argv,'cwd':str(ROOT),'environment':env,'started_at':start,
                     'ended_at':now(),'process_observation':last,'wrapper_error':error,
                     'actual_native_exit':last.get('actual_exit') if isinstance(last,dict) else None,'automatic_retry':False})
            require(error is None,'Git wrapper failure');job_ok(last);budget()
            return raw_file(out/(name+'.stdout.raw'))
        def guards():
            budget()
            for item in list(READS.values()):verify(item)
            for item in copies:require(raw_file(ROOT/item['canonical_path'])==verify(item['ref']),'Canonical changed')
            for item in protected:verify(item)
            for p in scope['old_deleted_paths']:require(not os.path.lexists(ROOT/p),'Old deletion restored')
            require(not list(hooks.iterdir()),'Hooks no longer empty')
        def runtime(name):
            expected={str(path(x['path']).absolute()).lower():x for x in document(scope['runtime_resources_ref'])['files']}
            for item in [scope['controller_ref'],hr]:expected[str(path(item['path']).absolute()).lower()]=item
            paths=set(helper.runtime_resource_paths())|{sys.executable}
            for module in list(sys.modules.values()):
                for field in ['__file__','__cached__']:
                    p=getattr(module,field,None)
                    if p and Path(p).is_file():paths.add(p)
            actual=[]
            for p in sorted(paths):
                k=str(Path(p).absolute()).lower();require(k in expected,'Unpinned controller runtime')
                verify(expected[k]);actual.append(ref(p))
            save(out,name+'.json',actual)
        guards();runtime('runtime.before')
        save(out,'immutable-inputs.before.json',list(READS.values()))
        require(run('head-before',['rev-parse','HEAD']).decode().strip()==BASE,'Main38 must actually be present')
        require(run('status-before',['status','--porcelain=v1','--untracked-files=no'])==verify(scope['status_ref']), 'Main dirty status')
        require(run('index-before',['diff','--cached','--name-only'])==b'','Start index not empty')
        require(run('cli-parent',['rev-list','--parents','-n','1',CLI]).decode().split()==[CLI,CLI_PARENT],'CLI parent')
        names=[x['path'] for x in exact]
        require(run('cli-delta',['diff-tree','--no-commit-id','--name-only','-r',CLI]).decode().splitlines()==names,'CLI8 source commit')
        base_tree=tree(run('tree-base',['ls-tree','-r','-z',BASE]))
        old_tree=tree(run('tree-cli-parent',['ls-tree','-r','-z',CLI_PARENT]))
        expected_tree=dict(base_tree)
        for item in exact:
            require(base_tree[item['path']]==old_tree[item['path']]==item['a5_preimage'],'Exact existing preimage')
            current=raw_file(bounded(ROOT/item['path']))
            require(hashlib.sha256(current).hexdigest()==item['before_sha256'] and len(current)==item['before_bytes'], 'Preimage bytes')
            expected_tree[item['path']]=item['after_git']
        # Ensure the declared full public source vector is exhaustive for the pre-registered list.
        expected_protected=document(scope['protected_source_paths_ref'])
        require(sorted(str(path(x['path']).relative_to(ROOT)).replace('\\','/') for x in protected if path(x['path']).is_relative_to(ROOT))==expected_protected,
                'Full protected public input paths mismatch')
        config=run('local-config-names',['config','--local','--no-includes','--name-only','--list']).decode()
        require(not any(x.lower().startswith(('filter.','include.','includeif.')) for x in config.splitlines()), 'External Git commands not approved')
        attribute_proof=document(scope['root_attributes_proof_ref'])
        require(set(attribute_proof)=={'schema','base_commit','cli_commit','base_tree_ref','cli_tree_ref','raw_ref','git_row'} and
                attribute_proof['schema']=='researchos.cli8-original-root-attributes-proof.v1' and
                attribute_proof['base_commit']==BASE and attribute_proof['cli_commit']==CLI,
                'Only the original root attribute proof is allowed')
        attribute_ref=attribute_proof['raw_ref']
        require(bounded(attribute_ref['path'])==ROOT/'.gitattributes' and
                attribute_ref['sha256']=='705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da' and
                attribute_ref['bytes']==8,'Exact root attribute identity')
        attribute_raw=verify(attribute_ref)
        require(attribute_raw==b'* -text\n','Original root attribute bytes')
        attribute_row={'mode':'100644','kind':'blob','blob':'fa1385d99a319b43c06f5309d1aae9fdd3adea46'}
        require(attribute_proof['git_row']==attribute_row and
                tree(verify(attribute_proof['base_tree_ref']))['.gitattributes']==attribute_row and
                tree(verify(attribute_proof['cli_tree_ref']))['.gitattributes']==attribute_row and
                base_tree['.gitattributes']==old_tree['.gitattributes']==attribute_row and
                hashlib.sha1(b'blob '+str(len(attribute_raw)).encode()+b'\0'+attribute_raw).hexdigest()==attribute_row['blob'],
                'Root attributes must retain the exact base/candidate Git blob')
        attribute_pins=[x for x in protected if path(x['path']).absolute()==ROOT/'.gitattributes']
        require(len(attribute_pins)==1 and attribute_pins[0]['sha256']==attribute_ref['sha256'] and
                attribute_pins[0]['bytes']==attribute_ref['bytes'],'Root attributes absent from immutable protected vector')
        attrs={ROOT/'.git/info/attributes',ROOT/'.gitattributes'}
        for item in exact:
            p=(ROOT/item['path']).parent
            while p!=ROOT:attrs.add(p/'.gitattributes');p=p.parent
        for p in attrs:
            if p.exists():
                if p==ROOT/'.gitattributes':
                    require(read(p)==verify(attribute_ref)==attribute_raw,'Original root attribute bytes changed')
                else:
                    require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()), 'Checkout attributes need scope')
        patch=verify(scope['patch_ref'])
        generated=run('patch-from-source',['diff','--binary','--full-index','--no-ext-diff',CLI_PARENT,CLI,'--']+names)
        require(generated==patch,'Patch does not match exact immutable CLI commit')
        local_patch=out/'exact8.patch'
        with local_patch.open('xb') as f:f.write(patch)
        run('apply-check',['apply','--check','--index',str(local_patch)],60)
        guards();runtime('runtime.preapply')
        require(run('head-preapply',['rev-parse','HEAD']).decode().strip()==BASE and
                run('index-preapply',['diff','--cached','--name-only'])==b'','Preapply CAS')
        save(out,'source-transaction.intent.json',{'scope_ref':sref,'grant_ref':ref(args.grant),'base':BASE,'candidate':CLI,
             'exact8_ref':scope['exact8_ref'],'patch_ref':scope['patch_ref'],'canonical_copies':copies,
             'protected_vector_ref':scope['protected_source_vector_ref'],'commit_attempt_cap':1,'apply_attempt_cap':1,
             'recovery':'Forward-only inspect staged bytes/HEAD; never reset, checkout or auto retry'})
        applied=True
        run('apply-index',['apply','--index','--whitespace=nowarn',str(local_patch)],60)
        require(run('staged-paths',['diff','--cached','--name-only']).decode().splitlines()==names,'Staged scope not exact8')
        for i,item in enumerate(exact,1):
            current=raw_file(ROOT/item['path']);staged=run('staged-blob-'+str(i),['show',':'+item['path']])
            require(current==staged and len(current)==item['after_bytes'] and hashlib.sha256(current).hexdigest()==item['after_sha256'],
                    'Staged/worktree differs from candidate blob')
        require(run('unrelated-status',['diff','--name-only']).decode().splitlines()==scope['expected_unstaged_paths'],
                'Unrelated unstaged set changed')
        guards();runtime('runtime.precommit')
        require(run('head-precommit',['rev-parse','HEAD']).decode().strip()==BASE and
                run('index-precommit',['diff','--cached','--name-only']).decode().splitlines()==names,'Commit CAS')
        identity=scope['commit_identity']
        require(identity=={'name':'ResearchOS Root Integration','email':'codex-root@localhost'},'Explicit local commit identity')
        require(scope['commit_message']=='Integrate reviewed CLI exact8 onto closed Main38','Fixed commit message')
        commit_attempted=True
        run('commit',['-c','user.name='+identity['name'],'-c','user.email='+identity['email'],
            'commit','--no-verify','--no-gpg-sign','-m',scope['commit_message']],120)
        head=run('head-after',['rev-parse','HEAD']).decode().strip()
        require(len(head)==40 and head not in [BASE,CLI] and
                run('commit-parent',['rev-list','--parents','-n','1',head]).decode().split()==[head,BASE],'One new source commit')
        require(tree(run('tree-after',['ls-tree','-r','-z',head]))==expected_tree,'Full resulting tree differs outside8')
        require(run('delta-after',['diff-tree','--no-commit-id','--name-only','-r',head]).decode().splitlines()==names,'Committed source8 scope')
        require(run('index-after',['diff','--cached','--name-only'])==b'' and
                run('status-after',['status','--porcelain=v1','--untracked-files=no'])==verify(scope['status_ref']), 'Postcommit index/status changed')
        guards();runtime('runtime.after')
        save(out,'immutable-inputs.after.json',list(READS.values()))
        save(out,'completed.json',{'actor':'codex:/root','status':'CLI_EXACT8_SOURCE_COMMIT_CLOSED_PENDING_FRESH43_VALIDATION',
             'parent':BASE,'actual_new_commit':head,'source_candidate':CLI,'source_paths':names,'unique_combined_paths':43,
             'scope_ref':sref,'grant_ref':ref(args.grant),'apply_attempts':1,'commit_attempts':1,'Git_steps':steps,
             'hash_read_bytes':HASHED_BYTES,'canonical_writes':0,'compile_SQL_HTTP_models':0,'source_acceptance':False,'formal_increment':0})
    except BaseException as exc:
        save(out,'failure.origin.json',{'phase':phase,'error':repr(exc),'traceback':traceback.format_exc(),
             'actual_native_exit':last.get('actual_exit') if isinstance(last,dict) else None,
             'apply_attempted':applied,'commit_attempted':commit_attempted,'automatic_retry':False,'rollback':False,'counter_reset':False})
        # Preserve own operation raw and index/HEAD byte observations without spawning recovery commands.
        evidence=[]
        for p in [ROOT/'.git/HEAD',ROOT/'.git/index']+[ROOT/x['path'] for x in exact]:
            try:
                raw=p.read_bytes();evidence.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
            except BaseException as error:evidence.append({'path':str(p),'error':repr(error)})
        save(out,'after_failure.readonly_observations.json',evidence)
        raise
    finally:
        rows=[]
        for p in sorted(out.rglob('*')):
            if p.is_file():
                b=p.read_bytes();rows.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
        save(out,'manifest.json',{'count':len(rows),'entries':rows,'excluded_only':str(out/'manifest.json')})


def main():
    global DEADLINE
    require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize,'Pinned Python -I -S -X utf8')
    DEADLINE=time.monotonic()+900
    p=argparse.ArgumentParser()
    for name in ['scope','scope-sha256','grant','grant-sha256']:p.add_argument('--'+name,required=True)
    execute(p.parse_args())


if __name__=='__main__':main()


