import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CANDIDATE = ROOT / '.local/worktrees/codex-w0599-command-queue/execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/w07-root-registration-candidate-a0c4f30a-50d2-42d5-924b-24131c5763e7'
def hash_bytes(b): return hashlib.sha256(b).hexdigest()
def ref(p): return {'path': p.relative_to(ROOT).as_posix(), 'sha256': hash_bytes(p.read_bytes())}
def read(p): return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def require(ok,reason):
    if not ok: raise ValueError(reason)
expected = {'issue_reviewed_current.py':'b65d2a363c513e0bbdec8659f96a0f19f3fe140a39d28f39e5590170b62bb250','handoff-final.json':'b5691e71e07968ac308ff1ecb62e6dedf24ace6dde0a618dfa8070c9e74551c8','manifest-final.json':'9f7ce984a436281675d64c802c876aee1aa4e8be5adb203241c3f62dcdb40396'}
for name,h in expected.items(): require(ref(CANDIDATE/name)['sha256']==h,'candidate drift '+name)
manifest=read(CANDIDATE/'manifest-final.json')
for row in manifest: require(hash_bytes(Path(row['path']).read_bytes())==row['sha256'],'manifest '+row['path'])
source=(CANDIDATE/'issue_reviewed_current.py').read_bytes()
tree=ast.parse(source)
require(not any(isinstance(n,ast.Assert) for n in ast.walk(tree)),'optimization unsafe guard')
compile(source,'reviewed-helper','exec',optimize=2)
handoff=read(CANDIDATE/'handoff-final.json')
argv=handoff['actual_argv_not_executed']
def argument(name): return argv[argv.index('--'+name)+1]
inputs={k: Path(argument(k)) for k in ('context','review','received-message')}
context,review,message=[read(inputs[k]) for k in ('context','review','received-message')]
for k,arg in [('review','expected-review-sha256'),('received-message','expected-message-sha256')]: require(ref(inputs[k])['sha256']==argument(arg),arg)
proof=ROOT/context['proof_ref']['path']
require(ref(proof)['sha256']==context['proof_ref']['sha256']==argument('expected-proof-sha256'),'proof binding')
require(review['context_ref']==ref(inputs['context']) and review['proof_ref']==ref(proof),'real review binding')
require(message['review_ref']==ref(inputs['review']) and message['sender']==review['reviewer_id']=='codex:/root/w05_merge_review','real reviewer')
require(message['recipient']==message['recorded_by']=='codex:/root','actual root')
locator_hash=hash_bytes(json.dumps(message['event_locator'],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
require(locator_hash==argument('expected-event-locator-sha256')==handoff['actual_locator_sha256'],'locator hash')
require(message['event_locator']['message_content_sha256']==hash_bytes(message['content'].encode()),'actual content locator')
require(ref(inputs['review'])['sha256'] in message['content'] and ref(proof)['sha256'] in message['content'],'actual delivered hashes')
require(datetime.fromisoformat(context['created_at'])<=datetime.fromisoformat(review['issued_at'])<=datetime.fromisoformat(message['received_at']),'real times')
state=read(ROOT/'execution/v2.4/step_state.json'); cp=read(ROOT/'execution/v2.4/checkpoint.json'); ownership=read(ROOT/'execution/v2.4/path_ownership.json')
owner=next(r for r in state['steps'] if r['id']=='W07-99')
require(owner['status'] in ('IN_PROGRESS','EXECUTION_REPORTED'),'root has not issued before helper review')
controls=read(HERE/'controls-result.json')
require(controls['status']=='PASS' and controls['count']==11,'controls')
require(controls['real_canonical_before']==controls['real_canonical_after'],'synthetic controls touched canonical')
audit={'schema':'researchos.w07.helper-independent-audit.v1','actor':'codex:/root/w05_merge_review','at':datetime.now(timezone.utc).isoformat(),'source_ref':ref(CANDIDATE/'issue_reviewed_current.py'),'manifest_ref':ref(CANDIDATE/'manifest-final.json'),'manifest_entries_verified':len(manifest),'candidate_handoff_ref':ref(CANDIDATE/'handoff-final.json'),'actual_argument_bindings':{k:ref(p) for k,p in inputs.items()},'proof_ref':ref(proof),'locator_sha256':locator_hash,'actual_received_at':message['received_at'],'canonical_at_review':{n:ref(ROOT/'execution/v2.4'/n) for n in ('step_state.json','checkpoint.json','path_ownership.json')},'checkpoint_revision':cp['revision'],'ownership_revision':ownership['revision'],'old_failure_counter_count':len(cp['failure_counters']),'old_parent_registration_records':cp['parent_tasks_accepted'],'W07_status':owner['status'],'W04_current_binding':ownership['card_path_bindings'].get('W04-99'),'tool_dependencies':[ref(ROOT/'execution/v2.4'/p) for p in ('formal_case_index.py','formal_profile_w07.py','parent_gate_ledger.py')],'controls_ref':ref(HERE/'controls-result.json'),'controls_raw_ref':ref(HERE/'controls.raw'),'controls_actual_exit':0,'controls_script_ref':ref(HERE/'synthetic_controls.py'),'source_optimized_compile':'PASS','assert_guards':0}
save(HERE/'audit.json',audit)
verdict={
 'schema':'researchos.w07.root-registration-helper-independent-review.v1',
 'reviewer_id':'codex:/root/w05_merge_review', 'issued_at':datetime.now(timezone.utc).isoformat(),
 'decision':'SOURCE_READY', 'failed':[], 'missing':[],
 'scope':'Exact Root-only registration helper source; no actual Root apply/recover, no product acceptance issuance or canonical mutation by reviewer.',
 'source_ref':ref(CANDIDATE/'issue_reviewed_current.py'), 'audit_ref':ref(HERE/'audit.json'),
 'checks':[
  {'id':'RAW_CAPTURE','status':'PASS','source_lines':[262,273],'actual':'Three canonical files each read once into original bytes, digest and strict JSON derived from those same bytes; duplicate keys/nonfinite rejected; immutable originals retained.'},
  {'id':'ACTUAL_DELIVERY','status':'PASS','source_lines':[274,339],'actual':'Reviewed final argv binds actual previously delivered reviewer message, review/proof SHA and canonical locator hash. Real envelope is retained rather than a fabricated event ID. _independent checks exact context/vector/run, distinct actual three actors, recipient/sender and ordered execution/context/review/received/observed/intent timestamps.'},
  {'id':'FULL_PENDING_VALIDATION','status':'PASS','source_lines':[340,389],'actual':'Exact frozen baseline plus current dependencies; full _vector/product/_dispatches/_global/_independent and reader.finish invoked before ACCEPTED owner construction; pending owner explicitly IN_PROGRESS. Existing context/review/issuance roots refused, not silently replaced.'},
  {'id':'HISTORY_PRESERVATION','status':'PASS','source_lines':[390,445],'actual':'W07 appends three roots and preserves entire prior evidence prefix; every other state row unchanged. Checkpoint and ownership are derived from current captured objects, preserving 116 historical origin counters, preexisting parent records, W04 scope/bindings and latest revisions. No hardcoded earlier metadata snapshot.'},
  {'id':'WRITE_BARRIER','status':'PASS','source_lines':[158,170,436,456],'actual':'Before each atomic os.replace, verify all three canonical hashes and frozen dependency snapshot; current target hash checked again. Original and desired bytes plus exact pending journal persist separately. Tested 0/1/2/3 write interruption restore against exact raw bytes.'},
  {'id':'RECOVERY','status':'PASS','source_lines':[185,251,525,568],'actual':'Only own desired bytes may restore original bytes; external/missing targets preserved and reported PARTIAL_REGISTRATION; corrupted archive fails before writes; OS replacement refusal stays PARTIAL; completed transaction refuses rollback. New exception origins immutable and retained with explicit subsequent Root checkpoint reconciliation obligation.'},
  {'id':'POSTDERIVE','status':'PASS','source_lines':[254,262,457,487],'actual':'Postwrite and final formal derivation require W07 VALID_ACCEPTED / A05 and input rechecks; actual parent ledger must independently include A05. Global PARTIAL from stale W04 is preserved. Historical parent registrations including gates-only entries are never presented as six fully current accepted parents.'},
  {'id':'COMPLETION','status':'PASS','source_lines':[488,516],'actual':'After receipt serialization and final rechecks, fsynced completion bytes are linked atomically using exclusive os.link insertion. Pending journal/issuance/registration/handoff alone are not completion. Synthetic NTFS duplicate marker insertion refused and completion recovery refused.'}
 ],
 'runtime_controls':{'classification':'SYNTHETIC_NOT_PRODUCT','actual_exit':0,'count':11,'result_ref':ref(HERE/'controls-result.json'),'raw_ref':ref(HERE/'controls.raw')},
 'required_operational_conditions':[
  'Root integrates this exact reviewed source SHA and uses its actual received-message argv; attestation authenticates external observation only because Root actually received it. JSON self-consistency alone is not delivery authentication.',
  'Root serial registration lease must cover all canonical writers; per-file replace is atomic, not a simultaneous three-file filesystem transaction. Pending intent remains incomplete until completed.json; crash recovery is explicit and hash-bound.',
  'Any new failure origin, including failed recovery, must be appended by Root on the next checkpoint reconciliation; exact rollback intentionally does not overwrite old counters to insert it.',
  'Actual apply must revalidate current inputs. This SOURCE_READY review does not grant permission to bypass a later input drift or unsuccessful final derive/ledger/recheck.'
 ],
 'formal_acceptance_delta':0,'canonical_changes_by_reviewer':0,'production_source_changes_by_reviewer':0,
 'independent_A05_review_ref':ref(inputs['review']), 'independent_A05_review_is_separate':True
}
save(HERE/'review.json',verdict)
inventory=[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='receipt-manifest.json']
save(HERE/'receipt-manifest.json',inventory)
print(json.dumps({'decision':'SOURCE_READY','review_ref':ref(HERE/'review.json'),'audit_ref':ref(HERE/'audit.json'),'source_ref':verdict['source_ref'],'receipt_manifest_ref':ref(HERE/'receipt-manifest.json'),'old_failure_counter_count':len(cp['failure_counters']),'checkpoint_revision':cp['revision'],'ownership_revision':ownership['revision']},ensure_ascii=False))
