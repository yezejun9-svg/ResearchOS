import datetime, hashlib, json
from pathlib import Path
E=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes()
    return {'path':str(p.relative_to(E)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
seal_captures=[]; incomplete=[]
for d in (E/'command-captures').iterdir():
    if 'seal-final-review' in d.name: seal_captures.append(d); continue
    if not (d/'before.json').is_file() or not (d/'after.json').is_file(): incomplete.append(str(d))
assert not incomplete, incomplete
required=['review.md','review.json','classified-author-nonzero.json','diagnostic-audit.json']
review=json.loads((E/'review.json').read_text(encoding='utf-8'))
assert review['verdict']=='NEEDS_CHANGES' and review['formal_increment']==0
entries=[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json' and not any(p.is_relative_to(d) for d in seal_captures)]
manifest={'schema':'researchos.owned-core-stop-source-r2-independent-review-evidence.v1','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':review['candidate'],'tree':review['tree'],'verdict':'NEEDS_CHANGES','root':str(E),'required_outputs':[ref(E/n) for n in required],'file_count':len(entries),'files':entries,'self_exclusions':['evidence-manifest.json'],'sealing_logger_exclusions':[str(p.relative_to(E)) for p in seal_captures],'sealing_logger_exclusion_reason':'The final seal logger writes stdout/after after this manifest is created; its pre-execution recipe and terminal raw/exit remain alongside this manifest and are separately verifiable. No earlier command/fixture evidence is excluded.','completed_earlier_captures_all_have_before_after':True,'source_write_authority_used':False,'formal_increment':0,'formal_total':'0/42','all_22_open':True,'actual_authority':False}
(E/'evidence-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'file_count':len(entries),'hashes':{n:ref(E/n)['sha256'] for n in required+['evidence-manifest.json']},'sealed':True},ensure_ascii=False))
