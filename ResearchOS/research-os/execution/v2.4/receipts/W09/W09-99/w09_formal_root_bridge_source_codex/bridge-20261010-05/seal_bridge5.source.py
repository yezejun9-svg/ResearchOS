"""Publish a Source handoff only. Independent review and all Root authority remain pending."""
from pathlib import Path
from datetime import datetime, timezone
import json, types

R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;OLD=D.parent/'bridge-20261010-04'
P=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(P)
exec(compile(P.read_bytes(),str(P),'exec'),s.__dict__);s.D=D
def read(p):return json.loads(Path(p).read_bytes())
oh=read(OLD/'HDF.json');controls=read(D/'delta-controls.json');built=controls['built']
assert controls['failure'] is None and controls['passed']==controls['count']
closed=read(built['source_guard_ref']['path'])
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
original=s.capture('dbf820',1,None,1185)
success=s.capture('233c90',0,0)
s.write('original1185.origin.json',dict(original_ordinal=1185,actor_id='codex:/root/full_w09_source_review',
    original_io=original,actual_outer_exit=1,actual_python_exit=None,actual_Native_exit=None,actual_Go_exit=None,
    actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_TP_exit=None,
    cause='Read-only rg addressed nonexistent ops/ci/formal_case_index.py. Existing BR4 successful read prefix retained.',
    original_failure_retained=True,automatic_retry=False,product_calls=0))
s.write('actual-source-build-hostpair.json',success)
generation='bridge-20261010-05';author='codex:/root/full_w09_source_review';backend='/root/full_w09_source_review'
now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
contract=dict(read(oh['root_calling_contract_ref']['path']))
contract.update(generation=generation,source_revision_uuid=controls['source_revision_uuid'],source_author=author,
    source_author_backend=backend,source_thread_id=s.THREAD,source_ref=built['source_ref'],
    consumer_launcher_ref=built['consumer_launcher_ref'],
    CLI_prefix=['C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe','-I','-S','-B','-X','utf8',built['source_ref']['path']],
    historical_current4_contract=dict(schema='researchos.w09-bridge-historical-current4.v1',
        meaning='ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY',
        fields=['schema','meaning','canonical_refs','archive_refs'],
        exactly_four_same_order=['checkpoint','path_ownership','step_state','commands'],
        canonical_identity_absolute_exact_three_keys=True,
        archive_location='Same exact proposal output directory: canonical-<Canon stem>.original.json',
        archive_bytes='Original bytes while proposal-stage current4 SourceReadGuard is held; archive SHA/bytes exactly equal canonical identity.',
        proposal_generation_and_source_review_binding_required=True,
        historical_SS_CM_must_equal_fresh_request_SS_CM=True,
        inline_uncovered_Canon_refs_in_historical_publication_or_role_input='REJECTED',
        polluted_historical_dependency_snapshots='REJECTED'),
    persistent_dependency_snapshots=dict(Canon_four_excluded=True,other_files_inventories_audit_ranges_preserved=True,
        fresh_authority_snapshot_separate=True,fresh_request_current4_explicitly_bound=True,
        non_TP_stage_current4_guarded=True,TP_stages='activate/publish-registration: CP/OW exclusively held only by unchanged update_pair CAS; SS/CM remain SourceReadGuard-held'),
    actual_executed=False,independent_Source_review_required=True,execution_grant=False,formal_acceptance=False)
md='''# Bridge05 Root calling contract

This is a Source handoff by codex:/root/full_w09_source_review. It is not an execution grant, Source acceptance, Mode decision or formal acceptance.

Use the sealed Caller as __main__ with locked Python -I -S -B -X utf8. Source review must be independent and bind the new HDF/MF, Source and unchanged launcher. The existing ten-stage request schema, actual Root request/grant audit, backend identities and six Main routes remain mandatory. Fresh Root Scope.source_actor is /root/full_w09_source_review; verifier is /root/backup_regression_resources.

At propose, the current4 SourceReadGuard holds all four original Canon bytes while the Caller saves four immutable canonical-<stem>.original.json files in the proposal's own output directory. The proposal has generation bridge-20261010-05 and historical_current4 with exactly schema/meaning/canonical_refs/archive_refs. Canonical identities remain absolute three-key refs in original order; archive refs must bind exactly the same SHA/bytes at the same exact proposal directory. Missing, duplicate, foreign, altered or borrowed archives are refused. SS/CM historical identities must match the fresh request's SS/CM.

History is only history. The dependency walker exempts exactly the validated proposal.current4 plus its historical proof's identity vector; it holds and rechecks the archive files. Any other inline Canon ref in that proposal, publication or role input is refused. Historical snapshots containing any of the four Canon paths are refused. No global Canon/ref/physical exemption is introduced.

Persistent dependency snapshots omit all four Canon files. Inventories, audit ranges and every other read dependency remain checked. A separate fresh authority snapshot explicitly binds req.current4, and every stage preserves current4, Source/Root audits, current registered proposal/worker/owner/finite lease and exact Main Native/Mode gates. Activation additionally requires proposal.current4 == req.current4. The unchanged transaction implementation owns CP/OW under exclusive CAS; activate/publish-registration never keep SourceReadGuard handles over that pair, while SS/CM remain guarded.

Root must use a fresh new proposal and Scope for Bridge05. Root stages, Scope issuance, Native/Go/SQL/dispatcher/model execution, Canon mutation and Source acceptance were not performed by this author. Prior Bridge03/04 and diagnostics are immutable. Original1185 is a read-only path lookup failure and remains retained with actual tool I/O; no child exits are inferred.
'''
with (D/'ROOT_CALL_CONTRACT.md').open('xb') as f:f.write(md.encode('utf-8'))
contract['contract_ref']=s.pin(D/'ROOT_CALL_CONTRACT.md')
contract_ref=s.write('root-calling-contract.source.json',contract)
g=s.guard();held=[s.pin(p) for p in D.iterdir() if p.is_file()]
try:
    g.acquire(held)
    assert s.pin(D/'w09_root_bridge.source.py')==built['source_ref']
    assert s.pin(D/'consumer_launch.source.py')==built['consumer_launcher_ref']
    assert built['consumer_launcher_ref']['sha256']==oh['consumer_launcher_ref']['sha256']
