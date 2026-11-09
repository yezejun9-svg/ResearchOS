"""SOURCE ONLY: Root's future seven-target adoption. No product command runs.

All seven business files are held with Windows shareMode=0 until verification
or rollback completes. Ordinary exceptions roll back under the same handles.
This is not an OS crash-atomic multi-file transaction: durable intent retains
complete before/after bytes for explicit Root recovery after process loss.
"""
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

R = Path('D:/作品集/ResearchOS/research-os')
N = R/'execution/v2.4/receipts/W09/W09-99/main_c19_source_registry_integration_codex/mainc19-1a11f84'
OUT = N/'actual-adoption'
W = R/'execution/v2.4/receipts/W09/W09-99'
AUTHOR = 'codex:/root/command_queue_impl'
ROOT_ACTOR = 'codex:/root'
REL = ('internal/domain/domain_test.go','internal/domain/retrieval_test.go',
       'ops/ci/retrieval.py','internal/domain/w09_evidence_export_test.go',
       'ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py',
       'execution/v2.4/commands.json')
TARGETS = tuple(R/p for p in REL)
EXISTING = (0,1,2,6)
NEW = (3,4,5)
CANON = tuple(R/'execution/v2.4'/f'{n}.json' for n in ('checkpoint','path_ownership','step_state','commands'))
SOURCE_PINS = (
 ('83b0a57fcd3dd9a58f8c7493b2a164efe91aa04bbf87b1c11f7477b413093aac',28018),
 ('518c6dbd8dbb774b88434138fd3f10f3e231843acf83f086a1ad7a381e2ffe69',31296),
 ('9d94366591e1620c62abd27c34a8e513499cf10f8fdeaf741fe2e5a20b63e0c2',14509),
 ('7862750e160532ee36d5fd3daa436e39e7a42cc1ea03884d129150ff7ce6ee2e',12362),
 ('d3b942b1c413ee6ea725ce68519651e02c2ebf6f152c32cf671e31c0c2c6bd56',21522),
 ('1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777',42716))
SOURCE_V6 = W/'w09_evidence_v6_source_preparation_codex/7e91acb06d354c0aa87b5f30ab9951d0'
SOURCE_PATHS = tuple(SOURCE_V6/p for p in ('domain_test.v6.proposed.go','retrieval_test.v6.proposed.go',
    'retrieval.v6.proposed.py','w09_evidence_export_test.v6.proposed.go','w09_formal_router.v6.proposed.py')) + (
    W/'w09_evidence_v7_fragment_source_codex/fragv7-1a11f30/w09_evidence_closure.v7.proposed.py',N/'commands.proposed.json')
SOURCE_ROSTER = ('adapters/retrieval/local.go','adapters/retrieval/local_test.go',
 'adapters/retrieval/identity_windows.go','adapters/retrieval/identity_unix.go',
 'internal/domain/retrieval.go','internal/domain/retrieval_local.go','internal/domain/evidence_origin.go',
 'internal/domain/retrieval_test.go','internal/domain/w09_evidence_export_test.go','internal/domain/domain_test.go',
 'internal/domain/http.go','internal/domain/context.go','internal/domain/materialize.go','internal/domain/contracts.go',
 'migrations/sqlite/0007_retrieval.sql','migrations/sqlite/0009_retrieval_root_identity.sql',
 'ops/ci/retrieval.py','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py','go.mod','go.sum')
