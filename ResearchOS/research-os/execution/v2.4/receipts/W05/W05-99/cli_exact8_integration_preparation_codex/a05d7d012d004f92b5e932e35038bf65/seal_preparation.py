"""Metadata-only preparation seal. Never imports or executes the integration controller."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import datetime

ROOT=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':sha(b),'bytes':len(b)}
def save(name,d):
    with (N/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def tree(p):
    result={}
    for line in p.read_bytes().split(b'\0'):
        if line:
            head,name=line.split(b'\t',1);mode,kind,blob=head.decode('ascii').split()
            result[name.decode('utf-8')]={'mode':mode,'kind':kind,'blob':blob}
    return result

controller=N/'integrate_cli8.py'
syntax=ast.parse(controller.read_text(encoding='utf-8'))
exact=load(N/'exact8.json');owned={r['path'] for r in exact}
base=tree(N/'tree-a5.stdout.raw')
catalog_path=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json'
catalog=load(catalog_path)
prefixes={'adapters','apps','bootstrap','contracts','docs','internal','migrations','ops','release','scripts','spec','tests','third_party'}
planned={p for p in base if '/' not in p or p.split('/')[0] in prefixes}
planned|={r['path'] for r in catalog['git_resources']}
planned-=owned
planned|={'execution/toolchains/locked.json','execution/project_identity.json',
          '.local/w0599-main-stream-integration-r268/mu-worker.mjs',
          'execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-main-closure-r284/formal-index.json'}
save('protected-public-paths.planned.json',sorted(planned))
save('protected-public-plan.json',{
    'state':'PLANNED_FUTURE_MAIN_A5_VECTOR_NOT_CURRENT_BYTES',
    'paths_ref':ref(N/'protected-public-paths.planned.json'),'count':len(planned),
    'base_git_tree_ref':ref(N/'tree-a5.stdout.raw'),'historical_public_catalog_ref':ref(catalog_path),
    'rules':['Root must hash these exact current files after actual Main38 completion and its forward canonical registration.',
             'All8 owned files use explicit a5 preimage and candidate blob checks; they are excluded from immutable vectors.',
             'Canonical4 are separately bound to new grant immutable copies; old11 deleted files stay absent.',
             'Entire committed Git tree is compared after commit: every path outside8 must retain a5 mode/blob.',
             'Only previously catalogued public Go resources under evaluation are enumerated. No private holdout data, Host DB, Vault or keys are read.',
             'This is source-preservation inventory, not a newly compiled Go graph. Fresh43 compiler/WORK/archives/tests require later separate scope.'],
    'external_runtime_catalog_separate':True,'current_or_future_source_acceptance':False})

before=load(N/'canonical.before.json')
after=[]
for row in before:
    b=(ROOT/row['path']).read_bytes();p=N/('canonical.after.'+Path(row['path']).name)
    with p.open('xb') as f:f.write(b)
    after.append({'path':row['path'],'ref':ref(ROOT/row['path']),'copy_ref':ref(p),'unchanged':sha(b)==row['ref']['sha256']})
save('canonical.after.json',after)
git='C:/Program Files/Git/cmd/git.exe'
env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']}
env.update(PATH='C:/Windows/System32;C:/Windows',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
results={}
for name,args in [('final-head',['rev-parse','HEAD']),('final-status',['status','--porcelain=v1','--untracked-files=no']),('final-index',['diff','--cached','--name-only'])]:
    argv=[git]+args;start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result=subprocess.run(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=False)
    for kind,data in [('stdout',result.stdout),('stderr',result.stderr)]:
        with (N/(name+'.'+kind+'.raw')).open('xb') as f:f.write(data)
    save(name+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'environment':env,'started_at':start,'actual_native_exit':result.returncode,
                                'read_only':True,'timeout_seconds':30,'automatic_retry':False})
    if result.returncode!=0:raise RuntimeError('Readonly query stopped: '+name)
    results[name]=result.stdout
status=results['final-status'].decode('utf-8').splitlines()
deleted=[x[3:] for x in status if x.startswith(' D ')]
unstaged=sorted(x[3:] for x in status)
history=[x['ref'] for x in load(N/'source-reference-inputs.json')]
scope={
 'schema':'researchos.cli8-source-integration-scope.v1','status':'PREPARATION_ONLY_NOT_EXECUTABLE','owner':'codex:/root',
 'authorized':False,'expected_registration':None,'expected_before_registration':None,'registration_namespace':None,
 'operation_uuid':None,'new_output_root':None,
 'base':'a5d6d16ffaf129de0361470c3a1570228bd259a2','candidate':'b98738ac093ea55bb8700cfa724ddd9e6b2a1251',
 'candidate_parent':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
 'exact_paths':8,'union_paths':43,'apply_cap':1,'commit_cap':1,'git_step_cap':64,'product_tests_HTTP_SQL_models':0,
 'controller_ref':ref(controller),'exact8_ref':ref(N/'exact8.json'),'patch_ref':ref(N/'exact8-patch.stdout.raw'),
 'preparation_cp_ref':before[0]['copy_ref'],'historical_evidence_refs':history,
 'protected_source_paths_ref':ref(N/'protected-public-paths.planned.json'),'protected_source_vector_ref':None,
 'main38_completed_ref':None,'main38_manifest_ref':None,'main38_post_registration_audit_ref':None,'main38_execution_review_ref':None,
 'toolchain_lock_ref':ref(ROOT/'execution/toolchains/locked.json'),
 'owned_process_helper_ref':ref(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'),
 'runtime_resources_ref':ref(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft/gate-launcher-preparation-d58b6cfd52a44f0f9cee84344abda03d/controller_runtime_resources.json'),
 'status_ref':None,'old_deleted_paths':deleted,'expected_unstaged_paths':unstaged,
 'commit_identity':{'name':'ResearchOS Root Integration','email':'codex-root@localhost'},
 'commit_message':'Integrate reviewed CLI exact8 onto closed Main38',
 'required_future_registration':'Root chooses explicit tuple CP>321/OW>149, after closed Main38 and canonical head=a5; no inferred next number.',
 'limits':{'query_seconds':30,'apply_check_seconds':60,'apply_seconds':60,'commit_seconds':120,
           'controller_observed_seconds':900,'proposed_outer_owned_job_seconds':1200,'outer_job_cleanup_seconds':5,
           'max_file_bytes':268435456,'max_cumulative_hash_read_bytes':34359738368},
 'outer_launch_required':'Root must use pinned Python -I -S -X utf8 under owned Windows Job, save actual outer/native/cleanup; no direct bare-PID launch. FS read deadline is checked between chunks, not a hard syscall deadline.',
 'formal_increment':0,'source_acceptance':False,'fresh43_validation_authorized':False}
save('scope.proposed.json',scope)
save('future-authority-contract.json',{
 'state':'PROPOSED_NOT_EXISTING_NOT_AUTHORIZATION',
 'required_refs':['actual Main38 completed.json + complete seal','Root forward-only registration head=a5 + audit','non-author actual Main38 closure review','fresh CLI scope + independent controller review','new sealed Root CAS with explicit tuple >321','Root once grant + ordered4 immutable canonical copies'],
 'new_proposed_schema_contracts':{
   'researchos.main38-post-integration-registration-audit.v1':{'actor':'codex:/root','completed_ref':'exact ref','manifest_ref':'exact ref','registered_head':scope['base'],'actual_registration_exit':0},
   'researchos.main38-closed-execution-review.v1':{'reviewer':'non-Root identity','decision':'EXACT38_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED','requested_changes':[],'completed_ref':'exact ref','manifest_ref':'exact ref','post_registration_audit_ref':'exact ref'},
   'researchos.cli8-source-integration-controller-review.v1':{'reviewer':'not controller author; Root allowed','decision':'READY_FOR_ROOT_EXACT8_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES','requested_changes':[],'actual_integration_executed':False,'scope_sha256':'final scope SHA','controller_sha256':ref(controller)['sha256']},
   'researchos.cli8-source-integration-grant.v1':{'actor':'codex:/root','actual_registration_completed':True,'status':'ROOT_REGISTERED_EXECUTION_AUTHORIZED','scope_ref':'final scope ref','controller_review_ref':'exact ref','operation_uuid':'fresh32hex','automatic_retry':False,'canonical_copies':'ordered4 canonical_path/ref','registration_refs':'manifest/audit/invocation/intent/verified refs'}},
 'root_scope_work_in_progress_keys':['cli_exact8_source_integration_scope_ref','cli_exact8_source_integration_controller_review_ref'],
 'registration_files':['manifest.json','registration-audit.json','invocation.json','canonical-write.intent.json','canonical-write.verified.json','register.py','run.py','prepared_refs.json','audit.json','stdout.raw','stderr.raw','canonical-write.checkpoint.done.json','canonical-write.path_ownership.done.json'],
 'warning':'These exact future schemas/file conventions are proposed API contracts, not facts about artifacts already written. Root must adopt or return a new immutable controller revision before execution; no fallback to old scope or plan.',
 'grant_read_set':'All immutable authority reads tracked and rechecked at guards. Live canonical4 compared to immutable grant copies; no canonical writes.'})
save('forward-recovery.json',{
 'automatic_retry':False,'automatic_rollback':False,'reset_clean_checkout_restore':False,
 'before_apply_failure':'Save raw, phase, actual nullable exit/Job; stop; no mutation assumed without checking receipts.',
 'after_apply_before_commit_failure':'Preserve exact staged8/current bytes/index/HEAD; do not reset or recreate patch. Root independently inspects and registers a new bounded continuation if needed.',
 'commit_exit_failure_or_timeout':'Do not infer commit absence from exit. Preserve raw and read-only HEAD/index/source observations; no automatic git commit repeat.',
 'HEAD_changed_CP_old':'Expected source-only window. Verify committed sole parent=a5 and complete tree delta8/source blobs, retain current canonical. Root separately registers forward-only cp.head update, never rewinds HEAD.',
 'postcommit_proof_failure':'Leave source/index/canonical facts intact; no success marker; independent diagnosis and exact new lease before any recovery.'})
save('static-audit.json',{
 'AST':'PARSED_ONLY_NOT_IMPORTED','controller_ref':ref(controller),'AST_nodes':sum(1 for _ in ast.walk(syntax)),
 'actual_controller_executed':False,'git_writes':0,'compile_tests_SQL_HTTP_SDK_models':0,
 'main_head':results['final-head'].decode().strip(),'index_empty':results['final-index']==b'',
 'status_rows':len(status),'old_deleted_rows':len(deleted),'canonical_before_after_unchanged':all(x['unchanged'] for x in after),
 'source_delta':8,'shared_with_handler38':sum(x['shared_with_handler38'] for x in exact),'additional_changed_paths':5,'new_file_paths':0,
 'preimages':'All8 a5 before blobs equal b987 parent22752; all8 existing files, no5absence condition.',
 'limits':'Pure static/AST check only; no Windows Job behavioral proof, no source acceptance.',
 'new_failures':[]})
save('tool-diagnostics.json',{'observed_tool_chunks':[{'chunk_id':x,'actual_outer_exit':0} for x in ['6e78e9','933352','b5d295','ccb2a6','e3e2c0','fc15bc','ccc6ff','530ff5','a95321','38034b']],
 'meaning':'References to original tool responses in conversation; not reconstructed stdout. All actual native readonly Git stdout/stderr/argv are separately retained.',
 'candidate_controller_or_helper_execution':0,'new_failure_origins':[]})
invocations=list(N.glob('*.invocation.json'))
save('handoff.json',{
 'status':'PREPARATION_COMPLETE_STOPPED_NOT_AUTHORIZED','author':'codex:/root/command_queue_impl',
 'controller_ref':ref(controller),'scope_ref':ref(N/'scope.proposed.json'),'exact8_ref':ref(N/'exact8.json'),
 'composition_ref':ref(N/'composition-proof.json'),'public_input_plan_ref':ref(N/'protected-public-plan.json'),
 'future_authority_contract_ref':ref(N/'future-authority-contract.json'),'recovery_ref':ref(N/'forward-recovery.json'),
 'static_audit_ref':ref(N/'static-audit.json'),'canonical_before_ref':ref(N/'canonical.before.json'),'canonical_after_ref':ref(N/'canonical.after.json'),
 'actual_readonly_git_invocations':len(invocations),'new_failure_origins':[],
 'blockers':['Main38 actual FF/closed execution/forward registration not yet available; all corresponding refs null.',
             'New Root scope/CAS/once grant/independent controller review absent.',
             'Fresh Main a5 public-vector and status bytes must be frozen by Root immediately before new CLI scope.',
             'Root must implement/adopt the future authority schema and owned outer-launch contract before grant.'],
 'open_product_gates':['Old221 evidence does not qualify current a5+CLI combination.','Fresh43 compile + actual generated/WORK/archive/executable/Windows inputs require a separate future scope.',
                       'Held API/attach completion/P02/fullformal cases remain held unless separately authorized.','Desktop58 and provider/LIVE are outside this operation.'],
 'commit_scope':'Exactly8 source paths; single new commit parent=a5; no receipt commit/wholeCLI tree/FF to b987.',
 'source_acceptance':False,'formal_increment':0})
entries=[ref(p) for p in sorted(N.rglob('*')) if p.is_file()]
save('manifest.json',{'count':len(entries),'entries':entries,'excluded_only':str(N/'manifest.json')})
print(json.dumps({'handoff':ref(N/'handoff.json'),'manifest':ref(N/'manifest.json'),'controller':ref(controller),'scope':ref(N/'scope.proposed.json'),'readonly_git_invocations':len(invocations),'manifest_count':len(entries)},ensure_ascii=False))
