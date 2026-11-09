"""Owned metadata sealer only; does not import or execute any candidate."""
from pathlib import Path
import hashlib,json
BASE=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_desktop169_go3_independent_source_review_codex/14818767d60a485885f7c5e0e36135cd')
def pin(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,value):
    b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (BASE/name).open('xb') as f:f.write(b)
    return pin(BASE/name)
before=json.loads((BASE/'frozen-inputs.before.json').read_bytes())
checks=[]
for r in before['refs']:
    a=pin(r['path'])
    checks.append({'ref':r,'actual':a,'equal':a==r})
after=save('frozen-inputs.after.json',{'checks':checks,'drift':[x for x in checks if not x['equal']]})
if any(not x['equal'] for x in checks):
    raise RuntimeError('Frozen reviewed input drift; no sealed approval')
origins=[pin(BASE/'failure-origin.058eb9.json'),pin(BASE/'failure-origin.b27bd3.json')]
handoff={
    'schema':'researchos.independent-desktop169-go3-review-handoff.v1',
    'actor':'codex:/root/f08_whole_scope_review','non_author':True,
    'state':'STOPPED','verdict':'REQUEST_CHANGES',
    'readiness':'SOURCE_PREPARATION_WITH_OPEN_GATES_ONLY',
    'review_ref':pin(BASE/'review.json'),'readable_review_ref':pin(BASE/'review.md'),
    'audit_ref':pin(BASE/'static-audit.json'),
    'inputs_before_ref':pin(BASE/'frozen-inputs.before.json'),'inputs_after_ref':after,
    'original_tool_io_ref':pin(BASE/'original-tool-io.json'),
    'new_failure_origins':origins,'new_failure_count':2,
    'metadata_failures_original_exits':[{'origin':'058eb9','outer':1,'Python':1,'target_native':None},{'origin':'b27bd3','outer':1,'Python':1,'target_native':None}],
    'blocking_Important':['D169-R01','D169-R02'],'Critical':[],
    'candidate_imports':0,'candidate_target_calls':0,
    'canonical_mutations':0,'source_acceptance':False,'formal_increment':0,
    'AST_parse_only':True,'Go_Node_DLL_Job_OS_behavior':'NOT_RUN',
    'Root_actual_adapter_catalog_tuple_grant_budget':'OPEN',
    'manifest_path':str(BASE/'manifest.json'),
    'external_final_tool_annex_path':str(BASE/'metadata-seal-tool-annex.json'),
    'external_annex_reason':'Exact completion of this metadata sealer is captured afterward; no recursive self-hash claim.'
}
h=save('handoff.json',handoff)
names=['failure-origin.058eb9.json','failure-origin.b27bd3.json','review.json','review.md','frozen-inputs.before.json','frozen-inputs.after.json','static-audit.json','original-tool-io.json','seal_metadata.py','handoff.json']
members=[pin(BASE/n) for n in names]
m=save('manifest.json',{'schema':'researchos.independent-review-manifest.v1','self_excluded':True,'count':len(members),'entries':members,'external_annex_paths':[str(BASE/'metadata-seal-tool-annex.json')]})
print(json.dumps({'review':pin(BASE/'review.json'),'handoff':h,'manifest':m,'origins':origins,'before_after_count':len(checks),'drift':0,'state':'STOPPED'},ensure_ascii=False))
