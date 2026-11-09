import ast,difflib,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
C=N.parents[1]/'w09_formal_profile_v2_source_codex/profv2-01a12b31'
R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,obj):
 p=N/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
controls=json.loads((N/'controls.json').read_bytes());pins=json.loads((N/'input-pins.json').read_bytes());guard=json.loads((N/'sourceguard.final.json').read_bytes())
assert len(controls['checks'])==41 and all(x['status']=='PASS' for x in controls['checks'])
assert guard['verification']=='PASSED' and guard['closed'] is True and guard['retained_handles_count']==0 and not guard['errors']
assert all(pin(r['path'])==r for r in pins)
before=C/'formal_case_index.before.py';after=C/'formal_case_index.after.py';profile=C/'formal_profile_w09.after.py'
left=before.read_text(encoding='utf-8').splitlines(keepends=True);right=after.read_text(encoding='utf-8').splitlines(keepends=True)
forward=''.join(difflib.unified_diff(left,right,fromfile=before.name,tofile=after.name)).encode()
inverse=''.join(difflib.unified_diff(right,left,fromfile=after.name,tofile=before.name)).encode()
assert forward==(C/'formal_case_index.forward.diff').read_bytes()
assert inverse==(C/'formal_case_index.inverse.diff').read_bytes()
tree=ast.parse(after.read_bytes());defs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
api_ns={'__name__':'w09_v2_seal_nonmain'};exec(compile(after.read_bytes(),str(after),'exec'),api_ns)
assert api_ns['_profile_api']()._owned_inventory is api_ns['_owned_inventory']
assert api_ns['_profile_api']().Reader is api_ns['Reader']
extra=save('supplemental-checks.json',{'scope':'SYNTHETIC_NONAUTHORITATIVE_SOURCE_ONLY','checks':[{'name':'forward_diff_exact','status':'PASS'},{'name':'inverse_diff_exact','status':'PASS'},{'name':'actual_profile_API_exports_owned_inventory','status':'PASS'},{'name':'actual_profile_API_retains_Reader','status':'PASS'}],'actual_index_main_runs':0})
findings=[
 {'id':'F2','priority':'P1','status':'PARTIALLY_FIXED_STILL_OPEN','file':str(profile),'start':230,'end':230,'related_lines':[378,379,470,483,584],
  'title':'Review cutoff still trusts report timestamps when original Go stream contradicts them',
  'impact':'The v2 ordering check rejects future self-reported dates, but takes native clocks only from report.started_at/ended_at. The pinned raw Go JSONL and original process completion are not bound to those clocks. Earlier review can still pass when the raw stream carries later execution times.',
  'evidence':'Independent control called the actual trusted verify_native consumer on isolated synthetic Go JSONL with Time=2026-10-20. Report end=2026-10-01 and real _review_execution_cutoff with review=2026-10-03 both passed. No Go process ran and no full formal owner was accepted.',
  'required_fix':'Derive or validate Native and dispatcher completion against the pinned original execution record and raw stream timestamps, including identified process/run provenance. Reject report/raw-clock contradictions. Keep GLOBAL completion bounded to those original execution intervals and the independent review/Root receipt.'},
 {'id':'F3','priority':'P1','status':'PARTIALLY_FIXED_STILL_OPEN','file':str(after),'start':1032,'end':1038,'related_lines':[1060,1119],
  'title':'Uppercase .RAW additions evade the Windows owned-inventory CAS',
  'impact':'_owned_inventory uses case-sensitive name.endswith(".raw"), whereas the producer and trusted closure use Windows Path.rglob("*.raw") with case-insensitive matching. Added extra.RAW changes the actual closure member set but recheck_inputs remains PASS.',
  'evidence':'Real Windows Reader + _owned_inventory + recheck_inputs over the isolated own review repository: original one.raw pinned; extra.RAW added; closure-equivalent rglob includes both; CAS returns PASS. Lowercase addition, deletion, changed bytes and conflicting prior hashes correctly reject.',
  'required_fix':'Use the same explicit case semantics and membership algorithm in producer, closure, initial inventory and CAS. Add Windows .RAW/mixed-case and nested-member tests. Retain the new compare-before-register behavior.'},
 {'id':'F5','priority':'P1','status':'NOT_FIXED','file':str(profile),'start':493,'end':528,
  'title':'Fixed Root paths still accept fabricated original collaboration events',
  'impact':'The fixed index and origin schemas contain only asserted writer_actor/source/sender/recipient/event_id/content. The code does not validate an original tool event, channel or thread identity, or evidence that Root actually received the event. Moving self-reported JSON into root_original_events does not establish this authority.',
  'evidence':'Independent control used the real Reader and all exact fixed prefixes/pins. A fully invented index, capture and custom-schema origin with event_id=invented-event-with-no-tool-channel was accepted by unchanged _root_original. No real original collaboration event exists. Missing registration, author receipt path and pinned byte tampering correctly reject.',
  'required_fix':'Consume and validate a real Root-captured original delivery record, retaining source event shape/identity, channel/thread, actual sender/recipient, exact message bytes and receive time. Bind the capture registry to that independently established provenance. An author-supplied custom schema or source string cannot be the original evidence. Keep actual capture OPEN until Root receives it.'}
]
for row in findings:row['source_ref']=pin(row['file'])
fr=save('findings.json',{'schema':'researchos.w09-v2-independent-findings.v1','decision':'REQUEST_CHANGES','findings':findings,'closed_source_findings':['F1','F4']})
audit=save('audit-coverage.json',{'scope':'SOURCE_ONLY','compatibility':{'first_51719_bytes_exact':True,'original_Reader_AST_unchanged':True,'W07_loader_AST_unchanged':True,'original_final_CLI_guard_retained':True,'full_before_inverse_preserved':True,'both_diff_directions_recomputed_exact':True,'profile_API_exposes_inventory':True,'runtime_W04_W07_not_executed':True},'fixed_source_loader':'Fixed execution/v2.4/formal_profile_w09.py only; no receipt-selected Python; both index and new profile must be adopted together later.','F1':'CLOSED_SOURCE: exact int checks for both report and tool exits; False/True/float/null/string/nonzero negative controls; _native actually calls helper.','F2':'PARTIAL: self-reported Native/dispatcher/GLOBAL future dates rejected, but raw original execution time conflict accepted.','F3':'PARTIAL: lowercase add/delete/change/prior-hash conflicts rejected; uppercase .RAW addition still accepted on Windows.','F4':'CLOSED_SOURCE: exactly 21 fixed producer SOURCES parsed after hash pin, exact native source set and every digest compared to current vector/bytes; 21 inputs included in independent actual SourceGuard. This does not create Actual process provenance.','F5':'OPEN: paths/hashes and custom schemas are validated, original delivery authenticity remains unestablished.','reader_CAS':'All previously declared input classes remain pinned. v2 adds owned inventories to context and generic dependency snapshot, reruns inventories before return and in CAS, and compare-before-register pins streams/source/witnesses. F3 remains a completeness mismatch. Root capture index/origin enter Reader file CAS but authenticity is F5.','routes_GLOBAL':'Six routes preserved; G01 FIXTURE, G02 LIVE_WINDOWS, C19/A06 each three frozen assertions and four distinct GLOBAL files remain required. No route or GLOBAL actually executed/issued here.','source_guard':{'actual_guarded_inputs':40,'verification':'PASSED','closed':True,'retained_handles_count':0,'observation_ref':pin(N/'sourceguard.final.json')},'new_original_failures':[],'root_state':'No Canon state read or written; Root CP369/OW173 concurrent registration is outside these Source inputs and not a finding.','authority':'No indexMain, actual Native producer, dispatcher, Go, SQL, model or product execution. All test bytes synthetic nonauthoritative; current Formal and actual six routes/Root original capture remain OPEN; no formal cases created.','cleanup':'All transient synthetic repository files/directories removed from this own review namespace; counterexample descriptions retained.'})
decision=save('source-decision.json',{'schema':'researchos.w09-v2-independent-source-decision.v1','decision':'REQUEST_CHANGES','reviewer':'codex:/root/attach_fixture_source_review','source_handoff_ref':pin(C/'HDF.json'),'source_manifest_ref':pin(C/'MF.json'),'source_after_refs':[pin(after),pin(profile)],'findings_ref':fr,'audit_ref':audit,'controls_ref':pin(N/'controls.json'),'supplemental_checks_ref':extra,'controls_scope':'SYNTHETIC_NONAUTHORITATIVE_SOURCE_ONLY','checks':45,'source_fixes_closed':['F1','F4'],'blocking_source_findings':['F2','F3','F5'],'actual_guard_ref':pin(N/'sourceguard.final.json'),'guard_closed0':True,'adoption_authorized':False,'formal_acceptance':False,'new_formal_cases':0,'actual_runs':0,'STOP':True,'FINAL':True})
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
mf=save('MF.json',{'schema':'researchos.w09-v2-independent-source-manifest.v1','scope':'SOURCE_ONLY_REQUEST_CHANGES','members':members,'guarded_inputs':40,'retained_handles_count':0})
hd=save('HDF.json',{'schema':'researchos.w09-v2-independent-source-handoff.v1','status':'REQUEST_CHANGES','manifest_ref':mf,'source_decision_ref':decision,'findings_ref':fr,'source_handoff_ref':pin(C/'HDF.json'),'source_manifest_ref':pin(C/'MF.json'),'closed_source_findings':['F1','F4'],'blocking_findings':['F2','F3','F5'],'checks':45,'actual_sourceguard_closed0':True,'formal_acceptance':False,'STOP':True,'FINAL':True})
post=save('postseal.json',{'handoff_ref':hd,'manifest_ref':mf,'decision_ref':decision,'all_review_members_exact':all(pin(r['path'])==r for r in members),'all_Source_inputs_still_exact':all(pin(r['path'])==r for r in pins),'retained_handles_count':0,'new_original_failures':[]})
print(json.dumps({'handoff_ref':hd,'manifest_ref':mf,'decision_ref':decision,'findings_ref':fr,'postseal_ref':post},ensure_ascii=False))
