"""PREPARATION ONLY: Root must register/review a final scope and sealed grant.
The only future product mutation is one exact source-only fast-forward. No retry,
rollback, staging, source reconstruction, compilation, SQL, or business calls.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
import types

ROOT = Path('D:/作品集/ResearchOS/research-os')
PLAN = ROOT/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/7b236231f51d42319f8c21c0db715b01'
CHAIN = ['2cdb0d43d5a600eef13c8f1735946a9adf52d079','22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
         '534857db99fa5e694987f877af74c322eaa2a0b3','a5d6d16ffaf129de0361470c3a1570228bd259a2']
CANON = ['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']]
READS = {}


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
    raw=p.read_bytes()
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


def authority(scope, scope_ref, grant):
    require(scope['status']=='ROOT_REGISTERED_EXACT38_INTEGRATION_ONCE' and scope['owner']=='codex:/root',
            'Preparation scope cannot execute')
    expected=scope['expected_registration']
    require(expected==[321,149,421],'Only explicitly proposed Root321/149/421; old319/320 refuses')
    require(grant['schema']=='researchos.exact38-source-integration-grant.v1' and grant['actor']=='codex:/root' and
            grant['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and grant['actual_registration_completed'] is True and
            grant['scope_ref']==scope_ref and grant['automatic_retry'] is False,'No actual new Root grant')
    require(grant['source_chain']==scope['source_chain']==CHAIN and scope['unique_source_paths']==38 and
            scope['merge_attempt_cap']==1 and scope['product_tests_HTTP_SQL_models']==0,'Bounded exact source chain')
    require(grant['operation_uuid']==scope['operation_uuid'],'Operation UUID')
    require(scope['controller_ref']['sha256']==hashlib.sha256(read(__file__)).hexdigest() and
            bounded(scope['controller_ref']['path'])==Path(__file__).resolve(),'Controller binding')
    review=document(grant['controller_review_ref'])
    require(review['schema']=='researchos.exact38-integration-controller-review.v1' and
            review['reviewer'] not in ['codex:/root','codex:/root/command_queue_impl'] and
            review['decision']=='READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE' and review['requested_changes']==[] and
            review['controller_sha256']==scope['controller_ref']['sha256'] and
            review['scope_sha256']==scope_ref['sha256'] and review['actual_integration_executed'] is False,
            'Missing independent controller/scope review')
    rows=grant['canonical_copies']
    require([x['canonical_path'] for x in rows]==CANON,'Four ordered immutable canonical copies required')
    docs=[]
    for item in rows:
        require(bounded(item['ref']['path'])!=ROOT/item['canonical_path'],'Canonical snapshot must be immutable copy')
        raw=verify(item['ref'])
        require(raw==(ROOT/item['canonical_path']).read_bytes(),'Actual canonical differs from grant snapshot')
        docs.append(parse(raw))
    cp,ow=docs[:2]
    require([cp['revision'],ow['revision'],len(cp['failure_counters'])]==expected,'Canonical registration tuple')
    require(cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','Project identity')
    require(cp['work_in_progress']['handler38_source_integration_scope_ref']==scope_ref and
            cp['work_in_progress']['handler38_source_integration_controller_review_ref']==grant['controller_review_ref'],
            'Canonical scope/reviewer binding absent')
    old=document(scope['preparation_canonical_checkpoint_ref'])
    require(old['revision']==320 and len(old['failure_counters'])==417 and
            cp['failure_counters'][:417]==old['failure_counters'],'Original417 failure prefix altered')
    reg=bounded(scope['registration_namespace'])
    require(reg.is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex') and
            'r'+str(expected[0]) in reg.name,'Wrong registration namespace')
    regs=grant['registration_refs']
    fixed={'manifest':'manifest.json','audit':'registration-audit.json','invocation':'invocation.json',
           'intent':'canonical-write.intent.json','verified':'canonical-write.verified.json'}
    for k,n in fixed.items():
        require(bounded(regs[k]['path'])==reg/n,'Wrong registration evidence path')
    manifest=document(regs['manifest']);listed={}
    require(len(manifest['entries'])==manifest['count'],'Registration manifest count')
    for item in manifest['entries']:
        p=bounded(item['path']);require(p.is_relative_to(reg) and str(p) not in listed,'Registration manifest boundary')
        verify(item);listed[str(p)]=item
    for k in ['audit','invocation','intent','verified']:
        require(listed.get(str(bounded(regs[k]['path'])))==regs[k],'Unsealed registration evidence')
    audit,inv,intent,done=[document(regs[k]) for k in ['audit','invocation','intent','verified']]
    require(audit['actor']=='codex:/root' and audit['actual_registration_exit']==0 and audit['before']==[320,148,417] and
            audit['after']==expected and
            audit['invocation_ref']==regs['invocation'] and audit['intent_ref']==regs['intent'] and
            audit['verified_ref']==regs['verified'],'Registration audit not actual sealed completion')
    require(inv['actor']=='codex:/root' and inv['actual_exit']==0 and inv['automatic_retry'] is False and
            inv['counter_reset'] is False,'Registration invocation invalid')
    rr=document(inv['review_ref'])
    require(rr['schema']=='researchos.root-registration-source-review.v1' and rr['reviewer']!='codex:/root' and
            rr['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and rr['requested_changes']==[] and
            rr['actual_registration_executed'] is False and rr['expected_before']==[320,148,417] and
            rr['expected_after']==expected,'Registration independent review')
    for k,n in [('register_sha256','register.py'),('wrapper_sha256','run.py'),
                ('prepared_refs_sha256','prepared_refs.json'),('audit_sha256','audit.json')]:
        require(ref(reg/n)['sha256']==rr[k] and str(reg/n) in listed,'Unreviewed registration code/input')
    require(inv['runner_sha256']==rr['register_sha256'] and inv['wrapper_sha256']==rr['wrapper_sha256'],
            'Registration actual executable scripts differ')
    for stream in ['stdout','stderr']:
        require(ref(reg/(stream+'.raw'))['sha256']==inv[stream+'_sha256'] and str(reg/(stream+'.raw')) in listed,
                'Registration raw stream not sealed')
    require([done['checkpoint'],done['ownership'],done['failure_origins']]==expected and
            done['intent_ref']==regs['intent'],'Registration verification tuple')
    require(intent['Main_head']==CHAIN[0] and
            intent['transition']=={'checkpoint':[320,321],'ownership':[148,149],'failures':[417,421]} and
            [x['path'] for x in intent['metadata']]==CANON[:2] and
            [x['path'] for x in intent['unchanged']]==CANON[2:],'Registration intent boundary')
    for i,item in enumerate(intent['metadata']):
        require(verify(item['desired_ref'])==verify(rows[i]['ref']),'Desired canonical differs')
        verify(item['original_ref'])
        committed=document(listed[str(reg/('canonical-write.'+Path(item['path']).stem+'.done.json'))])
        require(committed['sha256']==item['desired_ref']['sha256'],'Canonical commit incomplete')
    for i,item in enumerate(intent['unchanged'],2):
        require(rows[i]['ref']['sha256']==item['sha256'],'Unchanged ST/CM differ')
    for item in scope['evidence_refs']:
        verify(item)
    root14=document(scope['root14_review_ref'])
    require(scope['root14_review_ref']['sha256']=='043efd8e2397c1c5d219ff83822122e5ee4a11c59058d3508662edb03b13e5a0' and
            root14['decision']=='READY_FOR_ROOT_REGISTERING_BOUNDED14_LIST_FIX_SOURCE_WITH_DECLARED_OPEN_GATES' and
            root14['source_chain']==CHAIN and root14['final_unique_source_paths']==38 and root14['requested_changes']==[],
            'Bounded14 independent source basis differs')
    verify(root14['basis']['original_handler38_review_ref'])
    require(root14['basis']['original_handler38_review_ref']==scope['handler38_review_ref'], 'Original38 review ref')
    require(scope['root14_audit_ref']==root14['basis']['root_audit_ref'] and
            scope['root14_audit_ref']['sha256']=='5444b4202ce69e82f4b39ad8216ed1ab849bf7a39c83b2cda4232a2c3eb31e58',
            'Root14 audit identity')
    verify(scope['root14_audit_ref'])
    return rows


def execute(args):
    scope_raw=read(args.scope);require(hashlib.sha256(scope_raw).hexdigest()==args.scope_sha256,'Scope SHA')
    scope=parse(scope_raw);scope_ref=ref(args.scope)
    grant_raw=read(args.grant);require(hashlib.sha256(grant_raw).hexdigest()==args.grant_sha256,'Grant SHA')
    grant=parse(grant_raw)
    require(bounded(grant['scope_ref']['path'])==bounded(args.scope),'Grant scope location')
    # Preserve Root's actual ref spelling; no self-referential scope SHA field.
    scope_ref['path']=grant['scope_ref']['path']
    canonical=authority(scope,scope_ref,grant)
    tools=document(scope['toolchain_lock_ref'])['tools']
    for n in ['python','git']:
        require(hashlib.sha256(read(tools[n]['path'])).hexdigest()==tools[n]['sha256'],'Pinned tool bytes')
    require(Path(sys.executable).absolute()==Path(tools['python']['path']).absolute(),'Actual interpreter identity')
    exact=document(scope['exact38_ref']);protected=document(scope['protected_ref'])
    require(len(exact)==38 and len({x['path'] for x in exact})==38,'Exact source roster')
    independent=document(scope['root14_review_ref'])
    require([x['path'] for x in exact]==independent['minimum_future_integration_scope']['exact_unique_paths'],
            'Source roster differs from actual independent source scope')
    reviewed={x['relative_path']:x for x in document(independent['source38_final_hashes_ref'])}
    for item in exact:
        match=reviewed[item['path']]
        require(item['after_sha256']==match['sha256'] and item['after_bytes']==match['bytes'] and
                item['after_git']['blob']==match['git_blob'] and item['after_git']['mode']==match['mode'],
                'Final map differs from independently verified source38')
    for item in protected:
        verify(item)
    out=bounded(scope['new_output_root'],False)
    require(out.parent==ROOT/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_executor_codex' and
            out.name==scope['operation_uuid'] and len(out.name)==32 and
            all(c in '0123456789abcdef' for c in out.name) and not os.path.lexists(out),'Fresh operation output')
    out.mkdir() # Once marker; never delete, even if the first subsequent operation fails.
    phase='PIN_OWNED_HELPER'; last=None; attempted=False
    try:
        helper_raw=verify(scope['owned_process_helper_ref'])
        require(scope['owned_process_helper_ref']['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad',
                'Owned helper pin')
        helper=types.ModuleType('exact38_owned_job');helper.__file__=str(path(scope['owned_process_helper_ref']['path']))
        exec(compile(helper_raw,helper.__file__,'exec'),helper.__dict__)
        hooks=out/'empty-hooks';hooks.mkdir()
        env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']}
        env.update(PATH='C:/Windows/System32;C:/Windows',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',
                   GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',
                   PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
        prefix=[tools['git']['path'],'-c','core.hooksPath='+str(hooks),'-c','core.fsmonitor=false',
                '-c','core.untrackedCache=false','-c','core.attributesFile='+os.devnull,'-c','core.autocrlf=false',
                '-c','core.eol=lf','-c','gc.auto=0','-c','maintenance.auto=false','-c','submodule.recurse=false',
                '-c','merge.autoStash=false']
        def run(name,argv,timeout=60):
            nonlocal last,phase
            phase=name;last=None;error=None;started=now()
            try:
                with (out/(name+'.stdout.raw')).open('xb') as so,(out/(name+'.stderr.raw')).open('xb') as se:
                    last=helper.run_owned(prefix+argv,str(ROOT),env,so,se,timeout)
            except BaseException as exc:
                error=repr(exc)
            finally:
                save(out,name+'.invocation.json',{'argv':prefix+argv,'cwd':str(ROOT),'environment':env,
                     'started_at':started,'ended_at':now(),'process_observation':last,'wrapper_error':error,
                     'actual_native_exit':last.get('actual_exit') if isinstance(last,dict) else None,
                     'automatic_retry':False,'stdout_ref':ref(out/(name+'.stdout.raw')) if (out/(name+'.stdout.raw')).is_file() else None,
                     'stderr_ref':ref(out/(name+'.stderr.raw')) if (out/(name+'.stderr.raw')).is_file() else None})
            require(error is None,'Wrapper error');job_ok(last)
            return (out/(name+'.stdout.raw')).read_bytes()
        def runtime_snapshot(name):
            catalog=document(scope['runtime_resources_ref'])['files']
            expected={os.path.normcase(str(path(x['path']).absolute())):x for x in catalog}
            expected[os.path.normcase(str(Path(__file__).absolute()))]=scope['controller_ref']
            expected[os.path.normcase(str(path(scope['owned_process_helper_ref']['path']).absolute()))]=scope['owned_process_helper_ref']
            paths=set(helper.runtime_resource_paths())|{sys.executable}
            for module in list(sys.modules.values()):
                for a in ['__file__','__cached__']:
                    p=getattr(module,a,None)
                    if p and Path(p).is_file():paths.add(p)
            rows=[]
            for p in sorted(paths):
                k=os.path.normcase(str(Path(p).absolute()));require(k in expected,'Unpinned actual controller runtime')
                verify(expected[k]);rows.append(ref(p))
            save(out,name+'.json',rows)
        def canonical_protected():
            for item in canonical:
                require((ROOT/item['canonical_path']).read_bytes()==verify(item['ref']),'Canonical changed under integration lease')
            for item in protected:verify(item)
            require(not list(hooks.iterdir()),'Hooks directory not empty')
            for old in scope['old_deleted_paths']:
                require(not os.path.lexists(ROOT/old),'Preexisting deletion was restored')
        def state(name,expected_head):
            require(run(name+'-head',['rev-parse','HEAD']).decode().strip()==expected_head,'Unexpected HEAD')
            require(run(name+'-status',['status','--porcelain=v1','--untracked-files=no'])==verify(scope['status_ref']),
                    'Tracked status changed')
            require(run(name+'-index',['diff','--cached','--name-only'])==b'','Index not empty')
            canonical_protected()
        runtime_snapshot('runtime.before')
        require(bounded(ROOT/'.git').is_dir(),'Main Git directory identity')
        state('before',CHAIN[0])
        # Reject arbitrary clean/smudge, attributes and hook-driven execution paths.
        config=run('local-config-names',['config','--local','--no-includes','--name-only','--list']).decode('utf-8',errors='strict')
        require(not any(x.lower().startswith(('filter.','include.','includeif.'))
                        for x in config.splitlines() if x),'External filter/include config not authorized')
        attribute_paths={ROOT/'.git/info/attributes',ROOT/'.gitattributes'}
        for item in exact:
            cursor=(ROOT/item['path']).parent
            while cursor!=ROOT:
                attribute_paths.add(cursor/'.gitattributes');cursor=cursor.parent
        for p in attribute_paths:
            if p.exists():
                require(not any(x.strip() and not x.lstrip().startswith(b'#') for x in read(p).splitlines()),
                        'Nonempty checkout attributes need separate scope')
        for i,c in enumerate(CHAIN[1:],1):
            require(run('parent-'+str(i),['rev-list','--parents','-n','1',c]).decode().split()==[c,CHAIN[i-1]],
                    'Nonlinear or multi-parent source chain')
            delta=run('delta-'+str(i),['diff-tree','--no-commit-id','--name-only','-r',c]).decode().splitlines()
            require(len(delta)==[38,2,1][i-1] and set(delta)<={x['path'] for x in exact},'Commit source scope')
        require(run('union-delta',['diff','--name-only',CHAIN[0],CHAIN[-1]]).decode().splitlines()==[x['path'] for x in exact],
                'Exact38 aggregate delta')
        for i,item in enumerate(exact,1):
            raw=run('target-blob-'+str(i),['cat-file','blob',CHAIN[-1]+':'+item['path']])
            require(hashlib.sha256(raw).hexdigest()==item['after_sha256'] and len(raw)==item['after_bytes'] and
                    hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==item['after_git']['blob'],
                    'Final reviewed blob mismatch')
            current=ROOT/item['path']
            if item['before_worktree'] is None:
                require(not os.path.lexists(current),'New source path occupied')
            else:
                verify(item['before_worktree'])
        state('precommit',CHAIN[0]);runtime_snapshot('runtime.precommit')
        save(out,'protected.before.json',protected)
        save(out,'source.before-and-target.json',exact)
        save(out,'immutable-inputs.before.json',sorted(READS.values(),key=lambda x:x['path']))
        save(out,'integration.intent.json',{'scope_ref':scope_ref,'grant_ref':ref(args.grant),'at':now(),
             'source_chain':CHAIN,'unique_paths':38,'canonical_copies':canonical,
             'protected_ref':scope['protected_ref'],'exact38_ref':scope['exact38_ref'],'merge_attempts_allowed':1,
             'recovery':'forward-only inspect; no reset/rollback/retry from this controller'})
        canonical_protected();require(not list(hooks.iterdir()),'Hooks populated before merge')
        attempted=True
        run('fast-forward',['merge','--ff-only','--no-autostash','--no-edit',CHAIN[-1]],180)
        state('after',CHAIN[-1])
        for item in exact:
            raw=(ROOT/item['path']).read_bytes()
            require(len(raw)==item['after_bytes'] and hashlib.sha256(raw).hexdigest()==item['after_sha256'],
                    'Post-FF working source differs from reviewed blob')
        runtime_snapshot('runtime.after');canonical_protected()
        save(out,'protected.after.json',protected)
        save(out,'source.after.json',[{'path':item['path'],'sha256':item['after_sha256'],'bytes':item['after_bytes']}
                                     for item in exact])
        save(out,'canonical.after.json',[{'canonical_path':item['canonical_path'],'unchanged_from_ref':item['ref']}
                                        for item in canonical])
        save(out,'completed.json',{'actor':'codex:/root','status':'EXACT38_SOURCE_ONLY_FAST_FORWARD_COMPLETE_PENDING_COMBINED_VALIDATION',
             'actual_head':CHAIN[-1],'unique_paths':38,'merge_attempts':1,'canonical_writes':0,'product_tests_HTTP_SQL_models':0,
             'whole_W05_acceptance':False,'formal_increment':0,'scope_ref':scope_ref,'grant_ref':ref(args.grant)})
    except BaseException as exc:
        save(out,'failure.origin.json',{'at':now(),'phase':phase,'error':repr(exc),'traceback':traceback.format_exc(),
             'actual_native_exit':last.get('actual_exit') if isinstance(last,dict) else None,
             'merge_attempted':attempted,'automatic_retry':False,'rollback_attempted':False,'counter_reset':False,
             'postfailure_state':'Do not infer HEAD from exit; Root must freshly inspect under a new recovery scope.'})
        # Raw filesystem observations only; do not run another Git command or overwrite changed sources.
        observations=[]
        for item in exact:
            p=ROOT/item['path']
            try:
                raw=p.read_bytes();observations.append({'path':item['path'],'exists':True,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            except BaseException as error:
                observations.append({'path':item['path'],'observation_error':repr(error)})
        save(out,'source.after_failure.json',observations)
        raise
    finally:
        files=[]
        for p in sorted(out.rglob('*')):
            if p.is_file():
                raw=p.read_bytes();files.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
        save(out,'manifest.json',{'count':len(files),'entries':files,'excluded_only':str(out/'manifest.json')})


def main():
    require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize,
            'Pinned Python -I -S -X utf8 required')
    p=argparse.ArgumentParser()
    for name in ['scope','scope-sha256','grant','grant-sha256']:p.add_argument('--'+name,required=True)
    execute(p.parse_args())


if __name__=='__main__':main()
