import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
R=Path('D:/作品集/ResearchOS/research-os'); E=Path(__file__).resolve().parent
S=R/'.local/worktrees/v24-continuation/spec/v2.4'
paths=[R/x for x in ['apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/host.js','apps/desktop/main/lib/http-wire.js','apps/desktop/main/lib/native.js','apps/desktop/package.json','apps/desktop/build-development.py','apps/cli/main.go','apps/cli/cli_contract.go','apps/cli/cli_native.go','apps/control/main.go','apps/control/discovery.go','internal/host/desktop_management_windows.go','internal/host/runtime_verifier_process_windows.go','internal/domain/runtime_drain_windows.go','ops/supervisor/release_host/main.go','ops/supervisor/release_host/control_windows.go']]
paths += [S/x for x in ['19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md','14_CLI_DESKTOP_PRODUCT.md','contracts/product.contract.json']]
paths += [E.parent/'delivery-contract-audit-20261025'/x for x in ['DELIVERY-CONTRACT-AUDIT.md','AUDIT-SEAL.json']]
(E/'inputs').mkdir(exist_ok=False)
refs=[]
for i,p in enumerate(paths,1):
 b=p.read_bytes(); f=E/'inputs'/f'{i:03}-{p.name}';f.write_bytes(b)
 refs.append(dict(source=str(p),copy=f.relative_to(E).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
heads={}
for name,root in [('main',R),('candidate',R/'.local/worktrees/desktop-installed-delivery-20261025')]:
 proc=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,check=True)
 heads[name]=proc.stdout.decode().strip()
result=dict(captured_at=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,refs=refs,source_edits=0,native_runs=0,tests_run=0,original_data_reads=0,formal_increment=0)
(E/'DESIGN-INPUTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(refs=len(refs),heads=heads),ensure_ascii=False))
