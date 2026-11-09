from pathlib import Path
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-peer-auth-seam-20261104')
AUTHOR = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam/author')
scope = json.loads((AUTHOR.parent/'scope.json').read_text(encoding='utf-8-sig'))
lock = json.loads(Path('D:/作品集/ResearchOS/research-os/execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))
git = Path(lock['tools']['git']['path'])
assert hashlib.sha256(git.read_bytes()).hexdigest() == lock['tools']['git']['sha256']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name, obj):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(obj,stream,ensure_ascii=False,indent=2);stream.write('\n')

head = subprocess.run([str(git),'-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').strip()
assert head == scope['base_head']
names = scope['production_paths'] + scope['test_paths']
first = json.loads((AUTHOR/'checks01/results.json').read_text(encoding='utf-8'))
second = json.loads((AUTHOR/'checks02/results.json').read_text(encoding='utf-8'))
assert first['status']=='DEVELOPMENT_CHECKS_FAILED'
assert second['status']=='DEVELOPMENT_CHECKS_PASS'
assert {n:sha(ROOT/n) for n in names} == second['sources_after']
unchanged = scope['production_paths'] + ['internal/host/native_peer_provenance_test.go','internal/domain/client_protocol_auth_context_test.go']
assert all(first['sources_after'][n] == second['sources_after'][n] for n in unchanged)

statistics=[]
for attempt,phase in [('checks01','host-focused'),('checks01','domain-focused'),('checks02','api-focused'),('checks01','compatibility')]:
    path=AUTHOR/attempt/(phase+'.stdout.raw')
    events=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    passed=[e for e in events if e.get('Action')=='pass' and e.get('Test')]
    failed=[e for e in events if e.get('Action')=='fail']
    assert not failed,(attempt,phase,failed)
    tops=[e['Test'] for e in passed if '/' not in e['Test']]
    statistics.append({'attempt':attempt,'phase':phase,'top_level_passed':len(tops),'top_level_tests':tops,
                       'nested_pass_records':len(passed)-len(tops),'total_test_pass_records':len(passed),
                       'stdout_sha256':sha(path)})
assert [x['top_level_passed'] for x in statistics] == [3,4,5,7]
manifest = {'status':'FROZEN_FOR_INDEPENDENT_REVIEW','scope_id':scope['scope_id'],'base_head':head,
            'files':[{'path':n,'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size} for n in names],
            'formal_increment':0,'accepted':False}
save('source-manifest.json',manifest)
save('test-statistics.json',{'status':'FOCUSED_DEVELOPMENT_ONLY','phases':statistics,
                           'new_top_level_tests':12,'legacy_top_level_regressions':7,
                           'counts_are_not_formal_assertions':True})
save('diagnostics.json',{
    'counter_reset':False,'global_counter_written':False,
    'first_test_failure':{'origin':'W14_API_FIXTURE_MISSING_CONFIGURATION_AUTHORITY_V1','attempt_index':1,
       'location':'checks01/api-focused.stdout.raw', 'stdout_sha256':sha(AUTHOR/'checks01/api-focused.stdout.raw'),
       'leaf':'TestCommandAuthHTTPOrdinaryTokenAndErrorPrecedence/ordinary-status',
       'actual':'HTTP200 REJECTED HOST_UNAVAILABLE: host configuration authority unavailable',
       'cause':'Fresh test fixture lacked its existing required configuration metadata port, not an authentication implementation regression.'},
    'directed_fix':{'same_origin':True,'attempt_index':2,'only_source':'internal/api/v2_auth_context_test.go',
       'change':'Provide explicitly synthetic configuration metadata for the ordinary host.status fixture. No production change, assertion relaxation, proof fabrication or old-test edit.',
       'result':'checks02 API focused exit0; production and other new test hashes unchanged.'},
    'other_diagnostics':[
       {'action':'Get-Content internal/host/host_test.go','result':'Absent guessed file; no writes. Actual native_first_use_windows_test.go located/read.'},
       {'action':'rg internal/api/v2_test.go','result':'Absent guessed file; no writes. Actual v2_sessions_test.go located/read.'},
       {'action':'rg internal/domain/remote*.go','result':'Windows literal wildcard os123; actual remote_auth.go located/read.'},
       {'action':'C edit-production.py apply_patch update','result':'Patch verification failed: context incorrectly included literal + prefixes. No file modified by that patch. Directed corrected C patch then succeeded; D edits only executed after all base hashes checked.'},
    ],
    'actual_completed_invocations':[
       {'tool_chunk':'e24e60','action':'edit-production.py','exit_code':0},
       {'tool_chunk':'d7e9e1','action':'install-tests.py','exit_code':0},
       {'tool_chunk':'349e3c/f33bf8','session':56400,'action':'run-checks.py checks01','exit_code':1},
       {'tool_chunk':'42ac89/b93b9f','session':53987,'action':'fix-api-fixture.py then run-checks.py checks02 api-only','exit_code':0},
    ],'uncertain_operations_remaining':[]})
tools=AUTHOR/'controller-snapshot'
tools.mkdir(exist_ok=False)
for p in HERE.iterdir():
    if p.is_file():
        with (tools/(p.name+'.txt')).open('xb') as stream:stream.write(p.read_bytes())
save('author-summary.json',{
    'status':'FROZEN_FOCUSED_DEVELOPMENT_CHECKS_PASS_REQUIRES_INDEPENDENT_REVIEW',
    'scope_id':scope['scope_id'],'checkpoint_at_author_start':593,'worktree':str(ROOT),'base_head':head,
    'source_manifest_sha256':sha(AUTHOR/'source-manifest.json'),'changed_source_files':9,
    'functions':{
       'producer':'verifyNativePeer(pid) -> private Host/generation/OS-peer capability; typed invocation retained to dispatch; legacy boolean has nil peer.',
       'boot_generation':'New uses crypto/rand.Reader; private newHost entropy seam returns before mutable setup on failed/short/zero entropy.',
       'auth':'AuthenticateCommandTx(ctx,tx,token,*ClientService) resolves existing real credential/RBAC/remote checks inside caller command transaction; private context requires same tx/service/principal and contains no raw token or native/client/sameOS claim.'},
    'validation':statistics,'first_failure_preserved':'checks01','directed_followup':'checks02',
    'eight_source_files_identical_after_first_pass':unchanged,
    'ordinary_auth_and_public_schemas_preserved':True,'production_bootstrap_calls_added':0,
    'test_execution':'New API fixtures use httptest.Recorder with fresh SQLite; existing selected API compatibility uses ephemeral loopback fixtures. Injected peer tests open no pipe. No actual native/model/backend/product process or old database was used.',
    'test_fixture_ordinary_credential_issuance':True,
    'actual_native_transport_calls':0,'model_provider_calls':0,'old_database_access':0,
    'writer_grant_changes':0,'native_wire_changes':0,'new_tables_or_migrations':0,'registry_changes':0,
    'formal_increment':0,'accepted':False,'counter_reset':False,
    'limitations':['No durable native client or writer provenance','No command-bound native attestation','No attach ACK/replay/full-settlement/CAS implementation','No active Run pause implementation','Ordinary bearer authentication is not native identity evidence'],
    'model_selection':'Inherited Codex agent assigned by parent; no side CLI/model/native construction session.'})
packet_files=[p for p in AUTHOR.rglob('*') if p.is_file()]
save('packet-manifest.json',{'status':'AUTHOR_PACKET_FROZEN','files':[{'path':str(p.relative_to(AUTHOR)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(packet_files)],'formal_increment':0})
print(json.dumps({'status':'FROZEN_FOR_INDEPENDENT_REVIEW','source_manifest_sha256':sha(AUTHOR/'source-manifest.json'),
                  'author_summary_sha256':sha(AUTHOR/'author-summary.json'),'packet_manifest_sha256':sha(AUTHOR/'packet-manifest.json'),
                  'top_level_tests':19,'new_top_level_tests':12,'test_pass_records':sum(x['total_test_pass_records'] for x in statistics)},ensure_ascii=False))
