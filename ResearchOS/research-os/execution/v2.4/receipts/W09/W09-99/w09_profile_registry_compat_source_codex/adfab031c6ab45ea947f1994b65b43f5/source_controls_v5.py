"""Finite pure Source controls; synthetic role captures confer no authority."""
import sys
sys.dont_write_bytecode=True
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import tempfile
import traceback

Q=Path(__file__).resolve().parent
R=Q.parents[6]
checks=[]
originals={}
index={'__name__':'synthetic_v5_index'}
profile={'__name__':'synthetic_v5_profile'}
exec(compile((Q/'formal_case_index.after.py').read_bytes(),'SOURCE_index','exec'),index)
exec(compile((Q/'formal_profile_w09.after.py').read_bytes(),'SOURCE_profile','exec'),profile)
api=index['_profile_api']()

def require_control(label,fn):
    value=fn();checks.append({'id':label,'status':'PASS_SOURCE_ONLY'});return value

def reject(label,fn,code):
    try:fn()
    except index['InvalidEvidence'] as exc:
        assert exc.code==code,(label,exc.code,code)
        checks.append({'id':label,'status':'PASS_SOURCE_ONLY','rejection_code':exc.code})
    else:raise AssertionError(label+': invalid evidence accepted')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def clone(obj):return copy.deepcopy(obj)
def encode(obj):return (json.dumps(obj,ensure_ascii=False,sort_keys=True)+'\n').encode('utf-8')

