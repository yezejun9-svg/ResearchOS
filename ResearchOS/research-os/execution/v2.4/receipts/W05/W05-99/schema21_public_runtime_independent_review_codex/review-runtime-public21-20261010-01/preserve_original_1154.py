from pathlib import Path
import json,types,ntpath
D=Path(__file__).resolve().parent;W=Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99')
p=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py';s=types.ModuleType('review_support');s.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),s.__dict__);s.D=D
captured=s.capture('b3f665',1,1,1154)
report=json.loads((D/'runtime-resource-review.result.json').read_bytes());manifest=json.loads(Path(report['runtime_manifest_ref']['path']).read_bytes())
missing=report['checks'][-1]['evidence']['missing'];pairs=[]
for ref in missing:
 pairs.append({'historical_programme_member_ref':ref,'prepared_current_resource_ref':[r for r in manifest['resource_refs'] if ntpath.normcase(ntpath.normpath(r['path']))==ntpath.normcase(ntpath.normpath(ref['path']))]})
result=s.write('original-1154.diagnosis.json',dict(schema='researchos.public21-runtime-review-original-diagnosis.v1',original_ordinal=1154,original_host=captured,original_report_ref=s.pin(D/'runtime-resource-review.result.json'),original_guard_ref=s.pin(D/'runtime-resources.guard.closed.json'),missing_actual_pairs=pairs,original_outcome_unchanged=True,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(original_host=captured,diagnosis_ref=result,missing_actual_pairs=pairs),ensure_ascii=False))
