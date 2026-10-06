from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,fnmatch
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
P=ROOT/'execution/v2.4/receipts/W07/W07-99/source_executor_codex/doctor_scope_proposal_92c5b09ac9e14ca4a66184e1653f78e5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(n,v):
 with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def require(v,s):
 if not v:raise ValueError(s)
require(sha(P/'proposal.json')=='28d878c97caf0cc0a0cd33e182e189bb5591ac146f2a5bf2912c1878cd5db31b','proposal')
proposal=read(P/'proposal.json');coverage=read(P/'coverage-intersection.json');sources=read(P/'source-before.json')
require(sources==read(P/'source-after.json'),'proposal drift')
source_checks=[]
for r in sources:
 p=Path(r['path']); require(sha(p)==r['sha256'],'current source drift '+str(p));source_checks.append(ref(p))
scope=proposal['exact_product_source_scope']+[proposal['separate_minimal_fixture_scope_proposal']['path']]
require(scope==['apps/cli/main.go','apps/cli/cli_doctor.go','apps/cli/cli_doctor_test.go','tests/runtime/cli_contract/v2verbs.go'],'exact four')
intersections=[]
for record in coverage['contexts']:
 cp=Path(record['actual_context_ref']['path']);require(sha(cp)==record['actual_context_ref']['sha256'],'context digest')
 c=read(cp);v=c['version_vector'];covered=c['source_coverage'];matches=[]
 for path in scope:
  groups=[g for g,rows in v.items() if isinstance(rows,list) and any(isinstance(row,dict) and row.get('path')==path for row in rows)]
  roots=[r['path'] for r in covered['roots'] if path.startswith(r['path'].rstrip('/')+'/') and any(fnmatch.fnmatch(Path(path).name,p) for p in r['patterns'])]
  exact=path in covered['exact_files'];require(not groups and not roots and not exact,'coverage intersection '+path)
  matches.append({'path':path,'groups':groups,'roots':roots,'exact_file':exact})
 intersections.append({'owner':record['owner'],'context_ref':ref(cp),'computed_intersections':matches})
