import pathlib,json,hashlib
P=pathlib.Path;O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
I=B/'integration_codex/attach-fixture-two-parent-sparse-isolation-root-1791516205000';A=B/'integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000';S=B/'integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths'
def ref(p):
 p=P(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
r=json.loads((O/'review.json').read_bytes());assert r['decision']=='T11_TWO_PARENT_ACTUAL_COMPONENT_ACCEPTED_NO_FORMAL_AUTHORITY' and len(r['checks'])==6165 and all(x['passed'] for x in r['checks'])
sup=json.loads((O/'supplemental-accepted-composition-binding.json').read_bytes());assert sup['checks_passed']==sup['checks_total']==5
ip=json.loads((O/'input-pins.json').read_bytes());cpr=next(x for x in ip if P(x['path'])==R/'execution/v2.4/checkpoint.json')
assert cpr['sha256']=='9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25'
b=(S/'postseal-root-actual-original-io.json').read_bytes()
with (O/'original-root-actual-tool-io.json').open('xb') as f:f.write(b)
assert ref(O/'original-root-actual-tool-io.json')['sha256']==ref(S/'postseal-root-actual-original-io.json')['sha256']
save('HDF.json',{'schema':'researchos.independent-T11-actual-review-handoff.v1','decision':r['decision'],'reviewer':'codex:/root/native_temp_independent_review','actual_author':'codex:/root','reviewer_did_not_execute_actual':True,'isolation_ready_ref':ref(I/'isolation.ready.json'),'actual_closed_ref':ref(A/'validation.closed.json'),'reviewed_checkpoint_ref':cpr,'reviewed_checkpoint_revision':363,'review_ref':ref(O/'review.json'),'report_ref':ref(O/'report.md'),'manifest_inputs_ref':ref(O/'input-pins.json'),'guard_ref':ref(O/'guard.final.json'),'process_facts_ref':ref(O/'owned-process-facts.json'),'inventory_reconstruction_ref':ref(O/'inventory-reconstruction.json'),'supplemental_binding_ref':ref(O/'supplemental-accepted-composition-binding.json'),'original_reviewer_io_ref':ref(O/'original-tool-io.json'),'original_Root_io_ref':ref(O/'original-root-actual-tool-io.json'),'primary_checks_passed':6165,'primary_checks_total':6165,'supplemental_checks_passed':5,'supplemental_checks_total':5,'guarded_inputs':4978,'all_guards_closed':True,'actual_parent_count':2,'actual_leaf_count':3,'actual_pass_terminals':5,'actual_fail_terminals':0,'actual_skip_terminals':0,'other52_executed_or_newly_accepted':False,'all132_declarations_are_not_execution_scope':True,'Main_adopted':False,'current_formal_count':0,'required_formal_count':42,'native_migration_authority_accepted':False,'new_review_execution_failures':0,'formal_acceptance':False,'authority':'ACTUAL_COMPONENT_EVIDENCE_ONLY','stop':True})
ms=[ref(p) for p in sorted(O.iterdir()) if p.is_file()]
save('MF.json',{'members':ms,'scope':'All own files present before MF. MF and terminal full-io/postseal descendants excluded; large referenced input tree not copied.','stop':True})
for x in ms:assert ref(P(x['path']))==x
print(json.dumps({'HDF':ref(O/'HDF.json'),'MF':ref(O/'MF.json'),'report':ref(O/'report.md'),'members_verified':len(ms),'decision':r['decision']},ensure_ascii=False))

