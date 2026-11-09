"""Pure public context validation in a fresh Python; never serves or signs."""
import json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
if '--reviewer-imports' in sys.argv:
    import subprocess
    subprocess.run(['git','--version'],capture_output=True,check=True)
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-02/controller.public.config.json'
config=json.loads(P.read_bytes());source=config['ControllerSource']
m=types.ModuleType('readiness_pure_context');m.__file__=source['path']
exec(compile(Path(source['path']).read_bytes(),source['path'],'exec'),m.__dict__)
pin=m.public_ref(P)
assert pin['sha256']=='sha256:021ee123c2b05facd7fca0c4e945792eb75271cad720c1a4dcb81c458d2fa0e6'
for label,k in [('guard','SourceReadGuard'),('observed','ObservedOwnedHelper')]:m.load_public_module(config[k],label)
helper=m.load_public_module(config['OriginalOwnedHelper'],'original')
frozen={m.path_key(v['path']) for v in config['FrozenInputs']}
loaded=list(helper.runtime_resource_paths())
missing=[p for p in loaded if m.path_key(p) not in frozen]
result={'schema':'researchos.native25-fresh-context-probe/1','reviewer_imports':'--reviewer-imports' in sys.argv,'missing_runtime_paths':missing,'loaded_runtime_paths':loaded,'config_ref':pin,'serve_called':False,'signing_called':False}
try:
    c=m.context(pin)
    result.update(context_result='PASS',case=c['hc']['Case'])
except BaseException as e:
    result.update(context_result='FAIL',error_type=type(e).__name__,error=str(e))
print(json.dumps(result,ensure_ascii=True))
raise SystemExit(result['context_result']!='PASS')