class RoleFixture:
    def __init__(self,root):
        self.root=Path(root)
        self.serial=0
        self.log=self.root/'synthetic-original-public-audit.jsonl'
        self.header=encode({'type':'session_meta','ordinal':0,'payload':{'id':profile['ROOT_THREAD_ID']}})
        self.log.write_bytes(self.header)
        self.auth='codex:/root/source-author-synthetic'
        self.review='codex:/root/verifier-synthetic'
        scope=self.put('scope',{'schema':'researchos.w09.synthetic-scope.v1','issued_by':'codex:/root','source_actor':self.auth,'slice_id':'W09_FULL_FORMAL_ASSEMBLY','routes':['test.retrieval','test.research.fixture','test.security']})
        mode=self.put('mode',{'schema':'researchos.w09-mode-decision.v2','producer_id':'codex:/root','reviewer_id':self.review,'reviewer_role':'INDEPENDENT_NON_AUTHOR','decision':'QUALIFIED'})
        owner=self.put('owner',{'owner_id':'codex:/root','selected_worker_id':'codex:/root','scope_ref':scope,'lease_status':'ACTIVE','lease_expires_at':'2026-10-10T20:00:00Z','routes':['test.retrieval','test.research.fixture','test.security']})
        self.scope,self.mode,self.owner=scope,mode,owner
        self.context={'run_id':'SOURCE_SYNTHETIC_NOTFORMAL','executor_id':'codex:/root','created_at':'2026-10-09T18:00:00Z'}
        roles={'source_authors':[self.auth],'executor':'codex:/root','assembler':'codex:/root','verifier':self.review,'root_observer':'codex:/root'}
        rows=[('SOURCE_AUTHOR',self.auth,'ROOT_SCOPE_REGISTRATION',scope,'/source_actor'),('EXECUTOR','codex:/root','ACTUAL_MODE_DECISION',mode,'/producer_id'),('EVIDENCE_ASSEMBLER','codex:/root','ROOT_OWNER_REGISTRATION',owner,'/selected_worker_id'),('VERIFIER',self.review,'ACTUAL_MODE_DECISION',mode,'/reviewer_id'),('ROOT_OBSERVER','codex:/root','ROOT_SCOPE_REGISTRATION',scope,'/issued_by')]
        proofs=[]
        for role,actor,kind,ref,pointer in rows:
            raw={k:ref[k] for k in ('path','sha256')};raw['locator']={'json_pointer':pointer}
            proofs.append({'role':role,'actor_id':actor,'origin_kind':kind,'raw_ref':raw,'actual_audit_ref':self.audit(role,actor,ref['sha256'])})
        self.registry={'schema':'researchos.w09.execution-role-registry.v1','writer_actor':'codex:/root','run_id':self.context['run_id'],'roles':roles,'provenance':proofs,'route_execution_refs':[{'command_key':k,'check_id':c,'case_id':i,'scope_ref':scope,'owner_ref':owner} for k,c,i in profile['ROUTES']]}
        self.install()
    def put(self,name,doc,relative=None):
        self.serial+=1
        relative=relative or profile['SOURCE_PREFIX']+'synthetic-source-only/'+str(self.serial)+'-'+name+'.json'
        path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True)
        raw=encode(doc);path.write_bytes(raw)
        return {'path':relative,'sha256':digest(raw),'bytes':len(raw)}
    def audit(self,role,actor,binding):
        number=self.serial*10+1
        if actor=='codex:/root':
            call={'type':'response_item','ordinal':number,'payload':{'type':'function_call','call_id':'SOURCE_SYNTHETIC_'+str(number),'name':'Source_only_control','arguments':json.dumps({'binding':binding})}}
            result={'type':'response_item','ordinal':number+1,'payload':{'type':'function_call_output','call_id':'SOURCE_SYNTHETIC_'+str(number),'output':binding}}
        else:
            call={'type':'inter_agent_communication_metadata','ordinal':number,'timestamp':'2026-10-09T17:00:00Z','payload':{'trigger_turn':False}}
            result={'type':'response_item','ordinal':number+1,'timestamp':call['timestamp'],'metadata':{'client_authored':False},'payload':{'type':'agent_message','author':actor,'recipient':'/root','content':[{'type':'input_text','text':'SOURCE_SYNTHETIC_NOTFORMAL '+binding}]}}
        first,second=encode(call),encode(result)
        old=self.log.read_bytes();offsets=[0,len(old),len(old)+len(first)]
        self.log.write_bytes(old+first+second)
        raw=self.header+first+second
        relative=profile['ROOT_ORIGIN_PREFIX']+'synthetic-source-only/'+str(self.serial)+'-'+role+'.jsonl'
        path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        capture={'path':relative,'sha256':digest(raw),'bytes':len(raw)}
        doc={'schema':'researchos.w09.actual-role-audit.v1','actor_id':actor,'role':role,'Root_thread_id':profile['ROOT_THREAD_ID'],'source_audit_path':str(self.log),'source_line_offsets':offsets,'original_line_sha256':[digest(part) for part in (self.header,first,second)],'source_prefix_size_observed':len(old+first+second),'original_capture_ref':capture,'binding_sha256':binding}
        return self.put('audit-'+role,doc)
    def install(self):
        ref=self.put('registry',self.registry,profile['ROLE_REGISTRY_PATH'])
        self.context['role_policy']={'schema':profile['ROLE_POLICY_SCHEMA'],'registry_ref':ref}
        path=self.root/'execution/v2.4/checkpoint.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(encode({'work_in_progress':{'w09_execution_role_registry_ref':ref}}))
    def validate(self):
        profile['ROOT_SOURCE_AUDIT_LOG']=str(self.log)
        reader=index['Reader'](self.root);reader.w09_audit_ranges=[]
        result=profile['_role_registry'](api,reader,self.context)
        reader.finish()
        assert len(reader.w09_audit_ranges)==15
        return result

