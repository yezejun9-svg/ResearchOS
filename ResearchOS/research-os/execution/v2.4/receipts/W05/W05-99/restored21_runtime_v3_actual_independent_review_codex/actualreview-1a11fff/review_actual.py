from pathlib import Path
import ast,hashlib,json,re,sys,types
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
N=B/'restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01'
A=B/'checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009'
O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[];refs={};documents={};before_bytes={}
def ck(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(r,record=True):
    p=Path(r['path']);raw=p.read_bytes();clean=dict(path=str(p),sha256=r['sha256'],bytes=r.get('bytes',len(raw)))
    ck('pin:'+str(p),(hashlib.sha256(raw).hexdigest(),len(raw))==(clean['sha256'],clean['bytes']))
    if record:
        key=str(p).casefold();ck('consistent_pin:'+str(p),key not in refs or refs[key]==clean);refs[key]=clean;before_bytes[key]=raw
    return raw
def obj(r):
    raw=read(r);d=json.loads(raw);documents[str(Path(r['path'])).casefold()]=d;return d
def fresh(p):return obj(pin(p))
def save(name,d):
    p=O/name
    with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def clean_ref(r):return {k:r[k] for k in ('path','sha256','bytes')}
def collect(d):
    if type(d)==dict:
        if {'path','sha256','bytes'}<=set(d) and type(d['path'])==str and Path(d['path']).is_absolute():read(clean_ref(d))
        else:
            for v in d.values():collect(v)
    elif type(d)==list:
        for v in d:collect(v)
def samepath(a,b):return Path(a)==Path(b)
def same_ref(a,b):return samepath(a['path'],b['path']) and (a['sha256'],a['bytes'])==(b['sha256'],b['bytes'])
hr=dict(path=str(N/'HDF.json'),sha256='72df2851c4c8fe5f8db37c283dad9cfcaba0921554606f4b3d0b51f0c6e856fd',bytes=4821)
h=obj(hr);mr=h['manifest_ref'];mf=obj(mr);collect(mf['members']);C=obj(h['contract_ref']);T=Path(C['worktree']);ISO=Path(C['isolation_output']);V=Path(C['validation_output'])
sr=dict(path=str(A/'scope-registration.root.json'),sha256='21a9433147678dd0daa3b86a9de1c50358795ae66242ca6b736732eea3db629b',bytes=4047)
scope=obj(sr);vr=dict(path=str(A/'W05-current-canonical-vector.actual.root.json'),sha256='3d2742035391d7027f70efb3b93a6b14313d479acc3452088da6c1e5e9cf4fcd',bytes=1363);vector=obj(vr)
ready_ref=dict(path=str(ISO/'isolation.ready.json'),sha256='8f1b77cb09f8e6f38f9f9f7d3d48728731685cdeaff52caf341f33d785878038',bytes=5014)
closed_ref=dict(path=str(V/'validation.closed.json'),sha256='3b5109fc204e73f0dd455e85ec8a369c40c8777d1368ef3ae0aed67bbffe0ab8',bytes=12474)
ready=obj(ready_ref);closed=obj(closed_ref);prepclose=obj(ready['cleanup_closed_ref']);prepattempts=obj(prepclose['attempts_ref']);valattempts=obj(closed['cleanup_attempts_ref'])
reviewh=obj(scope['source_review_handoff_ref']);reviewm=obj(scope['source_review_manifest_ref']);collect(reviewm['members'])
ck('exact_Source_manifest',mr['sha256']=='5aadb19d3312853749e3bcdb5cd45d199010b15d306952f9f73610bd8a4d0b62' and mr['bytes']==5073)
ck('prior_independent_Source_acceptance',reviewh['status']=='SOURCE_ACCEPTED_FOR_ROOT_DEVELOPMENT_TESTS_ONLY' and reviewh['manifest_ref']==scope['source_review_manifest_ref'])
ck('Root_scope_source_contract_bindings',scope['source_handoff_ref']==hr and scope['source_manifest_ref']==mr and scope['contract_ref']==h['contract_ref'])
ck('Root_scope_authorized_once',scope['issued_by']==scope['executor']=='codex:/root' and scope['status']=='ROOT_AUTHORIZED_SINGLE_BOUNDED_RESTORED21_DEVELOPMENT_RUN' and scope['maximum_actual_attempts']==1 and scope['maximum_unique_tests']==13)
ck('Root_scope_no_grant_expansion',all(scope[k] is False for k in ['formal_dispatcher','formal_acceptance','Main_adoption','production_DB_writes','external_model_calls','automatic_retry','parent_acceptance']) and scope['formal_case_accepted_delta']==0)
ck('Root_scope_exact_output_paths',all(scope[k]==C[k] for k in ['worktree','environment','isolation_output','validation_output']))
collect(scope);collect(vector)
canonical=[obj(r) for r in vector['refs']];cp,ow,ss,commands=canonical
ck('ordered_canonical_vector',list(Path(r['path']).name for r in vector['refs'])==C['four_exact_current_canonical_refs'] and vector['scope_ref']==sr)
ck('current_revision_and_HEAD',cp['revision']==vector['checkpoint_revision']==368 and ow['revision']==vector['ownership_revision']==172 and cp['head']==vector['expected_head'])
owner=ow['card_path_bindings']['W05-99'];dev=owner['subtasks']['restored21_v3_root_development']
ck('historical_W05_owner_preserved',owner['owner']==scope['historical_W05_parent_owner']=='codex:/root/w1102_impl')
ck('current_Root_development_owner',dev['owner']=='codex:/root' and dev['current_source_writer'] is None and dev['scope_ref']==sr and dev['state']=='ROOT_REGISTERED_PENDING_RESTORED21_V3_DEVELOPMENT')
ck('owner_exact_refs_paths',all(dev[k]==scope[k] for k in ['source_handoff_ref','source_manifest_ref','source_review_handoff_ref','source_review_manifest_ref','worktree','environment','isolation_output','validation_output']))
workers=[w for w in cp['workers'] if w.get('slice_id')=='RESTORED21_V3_BOUNDED_DEVELOPMENT']
ck('one_exact_Root_worker',len(workers)==1 and workers[0]['owner']=='codex:/root' and workers[0]['scope_ref']==sr and workers[0]['source_handoff_ref']==hr and workers[0]['source_review_handoff_ref']==scope['source_review_handoff_ref'] and workers[0]['worktree']==C['worktree'])
two=fresh(A/'W05-two-stage-argv.actual.root.json');stage2=fresh(A/'W05-stage2-argv.actual.root.json')
pr=fresh(A/'isolation.actual.original-tool-io.root.json');va=fresh(A/'validation.actual.original-tool-io.root.json')
io_refs=[pin(A/'isolation.actual.original-tool-io.root.json'),pin(A/'validation.actual.original-tool-io.root.json')]
expectedargs=[vector['expected_head'],vector['refs'][0]['sha256'],str(vector['refs'][0]['bytes']),str(vector['checkpoint_revision']),vector['refs'][1]['sha256'],str(vector['refs'][1]['bytes']),vector['refs'][2]['sha256'],str(vector['refs'][2]['bytes']),vector['refs'][3]['sha256'],str(vector['refs'][3]['bytes'])]
ck('exact_same_stage_arguments',two['prepare_argv'][7:]==expectedargs and stage2['argv'][7:]==expectedargs+[ready_ref['sha256'],str(ready_ref['bytes'])] and two['validate_argv_prefix']==stage2['argv'][:-2])
for label,d,want in [('prepare',pr,two['prepare_argv']),('validate',va,stage2['argv'])]:
    first=d['original_args']['cmd'].splitlines()[0];observed=re.findall("'([^']*)'",first)
    ck(label+'_original_shell_argv',observed==want and samepath(d['original_args']['workdir'],R))
    ck(label+'_outer_SourcePython_exit0',d['completion_poll']['exit_code']==0 and 'SOURCE_PYTHON_EXIT=0' in d['completion_poll']['output'] and 'ROOT_SOURCE_PYTHON_EXIT=0' in d['completion_poll']['output'])
    chunks=[d['original_result']]
    if 'poll1' in d:chunks.append(d['poll1']['value'])
    chunks.append(d['completion_poll']);progress=[];final=[]
    for chunk in chunks:
        for line in chunk['output'].splitlines():
            if not line.startswith('{'):continue
            row=json.loads(line)
            if 'progress' in row:
                progress.append(row['receipt_ref']);read(row['receipt_ref'],record=False)
            else:final.append(row)
    wantrefs=ready['invocation_refs'] if label=='prepare' else closed['invocation_refs']
    ck(label+'_all_original_progress_refs',len(progress)==len(wantrefs) and all(same_ref(a,b) for a,b in zip(progress,wantrefs)))
    key='ready_ref' if label=='prepare' else 'closed_ref';wanted=ready_ref if label=='prepare' else closed_ref
    ck(label+'_original_final_exact_ref',len(final)==1 and same_ref(final[0][key],wanted))
    ck(label+'_same_before_after_Canon',ready['canonical_refs']==closed['canonical_refs']==prepclose['canonical_refs']==vector['refs'])
    collect(fresh((ISO if label=='prepare' else V)/'canonical.pre-run.exact.json'))
ck('actual_status_partial_ceiling',closed['status']==scope['qualification_ceiling']=='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN')
guard_refs=prepclose['guard_refs']+closed['guard_cleanup_refs'];guard_docs=[]
for gr in guard_refs:
    d=obj(gr);guard_docs.append(d)
    ck('actual_guard_closed:'+gr['path'],d['closed'] is True and d['verification']=='PASSED' and d['failure'] is None and d['retained_handles_count']==0 and not d['errors'])
    ck('all_guard_entries_closed:'+gr['path'],all(e['verified'] is True and e['final_path_match'] is True and e['closed'] is True for e in d['entries']))
    collect(d['entries'])
ck('two_prepare_five_validate_guards',len(prepclose['guard_refs'])==2 and len(closed['guard_cleanup_refs'])==5)
ck('cleanup_attempts_complete',prepattempts['guard_refs']==prepclose['guard_refs'] and valattempts['guard_refs']==closed['guard_cleanup_refs'] and prepattempts['jobs']==prepclose['jobs'] and valattempts['jobs']==closed['jobs'] and not prepattempts['errors'] and not valattempts['errors'] and prepattempts['all_guards_closed'] is True and valattempts['all_guards_closed'] is True)
bylabel={};actualjobs=[]
bits=['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']
for kind,rows in [('prepare',prepclose['jobs']),('validate',closed['jobs'])]:
    for j in rows:
        inv=obj(j['invocation_ref']);collect([inv['stdout_ref'],inv['stderr_ref']]);x=inv['result'];cl=x['job_cleanup'];bylabel[j['label']]=inv
        ck('owned_job_closed:'+j['label'],j['closed'] is True and inv['exception'] is None and inv['actual_native_exit']==x['actual_exit']==0 and x['timed_out'] is False and x['error'] is None and x['resumed'] is True and cl['active_processes_last_observed']==0 and not cl['errors'] and all(cl[k] is True for k in bits))
        ck('primary_exact_integers:'+j['label'],type(x['owned_child_pid']) is int and x['owned_child_pid']>0 and type(x['creation_time_100ns']) is int and x['creation_time_100ns']>2**53)
        if kind=='validate':ck('primary_decimal_exact:'+j['label'],inv['typed_primary_identity']==dict(pid_decimal=str(x['owned_child_pid']),creation_filetime_100ns_decimal=str(x['creation_time_100ns'])))
        actualjobs.append(dict(stage=kind,label=j['label'],invocation_ref=j['invocation_ref'],primary_pid_decimal=str(x['owned_child_pid']),primary_FILETIME_decimal=str(x['creation_time_100ns']),actual_outer_exit=x['actual_exit'],job_closed=True,individual_descendant_exit=None))
ck('six_prepare_four_validate_jobs',len(prepclose['jobs'])==6 and len(closed['jobs'])==4 and ready['all_owned_jobs_closed'] and closed['all_owned_jobs_closed'])
ck('HEAD_before_after_raw',read(bylabel['head-before']['stdout_ref']).decode().strip()==read(bylabel['head-after']['stdout_ref']).decode().strip()==vector['expected_head'])
ck('staged_index_empty_observed',not read(bylabel['staged-status']['stdout_ref']).strip() and ready['staged_index_empty'] is True)
ck('dirty_state_recorded',read(bylabel['tracked-status']['stdout_ref']).decode().splitlines()==ready['tracked_dirty_paths'] and bool(ready['tracked_dirty_paths']))
ck('git_mutations_only_fixed_detached_candidate',bylabel['create-worktree']['argv'][-4:]==['--no-checkout','--detach',str(T),vector['expected_head']] and bylabel['checkout-product-source']['argv'][1:3]==['-C',str(T)] and bylabel['checkout-product-source']['argv'][-3:]==['read-tree','-mu','HEAD'])
sparse=obj(ready['sparse_checkout_ref']);collect(sparse)
ck('sparse_no_shared_git_config',sparse['excluded_history_receipts'] is True and sparse['shared_git_config_mutated'] is False and not (T/'execution/v2.4/receipts').exists())
overlay=obj(closed['source_overlay_ref']);formatted=obj(closed['formatted_source_ref']);inventory=obj(closed['compiler_inventory_ref']);typed=obj(closed['typed_fixture_evidence_inventory_ref'])
roster=obj(C['exact_source_roster']);base=obj(C['h20_source_overlay']);five=obj(C['a21_v2_overlay']);composed=dict(base['sources']);composed.update(five['files'])
ck('source63_exact_61_plus5_with2_additions',len(base['sources'])==61 and len(five['files'])==5 and len(set(five['files'])-set(base['sources']))==2 and len(composed)==63 and composed==overlay['sources']==roster['sources'])
ck('overlay_five_exact_paths',set(five['files'])==set(C['overlay_exact_paths']))
collect(composed);collect(formatted);collect(inventory)
ck('formatted_exact63_targets',len(formatted)==63 and {str(Path(r['path']).relative_to(T)).replace('\\','/') for r in formatted}==set(composed))
fmt=bylabel['format'];wantfmt=[str(Path(C['go']['path']).with_name('gofmt.exe')),'-w',*[str(T/p) for p in composed if p.endswith('.go')]]
ck('actual_formatter_exact_source_set',fmt['argv']==wantfmt and samepath(fmt['cwd'],T))
candidate_guard=next(d for r,d in zip(guard_refs,guard_docs) if Path(r['path']).name=='candidate-source-guard.cleanup.actual.json');candidate_entries={e['path']:clean_ref(e) for e in candidate_guard['entries']}
ck('formatted_output_held_through_compile',all(candidate_entries.get(r['path'])==r for r in formatted) and candidate_entries.get(closed['formatted_source_ref']['path'])==closed['formatted_source_ref'])
compiler_guard=next(d for r,d in zip(guard_refs,guard_docs) if Path(r['path']).name=='compiler-source-guard.cleanup.actual.json');held={e['path']:clean_ref(e) for e in compiler_guard['entries']}
compile_refs=[*inventory['build_inputs'],*inventory['product_inventory'],*inventory['export_refs'],*inventory['module_go_mod_refs'],*inventory['compiler_tool_refs'],inventory['GoRef'],closed['compiler_inventory_ref']]
ck('complete_compiler_inventory_held',all(held.get(r['path'])==r for r in compile_refs) and len(held)==len({r['path'] for r in compile_refs}))
ck('compiler_counts',inventory['package_count']==len(inventory['packages'])==352 and len(inventory['build_inputs'])==3735 and len(inventory['export_refs'])==351 and len(inventory['module_go_mod_refs'])==19)
cache=Path(C['environment'])/'validation/gocache';ck('actual_exports_fresh_private_cache',Path(inventory['fresh_private_GOCACHE'])==cache and all(Path(r['path']).is_relative_to(cache) for r in inventory['export_refs']))
go_list=bylabel['tagged-compiler-input-list'];raw=read(go_list['stdout_ref']).decode();decoder=json.JSONDecoder();pos=0;packages=[];buildpaths=set();exportpaths=set();modpaths=set();embeds=[]
fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
while pos<len(raw):
    while pos<len(raw) and raw[pos].isspace():pos+=1
    if pos==len(raw):break
    pkg,pos=decoder.raw_decode(raw,pos);packages.append(pkg['ImportPath']);ck('Go_list_no_package_errors:'+pkg['ImportPath'],not pkg.get('Error') and not pkg.get('DepsErrors'))
    if pkg.get('Export'):exportpaths.add(str(Path(pkg['Export']).resolve()))
    mod=pkg.get('Module')
    while type(mod)==dict:
        if mod.get('GoMod'):modpaths.add(str(Path(mod['GoMod']).resolve()))
        mod=mod.get('Replace')
    if not pkg.get('Dir'):continue
    for field in fields:
        for name in pkg.get(field,[]):
            p=Path(name);p=p if p.is_absolute() else Path(pkg['Dir'])/p;p=p.resolve();buildpaths.add(str(p))
            if field.endswith('EmbedFiles'):embeds.append((pkg['ImportPath'],field,str(p)))
ck('raw_go_list_rederived_exact_inventory',packages==inventory['packages'] and buildpaths=={r['path'] for r in inventory['build_inputs']} and exportpaths=={r['path'] for r in inventory['export_refs']} and modpaths=={r['path'] for r in inventory['module_go_mod_refs']})
ck('raw_embed_records_exact',embeds==[(e['package'],e['field'],e['ref']['path']) for e in inventory['actual_embed_files']])
ck('Go_list_exact_tagged_argv',go_list['argv']==[str(Path(C['go']['path'])),'list','-export','-test','-deps','-compiled','-tags=researchos_native_recovery_harness','-json','./internal/domain'])
binary=closed['compiled_test_ref'];comp=bylabel['tagged-test-binary-compile'];test=bylabel['restored21-v2-nine-parent-jsonl'];bg=next(d for r,d in zip(guard_refs,guard_docs) if Path(r['path']).name=='binary-source-guard.cleanup.actual.json')
ck('fresh_actual_binary_compile_argv',comp['argv']==[str(Path(C['go']['path'])),'test','-c','-tags=researchos_native_recovery_harness','-trimpath','-buildvcs=false','-o',binary['path'],'./internal/domain'] and samepath(comp['cwd'],T))
ck('compiled_binary_and_official_test2json_held',{e['path']:clean_ref(e) for e in bg['entries']}=={r['path']:r for r in [binary,inventory['test2json_executable_ref']]})
ck('official_test2json_approved_pin',inventory['test2json_executable_ref']['sha256']==C['test2json']['sha256'] and samepath(inventory['test2json_executable_ref']['path'],C['test2json']['path']))
parents=closed['exact_parent_names'];terminal=set(parents)|{'TestRestored21RejectsForeignPartialSessionAndMissingFence/'+s for s in ['foreign','partial-session','session-addon','missing-restore-trigger']}
selector='^('+'|'.join(sorted(parents))+')$';ck('official_test2json_exact_test_argv',test['argv']==[str(Path(C['test2json']['path'])),'-p','researchos.local/research-os/internal/domain','-t',binary['path'],'-test.v=test2json','-test.run='+selector,'-test.count=1','-test.timeout=14m'] and samepath(test['cwd'],T/'internal/domain'))
events=[json.loads(line) for line in read(test['stdout_ref']).decode().splitlines()];started=[];ends={};duplicate=False;unknown=False
for event in events:
    if event.get('Package')!='researchos.local/research-os/internal/domain':unknown=True
    name=event.get('Test')
    if not name:continue
    if name not in terminal:unknown=True
    if event['Action']=='run':
        if name in started:duplicate=True
        started.append(name)
    elif event['Action'] in ['pass','fail','skip']:
        if name not in started or name in ends:duplicate=True
        ends[name]=event['Action']
ck('raw_actual13_unique_pass',len(parents)==len(set(parents))==9 and len(terminal)==13 and set(started)==set(ends)==terminal and len(started)==13 and not duplicate and not unknown and set(ends.values())=={'pass'} and events[-1]['Action']=='pass' and 'Test' not in events[-1])
ck('raw_counts_equal_closed',ends==closed['actions'] and sorted(started)==closed['started_names']==closed['expected_terminal_names'] and closed['pass_count']==13 and closed['fail_count']==closed['skip_count']==0 and not read(test['stderr_ref']))
for label in ['format','tagged-compiler-input-list','tagged-test-binary-compile','restored21-v2-nine-parent-jsonl']:
    e=bylabel[label]['public_environment'];ck('isolated_no_fetch_environment:'+label,e==test['public_environment'] and e['GOPROXY']==e['GOSUMDB']==e['GOWORK']=='off' and Path(e['GOCACHE'])==cache and Path(e['TEMP']).is_relative_to(Path(C['environment'])))
ck('typed_evidence_absent_NULL_OPEN',typed['directory_observed'] is False and typed['files']==[] and typed['selected_roster_has_typed_fixture_parent'] is False and typed['individual_descendant_PID_FILETIME_raw_streams_exit'] is None and typed['native_qualification_accepted'] is False and not Path(typed['environment_directory']).exists())
ck('no_individual_descendant_exit_inference',closed['descendant_test_binary_exit'] is None and closed['individual_descendant_PID_FILETIME_and_raw_streams'] is None)
ck('qualification_all_open',all(closed[k]=='OPEN' for k in ['genuine21_22_release_program_provenance','public_late_failure_no_publication','overall20to24']) and all(closed[k] is False for k in ['formal_acceptance','Main_adopted','original_trial_DB_touched','native_qualification_accepted','component_validation_accepted']))
ck('no_model_or_trial_claim_expansion',closed['external_model_requests']==0 and closed['original_trial_provider_requests'] is None)
# Main/Cannon observations are re-read, not locked by this reviewer, so Root remains free to coordinate.
canonical_paths={str(Path(r['path'])).casefold() for r in vector['refs']}
unlocked={k:r for k,r in refs.items() if Path(r['path']).is_relative_to(R) and not Path(r['path']).is_relative_to(R/'.local') and not Path(r['path']).is_relative_to(R/'execution/v2.4/receipts')}
held_refs={k:r for k,r in refs.items() if k not in unlocked}
gm=types.ModuleType('independent_actual_read_guard');gp=C['source_guard'];gm.__file__=gp['path'];exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
print(json.dumps(dict(progress='independent_finite_guard',inputs=len(held_refs),total_bytes=sum(r['bytes'] for r in held_refs.values()),source_only_review=True)),flush=True)
try:
    guard.acquire(list(held_refs.values()))
    ck('review_actually_held_unchanged',all(guard.get_buffer(r['path'])==before_bytes[k] for k,r in held_refs.items()))
    ck('Main_and_Canon_current_match_actual_guards',all(Path(r['path']).read_bytes()==before_bytes[k] for k,r in unlocked.items()))
    ck('actual_Main_and_Canon_closure_claims',closed['Main_8_guarded_files_unchanged'] is True and closed['canonical_unchanged'] is True and ready['Main_canonical_unchanged'] is True)
finally:
    cleanup=guard.close();cleanup_ref=save('review-source-guard.cleanup.actual.json',cleanup)
ck('review_guard_closed',cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0 and cleanup['verification']=='PASSED')
failed=[c for c in checks if not c['passed']]
verdict='ACTUAL_DEVELOPMENT_13_EVIDENCE_VERIFIED' if not failed else 'REQUEST_CHANGES'
findings_ref=save('findings.json',dict(findings=failed,blocking_findings=len(failed),actual_save_failures_observed=False,save_failure_path_evidence='Prior independent Source v3 AST controls only; not claimed as actual fault execution'))
checks_ref=save('checks.json',dict(count=len(checks),passed=sum(c['passed'] for c in checks),checks=checks))
save('verified-input-pins.json',list(refs.values()));save('actual-primary-jobs.json',actualjobs)
save('independent-test-events.json',dict(raw_stdout_ref=test['stdout_ref'],raw_stderr_ref=test['stderr_ref'],event_count=len(events),parents=parents,run_names=started,terminal_actions=ends,pass_count=sum(x=='pass' for x in ends.values()),fail_count=sum(x=='fail' for x in ends.values()),skip_count=sum(x=='skip' for x in ends.values()),individual_descendant_identity_raw_exit=None))
qualification='COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN'
decision=dict(schema='researchos.restored21-v3-independent-actual-development-decision.v1',decision=verdict,evidence_verdict=verdict,qualification=qualification,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',actual_executor='codex:/root',source_handoff_ref=hr,source_manifest_ref=mr,source_review_handoff_ref=scope['source_review_handoff_ref'],source_review_manifest_ref=scope['source_review_manifest_ref'],calling_contract_ref=h['contract_ref'],Root_scope_ref=sr,canonical_vector_ref=vr,actual_isolation_ready_ref=ready_ref,actual_validation_closed_ref=closed_ref,actual_original_tool_io_refs=io_refs,exact_source_roster_ref=C['exact_source_roster'],source_count=63,overlay_count=5,actual_unique_test_count=13,pass_count=13,fail_count=0,skip_count=0,actual_development_test_evidence_verified=not failed,actual_rerun_by_reviewer=False,review_only=True,actual_jobs_observed=10,actual_source_guards_observed=7,all_review_handles_closed=cleanup['closed'],review_guard_cleanup_ref=cleanup_ref,retained_handles_count=cleanup['retained_handles_count'],findings_ref=findings_ref,checks_ref=checks_ref,typed_descendant_PID_FILETIME_raw_streams_exit=None,native_qualification_accepted=False,genuine21_22_release_program_provenance='OPEN',public_late_failure_no_publication='OPEN',overall20to24='OPEN',component_validation_accepted=False,Main_adopted=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,Main_Canon_old_Source_written=False,original_failure_965_ref=pin(O/'failure-read-summary.original-tool-io.json'),limitations=['Only actual development-test evidence verified; no full Native qualification.','Staged empty and tracked dirty before execution, HEAD before/after, finite Main/Cannon input guard receipts and scoped candidate write commands were checked. No full dirty-tree byte snapshot or post-stage2 Git status was invented.','Save-failure behavior is inherited from the pinned independent Source v3 AST review; successful actual receipts show no actual save failure.'],reviewed_at=datetime.now(timezone.utc).isoformat())
decision_ref=save('actual-decision.json',decision)
report='W05 restored21 v3 独立实际复核：'+verdict+'；资格 COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN。两个 Root stages 使用同一 CP368/OW172/SS/commands，scope/owner/worker 与原始 argv 一致，W05 原父 owner 保留。实际 6+4 owned jobs、2+5 source guards 关闭；Source63 与 overlay5、格式化候选、352 包编译输入/351 Export/19 Module.GoMod 和测试 binary 的持锁链一致；从原始 JSONL 重算 9 parents+4 drift leaves，共13唯一pass/0fail/0skip。FILETIME 由 Python 整数与十进制字符串核对，无 JS 数字往返。typed descendants identity/raw/exit 仍 NULL/OPEN，真实21/22 release programmes、public late failure、20→24、Native/Parent/Formal均未接受。审查未重跑 Actual/Go/Git/SQL/model，未写 Main/Canon/旧Source。源码保存失败控制仅沿用已封存的 Source AST 审查，未宣称实际注入故障。原只读摘要失败965保留完整IO。\n'
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
manifest_ref=save('MF.json',dict(schema='researchos.restored21-v3-independent-actual-review-manifest.v1',members=members,source_handoff_ref=hr,actual_validation_closed_ref=closed_ref))
handoff_ref=save('HDF.json',dict(schema='researchos.restored21-v3-independent-actual-review-handoff.v1',status=verdict,qualification=qualification,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',manifest_ref=manifest_ref,actual_decision_ref=decision_ref,source_handoff_ref=hr,source_manifest_ref=mr,actual_isolation_ready_ref=ready_ref,actual_validation_closed_ref=closed_ref,checks=len(checks),blocking_findings=len(failed),held_inputs=len(held_refs),all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanup_ref,actual_unique_development_tests=13,native_qualification_accepted=False,component_validation_accepted=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,actual_rerun_by_reviewer=False,Main_Canon_old_Source_written=False,execution_grant=False,new_original_failures=[965],original_failure_965_ref=pin(O/'failure-read-summary.original-tool-io.json'),STOP=True,FINAL=True))
for r in members+[manifest_ref,handoff_ref]:
    b=Path(r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
print(json.dumps(dict(HDF=handoff_ref,MF=manifest_ref,decision=decision_ref,verdict=verdict,qualification=qualification,checks=len(checks),blocking_findings=len(failed),held_inputs=len(held_refs)),ensure_ascii=False),flush=True)
