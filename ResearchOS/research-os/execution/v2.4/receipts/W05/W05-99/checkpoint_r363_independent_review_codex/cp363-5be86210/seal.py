import pathlib,json,hashlib
P=pathlib.Path;O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r363-native-grant-expired-fixture-lost-attach-source-ready'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
r=json.loads((O/'review.json').read_bytes())
checkpoint_reviewed_ref=next(x for x in json.loads((O/'input-pins.json').read_bytes()) if P(x['path'])==R/'execution/v2.4/checkpoint.json')
assert checkpoint_reviewed_ref['sha256']=='9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25' and checkpoint_reviewed_ref['bytes']==4223052
assert r['decision']=='CP363_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' and all(x['passed'] for x in r['checks']) and len(r['checks'])==2172
b=(N/'postwrite-original-root-tool-io.json').read_bytes()
with (O/'original-root-postwrite-tool-io.json').open('xb') as f:f.write(b)
assert ref(O/'original-root-postwrite-tool-io.json')['sha256']==ref(N/'postwrite-original-root-tool-io.json')['sha256']
save('HDF.json',{'schema':'researchos.independent-cp363-consistency-handoff.v1','decision':r['decision'],'checkpoint_ref':checkpoint_reviewed_ref,'checkpoint_revision':363,'checkpoint_author':'codex:/root','reviewer':'codex:/root/native_temp_independent_review','reviewer_is_not_checkpoint_author':True,'source_handoff_ref':ref(N/'handoff.json'),'source_manifest_ref':ref(N/'manifest.json'),'review_ref':ref(O/'review.json'),'report_ref':ref(O/'report.md'),'input_pins_ref':ref(O/'input-pins.json'),'guard_ref':ref(O/'guard.final.json'),'origin_qualification_ref':ref(O/'failure-exit-qualifications.json'),'original_tool_io_ref':ref(O/'original-tool-io.json'),'Root_original_postwrite_io_ref':ref(O/'original-root-postwrite-tool-io.json'),'checks_passed':2172,'checks_total':2172,'guarded_input_count':1997,'all_guards_closed':True,'old873_entire_objects_and_raw_array_prefix_preserved':True,'registered_failures':893,'registered_ordinal_cutoff':895,'later896_to899_not_registered_in_CP363':True,'postwrite_next_ordinal':900,'new_review_execution_failures':0,'authority':'CHECKPOINT_CONSISTENCY_ONLY','product_authority':'NONE','formal_acceptance':False,'canonical_writes':False,'stop':True})
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file()]
save('MF.json',{'members':members,'scope':'All files present before MF; MF itself and terminal full-io/postseal excluded. Referenced evidence tree is not duplicated.','authority':'CHECKPOINT_CONSISTENCY_ONLY','stop':True})
for r in members:assert ref(P(r['path']))==r
print(json.dumps({'HDF':ref(O/'HDF.json'),'MF':ref(O/'MF.json'),'report':ref(O/'report.md'),'members_verified':len(members)},ensure_ascii=False))

