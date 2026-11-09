import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,x):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
checks=json.loads((N/'checks.json').read_bytes())
assert checks['all_pass'] and checks['count']==153
for v in json.loads((N/'input-pins.json').read_bytes()):assert pin(Path(v['path']))==v,v['path']
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal.json','seal.original-tool-io.json','postseal.original-tool-io.json')]
save('MF.json',{'schema':'researchos.independent-review-manifest.v1','members':members,'member_count':len(members)})
save('HDF.json',{'schema':'researchos.independent-gqb-source-review.v1','status':'SOURCE_ACCEPTED_FOR_ROOT_INERT_REQUEST_GENERATION','report_ref':pin(N/'report.md'),'manifest_ref':pin(N/'MF.json'),'checks_ref':pin(N/'checks.json'),'inputs_ref':pin(N/'input-pins.json'),'guard_ref':pin(N/'guard.final.json'),'candidate_source_ref':{'path':str(N.parent.parent/'native_grant_archive_request_builder_source_codex/gqb-1a11ee4f162766098eda3028b0679f2/root_build_grant_archive_request.py'),'sha256':'sha256:732694a07b89813c39e794e21f7edb1bc3ee7a335a0d8a0b8cf1c503fcd002cc','bytes':24509},'check_count':153,'input_count':25,'actual_main_compose_writer_helper':False,'actual_native_Go_SQL_API_private_model':False,'request_archive_created':False,'canonical_unchanged':True,'mechanical_failure_ordinals':[918,920],'parent_next_last_observed':921,'Root_only_actual_and_canonical':True,'full_20_to24_realOwner_nineCases_formal42':'OPEN','STOP_FINAL':True})
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json')}))