finally:seal_guard=s.write('seal-source-guard.closed.json',g.close())
sg=read(seal_guard['path']);assert sg['closed'] and sg['retained_handles_count']==0 and sg['errors']==[]
mf=s.write('MF.json',dict(schema='researchos.w09-formal-root-bridge-source-manifest.v3',
    members=[s.pin(p) for p in sorted(D.iterdir(),key=lambda p:p.name) if p.is_file()],
    exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
h=dict(schema='researchos.w09-formal-root-bridge-source-handoff.v3',source_author=author,source_author_backend=backend,
    actual_source_thread=s.THREAD,actual_parent_thread='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    status='SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',generation=generation,created_utc=now,
    source_revision_uuid=controls['source_revision_uuid'],source_ref=built['source_ref'],
    consumer_launcher_ref=built['consumer_launcher_ref'],contract_ref=s.pin(D/'ROOT_CALL_CONTRACT.md'),
    root_calling_contract_ref=contract_ref,manifest_ref=mf,
    base_hdf_ref=s.pin(OLD/'HDF.json'),base_mf_ref=s.pin(OLD/'MF.json'),base_source_ref=oh['source_ref'],
    base_source_contribution=oh['original_Attach_contribution'],exact_inverse_ref=built['inverse_ref'],patch_ref=built['patch_ref'],
    source_inputs_ref=built['inputs_ref'],delta_controls_ref=s.pin(D/'delta-controls.json'),
    source_guard_ref=built['source_guard_ref'],seal_source_guard_ref=seal_guard,actual_source_build_host=success,
    original1185_io=original,new_original_failures=[1185],historical_search_no_match=dict(chunk='2e9992',failure_ordinal=None),
    historical_BR4_delta_controls_ref=oh['delta_controls_ref'],old_successful_controls_rerun=False,
    finite_delta_controls=controls['count'],finite_new_seal_checks=1,
    changes=['Proposal freezes complete original current4 into four immutable same-directory archives.',
        'History walker resolves only explicit archive-covered proposal.current4; other inline Canon refs are refused.',
        'Persistent snapshots exclude Canon; fresh authority/current4 guard and TP CAS remain separate and mandatory.',
        'New generation/selfrefs, same actual Full author and Backup verifier; unchanged consumer launcher and Main gates.'],
    guards_closed_zero=True,retained_handles_count=0,live_Canon_handles_held=0,
    independent_source_review_required=True,independent_source_review_ref=None,Source_author_self_acceptance=False,
    verifier_backend='/root/backup_regression_resources',future_Root_Scope_source_actor=backend,
    future_Root_Scope_source_author_canonical=author,future_Root_scope=None,future_Root_request=None,
    future_execution_grant=None,future_Mode_refs=None,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
    actual_bridge_stages=0,actual_Main_module_calls=0,actual_Native_Go_SQL_model_TP_calls=0,
    Main_Canon_Scope_written=False,actual_product_exits=dict(Native=None,Go=None,SQL=None,dispatcher=None,model=None,TP=None),STOP=True)
hdf=s.write('HDF.json',h)
print(json.dumps(dict(schema='researchos.w09-bridge-source-delivery.v1',operation='SOURCE_PREPARED',source_author=author,
    source_author_backend=backend,generation=generation,source_refs=[hdf,mf,contract_ref],source_ref=built['source_ref'],
    consumer_launcher_ref=built['consumer_launcher_ref'],delta_controls=controls['count'],guard_closed_zero=True,
    original1185_io=original,independent_Source_acceptance=False,execution_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False))
