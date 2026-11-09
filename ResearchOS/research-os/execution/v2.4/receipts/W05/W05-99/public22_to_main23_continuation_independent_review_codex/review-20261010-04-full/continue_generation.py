"""Run only unreached Source04 review tail; original prefix and failure remain immutable."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-04'
OLD=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-03'
PR=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-03-full'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
AUTHOR_AUDIT=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public22-main23-continuation-source04.actual-audit.root.json'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
h=json.loads((N/'HDF.json').read_bytes());lineage=json.loads(Path(h['predecessor_lineage_ref']['path']).read_bytes());author=json.loads(AUTHOR_AUDIT.read_bytes())
prefix=json.loads((D/'independent-delta-result.json').read_bytes());prefix_guard=json.loads(Path(prefix['source_guard_ref']['path']).read_bytes())
assert prefix['passed']==prefix['count']==7 and prefix_guard['closed'] is True and prefix_guard['retained_handles_count']==0
refs=[s.pin(__file__),s.pin(HELPER),s.pin(N/'HDF.json'),h['manifest_ref'],h['caller_ref'],h['source_inputs_ref'],h['predecessor_lineage_ref'],
    s.pin(OLD/'public22_to23_root.source.py'),s.pin(PR/'decision.json'),*lineage['frozen_lineage']['after_archive_refs'],
    s.pin(AUTHOR_AUDIT),author['original_capture_ref']]
g=s.guard();checks=[];failure=None;observations={};prep=None
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok:raise ValueError(name)
try:
    g.acquire(refs)
    raw=g.get_buffer(h['caller_ref']['path']);old=g.get_buffer(str(OLD/'public22_to23_root.source.py'))
    m=s.inert(N/'public22_to23_root.source.py',raw)
    i=json.loads(g.get_buffer(h['source_inputs_ref']['path']))
    archive_cp,archive_ow=[json.loads(g.get_buffer(ref['path'])) for ref in lineage['frozen_lineage']['after_archive_refs']]
    # No fixture document is written, registered, or represented as an issued Root grant.
    scope_ref=dict(path=str(D/'Source_fixture_UNISSUED_scope.json'),sha256='1'*64,bytes=0)
    owner_ref=dict(path=str(D/'Source_fixture_UNISSUED_owner.json'),sha256='2'*64,bytes=0)
    worker_ref=dict(path=str(D/'Source_fixture_UNISSUED_worker.json'),sha256='3'*64,bytes=0)
    facts_ref=dict(path=str(D/'Source_fixture_UNISSUED_facts.json'),sha256='4'*64,bytes=0)
    owner=dict(scope_ref=scope_ref,lease_id='Source_fixture_UNISSUED_NEW_LEASE',selected_worker_id=m.ROOT)
    worker=dict(scope_ref=scope_ref,lease_id=owner['lease_id'],selected_owner_ref=owner_ref,worker_id=m.ROOT)
    cp=copy.deepcopy(archive_cp);ow=copy.deepcopy(archive_ow)
    cp['revision']=987;ow['revision']=654
    cp['work_in_progress']['root_next_failure_ordinal_live']=2000001
    assert type(cp['failure_counters']) is list
    cp['failure_counters'].append({'Source_fixture_future_before_marker':True,'retained':True,'value':2000000})
    snapshot=copy.deepcopy((cp,ow,owner,worker))
    m.predecessor_generation(cp,ow,scope_ref,owner,worker)
    check('actual_closed_predecessor_allows_only_Source_fixture_fresh_generation',snapshot==(cp,ow,owner,worker),dict(Source_fixture_only=True,Root_grant=False))
    def reject(name,mutate,expected,projection_gate=False):
        cx,ox,own,work=copy.deepcopy(snapshot);mutate(cx,ox,own,work);code=None
        try:
            if projection_gate:m.projection(cx,ox,scope_ref,owner_ref,worker_ref,facts_ref,own,work,'Source_fixture_created')
            else:m.predecessor_generation(cx,ox,scope_ref,own,work)
        except ValueError as exc:code=str(exc)
        check(name,code==expected,dict(observed=code,Source_fixture_only=True))
    p=m.PREDECESSOR
    def oldrow(ox):return ox['card_path_bindings']['W05-99']['subtasks'][p['key']]
    def oldworker(cx):return next(item for item in cx['workers'] if item.get('slice_id')==p['slice_id'])
    reject('missing_predecessor_subtask_rejected',lambda cx,ox,own,work:ox['card_path_bindings']['W05-99']['subtasks'].pop(p['key']),'PREDECESSOR_EXACTLY_ONE')
    reject('active_predecessor_worker_rejected',lambda cx,ox,own,work:oldworker(cx).update(lease_status='ACTIVE'),'PREDECESSOR_CLOSED_CONSUMED')
    reject('duplicate_old_worker_rejected',lambda cx,ox,own,work:cx['workers'].append(copy.deepcopy(oldworker(cx))),'PREDECESSOR_EXACTLY_ONE')
    reject('extra_scope_chain_alias_rejected',lambda cx,ox,own,work:ox['card_path_bindings']['W05-99']['subtasks'].update(Source_fixture_alias=dict(scope_ref=p['scope_ref'])),'PREDECESSOR_UNIQUE_CHAIN')
    reject('wrong_closed_owner_ref_rejected',lambda cx,ox,own,work:oldrow(ox).update(owner_document_ref=owner_ref),'PREDECESSOR_OWNER_WORKER')
    reject('unlisted_old_record_field_mutation_rejected',lambda cx,ox,own,work:oldworker(cx).update(Source_fixture_unlisted=True),'PREDECESSOR_CLOSED_BYTES')
    reject('new_KEY_collision_rejected',lambda cx,ox,own,work:ox['card_path_bindings']['W05-99']['subtasks'].update({m.KEY:{}}),'READONLY_SLICE_ALREADY_REGISTERED',True)
    reject('new_SLICE_collision_rejected',lambda cx,ox,own,work:cx['workers'].append(dict(slice_id=m.SLICE)),'READONLY_SLICE_ALREADY_REGISTERED',True)
    reject('old_consumed_lease_reuse_rejected',lambda cx,ox,own,work:own.update(lease_id=p['lease_id']),'NEW_GENERATION_FRESH_SCOPE_LEASE')
    out_cp,out_ow=m.projection(cp,ow,scope_ref,owner_ref,worker_ref,facts_ref,owner,worker,'Source_fixture_created')
    check('future_before_complete_counter_and_next_preserved_without_archive_reset',
        out_cp['failure_counters']==cp['failure_counters']
        and out_cp['work_in_progress']['root_next_failure_ordinal_live']==cp['work_in_progress']['root_next_failure_ordinal_live']==2000001
        and out_cp['revision']==988 and out_ow['revision']==655 and snapshot==(cp,ow,owner,worker))
    check('all_predecessor_rows_and_unrelated_owner_records_unchanged',
        all(out_ow['card_path_bindings']['W05-99']['subtasks'][key]==value for key,value in ow['card_path_bindings']['W05-99']['subtasks'].items())
        and out_cp['workers'][:-1]==cp['workers'] and m.KEY in out_ow['card_path_bindings']['W05-99']['subtasks'])
    lines=g.get_buffer(author['original_capture_ref']['path']).splitlines(keepends=True)
    assert len(lines)==3 and all(line.endswith(b'\n') for line in lines)
    head,meta,final=[json.loads(line) for line in lines];payload=final['payload']
    check('actual_Source04_Attach_Final_identity_and_full_refs',head['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        and meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item'
        and final['ordinal']==meta['ordinal']+1 and meta['timestamp']==final['timestamp']=='2026-10-10T01:52:52.500Z'
        and payload['type']=='agent_message' and payload['author']=='/root/attach_restore_independent_review'
        and payload['recipient']=='/root' and final['metadata']['client_authored'] is False
        and author['binding_sha256']==s.pin(N/'HDF.json')['sha256']
        and all(m.contains_ref(payload['content'],ref) for ref in [s.pin(N/'HDF.json'),h['manifest_ref'],h['caller_ref']]))
    check('actual_author_capture_line_hashes_and_unique_offsets',author['original_line_sha256']==[hashlib.sha256(line).hexdigest() for line in lines]
        and author['source_line_offsets']==sorted(set(author['source_line_offsets'])) and author['source_line_offsets'][0]==0)
    with Path(author['source_audit_path']).open('rb') as f:
        for offset,line in zip(author['source_line_offsets'],lines):
            f.seek(offset);assert offset+len(line)<=author['source_prefix_size_observed'] and f.read(len(line))==line
    check('actual_author_Root_offset_original_bytes_readback',True)
    prior=json.loads(g.get_buffer(str(PR/'decision.json')))
    before=ast.parse(old);after=ast.parse(raw)
    def functions(tree):return {node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    a=functions(before);b=functions(after)
    check('Source03_runtime_and_business_closure_inherited_without_replay',prior['decision']=='ACCEPTED_SOURCE_ONLY'
        and prior['runtime_closure_reviewed'] is True and h['runtime_resources_ref']==prior['runtime_resources_ref']==i['runtime_resources_ref']
        and all(ast.dump(a[key],include_attributes=False)==ast.dump(b[key],include_attributes=False) for key in a if key!='projection')
        and ast.dump(ast.Module(body=[node for node in before.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False)
            ==ast.dump(ast.Module(body=[node for node in after.body if isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[]),include_attributes=False),
        dict(runtime_manifest_reused=149,runtime_actual_required_reused=144,Source03_full26_replayed=False,author19_replayed=False))
    observations=dict(complete_Source03_inverse_from_prefix=True,actual_source_author_audit_ref=s.pin(AUTHOR_AUDIT),
        archive_pair_refs=lineage['frozen_lineage']['after_archive_refs'],archive_revisions_only=[386,190],
        actual_live_CP387_OW191_read=False,Source_fixture_future_next=2000001,
        generation=dict(KEY=m.KEY,SLICE=m.SLICE,MODE=m.MODE,STATE=m.STATE),
        runtime_closure_evidence_ref=prior['runtime_closure_evidence_ref'],
        original1201_retained=True,original1025_retained=True,Root_Runtime_qualification_issued=False)
    prep=dict(source_hdf_ref=s.pin(N/'HDF.json'),source_mf_ref=h['manifest_ref'],
        **{key:h[key] for key in ('caller_ref','source_inputs_ref','calling_contract_ref','runtime_resources_ref','main23_bound_ref','existing22_decision_ref')},
        source_author=h['source_author'],runtime_boundary=prior['runtime_review_boundary'],
        inherited_review_ref=s.pin(PR/'decision.json'),actual_source_author_audit_ref=s.pin(AUTHOR_AUDIT),
        lineage_ref=h['predecessor_lineage_ref'],created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
        observations=observations)
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('tail-guard.closed.json',g.close())
    result_ref=s.write('tail-delta-result.json',dict(checks=checks,count=len(checks),passed=sum(x['passed'] for x in checks),
        failure=failure,observations=observations,source_guard_ref=guard_ref,held_count=len(refs),reused_prefix_ref=s.pin(D/'independent-delta-result.json'),
        Source_only=True,Source_fixtures_are_not_Root_Scope_or_grant=True,
        product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0),execution_grant=False,formal_acceptance=False))
if prep is not None:s.write('review-preparation-context.json',prep)
print(json.dumps(dict(count=len(checks),passed=sum(x['passed'] for x in checks),failure=failure,
    source_guard_ref=guard_ref,result_ref=result_ref,Source_only=True,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
