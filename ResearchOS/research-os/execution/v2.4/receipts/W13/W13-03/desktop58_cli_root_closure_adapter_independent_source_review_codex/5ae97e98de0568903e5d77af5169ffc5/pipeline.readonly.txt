"""PREPARATION ONLY. Future Root metadata operations; never a product runner.

No embedded registration tuple, resource catalogue, failure cut or grant.
The immutable v3 gate resolves review through the actual sealed CP reference.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import types

ROOT = Path('D:/作品集/ResearchOS/research-os')
RECEIPTS = ROOT/'execution/v2.4/receipts/W05/W05-99'
CANON = ['execution/v2.4/'+n+'.json' for n in ('checkpoint','path_ownership','step_state','commands')]
SOURCE = 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
OLD_GATE_SHA = '3e5f7843ce15f709c7fd416ef30d787246f04818b7d25513ce6c171fddba1fe8'
V3_GATE_SHA = 'b918c3b36f1152de82d144443d73ad0437095752b51472e353535ca3396c3213'
WIP_KEYS = ('desktop58_finite_validation_scope_ref',
            'desktop58_finite_validation_current_source_authority_ref',
            'desktop58_finite_validation_controller_review_ref',
            'desktop58_finite_validation_CLI2_qualification_ref',
            'desktop58_finite_validation_state')
DESKTOP_RECEIPTS = ROOT/'execution/v2.4/receipts/W13/W13-03'
OBSERVATION_PHASES = ('admission.runtime','grant-final.runtime','grant-final.runtime.after')
DESKTOP_VALUE_KEYS = ('source_catalog_ref','resource_catalog_ref','current58_CLI2_qualification_ref',
    'current58_CLI2_review_ref','current58_CLI2_manifest_ref','Root_forward_head_seal_ref',
    'Root_forward_head_review_ref','negative_alias_declarations','inner_seconds','outer_seconds',
    'builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds',
    'expected_runtime_observation_paths','runtime_observation_phases')

def wip_values(b, scope_ref):
    return [scope_ref,b['current43_authority_ref'],b['controller_review_ref'],
            b['desktop_scope_values']['current58_CLI2_qualification_ref'],'REGISTERED_PENDING_ONCE_EXECUTION']

def desktop_lease(b, scope_ref):
    return {'owner':'codex:/root','current_source_writer':None,'state':'REGISTERED_PENDING_ONCE_EXECUTION',
            'scope_ref':scope_ref,'run_uuid':b['run_uuid'],'source_commit':SOURCE}


def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def parse(raw):
    def pairs(items):
        d = {}
        for k,v in items:
            need(k not in d, 'duplicate JSON key')
            d[k] = v
        return d
    return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def encoded(doc):
    return (json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')

def safe(value, existing=True):
    p = Path(value)
    if not p.is_absolute(): p = ROOT/p
    need('..' not in p.parts and p.is_relative_to(ROOT) and p != ROOT, 'outside repository')
    need(p.resolve(strict=existing) == p.absolute(), 'alias path')
    for q in [p,*p.parents]:
        if os.path.lexists(q):
            need(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400), 'reparse path')
        if q == ROOT: break
    return p

def pin(p):
    p = Path(p)
    raw = p.read_bytes()
    return {'path':p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),
            'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

READS = {}
OWNED_GRANT_ROOT = None
OWNED_GRANT_PREFLIGHT_ROOT = None
def verify(r):
    need(isinstance(r,dict) and set(r)=={'path','sha256','bytes'}, 'exact ref required')
    p = Path(r['path']); p = p if p.is_absolute() else ROOT/p
    if p.is_relative_to(ROOT): p = safe(p)
    need(p.is_absolute() and '..' not in p.parts and p.is_file(), 'invalid public input')
    raw = p.read_bytes()
    need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'input mismatch: '+str(p))
    if str(p) in READS: need(raw==READS[str(p)],'read drift')
    READS[str(p)] = raw
    return raw

def doc(r): return parse(verify(r))
def argref(value):
    # Each CLI ref is exact JSON, not an unpinned filename.
    r = parse(value.encode('utf-8')); verify(r); return r

def write(p, raw):
    p = safe(p,False)
    with p.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)

def save(p, value): return write(p,encoded(value))
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def unchanged_reads():
    for p,raw in list(READS.items()): need(Path(p).read_bytes()==raw,'immutable input changed: '+p)

def load_module(r, name):
    raw = verify(r)
    m = types.ModuleType(name); m.__file__ = str(safe(r['path']))
    exec(compile(raw,m.__file__,'exec'),m.__dict__)
    return m

def job_ok(r):
    need(isinstance(r,dict) and r['actual_exit']==0 and r['error'] is None and not r['timed_out']
         and r['resumed'] is True and r['owned_child_pid']>0 and r['creation_time_100ns']>0,'owned child failure')
    c=r['job_cleanup']
    need(c['errors']==[] and c['active_processes_last_observed']==0 and all(c[k] is True for k in
         ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume',
          'primary_exit_confirmed','job_idle_confirmed','handles_closed')),'owned cleanup incomplete')

def runtime(b, output, label):
    """Future only. Pin all resources BEFORE helper import; observation is point-in-time."""
    rows=doc(b['runtime_resources_ref'])['files']
    for r in rows: verify(r)
    lock=doc(b['toolchain_lock_ref'])['tools']
    need(Path(sys.executable).resolve()==Path(lock['python']['path']).resolve(),'actual Python')
    for name in ('python','git','go'):
        need(hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest()==lock[name]['sha256'],'tool SHA')
    helper=load_module(b['owned_process_helper_ref'],'root_cli43_owned')
    # Reuse the frozen controller's Python __file__/__cached__/loaded-DLL point observation.
    util=load_module(b['utility_ref'],'root_desktop58_runtime_definitions')
    for r in b['metadata_code_refs']: verify(r)
    actual_code=[b[k] for k in ('runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref','utility_ref')]+b['metadata_code_refs']
    allowed={os.path.normcase(str(Path(r['path']).absolute())):r for r in rows}
    for r in actual_code:
        raw=verify(r); path=str(safe(r['path']))
        need(os.path.normcase(path) in allowed and allowed[os.path.normcase(path)]['sha256']==hashlib.sha256(raw).hexdigest()
             and allowed[os.path.normcase(path)]['bytes']==len(raw),'current metadata/controller absent from Root runtime catalogue')
    allowed=list(allowed.values())
    observation=util.module_observation(allowed,helper)
    observation['all_observed_inputs_pre_pinned']=True
    observation['producer_stage']=label
    return helper,lock,save(output/(label+'.json'),observation)

def git_guard(b, output, label):
    helper,lock,observation=runtime(b,output,label+'.runtime')
    records=[]; outputs=[]
    env=dict(b['public_environment'])
    env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL='nul',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='2',
               GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
               GIT_CONFIG_KEY_1='core.untrackedCache',GIT_CONFIG_VALUE_1='false')
    for kind,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','--untracked-files=no']),('index',['diff','--cached','--name-only'])]:
        argv=[lock['git']['path']]+args; result=None; error=None
        a=output/(label+'.'+kind+'.stdout.raw'); z=output/(label+'.'+kind+'.stderr.raw')
        try:
            with a.open('xb') as stdout,z.open('xb') as stderr:
                result=helper.run_owned(argv,str(ROOT),env,stdout,stderr,30)
        except BaseException as e:
            error=repr(e)
            raise
        finally:
            item={'kind':kind,'argv':argv,'cwd':str(ROOT),'environment':env,'result':result,'wrapper_error':error,
                  'actual_stage_native_exit':result['actual_exit'] if result else None,
                  'stdout_ref':pin(a) if a.exists() else None,'stderr_ref':pin(z) if z.exists() else None}
            save(output/(label+'.'+kind+'.invocation.json'),item)
        job_ok(result); records.append(item); outputs.append(verify(item['stdout_ref']))
    g=b['main_git']; rows=outputs[1].splitlines()
    need(outputs[0].decode('ascii').strip()==SOURCE and outputs[2]==b'','HEAD/index')
    need(hashlib.sha256(outputs[1]).hexdigest()==g['status_sha256'] and len(outputs[1])==g['status_bytes']
         and len(rows)==13 and sum(x.startswith(b' D ') for x in rows)==11,'status13/old11D')
    return records,observation

def binding(r, mode):
    b=doc(r)
    need(b['schema']=='researchos.desktop58-root-metadata-binding.v1' and b['owner']=='codex:/root','binding schema/owner')
    need(b['preparation_only'] is False and b['execution_authorized'] is True,'unbound preparation')
    before=b['before']; after=b['after']
    need(all(isinstance(x,list) and len(x)==3 and all(type(y)is int for y in x) for x in (before,after)),'explicit tuples')
    need(before[0]>323 and before[2]>=430 and after[:2]==[before[0]+1,before[1]+1],'tuple progression')
    need(b['registration_metadata_paths']==CANON[:2] and b['main_git']['head']==SOURCE,'two-write layout/source')
    need(b['python_flags']==['-I','-S','-X','utf8'] and b['formal_increment']==0,'flags/formal')
    need(set(b['public_environment'])<= {'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'},'public environment')
    for k in ('runtime_resources_ref','compiler_resources_ref','current43_authority_ref',
              'origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref','scope_template_ref'):
        need(b.get(k) is not None,'missing required '+k); verify(b[k])
    need(b['authorization_gate_ref']['sha256']==V3_GATE_SHA,'exact acyclic v3 gate')
    safe(b['controller_review_path'],False)
    pf=safe(b['new_grant_preflight_root'],False)
    need(pf.is_relative_to(DESKTOP_RECEIPTS) and b['run_uuid'] in pf.name,'explicit bounded preflight UUID leaf')
    roots=[safe(b[k],False) for k in ('new_output_root','new_wrapper_root','new_export_root','new_authorization_root')]
    need(all(pf!=p and not pf.is_relative_to(p) and not p.is_relative_to(pf) for p in roots),'preflight disjoint from four run roots')
    if mode!='scope':
        need(b.get('controller_review_ref') is not None,'actual later independent review ref required')
        verify(b['controller_review_ref'])
        need(safe(b['controller_review_ref']['path'])==safe(b['controller_review_path']),'actual review path')
    # Full actual public inventories, not only hashes of inventory JSON files.
    for k in ('runtime_resources_ref','compiler_resources_ref','source_inputs_ref'):
        inventory=doc(b[k]); rows=inventory['files'] if 'files' in inventory else inventory['entries']
        need(isinstance(rows,list) and rows,'empty full public inventory')
        for row in rows: verify(row)
    for x in b['metadata_code_refs']: verify(x)
    values=b['desktop_scope_values']
    need(type(values)is dict and set(values)==set(DESKTOP_VALUE_KEYS) and all(values[k] is not None for k in DESKTOP_VALUE_KEYS),'all Desktop future values explicit')
    for k in DESKTOP_VALUE_KEYS:
        if k.endswith('_ref'):verify(values[k])
    root=safe(b['new_authorization_root'],False)
    expected=[str(root/(phase+'.json')) for phase in OBSERVATION_PHASES]
    need(values['expected_runtime_observation_paths']==expected,'Root exact observation paths must match actual three producer stages')
    need(values['runtime_observation_phases']==[{'stage':phase,'path':path} for phase,path in zip(OBSERVATION_PHASES,expected)],'Root frozen observation stage mapping')
    need(safe(b['new_output_root'],False).is_relative_to(DESKTOP_RECEIPTS) and
         safe(b['new_wrapper_root'],False).is_relative_to(DESKTOP_RECEIPTS) and root.is_relative_to(DESKTOP_RECEIPTS),'Desktop receipt roots')
    return b

def canonical_expected(b):
    rows=doc(b['canonical_before_ref'])['entries']
    need([x['canonical_path'] for x in rows]==CANON,'canonical four order')
    raw=[verify(x['ref']) for x in rows]
    cp,ow=map(parse,raw[:2])
    need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'] and cp['head']==SOURCE,'before tuple/head')
    prefix=doc(b['failure_prefix430_ref'])['failure_counters']
    need(len(prefix)==430 and cp['failure_counters'][:430]==prefix,'actual frozen original430 prefix')
    need(all((ROOT/p).read_bytes()==r for p,r in zip(CANON,raw)),'current four CAS')
    return raw

def origins(b, cp):
    cut=doc(b['origin_cut_ref'])
    need(cut['before']==b['before'] and cut['after']==b['after'] and cut['counter_reset'] is False,'explicit origin cut')
    rows=cut['origins']; need(len(rows)==b['after'][2]-b['before'][2],'origin count')
    hashes=set()
    for row in rows:
        r=row['evidence_ref']; actual=doc(r)
        need(r['sha256'] not in hashes and all(old.get('evidence_ref',{}).get('sha256')!=r['sha256'] for old in cp['failure_counters']),'duplicate origin')
        need(row['original_payload']==actual and row['counter_reset'] is False,'original origin preserved')
        hashes.add(r['sha256'])
    return rows

def project_scope(b, template):
    s=copy.deepcopy(template)
    need(s['preparation_only'] is True and s['execution_authorized'] is False,'original preparation template required')
    aliases={'output_root':'new_output_root','outer_output_root':'new_wrapper_root','export_root':'new_export_root',
        'new_authorization_root':'new_authorization_root','new_grant_preflight_root':'new_grant_preflight_root',
        'current_source_authority_ref':'current43_authority_ref','authorization_verifier_ref':'authorization_gate_ref',
        'controller_ref':'runner_ref','owned_helper_ref':'owned_process_helper_ref','debug_helper_ref':'debug_tree_helper_ref'}
    for key,src in aliases.items():s[key]=b[src]
    for k in ('run_uuid','registration_namespace','runtime_resources_ref','compiler_resources_ref',
              'controller_review_path','main_git','public_environment','launcher_ref','utility_ref','toolchain_lock_ref'):
        s[k]=b[k]
    s.update(b['desktop_scope_values'])
    s.update(preparation_only=False,execution_authorized=True,expected_before_registration=b['before'],
             expected_registration=b['after'],registration_metadata_paths=CANON[:2])
    need(s['source_commit']==SOURCE and s['node_cases']==169 and s['Go_top_cases']==3,'fixed source/roster')
    basis=('scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref',
        'origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref')
    s['Root_metadata_binding_inputs']={'refs':{k:b[k] for k in basis},
        'metadata_code_refs':copy.deepcopy(b['metadata_code_refs'])}
    return s

def reviewed_scope_match(b, scope):
    # Compare every projected field; the later review REF remains outside the scope.
    need(scope==project_scope(b,doc(b['scope_template_ref'])),
         'Final Root metadata binding differs from independently reviewed full scope')

def scope_build(b, scope_template_ref, dest):
    need(scope_template_ref==b['scope_template_ref'],'Scope template binding differs')
    return save(dest,project_scope(b,doc(scope_template_ref)))

def prepare(b, scope_ref, output):
    s=doc(scope_ref)
    reviewed_scope_match(b,s)
    need(s['registration_namespace']==output.relative_to(ROOT).as_posix(),'registration directory')
    gate=load_module(b['authorization_gate_ref'],'root_cli43_gate_prepare')
    gate.load_scope(gate.Reader(),str(safe(scope_ref['path'])),scope_ref['sha256'])
    review=doc(b['controller_review_ref'])
    need(review['schema']=='researchos.desktop58-controller-static-review.v1' and
         review['reviewer']=='codex:/root/w05_merge_review' and
         review['decision']=='READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE' and review['requested_changes']==[], 'controller review verdict')
    for key,actual in [('scope_sha256',scope_ref['sha256']),('controller_sha256',s['controller_ref']['sha256']),
                       ('launcher_sha256',s['launcher_ref']['sha256']),('gate_sha256',s['authorization_verifier_ref']['sha256'])]:
        need(review[key]==actual,'controller review complete scope/code pin')
    before=canonical_expected(b); cp,ow=map(parse,before[:2]); rows=origins(b,cp)
    reader=gate.Reader()
    gate.validate_cli2(reader,s)
    gate.validate_current58_source(reader,{'catalog_ref':s['source_catalog_ref']},doc(b['current43_authority_ref']),cp,ow)
    for path,raw in reader.raw.items():
        if path in READS:need(READS[path]==raw,'qualification/source input drift')
        READS[path]=raw
    # These must be staged by Root from the reviewed template before preparation.
    known={safe(x['path']):x for x in b['metadata_code_refs'] if Path(x['path']).is_absolute() or not Path(x['path']).drive}
    for name in ('register.py','run.py','seal.py','grant_preflight.py','scope_builder.py','prepare.py'):
        need(output/name in known and pin(output/name)==known[output/name],'unstaged or unpinned metadata wrapper '+name)
    need(doc(pin(output/'binding.json'))==b,'exact final binding filename')
    git_guard(b,output,'prepare')
    desiredcp=copy.deepcopy(cp); desiredow=copy.deepcopy(ow); stamp=now()
    desiredcp['revision']=b['after'][0]; desiredcp['expected_previous_revision']=b['before'][0]
    desiredcp['updated_at']=stamp; desiredcp['updated_by']='codex:/root'
    desiredcp['failure_counters'].extend(copy.deepcopy(rows))
    wipvalues=wip_values(b,scope_ref)
    desiredcp['work_in_progress'].update(dict(zip(WIP_KEYS,wipvalues)))
    desiredow.update(revision=b['after'][1],amended_at=stamp,amended_by='codex:/root')
    card=desiredow['card_path_bindings']['W13-03']
    need(type(card['subtasks'])is dict,'Root actual W13-03 subtask map required')
    prior=card['subtasks'].get('desktop58_finite_validation')
    need(prior is None or prior.get('state') not in ('REGISTERED_PENDING_ONCE_EXECUTION','RUNNING'),'cannot replace active Desktop lease')
    card['subtasks']['desktop58_finite_validation']=desktop_lease(b,scope_ref)
    need(desiredcp['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters'],'failure prefix')
    rawdesired=[encoded(desiredcp),encoded(desiredow),*before[2:]]
    original=[write(output/(Path(p).stem+'.original.json'),raw) for p,raw in zip(CANON,before)]
    desired=[write(output/(Path(p).stem+'.desired.json'),raw) for p,raw in zip(CANON,rawdesired)]
    audit=save(output/'audit.json',{'schema':'researchos.root-registration-draft-audit.v1','actor':'codex:/root',
        'expected_before':b['before'],'expected_after':b['after'],'actual_registration_executed':False,
        'registration_metadata_paths':CANON[:2],'formal_increment':0,'source_acceptance':False})
    refs=[pin(Path(p)) for p in sorted(READS) if p not in [str(ROOT/x) for x in CANON]]
    save(output/'prepared_refs.json',{'binding':b,'scope_ref':scope_ref,'canonical_before':[pin(ROOT/p) for p in CANON],
        'original_refs':original,'desired_refs':desired,'origins':rows,'audit_ref':audit,'verified_refs':refs,
        'expected_before':b['before'],'expected_after':b['after'],'actual_registration_executed':False})
    need(all((ROOT/p).read_bytes()==r for p,r in zip(CANON,before)),'prepare canonical drift')

def prepared(output,b):
    p=doc(pin(output/'prepared_refs.json')); need(p['binding']==b,'binding differs from prepared')
    for r in p['verified_refs']: verify(r)
    original=[verify(r) for r in p['original_refs']]; desired=[verify(r) for r in p['desired_refs']]
    need(len(original)==len(desired)==4 and original[2:]==desired[2:],'four originals/two changed')
    oldcp,oldow=map(parse,original[:2]); cp,ow=map(parse,desired[:2])
    need(cp['failure_counters']==oldcp['failure_counters']+origins(b,oldcp),'complete original prefix')
    protectedcp=copy.deepcopy(cp); protectedow=copy.deepcopy(ow)
    for k in ('revision','expected_previous_revision','updated_at','updated_by','failure_counters'):
        if k in oldcp: protectedcp[k]=oldcp[k]
        else: protectedcp.pop(k,None)
    for k in WIP_KEYS:
        if k in oldcp['work_in_progress']: protectedcp['work_in_progress'][k]=oldcp['work_in_progress'][k]
        else: protectedcp['work_in_progress'].pop(k,None)
    for k in ('revision','amended_at','amended_by'):
        if k in oldow: protectedow[k]=oldow[k]
        else: protectedow.pop(k,None)
    expectedcard=copy.deepcopy(oldow['card_path_bindings']['W13-03'])
    expectedcard['subtasks']['desktop58_finite_validation']=desktop_lease(b,p['scope_ref'])
    need(ow['card_path_bindings']['W13-03']==expectedcard,'only registered finite Desktop sublease may change')
    protectedow['card_path_bindings']['W13-03']=oldow['card_path_bindings']['W13-03']
    need(protectedcp==oldcp and protectedow==oldow,'unrelated canonical field modified')
    need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['after'],'desired tuple')
    need([cp['work_in_progress'][k] for k in WIP_KEYS]==wip_values(b,p['scope_ref']), 'desired scope/review authority values')
    return p,original,desired

def registration_review(output,b,p,r):
    d=doc(r)
    need(d['schema']=='researchos.root-registration-source-review.v1' and d['reviewer']=='codex:/root/w05_merge_review'
         and d['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and d['requested_changes']==[]
         and d['actual_registration_executed'] is False and d['expected_before']==b['before'] and d['expected_after']==b['after'],'registration review')
    for key,name in [('register_sha256','register.py'),('wrapper_sha256','run.py'),('prepared_refs_sha256','prepared_refs.json'),('audit_sha256','audit.json')]:
        need(d[key]==pin(output/name)['sha256'],'registration review pin')
    need(d['canonical_before']==p['canonical_before'] and len(d['copied_canonical_before_refs'])==4,'review canonical order')
    for copied,original in zip(d['copied_canonical_before_refs'],p['original_refs']):
        need(safe(copied['path']).parent==safe(r['path']).parent and verify(copied)==verify(original),'review original copy')
    return d

def register(b,output,review_ref):
    p,before,desired=prepared(output,b); registration_review(output,b,p,review_ref)
    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,before)),'initial four CAS')
    git_guard(b,output,'register-before')
    intent=save(output/'canonical-write.intent.json',{'actor':'codex:/root','Main_head':SOURCE,
        'transition':{k:[b['before'][i],b['after'][i]] for i,k in enumerate(('checkpoint','ownership','failures'))},
        'metadata':[{'path':x,'original_ref':p['original_refs'][i],'desired_ref':p['desired_refs'][i]} for i,x in enumerate(CANON[:2])],
        'unchanged':[{'path':x,'sha256':p['original_refs'][i]['sha256']} for i,x in enumerate(CANON) if i>=2],
        'review_ref':review_ref,'automatic_retry':False,'recovery':'FORWARD_ONLY_REQUIRES_SEPARATE_ROOT_DECISION; NEVER RESET/ROLLBACK'})
    expected=list(before)
    for i,name in enumerate(CANON[:2]):
        target=ROOT/name; temp=target.with_name(target.name+'.'+b['run_uuid']+'.tmp')
        write(temp,desired[i])
        unchanged_reads(); git_guard(b,output,'pre-replace-'+str(i))
        need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,expected)),'all-four immediately before replace CAS')
        os.replace(temp,target); expected[i]=desired[i]
        READS.pop(str(target),None)
        need(target.read_bytes()==desired[i],'own write mismatch')
        save(output/('canonical-write.'+target.stem+'.done.json'),{'sha256':p['desired_refs'][i]['sha256'],'intent_ref':intent})
    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired)),'final four CAS')
    unchanged_reads(); git_guard(b,output,'register-after')
    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired)),'post-source-guard final four CAS')
    save(output/'canonical-write.verified.json',{'checkpoint':b['after'][0],'ownership':b['after'][1],
         'failure_origins':b['after'][2],'intent_ref':intent,'step_state_commands_unchanged':True})

def run_registration(b,output,review_ref):
    p,before,desired=prepared(output,b); rev=registration_review(output,b,p,review_ref)
    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,before)),'wrapper four CAS')
    helper,lock,obs=runtime(b,output,'run.runtime.before')
    argv=[lock['python']['path'],'-I','-S','-X','utf8',str(output/'register.py'),
          '--binding-ref',json.dumps(pin(output/'binding.json')),'--output',str(output),
          '--review-ref',json.dumps(review_ref)]
    result=None; error=None
    a=output/'stdout.raw'; z=output/'stderr.raw'
    try:
        with a.open('xb') as stdout,z.open('xb') as stderr:
            result=helper.run_owned(argv,str(ROOT),dict(b['public_environment']),stdout,stderr,600)
    except BaseException as e:
        error=repr(e); raise
    finally:
        save(output/'invocation.json',{'actor':'codex:/root','argv':argv,'cwd':str(ROOT),
            'actual_exit':result['actual_exit'] if result else None,'result':result,'wrapper_error':error,
            'review_ref':review_ref,'runner_sha256':rev['register_sha256'],'wrapper_sha256':rev['wrapper_sha256'],
            'stdout_sha256':pin(a)['sha256'] if a.exists() else None,'stderr_sha256':pin(z)['sha256'] if z.exists() else None,
            'automatic_retry':False,'counter_reset':False,'actual_outer_tool_exit':None})
    job_ok(result)

def seal(b,output):
    p,before,desired=prepared(output,b)
    invref=pin(output/'invocation.json'); inv=doc(invref)
    registration_review(output,b,p,inv['review_ref']); job_ok(inv['result'])
    need(inv['actual_exit']==0 and inv['wrapper_error'] is None,'actual registration failed')
    for name in ('stdout','stderr'): need(inv[name+'_sha256']==pin(output/(name+'.raw'))['sha256'],'actual raw mismatch')
    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired)),'seal current four mismatch')
    intent=pin(output/'canonical-write.intent.json'); verified=pin(output/'canonical-write.verified.json')
    need(doc(verified)['intent_ref']==intent,'verified intent')
    for i,name in enumerate(CANON[:2]): need(doc(pin(output/('canonical-write.'+Path(name).stem+'.done.json')))['sha256']==p['desired_refs'][i]['sha256'],'completion row')
    git_guard(b,output,'seal')
    need(all((ROOT/x).read_bytes()==r for x,r in zip(CANON,desired)),'post-source-guard seal four CAS')
    save(output/'registration-audit.json',{'actor':'codex:/root','status':'ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE',
        'before':b['before'],'after':b['after'],'actual_registration_exit':0,'invocation_ref':invref,
        'intent_ref':intent,'verified_ref':verified,'review_ref':inv['review_ref'],'formal_increment':0})
    entries=[pin(x) for x in sorted(output.rglob('*')) if x.is_file() and x.name!='manifest.json']
    save(output/'manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})

def grant(b,output,scope_ref):
    global OWNED_GRANT_ROOT, OWNED_GRANT_PREFLIGHT_ROOT
    scope=doc(scope_ref)
    reviewed_scope_match(b,scope)
    need(scope['new_grant_preflight_root']==b['new_grant_preflight_root'],'full-scope preflight path binding')
    pf=safe(scope['new_grant_preflight_root'],False)
    root=safe(scope['new_authorization_root'],False)
    others=[safe(scope[k],False) for k in ('output_root','outer_output_root','export_root')]
    need(pf.is_relative_to(DESKTOP_RECEIPTS) and b['run_uuid'] in pf.name,'bounded preflight leaf/UUID')
    roots=[pf,root,*others]
    need(len(set(roots))==5 and all(not x.is_relative_to(y) for x in roots for y in roots if x!=y),'five disjoint leaves')
    need(pf.parent.is_dir() and root.parent.is_dir() and all(not os.path.lexists(p) for p in roots),'fresh preflight/auth/execution leaves')
    pf.mkdir()
    OWNED_GRANT_PREFLIGHT_ROOT=pf
    save(pf/'preflight.started.json',{'actor':'codex:/root','at':now(),'scope_ref':scope_ref,
        'authorization_leaf_created':False,'automatic_retry':False,'counter_reset':False})
    gate=load_module(b['authorization_gate_ref'],'root_cli43_gate_grant')
    reader=gate.Reader()
    gate.load_scope(reader,str(safe(scope_ref['path'])),scope_ref['sha256'])

    # These are real preflight point snapshots, not yet grant-directory originals.
    preliminary=[]
    for x in CANON:
        preliminary.append({'canonical_path':x,
            'ref':write(pf/(Path(x).stem+'.original.json'),(ROOT/x).read_bytes())})
    rr=gate.registration_refs(reader,scope)
    ar=gate.validate_authority(reader,scope,scope_ref,preliminary,rr)
    need(all((ROOT/x['canonical_path']).read_bytes()==verify(x['ref']) for x in preliminary),'sealed-authority live four CAS')
    save(pf/'sealed-authority.verified.json',{'at':now(),'registration_refs':rr,
        'authority_review_refs':ar,'canonical_copies':preliminary,'authorization_leaf_created':False})

    def facts(label):
        started=now(); records=None; observation=None; error=None
        try:
            records,observation=git_guard(b,pf,label)
            return records,observation
        except BaseException as e:
            error=repr(e)
            raise
        finally:
            # Individual child invocation/raw/result carries actual native status.
            # This parent timing record never converts an earlier exit into its own native exit.
            try:
                save(pf/(label+'.time-window.json'),{'started_at':started,'ended_at':now(),
                    'Git_records':records,'runtime_observation_ref':observation,'error':error,
                    'actual_stage_native_exit':None,'point_in_time_only':True})
            except BaseException as secondary:
                if error is None: raise
                sys.stderr.write(json.dumps({'first_cause':error,'secondary_receipt_error':repr(secondary),
                    'actual_stage_native_exit':None,'phase':label},ensure_ascii=False)+'\n')

    first_records,first_observed=facts('admission')
    need(all((ROOT/x['canonical_path']).read_bytes()==verify(x['ref']) for x in preliminary),'post-admission live four CAS')
    admission=save(pf/'admission.verified.json',{'at':now(),'scope_ref':scope_ref,
        'sealed_authority_ref':pin(pf/'sealed-authority.verified.json'),
        'actual_Git_records':first_records,'time_window_ref':pin(pf/'admission.time-window.json'),
        'canonical_copies':preliminary,'authorization_leaf_created':False})
    # No authorization directory exists until both sealed authority and actual Git/live-four facts pass.
    need(all(not os.path.lexists(p) for p in [root,*others]),'auth/execution leaf appeared during preflight')
    root.mkdir()
    OWNED_GRANT_ROOT=root
    save(pf/'authorization-leaf.created.json',{'at':now(),'path':str(root),'admission_ref':admission,
        'directory_is_not_grant':True,'source_acceptance':False})

    copied={}
    def copy_fact(source):
        source=safe(source)
        need(source.parent==pf,'only direct owned preflight facts copied')
        original=pin(source); raw=verify(original)
        dest=root/source.name
        if source.name in copied:
            pair=copied[source.name]
            need(pair['original_ref']==original and verify(pair['copy_ref'])==raw,'copied fact drift')
            return pair['copy_ref']
        copied_ref=write(dest,raw)
        need(copied_ref['sha256']==original['sha256'] and copied_ref['bytes']==original['bytes'],'byte-identical fact copy')
        copied[source.name]={'original_ref':original,'copy_ref':copied_ref}
        return copied_ref

    copies=[{'canonical_path':x['canonical_path'],'ref':copy_fact(safe(x['ref']['path']))} for x in preliminary]
    # Re-evaluate the real registration chain using actual authorization copies before final Git.
    ar=gate.validate_authority(reader,scope,scope_ref,copies,rr)
    ar.update({'CLI2_qualification_ref':scope['current58_CLI2_qualification_ref'],
        'CLI2_review_ref':scope['current58_CLI2_review_ref'],'CLI2_manifest_ref':scope['current58_CLI2_manifest_ref']})
    final_records,final_observed=facts('grant-final')
    _,_,after_observed=runtime(b,pf,'grant-final.runtime.after')
    observed=[]
    for phase,r in zip(OBSERVATION_PHASES,(first_observed,final_observed,after_observed)):
        need(safe(r['path'])==pf/(phase+'.json'),'actual observation producer/path mismatch')
        copyref=copy_fact(safe(r['path']))
        observed.append({'path':str(safe(copyref['path'])),'sha256':copyref['sha256'],'bytes':copyref['bytes']})
    need([r['path'] for r in observed]==scope['expected_runtime_observation_paths'],'actual ordered observation selection differs from frozen scope')
    preflight_pre=save(pf/'prelaunch.json',{'runtime_observation_refs':observed,'runtime_resources_ref':scope['runtime_resources_ref'],
        'toolchain_lock_ref':b['toolchain_lock_ref'],'git':final_records,
        'source_round':'grant-final','time_window_ref':pin(pf/'grant-final.time-window.json'),
        'admission_ref':admission,'point_in_time_only':True,
        'raw_reference_semantics':'Git records retain original preflight raw paths; all copied bytes are linked separately'})
    # Copy unchanged original fact bytes. Do not rewrite original argv, time, refs or native result fields.
    for p in sorted(pf.iterdir()):
        if p.is_file():copy_fact(p)
    pre=copy_fact(safe(preflight_pre['path']))
    save(root/'preflight-copy-map.json',{'preflight_root':str(pf),'entries':list(copied.values()),
        'time_boundary':'admission before auth mkdir; independent grant-final Git after auth mkdir; live four immediately before grant',
        'directory_or_copy_is_not_authority':True})
    need(all((ROOT/x['canonical_path']).read_bytes()==verify(x['ref']) for x in copies),'immediate pre-grant live four CAS')
    need(all(not os.path.lexists(p) for p in others),'fresh execution leaves appeared before grant')
    gr=save(root/'authorization.execute.json',{'schema':'researchos.desktop58-finite-authorization.v1','actor':'codex:/root',
        'status':'ROOT_REGISTERED_EXECUTION_AUTHORIZED','actual_registration_completed':True,'scope_ref':scope_ref,
        'binding':gate.binding(scope),'canonical_copies':copies,'registration_refs':rr,'authority_review_refs':ar,
        'prelaunch_evidence_ref':pre,'runtime_observation_refs':observed,
        'fresh_roots_observed_absent':[scope[k] for k in ('output_root','outer_output_root','export_root')],
        'automatic_retry':False,'counter_reset':False})
    gate.validate_grant(str(safe(scope_ref['path'])),scope_ref['sha256'],str(root/'authorization.execute.json'),gr['sha256'])
    save(root/'grant.completed.json',{'grant_ref':gr,'source_acceptance':False,'formal_increment':0,
        'launcher_executions':0,'preflight_root':str(pf),'point_in_time_not_lifecycle':True})
    pf_members=[pin(p) for p in sorted(pf.rglob('*')) if p.is_file()]
    save(pf/'manifest.json',{'entries':pf_members,'count':len(pf_members),'excluded_only_self':True})
    members=[pin(p) for p in sorted(root.rglob('*')) if p.is_file()]
    save(root/'manifest.json',{'entries':members,'count':len(members),'excluded_only_self':True})


def main(mode):
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'-I -S -X utf8 required')
    sys.dont_write_bytecode=True
    ap=argparse.ArgumentParser()
    ap.add_argument('--binding-ref',required=True,help='Exact JSON path/SHA/bytes; every future input explicit')
    ap.add_argument('--output',required=True)
    ap.add_argument('--scope-ref',required=mode in ('prepare','grant'))
    ap.add_argument('--review-ref',required=mode in ('register','run'))
    ap.add_argument('--scope-template-ref',required=mode=='scope')
    a=ap.parse_args(); out=None; first=None
    try:
        br=argref(a.binding_ref); b=binding(br,mode)
        candidate=safe(a.output)
        need(candidate.is_relative_to(RECEIPTS/'integration_codex') and candidate.relative_to(ROOT).as_posix()==b['registration_namespace'],'exact Root registration output')
        out=candidate
        # Each phase has one immutable attempt; no retry of the same prepared input.
        save(out/(mode+'.started.json'),{'mode':mode,'binding_ref':br,'at':now(),'automatic_retry':False})
        if mode=='scope': scope_build(b,argref(a.scope_template_ref),out/'scope_registration.json')
        elif mode=='prepare': prepare(b,argref(a.scope_ref),out)
        elif mode=='register': register(b,out,argref(a.review_ref))
        elif mode=='run': run_registration(b,out,argref(a.review_ref))
        elif mode=='seal': seal(b,out)
        elif mode=='grant': grant(b,out,argref(a.scope_ref))
        else: raise RuntimeError('unknown mode')
        return 0
    except BaseException as e:
        first={'phase':mode,'error':repr(e),'traceback':traceback.format_exc(),'actual_stage_native_exit':None,
               'actual_outer_tool_exit':None,'automatic_retry':False,'counter_reset':False,'rollback':False}
        try:
            if OWNED_GRANT_PREFLIGHT_ROOT is not None:
                save(OWNED_GRANT_PREFLIGHT_ROOT/'failure.origin.json',first)
                members=[pin(p) for p in sorted(OWNED_GRANT_PREFLIGHT_ROOT.rglob('*')) if p.is_file()]
                save(OWNED_GRANT_PREFLIGHT_ROOT/'manifest.partial.json',{'entries':members,'count':len(members),'grant_usable':False})
            if OWNED_GRANT_ROOT is not None:
                save(OWNED_GRANT_ROOT/'failure.origin.json',first)
                members=[pin(p) for p in sorted(OWNED_GRANT_ROOT.rglob('*')) if p.is_file()]
                save(OWNED_GRANT_ROOT/'manifest.partial.json',{'entries':members,'count':len(members),'grant_usable':False})
            elif OWNED_GRANT_PREFLIGHT_ROOT is None and out is not None: save(out/('failure.'+mode+'.json'),first)
        except BaseException as secondary:
            first['secondary_receipt_error']=repr(secondary)
        sys.stderr.write(json.dumps(first,ensure_ascii=False)+'\n')
        return 1
