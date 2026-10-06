"""Read-only inputs; write this review's own dated snapshot, never qualify a proof."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
REPO = next(p for p in OUT.parents if (p / 'execution/project_identity.json').is_file())
SPEC = REPO.parent / 'ResearchOS_Implementation_Package_v2.4'
PREFIX = 'execution/v2.4/receipts/W07/W07-99/'
OLD = PREFIX + 'source_executor_codex/run-8017e0f7e4384703b223c3dbc542a057/'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def ref(path):
    return {'path': str(path), 'sha256': sha(path)}

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def fields(**kwargs):
    return kwargs

started = datetime.now(timezone.utc).isoformat()
inputs = [REPO / x for x in ['AGENTS.md', 'execution/v2.4/formal_profile_w07.py',
    'execution/v2.4/formal_case_index.py', 'execution/v2.4/formal_profile_w07_test.py',
    'execution/v2.4/step_state.json', 'execution/v2.4/parent_gate_ledger.json',
    'execution/v2.4/current_spec.json', 'execution/commands.json', 'execution/v2.4/commands.json',
    'execution/toolchains/locked.json', 'execution/command_dispatcher/dispatch.py',
    'execution/v2.4/parent_gate_ledger.py', 'ops/ci/sources.py', 'tests/sources/check/main.py']]
inputs += [SPEC / x for x in ['contracts/execution.plan.json','contracts/tasks.json',
    'contracts/acceptance.json','contracts/harness.contract.json','PACKAGE_MANIFEST.json',
    'tasks/steps/W07-99.md','tools/task_packet.py']]
before = [ref(p) for p in inputs]
state = read(REPO / 'execution/v2.4/step_state.json')
plan = read(SPEC / 'contracts/execution.plan.json')
step = next(x for x in plan['steps'] if x['id'] == 'W07-99')
rows = {x['id']: x for x in state['steps']}
selected = {k: rows[k] for k in [*step['dependencies'], 'W07-99']}
evidence = []
for key, row in selected.items():
    for r in row.get('evidence', []):
        p = REPO / 'execution/v2.4' / r['path']
        actual = sha(p) if p.is_file() else None
        evidence.append({'owner':key, 'ref':r, 'actual_sha256':actual, 'matches':actual == r['sha256']})
old_proof = read(REPO / OLD / 'proof.json')
old_map = read(REPO / OLD / 'source-before.json')
drift = []
for name, expected in old_map.items():
    p = REPO / name
    actual = sha(p) if p.is_file() else None
    if actual != expected.removeprefix('sha256:'):
        drift.append({'path':name, 'captured_sha256':expected, 'current_sha256':actual})
locked = read(REPO / 'execution/toolchains/locked.json')['tools']
toolchecks = {name:{**locked[name], 'actual_sha256':sha(Path(locked[name]['path']))} for name in ['python','go','browser_act']}
registries = {}
for name, key in [('execution/commands.json','test.sources.fixture'),('execution/v2.4/commands.json','test.sources.live')]:
    registries[key] = {'registry_ref':ref(REPO/name), 'entry':read(REPO/name)['commands'][key]}
proc = subprocess.run([locked['git']['path'], 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True)
(OUT/'git-head.stdout').write_bytes(proc.stdout)
(OUT/'git-head.stderr').write_bytes(proc.stderr)
git_result = {'argv':[locked['git']['path'],'rev-parse','HEAD'], 'cwd':str(REPO), 'exit_code':proc.returncode,
              'stdout_ref':ref(OUT/'git-head.stdout'), 'stderr_ref':ref(OUT/'git-head.stderr')}
module = ast.parse((REPO/'execution/v2.4/formal_profile_w07.py').read_text(encoding='utf-8'))
symbols = {n.name:{'start':n.lineno,'end':n.end_lineno} for n in module.body if isinstance(n, ast.FunctionDef)}
frozen = {}
for relative in ['contracts/acceptance.json','contracts/tasks.json','contracts/execution.plan.json','contracts/harness.contract.json','tasks/steps/W07-99.md','PACKAGE_MANIFEST.json']:
    p = REPO / 'execution/v2.4/receipts/W04/W04-99/executor_codex/frozen_inputs/package' / relative
    frozen[relative] = {'external':ref(SPEC/relative),'repository_copy':ref(p) if p.is_file() else None,
                        'same_bytes':p.is_file() and sha(p)==sha(SPEC/relative)}

mapping = {
 'schema':'researchos.w07.preflight-field-map.v1','actor':'codex:/root/queue_upgrade_impl','formal_acceptances':0,
 'reference_rules':{'general':{'path':'repository-relative forward slash; no traversal/drive', 'sha256':'bare lowercase SHA256, 64 hex'},
   'w07_proof_raw':'W07 PREFIX only; source proof may use sha256: prefix, preserve exact refs where equality required',
   'owner_evidence':'path relative to execution/v2.4, bare SHA256; unique root schema context/review/issuance',
   'raw_locator':'json_pointer (RFC6901, empty pointer allowed), or 1-based inclusive line_start/line_end; nonempty located value'},
 'context':fields(schema='researchos.w07.current-context.v1',task_id='W07',step_id='W07-99',
   executor_id='fresh proof.executor_id / actual executor',run_id='fresh proof.run_id',created_at='actual final context time >= proof.ended_at',
   acceptance_baseline_ref='repository copy frozen acceptance.json',version_vector='formal_vector below',source_coverage='coverage below',
   proof_ref='fresh LIVE_SERVICE proof',compilation_invocation_ref='fresh go-list.invocation.json; stdout_ref == proof.compilation_inputs_ref',
   execution_report_ref='fresh report.json; product_proof_ref same identity as context.proof_ref',
   registered_commands='four objects {id, receipt_ref}; id W07-G01/W07-G02/W07-H07/A05; receipt_ref byte copy of native receipt under W07',
   global_evidence_refs='ordered object keys run_receipt,version_manifest,command_receipt,assertion_results; four different W07 files'),
 'formal_vector':fields(schema='researchos.w07.version-vector.v1',package_version='2.4.0',
   spec_files='nonempty hashrefs including six frozen files in frozen_baselines',
   source_files='nonempty complete applicable code refs; MINIMUM_SOURCE is only a lower bound; source_before complete compilation closure must match pinned current hashes',
   input_files='nonempty refs; both registries included among vector groups, plus applicable contracts/migrations/assets',
   lock_files='nonempty refs; execution/toolchains/locked.json pinned; go.mod/go.sum from capture pinned',
   tool_files='nonempty tool-identity JSON refs, not direct binary refs',
   environment='exact object {os,arch,timezone}; actual nonempty strings; equals GLOBAL run',
   components='exact model/adapter/rubric/policy; model+rubric {status:not_applicable,reason}; adapter+policy {status:applicable,version,refs}; refs already pinned in vector'),
 'tool_identity':fields(schema='researchos.w07.tool-identity.v1',locked_ref='current canonical lock; also pinned in vector',
   tools='unique rows {name,version,path,sha256}; go/python/browser_act mandatory; path and version_output/hash match lock and current actual executable'),
 'coverage':fields(roots='nonempty [{path:relative directory, patterns:[fnmatchcase relative patterns]}]; walk rejects symlink/junction subdirectories',
   exact_files='list of exact repository-relative files; may be empty',paths_sha256='formal_case_index.object_sha256(sorted(observed paths))',
   invariant='union roots matches + exact_files exactly equals source_files paths'),
 'global_run':fields(schema='researchos.w07.run-receipt.v1',case_id='A05',run_id='context.run_id',environment_mode='LIVE_SERVICE',
   os='vector.environment.os',arch='vector.environment.arch',timezone='vector.environment.timezone',started_at='proof.started_at',ended_at='proof.ended_at',
   executor_id='context.executor_id',verifier_id='actual independent review.reviewer_id'),
 'global_version':fields(schema='researchos.w07.version-manifest.v1',case_id='A05',run_id='context.run_id',package_version='2.4.0',
   package_manifest_ref='same exact hashref present in vector.spec_files; frozen hash',code_revision='execution report.execution_head actual 40hex',
   dirty='JSON boolean bool(execution report.dirty_before)',version_vector_ref='W07 formal vector JSON == context.version_vector',product_version_vector_ref='exact proof.version_vector_ref'),
 'global_command':fields(schema='researchos.w07.command-receipt.v1',case_id='A05',run_id='context.run_id',registered_commands='exact context.registered_commands',
   source_invocations='exact proof.source_invocations',h07_invocations='exact proof.h07_invocations',build_invocation_ref='exact proof.build_invocation_ref'),
 'global_assertions':fields(schema='researchos.w07.assertion-results.v1',case_id='A05',run_id='context.run_id',
   assertions='five rows {id,expected,actual,status,raw_evidence_refs,refusal_evidence_refs,command_keys}; id A05-01..05; first five fields exact proof row; refusal refs nonempty actual negative locator refs; command_keys [test.sources.live]'),
 'independent_review':fields(schema='researchos.w07.independent-review.v1',task_id='W07',step_id='W07-99',run_id='context.run_id',executor_id='context.executor_id',
   reviewer_id='actual independent actor; casefold differs from executor and codex:/root',context_ref='final context hashref',proof_ref='exact context.proof_ref',
   acceptance_baseline_ref='exact context.acceptance_baseline_ref',evidence_index_ref='exact context_ref',decision='ACCEPTED only after actual full independent review',
   missing='[] only if no missing items',failed='[] only if no failed items',version_vector='exact context.version_vector',issued_at='actual review time >= context.created_at',
   assertion_verdicts='five {id,status:PASS,actual:meaningful,raw_evidence_refs:nonempty}; exact A05-01..05',
   gate_verdicts='three same-shape verdicts; exact W07-G01/W07-G02/W07-H07',supersedes_review_refs='absent or []'),
 'received_message':fields(schema='researchos.root-received-independent-message.v1',recorded_by='codex:/root',recipient='codex:/root',sender='actual review.reviewer_id',
   event_type='actual MESSAGE or FINAL_ANSWER',review_ref='exact issuance.review_ref',received_at='actual received time >= review.issued_at',
   content='actual delivered message text containing full review sha256 and full proof sha256'),
 'root_issuance':fields(schema='researchos.w07.root-observed-issuance.v1',task_id='W07',step_id='W07-99',run_id='context.run_id',actor='codex:/root',
   executor_id='context.executor_id',reviewer_id='review.reviewer_id',context_ref='final context hashref',review_ref='actual independent review hashref',
   delivery_ref='actual Root-received-message hashref',observed_at='actual observation time >= message.received_at'),
 'owner_transition':{'entry':'Root serialized canonical step_state.json update; no accept command exists in task_packet.py',
   'status_order':'IN_PROGRESS -> optional EXECUTION_REPORTED -> ACCEPTED only after real independent review and Root observation',
   'actor_fields':['executor_id','verifier_id'],'accepted_at':'actual time >= issuance.observed_at','evidence':'preserve historical refs; register exactly one context/review/issuance root; CAS state before write',
   'postcheck':'task_packet show; derive_formal_cases/formal_case_index and recheck_inputs; Root regenerates parent_gate_ledger separately'},
 'frozen_baselines':frozen,'code_symbol_locations':symbols,
 'fresh_product_constraints':{'modes':'3 actual sources LIVE_SERVICE; H07 INJECTED; G01 FIXTURE separate',
   'source_kinds':['GITHUB','PAPER','X'],'h07_ids':['not_configured','429','401_or_revoked','timeout','empty_valid_result','visible_empty','index_only','pr_open','pr_closed_unmerged','pr_merged','cycle_partial','effect_confirmed','effect_unresolved'],
   'inventory_argv_tail':['list','-deps','-json','./tests/sources/live'],
   'h07_argv_tail':['test','-count=1','-json','-run','^TestW07','./adapters/sources','./internal/domain','./tests/sources/live'],
   'build_argv_tail':['build','-o','actual captured binary absolute path','./tests/sources/live'],
   'dependency_closure':'real unique ImportPath/Dir mapping; complete local imports+Deps, all current non-test Go parsed; all current package Go hash covered; literal go:embed contents covered; wildcard/directory/all: patterns unqualified fail closed',
   'h07_events':'all three packages real start/run/pass lifecycle, uncached, bounded Time, no skips/fail, required production tests and public ingress forgery rejection'},
 'forbidden_shortcuts':['old8017 as current','shape unit tests as acceptance','executor writes own independent review','Root as executor and observer','synthetic ACCEPTED owner','rewritten native receipt or source capture','receipt-selected Python or SQL','partial source vector','zero assertions or skipped tests']}
write('field_map.json',mapping)
after = [ref(p) for p in inputs]
result = {'schema':'researchos.w07.readonly-preflight-snapshot.v1','actor':'codex:/root/queue_upgrade_impl','started_at':started,
 'ended_at':datetime.now(timezone.utc).isoformat(),'formal_acceptances':0,'live_invocations':0,'qualification_runs':0,
 'head':proc.stdout.decode('utf-8').strip(),'git_command':git_result,'inputs_before':before,'inputs_after':after,'input_drift':before!=after,
 'canonical_rows':selected,'plan_step':step,'registered_evidence_hash_checks':evidence,'registries':registries,'actual_tools':toolchecks,
 'old_proof_shape_sample':{'proof_ref':ref(REPO/OLD/'proof.json'),'executor_id':old_proof['executor_id'],'run_id':old_proof['run_id'],
    'captured_paths':len(old_map),'drifted_paths':drift,'currentness_claim':'NONE; read-only comparison only, never product qualification'},
 'frozen_baselines':frozen,'outputs':{'README.md':ref(OUT/'README.md'),'field_map.json':ref(OUT/'field_map.json'),'snapshot.py':ref(Path(__file__))}}
write('snapshot.json',result)
print(json.dumps({'status':'READONLY_PREFLIGHT_COMPLETE','formal_acceptances':0,'input_drift':before!=after,
 'head':result['head'],'owner_status':rows['W07-99']['status'],'old_proof_drift_count':len(drift),
 'evidence_hash_mismatches':sum(not x['matches'] for x in evidence),'snapshot_sha256':sha(OUT/'snapshot.json')},ensure_ascii=False))
sys.exit(1 if before!=after or proc.returncode else 0)
