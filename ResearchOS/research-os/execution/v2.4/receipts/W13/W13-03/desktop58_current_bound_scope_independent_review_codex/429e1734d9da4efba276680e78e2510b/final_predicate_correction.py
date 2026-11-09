from pathlib import Path
import json,hashlib
O=Path(__file__).parent;a=json.loads((O/'final-checks.json').read_bytes());old=a['failed']
rows=[x for x in a['frozen_git_raw_facts'] if Path(x['ref']['path']).name=='index-after.stdout.raw']
ok=len(rows)==1 and rows[0]['bytes']==0 and rows[0]['ref']['sha256']==hashlib.sha256(b'').hexdigest()
d={'schema':'researchos.static-predicate-correction.v1','original_audit_preserved':True,'original_tool_exit':0,'original_failed_predicate':old,'explanation':'Precommit index is expected nonempty after exact15 apply. Final empty-index evidence must select index-after.stdout.raw, not all names containing index. No product/candidate failure occurred.','corrected_predicate':'Exactly one frozen index-after.stdout.raw with zero bytes and SHA256(empty).','passed':ok,'exact_evidence_refs':[x['ref'] for x in rows],'other_final_checks_passed':all(x['passed'] for x in a['checks'] if x['check']!='source closure sealed empty-index raw exists'),'new_failure_origin_count':0}
with (O/'final-predicate-correction.json').open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'corrected_final_index':ok,'other_final_checks_passed':d['other_final_checks_passed'],'new_failure_origins':0}))
