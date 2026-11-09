"""Future Root-only driver18 producer. Source preparation, never self-authorizing.

Actions consume exact REF JSON arguments. Nothing runs at import. The unchanged
consumer is used for final authority/prepare verification; no fixture success is
invented here. Partial CAS failures are forward-only and cannot be retried here.
"""
import argparse,copy,datetime,hashlib,json,os,sys,time,traceback,types
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
RECEIPTS=ROOT/'execution/v2.4/receipts/W05/W05-99'
GATE={'path':'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_binding_terminal_pairing_preparation_codex/f38b92cdbd4844529ce3da03d08630ad/authority_adapter.v3.proposed.py','sha256':'c391a1673856c4ff072474639bbcd843b0e87cb1910cef6db4bf1386b2fbc1c7','bytes':38021}
BINDER={'path':'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_binding_terminal_pairing_preparation_codex/f38b92cdbd4844529ce3da03d08630ad/binding_adapter.v3.proposed.py','sha256':'d2ad4dd777e1b5dfe2d96c20a1a36cfe25d245630fe3474e984f1c4276bc4f6b','bytes':9563}
CANON=['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/step_state.json','execution/v2.4/commands.json']
FLAGS=['-I','-S','-X','utf8']
OWN=None
STAGE='ENTRY'
def need(ok,why):
    if not ok:raise ValueError(why)
def parse(raw):
    def pairs(rows):
        d={}
        for k,v in rows:need(k not in d,'DUPLICATE_KEY');d[k]=v
        return d
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def safe(text):
    p=Path(text);need(p.is_absolute() and '..' not in p.parts and p.resolve()==p,'CANONICAL_ABSOLUTE_PATH')
    for q in [p,*p.parents]:
        if os.path.lexists(q):need(not q.is_symlink() and not getattr(q.lstat(),'st_file_attributes',0)&0x400,'ALIAS')
    return p
