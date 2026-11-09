"""Source-only revision of AD2: four new-generation scopes, no Main adoption."""
import ast,copy,difflib,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
W=N.parent.parent
OLD=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02'
NF=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-04'
GEN='fullw09-20261010-04'
AUTHOR='codex:/root/attach_restore_independent_review'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def replace(s,a,b):
 assert a in s,('REPLACE_MISSING',a);return s.replace(a,b)
def replace_function(s,name,new):
 tree=ast.parse(s);node=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
 lines=s.splitlines(keepends=True);return ''.join(lines[:node.lineno-1])+new+''.join(lines[node.end_lineno:])
def write_source(name,original,text):
 ast.parse(text,filename=name)
 changes=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,original,text,autojunk=False).get_opcodes():
  if tag!='equal':changes.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,before=original[i:j],after=text[k:l]))
 restored=text
 for e in reversed(changes):
  assert restored[e['new_start']:e['new_end']]==e['after']
  restored=restored[:e['new_start']]+e['before']+restored[e['new_end']:]
 assert restored==original,'EXACT_COMPLETE_SOURCE_INVERSE'
 (N/name).write_bytes(text.encode('utf-8'));return dict(file=name,base_ref=ref(OLD/name),candidate_ref=ref(N/name),inverse_edits=changes)
