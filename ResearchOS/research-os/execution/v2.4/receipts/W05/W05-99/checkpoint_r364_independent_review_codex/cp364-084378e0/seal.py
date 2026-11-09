import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib
P=pathlib.Path;O=P(__file__).resolve().parent
def pin(p):
 b=P(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
r=json.loads((O/'review.final.json').read_bytes())
assert r['decision']=='CP364_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' and not r['remaining_findings']
for n in ['guard.final.json','supplemental.guard.final.json']:
 g=json.loads((O/n).read_bytes());assert g['closed'] and g['retained_handles_count']==0 and not g['errors']
mf=save('MF.json',dict(schema='researchos.independent-cp364-manifest.v1',members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()],formal_acceptance=False))
h=save('HDF.json',dict(schema='researchos.independent-cp364-handoff.v1',reviewer='codex:/root/native_temp_independent_review',decision=r['decision'],manifest_ref=mf,review_ref=pin(O/'review.final.json'),initial_review_ref=pin(O/'review.json'),report_ref=pin(O/'report.md'),original_tool_io_ref=pin(O/'original-tool-io.json'),failure904_ref=pin(O/'failure-origin.904.json'),guard_refs=[pin(O/n) for n in ['guard.final.json','supplemental.guard.final.json']],registered_failures=900,highest_registered_ordinal=902,next_at_cutoff=903,later_pending=[903,904],live_next_as_reported_by_Root=905,checks='480 initial PASS plus 3 schema assumptions resolved through 6 passing supplemental checks',reviewed_inputs=360,supplemental_inputs=363,review_execution_failures=[904],formal_acceptance=False,authority='CHECKPOINT_CONSISTENCY_ONLY',Main_canonical_write=False,product_native_model_SQL_execution=False,private_key_read=False,all_guards_closed=True,STOP=True))
print(json.dumps(dict(handoff_ref=h,manifest_ref=mf,report_ref=pin(O/'report.md'),review_ref=pin(O/'review.final.json'),failure904_ref=pin(O/'failure-origin.904.json'))))
print('ROOT_PYTHON_EXIT=0')
