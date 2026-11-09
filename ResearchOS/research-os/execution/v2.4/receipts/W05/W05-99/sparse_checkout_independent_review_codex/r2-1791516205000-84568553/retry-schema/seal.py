import pathlib,json,hashlib
P=pathlib.Path;O=P(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
r=json.loads((O/'review.json').read_bytes());assert r['decision']=='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL' and all(x['passed'] for x in r['checks'])
source=P('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths')
save('HDF.json',{'schema':'researchos.independent-sparse-revision-source-review.v1','status':r['decision'],'source_handoff':ref(source/'HDF.json'),'source_manifest':ref(source/'MF.json'),'prepare_ref':ref(source/'prepare_attach_fixture_two_parent.actual_owned.py'),'validate_ref':ref(source/'validate_attach_fixture_two_parent.actual_owned.py'),'choice_ref':ref(source/'source.integration.choice.json'),'review_ref':ref(O/'review.json'),'report_ref':ref(O/'report.md'),'guard_ref':ref(O/'guard.final.json'),'original_tool_io_ref':ref(O/'original-tool-io.json'),'previous_mechanical_failure_ref':ref(O.parent/'failure-896-original-tool-io.json'),'reviewer_failure_ordinal_requested':896,'reviewer_actual_failure_count':1,'candidate_actual_execution':False,'authority':'SOURCE_REVIEW_ONLY','formal_acceptance':False,'stop':True})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file()]+[ref(p) for p in sorted(O.parent.iterdir()) if p.is_file()]
save('MF.json',{'members':members,'scope':'All review and failed-review files present before MF; MF and terminal full-io/postseal descendants excluded.','stop':True})
for p in members:assert ref(P(p['path']))==p
print(json.dumps({'HDF':ref(O/'HDF.json'),'MF':ref(O/'MF.json'),'report':ref(O/'report.md'),'members_verified':len(members),'decision':r['decision']},ensure_ascii=False))