source=doc(OLD/'input-pins.json')
pins=copy.deepcopy(source['refs'])
for key,name in {'NF_hdf':'HDF.json','NF_mf':'MF.json','NF_contract':'root-calling-contract.json','NF_choice':'source.choice.json','NF_runtime':'full_w09_runtime.source.py','NF_prepare':'prepare_full_w09.source.py','NF_run':'run_full_w09.source.py','NF_launcher':'full_w09_launcher.source.py','NF_blueprint':'compiler-source-blueprint.json'}.items():pins[key]=ref(NF/name)
for key in ('NR_hdf','NR_mf','NR_decision'):del pins[key]
source['refs']=pins
source['schema']='researchos.w09-nf4-registration-input-pins.v1'
source['new_producer_review']='REQUIRED_FROM_FUTURE_ROOT_REQUEST_AND_EXACT_REAL_PEER_AUDITS'
put(N/'input-pins.json',source)
gr=pins['guard'];raw=Path(gr['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==gr['sha256']
gm=types.ModuleType('nf4_registration_source_guard');gm.__file__=gr['path'];exec(compile(raw,gr['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(total_cap=256*1024*1024)
g.acquire([ref(OLD/name) for name in ('input-pins.json','register_w09_adoption.source.py','adoption_core.source.py','root-calling-contract.source.json','HDF.json','MF.json')]+[pins[k] for k in pins if k.startswith('NF_')])
deltas=[]
try:
 original=(OLD/'adoption_core.source.py').read_bytes().decode('utf-8');s=original
 for a,b in [
 ("AUTHOR='codex:/root/backup_regression_resources'","AUTHOR='"+AUTHOR+"'\nGENERATION='"+GEN+"'"),
 ("NKEY='full_w09_main_native_producer'","NKEY='full_w09_main_native_producer_"+GEN+"'"),
 ("NSLICE='FULL_W09_MAIN_NATIVE_PRODUCER'","NSLICE='FULL_W09_MAIN_NATIVE_PRODUCER_"+GEN+"'"),
 ("('W09-G01','W09-G02','A06')","('W09-G01','W09-G02','A06','C19')"),
 ('researchos.w09-root-adoption-independent-source-decision.v1','researchos.w09-nf4-registration-independent-source-decision.v1'),
 ('SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION','SOURCE_ACCEPTED_FOR_ROOT_NF4_REGISTRATION'),
 ("'THREE_NATIVE_LEASES'","'FOUR_NATIVE_LEASES'"),
 ("})==3,'DISTINCT_SELECTOR_LEASES'","})==4,'DISTINCT_SELECTOR_LEASES'"),
 ("'source21'):","'source21','generation'):"),
 ("'EXACT_NF3_SCOPE_FIELDS'","'EXACT_NF4_SCOPE_FIELDS'"),
 ("owner=dict(owner=ROOT,","owner=dict(generation=scope['generation'],owner=ROOT,"),
 ("worker=dict(step_id='W09-99',slice_id=NSLICE","worker=dict(generation=scope['generation'],step_id='W09-99',slice_id=NSLICE")]:
  s=replace(s,a,b)
 for name in ('cm40_document','main_pair_payloads','make_q_scope'):s=replace_function(s,name,'')
 newcanon='''def canonical_changes(cp,ow,request,scope_refs,scopes,pending,archives,own,commit_ref=None):
    """Only append NF4 generation slots; all historical scopes and counters survive."""
    require(type(cp['revision']) is int and type(ow['revision']) is int,'EXACT_CANON_REVISIONS')
    require(cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
        and ow['active_integrator']['id']==ROOT and ow['shared_integrator']=='qoder-desktop:/root/platform_owner'
        and ow['card_path_bindings']['W09-99']['owner']==ROOT,'CURRENT_ROOT_ROLE')
    require(request['kind']=='NATIVE_SCOPES' and request['generation']==GENERATION and commit_ref is not None,'NF4_ONLY_NO_MAIN_ADOPTION')
    require(type(cp['workers']) is list and set(scopes)==set(scope_refs)==set(SELECTORS),'EXACT_FOUR_SCOPES')
    merged,next_ordinal=merge_pending(cp,pending,request['before_canonical_refs'])
    co=[];oo=[];work=copy.deepcopy(cp);owners=copy.deepcopy(ow)
    def change(doc,ops,path,value):
        exists,before=value_at(doc,path);op=dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value))
        ops.append(op);put(doc,path,value)
    workers=copy.deepcopy(cp['workers']);subtasks=ow['card_path_bindings']['W09-99']['subtasks']
    require(subtasks[QKEY]['state']==QDONE,'ALREADY_ADOPTED_CURRENT_PROFILE')
    prior=cp['work_in_progress']['w09_native_producer_scopes']
    require(set(prior)=={'W09-G01','W09-G02','A06'},'PRESERVED_OLD_THREE_SCOPES')
    for selector in ('W09-G01','W09-G02','A06'):
        old_owner=subtasks['full_w09_main_native_producer_'+selector]
        old_workers=[x for x in workers if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_'+selector]
        require(len(old_workers)==1,'UNIQUE_OLD_NATIVE_WORKER')
        old_worker=old_workers[0]
        require(old_owner['scope_ref']==old_worker['scope_ref']==prior[selector]
            and old_owner['state']==old_worker['state']
            and old_owner['state'] in ('CLOSED_QUALIFIED_HISTORICAL_SOURCE_CHANGED','CLOSED_ACTUAL_NATIVE_FAILED'),'OLD_NATIVE_MUST_BE_CLOSED')
        for record in (old_owner,old_worker):
            require(record['actual_closed']['all_guards_closed'] is True
                and record['actual_closed']['all_owned_jobs_closed'] is True,'OLD_NATIVE_RESOURCES_CLOSED')
        require(all(scopes[k]['run_id']!=old_worker['run_id'] for k in SELECTORS),'NEW_RUN_IDS_ONLY')
    generations=copy.deepcopy(cp['work_in_progress'].get('w09_native_producer_scope_generations',{}))
    registrations=copy.deepcopy(cp['work_in_progress'].get('w09_nf4_scope_registrations',{}))
    require(type(generations) is dict and type(registrations) is dict
        and GENERATION not in generations and GENERATION not in registrations,'FRESH_FOUR_SELECTOR_GENERATION')
    for selector in SELECTORS:
        require(scopes[selector]['generation']==GENERATION,'EXACT_SCOPE_GENERATION')
        require(NKEY+'_'+selector not in subtasks
            and not any(x.get('slice_id')==NSLICE+'_'+selector for x in workers),'FRESH_GENERATION_OWNER_WORKER')
        owner,worker=native_owner_worker(scopes[selector],scope_refs[selector]);workers.append(worker)
        change(owners,oo,['card_path_bindings','W09-99','subtasks',NKEY+'_'+selector],owner)
    generations[GENERATION]=copy.deepcopy(scope_refs)
    registrations[GENERATION]=dict(scope_refs=copy.deepcopy(scope_refs),before_canonical_archive_refs=archives,
        pending_ref=request['pending_ref'],profile_adoption_ref=commit_ref,
        source_handoff_ref=own['hdf'],source_review_decision_ref=own['decision'],
        formal_case_accepted_delta=0,parent_acceptance=False)
    if merged!=cp['failure_counters']:change(work,co,['failure_counters'],merged)
    change(work,co,['work_in_progress','root_next_failure_ordinal_live'],next_ordinal)
    change(work,co,['work_in_progress','w09_native_producer_scope_generations'],generations)
    change(work,co,['work_in_progress','w09_nf4_scope_registrations'],registrations)
    change(work,co,['workers'],workers)
    for key,value in dict(revision=cp['revision']+1,expected_previous_revision=cp['revision'],updated_at=request['created_utc'],
        updated_by=ROOT,note='Root bounded NF4 four-selector generation registration; no formal acceptance.').items():change(work,co,[key],value)
    for key,value in dict(revision=ow['revision']+1,updated_at=request['created_utc'],updated_by=ROOT).items():change(owners,oo,[key],value)
    require(inverse_operations(work,co)==cp and inverse_operations(owners,oo)==ow,'COMPLETE_STRUCTURAL_INVERSE')
    require(work['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters'],'ALL_OLD_FAILURES_UNCHANGED')
    require(work['work_in_progress']['w09_native_producer_scopes']==prior,'OLD_SCOPE_REFS_UNCHANGED')
    return work,owners,co,oo
'''
 s=replace_function(s,'canonical_changes',newcanon)
 deltas.append(write_source('adoption_core.source.py',original,s))
 original=(OLD/'register_w09_adoption.source.py').read_bytes().decode('utf-8');s=original
 for a,b in [
 ('Future Root-only W09 profile adoption and NF3 Scope registration.','Future Root-only NF4 generation Scope registration.'),
 ('activate/apply-profile modes','activate mode'),
 ("AUTHOR='codex:/root/backup_regression_resources'","AUTHOR='"+AUTHOR+"'"),
 ("OUTPUT_BASE=W/'w09_profile_nf3_root_adoption_root'","OUTPUT_BASE=W/'w09_nf4_root_registration_root'"),
 ("INPUT_PINS_SHA='7543d7ba46be8b07c996122f5e48e449a453680f337f99609a3c2efd76b8bfd8'","INPUT_PINS_SHA='"+ref(N/'input-pins.json')['sha256']+"'"),
 ("'source_author_audit_ref','source_review_audit_ref','lease'","'source_author_audit_ref','source_review_audit_ref','generation','producer_review_handoff_ref','producer_review_manifest_ref','producer_review_decision_ref','lease'"),
 ('researchos.w09-root-adoption-source-handoff.v1','researchos.w09-nf4-registration-source-handoff.v1'),
 ("'main_pair_ref':'main_pair_bytes.source.py','contract_ref'","'contract_ref'"),
 ('SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE','SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE'),
 ('researchos.root-w09-profile-nf3-registration-request.v1','researchos.root-w09-nf4-registration-request.v1'),
 ("request['kind'] in ('PROFILE_ADOPTION','NATIVE_SCOPES')","request['kind']=='NATIVE_SCOPES' and request['generation']==core.GENERATION"),
 ("source,pinref=inputs();pins=source['refs'];core,native=fixed_modules(pins)\r\n    request=doc(request_ref)","source,pinref=inputs();pins=copy.deepcopy(source['refs']);request=doc(request_ref)\n    for k,qk in {'NR_hdf':'producer_review_handoff_ref','NR_mf':'producer_review_manifest_ref','NR_decision':'producer_review_decision_ref'}.items():pins[k]=ref_shape(request[qk])\n    core,native=fixed_modules(pins)"),
 ("and request['reviewed_source_audit_refs']==source['peer_audit_refs']","and set(request['reviewed_source_audit_refs'])==set(source['peer_audit_refs'])\n            and all(request['reviewed_source_audit_refs'][k]==source['peer_audit_refs'][k] for k in ('profile-author','profile-review'))"),
 ("reviewed_dependencies(pins,source['peer_audit_refs'],native,core)","reviewed_dependencies(pins,request['reviewed_source_audit_refs'],native,core)"),
 ("Path(ref['path']).is_relative_to(OUTPUT_BASE) and Path(ref['path']).name=='apply-profile.completed.json'","Path(ref['path']).is_relative_to(W/'w09_profile_nf3_root_adoption_root') and Path(ref['path']).name=='apply-profile.completed.json'"),
 ('researchos.root-w09-adoption-registration-plan.v1','researchos.root-w09-nf4-registration-plan.v1'),
 ('researchos.root-w09-adoption-registration-completed.v1','researchos.root-w09-nf4-registration-completed.v1'),
 ('researchos.w09-three-selector-native-canonical-vector.v1','researchos.w09-four-selector-native-canonical-vector.v1'),
 ('researchos.root-w09-three-selector-native-request.v1','researchos.root-w09-four-selector-native-request.v1'),
 ('NF3','NF4'),('nf3_runtime','nf4_runtime')]:
  s=replace(s,a,b)
 # Remove Main mutation paths entirely. Keep read-only exact CM40 verification.
 for name in ('profile_outputs','apply_profile'):s=replace_function(s,name,'')
 oldbranch="""    if request['kind']=='PROFILE_ADOPTION':
        require(request['native_leases']=={} and request['profile_commit_ref'] is None
                and request['profile_commit_audit_ref'] is None,'PROFILE_STAGE_ONLY')
        require(request['main_profile_ref']['sha256']==pins['Q_profile_before']['sha256']
                and request['main_profile_ref']['bytes']==pins['Q_profile_before']['bytes'],'REVIEWED_MAIN_PROFILE_BEFORE')
    else:
        require(set(request['native_leases'])==set(core.SELECTORS),'EXACT_SELECTOR_LEASES')
        for lease in request['native_leases'].values():
            core.validate_lease(lease,now(),core.utc(request['created_utc']))
            require(core.utc(lease['lease_expires_at'])<=core.utc(request['lease']['lease_expires_at']),'NATIVE_LEASE_WITHIN_ROOT_LEASE')
        ref_shape(request['profile_commit_ref']);ref_shape(request['profile_commit_audit_ref'])
"""
 newbranch="""    require(set(request['native_leases'])==set(core.SELECTORS),'EXACT_SELECTOR_LEASES')
    for lease in request['native_leases'].values():
        core.validate_lease(lease,now(),core.utc(request['created_utc']))
        require(core.utc(lease['lease_expires_at'])<=core.utc(request['lease']['lease_expires_at']),'NATIVE_LEASE_WITHIN_ROOT_LEASE')
    ref_shape(request['profile_commit_ref']);ref_shape(request['profile_commit_audit_ref'])
"""
 # Existing retained segments are CRLF. New replaced fragments may be LF; preserve both through exact inverse.
 s=replace(s,oldbranch.replace('\n','\r\n'),newbranch)
 start=s.index("    if request['kind']=='PROFILE_ADOPTION':",s.index('def model('))
 end=s.index("    scope_refs=",start)
 s=s[:start]+"""    validate_profile_commit(ctx,cp,ow)
    choice=doc(pins['NF_choice']);contract=doc(pins['NF_contract'])
    require(choice['common']['generation']==request['generation']==core.GENERATION,'EXACT_NF4_GENERATION')
    scopes=core.make_native_scopes(request,pins,choice,contract)
    for scope in scopes.values():
        for path in (scope['receipt_root'],scope['scratch_root'],scope['output_root']):
            path_checked(path,True);require(not Path(path).exists(),'NATIVE_ONE_SHOT_PATH_ALREADY_EXISTS')
        for source_ref in scope['source21']:read_ref(source_ref);ctx['refs'].append(source_ref)
    target_before=[];target_after=[];after_refs=[];main_proposals=[]
"""+s[end:]
 oldcli="""    elif mode=='apply-profile':
        require(len(args)==4,'PROFILE_STAGE_ARGUMENTS');result=apply_profile(ref)
"""
 s=replace(s,oldcli.replace('\n','\r\n'),'')
 deltas.append(write_source('register_w09_adoption.source.py',original,s))
 caller=ast.parse(s);request_fields=ast.literal_eval(next(x.value for x in caller.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUEST_FIELDS' for t in x.targets)))
 contract=dict(schema='researchos.w09-nf4-registration-calling-contract.v1',status='SOURCE_ONLY_NO_EXECUTION_GRANT',
 source_author=AUTHOR,source_thread_id='01a11e0c-eef6-7363-a5b1-da61d6ae7f4c',root_actor='codex:/root',
 source_bindings={k:ref(N/name) for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py'}.items()},
 input_pins_ref=ref(N/'input-pins.json'),shared_canonical_transaction_ref=pins['TP'],
 existing_native_contract_ref=pins['NF_contract'],generation=GEN,selectors=['W09-G01','W09-G02','A06','C19'],
 request_schema='researchos.root-w09-nf4-registration-request.v1',request_required_fields=sorted(request_fields),
 request_kind='NATIVE_SCOPES',new_producer_review_fields=['producer_review_handoff_ref','producer_review_manifest_ref','producer_review_decision_ref'],
 review_schema='researchos.w09-nf4-registration-independent-source-decision.v1',review_decision='SOURCE_ACCEPTED_FOR_ROOT_NF4_REGISTRATION',
 review_binding_fields=['source_handoff_ref','source_manifest_ref','caller_ref','core_ref','contract_ref'],
 peer_audits='profile-author/profile-review remain exact historical accepted peers; producer-author/producer-review bind new NF4 Source and independent decision from future Root request.',
 CLI=dict(prefix=[pins['locked']['path']],modes=['propose','check','activate','finalize-native-requests'],
 entrypoint=str(N/'register_w09_adoption.source.py'),exact_ref_argv=['<path>','<sha256>','<bytes>'],
 note='Use locked Python -I -S -B -X utf8; propose/finalize each also require an exact completed actual Root audit ref.'),
 permitted_Canon_writes=['checkpoint.json','path_ownership.json'],permitted_Main_writes=[],
 source_parent_creation=False,native_scratch_parent='C:\\Users\\yqyyds\\AppData\\Local\\ResearchOS\\w09-native-v4',
 scratch_parent_gate='Root must separately create and observe missing fixed parents before proposing; existing no-alias/no-reparse checks remain mandatory.',
 old_three_scope_refs_owners_workers_preserved=True,old_three_must_be_closed=True,
 current4='Root supplies live exact ordered CP/OW/SS/CM refs; no fixed current revision supplied by Source.',
 pending_original_diagnostics='Root complete contiguous suffix, original exits null when unobserved; counter prefix remains exact.',
 exact_inverse=True,Main_profile_and_CM40='Already adopted bytes are verified read-only through real historical completion/audit.',
 actual_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,future_Root_request=None)
 # Locked manifest reference is not an executable: expose real pinned NF4 Python instead.
 contract['CLI']['prefix']=[doc(NF/'source.choice.json')['common']['tool_refs']['python']['path'],'-I','-S','-B','-X','utf8',str(N/'register_w09_adoption.source.py')]
 put(N/'root-calling-contract.source.json',contract)
 put(N/'source-delta.json',dict(schema='researchos.w09-nf4-registration-source-delta.v1',base_hdf_ref=ref(OLD/'HDF.json'),
  base_mf_ref=ref(OLD/'MF.json'),source_deltas=deltas,exact_source_inverse=True,
  source_guard_input_refs=[ref(OLD/n) for n in ('register_w09_adoption.source.py','adoption_core.source.py','input-pins.json')],
  actual_TP_calls=0,actual_Main_writes=0,actual_Canon_writes=0))
finally:
 closed=g.close();put(N/'source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(status='NF4_REGISTRATION_SOURCE_BUILT',caller_ref=ref(N/'register_w09_adoption.source.py'),
 core_ref=ref(N/'adoption_core.source.py'),contract_ref=ref(N/'root-calling-contract.source.json')),ensure_ascii=False))

