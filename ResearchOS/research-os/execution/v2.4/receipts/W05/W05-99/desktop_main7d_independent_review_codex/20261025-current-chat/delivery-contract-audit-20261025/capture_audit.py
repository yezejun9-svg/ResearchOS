import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
E = Path(__file__).resolve().parent
S = R / '.local/worktrees/v24-continuation/spec/v2.4'

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name, obj): (E/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

paths = [R/'AGENTS.md', R/'execution/v2.4/current_spec.json', R/'execution/v2.4/checkpoint.json', R/'execution/v2.4/step_state.json', R/'execution/v2.4/path_ownership.json', R/'execution/v2.4/commands.json', R/'execution/commands.json', R/'execution/command_dispatcher/dispatch.py', R/'docs/installation/desktop-development.md', R/'apps/desktop/launch-development.mjs']
paths += [S/name for name in ['PACKAGE_MANIFEST.json','08_AGENT_EXECUTION_GOAL.md','14_CLI_DESKTOP_PRODUCT.md','17_USER_JOURNEYS_AND_VALUE.md','19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md','12_IMPLEMENTATION_AND_HANDOFF.md','contracts/product.contract.json','contracts/delivery.contract.json','contracts/tasks.json','contracts/acceptance.json','contracts/execution.plan.json','tasks/steps/W13-01.md','tasks/steps/W13-02.md','tasks/steps/W13-03.md','tasks/steps/W13-99.md','tasks/steps/W20-01.md','tasks/steps/W20-02.md','tasks/steps/W20-99.md']]
paths += [E.parent/name for name in ['complete-tree/R3-INDEPENDENT-REVIEW.md','complete-tree/R3-REVIEW-SEAL.json','native-proof/NATIVE-PROOF-REVIEW.md','native-proof/NATIVE-PROOF-REVIEW-SEAL.json','main-integration-post/POST-REVIEW.md','main-integration-post/POST-SEAL.json']]
(E/'inputs').mkdir(exist_ok=False)
refs=[]
for i,p in enumerate(paths,1):
    b=p.read_bytes(); target=E/'inputs'/f'{i:03}-{p.name}'; target.write_bytes(b)
    refs.append(dict(source=str(p),copy=target.relative_to(E).as_posix(),sha256=sha(b),bytes=len(b)))
write('CAPTURED-INPUTS.json',dict(captured_at=dt.datetime.now(dt.timezone.utc).isoformat(),refs=refs))
pointer=read(R/'execution/v2.4/current_spec.json')
assert sha((S/'PACKAGE_MANIFEST.json').read_bytes()) == pointer['manifest_sha256']
assert sha((S/'contracts/execution.plan.json').read_bytes()) == pointer['plan_sha256']
tasks=read(S/'contracts/tasks.json'); cases=read(S/'contracts/acceptance.json'); state=read(R/'execution/v2.4/step_state.json')
keys=['desktop.shell_launch','desktop.installer_build','cli.entry_run','cli.entry_build','release.reproduce','acceptance.audit','test.ui.routes','test.ui.visual']
v24=read(R/'execution/v2.4/commands.json'); legacy=read(R/'execution/commands.json')
registry={}
for key in keys:
    selected = 'v2.4' if key in v24['commands'] else 'v2.0'
    registry[key]=dict(selected_registry=selected,entry=(v24 if selected=='v2.4' else legacy)['commands'].get(key))
ids=['W13-01','W13-02','W13-03','W13-99','W17-03','W18-02','W20-01','W20-02','W20-99']
rows={x['id']:x for x in state['steps']}
selected_state={k: rows.get(k,{'id':k,'status':'ROW_ABSENT_NOT_ASSUMED_ACCEPTED'}) for k in ids}
git=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,check=True)
write('CURRENT-CONTRACT-AND-REGISTRY.json',dict(main_head=git.stdout.decode().strip(),checkpoint_revision=read(R/'execution/v2.4/checkpoint.json')['revision'],ownership_revision=read(R/'execution/v2.4/path_ownership.json')['revision'],spec_pointer=pointer,manifest_plan_hashes_verified=True,registry=registry,task_contracts=[x for x in tasks['tasks'] if x['task_id'] in ['W13','W20']],acceptance_cases=[x for x in cases['cases'] if x['id'] in ['A15','C23']],step_state=selected_state,formal_increment=0))
write('DIAGNOSTICS.json',dict(product_tests_run=0,native_runs=0,original_business_data_reads=0,formal_increment=0,read_diagnostics=[dict(issue='Initial guessed spec/current_spec.json and spec/live absent',resolution='Actual execution/v2.4/current_spec.json read, pointer snapshot validated'),dict(issue='Broad rg output exceeded output budget',resolution='Exact JSON task/case selection and copied inputs used'),dict(issue='PowerShell LiteralPath wildcard launch* rejected by rg',resolution='Actual git-listed launch-development.mjs read directly')],source_mutations=False,shared_state_mutations=False,scope='READONLY_CONTRACT_AUDIT_NOT_FORMAL_ACCEPTANCE'))
print(json.dumps(dict(refs=len(refs),main_head=git.stdout.decode().strip(),output=str(E)),ensure_ascii=False))
