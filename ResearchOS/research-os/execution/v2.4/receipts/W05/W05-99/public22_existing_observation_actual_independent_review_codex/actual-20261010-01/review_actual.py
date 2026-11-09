"""Independently review public22 actual evidence; never run product functions."""
import ast
import copy
from datetime import datetime
import hashlib
import json
import ntpath
import os
from pathlib import Path
import stat
import types

D=Path(__file__).resolve().parent
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/public22.readonly.actual.complete-hostpair-seal.root.json')
ACTOR='codex:/root/full_w09_source_review'
def doc(p):return json.loads(Path(p).read_bytes())
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def same_bytes(left,right):return left['sha256']==right['sha256'] and left['bytes']==right['bytes']
def module(ref,name):
    assert same_bytes(pin(ref['path']),ref)
    m=types.ModuleType(name);m.__file__=ref['path'];exec(compile(Path(ref['path']).read_bytes(),ref['path'],'exec'),m.__dict__)
    return m
def main():
    b=doc(P);assert pin(P)['sha256']=='e5d4e7628a0fbeb3e2a9640ff7e11f37a0c7eaf2aad9915269964d749a1dcc89'
    q=doc(b['source_caller_request_ref']['path']);a=doc(b['actual_request_ref']['path'])
    facts=doc(a['facts_ref']['path']);scope=doc(a['scope_ref']['path']);owner=doc(facts['owner_ref']['path']);worker=doc(facts['worker_ref']['path'])
    activation=doc(a['registration_result_ref']['path']);after=doc(b['activation_observation_ref']['path'])
    source=doc(q['source_hdf_ref']['path']);m=module(source['caller_ref'],'public22_actual_readonly_review_NO_PRODUCT_CALL')
    assert ACTOR not in (m.ROOT,m.AUTHOR,m.LEAF_AUTHOR)
    # These functions only validate existing bytes and pure metadata; no Root
    # request/live/registration/readonly_run/runtime_refs function is invoked.
    chain=m.source_chain(q);original=m.original_evidence(m.inputs())
    resources=doc(source['runtime_resources_ref']['path']);previous_guard=doc(b['source_guard_closed_ref']['path'])
    journal=Path(activation['transaction']['transaction_journal'])
    inventory=doc(D/'actual-dictionary-inspection.json')['journal_actual_inventory']
    assert inventory==sorted(p.name for p in journal.iterdir())
    refs=[pin(P),*[b[k] for k in ('source_caller_request_ref','actual_request_ref','activation_observation_ref','caller_return_ref','observation_ref','source_guard_closed_ref')],
        a['facts_ref'],a['scope_ref'],facts['owner_ref'],facts['worker_ref'],a['registration_result_ref'],source['caller_ref'],source['runtime_resources_ref'],
        *facts['before_archive_refs'],*after['archive_refs'],*[pin(journal/name) for name in inventory],*chain['refs'],*original['refs'],*resources['resource_refs']]
    for record in b['records'].values():refs.extend([record['raw_ref'],record['binding_ref']])
    for key in ('postreview_live_audit_ref',):refs.extend(m.audit(q[key],m.ROOT,q['before_canonical_refs']+[q['review_decision_ref'],q['case_request_ref']])['refs'])
    refs.extend(m.audit(a['activation_audit_ref'],m.ROOT,[a['registration_result_ref'],*a['current_canonical_refs'],a['scope_ref']])['refs'])
    live={m.canonical(str(p)) for p in m.CANON}
    refs=[r for r in refs if m.canonical(r['path']) not in live]
    assert all('private' not in [x.lower() for x in Path(r['path']).parts] for r in refs)
    refs=m.refs_unique(refs)
    guard=m.load(m.GUARD_REF,'public22_actual_review_SourceGuard_ONLY').SourceReadGuard(per_file_cap=m.MAX,total_cap=2*1024*1024*1024)
    checks=[]
    def check(ok,name,detail=None):
        if not ok:raise AssertionError(name)
        checks.append(dict(name=name,passed=True,detail=detail))
    try:
        guard.acquire(refs)
        check(all(same_bytes(pin(r['path']),r) for r in refs),'all selected actual refs pinned while held',len(refs))
        check(m.source_chain(q)['refs']==chain['refs'],'Root real nonauthor Source review and actual peer audit chain')
        replay=m.original_evidence(m.inputs())
        check(replay['state']==original['state'],'original1025 evidence unchanged; no original invocation replay')
        check(set(original['case'])=={'case_id','output_root','end_version'} and original['case']['end_version']==22,'original exact three-field request')
        check(len(q['evidence'])==9 and q['evidence']==scope['evidence']==original['evidence'],'original exact nine evidence')
        check(scope==m.scope_projection(q,b['source_caller_request_ref'],chain,original),'actual exact registered Scope projection')
        check(scope['lease_id']==owner['lease_id']==worker['lease_id']==q['lease_id'],'same actual Root lease')
        check(owner['owner']==worker['worker_id']==m.ROOT and worker['selected_owner_ref']==facts['owner_ref']
            and owner['selected_worker_id']==m.ROOT and worker['scope_ref']==owner['scope_ref']==a['scope_ref'],'actual Scope owner worker acyclic refs')
        check(len(resources['resource_refs'])==149,'149 declared loaded runtime refs')
        actual_held={m.canonical(r['path']):r for r in previous_guard['entries']}
        check(previous_guard['closed'] is True and previous_guard['retained_handles_count']==0 and not previous_guard['errors']
            and previous_guard['verification']=='PASSED' and all(r['closed'] and r['verified'] and r['final_path_match'] for r in previous_guard['entries']),
            'actual 933 Source guards passed and closed0',len(previous_guard['entries']))
        check(all(m.canonical(r['path']) in actual_held and same_bytes(r,actual_held[m.canonical(r['path'])]) for r in resources['resource_refs']),
            'all loaded149 resources covered by actual held guard')
        before=[doc(r['path']) for r in facts['before_archive_refs']];current=[doc(r['path']) for r in after['archive_refs']]
        check(all(same_bytes(r,p) for r,p in zip(facts['before_archive_refs'],q['before_canonical_refs'])),'complete full4 before archive exact bytes')
        check(all(same_bytes(r,p) for r,p in zip(after['archive_refs'],a['current_canonical_refs'])),'complete cp372 full4 actual archives exact bytes')
        check([before[0]['revision'],before[1]['revision'],current[0]['revision'],current[1]['revision']]==[371,175,372,176],'actual CP371/OW175 to CP372/OW176')
        projected=m.projection(before[0],before[1],facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],a['facts_ref'],owner,worker,q['created_utc'])
        check(projected==(current[0],current[1]),'pure exact projected committed pair and complete inverse')
        check(current[0].get('failure_counters')==before[0].get('failure_counters') and current[0]['work_in_progress'].get('root_next_failure_ordinal_live')==before[0]['work_in_progress'].get('root_next_failure_ordinal_live'),
            'all original failure counters and next ordinal unchanged')
        check(all(Path(r['path']).read_bytes()==Path(s['path']).read_bytes() for r,s in zip(facts['before_archive_refs'][2:],after['archive_refs'][2:])),
            'actual SS and CM39 unchanged')
        committed=doc(journal/'committed.json')
        check(committed['both_verified_while_exclusively_held'] is True and committed['written_indices']==[0,1]
            and all(same_bytes(r,p) for r,p in zip(committed['after_refs'],a['current_canonical_refs'][:2])),'actual TP committed exclusively-held pair')
        check(all(same_bytes(pin(journal/(str(i)+'.before.json')),facts['before_archive_refs'][i])
            and same_bytes(pin(journal/(str(i)+'.after.proposed.json')),after['archive_refs'][i]) for i in (0,1)),
            'TP complete before and after archived inverse bytes')
        check(current[0]['work_in_progress']['public22_existing_observation_scope_ref']==a['scope_ref']
            and current[0]['work_in_progress']['public22_existing_observation_facts_ref']==a['facts_ref'],'actual checkpoint scope facts registration')
        task=current[1]['card_path_bindings']['W05-99']['subtasks'][m.KEY]
        check(task==dict(owner,owner_document_ref=facts['owner_ref'],worker_document_ref=facts['worker_ref'],current_source_writer=None,formal_case_accepted_delta=0,parent_acceptance=False),
            'actual ownership exact registered document')
        check([x for x in current[0]['workers'] if x.get('slice_id')==m.SLICE]==[dict(worker,worker_document_ref=facts['worker_ref'])],
            'one exact actual checkpoint worker')
        hostpairs={};phases=['build','check','activate','readonly']
        for label,record in b['records'].items():
            binding=doc(record['binding_ref']['path']);raw=Path(record['raw_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True)
            check(len(lines)==3 and all(x.endswith(b'\n') for x in lines),'actual '+label+' exactly3rows')
            check(binding['original_capture_ref']==record['raw_ref'] and [len(x) for x in lines]==binding['source_line_bytes']
                and [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256'],'actual '+label+' full raw bindings')
            rows=[json.loads(x) for x in lines];first,last=rows[1:]
            check(rows[0]['payload']['id']==b['root_thread_id'] and first['payload']['call_id']==last['payload']['call_id']==binding['original_call_id'],
                'actual '+label+' Root session and matching callid')
            with Path(binding['source_audit_path']).open('rb') as stream:
                for off,line in zip(binding['source_line_offsets'],lines):
                    check(type(off) is int and off+len(line)<=binding['source_prefix_size_observed'],'actual '+label+' bounded offset')
                    stream.seek(off);check(stream.read(len(line))==line,'actual '+label+' original log bytes')
            check(binding['tool_call_timestamp']==first['timestamp'] and binding['tool_result_timestamp']==last['timestamp'],
                'actual '+label+' original timestamps')
            check(m.when(q['lease_issued_at'])<=m.when(first['timestamp'])<=m.when(last['timestamp'])<m.when(q['lease_expires_at']),
                'actual '+label+' execution inside historical lease')
            hosts=[x for x in m.structured_values(last['payload']['output']) if x.get('chunk_id')==record['chunk_id']]
            check(len(hosts)==1,'actual '+label+' exact returned host dictionary')
            hostpairs[label]=dict(host=hosts[0],call=first,result=last)
        for phase in phases:
            start,end=hostpairs[phase+'_start'],hostpairs[phase+'_complete']
            check(type(start['host'].get('session_id')) is int and start['host']['session_id']>0,'actual '+phase+' started session')
            check(end['host'].get('exit_code')==0 and type(end['host'].get('exit_code')) is int,'actual '+phase+' outer exit0')
            check(str(start['host']['session_id']) in str(end['call']['payload']),'actual '+phase+' completion waits original session')
            check('PYTHON_EXIT=0' in end['host']['output'].upper(),'actual '+phase+' explicitly observed Python exit0')
        returned=doc(b['caller_return_ref']['path']);observation=doc(b['observation_ref']['path'])
        check(returned['status']=='READONLY_83_TABLES_VALIDATED_PENDING_NONAUTHOR_REVIEW' and returned['error'] is None
            and returned['secondary_errors']==[] and returned['automatic_retry'] is False,'actual caller returned successful readonly only')
        check(returned['leaf_returned']==observation['leaf_result'] and observation['no_original_case_writes'] is True,'actual observation matches returned leaf and original immutable case')
        leaf_result=returned['leaf_returned']
        check(leaf_result['table_count']==83 and leaf_result['database_mode']=='ro,immutable,query_only'
            and leaf_result['raw_rows_emitted'] is False and leaf_result['new_native_children']==0 and leaf_result['original_ordinal']==1025,
            'actual readonly83 summary, no extra Native and no raw credential rows')
        check(any(x.get('schema')=='researchos.root-public22-existing-caller-return.v1' and x==returned
            for x in m.structured_values(hostpairs['readonly_complete']['host']['output'])),'actual returned stdout binds exact persisted caller record')
        filetimes=[]
        for call in original['state']['calls']:
            value=call['observation']['creation_time_100ns'];decimal=m.native_observation(call['observation'])
            check(type(value) in (int,str) and decimal==str(value) and int(decimal)>2**53 and int(decimal)<=2**64-1,
                'actual old '+call['phase']+' uint64 FILETIME exact Python integer/string')
            filetimes.append(dict(phase=call['phase'],creation_time_decimal=decimal,actual_exit=call['actual_exit'],result_ref=call['result_ref']))
        check(original['state']['first_failure']['message']=='PUBLIC_RESTORE_SCHEMA_MISMATCH'
            and original['assignment']['ordinal']==1025 and original['state']['status']=='STOPPED_AT_FIRST_FAILURE',
            'original1025 remains failed and last actual child0 remains distinct')
        check(all(bool(Path(r['path']).stat().st_file_attributes&stat.FILE_ATTRIBUTE_READONLY) for r in original['baseline']['references']),
            'original baseline retains real readonly attributes')
        leaf_text=Path(scope['leaf_runner_ref']['path']).read_text(encoding='utf-8');tree=ast.parse(leaf_text)
        oracle=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validate_restore22')
        recheck=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='recheck_existing_public22')
        readonly=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='readonly_database_observation')
        check(all(token in ast.get_source_segment(leaf_text,oracle) for token in ('PUBLIC_RESTORE_83_TABLES_REQUIRED','PUBLIC_RESTORE_TABLE_SET_MISMATCH',
            'PUBLIC_RESTORE_TABLE_STATE_MISMATCH','PUBLIC_RESTORE_CREDENTIAL_ROWS_MISMATCH','PUBLIC_RESTORE_TRIGGER_MISMATCH')),
            'actual pinned all83 table oracle requires exact schema/trigger/digest/revocation')
        check('validate_restore22(restored, source, manifest, expected_sql)' in ast.get_source_segment(leaf_text,recheck)
            and '?mode=ro&immutable=1' in ast.get_source_segment(leaf_text,readonly) and 'PRAGMA query_only=ON' in ast.get_source_segment(leaf_text,readonly),
            'actual successful exact pinned leaf path ran all83 readonly oracle')
        evidence=save('actual-independent-checks.json',dict(status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',
            actor_id=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],input_bundle_ref=pin(P),checks=checks,
            held_refs=refs,actual_original_hostpairs=b['records'],old4_exact_FILETIME=filetimes,
            readonly83_oracle_source_ref=scope['leaf_runner_ref'],oracle_lines=[oracle.lineno,oracle.end_lineno],
            loaded149_refs=resources['resource_refs'],actual_933_guard_ref=b['source_guard_closed_ref'],
            original1025_result='FAILED_RETAINED',actual_Go_runs_by_reviewer=0,actual_SQL_queries_by_reviewer=0,
            actual_new_Native_children_by_reviewer=0,dispatcher_runs=0,model_calls=0,live_CP_OW_held=False,
            historic_Canon_business_refs_recursed=False,private_owner_or_key_read=False,formal_acceptance=False,parent_acceptance=False,
            unresolved=['schema21','full20to24','freshMain23_build_and_main23to24'],Root_current_dynamic_CAS_required=True))
    finally:
        closed=guard.close();guard_ref=save('independent-Source-guard.closed.json',closed)
    assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
    print(json.dumps(dict(status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',checks=len(checks),evidence_ref=evidence,
        guard_ref=guard_ref,retained_handles_count=0,SQL_queries_by_reviewer=0,new_Native_children_by_reviewer=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
