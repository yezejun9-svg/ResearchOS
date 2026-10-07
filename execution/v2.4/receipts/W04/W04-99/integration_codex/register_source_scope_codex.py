"""Register only the independently reviewed W04 current rule/context slice."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
CARD=HERE.parent
V24=ROOT/'execution/v2.4'
SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

assert len(sys.argv)==2
architecture_path=CARD/'independent_architecture_codex.json'
assert sha(architecture_path)==sys.argv[1]
architecture=load(architecture_path)
assert architecture['reviewer']=='codex:/root/w1702_review'
assert architecture['verdict']=='SUPPORTED_MINIMAL_DESIGN_PENDING_ROOT_SCOPE_IMPLEMENTATION_AND_INDEPENDENT_ACCEPTANCE'
assert architecture['implementation_accepted'] is False and architecture['formal_case_count_delta']==0
for p,digest in {**architecture['source_hashes'],**architecture['contract_hashes']}.items():
    assert sha(ROOT/p)==digest,p
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head=='04217f8a0b6fdb7ec06a392b6273664104c291b3'
cp_path,state_path,path_path=(V24/n for n in ['checkpoint.json','step_state.json','path_ownership.json'])
cp,state,paths=(load(p) for p in [cp_path,state_path,path_path])
assert cp['revision']==213 and len(cp['failure_counters'])==73 and paths['revision']==48
assert next(r for r in state['steps'] if r['id']=='W04-99')['status']=='IN_PROGRESS'
old_failures=copy.deepcopy(cp['failure_counters']);state_bytes=state_path.read_bytes()
existing=['internal/domain/operations.go','internal/domain/import.go','internal/domain/store.go','internal/domain/domain_test.go','internal/domain/context_test.go']
new=['internal/domain/project_rules_v24.go','internal/domain/w04_current_context_test.go','tests/context/parent/w0499_test.go']
root_assets=['internal/domain/contracts/new-project-rules-v24.md','internal/domain/contracts/new-project-rules-v24.json']
assert all((ROOT/p).is_file() for p in existing)
assert all(not (ROOT/p).exists() for p in new+root_assets)
raw_rules=SPEC/'15_NEW_PROJECT_WORKFLOW.md';manifest=SPEC/'PACKAGE_MANIFEST.json'
assert sha(raw_rules)=='b81a28161c9115f3290a9e61e0460d22a516e168071965efd9692a0d45dc2497'
assert len(raw_rules.read_bytes())==12952 and '规则版本：1.1；纳入实施包2.4.0。' in raw_rules.read_text(encoding='utf-8')
assert sha(manifest)=='4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
entry=next(f for f in load(manifest)['files'] if f['path']==raw_rules.name)
assert entry['size_bytes']==12952 and entry['sha256']==sha(raw_rules)
now=dt.datetime.now(dt.timezone.utc).isoformat()
scope_path=HERE/'source_scope_codex.json'
scope={'schema':'researchos.reviewed-current-source-scope.v1','step_id':'W04-99','status':'REGISTERED_BEFORE_PRODUCTION_EDITS',
    'registered_at':now,'integrator':'codex:/root','executor':'codex:/root/w1102_impl','main_source_head':head,
    'candidate_worktree':'.local/worktrees/codex-w0299','candidate_branch':'work/codex-w0499','candidate_initial_head':'58781d7d63a3a0ba057554912d0896b6134e6f95',
    'independent_architecture':ref(architecture_path),'existing_allowed_paths':{p:sha(ROOT/p) for p in existing},'new_allowed_worker_paths':new,'root_only_assets':root_assets,
    'frozen_rules':{'source':ref(raw_rules),'manifest':ref(manifest),'rules_version':'1.1','package_version':'2.4.0','size_bytes':12952},
    'source_observation':'New project creation currently leaves source_document_refs empty, while ImportSpecification already seals package files. Existing recursive context/materialization can carry an exact per-project rule Artifact without a second rule store.',
    'manifest_metadata_compatibility':{'source_manifest':ref(manifest),'added_frozen_metadata_fields':['harness_capability_ids','supersedes','short_goal','change_summary','product_capability_ids','adoption_capability_ids','source_package_revision','execution_plan','execution_step_count','construction_model','built_at','scope_notice','delivery_revision','construction_host','updated_at'],
        'meaning':'Read-only fields actually present in the pinned v2.4 package but absent from the current legacy manifest allowlist; adding only these metadata names grants no authority and preserves unknown-field refusal.'},
    'implementation_constraints':[
        'Use private trusted NewCurrentMu policy only, no new client field, route, environment switch or schema state. Legacy New and existing projects keep historical contents.',
        'In existing createProject transaction after original profile/state and successful grant insertion, seal byte-exact built-in workflow rules as same-project Artifact; append immutable Ref, bump+put Profile, synchronize existing State.profile_revision, bump+put State, then return updated Profile. All writes roll back together on failure.',
        'NewCurrentMu may validate embedded fixed assets at construction; store.go changes restricted to that trusted constructor only.',
        'ImportSpecification keeps complete pinned manifest/path/hash/authority validation before transaction. Reuse existing same-project workflow rule Artifact only on exact source filename, bytes/hash/size match; merge references precisely and preserve original inventory/byPath semantics.',
        'Permit only the exact added frozen manifest metadata names listed above. They never grant authority or mutate acceptance; reject fake authorization/history approval or arbitrary unknown fields, and preserve package product_test_status NOT_RUN.',
        'Do not change global serverArtifact de-duplication or context/materialize/runtime behavior. Existing original-byte visibility/hash/revision checks remain mandatory.',
        'Refactor fixture creation/C03/C04 scenario factory minimally to add trusted current entries. Original legacy test entries preserve default semantics and full original assertions; do not relabel old THIN_CORE evidence as current.',
        'Add actual current REST and bootstrap rule sealing, import facts/authority negatives, two-project inventory/fresh-session rule materialization, required-context three independent missing branches and optional-recall coverage checks in one new test file.',
        'Use exactly tests/context/parent/w0499_test.go as an external-package actual Scanner/Authority/host protocol fixture to avoid the existing local_workspace→domain import cycle; no new production interface or synthetic scanner substitution.',
        'H01 missing RunPolicy reference is an actual required contract component; separate rule Artifact bytes absence and caller authorization revocation use independent fresh fixtures and preserve before/after effect counts. No C01/C02 final-owner acceptance inferred.',
        'Preserve failures and per-attempt actual argv/cwd/environment names/exit/raw. After fixing changed source/input, enroll new current source before verification; no unchanged failed retry.'
    ],
    'owned_cases':{'C03':['C03-01','C03-02','C03-03'],'C04':['C04-01','C04-02','C04-03'],'A01':['A01-01','A01-02','A01-03','A01-04']},
    'mode':'FIXTURE','formal_case_count_delta':0,'independent_acceptance_required':True,
    'protected_sha256':{p:sha(ROOT/p) for p in ['execution/v2.4/commands.json','execution/commands.json','execution/toolchains/locked.json','execution/command_dispatcher/dispatch.py',
        'bootstrap/v24_checkpoint.py','internal/domain/context.go','internal/domain/materialize.go','internal/domain/changes.go','internal/domain/project_bootstrap.go',
        'internal/domain/contracts/persistence-v24.schema.json','internal/domain/contracts/evaluation-v24.schema.json','spec/v2.0/contracts/domain.schema.json','spec/v2.0/contracts/openapi.json']}}
save(scope_path,scope)
binding=paths['card_path_bindings']['W04-99']
binding['paths'].extend(existing+new)
binding['root_only_paths'].extend(root_assets)
binding['source_scope']=ref(scope_path)
binding['rationale']='Independently reviewed minimum current workflow rule sealing/import compatibility and current formal context scenarios; shared registries and byte-exact assets remain root-owned.'
paths.update(revision=49,amended_at=now,amended_by='codex:/root',updated_at=now,updated_by='codex:/root')
replace(path_path,paths)
cp.update(head=head,updated_at=now,updated_by='codex:/root',
    work_in_progress={'step_id':'W04-99','owner':binding['owner'],'status':'REGISTERED_CURRENT_RULE_CONTEXT_SOURCE_SLICE','worktree':binding['worktree'],
        'next_action':'Root copies exact embedded rule assets; executor implements registered current creation/import and meaningful current fixture scenarios; independent formal validator remains separate.'},
    note='W04 exact source slice registered after independent architecture review, before production changes.38 accepted rows,parent4/22,formal0/42,73 original failures unchanged. Root-only frozen rule assets and independent verifier preserved.')
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W04_EXACT_CURRENT_RULE_CONTEXT_SOURCE_SCOPE_REGISTERED','evidence':ref(scope_path)})
cp['evidence_index'].append(scope_path.relative_to(ROOT).as_posix())
replace(cp_path,cp)
event=HERE/'source_scope_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W04-current-rules-source-scope-20261006','delta':'INFRASTRUCTURE',
    'summary':'Register independently reviewed current project rule/context source paths and exact immutable assets before edits; no formal case acceptance.',
    'evidence_refs':[ref(scope_path),ref(architecture_path),ref(raw_rules),ref(manifest)]})
argv=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),
    '--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','213','--round-event',str(event),'--actor','codex:/root']
result=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'checkpoint214.stdout.txt').write_bytes(result.stdout);(HERE/'checkpoint214.stderr.txt').write_bytes(result.stderr)
assert result.returncode==0,result.stderr.decode('utf-8','replace')
after=load(cp_path)
assert after['revision']==214 and after['failure_counters']==old_failures and state_path.read_bytes()==state_bytes
print(json.dumps({'status':'PASS_W04_SOURCE_SCOPE_REGISTERED','checkpoint':214,'path_revision':49,'failure_origins':73,'worker_paths':len(existing+new)}))
