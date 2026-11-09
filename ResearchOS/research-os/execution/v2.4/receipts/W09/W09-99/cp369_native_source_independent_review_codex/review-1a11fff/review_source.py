from pathlib import Path
import ast,base64,copy,hashlib,json,re,sys,types
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
N=W/'checkpoint_r369_native_source_root/cp369-c19-20261009';O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[];controls=[];refs={};raws={}
def ck(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def pinraw(p,b):return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def pin(p):
    p=Path(p);return pinraw(p,p.read_bytes())
def read(r):
    if not(type(r)==dict and set(r)=={'path','sha256','bytes'} and type(r['path'])==str and type(r['sha256'])==str and re.fullmatch('[0-9a-f]{64}',r['sha256']) and type(r['bytes'])==int):raise ValueError('EXACT_TYPED_REF')
    p=Path(r['path']);b=p.read_bytes();ck('exact_pin:'+str(p),pinraw(p,b)==r)
    k=str(p).casefold();ck('unique_pin:'+str(p),k not in refs or refs[k]==r);refs[k]=r;raws[k]=b;return b
def obj(r):return json.loads(read(r))
def save(name,value):
    p=O/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def module(r,name):
    m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m;exec(compile(read(r),r['path'],'exec'),m.__dict__);return m
def pair(href,mref):
    h=obj(href);m=obj(mref);ck('pair_binding:'+href['path'],h['manifest_ref']==mref)
    members=m['members'];members=list(members.values()) if type(members)==dict else members
    for r in members:read(r)
    return h,m
def caught(f):
    try:f()
    except BaseException as e:return dict(type=type(e).__name__,error=str(e))
    return None
hr=dict(path=str(N/'HDF.json'),sha256='702278d4a2866ecccd8d82e5d746c23b536b932790df01a921389eb459e78edd',bytes=2123)
h=obj(hr);mr=h['manifest_ref'];mf=obj(mr)
ck('exact_manifest',mr['sha256']=='a5657a53494e643ef85a7729a253b7b9bc548f8c69546e3db98cbe4b02dd2ac5' and mr['bytes']==2462)
for r in mf['members']:read(r)
facts=obj(h['facts_ref']);scope=obj(h['scope_ref']);contract=obj(facts['calling_contract_ref']);proof=obj(h['proof_ref'])
membermap={Path(r['path']).name:r for r in mf['members']}
live=obj(membermap['live-context.source-check.root.json']);author_guard=obj(membermap['source_guard.cleanup.check.json'])
ck('author_guard_closed',author_guard['closed'] is True and not author_guard['errors'] and author_guard['retained_handles_count']==0 and author_guard['verification']=='PASSED')
for e in author_guard['entries']:
    ck('author_entry_closed:'+e['path'],e['closed'] is True and e['verified'] is True and e['final_path_match'] is True)
    read({k:e[k] for k in ['path','sha256','bytes']})
for p in facts['pairs']:pair(p['handoff_ref'],p['manifest_ref'])
for r in facts['input_refs']:read(r)
origin_checks=[]
for row in facts['diagnostics']:
    raw=read(row['origin_ref']);ordinal=row['ordinal']
    if Path(row['origin_ref']['path']).suffix=='.json':
        d=json.loads(raw)
        if ordinal in [955,956]:
            e=d['diagnostic_classification'];observed=(e['outer_exit_code'],e['python_exit_code'],e['native_exit_code']);ck('model_NULL:'+str(ordinal),e['model_exit_code'] is None)
            ck('outer_result_fidelity:'+str(ordinal),d['original_result']['exit_code']==observed[0])
            if ordinal==955:ck('rg2_outer0_preserved',e['first_rg_child_exit_code']==2 and observed[0]==0)
            if ordinal==956:ck('956_truncated_original_not_reconstructed',e['original_tool_output_truncated'] is True and e['child_exit_codes_not_captured'] is True)
        elif ordinal==957:observed=(d['actual_outer_exit'],d['actual_python_exit'],d['actual_native_exit']);ck('model_NULL:957',d['actual_model_exit'] is None)
        else:
            observed=(d['outer_exit'],d['SourcePython_exit'],d['Native_exit']);ck('model_NULL:'+str(ordinal),d['Model_exit'] is None and d['Go_exit'] is None)
            if ordinal==965:ck('Root965_not_requested964',d['root_assigned_ordinal']==965 and d['root_requested_ordinal']==964)
    else:
        text=raw.decode();fields={line.partition(':')[0]:line.partition(':')[2].strip() for line in text.splitlines() if ':' in line};observed=tuple(None if fields[name]=='NULL' else int(fields[name]) for name in ['outer_exit_code','python_exit_code','native_exit_code'])
        ck('text_model_NULL:'+str(ordinal),'model_exit_code: NULL' in text)
        if ordinal==958:ck('958_no_dispatch',observed==(None,None,None) and 'subcommand_dispatch: none' in text)
    wanted=(row['actual_outer_exit'],row['actual_python_exit'],row['actual_native_exit']);ck('origin_exit_fidelity:'+str(ordinal),wanted==observed and all(v is None or type(v)==int for v in wanted));origin_checks.append(dict(ordinal=ordinal,origin_ref=row['origin_ref'],verified_observed_exits=observed))
ck('exact13_once_cutoff',list(r['ordinal'] for r in facts['diagnostics'])==list(range(953,966)) and len({(r['origin_ref']['sha256'],r['ordinal']) for r in facts['diagnostics']})==13 and h['source_cutoff']==live['source_cutoff']=={'highest_ordinal':965,'next_failure_ordinal':966} and live['next_original_failure_ordinal']==966 and live['pending']==[])
oldraw=[read(r) for r in facts['canonical_refs']];oldc,oldo=json.loads(oldraw[0]),json.loads(oldraw[1])
writer=module(h['writer_ref'],'independent_cp369_writer');read(writer.BASE_REF)
gp=dict(path=str(writer.base.GP),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
tp=dict(path=str(writer.base.TP),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=6877)
transaction_raw=read(tp);transaction_tree=ast.parse(transaction_raw)
ck('scope_owner_worker_exact_shapes',len(scope)==45 and len(facts['owner'])==17 and len(facts['worker'])==9 and set(scope)==set(contract['scope_required_fields']) and set(facts['owner'])==set(contract['owner_fields']) and set(facts['worker'])==set(contract['worker_fields']))
sc,owner,worker=writer.scope_bindings(facts)
ck('writer_derives_exact_owner_worker',sc==scope and owner==facts['owner'] and worker==facts['worker'])
proposed=writer.transform(copy.deepcopy(oldc),copy.deepcopy(oldo),facts,h['facts_ref'],oldc,oldo,live);pc,po=proposed
ck('proposed_exact_author_proof',[pinraw(Path(r['path']),writer.encoded(x)) for r,x in zip(facts['canonical_refs'],proposed)]==proof['proposed_refs'])
ck('increment_only_CP_OW',pc['revision']==369 and pc['expected_previous_revision']==368 and po['revision']==173)
ck('old950_unchanged_plus13',len(oldc['failure_counters'])==950 and pc['failure_counters'][:950]==oldc['failure_counters'] and len(pc['failure_counters'])==963)
ck('new_origins_exact_once',[r['original_payload']['observed_ordinal'] for r in pc['failure_counters'][950:]]==list(range(953,966)) and len({r['origin_key'] for r in pc['failure_counters'][950:]})==13)
for row,added in zip(facts['diagnostics'],pc['failure_counters'][950:]):
    ck('appended_fidelity:'+str(row['ordinal']),added['evidence_ref']==row['origin_ref'] and added['original_payload']['immutable_origin_ref']==row['origin_ref'] and all(added['original_payload'][k]==row[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit','origin_selector','exit_qualification']) and added['counted_once'] is True and added['counter_reset'] is False and added['automatic_retry'] is False)
ck('two_parents_and_active_Root_preserved',pc['work_in_progress']['construction_active_parents']==oldc['work_in_progress']['construction_active_parents']==['W05','W09'] and po['active_integrator']==oldo['active_integrator'] and po['active_integrator']['id']=='codex:/root' and po['shared_integrator']==oldo['shared_integrator'])
ck('both_parent_owners_preserved',all(po['card_path_bindings'][x]['owner']==oldo['card_path_bindings'][x]['owner'] for x in ['W05-99','W09-99']))
ck('W05_OW_subtree_unchanged',po['card_path_bindings']['W05-99']==oldo['card_path_bindings']['W05-99'])
ck('single_exact_native_owner_worker',po['card_path_bindings']['W09-99']['subtasks'][writer.KEY]==facts['owner'] and [x for x in pc['workers'] if x.get('slice_id')==writer.SLICE]==[facts['worker']])
ic,io=copy.deepcopy(pc),copy.deepcopy(po)
for k in ['failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note']:ic[k]=copy.deepcopy(oldc[k])
del io['card_path_bindings']['W09-99']['subtasks'][writer.KEY]
for k in ['revision','updated_at','updated_by']:io[k]=oldo[k]
ck('complete_inverse',ic==oldc and io==oldo)
# Independently constrain all modified leaves, rather than trusting whole-subtree reversal alone.
def diff(a,b,path=''):
    if type(a)!=type(b):return [path]
    if type(a)==dict:
        out=[]
        for k in set(a)|set(b):out+=([path+'/'+k] if k not in a or k not in b else diff(a[k],b[k],path+'/'+k))
        return out
    if type(a)==list:return [] if a==b else [path]
    return [] if a==b else [path]
cpdiff=diff(oldc,pc);owdiff=diff(oldo,po)
allowedc={'/failure_counters','/workers','/expected_previous_revision','/revision','/updated_at','/updated_by','/note','/work_in_progress/mu_sdk_r369','/work_in_progress/root_next_failure_ordinal_live','/work_in_progress/later_diagnostics_observed_after_cutoff'}
allowedo={'/revision','/updated_at','/updated_by','/card_path_bindings/W09-99/subtasks/'+writer.KEY}
ck('exact_diff_whitelist',set(cpdiff)<=allowedc and set(owdiff)<=allowedo,dict(CP=cpdiff,OW=owdiff))
dev=obj(facts['W05_actual_closed_ref']);dh,dm=pair(facts['W05_actual_review_handoff_ref'],facts['W05_actual_review_manifest_ref']);dd=obj(dh['actual_decision_ref'])
ck('W05_only_dev13_partial',dev['status']=='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN' and dev['pass_count']==13 and dev['native_qualification_accepted'] is False and dd['decision']=='ACTUAL_DEVELOPMENT_13_EVIDENCE_VERIFIED' and dd['qualification']=='COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN' and dd['native_qualification_accepted'] is False and pc['work_in_progress']['mu_sdk_r369']['W05_qualification']==dev['status'])
ck('no_new_acceptance_flags',pc['work_in_progress']['mu_sdk_r369']['formal_case_accepted_delta']==0 and pc['work_in_progress']['mu_sdk_r369']['parent_acceptance'] is False and facts['formal_acceptance'] is False and h['actual_executed'] is False)
inverse_ref=save('complete-canonical-byte-inverse.source.json',dict(meaning='In-memory Source proposal; these bytes were not written to Canon',files=[dict(original_ref=r,proposed_ref=pinraw(Path(r['path']),writer.encoded(x)),whole_before_base64=base64.b64encode(b).decode(),whole_after_base64=base64.b64encode(writer.encoded(x)).decode()) for r,b,x in zip(facts['canonical_refs'],oldraw,proposed)],complete_semantic_inverse=True))
# Pure Source negative controls; rejected controls are not new tool failures.
for label,mutate in [('live_bool',lambda x:x.update(next_original_failure_ordinal=True)),('live_null',lambda x:x.update(next_original_failure_ordinal=None)),('live_reset',lambda x:x.update(next_original_failure_ordinal=965)),('missing_pending',lambda x:x.pop('pending')),('pending_null',lambda x:x.update(pending=None)),('omitted_966',lambda x:x.update(next_original_failure_ordinal=967)),('cutoff_changed',lambda x:x['source_cutoff'].update(highest_ordinal=964))]:
    bad=copy.deepcopy(live);mutate(bad);e=caught(lambda:writer.validate_live(bad));ck('reject_'+label,e is not None);controls.append(dict(case=label,rejection=e))
for label,mutate in [('outer_bool',lambda f:f['diagnostics'][0].update(actual_outer_exit=True)),('ordinal_bool',lambda f:f['diagnostics'][0].update(ordinal=True)),('origin_missing',lambda f:f['diagnostics'][0].pop('origin_ref')),('diagnostic_duplicate',lambda f:f['diagnostics'].append(copy.deepcopy(f['diagnostics'][0])))]:
    f=copy.deepcopy(facts);mutate(f);e=caught(lambda:writer.transform(copy.deepcopy(oldc),copy.deepcopy(oldo),f,h['facts_ref'],oldc,oldo,live));ck('reject_'+label,e is not None);controls.append(dict(case=label,rejection=e))
for label,mutate in [('third_parent',lambda c,o:c['work_in_progress'].update(construction_active_parents=['W05','W09','W10'])),('active_root_changed',lambda c,o:o['active_integrator'].update(id='other')),('duplicate_worker',lambda c,o:c['workers'].append(copy.deepcopy(worker))),('duplicate_owner',lambda c,o:o['card_path_bindings']['W09-99']['subtasks'].update({writer.KEY:copy.deepcopy(owner)})),('old_counter_reset',lambda c,o:c.update(failure_counters=[])),('stale_revision',lambda c,o:c.update(revision=367))]:
    c,o=copy.deepcopy(oldc),copy.deepcopy(oldo);mutate(c,o);e=caught(lambda:writer.transform(copy.deepcopy(c),copy.deepcopy(o),facts,h['facts_ref'],c,o,live));ck('reject_'+label,e is not None);controls.append(dict(case=label,rejection=e))
tx=next(n for n in transaction_tree.body if isinstance(n,ast.FunctionDef) and n.name=='update_pair');prefix=[]
for n in tx.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='k' for t in n.targets):break
    prefix.append(n)
prefix.append(ast.Return(ast.Constant('VALIDATED_BEFORE_WINAPI')))
fun=ast.FunctionDef(name='validate_tx_prefix',args=copy.deepcopy(tx.args),body=prefix,decorator_list=[]);ast.fix_missing_locations(fun)
ns=dict(os=types.SimpleNamespace(name='nt'),Path=Path,PATHS=tuple(writer.CANON[:2]));exec(compile(ast.Module(body=[fun],type_ignores=[]),'<transaction-prefix-no-WinAPI>','exec'),ns)
for operation in ['activate','close']:ck('transaction_legal_'+operation,ns['validate_tx_prefix'](facts['canonical_refs'][:2],None,O,operation)=='VALIDATED_BEFORE_WINAPI')
for operation in ['check','reset','retry','Activate',None,True]:
    e=caught(lambda:ns['validate_tx_prefix'](facts['canonical_refs'][:2],None,O,operation));ck('transaction_reject_'+repr(operation),e is not None)
wrong=list(reversed(facts['canonical_refs'][:2]));ck('transaction_reject_reordered_pair',caught(lambda:ns['validate_tx_prefix'](wrong,None,O,'activate')) is not None)
txt=transaction_raw.decode();ck('transaction_CAS_and_durable_before_after',all(s in txt for s in ['create(str(path),0x80000000|0x40000000,0,None,3,0x80,None)','[pin_raw(p,b) for p,b in zip(PATHS,before)]!=expected_refs','before_refs=[exclusive','after_refs=[exclusive','"automatic_inverse":False','for handle in reversed(handles)','if [raw_read(h) for h in handles]!=after']))
cas=next(n for n in ast.walk(tx) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and 'expected_refs' in ast.unparse(n.test) and 'pin_raw' in ast.unparse(n.test))
cascode=compile(ast.Module(body=[cas],type_ignores=[]),'<exact-under-lock-CAS>','exec');cn=dict(PATHS=tuple(writer.CANON[:2]),before=oldraw[:2],pin_raw=pinraw,expected_refs=facts['canonical_refs'][:2])
ck('transaction_CAS_exact_pass',caught(lambda:exec(cascode,cn)) is None)
cn=dict(cn,before=[oldraw[0]+b' ',oldraw[1]]);ck('transaction_CAS_byte_drift_rejected',caught(lambda:exec(cascode,cn)) is not None)
# Run the actual accepted Native v2 authority function only against hypothetical in-memory Canon.
nativeh,nativem=pair(scope['source_handoff_ref'],scope['source_manifest_ref']);runtime=module(nativeh['runtime_ref'],'independent_native_authority_only');choice=obj(nativeh['choice_ref'])
proposed_raw={str(p):writer.encoded(v) for p,v in zip(writer.CANON,proposed)}
vdoc=dict(schema='researchos.w09-main-c19-native-canonical-vector.v1',checkpoint_revision=369,ownership_revision=173,refs=[pinraw(p,proposed_raw[str(p)]) if str(p) in proposed_raw else r for p,r in zip(writer.CANON,facts['canonical_refs'])])
vpath=O/'hypothetical-vector-not-written.json';vbytes=writer.encoded(vdoc);vref=pinraw(vpath,vbytes)
qdoc=dict(schema='researchos.root-w09-main-c19-native-request.v1',issued_by='codex:/root',scope_ref=facts['scope_ref'],canonical_vector_ref=vref,calling_contract_ref=facts['calling_contract_ref'])
qpath=O/'hypothetical-request-not-written.json';qbytes=writer.encoded(qdoc);qref=pinraw(qpath,qbytes)
memory={str(p):(pinraw(p,b),b) for p,b in [(Path(k),v) for k,v in proposed_raw.items()]+[(vpath,vbytes),(qpath,qbytes)]}
original_read=runtime.read_ref
def memory_read(r):
    if r['path'] in memory:
        wanted,b=memory[r['path']];runtime.require(r==wanted,'MEMORY_EXACT_REF');return b
    b=original_read(r);read(r);return b
runtime.read_ref=memory_read
qualification=runtime.validate_authority(qref,choice)
ck('accepted_Native_v2_authority_exact_proposed_Canon',qualification[1]==scope and qualification[2]==vdoc)
for label,mutate in [('request_extra',lambda q:q.update(unreviewed=True)),('request_wrong_issuer',lambda q:q.update(issued_by=ACTOR)),('request_scope_missing',lambda q:q.pop('scope_ref'))]:
    bad=copy.deepcopy(qdoc);mutate(bad);b=writer.encoded(bad);r=pinraw(qpath,b);old=memory[str(qpath)];memory[str(qpath)]=(r,b);e=caught(lambda:runtime.validate_authority(r,choice));memory[str(qpath)]=old;ck('Native_reject_'+label,e is not None);controls.append(dict(case=label,rejection=e))
# Substitute semantic negative control documents only inside the test memory.
def reject_document(label,ref,doc,mutate):
    bad=copy.deepcopy(doc);mutate(bad);key=ref['path'];prior=memory.get(key);memory[key]=(ref,writer.encoded(bad));e=caught(lambda:runtime.validate_authority(qref,choice))
    if prior is None:del memory[key]
    else:memory[key]=prior
    ck('Native_reject_'+label,e is not None);controls.append(dict(case=label,rejection=e))
for label,mutate in [('scope_bool_count',lambda s:s.update(maximum_go_test_runs=True)),('scope_null_count',lambda s:s.update(maximum_go_list_runs=None)),('scope_formal_grant',lambda s:s.update(formal_acceptance=True)),('scope_Source21_drift',lambda s:s['source21'][0].update(bytes=0)),('scope_missing_field',lambda s:s.pop('automatic_retry'))]:reject_document(label,facts['scope_ref'],scope,mutate)
reject_document('owner_shape_drift',vdoc['refs'][1],po,lambda o:o['card_path_bindings']['W09-99']['subtasks'][writer.KEY].update(extra=True))
reject_document('worker_duplicate',vdoc['refs'][0],pc,lambda c:c['workers'].append(copy.deepcopy(worker)))
sd=obj(scope['source_review_decision_ref']);reject_document('source_self_authorized',scope['source_review_decision_ref'],sd,lambda d:d.update(actor_id='codex:/root'))
ad=obj(scope['adoption_review_decision_ref']);reject_document('adoption_handles_unknown',scope['adoption_review_decision_ref'],ad,lambda d:d.update(all_handles_closed=None))
ck('no_actual_entrypoint_or_transaction',not any((O/p).exists() for p in ['hypothetical-vector-not-written.json','hypothetical-request-not-written.json']))
canonical_paths={str(p).casefold() for p in writer.CANON}
held={k:r for k,r in refs.items() if k not in canonical_paths and not (Path(r['path']).is_relative_to(R) and not Path(r['path']).is_relative_to(R/'execution/v2.4/receipts') and not Path(r['path']).is_relative_to(R/'.local'))}
gm=module(gp,'cp369_review_actual_guard');guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(held.values()));ck('finite_review_inputs_held_unchanged',all(guard.get_buffer(r['path'])==raws[k] for k,r in held.items()))
    ck('four_Canon_byte_unchanged',all(p.read_bytes()==b for p,b in zip(writer.CANON,oldraw)))
finally:
    cleanup=guard.close();cleanup_ref=save('review-source-guard.cleanup.actual.json',cleanup)
ck('all_review_guards_closed',cleanup['closed'] is True and cleanup['verification']=='PASSED' and not cleanup['errors'] and cleanup['retained_handles_count']==0)
failed=[x for x in checks if not x['passed']];decision='SOURCE_ACCEPTED_FOR_ROOT_CP369_MAIN_C19_REGISTRATION' if not failed else 'REQUEST_CHANGES'
findings_ref=save('findings.json',dict(findings=failed,blocking_findings=len(failed)))
checks_ref=save('checks.json',dict(count=len(checks),passed=sum(x['passed'] for x in checks),checks=checks))
save('negative-controls.json',dict(controls=controls,synthetic_control_authority=False,actual_Native_executed=False));save('verified-input-pins.json',list(refs.values()));save('original-exit-fidelity.json',origin_checks)
decision_ref=save('source-decision.json',dict(schema='researchos.root-cp369-native-independent-source-decision.v1',decision=decision,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_handoff_ref=hr,source_manifest_ref=mr,writer_ref=h['writer_ref'],facts_ref=h['facts_ref'],scope_ref=h['scope_ref'],calling_contract_ref=facts['calling_contract_ref'],native_source_handoff_ref=scope['source_handoff_ref'],native_source_manifest_ref=scope['source_manifest_ref'],scope_field_count=45,owner_field_count=17,worker_field_count=9,current_before_canonical_refs=facts['canonical_refs'],proposed_refs=proof['proposed_refs'],complete_inverse_ref=inverse_ref,Native_v2_validate_authority_in_memory_passed=True,source_cutoff=h['source_cutoff'],Root_live_next_reported=970,fresh_postseal_context_required=True,postcut_ordinals_reported=[966,967,968,969],actual_executed=False,Canon_written=False,Main_Source_written=False,Native_executed=False,execution_grant=False,formal_case_accepted_delta=0,parent_acceptance=False,W05_qualification='COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',W05_native_qualification_accepted=False,all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanup_ref,checks_ref=checks_ref,findings_ref=findings_ref,new_original_failures=[969],original_failure_969_ref=pin(O/'failure-e84755.original-tool-io.json'),reviewed_at=datetime.now(timezone.utc).isoformat()))
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write('CP369/OW173 Root登记 Source独审：'+decision+'。13原始953..965逐项核对原始退出类别与NULL，旧950条原样保留；完整CP/OW inverse及逐变更路径白名单通过，保留Root与W05/W09两个父任务、W05 dev13 partial NativeOPEN。45 Scope/17 Owner/9 Worker与已接受Native v2的真实validate_authority在内存拟议Canon上通过。交易仅activate/close合法，比较精确原字节的CAS、先保存before/after intent、异常保留partial与逆序关闭句柄已审；未调用WinAPI事务或prepare/run。布尔、NULL、回退计数、遗漏pending、重复owner/worker、Source21、独审与adoption边界负向控制通过。Source截止965/next966；Root后报live970，966/967/968/969必须由未来freshpostseal context带入，不改Source包。所有审查guard实关0，无Canon/Main/Native写执行，无Formal/Parent增量。\n')
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mref=save('MF.json',dict(schema='researchos.root-cp369-independent-source-manifest.v1',members=members,source_handoff_ref=hr,source_manifest_ref=mr))
href=save('HDF.json',dict(schema='researchos.root-cp369-independent-source-handoff.v1',status=decision,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',manifest_ref=mref,source_decision_ref=decision_ref,source_handoff_ref=hr,source_manifest_ref=mr,checks=len(checks),blocking_findings=len(failed),held_inputs=len(held),all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanup_ref,source_cutoff=h['source_cutoff'],actual_executed=False,Canon_written=False,Native_executed=False,execution_grant=False,formal_case_accepted_delta=0,parent_acceptance=False,new_original_failures=[969],original_failure_969_ref=pin(O/'failure-e84755.original-tool-io.json'),STOP=True,FINAL=True))
for r in members+[mref,href]:
    b=Path(r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
print(json.dumps(dict(HDF=href,MF=mref,decision=decision_ref,status=decision,checks=len(checks),blocking_findings=len(failed),held_inputs=len(held)),ensure_ascii=False),flush=True)
