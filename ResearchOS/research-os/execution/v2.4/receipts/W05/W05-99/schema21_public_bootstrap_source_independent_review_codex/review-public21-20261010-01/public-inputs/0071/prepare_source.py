"""Task87 Source preparation only: pinned public files, no SQLite or processes."""
import ast, hashlib, json, ntpath, re, sys, traceback, types
from pathlib import Path
from datetime import datetime, timezone
Q=Path(__file__).resolve().parent
B=Q.parent.parent
R=B.parents[4]
AUTHOR='codex:/root/backup_regression_resources'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def need(ok,code):
    if not ok: raise AssertionError(code)
def pin(path):
    p=Path(path); raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def load(ref):
    raw=Path(ref['path']).read_bytes()
    need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'PIN_DRIFT')
    return json.loads(raw)
def exact(path,sha,n):
    ref=pin(path); need(ref['sha256']==sha and ref['bytes']==n,'FIXED_INPUT_PIN')
    return ref
def save(name,value):
    p=Q/name
    with p.open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(p)
def unique(refs):
    out={}
    for ref in refs:
        key=ntpath.normcase(ntpath.normpath(ref['path'].replace('/','\\')))
        if key in out: need(out[key]['sha256']==ref['sha256'] and out[key]['bytes']==ref['bytes'],'INCONSISTENT_REF')
        else: out[key]=ref
    return [out[k] for k in sorted(out)]
