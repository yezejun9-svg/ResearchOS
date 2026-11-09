"""Independent static registration review: bytes/AST only, no registrar/helper/product import."""
from pathlib import Path
import ast
import hashlib
import json

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
N=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/closure-and-finite-continuation-r309'
PINS={
 'register.v2.py':'44d7d5263f895e272935d456c4db5cae63f9767d4d12958257c2472a2ad3f9a6',
 'run.v2.py':'04e50fc26a615e10edb4bd876cb5d0219f3e4985e8951e2ee9ea7944dc9df7fa',
 'prepared_refs.v2.json':'d29812c297b583af9a4ec05ecf19641578503cbc082c806b971258fad53ad480',
 'audit.v2.json':'84cb2d7c43021b05ebb4b59e3ef908cb474887fa6d2e05edc62af8bcfb424ae3',
 'list_replay.v2.py':'a714295db60586264dd7afdb302b48dfaa18791fd49b66e85455824783c014ad',
 'list_independent_scope.v2.json':'8619aec61da6b0785f54849714e3574ecb3d37389145b7eacb75de2dfb761f93',
 'cli_continuation_scope.v2.json':'29ffca39b944aeebaac5055905cb286516c673b0d807ba210c12dca2a016b083',
}

def rawref(path):
    data=path.read_bytes()
    return data,{'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
def ref(path):return rawref(path)[1]
def read(path):return json.loads(path.read_bytes())
def save(name,obj):
    with (HERE/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return ref(HERE/name)

sources=[]
for name,expected in PINS.items():
    raw,entry=rawref(N/name)
    if entry['sha256']!=expected:raise RuntimeError('INPUT_SHA_MISMATCH:'+name)
    if name.endswith('.py'):ast.parse(raw)
    dst=HERE/('input-'+name)
    with dst.open('xb') as f:f.write(raw)
    sources.append({'original':entry,'copy':ref(dst)})
prepared=read(N/'prepared_refs.v2.json')
checks=[]
for pin in prepared['verified_refs']:
    path=Path(pin['path']);path=path if path.is_absolute() else ROOT/path
    actual=ref(path)
    same=actual['sha256']==pin['sha256'] and actual['bytes']==pin['bytes']
    checks.append({'expected':pin,'actual':actual,'same':same})
    if not same:raise RuntimeError('REFERENCED_INPUT_MISMATCH:'+pin['path'])
save('all76refs.actual.json',checks)
canonical=[]
copies=[]
for pin in prepared['canonical_before']:
    raw,actual=rawref(ROOT/pin['path'])
    if actual!=pin:raise RuntimeError('CANONICAL_CHANGED:'+pin['path'])
    target=HERE/('before-'+Path(pin['path']).name)
    with target.open('xb') as f:f.write(raw)
    canonical.append(actual);copies.append(ref(target))
cp=read(ROOT/'execution/v2.4/checkpoint.json')
ow=read(ROOT/'execution/v2.4/path_ownership.json')
if [cp['revision'],ow['revision'],len(cp['failure_counters'])]!=[308,136,371]:raise RuntimeError('STATE_TUPLE')
oldkeys={x.get('origin_key') for x in cp['failure_counters']}
origins=prepared['origins']
if len(origins)!=8 or len({x['origin_key'] for x in origins})!=8 or any(x['origin_key'] in oldkeys for x in origins):raise RuntimeError('ORIGIN_DUPLICATION')
if any(x['actual_outer_exit']!=1 or x['product_test_failures']!=0 for x in origins):raise RuntimeError('ORIGIN_CLASSIFICATION')
save('origins.actual.json',{'origins':origins,'current_prefix_count':371,'new_count':8,'expected_after':379,'zero_outer_not_counted':True,'not_eight_product_test_failures':True})

old_scope=read(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/list_independent_scope.json')
test_path=Path(old_scope['checkout'])/'internal/api/v2_sessions_test.go'
test_raw,test_ref=rawref(test_path)
if test_ref['sha256']!='e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0':raise RuntimeError('LIST_TEST_SOURCE_CHANGED')
with (HERE/'input-v2_sessions_test.go').open('xb') as f:f.write(test_raw)
names=['NullContext','OwnedContext','ContextNotResultFilter','ExactReplayAfterCommit','ChangedPayloadConflict','ChangedSIDConflict','CrossProjectContext','ForeignPrincipalContext','ForeignPrincipalNullList','UnknownContext','ProjectGrantDenied','CrossProjectCursor','CrossPrincipalCursor','MalformedRequest']
scope=read(N/'list_independent_scope.v2.json')
if scope['ordered_cases']!=names:raise RuntimeError('LIST_CASE_SCOPE_DRIFT')
text=test_raw.decode('utf-8')
if any('"'+name+'"' not in text for name in names):raise RuntimeError('LIST_CASE_SOURCE_MISSING')
save('list14.static.json',{'source':test_ref,'copy':ref(HERE/'input-v2_sessions_test.go'),
 'ordered_cases':names,'case_assertions_static_read':{
 'identity':'OwnedContext different client with same principal; null/non-null context echoed; context must not filter returned sessions.',
 'authorization':'Cross-project/unknown rejected NOT_FOUND; foreign principal nonnull FORBIDDEN; foreign principal null list contains no private items; project grant denied403.',
 'replay':'Exact same command preserves response bytes and all table state; changed payload/SID ContentHash differs then409 COMMAND_ID_CONFLICT, no second journal.',
 'cursor_and_schema':'Actual generated cursor rejects crossproject/crossprincipal; malformed unknown field400 short response; typed full schema kept for other cases.',
 'tables':'Actual before/after mutations bounded by native sessionListDelta. Closed schema/column/typedmultisets independently compared by planned controller; implicit rowid limitation explicit.',
 'no_assertion_changes':'Candidate source2 SHA pinned, protected original suffix hash checked by driver; controller only selects original14 and verifies native reached assertions/raw.'},
 'executed':False,'public_HTTP_limit':224,'percase_limit':16,'source_acceptance':False})

save('source_analysis.json',{
 'registrar':{
 'four_pins_before_write':True,'per_replace_four_expected_live_checks':True,
 'per_replace_HEAD_status_checks':True,'expected_live_UPDATED_after_each_replace':True,
 'before_desired_intent_temp_exclusive_files':True,'persistent_done_exception_verified_journal':True,
 'READS_own_metadata_cache_updated':True,'no_rollback_or_automatic_rerun':True,
 'ST_CM_left_untouched':True,'old371_prefix_exact':True,'formal_status_equal_guard':True,
 'G2_release_is_only_writer_release_no29_run_grant':True,'Desktop_no_execution_lease':True,
 'recovery_boundary':'Manual forward-only under own exact original/desired + unchanged four metadata/HEAD/status. No recovery executed or implied automated handler.'},
 'wrapper':{
 'review_actor_schema_decision_requested_changes_guard':True,'four_current_bytes_equal_review_copies_before_child':True,
 'register_wrapper_prepared_audit_SHA_bound':True,'actualPython_Git_binary_SHA_bound':True,
 'no_optimize_and_child_I':True,'single_register_child_no_retry':True},
 'list_controller_v2':{
 'pyc_included':'runtime_paths now hashes __file__ and existing __cached__, actual loaded OS DLLs via pinned helper.',
 'lazy_URI_preloaded':'Pure Path.as_uri called before input freeze, no URL open.',
 'owned_process':'Finally stores actual nullable exit/error/raw facts; positive requires resumed, Job assignment before resume, primary exit, Job idle, all handles closed/errors empty.',
 'environment':'Public allowlist; GOAMD64/GOEXPERIMENT/GODEBUG/buildvcs/Git replace/env explicitly controlled; no inherited private credential values.',
 'finite_execute':'Fresh source/export/compiler cache/WORK/exe;14 exact selectors and <=224loopback calls, before/native-after/fixture-after runtime and fullinput checks.',
 'own_output':'Existing OUT/EXPORT refused before owns_output latch; failure handler only writes if created by this invocation.',
 'resources':'Only5 pinned public JEV implementation files alongside approved prefixes; no generator/test execution or private holdout resource.'},
 'CLI_continuation':'v4 tracks current Root grant raw hash/bytes/path in full per-case input vector.44/145 preserved, old first3/76 retained; this review approves registering scope only, not accepting own preparation as product proof.',
 'resolved_prior_static_findings':['list Python __cached__ omission','CLI new Root scope absent from input vector','list run wrapper exceptions omitted per-invocation receipt','list inherited environment incomplete provenance'],
 'no_new_actual_failure':True,'no_register_helper_list_CLI_import_or_execution':True,
 'source_read_tool_traces':['fda9dc','6f11c4','4bc432','639fe9','f5ad8f','dbd899','424c60']})

review={
 'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],
 'actual_registration_executed':False,'expected_before':[308,136,371],'expected_after':[309,137,379],
 'register_sha256':PINS['register.v2.py'],'wrapper_sha256':PINS['run.v2.py'],
 'prepared_refs_sha256':PINS['prepared_refs.v2.json'],'audit_sha256':PINS['audit.v2.json'],
 'canonical_before':canonical,'copied_canonical_before_refs':copies,
 'all_referenced_inputs_verified':ref(HERE/'all76refs.actual.json'),
 'source_analysis':ref(HERE/'source_analysis.json'),'list14_static':ref(HERE/'list14.static.json'),
 'origins':ref(HERE/'origins.actual.json'),'source_copies':sources,
 'scope_of_decision':'Root registration only. Does not execute or accept CLI44/list14/source/Main/parent/formal; all future outcomes remain unproved.',
 'independence':'Reviewer did not author Root registrar/list product or native list tests. CLI controller authorship disclosed; only registration binding/constraints reviewed here, not self-signing CLI product acceptance.',
 'future_state_guard':'Any referenced bytes/canonical/HEAD/status change requires Root wrapper to fail before execution; no acceptance of stale scope.',
 'new_failure_origins':[]}
save('review.json',review)
entries=[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file()]
save('manifest.json',{'schema':'researchos.independent-readonly-review-manifest.v1','entries':entries,'count':len(entries),'self_and_handoff_excluded':True})
save('handoff.json',{'decision':review['decision'],'review':ref(HERE/'review.json'),'manifest':ref(HERE/'manifest.json'),
 'register_sha256':review['register_sha256'],'wrapper_sha256':review['wrapper_sha256'],
 'actual_registration_executed':False,'product_tests':0,'formal_increment':0,'new_failure_origins':[]})
print(json.dumps({n:ref(HERE/n) for n in ('review.json','manifest.json','handoff.json')},ensure_ascii=False))
