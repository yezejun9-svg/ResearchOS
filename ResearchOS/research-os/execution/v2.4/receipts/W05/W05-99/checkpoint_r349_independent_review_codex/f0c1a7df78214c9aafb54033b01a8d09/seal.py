import json,pathlib,hashlib
O=pathlib.Path(__file__).parent
def ref(p):
 p=pathlib.Path(p);b=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def put(n,d):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
intake=json.loads((O/'input-intake.json').read_bytes())
for r in intake['refs']:
 actual=ref(r['path'])
 assert actual['sha256']==r['sha256'] and actual['bytes']==r['bytes']
review=json.loads((O/'review.json').read_bytes())
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
put('manifest.json',dict(schema='researchos.independent-checkpoint-review-manifest.v1',members=members,member_count=len(members),input_refs=intake['refs'],input_drift=0,excludes_self_and_handoff=True))
put('handoff.json',dict(schema='researchos.independent-checkpoint-review-handoff.v1',actor_id='codex:/root/command_queue_impl',decision=review['decision'],manifest_ref=ref(O/'manifest.json'),review_ref=ref(O/'review.json'),checks_ref=ref(O/'evidence-checks.json'),checkpoint_ref=review['checkpoint_ref'],ownership_ref=review['ownership_ref'],verified_checks=review['verified_checks'],unique_inputs=review['unique_inputs'],input_drift=0,old742_preserved=True,added_ordinals=[745,746,747,748,749],registered_failures=747,highest_ordinal=749,provider_requests=None,recorded_model_effects=0,business_reconciliation='OPEN',formal_acceptance=False,qualification=False,C7_actual_started=False,new_failures=[],Source_canonical_SQL_Native_provider_mutations=0,private_state_read=False,stopped=True))
print(json.dumps({'handoff_ref':ref(O/'handoff.json'),'manifest_ref':ref(O/'manifest.json'),'review_ref':ref(O/'review.json'),'member_count':len(members)}))