def pin(p):
    p=safe(str(p));b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(ref):
    need(isinstance(ref,dict) and set(ref)=={'path','sha256','bytes'},'EXACT_REF')
    p=safe(str(Path(ref['path'])));b=p.read_bytes()
    need(type(ref['bytes']) is int and len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256'],'PIN')
    return b
def module(ref,name):
    b=verify(ref);m=types.ModuleType(name);m.__file__=ref['path'];sys.modules[name]=m
    exec(compile(b,ref['path'],'exec'),m.__dict__);return m
def gate():return module(GATE,'driver18_producer_gate')
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def write(p,b):
    p=safe(str(p))
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
def save(p,v):return write(p,encoded(v))
def leaf(text):
    global OWN
    p=safe(text);need(p!=RECEIPTS and p.is_relative_to(RECEIPTS) and p.parent.is_dir() and not os.path.lexists(p),'FRESH_OWNED_RECEIPT_LEAF')
    p.mkdir();OWN=p;return p
def immutable_manifest(out,extra=()):
    refs=[pin(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json']
    for ref in extra:
        verify(ref)
        if ref not in refs:refs.append(ref)
    need(len({str(safe(r['path'])).casefold() for r in refs})==len(refs),'MANIFEST_COLLISION')
    return save(out/'manifest.json',{'files':refs,'excluded_only_self':True})
def live4(raws):
    need(len(raws)==4 and all((ROOT/p).read_bytes()==b for p,b in zip(CANON,raws)),'ALL_FOUR_CAS')
def load(sref):
    g=gate();r=g.Reader();s=g.scope(r,sref)
    need(s['authority_validator_ref']['sha256']==GATE['sha256'],'FROZEN_GATE')
    return g,r,s
def runtime(g,r,s,out,label):
    res=r.doc(s['resource_catalog_ref']);rows=res['files']
    for ref in rows:r.verify(ref)
    allowed={str(g.safe(ref['path'])).casefold():ref for ref in rows}
    code=[pin(Path(__file__).resolve()),pin(Path(sys.modules['__main__'].__file__).resolve()),GATE,BINDER]
    for ref in code+[s['utility_ref'],s['owned_helper_ref']]:
        key=str(g.safe(ref['path'])).casefold()
        need(key in allowed and g.same_ref(allowed[key],ref),'METADATA_CODE_NOT_PREPINNED')
    need(g.same_ref(pin(Path(sys.executable).resolve()),res['python']),'ACTUAL_PYTHON')
    helper=module(s['owned_helper_ref'],'driver18_root_owned')
    util=module(s['utility_ref'],'driver18_root_util')
    obs=util.module_observation(rows,helper)
    obs['all_observed_inputs_pre_pinned']=True
    save(out/(label+'.runtime.json'),obs)
    return helper,res
def owned(g,helper,argv,cwd,env,timeout,out,label):
    result=None;first=None;so=out/(label+'.stdout.raw');se=out/(label+'.stderr.raw')
    try:
        with so.open('xb') as a,se.open('xb') as b:result=helper.run_owned(argv,cwd,env,a,b,timeout)
    except BaseException as e:first={'error':repr(e),'traceback':traceback.format_exc()}
    item={'argv':argv,'cwd':cwd,'env':env,'timeout':timeout,'result':result,'actual_native_exit':None if result is None else result.get('actual_exit'),'first_cause':first,'stdout_ref':pin(so) if so.exists() else None,'stderr_ref':pin(se) if se.exists() else None,'automatic_retry':False,'counter_reset':False}
    save(out/(label+'.owned.json'),item)
    need(first is None,'OWNED_CALL_EXCEPTION');g.job(result);return item
def source_guard(g,r,s,out,label,canonical_refs):
    helper,res=runtime(g,r,s,out,label);a=s['actual_Root_registration'];want=a['source_guard_expected'];git=a['source_guard_git_ref']
    r.verify(git);need(any(g.same_ref(git,x) for x in res['files']),'GIT_NOT_CATALOGUED')
    env=dict(s['public_environment']);env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',GIT_CONFIG_KEY_1='core.untrackedCache',GIT_CONFIG_VALUE_1='false')
    records={}
    for name,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','--untracked-files=no']),('index',['diff','--cached','--name-only'])]:
        item=owned(g,helper,[git['path'],'-C',str(ROOT),*args],str(ROOT),env,min(30,a['registration_timeout_seconds']),out,label+'.'+name)
        raw=r.verify(item['stdout_ref'])
        if name=='head':need(raw.decode('ascii').strip()==want['head'],'HEAD')
        elif name=='status':need(len(raw)==want['status_bytes'] and hashlib.sha256(raw).hexdigest()==want['status_sha256'],'STATUS')
        else:need(raw==b'' and want['index_empty'] is True,'INDEX')
        records[name]=item
    return save(out/(label+'.source-guard.json'),{'schema':'researchos.driver18-root-source-guard.v1','actor':'codex:/root','run_uuid':a['run_uuid'],'main_git':want,'canonical_refs':canonical_refs,'git':records,'Python_observation':'POINT_IN_TIME_NOT_LIFECYCLE'})

def resource_catalog(inp,out):
    """Caller supplies an explicit finite union; no downloads/discovery/copy/Go."""
    x=parse(verify(inp));g=gate();r=g.Reader();need(x['schema']=='researchos.driver18-root-resource-input.v1','RESOURCE_INPUT')
    rows=[];seen=set()
    for item in x['files']:
        r.verify(item);k=g.path_key(g.safe(item['path']));need(k not in seen,'RESOURCE_COLLISION');seen.add(k);rows.append(item)
    need(rows and 0<len(x['compiler_images'])<=61,'FINITE_RESOURCE_SET')
    for item in [x['python'],x['go'],*x['compiler_images']]:need(any(g.same_ref(item,v) for v in rows),'RESOURCE_TOOL')
    need(x['python']['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b' and x['go']['sha256']=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490','PINNED_TOOLS')
    dest=set()
    for item in x['offline_modcache_copies']:
        p=Path(item['relative_path']);need(not p.is_absolute() and not p.drive and '..' not in p.parts and p.parts,'OFFLINE_PATH')
        need(str(p).casefold() not in dest,'OFFLINE_COLLISION');dest.add(str(p).casefold())
        need(not (p.parts[0].casefold()=='modernc.org' and len(p.parts)>1 and p.parts[1].casefold()=='sqlite@v1.60.1'),'PRISTINE_OVERWRITE')
        need(any(g.same_ref(item['ref'],v) for v in rows),'OFFLINE_SOURCE')
    for item in x['provenance_refs']:r.verify(item)
    r.unchanged();return save(out/'resource-catalog.json',{k:x[k] for k in ['files','python','go','GOROOT','compiler_images','offline_modcache_copies']}|{'provenance_refs':x['provenance_refs'],'actual_graph':'OPEN_NOT_RUN','source_acceptance':False})

def stage_sources(out):
    """Root later stages immutable reviewed bytes before binding any scope."""
    engine=write(out/'driver18_root_producer.py',Path(__file__).read_bytes())
    refs={}
    for role,entry in [('register','register_entry'),('wrapper','wrapper_entry')]:
        source='import hashlib,sys,types\nfrom pathlib import Path\nsys.dont_write_bytecode=True\nREF='+repr(engine)+'\nraw=Path(REF["path"]).read_bytes()\nif len(raw)!=REF["bytes"] or hashlib.sha256(raw).hexdigest()!=REF["sha256"]:raise RuntimeError("PRODUCER_PIN")\nm=types.ModuleType("root_driver18_producer");m.__file__=REF["path"];sys.modules[m.__name__]=m\nexec(compile(raw,REF["path"],"exec"),m.__dict__)\nsys.exit(m.entry("'+entry+'",sys.argv[1:]))\n'
        refs[role]=write(out/('register.py' if role=='register' else 'run.py'),source.encode())
    return save(out/'staged-code.json',{'producer_ref':engine,'gate_ref':GATE,'binder_ref':BINDER,**refs,'actual_CAS':False,'actual_grant':False})

def prepare_scope(inp,out):
    g=gate();r=g.Reader();b=module(BINDER,'driver18_root_binder');s=b.build_scope(g,r,inp)
    ref=save(out/'scope.proposed.json',s);g.scope(r,ref);r.unchanged();return ref
def prepare_draft(sref,cref,stage_ref,out):
    g,r,s=load(sref);a=s['actual_Root_registration'];stage=r.doc(stage_ref)
    need(out.is_relative_to(g.safe(a['registration_namespace'])),'DRAFT_NS')
    for item in stage.values():
        if isinstance(item,dict) and set(item)=={'path','sha256','bytes'}:r.verify(item)
    need(stage['gate_ref']==GATE and stage['binder_ref']==BINDER,'STAGED_FROZEN_CONSUMERS')
    copies=[{'canonical_path':p,'ref':write(out/(Path(p).stem+'.captured.json'),(ROOT/p).read_bytes())} for p in CANON]
    copiesref=save(out/'four-canonical-copies.json',{'entries':copies})
    b=module(BINDER,'driver18_root_binder');b.draft(g,r,sref,cref,copiesref,out)
    dref=pin(out/'registration.draft.json');d=r.doc(dref)
    prepared=save(out/'prepared_refs.json',{'schema':'researchos.driver18-registration-prepared-refs.v1','current_scope_ref':sref,'registration_draft_ref':dref,'canonical_paths':CANON,'original_refs':d['original_refs'],'desired_refs':d['desired_refs'],'current_root_lease':g.lease(s,sref)})
    preaudit=save(out/'preaudit.json',{'schema':'researchos.driver18-registration-preexecution-audit.v1','actual_registration_executed':False,'current_scope_ref':sref,'registration_draft_ref':dref,'original_refs':d['original_refs'],'desired_refs':d['desired_refs']})
    codes={'register':stage['register'],'wrapper':stage['wrapper'],'prepared_refs':prepared,'audit':preaudit}
    index=save(out/'draft-index.json',{'scope_ref':sref,'draft_ref':dref,'producer_ref':stage['producer_ref'],'codes':codes,'stage_ref':stage_ref})
    r.unchanged();live4([r.verify(x) for x in d['original_refs']])
    return save(out/'draft-manifest.json',{'members':[sref,dref,index,stage_ref,stage['producer_ref'],GATE,BINDER,*codes.values(),*d['original_refs'],*d['desired_refs']],'actual_registration':False})

def reviewed(dref,regref):
    g=gate();r=g.Reader();d=r.doc(dref);sref=d['scope_ref'];s=g.scope(r,sref);a=s['actual_Root_registration']
    index=r.doc(pin(g.safe(dref['path']).parent/'draft-index.json'));codes=index['codes'];mfref=pin(g.safe(dref['path']).parent/'draft-manifest.json')
    need(index['draft_ref']==dref and index['scope_ref']==sref,'INDEX_DRAFT')
    g.member_manifest(r,mfref,[sref,dref,*codes.values(),index['producer_ref'],*d['original_refs'],*d['desired_refs']])
    need(g.same_ref(pin(Path(__file__).resolve()),index['producer_ref']),'ACTUAL_REVIEWED_PRODUCER')
    rv=r.doc(regref);need(g.safe(regref['path'])==g.safe(a['registration_review_path']),'REVIEW_PATH')
    need(rv['schema']=='researchos.root-registration-source-review.v1' and rv['reviewer'] in g.REVIEWERS and rv['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and rv['requested_changes']==[] and rv['actual_registration_executed'] is False,'NONAUTHOR_REGISTRATION_REVIEW')
    for key,want in [('expected_before',a['before']),('expected_after',a['after']),('current_scope_ref',sref),('registration_draft_ref',dref),('registration_draft_manifest_ref',mfref),('canonical_paths',CANON),('original_refs',d['original_refs']),('desired_refs',d['desired_refs']),('current_root_lease',g.lease(s,sref)),('producer_ref',index['producer_ref'])]:need(rv[key]==want,'REVIEW_'+key)
    for k,v in codes.items():need(rv[k+'_sha256']==v['sha256'],'REVIEW_CODE_'+k);r.verify(v)
    before=[r.verify(x) for x in d['original_refs']];desired=[r.verify(x) for x in d['desired_refs']]
    need(len(before)==len(desired)==4 and before[2:]==desired[2:],'TWO_WRITES')
    need(len(rv['copied_canonical_before_refs'])==4,'REVIEW_COPIES')
    for x,b in zip(rv['copied_canonical_before_refs'],before):need(g.safe(x['path']).parent==g.safe(regref['path']).parent and r.verify(x)==b,'REVIEW_ORIGINAL_BYTES')
    oldcp,oldow=map(parse,before[:2]);cp,ow=map(parse,desired[:2]);cut=r.doc(s['actual_origin_cut'])
    need([oldcp['revision'],oldow['revision'],len(oldcp['failure_counters'])]==a['before'] and [cp['revision'],ow['revision'],len(cp['failure_counters'])]==a['after'],'TUPLES')
    need(cut['before']==a['before'] and cut['after']==a['after'] and cut['counter_reset'] is False and cp['failure_counters']==oldcp['failure_counters']+cut['origins'],'FAILURE_PREFIX')
    seen=set()
    for row in cut['origins']:
        ref=row['evidence_ref'];need(row['original_payload']==r.doc(ref) and row['counter_reset'] is False and ref['sha256'] not in seen and all(x.get('evidence_ref',{}).get('sha256')!=ref['sha256'] for x in oldcp['failure_counters']),'ORIGIN_RECOUNT_OR_REWRITE');seen.add(ref['sha256'])
    prefix='f08_driver18_'+a['phase'];cref=cp['work_in_progress'][prefix+'_controller_review_ref'];cr=r.doc(cref)
    need(g.safe(cref['path'])==g.safe(a['controller_review_path']) and cr['reviewer'] in g.REVIEWERS and cr['schema']=='researchos.driver18-bound-controller-review.v1' and cr['decision']=='READY_FOR_ROOT_DRIVER18_'+a['phase'].upper()+'_ONCE' and cr['requested_changes']==[] and cr['scope_sha256']==sref['sha256'] and cr['mode']=='PARTIAL_17_EXPLICIT','BOUND_REVIEW')
    for k in ['controller_ref','launcher_ref','authority_validator_ref','utility_ref','owned_helper_ref','debug_helper_ref']:need(cr['code_refs'][k]==s[k],'BOUND_CODE')
    need(cp['work_in_progress'][prefix+'_scope_ref']==sref and a['lease_key'] not in oldow['special_paths'] and ow['special_paths'][a['lease_key']]==g.lease(s,sref),'CURRENT_LEASE')
    pc=copy.deepcopy(cp);po=copy.deepcopy(ow)
    for obj,old,keys in [(pc,oldcp,['revision','expected_previous_revision','updated_at','updated_by','failure_counters']),(po,oldow,['revision','amended_at','amended_by'])]:
        for k in keys:
            if k in old:obj[k]=old[k]
            else:obj.pop(k,None)
    for k in [prefix+'_scope_ref',prefix+'_controller_review_ref']:
        if k in oldcp['work_in_progress']:pc['work_in_progress'][k]=oldcp['work_in_progress'][k]
        else:pc['work_in_progress'].pop(k,None)
    po['special_paths'].pop(a['lease_key']);need(pc==oldcp and po==oldow,'UNRELATED_CANONICAL_FIELDS')
    need(d['schema']=='researchos.driver18-root-registration-draft.v1' and d['canonical_paths']==CANON and d['before']==a['before'] and d['after']==a['after'] and d['current_root_lease']==g.lease(s,sref),'DRAFT_BINDING')
    need(d['registration_metadata_paths']==CANON[:2] and d['actual_registration_executed'] is False and d['source_acceptance'] is False and d['invocation_contract']=={'cwd':str(ROOT),'env':s['public_environment'],'timeout':a['registration_timeout_seconds'],'output_root':str(g.safe(a['registration_output_root'])),'registration_review_path':a['registration_review_path']},'DRAFT_WRITE_AND_INVOCATION_BOUNDARY')
    need(r.doc(codes['prepared_refs'])=={'schema':'researchos.driver18-registration-prepared-refs.v1','current_scope_ref':sref,'registration_draft_ref':dref,'canonical_paths':CANON,'original_refs':d['original_refs'],'desired_refs':d['desired_refs'],'current_root_lease':g.lease(s,sref)},'PREPARED_REFS_EXACT')
    preaudit=r.doc(codes['audit'])
    need(preaudit['schema']=='researchos.driver18-registration-preexecution-audit.v1' and preaudit['actual_registration_executed'] is False and preaudit['current_scope_ref']==sref and preaudit['registration_draft_ref']==dref and preaudit['original_refs']==d['original_refs'] and preaudit['desired_refs']==d['desired_refs'],'PREEXECUTION_AUDIT')
    return g,r,s,sref,d,index,mfref,before,desired

def request_for(g,s,sref,dref,regref,index,out):
    a=s['actual_Root_registration'];res=parse(verify(s['resource_catalog_ref']));codes=index['codes']
    argv=[res['python']['path'],*FLAGS,codes['register']['path'],'--registration-draft',dref['path'],'--draft-sha256',dref['sha256'],'--registration-review',regref['path'],'--review-sha256',regref['sha256'],'--output-root',str(out)]
    return {'schema':'researchos.driver18-registration-request.v1','actor':'codex:/root','argv':argv,'cwd':str(ROOT),'env':s['public_environment'],'timeout':a['registration_timeout_seconds'],'current_scope_ref':sref,'registration_draft_ref':dref,'review_ref':regref,'stdout_ref_path':str(out/'stdout.raw'),'stderr_ref_path':str(out/'stderr.raw'),'automatic_retry':False,'counter_reset':False}

def register_entry(argv):
    ap=argparse.ArgumentParser();ap.add_argument('--registration-draft',required=True);ap.add_argument('--draft-sha256',required=True);ap.add_argument('--registration-review',required=True);ap.add_argument('--review-sha256',required=True);ap.add_argument('--output-root',required=True);x=ap.parse_args(argv)
    dref=pin(safe(x.registration_draft));regref=pin(safe(x.registration_review));need(dref['sha256']==x.draft_sha256 and regref['sha256']==x.review_sha256,'ARGUMENT_PINS')
    g,r,s,sref,d,index,mfref,before,desired=reviewed(dref,regref);a=s['actual_Root_registration'];out=safe(x.output_root)
    need(out==g.safe(a['registration_output_root']),'REGISTRATION_OUT');reqref=pin(out/'requested.json');need(r.doc(reqref)==request_for(g,s,sref,dref,regref,index,out),'ORIGINAL_REQUEST')
    # Root-created request directory is fixed; each writer is exclusive once.
    marker=write(out/'register.started',b'ONCE\n');live4(before)
    source_guard(g,r,s,out,'register-before',[{'canonical_path':p,'ref':v} for p,v in zip(CANON,d['original_refs'])]);r.unchanged();live4(before)
    common={'current_scope_ref':sref,'registration_draft_ref':dref,'requested_ref':reqref}
    intent=save(out/'canonical-write.intent.json',common|{'actor':'codex:/root','transition':{k:[a['before'][i],a['after'][i]] for i,k in enumerate(['checkpoint','ownership','failures'])},'metadata':[{'path':p,'original_ref':d['original_refs'][i],'desired_ref':d['desired_refs'][i]} for i,p in enumerate(CANON[:2])],'unchanged':[{'path':CANON[i],'sha256':d['original_refs'][i]['sha256']} for i in [2,3]],'review_ref':regref,'automatic_retry':False,'recovery':'FORWARD_ONLY_SEPARATE_ROOT_DECISION_NO_AUTOMATIC_RETRY_OR_ROLLBACK'})
    expected=list(before)
    for i,name in enumerate(CANON[:2]):
        target=ROOT/name;tmp=target.with_name(target.name+'.driver18-'+a['run_uuid']+'.tmp');write(tmp,desired[i])
        r.unchanged();source_guard(g,r,s,out,'pre-replace-'+str(i),[{'canonical_path':p,'ref':d['desired_refs'][j] if j<i else d['original_refs'][j]} for j,p in enumerate(CANON)])
        live4(expected);os.replace(tmp,target);expected[i]=desired[i];need(target.read_bytes()==desired[i],'OWN_WRITE')
        save(out/('canonical-write.'+target.stem+'.done.json'),{'intent_ref':intent,'sha256':d['desired_refs'][i]['sha256']})
    live4(desired);r.unchanged();source_guard(g,r,s,out,'register-after',[{'canonical_path':p,'ref':v} for p,v in zip(CANON,d['desired_refs'])]);live4(desired)
    save(out/'canonical-write.verified.json',common|{'checkpoint':a['after'][0],'ownership':a['after'][1],'failure_origins':a['after'][2],'step_state_commands_unchanged':True,'intent_ref':intent});return 0

def wrapper_entry(argv):
    ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--request-sha256',required=True);x=ap.parse_args(argv)
    reqref=pin(safe(x.request));need(reqref['sha256']==x.request_sha256,'REQUEST_SHA');req=parse(verify(reqref))
    g,r,s,sref,d,index,mfref,before,desired=reviewed(req['registration_draft_ref'],req['review_ref']);out=safe(reqref['path']).parent
    need(req==request_for(g,s,sref,req['registration_draft_ref'],req['review_ref'],index,out),'EXACT_WRAPPER_REQUEST');live4(before)
    write(out/'wrapper.started',b'ONCE\n');helper,res=runtime(g,r,s,out,'wrapper-before');result=None;error=None
    try:
        with Path(req['stdout_ref_path']).open('xb') as so,Path(req['stderr_ref_path']).open('xb') as se:result=helper.run_owned(req['argv'],str(ROOT),req['env'],so,se,req['timeout'])
    except BaseException as e:error=repr(e)
    finally:
        save(out/'invocation.json',{'actor':'codex:/root','actual_exit':None if result is None else result.get('actual_exit'),'result':result,'wrapper_error':error,'automatic_retry':False,'counter_reset':False,'argv':req['argv'],'cwd':req['cwd'],'env':req['env'],'timeout':req['timeout'],'requested_ref':reqref,'current_scope_ref':sref,'registration_draft_ref':req['registration_draft_ref'],'review_ref':req['review_ref'],'runner_sha256':index['codes']['register']['sha256'],'wrapper_sha256':index['codes']['wrapper']['sha256'],'stdout_sha256':pin(out/'stdout.raw')['sha256'] if (out/'stdout.raw').exists() else None,'stderr_sha256':pin(out/'stderr.raw')['sha256'] if (out/'stderr.raw').exists() else None})
    need(error is None,'WRAPPER_EXCEPTION');g.job(result);return 0

def run_registration(dref,regref):
    global OWN
    g,r,s,sref,d,index,mfref,before,desired=reviewed(dref,regref);a=s['actual_Root_registration'];out=leaf(a['registration_output_root'])
    live4(before);reqref=save(out/'requested.json',request_for(g,s,sref,dref,regref,index,out));helper,res=runtime(g,r,s,out,'outer-before')
    args=[res['python']['path'],*FLAGS,index['codes']['wrapper']['path'],'--request',reqref['path'],'--request-sha256',reqref['sha256']]
    result=None;error=None
    try:
        with (out/'wrapper.stdout.raw').open('xb') as so,(out/'wrapper.stderr.raw').open('xb') as se:result=helper.run_owned(args,str(ROOT),s['public_environment'],so,se,a['registration_timeout_seconds']+5)
    except BaseException as e:error=repr(e)
    finally:
        save(out/'wrapper-invocation.json',{'actor':'codex:/root','argv':args,'cwd':str(ROOT),'env':s['public_environment'],'requested_ref':reqref,'inner_invocation_ref':pin(out/'invocation.json') if (out/'invocation.json').exists() else None,'result':result,'error':error,'actual_native_exit':None if result is None else result.get('actual_exit'),'automatic_retry':False,'counter_reset':False})
    need(error is None,'OUTER_WRAPPER_EXCEPTION');g.job(result);live4(desired)
    return pin(out/'wrapper-invocation.json')

def seal_registration(dref,regref):
    g,r,s,sref,d,index,mfref,before,desired=reviewed(dref,regref);a=s['actual_Root_registration'];out=g.safe(a['registration_output_root'])
    invref=pin(out/'invocation.json');inv=r.doc(invref);wrref=pin(out/'wrapper-invocation.json');wr=r.doc(wrref);g.job(inv['result']);g.job(wr['result'])
    need(inv['wrapper_error'] is None and wr['error'] is None,'REGISTRATION_FAILURE');reqref=pin(out/'requested.json');need(r.doc(reqref)==request_for(g,s,sref,dref,regref,index,out),'SEALED_REQUEST')
    intent=pin(out/'canonical-write.intent.json');verified=pin(out/'canonical-write.verified.json');live4(desired);r.unchanged()
    source_guard(g,r,s,out,'seal',[{'canonical_path':p,'ref':v} for p,v in zip(CANON,d['desired_refs'])]);live4(desired)
    copies=[{'canonical_path':p,'ref':write(out/(Path(p).stem+'.after.json'),(ROOT/p).read_bytes())} for p in CANON];live4(desired)
    audit=save(out/'registration-audit.json',{'actor':'codex:/root','status':'ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE','before':a['before'],'after':a['after'],'actual_registration_exit':inv['actual_exit'],'intent_ref':intent,'invocation_ref':invref,'verified_ref':verified,'review_ref':regref,'current_scope_ref':sref,'registration_draft_ref':dref,'requested_ref':reqref,'wrapper_invocation_ref':wrref,'draft_manifest_ref':mfref,'formal_increment':0})
    extra=[dref,mfref,sref,regref,*index['codes'].values(),*d['original_refs'],*d['desired_refs'],index['producer_ref']]
    manifest=immutable_manifest(out,extra)
    bundle={'schema':'researchos.driver18-root-registration-evidence.v1','draft_ref':dref,'draft_manifest_ref':mfref,'audit_ref':audit,'intent_ref':intent,'invocation_ref':invref,'requested_ref':reqref,'wrapper_invocation_ref':wrref,'verified_ref':verified,'stdout_ref':pin(out/'stdout.raw'),'stderr_ref':pin(out/'stderr.raw'),'manifest_ref':manifest,'registration_code_and_draft_refs':index['codes'],'canonical_after_copies':copies}
    g.registration(r,s,sref,bundle);r.unchanged();live4(desired)
    return save(g.safe(a['registration_namespace'])/('registration-bundle-'+a['phase']+'.json'),bundle)

def grant(sref,bundleref,prepared_proof_ref,preflight,authroot):
    g,r,s=load(sref);a=s['actual_Root_registration'];bundle=r.doc(bundleref);desired=g.registration(r,s,sref,bundle)
    pf=leaf(preflight);auth=safe(authroot);need(auth.parent.is_dir() and not os.path.lexists(auth) and auth.is_relative_to(RECEIPTS) and a['run_uuid'] in auth.name and a['run_uuid'] in pf.name and not (auth.is_relative_to(pf) or pf.is_relative_to(auth)),'FRESH_DISJOINT_AUTH')
    for k in ['prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']:
        q=g.safe(s[k]);need(not (auth==q or auth.is_relative_to(q) or q.is_relative_to(auth)),'AUTH_EXECUTION_OVERLAP')
    proof=None if prepared_proof_ref is None else r.doc(prepared_proof_ref)
    if a['phase']=='execute':need(proof is not None,'REAL_PREPARE_REQUIRED');g.prepared_evidence(r,s,proof)
    else:need(proof is None,'NO_FUTURE_PREPARE_FACT')
    live4(desired);r.unchanged();source_guard(g,r,s,pf,'preflight',bundle['canonical_after_copies']);live4(desired)
    # No authorization directory is created until real registration/source/CAS pass.
    auth.mkdir();copies=[{'canonical_path':p,'ref':write(auth/(Path(p).stem+'.json'),raw)} for p,raw in zip(CANON,desired)]
    r.unchanged();facts=source_guard(g,r,s,auth,'grant-current',copies);live4(desired)
    value={'schema':'researchos.driver18-root-phase-grant.v1','actor':'codex:/root','actual_registration_completed':True,'phase':a['phase'],'run_uuid':a['run_uuid'],'scope_ref':sref,'registration_evidence_ref':bundleref,'canonical_snapshot_refs':copies,'authority_code_refs':{k:s[k] for k in g.FIXED}|{'authority_validator_ref':s['authority_validator_ref']},'root_source_guard_ref':facts,'prepared_evidence':proof,'automatic_retry':False,'counter_reset':False}
    g.verify_authority(r,s,sref,value);r.unchanged()
    # Full authority/resource reads above may be slow: refresh actual Git facts,
    # then immediately recheck all four targets before writing the grant.
    value['root_source_guard_ref']=source_guard(g,r,s,auth,'grant-final',copies);live4(desired)
    return save(auth/'phase-grant.json',value)

def action_identity(s,sref,gref,phase):
    res=parse(verify(s['resource_catalog_ref']))
    return {'launcher_ref':s['launcher_ref'],'argv':[res['python']['path'],*FLAGS,s['launcher_ref']['path'],phase,sref['path'],sref['sha256'],gref['path'],gref['sha256']],'cwd':str(ROOT),'phase':phase,'scope_ref':sref,'grant_ref':gref,'run_uuid':s['actual_Root_registration']['run_uuid']}
def launch_request(sref,gref,out):
    g,r,s=load(sref);value=r.doc(gref);g.verify_authority(r,s,sref,value);a=s['actual_Root_registration'];phase=a['phase']
    need(not os.path.lexists(g.safe(s[phase+'_launcher_output_root'])) and not os.path.lexists(g.safe(s[phase+'_output_root'])),'FRESH_PHASE_OUTPUT')
    desired=g.registration(r,s,sref,r.doc(value['registration_evidence_ref']));live4(desired);r.unchanged();source_guard(g,r,s,out,'launch-current',value['canonical_snapshot_refs']);live4(desired)
    ident=action_identity(s,sref,gref,phase)
    # Literal PowerShell array quoting, not JSON escaping or expression interpolation.
    quoted=["'"+v.replace("'","''")+"'" for v in ident['argv']]
    command='& '+quoted[0]+' '+ ' '.join(quoted[1:])+'; exit $LASTEXITCODE'
    req={'cmd':command,'workdir':str(ROOT),'yield_time_ms':1000,'max_output_tokens':4000}
    return save(out/'exec-command.input.json',req),save(out/'command-identity.json',ident)

def capture_action(sref,gref,kind,inputref,responseref,request_locator,response_locator,initialref,out):
    g,r,s=load(sref);g.verify_authority(r,s,sref,r.doc(gref));phase=s['actual_Root_registration']['phase'];identity=action_identity(s,sref,gref,phase)
    inp=r.doc(inputref);response=r.doc(responseref)
    need(isinstance(request_locator,str) and request_locator and isinstance(response_locator,str) and response_locator,'ACTUAL_TOOL_EVENT_LOCATORS_REQUIRED')
    if kind=='exec_command':
        need(initialref is None and g.safe(inp['workdir'])==ROOT and isinstance(inp['cmd'],str) and type(response.get('session_id')) is int and response.get('exit_code') is None,'REAL_ASYNC_INITIAL_REQUIRED')
        quoted=["'"+v.replace("'","''")+"'" for v in identity['argv']]
        need(inp['cmd']=='& '+quoted[0]+' '+ ' '.join(quoted[1:])+'; exit $LASTEXITCODE','ACTUAL_DISPATCHED_COMMAND')
    else:
        need(kind=='write_stdin' and initialref is not None,'ACTUAL_TERMINAL_INPUT_REQUIRED');ia=r.doc(initialref);ir=r.doc(ia['response_ref'])
        need(ia['tool_name']=='exec_command' and ia['command_identity']==identity and set(inp)<={'session_id','chars','yield_time_ms','max_output_tokens'} and type(inp['session_id']) is int and inp['session_id']==ir['session_id'] and inp.get('chars','')=='' and request_locator!=ia['request_event_locator'],'ORIGINAL_SESSION_PAIR')
        if 'session_id' in response:need(response['session_id']==inp['session_id'],'RESPONSE_SESSION')
        need(type(response.get('exit_code')) is int,'TERMINAL_RESULT_REQUIRED')
    # Copy caller-supplied original bytes, never reconstruct a response or locator.
    iref=write(out/'original-input.json',r.verify(inputref));rref=write(out/'original-response.json',r.verify(responseref))
    return save(out/'tool-action.json',{'schema':'researchos.driver18-original-tool-action.v1','actor':'codex:/root','tool_name':kind,'input_ref':iref,'response_ref':rref,'initial_action_ref':initialref,'command_identity':identity,'request_event_locator':request_locator,'response_event_locator':response_locator})

def seal_outer(sref,gref,initialref,terminalref,out):
    g,r,s=load(sref);phase=s['actual_Root_registration']['phase'];identity=action_identity(s,sref,gref,phase);ia=r.doc(initialref);ta=r.doc(terminalref);first=r.doc(ia['response_ref']);last=r.doc(ta['response_ref'])
    need(ia['command_identity']==ta['command_identity']==identity and ta['initial_action_ref']==initialref,'ACTUAL_ACTION_PAIR')
    original={'schema':'researchos.driver18-root-outer-invocation.v1','actor':'codex:/root','cwd':str(ROOT),'argv':identity['argv'],'run_uuid':identity['run_uuid'],'scope_ref':sref,'grant_ref':gref,'launcher_output_root':s[phase+'_launcher_output_root'],'inner_output_root':s[phase+'_output_root'],'session_id':first['session_id'],'tool_initial_result_ref':ia['response_ref'],'tool_initial_action_ref':initialref,'tool_initial_input_ref':ia['input_ref'],'tool_command':r.doc(ia['input_ref'])['cmd']}
    originalref=save(out/'outer-invocation.json',original)
    completion={'schema':'researchos.driver18-root-outer-completion.v1','actor':'codex:/root','phase':phase,'run_uuid':identity['run_uuid'],'launcher_ref':s['launcher_ref'],'argv':identity['argv'],'scope_ref':sref,'outer_invocation_ref':originalref,'tool_result_ref':ta['response_ref'],'terminal_tool_action_ref':terminalref,'session_id':first['session_id'],'tool_completion_session_id':r.doc(ta['input_ref'])['session_id'],'actual_outer_exit':last['exit_code'],'actual_native_launcher_exit':None,'automatic_retry':False,'counter_reset':False}
    cref=save(out/'outer-completion.json',completion)
    # A nonzero terminal result has already been preserved; it cannot become a proof.
    g.outer_completion(r,cref,s,sref,gref,phase);r.unchanged();return cref

def seal_prepare(sref,gref,outerref,out):
    g,r,s=load(sref);need(s['actual_Root_registration']['phase']=='prepare','PREPARE_ONLY');g.verify_authority(r,s,sref,r.doc(gref));inner=g.safe(s['prepare_output_root']);launcher=g.safe(s['prepare_launcher_output_root'])
    proof={'prepare_scope_ref':sref,'prepare_grant_ref':gref,'outer_completion_ref':outerref}
    for key,name in [('prepared_ref','prepared.json'),('inner_result_ref','result.json'),('inner_manifest_ref','manifest.json')]:proof[key]=pin(inner/name)
    for key,name in [('launcher_invocation_ref','inner.invocation.json'),('launcher_requested_ref','requested.json'),('launcher_completed_ref','completed.json'),('launcher_manifest_ref','manifest.json'),('launcher_stdout_ref','stdout.raw'),('launcher_stderr_ref','stderr.raw')]:proof[key]=pin(launcher/name)
    inv=r.doc(proof['launcher_invocation_ref'])
    pair={'schema':'researchos.driver18-root-sealed-launcher-pair.v1','actor':'codex:/root','scope_ref':sref,'grant_ref':gref,'launcher_ref':s['launcher_ref'],'controller_ref':s['controller_ref'],'launcher_output_root':str(launcher),'inner_output_root':str(inner),'requested_ref':proof['launcher_requested_ref'],'invocation_ref':proof['launcher_invocation_ref'],'stdout_ref':proof['launcher_stdout_ref'],'stderr_ref':proof['launcher_stderr_ref'],'completed_ref':proof['launcher_completed_ref'],'outer_completion_ref':outerref,'launcher_manifest_ref':proof['launcher_manifest_ref'],'inner_manifest_ref':proof['inner_manifest_ref'],'prepared_ref':proof['prepared_ref'],'inner_result_ref':proof['inner_result_ref'],'actual_child_pid':inv['result']['owned_child_pid'],'creation_time_100ns':inv['result']['creation_time_100ns'],'actual_native_exit':inv['actual_native_exit'],'automatic_retry':False,'counter_reset':False}
    proof['launcher_pairing_ref']=save(out/'launcher-pair.json',pair)
    # This is a local expected prepare view, not an emitted execute scope or grant.
    view=dict(s);view['prepared_ref']=proof['prepared_ref'];g.prepared_evidence(r,view,proof);r.unchanged()
    return save(out/'prepare-proof.json',proof)

def entry(action,args):
    global STAGE,OWN
    sys.dont_write_bytecode=True;first=None;secondary=[];result=None
    try:
        need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'PYTHON_I_S_UTF8');STAGE=action
        if action in ['register_entry','wrapper_entry']:return globals()[action](args)
        ap=argparse.ArgumentParser();ap.add_argument('--input-ref',required=True);ap.add_argument('--output-root',required=True);x=ap.parse_args(args)
        inp=parse(x.input_ref.encode());data=parse(verify(inp));out=leaf(x.output_root)
        save(out/'producer-request.json',{'action':action,'input_ref':inp,'actualargv':sys.argv,'cwd':str(Path.cwd()),'automatic_retry':False,'counter_reset':False})
        if action=='resources':result=resource_catalog(inp,out)
        elif action=='stage-code':result=stage_sources(out)
        elif action=='scope':result=prepare_scope(inp,out)
        elif action=='draft':result=prepare_draft(data['scope_ref'],data['controller_review_ref'],data['staged_code_ref'],out)
        elif action=='register':result=run_registration(data['draft_ref'],data['registration_review_ref'])
        elif action=='seal-registration':result=seal_registration(data['draft_ref'],data['registration_review_ref'])
        elif action=='grant':result=grant(data['scope_ref'],data['registration_bundle_ref'],data['prepared_proof_ref'],data['new_preflight_root'],data['new_authorization_root'])
        elif action=='launch-request':result=launch_request(data['scope_ref'],data['grant_ref'],out)
        elif action=='capture-action':result=capture_action(data['scope_ref'],data['grant_ref'],data['tool_name'],data['original_input_ref'],data['original_response_ref'],data['request_event_locator'],data['response_event_locator'],data['initial_action_ref'],out)
        elif action=='seal-outer':result=seal_outer(data['scope_ref'],data['grant_ref'],data['initial_action_ref'],data['terminal_action_ref'],out)
        elif action=='seal-prepare':result=seal_prepare(data['scope_ref'],data['grant_ref'],data['outer_completion_ref'],out)
        else:raise ValueError('UNKNOWN_ACTION')
        save(out/'completed.json',{'action':action,'result_ref':result,'source_acceptance':False,'formal_increment':0,'counter_reset':False,'reported_exit':0});immutable_manifest(out)
    except BaseException as e:
        first={'stage':STAGE,'error':repr(e),'traceback':traceback.format_exc(),'actual_native_exit':None,'automatic_retry':False,'counter_reset':False,'recovery':'FORWARD_ONLY_NO_RETRY_NO_ROLLBACK'}
        if OWN is not None:
            try:save(OWN/('failure.'+str(time.time_ns())+'.json'),first)
            except BaseException as second:secondary.append(repr(second))
        sys.stderr.write(json.dumps({'first_cause':first,'secondary':secondary},ensure_ascii=False)+'\n')
    return 1 if first else 0
if __name__=='__main__':
    try:exit_code=entry(sys.argv[1],sys.argv[2:])
    except BaseException as exc:sys.stderr.write(json.dumps({'stage':'ENTRY','error':repr(exc),'actual_native_exit':None})+'\n');exit_code=1
    sys.exit(exit_code)
