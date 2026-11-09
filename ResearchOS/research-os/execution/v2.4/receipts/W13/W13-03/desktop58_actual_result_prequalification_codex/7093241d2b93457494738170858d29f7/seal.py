import json,hashlib
from pathlib import Path
O=Path(__file__).parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
save('handoff.json',{'schema':'researchos.readonly-prequalification-handoff.v1','actor':'codex:/root/w05_merge_review','decision':'ACTUAL_RESULT_REVIEW_PRECONDITIONS_MAPPED_FINAL_RESULT_PENDING','report_ref':pin(O/'report.json'),'matrix_ref':pin(O/'acceptance-matrix.json'),'actual_metadata_audit_exit':0,'new_failure_origins':[],'qualification_issued':False,'inflight_outputs_read':False,'next_required':'Root actual terminal plus sealed aggregate manifest and immutable E/L closure refs; no rerun.','status':'STOPPED_AWAITING_CLOSED_EXECUTION_REFS'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':rows,'count':len(rows),'self_excluded':True})
print(json.dumps({n:pin(O/n) for n in ['report.json','acceptance-matrix.json','handoff.json','manifest.json']},ensure_ascii=False))