GP = R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GP_PIN = dict(path=str(GP),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
MAX = 256*1024*1024
RECEIPT_NAMES = {'intent.json','committed.json','failed.json','owned-handles.cleanup.actual.json',
                 'input-guard.cleanup.actual.json','outcome.json'}

def require(value, message):
    if not value: raise ValueError(message)

def digest(raw): return hashlib.sha256(raw).hexdigest()

def exact_path(p, absent=False):
    p = Path(p)
    require(p.is_absolute() and str(p)==str(p.absolute()) and '..' not in p.parts,'ABSOLUTE_CANONICAL_PATH')
    for ancestor in reversed((p,*p.parents)):
        if not ancestor.exists():
            require(absent and ancestor==p,'MISSING_PARENT_OR_INPUT')
            continue
        s=ancestor.lstat()
        require(not ancestor.is_symlink() and not ancestor.is_junction()
                and not (getattr(s,'st_file_attributes',0)&0x400),'REPARSE_PATH')
    require(p.resolve(strict=not absent)==p,'PATH_ALIAS')
    return p

def raw_pin(p, raw): return dict(path=str(p),sha256=digest(raw),bytes=len(raw))

def read_ref(ref):
    require(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'EXACT_REF_FIELDS')
    require(type(ref['path']) is str and type(ref['sha256']) is str and len(ref['sha256'])==64
            and all(c in '0123456789abcdef' for c in ref['sha256'])
            and type(ref['bytes']) is int and 0<=ref['bytes']<=MAX,'REF_TYPES')
    p=exact_path(ref['path'])
    require(str(p)==ref['path'] and p.is_file(),'REGULAR_CANONICAL_REF')
    with p.open('rb') as f:raw=f.read(ref['bytes']+1)
    require(raw_pin(p,raw)==ref,'REF_PIN_DRIFT')
    return raw

def pin(p):
    p=exact_path(p)
    with p.open('rb') as f:raw=f.read(MAX+1)
    require(len(raw)<=MAX,'FILE_CAP')
    return raw_pin(p,raw)

def save(name, value):
    require(name in RECEIPT_NAMES,'FIXED_RECEIPT_NAME')
    exact_path(OUT)
    target=OUT/name
    exact_path(target,absent=True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with target.open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    return raw_pin(target,raw)

def manifest_refs(href,mref):
    h=json.loads(read_ref(href));m=json.loads(read_ref(mref))
    require(h['manifest_ref']==mref,'HANDOFF_MANIFEST_BINDING')
    parent=Path(mref['path']).parent
    require(Path(href['path']).parent==parent,'REVIEW_PAIR_NAMESPACE')
    members=m['members']
    require(type(members) is list and members,'MANIFEST_MEMBERS')
    refs=[href,mref]
    seen=set()
    for member in members:
        ref={k:member[k] for k in ('path','sha256','bytes')}
        require(Path(ref['path']).is_relative_to(parent) and Path(ref['path']) not in TARGETS,'MANIFEST_LOCAL_MEMBER')
        require(ref['path'].casefold() not in seen,'MANIFEST_DUPLICATE')
        seen.add(ref['path'].casefold());read_ref(ref);refs.append(ref)
    return h,refs

def validate_change_set(change):
    require(change['schema']=='researchos.w09-main-c19-seven-target-change-set.v1'
            and change['author']==AUTHOR and change['root']==str(R)
            and change['target_count']==7 and len(change['targets'])==7,'EXACT_SEVEN_CHANGE_SET')
    require(change['formal_case_accepted_delta']==0 and change['copies_producer_report_or_raw'] is False
            and change['main_adoption_executed'] is False,'CHANGE_SET_BOUNDARY')
    before=[];after=[];refs=[]
    for prefix in ('source_consumer','producer_source','producer_actual_review','component_actual_review'):
        href=change[prefix+'_handoff_ref'];mref=change[prefix+'_manifest_ref']
        handoff,pair_refs=manifest_refs(href,mref);refs+=pair_refs
        if prefix=='producer_actual_review':
            require(href['sha256']=='d6adce580965b6d8c607a5176a45043dbfb445a51d7d50d5a7f2195b89dcaa16'
                    and href['bytes']==5552 and mref['sha256']=='511830b94ffdd4059727d09bc240e02acb6976b5ee7f50ff1ac9f320cd3f4218'
                    and mref['bytes']==17590 and handoff['decision']=='ACTUAL_NATIVE_FIXTURE_QUALIFIED_CURRENT_V7_REPLAY_PASS'
                    and handoff['actual_fixture_decision']=='QUALIFIED' and handoff['formal_acceptance'] is False,'EXACT_PRODUCER_ACTUAL_REVIEW')
        if prefix=='component_actual_review':
            require(href['sha256']=='5ee925444fa3377b09cf2464dd91c786c87adcec8035b451ad0717c5f02980f8'
                    and href['bytes']==6019 and mref['sha256']=='6635364ecbc9eeff19f62667ff81c93a0a972483bfcbf01158b96f135ed55a7f'
                    and mref['bytes']==9632,'EXACT_COMPONENT_ACTUAL_PINS')
    for i,row in enumerate(change['targets']):
        require(row['target']==str(TARGETS[i]) and row['relative']==REL[i],'FIXED_TARGET_ORDER')
        source=row['after_source_ref']
        require(source['path']==str(SOURCE_PATHS[i]),'EXACT_SOURCE_PATH')
        raw=read_ref(source);after.append(raw);refs.append(source)
        require(row['after_target_ref']==raw_pin(TARGETS[i],raw),'AFTER_TARGET_PIN')
        if i<6:require((digest(raw),len(raw))==SOURCE_PINS[i],'SEALED_SIX_SOURCE_PIN')
        if i in NEW:
            require(row['before_ref'] is None and row['before_archive_ref'] is None,'THREE_ABSENT_BEFORE')
            before.append(None)
        else:
            ref=row['before_ref'];archive=row['before_archive_ref']
            require(ref['path']==str(TARGETS[i]) and archive['path']==str(N/f'before.{i}.raw'),'BEFORE_EXACT_PATH')
            original=read_ref(archive)
            require(raw_pin(TARGETS[i],original)==ref,'COMPLETE_BEFORE_ARCHIVE')
            before.append(original);refs.append(archive)
    require(len(change['source21'])==21,'SOURCE21_COUNT')
    sources={row['path']:row for row in change['source21']}
    require(set(sources)==set(SOURCE_ROSTER),'SOURCE21_EXACT_ROSTER')
    report_ref=change['source21_report_ref'];report=json.loads(read_ref(report_ref));refs.append(report_ref)
    require(set(report['version_manifest']['source_sha256'])==set(SOURCE_ROSTER),'ORIGINAL_REPORT_EXACT_SOURCE21')
    for rel,row in sources.items():
        if rel in REL[:6]:
            i=REL.index(rel)
            require(row['disposition']=='EXACT_SEALED_SOURCE_TO_ADOPT'
                    and row['desired_ref']==change['targets'][i]['after_source_ref'],'SOURCE21_SIX')
        else:
            ref=row['current_ref']
            require(row['disposition']=='CURRENT_MAIN_ALREADY_EXACT' and ref['path']==str(R/rel),'SOURCE21_OTHER15')
            read_ref(ref);refs.append(ref)
        source_ref=row.get('current_ref',row.get('desired_ref'))
        require(report['version_manifest']['source_sha256'][rel]=='sha256:'+source_ref['sha256'],'REPORT_SOURCE21_BINDING')
    return before,after,refs

def validate_scope(scope,sref,change,change_ref,self_ref,source_href,source_mref,source_refs,vector_ref):
    require(scope['schema']=='researchos.root-w09-main-c19-adoption-scope.v1'
            and scope['status']=='ROOT_AUTHORIZED_SEVEN_TARGET_SOURCE_ADOPTION_ONLY'
            and scope['issued_by']==scope['executor']==ROOT_ACTOR,'ROOT_EXPLICIT_SCOPE')
    require(scope['caller_ref']==self_ref and scope['change_set_ref']==change_ref
            and scope['source_handoff_ref']==source_href and scope['source_manifest_ref']==source_mref,'ROOT_SOURCE_BINDING')
    require(scope['exact_targets']==[str(p) for p in TARGETS]
            and scope['journal_root']==str(OUT),'ROOT_EXACT_WRITE_SCOPE')
    require(scope['formal_case_accepted_delta']==0 and all(scope[k] is False for k in
        ('formal_dispatcher','formal_acceptance','producer_rerun','copy_native_packet','new_Go_SQL_API_model_calls',
         'checkpoint_write','ownership_write','step_state_write')),'ROOT_SOURCE_ONLY_BOUNDARY')
    require(scope['consumer_closed_ref']==change['original_consumer_closed_ref'],'ORIGINAL_COMPONENT_CLOSED_BINDING')
    rh,rr=manifest_refs(scope['source_review_handoff_ref'],scope['source_review_manifest_ref'])
    decision_ref=scope['source_review_decision_ref']
    require(decision_ref in rr and rh['source_decision_ref']==decision_ref,'SOURCE_REVIEW_DECISION_MEMBER')
    d=json.loads(read_ref(decision_ref))
    require(d['schema']=='researchos.w09-main-c19-independent-source-decision.v1'
            and d['decision']=='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION'
            and d['actor_role']=='INDEPENDENT_NON_AUTHOR' and d['actor_id'] not in (AUTHOR,ROOT_ACTOR)
            and rh['actor_id']==d['actor_id'],'INDEPENDENT_SOURCE_ACCEPTANCE')
    for field,wanted in [('source_handoff_ref',source_href),('source_manifest_ref',source_mref),
                         ('caller_ref',self_ref),('change_set_ref',change_ref),
                         ('exact_targets',[str(p) for p in TARGETS])]:
        require(d[field]==wanted,'SOURCE_REVIEW_EXACT_BINDING_'+field)
    require(d['formal_case_accepted_delta']==0 and d['actual_adoption_executed'] is False,'SOURCE_REVIEW_BOUNDARY')
    # Bind the real sealed consumer review exactly; it creates no formal status.
    require(scope['component_review_handoff_ref']==change['component_actual_review_handoff_ref']
            and scope['component_review_manifest_ref']==change['component_actual_review_manifest_ref'],
            'EXACT_SEALED_COMPONENT_ACTUAL_REVIEW')
    ch,cr=manifest_refs(scope['component_review_handoff_ref'],scope['component_review_manifest_ref'])
    require(ch['schema']=='researchos.w09-c19-v7-consumer-independent-actual-handoff.v1'
            and ch['actor_id']=='codex:/root/native_temp_independent_review'
            and ch['decision']=='ACTUAL_TWO_C19_COMPONENT_CONSUMERS_VERIFIED_PASS'
            and ch['actual_component_status']=='PASS' and ch['formal_status']=='NOT_CURRENT_NOT_REGISTERED'
            and ch['consumer_closed_ref']==change['original_consumer_closed_ref']
            and ch['original_run_id']=='37dedbd890c44a93975558f2851d8675'
            and ch['consumer_python_exits']==[0,0] and ch['new_product_native_exit'] is None
            and ch['all_owned_jobs_closed'] is True and ch['all_guards_closed'] is True
            and ch['all_held_inputs_unchanged'] is True and ch['formal_case_accepted_delta']==0
            and ch['formal_acceptance'] is False and ch['CURRENT_formal_status_created'] is False,
            'COMPONENT_ACTUAL_REVIEW_REQUIRED')
    require('canonical_vector_ref' not in scope,'NO_SCOPE_CANONICAL_HASH_CYCLE')
    vector=json.loads(read_ref(vector_ref))
    require(set(vector)=={'schema','checkpoint_revision','ownership_revision','refs'}
            and vector['schema']=='researchos.w09-main-c19-adoption-canonical-vector.v1'
            and type(vector['checkpoint_revision']) is int and vector['checkpoint_revision']>366
            and type(vector['ownership_revision']) is int and vector['ownership_revision']>170,'FUTURE_ROOT_VECTOR')
    require(len(vector['refs'])==4 and [r['path'] for r in vector['refs']]==[str(p) for p in CANON],'EXACT_FOUR_CANONICAL')
    require(vector['refs'][3]==change['targets'][6]['before_ref'],'COMMANDS_BEFORE_VECTOR')
    docs=[json.loads(read_ref(r)) for r in vector['refs']]
    checkpoint,ownership=docs[:2]
    require(checkpoint['revision']==vector['checkpoint_revision'] and ownership['revision']==vector['ownership_revision'],
            'CURRENT_FUTURE_REVISIONS')
    require(checkpoint['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','PROJECT_ID')
    require(ownership['shared_integrator']=='qoder-desktop:/root/platform_owner'
            and ownership['active_integrator']['id']==ROOT_ACTOR
            and ownership['card_path_bindings']['W09-99']['owner']==ROOT_ACTOR,'CURRENT_ROOT_SHARED_INTEGRATION_ROLE')
    owner=ownership['card_path_bindings']['W09-99']['subtasks']['c19_main_source_registry_adoption']
    expected_owner=dict(owner=ROOT_ACTOR,current_source_writer=None,scope_ref=sref,exact_targets=scope['exact_targets'],
        state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',source_handoff_ref=source_href,source_manifest_ref=source_mref,
        source_review_handoff_ref=scope['source_review_handoff_ref'],source_review_manifest_ref=scope['source_review_manifest_ref'],
        component_review_handoff_ref=scope['component_review_handoff_ref'],component_review_manifest_ref=scope['component_review_manifest_ref'],
        journal_root=str(OUT),formal_case_accepted_delta=0,formal_dispatcher=False,parent_acceptance=False)
    require(owner==expected_owner,'REGISTERED_EXACT_ROOT_OWNER')
    workers=[w for w in checkpoint['workers'] if w.get('step_id')=='W09-99'
             and w.get('slice_id')=='C19_MAIN_SOURCE_REGISTRY_ADOPTION']
    expected_worker=dict(step_id='W09-99',slice_id='C19_MAIN_SOURCE_REGISTRY_ADOPTION',owner=ROOT_ACTOR,
        state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',scope_ref=sref,exact_targets=scope['exact_targets'],
        source_review_handoff_ref=scope['source_review_handoff_ref'],component_review_handoff_ref=scope['component_review_handoff_ref'])
    require(workers==[expected_worker],'REGISTERED_EXACT_ROOT_WORKER')
    require(self_ref in source_refs and change_ref in source_refs,'SOURCE_MANIFEST_CALLER_AND_CHANGE_SET')
    return [*rr,*cr,decision_ref,vector_ref,*vector['refs'][:3]],vector

class OwnedSeven:
    """Only the seven compile-time targets can be opened for mutation."""
    def __init__(self):
        require(os.name=='nt','WINDOWS_MANDATORY_OWNERSHIP')
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        def bind(name,args,result):
            f=getattr(k,name);f.argtypes=args;f.restype=result;return f
        H=ctypes.c_void_p;D=wintypes.DWORD;B=wintypes.BOOL
        self.create=bind('CreateFileW',[wintypes.LPCWSTR,D,D,H,D,D,H],H)
        self.close_handle=bind('CloseHandle',[H],B)
        self.size=bind('GetFileSizeEx',[H,ctypes.POINTER(ctypes.c_longlong)],B)
        self.seek=bind('SetFilePointerEx',[H,ctypes.c_longlong,ctypes.POINTER(ctypes.c_longlong),D],B)
        self.read=bind('ReadFile',[H,H,D,ctypes.POINTER(D),H],B)
        self.write=bind('WriteFile',[H,H,D,ctypes.POINTER(D),H],B)
        self.end=bind('SetEndOfFile',[H],B)
        self.flush=bind('FlushFileBuffers',[H],B)
        self.final=bind('GetFinalPathNameByHandleW',[H,wintypes.LPWSTR,D,D],D)
        self.dispose=bind('SetFileInformationByHandle',[H,ctypes.c_int,H,D],B)
        self.handles={};self.directories={};self.created=[];self.delete_marked=[];self.close_errors=[]
    def checked(self,ok):
        if not ok:raise ctypes.WinError(ctypes.get_last_error())
    def open_directories(self):
        # Denying FILE_SHARE_DELETE prevents parent renames/reparse swaps after
        # validation. Directory handles do not prevent ordinary child IO.
        paths={OUT}
        for p in (*TARGETS,OUT):paths.update(p.parents)
        for p in sorted(paths,key=lambda x:(len(x.parts),str(x))):
            exact_path(p)
            h=self.create(str(p),0x80,0x1|0x2,None,3,0x02000000,None)
            self.checked(h not in (None,ctypes.c_void_p(-1).value))
            self.directories[str(p)]=h
            name=ctypes.create_unicode_buffer(32768);count=self.final(h,name,len(name),0)
            self.checked(0<count<len(name))
            require(Path(name.value.removeprefix('\\\\?\\'))==p,'OWNED_DIRECTORY_FINAL_PATH')
    def open(self,i,new):
        require(type(i) is int and i in range(7) and i not in self.handles,'SEVEN_INDEX')
        require(new==(i in NEW),'CREATE_MODE')
        p=exact_path(TARGETS[i],absent=new)
        h=self.create(str(p),0x80000000|0x40000000|0x00010000,0,None,1 if new else 3,0x80,None)
        self.checked(h not in (None,ctypes.c_void_p(-1).value))
        self.handles[i]=h
        if new:self.created.append(i)
        name=ctypes.create_unicode_buffer(32768)
        count=self.final(h,name,len(name),0)
        self.checked(0<count<len(name))
        require(Path(name.value.removeprefix('\\\\?\\'))==p,'OWNED_FINAL_PATH')
    def read_raw(self,i):
        h=self.handles[i];size=ctypes.c_longlong();self.checked(self.size(h,ctypes.byref(size)))
        require(0<=size.value<=MAX,'TARGET_SIZE_CAP');self.checked(self.seek(h,0,None,0))
        remaining=size.value;chunks=[]
        while remaining:
            amount=min(remaining,1024*1024);buf=ctypes.create_string_buffer(amount);got=wintypes.DWORD()
            self.checked(self.read(h,buf,amount,ctypes.byref(got),None));require(got.value>0,'SHORT_READ')
            chunks.append(buf.raw[:got.value]);remaining-=got.value
        return b''.join(chunks)
    def write_raw(self,i,raw):
        require(type(raw) is bytes and len(raw)<=MAX and i in self.handles,'OWNED_WRITE_ONLY')
        h=self.handles[i];self.checked(self.seek(h,0,None,0));offset=0
        while offset<len(raw):
            part=raw[offset:offset+1024*1024];buf=ctypes.create_string_buffer(part);done=wintypes.DWORD()
            self.checked(self.write(h,buf,len(part),ctypes.byref(done),None));require(done.value>0,'SHORT_WRITE')
            offset+=done.value
        self.checked(self.end(h));self.checked(self.flush(h))
    def delete_created(self,i):
        require(i in NEW and i in self.created and i in self.handles,'DELETE_ONLY_OWNED_CREATED_FILE')
        flag=ctypes.c_ubyte(1)
        self.checked(self.dispose(self.handles[i],4,ctypes.byref(flag),ctypes.sizeof(flag)))
        self.delete_marked.append(i)
    def close(self):
        for i in reversed(tuple(self.handles)):
            if self.close_handle(self.handles[i]):del self.handles[i]
            else:self.close_errors.append(dict(index=i,error=ctypes.get_last_error()))
        for path in reversed(tuple(self.directories)):
            if self.close_handle(self.directories[path]):del self.directories[path]
            else:self.close_errors.append(dict(directory=path,error=ctypes.get_last_error()))
        return dict(closed=not self.handles and not self.directories,
                    retained_handles_count=len(self.handles)+len(self.directories),errors=self.close_errors,
                    created_indices=self.created,delete_marked_indices=self.delete_marked,
                    share_mode=0,exact_targets=[str(p) for p in TARGETS])

def transaction(owned,before,after,record):
    """Pure orchestration is tested with memory-only ownership adapters."""
    require(len(before)==len(after)==7,'SEVEN_TRANSACTION_INPUTS')
    written=[];opened_existing=[];rollback_errors=[];baseline_verified=False
    record('intent.json',dict(schema='researchos.w09-main-c19-owned-seven-intent.v1',
        exact_targets=[str(p) for p in TARGETS],before_base64=[None if b is None else base64.b64encode(b).decode() for b in before],
        after_base64=[base64.b64encode(b).decode() for b in after],share_mode=0,
        crash_atomic=False,ordinary_failure_rollback=True,process_loss_requires_root_reconciliation=True))
    try:
        for i in EXISTING:
            owned.open(i,False);opened_existing.append(i)
            require(owned.read_raw(i)==before[i],'BEFORE_CAS_MISMATCH')
        baseline_verified=True
        for i in NEW:
            owned.open(i,True);require(owned.read_raw(i)==b'','CREATE_NEW_NOT_EMPTY')
        require(len(owned.handles)==7,'ALL_SEVEN_EXCLUSIVELY_HELD')
        for i in range(7):
            # Record intent before a write can partially succeed.
            written.append(i);owned.write_raw(i,after[i])
        require([owned.read_raw(i) for i in range(7)]==after,'AFTER_VERIFY_FAILED')
        record('committed.json',dict(schema='researchos.w09-main-c19-owned-seven-committed.v1',
            after_refs=[raw_pin(p,b) for p,b in zip(TARGETS,after)],all_seven_verified_while_held=True,
            formal_case_accepted_delta=0,product_execution=False))
        return dict(status='SEVEN_SOURCE_TARGETS_COMMITTED',written_indices=written,rollback_attempted=False)
    except BaseException as exc:
        # No writes to an existing file occurred before all before-CAS checks.
        # A foreign before-CAS state is never overwritten during rollback.
        for i in reversed(written):
            if i in EXISTING and baseline_verified:
                try:
                    owned.write_raw(i,before[i]);require(owned.read_raw(i)==before[i],'ROLLBACK_VERIFY')
                except BaseException as back:rollback_errors.append(dict(index=i,error=repr(back)))
        for i in reversed(owned.created):
            try:owned.delete_created(i)
            except BaseException as back:rollback_errors.append(dict(index=i,error=repr(back)))
        value=dict(status='FAILED_ROLLED_BACK' if not rollback_errors else 'FAILED_ROLLBACK_REQUIRES_ROOT_RECONCILIATION',
            original_error=repr(exc),written_indices=written,rollback_errors=rollback_errors,
            new_file_deletion_pending_handle_close=list(owned.delete_marked),
            existing_before_verified=baseline_verified,formal_case_accepted_delta=0)
        try:record('failed.json',value)
        except BaseException as journal_error:value['failure_journal_error']=repr(journal_error)
        return value

def main():
    require(len(sys.argv)==4,'ROOT_REQUEST_ABSOLUTE_PATH SHA256 BYTES')
    require(sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode and sys.flags.utf8_mode,
            'LOCKED_PYTHON_I_S_B_X_UTF8_REQUIRED')
    require(Path(__file__).resolve()==N/'adopt_main_c19.source.py','FIXED_CALLER_LOCATION')
    qref=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]))
    require(Path(qref['path']).is_relative_to(W/'integration_codex'),'ROOT_REQUEST_NAMESPACE')
    request_raw=read_ref(qref);request=json.loads(request_raw)
    require(set(request)=={'schema','issued_by','scope_ref','canonical_vector_ref','caller_ref'}
            and request['schema']=='researchos.root-w09-main-c19-adoption-request.v1'
            and request['issued_by']==ROOT_ACTOR,'ROOT_EXPLICIT_POSTREGISTRATION_REQUEST')
    sref=request['scope_ref'];vector_ref=request['canonical_vector_ref']
    require(Path(sref['path']).is_relative_to(W/'integration_codex'),'ROOT_SCOPE_NAMESPACE')
    scope_raw=read_ref(sref);scope=json.loads(scope_raw)
    change_ref=scope['change_set_ref'];require(change_ref['path']==str(N/'change-set.json'),'FIXED_CHANGE_SET')
    change_raw=read_ref(change_ref);change=json.loads(change_raw)
    self_ref=pin(Path(__file__))
    require(request['caller_ref']==self_ref,'ROOT_REQUEST_CALLER')
    href=scope['source_handoff_ref'];mref=scope['source_manifest_ref']
    require(href['path']==str(N/'HDF.json') and mref['path']==str(N/'MF.json'),'FIXED_SOURCE_PACKAGE')
    source_h,source_refs=manifest_refs(href,mref)
    require(source_h['caller_ref']==self_ref and source_h['change_set_ref']==change_ref,'SOURCE_HANDOFF_BINDING')
    before,after,refs=validate_change_set(change)
    scope_refs,vector=validate_scope(scope,sref,change,change_ref,self_ref,href,mref,source_refs,vector_ref)
    python_ref=change['python_ref'];require(pin(sys.executable)==python_ref,'LOCKED_PYTHON')
    require(change['guard_ref']==GP_PIN,'EXACT_REVIEWED_SOURCE_GUARD')
    refs += source_refs+scope_refs+[qref,sref,change_ref,self_ref,GP_PIN,python_ref,change['identity_ref'],change['toolchain_ref']]
    gm=types.ModuleType('w09_main_c19_input_guard');gm.__file__=str(GP)
    exec(compile(read_ref(GP_PIN),str(GP),'exec'),gm.__dict__)
    for mod in tuple(sys.modules.values()):
        for key in ('__file__','__cached__'):
            path=getattr(mod,key,None)
            if path and Path(path).is_file():refs.append(pin(Path(path).resolve()))
    unique={}
    for ref in refs:
        require(Path(ref['path']) not in TARGETS,'NO_MUTATING_TARGET_IN_READ_GUARD')
        key=ref['path'].casefold();require(key not in unique or unique[key]==ref,'CONFLICTING_INPUT_PIN')
        unique[key]=ref
    guard=gm.SourceReadGuard(per_file_cap=MAX,total_cap=2*1024*1024*1024)
    owned=None;outcome=None;owned_cleanup=None;guard_cleanup=None;error=None;created_output=False
    try:
        guard.acquire(list(unique.values()))
        require(guard.get_buffer(qref['path'])==request_raw and guard.get_buffer(sref['path'])==scope_raw
                and guard.get_buffer(change_ref['path'])==change_raw,'HELD_REQUEST_BYTES')
        # Revalidate all authorization under held CP/OW/SS and immutable receipts.
        validate_scope(scope,sref,change,change_ref,self_ref,href,mref,source_refs,vector_ref)
        exact_path(OUT,absent=True);require(not OUT.exists(),'ONE_SHOT_JOURNAL_ALREADY_EXISTS')
        OUT.mkdir();created_output=True
        owned=OwnedSeven()
        owned.open_directories()
        outcome=transaction(owned,before,after,save)
    except BaseException as exc:error=repr(exc)
    finally:
        if owned is not None:owned_cleanup=owned.close()
        guard_cleanup=guard.close()
        if created_output:
            if owned_cleanup is not None:save('owned-handles.cleanup.actual.json',owned_cleanup)
            save('input-guard.cleanup.actual.json',guard_cleanup)
    successful=(error is None and outcome is not None and outcome['status']=='SEVEN_SOURCE_TARGETS_COMMITTED'
                and owned_cleanup['closed'] and not owned_cleanup['errors']
                and guard_cleanup['closed'] and not guard_cleanup['errors'])
    # Verify rollback/new-file deletion after all owned handles close.
    after_state=[]
    if created_output:
        for p in TARGETS:after_state.append(pin(p) if p.is_file() else None)
        expected=([raw_pin(p,b) for p,b in zip(TARGETS,after)] if successful else
                  [None if b is None else raw_pin(p,b) for p,b in zip(TARGETS,before)])
        final_matches=after_state==expected
        successful=successful and final_matches
        result=dict(status='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW' if successful else 'ADOPTION_FAILED_OR_CLEANUP_UNCONFIRMED',
            error=error,transaction=outcome,final_target_refs=after_state,
            final_matches_expected_commit_or_rollback=final_matches,
            owned_cleanup=owned_cleanup,guard_cleanup=guard_cleanup,canonical_vector_before_ref=vector_ref,
            checkpoint_ownership_step_state_written=False,producer_report_copied=False,
            formal_case_accepted_delta=0,formal_dispatcher=False,new_Go_SQL_API_model_calls=0,
            process_loss_recovery_automatic=False)
        result_ref=save('outcome.json',result)
        print(json.dumps(dict(result_ref=result_ref,status=result['status']),ensure_ascii=False),flush=True)
    elif error:print(json.dumps(dict(status='PREWRITE_REJECTED',error=error,guard_cleanup=guard_cleanup)),flush=True)
    return 0 if successful else 1

if __name__=='__main__':sys.exit(main())
