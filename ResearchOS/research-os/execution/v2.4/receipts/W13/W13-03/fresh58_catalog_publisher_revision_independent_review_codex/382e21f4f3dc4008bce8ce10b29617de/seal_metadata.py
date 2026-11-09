"""Pure owned review metadata sealing; no publisher/gate import or execution."""
from pathlib import Path
import json,hashlib
BASE=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_catalog_publisher_revision_independent_review_codex/382e21f4f3dc4008bce8ce10b29617de')
def pin(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,value):
    with (BASE/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(BASE/name)
before=json.loads((BASE/'inputs.before.json').read_bytes())
checks=[{'ref':r,'actual':pin(r['path'])} for r in before['files']]
drift=[x for x in checks if x['ref']!=x['actual']]
after=save('inputs.after.json',{'checks':checks,'drift':drift,'live_canonical_read':False})
if drift:raise RuntimeError('Frozen input drift; review not sealed')
origin=pin(BASE/'failure-origin.be84c9.json')
review=json.loads((BASE/'review.json').read_bytes())
handoff=save('handoff.json',{
    'schema':'researchos.fresh58-publisher-independent-source-review-handoff.v1',
    'reviewer':review['reviewer'],'nonauthor':True,'state':'STOPPED',
    'decision':review['decision'],'requested_changes':review['requested_changes'],
    'producer_ref':review['producer_ref'],'fixed_inputs_ref':review['fixed_inputs_ref'],
    'review_ref':pin(BASE/'review.json'),'readable_review_ref':pin(BASE/'review.md'),
    'audit_ref':pin(BASE/'audit.json'),'inputs_before_ref':pin(BASE/'inputs.before.json'),
    'inputs_after_ref':after,'original_tool_io_ref':pin(BASE/'original-tool-io.json'),
    'new_failure_origins':[origin],'new_failure_count':1,'previous_Desktop_origins_not_recounted':True,
    'publisher_or_gate_imports':0,'candidate_target_calls':0,'canonical_mutations':0,
    'actual_publication':False,'source_acceptance':False,'formal_increment':0,
    'future_scope_grant':None,'actual_positive_negative_controls':'NOT_RUN',
    'manifest_path':str(BASE/'manifest.json'),
    'external_tool_annex_path':str(BASE/'metadata-seal-tool-annex.json')
})
names=['failure-origin.be84c9.json','review.json','review.md','inputs.before.json','inputs.after.json','audit.json','original-tool-io.json','seal_metadata.py','handoff.json']
mf=save('manifest.json',{'schema':'researchos.independent-review-manifest.v1','self_excluded':True,'count':len(names),'entries':[pin(BASE/n) for n in names],'external_annex_paths':[str(BASE/'metadata-seal-tool-annex.json')]})
print(json.dumps({'review':pin(BASE/'review.json'),'handoff':handoff,'manifest':mf,'origin':origin,'checked_inputs':len(checks),'drift':0,'state':'STOPPED'},ensure_ascii=False))
