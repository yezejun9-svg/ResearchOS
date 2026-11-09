"""Pure immutable JSON binding proposal; no candidate execution."""
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
OLD=OUT.parents[1]/'fresh58_cli2_controller_preparation_codex/86d71652d03649879b13e03a974456d9'
def need(v,m):
    if not v:raise RuntimeError(m)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,o):
    with (OUT/n).open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
raw=(OLD/'scope.current58.proposed.json').read_bytes();before=json.loads(raw);after=json.loads(raw)
after['authorization_gate_ref']=ref(OUT/'authorization_gate.current58.v2.proposed.py')
inverse=json.loads(json.dumps(after));inverse['authorization_gate_ref']=before['authorization_gate_ref']
need(inverse==before,'Scope only gate ref change')
need(after['preparation_only'] is True and after['execution_authorized'] is False,'Preparation boundary')
for k in ['expected_registration','expected_before_registration','catalog_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','controller_review_path']:
    need(after[k] is None,'No guessed future authority '+k)
save('scope.current58.v2.proposed.json',after)
save('scope.ref-edits.json',[{'key':'authorization_gate_ref','before':before['authorization_gate_ref'],'after':after['authorization_gate_ref']}])
save('future-controls.NOT_RUN.json',{'status':'NOT_RUN','target_calls':0,'controls':[
 {'id':'SET-P01','input':'Original shared38/cli8/Desktop15 union; all exact current catalog pins','expected':'Pass source-set predicate only'},
 {'id':'SET-N01','input':'Replace one original43-only path with unrelated valid catalog go.mod while retaining Desktop15 and count58','expected':'Reject exact union'},
 {'id':'SET-N02','input':'Missing/duplicate original path or alias','expected':'Reject existing duplicate/canonical or union predicate'},
 {'id':'TUP-P01','input':'Actual sealed forward request/intent/audit/verified tuple; equal or later current CP/OW/failure count','expected':'Pass tuple predicate only'},
 {'id':'TUP-N01','input':'Forward failures count exceeds current canonical count while CP/OW do not','expected':'Reject third component'},
 {'id':'TUP-N02','input':'before/after/request tuple has boolean, float, extra element or missing element','expected':'Reject exact three ints'},
 {'id':'TUP-N03','input':'intent transition wrong checkpoint/ownership/failure pair or boolean/float pair','expected':'Reject precise transition'},
 {'id':'TUP-N04','input':'request tuple or head pair differs from audit or source closure','expected':'Reject origin pairing'},
 {'id':'TUP-N05','input':'verified tuple integer type differs or intent ref differs','expected':'Reject preserved verification binding'}],
 'qualification':'No candidate has been imported, invoked or evaluated. No Root actual forward facts have been invented.'})
save('binding-contract.v2.json',{'schema':'researchos.fresh58-cli2-gate-revision-binding.v1','selected_gate_ref':after['authorization_gate_ref'],'runner_ref':after['runner_ref'],'launcher_ref':after['launcher_ref'],'scope_template_ref':ref(OUT/'scope.current58.v2.proposed.json'),'prior_scope_ref':ref(OLD/'scope.current58.proposed.json'),'prior_handoff_ref':ref(OLD/'handoff.json'),'prior_manifest_ref':ref(OLD/'manifest.json'),'actual_source_head':after['source_commit'],'actual_parent':after['actual_candidate_parent_expected'],'unchanged':['runner entirety','launcher entirety','original two cases','HTTP admission and observation limits','16 native command bound in runner','helpers','instrumentation','timeouts','Root grant/CAS four-copy semantics'],'future_Root_authority':None,'future_actual_forward_seal':None,'actual_execution_authorized':False,'formal_increment':0,'no_circular_review_binding':'Root binds a future immutable scope containing this new gate pin; actual full-scope review is acquired from sealed canonical reference using the original path-only contract.'})
print(json.dumps({'scope':ref(OUT/'scope.current58.v2.proposed.json'),'binding':ref(OUT/'binding-contract.v2.json')},ensure_ascii=False))
