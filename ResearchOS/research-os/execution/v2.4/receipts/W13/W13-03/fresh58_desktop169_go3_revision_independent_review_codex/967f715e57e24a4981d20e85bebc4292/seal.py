import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');P=ROOT/'execution/v2.4/receipts/W13/W13-03';OUT=Path(__file__).parent
N=P/'fresh58_desktop169_go3_revision_preparation_codex/736e757cdbc148a286c1d2426b8a7382'
B=P/'fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4'
def ref(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(name,v):
    with (OUT/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
checks=[]
def check(name,v):checks.append({'check':name,'passed':bool(v)})
oldmf=read(B/'manifest.json')
check('old manifest cardinality',oldmf['count']==len(oldmf['entries'])==30)
for r in oldmf['entries']:
    a=ref(r['path']);check('old member preserved '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes'])
s=read(N/'scope.v2.proposed.json');old=read(B/'scope.proposed.json');undo=dict(s)
for k in ['controller_ref','launcher_ref','debug_helper_ref','fixture_evaluator_ref']:undo[k]=old[k]
for k in ['controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']:undo.pop(k)
check('scope only four code refs plus two NULL reserves',undo==old)
controller=(N/'desktop_controller.v3.proposed.py').read_text(encoding='utf-8')
check('assertions then evaluator then verdict then qualification',controller.index("state['source_assertions_passed']=True")<controller.index('evaluation=')<controller.index("save(case/'fixture-verdict.json',evaluation)")<controller.index("need(evaluation['qualified']"))
check('deadline passed to actual helper call','absolute_deadline=helper_deadline' in controller)
check('both reserves remain Root-required',s['controller_evidence_reserve_seconds'] is None and s['launcher_evidence_reserve_seconds'] is None)
audit=read(OUT/'audit.json');allchecks=audit['checks']+checks
fail=[x for x in allchecks if not x['passed']]
save('supplemental-audit.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'old_manifest_ref':ref(B/'manifest.json'),'old_scope_ref':ref(B/'scope.proposed.json'),'candidate_execution':False})
save('tool-observations.json',{'schema':'researchos.tool-observation-known-fields.v1','audit_tool':{'chunk_id':'7e945a','exit_code':0,'observed_output':{'checks':138,'failed':[]}},'original_tool_payload_complete':False,'original_native_stream_files':None,'candidate_native_exits':None,'new_failure_origins':[]})
review={
 'schema':'researchos.desktop58-169-go3-independent-source-review.v1',
 'actor':'codex:/root/w05_merge_review','reviewer':'codex:/root/w05_merge_review','non_author':True,
 'decision':'REQUEST_CHANGES' if fail else 'READY_SOURCE_PREPARATION_ONLY',
 'verdict':'REQUEST_CHANGES' if fail else 'READY_SOURCE_PREPARATION_ONLY',
 'requested_changes':fail,'readiness':'SOURCE_PREPARATION_WITH_EXPLICIT_OPEN_GATES_ONLY',
 'candidate_handoff_ref':ref(N/'handoff.json'),'candidate_manifest_ref':ref(N/'manifest.json'),
 'selected_refs':read(N/'handoff.json')['selected_refs'],'scope_ref':ref(N/'scope.v2.proposed.json'),
 'prior_review_ref':read(N/'handoff.json')['old_request_ref'],
 'reuse_statement':'Prior f6158ce source review supplied D169-R01/R02 and baseline boundaries. This review independently hashes new manifest24, old manifest30, four full-file inverses, unchanged AST/bytes, selected refs and narrow fixture sources; no historical resource tree, runtime or product replay is repeated.',
 'audit_refs':[ref(OUT/'audit.json'),ref(OUT/'supplemental-audit.json')],
 'checks':{'total':len(allchecks),'failed':len(fail),'whole_byte_inverses':4,'new_manifest_members':24,'old_manifest_members':30},
 'finding_disposition':[
  {'id':'D169-R01','status':'STATIC_SOURCE_CORRECTION_REVIEWED','evidence':'fixture_evaluator.v2.proposed.py observer_lifecycle and validate_case; desktop_controller.v3.proposed.py:225-230','assessment':'Positive unique PID and exact row sequences; request IDs unique contiguous per PID; one body/finish/close, both body and finish before close, finished and reader_complete true; duplicates, orphan, error/overflow/unknown events refused. Body and finish relative order may differ. Raw accepted_argument verification and unique gap-free method ordinals retained; synchronous nested return callbacks need not precede finish. Native/original assertion PASS is saved separately; lifecycle refusal returns transport OPEN, then fixture-verdict is saved before qualification failure stops.'},
  {'id':'D169-R02','status':'STATIC_SOURCE_CORRECTION_REVIEWED','evidence':'desktop_controller.v3.proposed.py:101-114,237-247; desktop_launch.v2.proposed.py:38-52,65-72; deadline helper:150-160,663-686,734-741','assessment':'Controller reserves25 finalization+5 cleanup+explicit Root IO before launch and passes absolute inner-minus-IO deadline. Helper caps own effective process timeout and cleanup/finalization to that deadline, checks generation/hash loops and final handle closure; overrun records timeout/incomplete instead of success. Launcher subtracts elapsed preparation, cleanup and its own IO reserve; post-result overrun refuses success. Blocking Windows API or filesystem calls cannot be preempted by Python checks; actual external owned-process boundary and measured Root budgets remain required.'}
 ],
 'fixture_compatibility':{
  'status':'STATIC_ONLY_NO_DEMONSTRATED_CONTRADICTION',
  'sources':[ref(ROOT/'tests/ui/desktop/http-wire-boundary.test.mjs'),ref(ROOT/'tests/ui/desktop/w13-react.test.js')],
  'observations':['HTTP wire harness consumes body before response; closeAllConnections occurs in cleanup after assertions. reply.hold branch has no hold:true call in this source; validator hang controls are child-process controls, not authorized incomplete HTTP exceptions.','Legacy401/redirect fixture handles response in request end callback; SSE fixture explicitly ends after20ms and test consumes response.text. Unchanged observer attaches data/end before original server listener, so normal body observation is possible. No actual event order or successful transport qualification was measured.','An actually premature close, body-end after close or interrupted request must remain OPEN even when the original negative assertion passes. Future evidence-specific exceptions require a new review; none are granted here.'],
  'socket_transmitted_byte_count':None,'auto_Date_ContentLength':None,'actual_Node_event_sequences':None,
  'expected_abort_exception_authorized':False},
 'budgets':{'Node_cases_expected':169,'Go_top_cases_expected':3,'native_top_command_cap':176,'case_invocations_expected':170,'builder_nested_expected':9,'HTTP_cap':390,'offscreen_Electron_controls':2,'installed_GUI':0,'SDK_model_external_paid':0,'Root_inner_seconds':None,'Root_outer_seconds':None,'Root_controller_IO_reserve_seconds':None,'Root_launcher_IO_reserve_seconds':None,'time_fit_proven':False},
 'future_controls':'All candidate controls remain NOT_RUN; JSON counterexample evaluation, Node observer lifecycle, deadline cancellation and handle closure were not executed.',
 'open_gates':['Actual Root authority adapter, scope/registration/grant and canonical snapshot bindings.','Current58 fresh CLI2 independently qualified prerequisite.','Current58 source/compiler/runtime catalogs, exact public environment, required IO/inner/outer/builder budgets and external owned launch bound.','New actual Go graph, builds and169Node+3Go finite execution with all observed vectors/runtime/HTTP lifecycle and first-failure evidence.','Installed GUI/NVDA, SDK/P02, whole-parent/formal and source acceptance remain outside this review.'],
 'actual_integration_executed':False,'actual_candidate_imports':0,'actual_candidate_executions':0,'actual_Node_Go_SQL_HTTP_Windows_calls':0,'canonical_writes':0,'source_acceptance':False,'formal_increment':0,'execution_authorized':False,'new_failure_origins':[],'status':'STOPPED'
}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-source-review-handoff.v1','review_ref':ref(OUT/'review.json'),'decision':review['decision'],'reviewer':review['reviewer'],'new_failure_origins':[],'actual_execution_authorized':False,'status':'STOPPED','manifest_filename':'manifest.json'})
files=sorted(p for p in OUT.iterdir() if p.is_file())
save('manifest.json',{'schema':'researchos.public-review-manifest.v1','self_excluded':True,'count':len(files),'entries':[ref(p) for p in files]})
print(json.dumps({'decision':review['decision'],'checks':len(allchecks),'failed':fail,'review_ref':ref(OUT/'review.json'),'manifest_ref':ref(OUT/'manifest.json'),'handoff_ref':ref(OUT/'handoff.json')},ensure_ascii=False))
