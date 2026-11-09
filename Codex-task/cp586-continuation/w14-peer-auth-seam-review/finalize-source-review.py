from pathlib import Path
import datetime,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
CANDIDATE=MAIN/'.local/worktrees/w14-peer-auth-seam-20261104'
RECEIPT=MAIN/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam'
ARCHIVE=RECEIPT/'reviews/independent-qa-01'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
result=json.loads((ARCHIVE/'result.json').read_bytes())
assert result['status']=='PRECONDITION_SEAM_QA_PASSED_NOT_HANDOFF_ACCEPTANCE'
assert all(r['exit_code']==0 and r['source_unchanged'] for r in result['results'])
pins=result['source_sha256']
manifest=RECEIPT/'author/source-manifest.json'
assert sha(manifest)=='2628e7d22108bc481d0efd1a1f40de5f7da82a3b4614cb67b3fef5b79390c6c7'
assert all(sha(CANDIDATE/name)==digest for name,digest in pins.items())
assert len(pins)==9
archive_manifest=ARCHIVE/'archive-manifest.json'
assert sha(archive_manifest)=='f33db8b3006178ceb05a0513abff0f23c2f225b0be06c9237c746663f0f8dab8'
archived=json.loads(archive_manifest.read_bytes())
assert all(sha(ARCHIVE/name)==entry['sha256'] for name,entry in archived['files'].items())
cleanup_path=ARCHIVE/'cache-cleanup-result.json';cleanup=json.loads(cleanup_path.read_bytes())
assert cleanup['status']=='OWNED_BUILD_CACHE_REMOVED_EVIDENCE_AND_MODULE_INPUTS_PRESERVED' and cleanup['target_absent'] and not cleanup['processes_before']
assert not Path(cleanup['target']).exists() and Path(cleanup['module_input_root_preserved']).is_dir()
new=[r for r in result['results'] if r['name'].startswith('new-')]
extra=[r for r in result['results'] if r['name'].startswith('independent-') and r['name']!='independent-vet']
def count(rows):return {'top_level':sum(len(r['top_level_passed']) for r in rows),'subtests':sum(r['subtests_passed'] for r in rows),'actual_test_run_events':sum(r['run_test_count'] for r in rows),'actual_test_pass_events':sum(r['pass_test_count'] for r in rows)}
assert count(new)=={'top_level':12,'subtests':52,'actual_test_run_events':64,'actual_test_pass_events':64}
assert count(extra)=={'top_level':8,'subtests':8,'actual_test_run_events':16,'actual_test_pass_events':16}
assert all(r['run_pass_rosters_equal'] and r['exact_top_level_roster'] and not r['failed'] and not r['skipped'] and r['package_terminal_pass'] for r in new+extra)
diagnostics=json.loads((ARCHIVE/'harness-attempt-01/failure.json').read_bytes())['diagnostics']
author_summary=json.loads((RECEIPT/'author/author-summary.json').read_bytes())
report={
 'schema':'researchos.w14-peer-auth-seam-independent-review.v1',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/implementation_review',
 'static_auth_api_reviewer':'/root/implementation_review/prompt_flow_review',
 'decision':'APPROVE_PRECONDITION_SEAM_ONLY_NOT_HANDOFF_ACCEPTANCE',
 'formal_increment':0,
 'source_integration_approved':True,
 'W14_acceptance':'NOT_PASSED',
 'base_head':'ebc340ef35cfdbf4449642ed559a05e5cdbaaee6',
 'worktree':str(CANDIDATE),
 'scope_sha256':sha(RECEIPT/'scope.json'),
 'source_manifest_sha256':sha(manifest),
 'source_sha256':pins,
 'exact_nine_source_hashes_read_back_after_QA_and_cache_cleanup':True,
 'findings':[],
 'verified_scope':[
  'The production named-pipe path obtains its PID from Windows, resolves the OS identity and compares SameUser before creating a private verifiedNativePeer. It carries only observed OS peer facts, owning Host pointer and private boot generation across the private invocation/dispatch boundary; client_id remains an unproven label.',
  'Public HandleNative(bool) preserves legacy size/trust/shape/kind/reply-validation/undo behavior and always prepares a nil-peer invocation. Boolean success, ordinary bearer/header/frame fields, matching stable InstanceID or another Host object cannot mint/reuse typed peer provenance.',
  'New supplies crypto/rand.Reader to a private constructor; each call reads a nonzero32-byte generation before directory/vault/domain initialization. Failed/short/zero entropy fails closed before filesystem or DB effects. No persistent host identifier substitutes for the generation.',
  'Existing authenticate and AuthenticateToken behavior retains real credential expiry/revocation/principal/RBAC/remote constraints. The new same-Tx entry point returns private credential hash/expiry/principal metadata, no raw token, native/client/sameOS assertion or writer grant.',
  'Opaque metadata requires the exact original sql.Tx pointer, ClientService pointer and principal ID. Real old context cannot replace missing/bad/revoked bearer in another transaction or new HTTP request; same DB/Domain objects do not substitute for the exact service. Authentication does not open/commit replacement transactions or issue credentials.',
  'v2 API authentication, existing Execute authorization and commit share the actual request command transaction. Protocol/body gates precede auth;401 precedes envelope/method400 after a valid protocol peek; authenticated project denial remains403 and execution/commit failures remain500. Existing ClientService principal/RBAC/remote checks remain load-bearing.',
  'Independent Recorder-only tests verify old genuine auth context cannot authenticate a new request, error paths leave command identities unchanged, closed DB/noBearer remains401, and body/protocol gates preserve413/400 priority. Fresh SQLite tests verify revoked/expired credentials, remote owner/device/grant intersection and closed/changed transactions.'
 ],
 'independent_QA':{
  'root':str(ARCHIVE),
  'new_source_fixture_counts':count(new),
  'additional_independent_overlay_counts':count(extra),
  'actual_run_pass_exact_rosters_match':True,
  'failure_or_skip_events':0,
  'commands_and_results':result['results'],
  'raw_archive_manifest_ref':str(archive_manifest),
  'raw_archive_manifest_sha256':sha(archive_manifest),
  'input_ref':str(ARCHIVE/'inputs.json'),
  'overlay_ref':str(ARCHIVE/'overlay-inputs.json'),
  'test_classification':'NO_LISTENER_FRESH_SQLITE_RECORDER_AND_INJECTED_PEER_DEVELOPMENT_FIXTURES',
  'cache_and_module_policy':'Reused only own prior completed binding-review module inputs/build cache; all test executions use -count=1. Inputs/raw/source/results were archived before verified build-cache-only removal.',
  'listener_native_model_provider_starts':0,
  'old_database_access':0
 },
 'independent_vet':{'exit_code':0,'ref':str(ARCHIVE/'independent-vet.result.json'),'sha256':sha(ARCHIVE/'independent-vet.result.json'),'command_ref':str(ARCHIVE/'independent-vet.command.json'),'stdout_ref':str(ARCHIVE/'independent-vet.stdout.txt'),'stderr_ref':str(ARCHIVE/'independent-vet.stderr.txt'),'packages':['internal/host','internal/domain','internal/api']},
 'candidate_git_guard':archived['git_readback'],
 'author_evidence':{
  'packet_manifest_sha256':sha(RECEIPT/'author/packet-manifest.json'),
  'summary_sha256':sha(RECEIPT/'author/author-summary.json'),
  'final_selected_counts':{'top_level':19,'nested':58,'test_pass_events':77},
  'classification':'New12 fixtures plus7 retained legacy compatibility cases. Selected old compatibility includes DEVELOPMENT_HTTP_FIXTURE ephemeral loopback, not Native/LIVE/product or provider qualification. It was not rerun by this stricter no-listener QA.',
  'checks01_API_fixture_failure':'PRESERVED; ordinary-status lacked injected ConfigurationAuthority, corrected only in the new API test using explicit SYNTHETIC metadata. Eight other sources stayed identical. No old failure was upgraded to PASS.',
  'followup_attempt':'checks02 API fixture only',
  'summary_validation':author_summary['validation']
 },
 'cache_cleanup':{'ref':str(cleanup_path),'sha256':sha(cleanup_path),'before_inventory_ref':str(ARCHIVE/'cache-cleanup-before.json'),'result':cleanup,'qualification':'Capacity is a recorded point-in-time fact. Root must recheck its own resource preflight; no model scope was started by this reviewer.'},
 'limits':[
  'This is a prerequisite provenance/authentication seam, not durable native client/writer proof or a handoff implementation. No command-bound native attestation, client-to-credential binding, ACK/replay/full settlement/CAS, active Run pause or writer/lease-expiry bypass is implemented.',
  'The peer tests inject synthetic OS identities and open no real pipe. Actual Windows DACL/PID transport behavior is source-reviewed here, not LIVE-qualified.',
  'Opaque credential facts are transaction-scoped authentication snapshots, not independent active-transaction/current-authority/lease/native proofs. They do not bypass existing Execute, RBAC, remote or later native authorization gates.',
  'No native wire method, public schema/table/migration, registry, old runtime scope, provider/model/renderer credential exposure or SDK output change is admitted.',
  'W14 remains NOT_PASSED. No formal22-parent/42-case, business Goal or product completion is established.'
 ],
 'diagnostics':diagnostics,
 'operations':{'frozen_source_writes':0,'old_database_connections':0,'listener_starts':0,'native_model_provider_starts':0,'control_registry_or_failure_counter_writes':0,'counter_reset':False,'formal_increment':0},
 'evidence_chunks':['ba893d','9fa6c5','6c499e','69264b','7f7b16','93963a','74b034','6420ac','d88fbf','fd6130','81d28f','20b429','271df6']
}
shutil.copyfile(Path(__file__),ARCHIVE/'review-finalizer.py.txt')
shutil.copyfile(ROOT/'cleanup-owned-cache.ps1',ARCHIVE/'cache-cleanup-controller.ps1.txt')
data=(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
c=ROOT/'source-review.json';d=RECEIPT/'reviews/source-review.json'
for target in (c,d):
 with target.open('xb') as stream:stream.write(data)
print(json.dumps({'C':str(c),'D':str(d),'sha256':sha(d),'decision':report['decision'],'independent_vet_exit_code':0,'free_after_report_bytes':shutil.disk_usage(ROOT).free},ensure_ascii=False))
