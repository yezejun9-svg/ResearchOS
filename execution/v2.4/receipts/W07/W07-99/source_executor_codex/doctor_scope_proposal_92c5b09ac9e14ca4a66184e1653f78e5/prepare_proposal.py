"""Read-only MAIN inspection; writes only this exclusive proposal directory."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess

OUT=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
WT=OUT.parents[6]
PACKAGE=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
def save(name,data):
    with (OUT/name).open('xb') as stream:stream.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=MAIN).decode('utf-8').strip()
sources=sorted(set(list((MAIN/'apps/cli').glob('*.go'))+[MAIN/x for x in ['apps/cli/build_check.py','tests/runtime/cli_contract/v2verbs.go','tests/runtime/cli_contract/main.go','internal/api/v2.go','internal/api/contracts/client.protocol.schema.json','internal/domain/client_protocol.go','execution/v2.4/receipts/W04/W04-99/executor_codex/evidence_module.py']]))
before=[ref(p) for p in sources]
save('source-before.json',before)
head=git('rev-parse','HEAD')
scope=['apps/cli/main.go','apps/cli/cli_doctor.go','apps/cli/cli_doctor_test.go']
fixture='tests/runtime/cli_contract/v2verbs.go'
schema=read(MAIN/'internal/api/contracts/client.protocol.schema.json')
product=read(PACKAGE/'contracts/product.contract.json')
facts={'schema_ref':ref(MAIN/'internal/api/contracts/client.protocol.schema.json'),
       'definitions':{name:schema['$defs'][name] for name in ['HostStatusResult','ModelConfiguration','CredentialSummary']},
       'frozen_product_ref':ref(PACKAGE/'contracts/product.contract.json'),
       'doctor_contract':[x for x in product['cli']['commands'] if x['id']=='doctor'],
       'exit_codes':product['cli']['exit_codes'],
       'frozen_W05_step_ref':ref(PACKAGE/'tasks/steps/W05-03.md'),
       'frozen_CLI_spec_ref':ref(PACKAGE/'14_CLI_DESKTOP_PRODUCT.md')}
save('contract-facts.json',facts)
evidence=[]
for relative,start,end in [('apps/cli/main.go',51,104),('apps/cli/cli_v2.go',213,285),('apps/cli/cli_verbs.go',189,220),('apps/cli/cli_native.go',110,158),('internal/api/v2.go',65,81),('internal/domain/client_protocol.go',931,962),('tests/runtime/cli_contract/v2verbs.go',166,198),('tests/runtime/cli_contract/v2verbs.go',414,434),('apps/cli/build_check.py',77,88)]:
    p=MAIN/relative;lines=p.read_text(encoding='utf-8').splitlines()
    evidence.append({'source_ref':ref(p),'locator':{'line_start':start,'line_end':end},'text':'\n'.join(lines[start-1:end])})
save('source-observations.json',evidence)
contexts={'W07':MAIN/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-73b0ed13c0cd4138bd44315261ecbb01/context.json',
          'W04_historical':MAIN/'execution/v2.4/receipts/W04/W04-99/integration_codex/current_context_codex.json'}
coverage=[]
for owner,path in contexts.items():
    context=read(path);cov=context['source_coverage'];vector=context['version_vector']
    groups={name:{row['path'] for row in rows} for name,rows in vector.items() if isinstance(rows,list) and all(isinstance(row,dict) and 'path' in row for row in rows)}
    checks=[]
    for candidate in scope+[fixture]:
        checks.append({'path':candidate,'vector_groups':[name for name,paths in groups.items() if candidate in paths],
            'coverage_roots':[row for row in cov['roots'] if candidate.startswith(row['path'].rstrip('/')+'/')],
            'exact_file_match':candidate in cov['exact_files']})
    assert all(not x['vector_groups'] and not x['coverage_roots'] and not x['exact_file_match'] for x in checks)
    coverage.append({'owner':owner,'actual_context_ref':ref(path),'source_coverage':cov,'group_counts':{name:len(rows) for name,rows in groups.items()},'candidate_checks':checks})
state=read(MAIN/'execution/v2.4/step_state.json')
rows=[row for row in state['steps'] if row['id'] in ('W04-99','W07-99')]
save('coverage-intersection.json',{'status':'READ_ONLY_NO_PATH_INTERSECTION','contexts':coverage,'actual_state_ref':ref(MAIN/'execution/v2.4/step_state.json'),'observed_rows':rows,
    'limitations':['This proposal writes receipts only. No product vector changes now.','An eventual CLI build changes the CLI artifact and its own W05 applicability; this is not a claim that all project vectors remain current.','W04 future auxiliary package closure must still be checked after its actual go-list; current six roots/eight inputs exclude CLI.','Registry changes independently invalidate exact W07 applicability; this proposal does not change registry.']})
tests=[
 {'name':'TestW05DoctorDiscoveryAndDownCompatibility','checks':['Missing discovery => NOT_FOUND/REJECTED/exit3; invalid discovery JSON => INVALID_JSON/exit3','Closed loopback host and health503 => health DOWN/REJECTED/exit1; preserve http_code503','stdout exactly one JSON object; stderr contains only sanitized diagnostics; no POST after failed health']},
 {'name':'TestW05DoctorTypedHostStatus','checks':['Actual native CLI process against recording loopback HTTP server sends one GET healthz and exactly one authenticated POST v2/command, method host.status, empty payload','No session/project/writer claim is sent, even with a saved stale session; command/client/reply identity match','Valid CommandResponse + HostStatusResult produces exit0 and allowlisted host/capability/model diagnostic facts; missing model inventory remains explicitly unreported','REJECTED/auth401 => exit3; incomplete/pending status, wrong identity, malformed or schema-invalid result => nonzero, never health-only success']},
 {'name':'TestW05DoctorSecretsAndNoProviderCalls','checks':['Known bearer sentinel and malicious raw health/error bodies never appear in stdout/stderr','Do not echo credential_ref, base_url credentials/query, session token, or arbitrary raw response/error text','Capture all requests; provider.probe/provider.models/host.configure/session.* never called; redirect not followed; no provider external address visited','Credential AVAILABLE, verified_at, supported_methods and health READY never produce provider_usable=true or tool-qualified claims; provider_verification=NOT_CHECKED']},
 {'name':'TestW05DoctorLocalHostIntegration','checks':['Fresh temporary SQLite + real existing API handler/local host supplies real typed host.status to built CLI, local session auth through existing helper','No existing user DB, model profile, protected holdout or external provider read/call; no workspace chooser or configuration mutation','Real service empty model_configurations/credentials reported as NOT_REPORTED_BY_HOST, without asserting systemwide absence']},
 {'name':'TestW05DoctorCredentialBlockAndContextPreservation','checks':['Absent/expired local auth => exit3 without fake UP completion; no token printed','Read config/session fixture bytes unchanged, no new writer epoch/session created, no automatic host launch/bootstrap/configure','Native CLI invocation runs under a path containing Chinese characters/spaces; recorded argv/exit/raw and binary hash retained']}]
locked=read(MAIN/'execution/toolchains/locked.json');go=locked['tools']['go']['path']
proposal={'schema':'researchos.w05.doctor-scope-proposal.v1','status':'READ_ONLY_SCOPE_PROPOSAL_NOT_IMPLEMENTED','actor':'codex:/root/sources_parent_impl','created_at':datetime.now(timezone.utc).isoformat(),'main_head_observed':head,'requested_baseline_head':'cf7ec1ec70cdeea842d878d131773b64ecb61d85',
 'readiness_ref':ref(WT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/w05-readonly-readiness-f84ef28adf1f4f7b8a4c2da664f8d631/audit-summary.json'),
 'exact_product_source_scope':scope,'product_scope_changes':[
 {'path':scope[0],'change':'Replace only doctor switch body with cliDoctor entry call; remove imports made unused by extraction. All other verbs/dispatch unchanged.','purpose':'Connect documented doctor entry to one testable diagnostic path.'},
 {'path':scope[1],'change':'Add local discovery/health compatibility, existing credential retrieval and strict typed host.status read, allowlisted redacted diagnostic rendering and bounded exit mapping.','purpose':'Report actual local host/capability/model observations without provider execution or a second scheduler.'},
 {'path':scope[2],'change':'Add meaningful HTTP/native-process and real local typed-service diagnostic tests, including rejection and secret sentinels.','purpose':'Prove actual wire method, real JSONL/exit behavior and refusal of forged success.'}],
 'required_behavior':[
 'Keep discovery env override, NOT_FOUND and INVALID_JSON exit3, health DOWN exit1/http_code, JSONL and diagnostic stderr separation. Keep safe existing host_pid/version/client_protocol fields; raw probe strings become bounded sanitized state/code summaries.',
 'Only accept a local loopback http/https discovery URL with no userinfo/query/fragment; do not follow redirects or attach bearer to a nonlocal target. Validate before HTTP. Use existing session credential helper or explicit CLI credential; never auto-start host or open chooser.',
 'Use fresh host-level context, empty project/session fields and no writer epoch. Existing newV2Context with empty cliConfig can reuse local session credential without project-bound renewal side effects. Missing/expired credential remains blocked exit3.',
 'Call v2CallContext for strict protocol/command/method identity, then validate CommandResponse and HostStatusResult through cliProtocolDocument. Require COMPLETED and matching result.client_id; nonterminal/malformed/extra-field replies cannot complete doctor.',
 'Output allowlisted host identity/build/state/config revision, advertised protocol/methods, reported model/provider identifiers and credential status counts. Do not forward raw reply, credential references, raw provider URLs, principal data, arbitrary error text or any known bearer substring.',
 'Keep host health, advertised capability, reported configuration, stored historical verified_at and actual provider verification as separate facts. provider_verification=NOT_CHECKED, provider_network_called=false, tool_qualification=NOT_EVALUATED; never infer usable from health/configuration/AVAILABLE.',
 'COMPLETED/exit0 means local diagnostic report obtained, not provider/task acceptance. Empty configuration arrays are reportable with models.status=NOT_REPORTED_BY_HOST and a settings hint, not fabricated global NOT_CONFIGURED. Auth/resource blockers exit3, local/protocol check failures exit1, invalid URL/input exit2. No new status or acceptance store.',
 'No source/domain/API/schema/S6/registry/migration/model route mutation; no credential inventory or secret database reads outside existing authorized host session helper.'],
 'upstream_limit':{'source_refs':[ref(MAIN/'internal/api/v2.go'),ref(MAIN/'internal/domain/client_protocol.go')],'finding':'newV2Service initializes identity/build/mode/revision0/lease only; ModelConfigs/CredentialSumm/WorkspaceBind are unpopulated and host.status returns empty arrays. CLI cannot truthfully infer all local configured model/credential state. Full diagnostics may require a separately owned future host inventory binding; this scope reports the limitation.'},
 'compatibility':{'preserved':['Documented doctor invocation','Missing discovery exit3','Health DOWN exit1 and503 code','Single JSONL stdout','Other CLI commands and accepted domain/S6 behavior'],
 'intentional_correction':'Health UP no longer substitutes a valid authenticated host.status result. Existing malformed host.status fixture will fail; no weakening of typed validation is proposed.',
 'legacy_fixture_gap':{'path':fixture,'response_lines':[192,196],'assertion_lines':[429,431],'actual':'complete fixture omits response.method and returns method_confirmed/session_id/writer_client_id, not HostStatusResult','anticipated_failure':'W0503-DOCTOR-UP-COMPLETES until fixture is corrected','not_executed':True},
 'legacy_build_probe':'apps/cli/build_check.py A7 assumes UP=>0 without explicitly supplying v2 auth; runtime compatibility must be tested with a real available local credential. Do not edit it or suppress a block in this scope.'},
 'separate_minimal_fixture_scope_proposal':{'path':fixture,'authorized_now':False,'change':'In complete/strict successful response branch only, add a host.status-specific valid CommandResponse with method host.status, echoed command/client IDs, HostStatusResult required fields (protocol, READY, config_revision0, empty arrays, advertised methods, operating_mode). Return before generic placeholder response.','unchanged':['All original UP/DOWN/NOT_FOUND assertions and expected exits','unhealthy/rejected/notimplemented/inprogress/malformed branches','Other method handlers and original negative controls'],'purpose':'Bring the existing positive fixture into the frozen protocol while preserving its behavioral assertion strength.'},
 'focused_tests':tests,
 'proposed_commands_not_executed':[
 {'argv':[go,'test','-count=1','-json','./apps/cli','-run','^TestW05Doctor'], 'mode':'FIXTURE','purpose':'All new diagnostic controls and native CLI subcommands'},
 {'argv':[go,'test','-count=1','-json','./apps/cli'],'mode':'FIXTURE','purpose':'Existing CLI regression including local SDK/queue fixtures; no live model claims'},
 {'argv':[go,'build','-o','<exclusive-receipt-run>/researchos-doctor.exe','./apps/cli'],'mode':'BUILD','purpose':'Actual native executable and hash'},
 {'argv':['<exclusive-receipt-run>/researchos-doctor.exe','doctor'],'mode':'FIXTURE','environment_names':['RESEARCHOS_CLI_DISCOVERY','RESEARCHOS_CLI_CONFIG','RESEARCHOS_CLI_CLIENT_ID','RESEARCHOS_CLI_CREDENTIAL (fixture sentinel only)'],'purpose':'Actual argv repeated across isolated loopback healthy/invalid/auth/DOWN fixture scenarios; retain each exit/raw'},
 {'argv':[go,'run','./tests/runtime/cli_contract'],'mode':'FIXTURE_LEGACY','condition':'Only after separate fixture scope approval or explicitly retaining expected old invalid-UP failure; inspect harness writes before use','purpose':'Original exit assertions unchanged; never treat historical pass as current'}],
 'tool_environment':{'locked_ref':ref(MAIN/'execution/toolchains/locked.json'),'go_sha256':locked['tools']['go']['sha256'],'GOROOT':str(Path(go).parents[1]),'GOTOOLCHAIN':'local','GOENV':'off','GOPATH':str(MAIN/'.local/gopath'),'GOCACHE':str(MAIN/'.local/gocache'),'network':'Loopback fixture/local host only; zero provider/model calls'},
 'source_vector_impact_ref':ref(OUT/'coverage-intersection.json'),
 'implementation_readiness':'Three product files sufficient for bounded diagnostic improvement; independent reviewer must also review separate one-file legacy fixture correction before claiming full legacy compatibility. Root registration required before any source implementation.',
 'formal_claims':{'new_acceptances':0,'W05_complete':False,'product_agent_live_coding_demonstrated':False,'P01_U02_A04_claimed':False},
 'excluded':['domain/S6/API/schema','shared registry/canonical/state','provider network/model/probe/fixed route changes','TUI/token streaming','old receipts','private DB/holdout/other project configuration']}
save('proposal.json',proposal)
after=[ref(p) for p in sources];save('source-after.json',after);assert before==after
save('inspection-result.json',{'status':'READ_ONLY_PROPOSAL_COMPLETE','main_head_before':head,'main_head_after':git('rev-parse','HEAD'),'source_before_after_equal':before==after,'source_files_count':len(before),'source_writes':0,'model_calls':0,'tests_executed':0,'source_scope':scope,'proposed_fixture_scope_only':fixture,'proposal_ref':ref(OUT/'proposal.json'),'coverage_ref':ref(OUT/'coverage-intersection.json'),'source_before_ref':ref(OUT/'source-before.json'),'source_after_ref':ref(OUT/'source-after.json')})
print(json.dumps({'proposal':ref(OUT/'proposal.json'),'result':ref(OUT/'inspection-result.json'),'coverage':ref(OUT/'coverage-intersection.json')},ensure_ascii=False))