def main():
    directory=Q/'synthetic-temp';directory.mkdir(exist_ok=True)
    tempfile.tempdir=str(directory)
    output=io.StringIO()
    with contextlib.redirect_stdout(output):runpy.run_path(str(Q/'source_controls_v4.py'),run_name='source_v4_controls_preserved')
    inherited=json.loads(output.getvalue())
    assert inherited['scope']=='SYNTHETIC_NONAUTHORITATIVE' and inherited['formal_acceptance'] is False
    with (Q/'source-controls-v4.result.json').open('xb') as stream:stream.write((json.dumps(inherited,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    require_control('V4_ORIGINAL_46_CONTROLS_PRESERVED',lambda:len(inherited['checks'])==46 or (_ for _ in ()).throw(AssertionError('v4 check count')))
    with tempfile.TemporaryDirectory(dir=directory,prefix='dual-prefix-') as name:
        root=Path(name)
        for prefix in (profile['NATIVE_PREFIX'],profile['SOURCE_PREFIX']):
            rel=prefix+'synthetic/tool-run.json';path=root/rel;path.parent.mkdir(parents=True)
            raw=encode({'schema':'SOURCE_ONLY'});path.write_bytes(raw)
            ref={'path':rel,'sha256':digest(raw)}
            require_control('NATIVE_TOOL_PREFIX_'+('NATIVE' if prefix==profile['NATIVE_PREFIX'] else 'SOURCE'),lambda ref=ref:profile['_native_tool_doc'](api,index['Reader'](root),ref))
            reject('TOOL_HASH_'+str(len(checks)),lambda ref=dict(ref,sha256='0'*64):profile['_native_tool_doc'](api,index['Reader'](root),ref),'HASH_MISMATCH')
        reject('TOOL_OUTSIDE_BOTH_PREFIXES',lambda:profile['_native_tool_doc'](api,index['Reader'](root),{'path':'outside.json','sha256':'0'*64}),'PATH_SCOPE')
        reject('TOOL_PREFIX_TRAVERSAL',lambda:profile['_native_tool_doc'](api,index['Reader'](root),{'path':profile['NATIVE_PREFIX']+'../outside.json','sha256':'0'*64}),'PATH_ESCAPE')
    archive=json.loads((Q/'inputs/commands.CM39.actual-archive.json').read_text(encoding='utf-8'))
    registry=json.loads((Q/'commands.after.json').read_text(encoding='utf-8'))
    current=digest((Q/'commands.after.json').read_bytes())
    for n,key in enumerate(('test.research.fixture','test.retrieval')):
        receipt=json.loads((Q/('inputs/C19-'+str(n)+'-dispatcher_receipt_ref.json')).read_text(encoding='utf-8'))
        allowed=profile['LEGACY_C19_RECEIPTS'][key]
        row={'command_key':key,'check_id':'','case_id':'C19','receipt_ref':{k:allowed[k] for k in ('path','sha256')}}
        call=lambda row=row,receipt=receipt,registry=registry:profile['_historical_registry'](api,index['Reader'](R),row,receipt,registry,current)
        require_control('EXACT_QUALIFIED_CM39_'+key,lambda:call() is True or (_ for _ in ()).throw(AssertionError('not exact historical')))
        for label,field,value in [('BAD_SELECTOR','case_id','A06'),('BAD_CHECK','check_id','W09-G01'),('UNKNOWN_KEY','command_key','test.security')]:
            bad=dict(row);bad[field]=value
            reject(key+'_'+label,lambda bad=bad:profile['_historical_registry'](api,index['Reader'](R),bad,receipt,registry,current),'LEGACY_RECEIPT_NOT_ALLOWED')
        bad=clone(row);bad['receipt_ref']['sha256']='0'*64
        reject(key+'_THIRD_RECEIPT_SHA',lambda:profile['_historical_registry'](api,index['Reader'](R),bad,receipt,registry,current),'LEGACY_RECEIPT_NOT_ALLOWED')
        bad=clone(row);bad['receipt_ref']['path']='execution/invocations/unknown/receipt.json'
        reject(key+'_THIRD_RECEIPT_PATH',lambda:profile['_historical_registry'](api,index['Reader'](R),bad,receipt,registry,current),'LEGACY_RECEIPT_NOT_ALLOWED')
        reject(key+'_WRONG_OLD_REGISTRY_SHA',lambda:profile['_historical_registry'](api,index['Reader'](R),row,dict(receipt,registered_command_revision='0'*64),registry,current),'LEGACY_RECEIPT_NOT_ALLOWED')
        for label,change in [('CM_REV',lambda d:d.update(revision=41)),('ARGV',lambda d:d['commands'][key]['argv'].append('untrusted')),('STATE',lambda d:d['commands'][key].update(state='UNBOUND')),('UNRELATED',lambda d:d['commands']['test.domain']['argv'].append('untrusted'))]:
            bad=clone(registry);change(bad)
            reject(key+'_SEMANTICS_'+label,lambda bad=bad:profile['_historical_registry'](api,index['Reader'](R),row,receipt,bad,current),'REGISTRY_SEMANTICS_CHANGED')
        require_control(key+'_LOGICAL_CM39_INPUT_ARCHIVE',lambda:profile['_dispatcher_input'](api,index['Reader'](R),{'path':'execution/v2.4/commands.json','sha256':profile['CM39_ARCHIVE']['sha256']},{},True,'C19'))
        reject(key+'_LOGICAL_CM39_INPUT_HASH',lambda:profile['_dispatcher_input'](api,index['Reader'](R),{'path':'execution/v2.4/commands.json','sha256':'0'*64},{},True,'C19'),'DISPATCH_INPUT_UNPINNED')
        source=receipt['input_versions'][0]
        reject(key+'_CURRENT_SOURCE_PIN_MISSING',lambda:profile['_dispatcher_input'](api,index['Reader'](R),source,{},True,'C19'),'DISPATCH_INPUT_UNPINNED')
    assert registry['commands']==profile['_cm40_commands'](archive)
    assert archive['commands']['test.security']['selectors']['check_id']==registry['commands']['test.security']['selectors']['check_id']
    assert 'W17' in registry['commands']['test.security']['selectors']['task_id']
    assert registry['commands']['test.security']['tool_env']['RESEARCHOS_GO']=='go'
    require_control('CM40_FOUR_ROUTES_ONLY_W17_FALLBACK_PRESERVED',lambda:True)
    def role_case(label,mutate,code):
        with tempfile.TemporaryDirectory(dir=directory,prefix='roles-') as name:
            f=RoleFixture(name);mutate(f);f.install()
            reject(label,f.validate,code)
    with tempfile.TemporaryDirectory(dir=directory,prefix='roles-positive-') as name:
        f=RoleFixture(name)
        roles=require_control('ROOT_EXECUTOR_OBSERVER_PEER_VERIFIER_WITH_RAW_AUDIT_SYNTHETIC',f.validate)
        context=f.context
        review={'reviewer_id':f.review,'executor_id':'codex:/root','issuer_id':f.review}
        issuance={'actor':'codex:/root','observer_id':'codex:/root','issuer_id':f.review,'executor_id':'codex:/root','reviewer_id':f.review}
        owner={'executor_id':'codex:/root','verifier_id':f.review}
        require_control('VERIFIER_ISSUER_ROOT_OBSERVER',lambda:profile['_independent_roles'](api,roles,context,review,issuance,owner))
        for label,badreview,badissuance,badowner in [('ISSUER_CHANGED_TO_ROOT',dict(review,issuer_id='codex:/root'),issuance,owner),('ISSUANCE_ISSUER_CHANGED',review,dict(issuance,issuer_id='codex:/root'),owner),('SELF_REVIEW',dict(review,reviewer_id='codex:/root'),issuance,owner),('ROOT_OWN_MESSAGE_NOT_PEER_ISSUANCE',review,dict(issuance,reviewer_id='codex:/root'),owner),('OWNER_VERIFIER_RELABEL',review,issuance,dict(owner,verifier_id='codex:/root'))]:
            reject(label,lambda a=badreview,b=badissuance,c=badowner:profile['_independent_roles'](api,roles,context,a,b,c),'INDEPENDENT_ACTOR')
        row={'command_key':'test.retrieval','check_id':'','case_id':'C19'}
        receipt={'started_at':'2026-10-09T13:27:52Z','ended_at':'2026-10-09T13:27:55Z'}
        decision={'producer_id':'codex:/root'}
        require_control('ACTUAL_MODE_ROOT_SELECTED_WORKER_SCOPE_LEASE_SYNTHETIC',lambda:profile['_route_execution_actor'](api,index['Reader'](f.root),row,receipt,decision,roles))
        reject('SOURCE_AUTHOR_CANNOT_RELABEL_NATIVE_EXECUTOR',lambda:profile['_route_execution_actor'](api,index['Reader'](f.root),row,receipt,{'producer_id':f.auth},roles),'EXECUTOR_ORIGIN')
        reject('ORIGINAL_ROUTE_LEASE_EXPIRED',lambda:profile['_route_execution_actor'](api,index['Reader'](f.root),row,dict(receipt,ended_at='2026-10-11T13:27:55Z'),decision,roles),'EXECUTION_LEASE')
    role_case('UNKNOWN_ACTOR_PROVENANCE',lambda f:f.registry['provenance'][0].update(actor_id='unknown'),'ROLE_PROVENANCE')
    role_case('FORGED_ROLE_ORIGIN',lambda f:f.registry['provenance'][1].update(origin_kind='SOURCE_AUTHOR_CLAIM'),'ROLE_PROVENANCE')
    role_case('SOURCE_AUTHOR_SELF_VERIFIER',lambda f:f.registry['roles'].update(verifier=f.auth),'INDEPENDENT_ACTOR')
    role_case('ROOT_SELF_VERIFIER',lambda f:f.registry['roles'].update(verifier='codex:/root'),'INDEPENDENT_ACTOR')
    role_case('SOURCE_AUTHOR_IMPERSONATES_EXECUTOR',lambda f:(f.context.update(executor_id=f.auth),f.registry['roles'].update(executor=f.auth)),'ROLE_PROVENANCE')
    role_case('MISSING_ACTUAL_AUDIT',lambda f:f.registry['provenance'][0].pop('actual_audit_ref'),'MISSING_FIELD')
    def corrupt_audit(f,field,value):
        proof=f.registry['provenance'][0]
        doc=json.loads((f.root/proof['actual_audit_ref']['path']).read_text(encoding='utf-8'))
        doc[field]=value
        proof['actual_audit_ref']=f.put('changed-audit',doc)
    role_case('AUDIT_FORGED_BINDING',lambda f:corrupt_audit(f,'binding_sha256','0'*64),'ROLE_ACTUAL_AUDIT')
    role_case('AUDIT_FORGED_OFFSETS',lambda f:corrupt_audit(f,'source_line_offsets',[0,1,2]),'ROLE_ACTUAL_AUDIT')
    role_case('AUDIT_UNKNOWN_ACTOR',lambda f:corrupt_audit(f,'actor_id','codex:/root'),'ROLE_ACTUAL_AUDIT')
    role_case('AUDIT_ORIGINAL_PREFIX_TOO_SHORT',lambda f:corrupt_audit(f,'source_prefix_size_observed',1),'ROLE_ACTUAL_AUDIT')
    def expired_assembly(f):
        origin=json.loads((f.root/f.owner['path']).read_text(encoding='utf-8'))
        origin['lease_expires_at']='2026-10-01T00:00:00Z'
        ref=f.put('expired-owner',origin)
        proof=next(x for x in f.registry['provenance'] if x['role']=='EVIDENCE_ASSEMBLER')
        proof['raw_ref']={k:ref[k] for k in ('path','sha256')};proof['raw_ref']['locator']={'json_pointer':'/selected_worker_id'}
    role_case('ASSEMBLY_EXPIRED_LEASE',expired_assembly,'EXECUTION_LEASE')
    ast.parse((Q/'candidate-root/execution/v2.4/formal_profile_w09.py').read_bytes())
    report={'schema':'researchos.w09-profile-v5-finite-controls.v1','scope':'SYNTHETIC_NONAUTHORITATIVE','status':'PASS_SOURCE_ONLY','inherited_v4_count':len(inherited['checks']),'new_control_count':len(checks),'checks':checks,'actual_native_runs':0,'actual_dispatcher_runs':0,'actual_model_runs':0,'actual_SQLite_runs':0,'new_actual_role_or_formal_captures':0,'formal_acceptance':False,'role_authority':'PENDING_ROOT_ACTUAL_ISSUANCE_AND_SCOPE_REGISTRATION','product_execution_status':'NOTRUN'}
    with (Q/'source-controls-v5.result.json').open('xb') as stream:stream.write((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    directory.rmdir()
    print(json.dumps({'new_control_count':len(checks),'inherited_v4_count':len(inherited['checks']),'formal_acceptance':False,'status':'PASS_SOURCE_ONLY'},ensure_ascii=False))

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:
        traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code))
    raise SystemExit(code)
