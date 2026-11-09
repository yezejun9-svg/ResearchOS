from pathlib import Path
import datetime as dt,hashlib,json,sys
P=Path(__file__).resolve().parents[1]/'ResearchOS_Implementation_Package_v2.4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if '--namespace' in sys.argv:
    paths=['route','component_lock','patch_inventory','client_mapping','local_inventory','reuse_decisions']
    targets=list(P.glob('[0-1][0-9]_*.md'))+[P/'contracts/tasks.json']
    for p in targets:
        if p.name.startswith(('17_','18_','19_')):continue
        s=p.read_text(encoding='utf8')
        for n in paths:s=s.replace('execution/'+n+'.json','execution/v2.4/'+n+'.json')
        p.write_text(s,encoding='utf8')
    # The original root dispatcher remains the code entry, versioned registry is the selected input.
    p=P/'contracts/execution.plan.json';plan=json.loads(p.read_text(encoding='utf8'))
    s=json.dumps(plan,ensure_ascii=False,indent=2).replace('execution/commands.json','execution/v2.4/commands.json')
    p.write_text(s+'\n',encoding='utf8')
    state=P/'examples/step_state.template.json';obj=json.loads(state.read_text(encoding='utf8'));obj['plan_sha256']=sha(p);put(state,obj)
    for name in ['checkpoint.template.json','step_receipt.template.json']:
        f=P/'examples'/name;obj=json.loads(f.read_text(encoding='utf8'))
        if 'plan_sha256' in obj:obj['plan_sha256']=sha(p)
        if 'input' in obj:obj['input']['plan_sha256']=sha(p)
        put(f,obj)
manifest=json.loads((P/'PACKAGE_MANIFEST.json').read_text(encoding='utf8'))
manifest.update(package_version='2.4.0',specification_date='2026-10-01',status='READY_FOR_IMPLEMENTATION',
                product_implementation_status='V24_NOT_STARTED_EXISTING_CODE_PRESERVED',product_test_status='NOT_RUN',
                execution_plan='contracts/execution.plan.json',execution_step_count=71,construction_model='Qwen3.8-Flash',
                built_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                scope_notice='Specification package and authoring-tool checks only; existing product repository was not modified.')
manifest['files']=[{'path':f.relative_to(P).as_posix(),'size_bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(P.rglob('*'))
                   if f.is_file() and f.name not in {'PACKAGE_MANIFEST.json','PACKAGE_VALIDATION.json'} and '__pycache__' not in f.parts]
put(P/'PACKAGE_MANIFEST.json',manifest)
(P.parent/'ResearchOS_Agent_Goal_v2.4.md').write_bytes((P/'08_AGENT_EXECUTION_GOAL.md').read_bytes())
print('Manifest files:',len(manifest['files']),'sha256:',sha(P/'PACKAGE_MANIFEST.json'))
