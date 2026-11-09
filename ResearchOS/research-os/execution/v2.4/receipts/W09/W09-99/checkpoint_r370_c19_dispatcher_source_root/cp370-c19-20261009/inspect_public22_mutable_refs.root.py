"""Finite Source inspection: report old current Canon refs in runtime closure."""
from pathlib import Path
import json,ntpath
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
items=[('caller_review_members',B/'public22_root_caller_registration_independent_review_codex/review-v4-01a1210b/MF.json','members'),
       ('leaf_source_inputs',B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v2/source-inputs.json','references'),
       ('leaf_review_members',B/'public22_runner_independent_source_review_codex/pub22r-20261009-02/MF.json','members')]
canon={ntpath.normcase(str(R/'execution/v2.4'/(n+'.json'))) for n in ('checkpoint','path_ownership','step_state','commands')}
out=[]
for label,path,key in items:
    refs=json.loads(path.read_bytes())[key]
    found=[r for r in refs if ntpath.normcase(r['path'].replace('/','\\')) in canon]
    out.append(dict(label=label,current_canonical_refs=found))
print(json.dumps(out,ensure_ascii=False),flush=True)