schema=read(ROOT/'internal/api/contracts/client.protocol.schema.json')
facts={name:schema['$defs'][name] for name in ('HostStatusResult','CommandResponse')}
fixture=(ROOT/scope[3]).read_text(encoding='utf-8');start=fixture.index('\tnf := call(');end=fixture.index('\n\tv := call(',start)
protected=fixture[start:end]
save('audit.json',{'schema':'researchos.w05.independent-doctor-scope-audit.v1','at':datetime.now(timezone.utc).isoformat(),'proposal_ref':ref(P/'proposal.json'),'inspection_ref':ref(P/'inspection-result.json'),'coverage_ref':ref(P/'coverage-intersection.json'),'current_source_checks':source_checks,'independent_coverage':intersections,'schema_ref':ref(ROOT/'internal/api/contracts/client.protocol.schema.json'),'host_status_required_fields':facts['HostStatusResult']['required'],'host_status_additionalProperties':facts['HostStatusResult'].get('additionalProperties'),'legacy_doctor_assertions_exact_text':protected,'legacy_doctor_assertions_utf8_sha256':hashlib.sha256(protected.encode()).hexdigest(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'product_tests_executed':0,'source_writes':0})
save('scope_review.json',{'schema':'researchos.w05.independent-doctor-source-scope-review.v1','reviewer_id':'codex:/root/w05_merge_review','issued_at':datetime.now(timezone.utc).isoformat(),'decision':'SOURCE_SCOPE_READY','proposal_ref':ref(P/'proposal.json'),'audit_ref':ref(OUT/'audit.json'),'exact_source_paths':scope,'bounds':{
 scope[0]:'Only replace doctor switch body with cliDoctor and remove imports made unused. Other verbs unchanged.',
 scope[1]:'One read-only diagnostic path: discovery and bounded local health request, existing local credential retrieval, strict typed authenticated host.status, allowlisted sanitized rendering and exit mapping. No domain/API/session/config/model mutations.',
 scope[2]:'Five proposed focused test groups plus necessary native built-CLI/real local typed-service controls, isolated temporary state, secret sentinels, no provider calls.',
 scope[3]:'Only add a host.status-specific valid CommandResponse/HostStatusResult within the successful complete/strict branch, before generic placeholder. Echo actual command/client IDs and method. Keep all prior assertions and exit expectations byte-identical; retain unhealthy/rejected/notimplemented/inprogress/malformed branches and other method handlers.'},
 'mandatory_behavior':[
 'Discovery absent/invalid JSON remains exit3 with NOT_FOUND/INVALID_JSON. Connection failure/health DOWN remains exit1; HTTP503 retained in http_code. Invalid local URL/input exit2. stdout exactly one JSON record; sanitized diagnostics only on stderr.',
 'Health requests must not reuse hostGet without overriding redirect behavior: existing hostGet follows redirects. Implement bounded no-redirect local health request in cli_doctor.go; validate local loopback URL before any credential or HTTP use, reject userinfo/query/fragment and remote targets.',
 'Build fresh host-level context with empty cliConfig and no project/session/writer args. Reuse only explicit CLI bearer or existing session credential helper; no cliInitCredential renewal branch, host launch, chooser, writer claim or persistent config write.',
 'Use v2CallContext strict protocol/command_id/method checks, then frozen CommandResponse and HostStatusResult schema checks and echoed client_id equality. Require COMPLETED; ACKNOWLEDGED/IN_PROGRESS/malformed/extra-field/identity-substitution replies cannot complete doctor.',
 'Map missing/expired credential and actual authorization/resource blocks to exit3. Protocol/transport/check failure exit1. A healthy endpoint with HTTP503 on command is a failed check, not evidence of successful auth. Do not reuse transport helper exit3 for every non-2xx blindly.',
 'Host health UP and READY, supported_methods, model IDs, AVAILABLE credential status or historical verified_at cannot establish provider usability. Emit provider_verification=NOT_CHECKED, provider_network_called=false and tool_qualification=NOT_EVALUATED.',
 'Current API leaves ModelConfigs/CredentialSumm/WorkspaceBind unpopulated. Empty arrays mean NOT_REPORTED_BY_HOST (or equivalent explicit host-unreported diagnostic), never machine-wide NOT_CONFIGURED/no credentials. Do not invent model inventory or read private stores to fill it.',
 'Allowlist bounded identifiers/counts and explicit diagnostic codes only. Do not serialize raw reply/error/probe text, credential_ref, principal data, raw provider URL or bearer. Redact known credential from every retained string, including discovery/detail/path fields; malformed inputs may themselves contain a sentinel.',
 'Exit0 means local diagnostic report obtained. Preserve all original UP0/DOWN1/NOTFOUND3/discovery override assertions. No W05/A04/provider/agent task success inference.'
 ],'test_completion_gates':proposal['focused_tests'],'additional_test_requirements':['Run focused TestW05Doctor tests, complete apps/cli regression, native built executable with recorded binary hash/argv/raw/exits, and original cli_contract harness under an exclusive receipt namespace. Inspect harness fixed output paths before running; retain every original failure.','Verify HTTP503/DOWN, absent discovery, malformed health/status, 401/expired credential, wrong method/command/client, nonterminal reply, redirect and remote URL refusals, secret sentinels, saved session unchanged, real fresh local API/SQLite empty inventory.','Do not edit apps/cli/build_check.py A7; verify actual local credential availability or retain a real block instead of weakening its assertions.'],
 'applicability':{'W04_current_recorded_source_vector_intersection':False,'W07_current_recorded_source_vector_intersection':False,'basis':'Independent exact vector and coverage checks against actual bound contexts; not a blanket future exemption.','W05_own_applicability_changes':True,'future_W04_compiled_closure_must_be_rechecked':True,'registry_or_shared_validator_edits_in_scope':False},'failed':[],'missing':[],'source_changes':0,'canonical_registry_changes':0,'formal_acceptance_delta':0,'implementation_started_by_reviewer':False})
print(json.dumps({'decision':'SOURCE_SCOPE_READY','review':ref(OUT/'scope_review.json'),'audit':ref(OUT/'audit.json')},ensure_ascii=False))