def main():
    # These are the enumerated, real prior Source endpoints, not guessed filenames.
    builder_dir=B/'schema21_programme_builder_source_codex/main21b-20261010-01'
    builder_ref=exact(builder_dir/'contract.v2.json','1472e40c8806dcb82de62352378c306077fef8e674925b57941f305527bf4402',22410)
    builder=load(builder_ref)
    root_bound_ref=exact(R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/old21.programme.qualification.bound.actual.root.json','8b5d6565586e51be741fa25b2f79cf41c55d0f8733c43d0f6a60f2ebca738a70',5911)
    bound=load(root_bound_ref)
    need(bound['status']=='QUALIFIED_OLD21_BUILD' and bound['source_schema_version']==21 and bound['execution_grant'] is False,'REAL_QUALIFICATION_NOT_GRANT')
    helper_ref=builder['base_helper_ref']; guard_ref=builder['source_guard_ref']; job_ref=builder['owned_job_ref']
    for ref in (helper_ref,guard_ref,job_ref): load_bytes=Path(ref['path']).read_bytes(); need(len(load_bytes)==ref['bytes'] and hashlib.sha256(load_bytes).hexdigest()==ref['sha256'],'SHARED_SOURCE_PIN')
    s22dir=Path(helper_ref['path']).parent
    helper_hdf_ref=exact(s22dir/'HDF.json','6f2ec5e3eeb6c06a343ab9fc2fdfb1462e0e740da72986f5c8b7639fab31187e',3494)
    helper_mf_ref=exact(s22dir/'MF.json','cca5a67720a616832d8503158c2c7b2c2933638bcdfc5da2b3eb69dcd1e78ca5',9010)
    helper_review_hdf_ref=pin(B/'public22_runner_independent_source_review_codex/pub22r-20261009-02/HDF.json')
    helper_review=load(helper_review_hdf_ref)
    need(helper_review['decision']=='ACCEPTED_SOURCE_ONLY' and helper_review['runner_ref']['sha256']==helper_ref['sha256'],'EXACT_HELPER_SOURCE_REVIEW')
    helper_review_mf_ref=helper_review['manifest_ref']; helper_review_decision_ref=helper_review['source_decision_ref']
    load(helper_review_mf_ref); load(helper_review_decision_ref)
    python_ref=exact(Path(sys.executable),'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',106328)
    package=R.parent/'ResearchOS_Implementation_Package_v2.4'
    spec_names=('00_START_HERE.md','08_AGENT_EXECUTION_GOAL.md','tools/task_packet.py','contracts/execution.plan.json','contracts/tasks.json','contracts/acceptance.json','tasks/steps/W05-99.md')
    spec_refs={name:pin(package/name) for name in spec_names}
    # Follow actual dictionary refs; the full completed Root/peer host chain is public.
    programme_refs=[root_bound_ref,*bound['program_refs'].values(),bound['qualification_ref'],*bound['review_refs']]
    capture_bindings={}
    for key in ('payload_ref','root_issuance_binding_ref','independent_peer_delivery_binding_ref'):
        ref=bound[key]; programme_refs.append(ref); obj=load(ref); capture_bindings[key]=obj
        if key!='payload_ref':
            need(type(obj) is dict and type(obj.get('original_capture_ref')) is dict,'ACTUAL_COMPLETED_HOST_CAPTURE_REF')
            programme_refs.append(obj['original_capture_ref'])
    # Existing completed build provenance is held at future runtime; no Go is run.
    programme_refs.append(bound['provenance_ref'])
    runtime_refs=builder['runtime_source_refs']; bootstrap_refs=builder['public_bootstrap_source_refs']
    versions=sorted(int(ntpath.basename(k)[:4]) for k in runtime_refs if re.fullmatch(r'[0-9]{4}_.+\.sql',ntpath.basename(k)))
    need(versions==list(range(1,22)) and 'migrations/sqlite/next_v24_sessions.sql' in runtime_refs,'REAL_FROZEN_PREFIX_PLUS_ADDON')
    common_refs=[builder_ref,builder['frozen_source_manifest_ref'],helper_ref,guard_ref,job_ref,helper_hdf_ref,helper_mf_ref,helper_review_hdf_ref,helper_review_mf_ref,helper_review_decision_ref,python_ref,*spec_refs.values(),*runtime_refs.values(),*bootstrap_refs.values(),*programme_refs]
    guard_module=types.ModuleType('task87_reviewed_guard')
    exec(compile(Path(guard_ref['path']).read_bytes(),guard_ref['path'],'exec'),guard_module.__dict__)
    guard=guard_module.SourceReadGuard(); references=unique(common_refs)
    try:
        guard.acquire(references)
        input_manifest_ref=save('input-manifest.json',{
            'schema':'researchos.schema21-public-bootstrap-input-manifest.v1',
            'source_author':AUTHOR,'references':references,
            'scope':'finite public programme/Source/contract resources only; no credentials or live Canon',
            'runtime_extra_resources':'Future separately qualified runtime closure must add exact Python standard-library/SQLite extension and DLL/Windows OwnedJob dependencies and current runner/caller/reviews/Root scope captures; this Source manifest is not that qualification.',
            'historical_build_provenance_read_only':True,'numbered_sql_versions':versions,
            'unnumbered_addon_ref':runtime_refs['migrations/sqlite/next_v24_sessions.sql'],
            'formal_acceptance':False,'execution_grant':False})
        contract={
            'schema':'researchos.schema21-public-bootstrap-contract.v1',
            'status':'SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_SEPARATE_ROOT_CALLER',
            'source_author':AUTHOR,'source_author_thread':'01a11cee-bf59-7a01-be0e-9f799f9b1084',
            'original_programme_source_author':bound['source_author'],
            'helpers_original_source_author':'codex:/root/native_temp_independent_review',
            'helpers_independent_source_review_author':helper_review['actor_id'],
            'root_thread_id':ROOT_THREAD,'runner_ref':pin(Q/'public21_runner.py'),
            'entry':'public21_runner.run_registered_case(contract_ref,request_ref,live_root_scope)',
            'scope_key':'PUBLIC21_BOOTSTRAP_ONLY','mode':'NATIVE_COMPONENT_OBSERVATION',
            'old21_control':bound['program_refs']['control'],'old21_backup':bound['program_refs']['backup'],
            'old21_qualification_ref':root_bound_ref,
            'old21_independent_qualification_ref':bound['qualification_ref'],
            'old21_qualification_chain_refs':unique(programme_refs),
            'old21_root':builder['historical_source_root'],
            'source_commit':builder['source_commit'],'source_tree':builder['source_tree'],
            'frozen_runtime_refs':runtime_refs,'public_bootstrap_source_refs':bootstrap_refs,
            'source_guard':guard_ref,'owned_job':job_ref,'public22_helpers_ref':helper_ref,
            'helpers_source_review_refs':{'HDF':helper_review_hdf_ref,'MF':helper_review_mf_ref,'decision':helper_review_decision_ref},
            'locked_python_ref':python_ref,'python_args':['-I','-S','-B','-X','utf8'],
            'input_manifest_ref':input_manifest_ref,'spec_refs':spec_refs,
            'output_parent':str(B/'integration_codex'),
            'exact_output_basename':'schema21-public-<32lowerhex>',
            'request_fields':['case_id','output_root'],
            'phases':['prepare','bootstrap21','inspect21','complete'],
            'public_cli':{'argv':['<qualified old21 control>','--bootstrap-owner','--credential-file','<new private owner file>'],'cwd':builder['historical_source_root'],'bounded_administrative_exit':True,'serve_required':False,'timeout_seconds':90,'native_child_limit':1,'backup_child_limit':0,'Go_children':0},
            'environment_keys':['SystemRoot','WINDIR','TEMP','TMP','RESEARCHOS_DATA_DIR'],
            'environment_policy':'Only two nonempty NUL-free inherited public Windows roots plus same isolated TEMP/TMP and a new source21 data root; no whole os.Environ, PATH, provider, HOME, key, proof-key or credential input.',
            'schema_oracle':{'numbered_ledger':list(range(1,22)),'unnumbered_addon':'next_v24_sessions.sql + installClientSessionFence','addon_not_numbered':True,'connection':'SQLite URI mode=ro&immutable=1; PRAGMA query_only=ON; all real table counts and row hashes; real schema-definition SHA256; integrity and foreign-key checks','database_from_public_control_only':True,'direct_database_creation_or_ledger_write':False,'rows_emitted':False,'owner_rows':1,'credential_rows':1,'business_rows_empty':True},
            'private_output_policy':'The genuine public CLI writes a new private 15-minute Owner fixture. Runner records path/existence only, never reads/copies/hashes Owner-file bytes or creates a credential input. It never authenticates a model/provider.',
            'baseline_policy':'After Job exits0/idle/closed, reject nonempty -wal/-shm/-journal; set readonly on DB, acquire exact FILE_SHARE_READ guard, read immutable SQLite, compare exact DB bytes before/after/final. Retain original new fixture and private Owner file, no automatic deletion/retry/recovery.',
            'Root_scope_interface':{
                'require_registered':'(contract_ref,request_ref,source_author=Backup): new registered PUBLIC21_BOOTSTRAP_ONLY scope, exact current leaf/contract/request and independent Source review before any read/mkdir/SQL/child.',
                'require_resources':'(contract_ref,input_manifest_ref): strict 7-key binding; full Root-issued runtime manifest and independent exact current Source/qualified resources with complete actual Root/peer captures; shape is not authority.',
                'qualified_old21_programmes':'(contract_ref,old21_qualification_ref): authenticate exact completed Root-bound programme and its actual independent peer/current Root issuance chain. Return exact 6-key binding, never build candidates or Main23/old22 permissions.',
                'require_phase':'(phase,request_ref,output_root): every finite phase in exact order revalidates new scope/owner/current4/fresh finite lease and retained resource guards.',
                'receipt_context':'(): return actual Root/executor/owner/scope/worker/lease/current4/provenance ref bindings without private credential bytes.'},
            'resource_binding_keys':sorted(['input_manifest_ref','source_review_ref','resource_qualification_ref','runtime_manifest_ref','outer_host_binding_ref','source_author','reviewer_actor']),
            'programme_binding_keys':sorted(['qualification_ref','program_refs','source_commit','source_tree','source_schema_version','outer_host_binding_ref']),
            'Root_caller_mandatory_contract':[
                'Implement separately reviewed Root caller; exact real Root actor and current parent thread; never trust JSON strings as issuer/peer evidence.',
                'Before leaf entry, hold current Source/resources and validate complete actual header/call/output plus anchored real peer FINAL and canonical codex actor/backend author mapping. Independent Verifier/reviewer differs actual executor and Source author.',
                'Register a new distinct PUBLIC21_BOOTSTRAP_ONLY scope, owner and finite lease for this exact one-shot case. Current4 is dynamic actual CAS, no fixed CP number, no old21 BUILD/Main23/public22 grant borrowing.',
                'Validate full runtime_manifest/resource_qualification/source_review business schemas, exact closed resource list, real Root-issued runtime qualification, nonauthor Source HDF/MF/decision and all actual host captures. Include caller/leaf/Sourceguard/OwnedJob/qualified native programs, actual locked Python/standard library/SQLite extension+DLL and loaded Windows resources.',
                'Root owns top-level execution and captures its full actual tool invocation and returned result after return. A pre-entry completed Root scope/qualification/activation/current4 capture may be outer_host_binding_ref; never require this future current case return before it exists.',
                'Lease interval must cover the 90-second child and finite preparation/oracle/cleanup. Root caller refuses released read handles, stale owner, wrong case, expired lease, changed current4/Source/pins, unknown actor, self-review or forged capture.',
                'Every child uses suspended assign-before-resume unnamed kill-on-close OwnedJob with all descendants; retain exact integer PID/FILETIME and actual primary exit; require idle/closed/zero active process and no cleanup errors. No taskkill/PID name lookup/unobserved exit inference.',
                'If bootstrap/oracle/guard/publication stops, save complete returned state and all actual stdout/stderr/call results; Root assigns original ordinal, preserve UNKNOWN exits and prior 1025/1109..1113 counters. No same-input retry or acceptance on partial output.',
                'Root and independent reviewer later reconcile case.closed persisted status versus returned closed_receipt.ref and full actual outer tool result; public_bootstrap_observed is only observation, not formal acceptance.' ],
            'W05_parent_boundary':{'card':'W05-99','cases':['A04','C11','C15'],'sole_final_owner':'A04','component_only':True,'all_22_parents_and_42_cases_unchanged':True,'accepted_case_delta':0},
            'future_Root_scope_ref':None,'future_current4_ref':None,'future_owner_ref':None,
            'future_lease_ref':None,'future_source_review_ref':None,'future_runtime_manifest_ref':None,
            'future_runtime_qualification_ref':None,'future_Root_original_capture_ref':None,
            'future_actual_case_ref':None,'future_independent_observation_ref':None,
            'scope_registration':False,'runtime_grant':False,'execution_grant':False,
            'formal_acceptance':False,'source_self_acceptance':False,
            'backup_restore_execution':False,'full20to24_acceptance':False,
            'original_1025_public22_failure_preserved':True,'Root_last_reported_next_original':1114}
        contract_ref=save('contract.json',contract)
        # Keep full byte sources untouched; bounded source excerpt provenance is explicit.
        excerpts={}
        for relative,ref in bootstrap_refs.items():
            if relative in ('apps/control/main.go','internal/domain/store.go','internal/domain/client_session_fence.go','internal/store/sqlite.go'):
                text=guard.get_buffer(ref['path']).decode('utf-8')
                lines=text.splitlines()
                terms={'apps/control/main.go':['flag.Bool("bootstrap-owner"','flag.String("credential-file"','if *bootstrapOwner','func bootstrap('],
                       'internal/domain/store.go':['func New(','filepath.Glob(','next_v24_sessions.sql','installClientSessionFence('],
                       'internal/domain/client_session_fence.go':['func installClientSessionFence','transcript_artifact_id','backup_restore_barriers','client_session_epoch_no_regression','client_session_require_fresh'],
                       'internal/store/sqlite.go':['func Open(','researchos.sqlite','func Bootstrap(']}[relative]
                excerpts[relative]={'ref':ref,'matches':[{'line':i+1,'text':line} for i,line in enumerate(lines) if any(term in line for term in terms)]}
        excerpt_ref=save('public-cli-source-evidence.json',{'schema':'researchos.schema21-public-bootstrap-source-evidence.v1','Source_only':True,'contract_ref':contract_ref,'exact_original_source_excerpts':excerpts,'numbered_sql_versions':versions,'session_addon_ref':runtime_refs['migrations/sqlite/next_v24_sessions.sql'],'programme_actual_qualification_ref':root_bound_ref,'bootstrap_executed_by_this_Source':False,'SQL_executed':False})
        save('Source-preparation.json',{'schema':'researchos.source-preparation-result.v1','source_author':AUTHOR,'contract_ref':contract_ref,'input_manifest_ref':input_manifest_ref,'public_cli_source_evidence_ref':excerpt_ref,'references_held':len(references),'namespace_new':True,'Main_Canon_old_Source_writes':0,'Native_Go_SQL_model_TP_calls':0,'current_scope_refs':None,'execution_grant':False,'formal_acceptance':False})
    finally:
        closed=guard.close(); save('source-preparation.guard.closed.json',closed)
    need(closed.get('closed') is True and closed.get('retained_handles_count')==0 and closed.get('verification')=='PASSED' and not closed.get('errors'),'SOURCE_GUARD_NOT_CLOSED')
    print(json.dumps({'contract_ref':contract_ref,'input_manifest_ref':input_manifest_ref,'guard_ref':pin(Q/'source-preparation.guard.closed.json'),'held_ref_count':len(references),'product_calls':0},ensure_ascii=False,sort_keys=True))
    return 0
if __name__=='__main__':
    code=1
    try: code=main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code)); sys.exit(code)
