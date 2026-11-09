from pathlib import Path
import json
R=Path(r'D:\\作品集\\ResearchOS\\research-os');B=Path(__file__).parent
r=json.loads((B/'continuation-cp526/RESUME.current.json').read_text(encoding='utf-8-sig'))
for k in ['C_design_adopted_constraints_ref','boot_supplement_root_decision_ref','boot_supplement_design_ref','qualification_failure_revision03_design_ref','source41_ready_map_draft_ref']:
 x=r[k];p=Path(x['path']);p=p if p.is_absolute()else R/p
 print('INPUT',k,x)
 if k=='source41_ready_map_draft_ref':
  v=json.loads(p.read_text(encoding='utf-8-sig'));print('DRAFT_KEYS',list(v));print(json.dumps(v,ensure_ascii=False))
 elif k in ['C_design_adopted_constraints_ref','boot_supplement_root_decision_ref']:
  print(p.read_text(encoding='utf-8-sig'))
