from pathlib import Path
import json,hashlib
R=Path(r'D:\\作品集\\ResearchOS\\research-os');B=Path(__file__).parent
r=json.loads((B/'continuation-cp528/RESUME.current.json').read_bytes())
for k in ['qualification_failure_revision03_design_ref','boot_supplement_design_ref','recovery_boundary_decision_ref','C_lease_F01_independent_ref']:
 x=r[k];p=Path(x['path']);p=p if p.is_absolute()else R/p;v=json.loads(p.read_bytes());assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 print('INPUT',k,x,'KEYS',list(v))
 fs=v.get('files',v.get('artifacts',{}));print('FILES',json.dumps(fs,ensure_ascii=False))
p=R/'execution/v2.4/receipts/W05/W05-99/qualification_failure_revision03_architecture_codex/20261015-current-chat/C-lease-exact-scope.json'
print('LEASE_SCOPE',p.read_text(encoding='utf-8-sig'))
