"""Read existing W07 delivery and guards; no collection, source-copy or registration."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,re,subprocess

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
BASE=ROOT/'execution/v2.4/receipts/W07/W07-99'
ISS=BASE/'integration_codex/current-issuance-42e43e7d0c464ddba5b4020fbeb1199b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(name,value):
    with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def resolve(r):
    p=(ROOT/r['path']).resolve();assert p.is_relative_to(ROOT)
    assert sha(p)==r['sha256'].removeprefix('sha256:'),(r['path'],'HASH_MISMATCH')
    return p
helper=BASE/'integration_codex/issue_reviewed_current.py'
profile=ROOT/'execution/v2.4/formal_profile_w07.py'
index=ROOT/'execution/v2.4/formal_case_index.py'
amend=ROOT/'execution/v2.4/receipts/W04/W04-99/revalidation_scope_review_codex/e4e2caf5-70e2-4568-86e0-1611eb0dee5a/acyclic_transition_scope_amendment.json'
statepath=ROOT/'execution/v2.4/step_state.json';state=read(statepath)
owner=next(row for row in state['steps'] if row['id']=='W07-99')
save('observed-owner.json',{'state_ref':ref(statepath),'owner':owner,'observed_at':datetime.now(timezone.utc).isoformat()})
roots={};nonroots=[]
schemas={'researchos.w07.current-context.v1':'context','researchos.w07.independent-review.v1':'review','researchos.w07.root-observed-issuance.v1':'issuance'}
for r in owner['evidence']:
    absolute={'path':'execution/v2.4/'+r['path'],'sha256':r['sha256']};p=resolve(absolute);data=read(p)
    if data.get('schema') in schemas:
        key=schemas[data['schema']];assert key not in roots;roots[key]=absolute
    else:nonroots.append(r)
assert set(roots)=={'context','review','issuance'} and len(nonroots)==3
context=read(resolve(roots['context']));review=read(resolve(roots['review']));issuance=read(resolve(roots['issuance']))
messagepath=resolve(issuance['delivery_ref']);message=read(messagepath)
proof=read(resolve(context['proof_ref']));completed=read(ISS/'completed.json');journal=read(resolve(completed['journal_ref']))
registration=read(resolve(completed['registration_ref']));resolve(completed['handoff_ref'])
assert issuance['context_ref']==roots['context']==review['context_ref']
assert issuance['review_ref']==roots['review']==message['review_ref']
assert review['proof_ref']==context['proof_ref'] and review['version_vector']==context['version_vector']
assert message['event_locator']['message_content_sha256']==hashlib.sha256(message['content'].encode()).hexdigest()
assert roots['review']['sha256'] in message['content'] and context['proof_ref']['sha256'] in message['content']
binding=read(ISS/'observed-delivery-binding.json')
assert binding['message_ref']==binding['raw_event_ref']==issuance['delivery_ref']
assert binding['event_locator']==message['event_locator']
assert completed['canonical_sha256']==registration['desired_sha256']
for item in journal['files']:
    resolve(item['original_ref']);p=resolve(item['desired_ref'])
    assert completed['canonical_sha256'][item['path']]==item['desired_sha256']
    if item['path'].endswith('/step_state.json'):
        historical_owner=next(row for row in read(p)['steps'] if row['id']=='W07-99');assert owner==historical_owner
times=[proof['ended_at'],context['created_at'],review['issued_at'],message['received_at'],issuance['observed_at'],owner['accepted_at'],completed['at']]
assert times==sorted(times)
chain={'status':'READ_ONLY_EXISTING_CHAIN_LINKS_VERIFIED_NOT_NEW_ACCEPTANCE','active_roots':roots,'nonroot_evidence_preserve_in_order':nonroots,
 'review_fields':{k:v for k,v in review.items() if k not in ('version_vector','assertion_verdicts','gate_verdicts')},
 'issuance':issuance,'received_message':message,'observed_delivery_binding':binding,'completed':completed,'journal_ref':ref(ISS/'pending-journal.json'),
 'original_root_helper_ref':journal['script_ref'],'old_owner_equals_historical_desired_row':True,'time_order':times,
 'bound_refs_verified':[roots[k] for k in ('context','review','issuance')]+[ref(messagepath),ref(ISS/'completed.json'),ref(ISS/'observed-delivery-binding.json')],
 'scope_limit':'Verified listed existing chain/hash/time links. Does not rerun product tests or claim full recursive raw/SQL semantic revalidation.'}
save('actual-old-chain.json',chain)
vector=context['version_vector'];catalog={}
for group in ('spec_files','source_files','input_files','lock_files','tool_files'):
    rows=vector[group]
    catalog[group]={'count':len(rows),'row_key_shapes':dict(Counter(','.join(sorted(r)) for r in rows)),
        'hash_kinds':dict(Counter('sha256:prefixed' if r['sha256'].startswith('sha256:') else 'bare_hex_sha256' if re.fullmatch('[0-9a-f]{64}',r['sha256']) else 'OTHER' for r in rows)),
        'rows':rows}
save('old-vector-catalog.json',{'context_ref':roots['context'],'version_vector_schema':vector['schema'],'groups':catalog,'source_coverage':context['source_coverage'],
 'product_hash_inventory_refs':{'source_before_ref':proof['source_before_ref'],'source_after_ref':proof['source_after_ref'],'version_vector_ref':proof['version_vector_ref'],'compilation_inputs_ref':proof['compilation_inputs_ref'],'live_binary_ref':proof['live_binary_ref']},
 'old_context_has_execution_source_snapshot':'execution_source_snapshot' in context,
 'observed_capture_directory_names':sorted(p.name for p in resolve(context['proof_ref']).parent.iterdir()),
 'archive_caution':'This catalogue copies JSON refs only, not source bytes. Root may now archive existing bytes only on exact original SHA match and public-source confinement; label capture provenance honestly.'})
guards=[]
for path,needles in [(helper,['"OWNER_STATE"','"COMPETING_ROOT"','"PARENT_ALREADY_REGISTERED"','"OLD_EVIDENCE_CHANGED"']),
                     (index,['"CONFLICTING_REVIEW" if']),
                     (profile,['"REVIEW_PROOF", "W07"','"COMMAND_REVISION", ident)'])]:
    lines=path.read_text(encoding='utf-8').splitlines()
    for needle in needles:
        hits=[i for i,line in enumerate(lines) if needle in line];assert hits,needle
        for i in hits:
            start=max(0,i-3);end=min(len(lines),i+2)
            guards.append({'source_ref':ref(path),'line_start':start+1,'line_end':end,'text':'\n'.join(lines[start:end])})
save('actual-helper-guards.json',guards)
assert sha(helper)=='b65d2a363c513e0bbdec8659f96a0f19f3fe140a39d28f39e5590170b62bb250'
assert sha(amend)=='ba95eb6c1608ea201ac40aed1988d023b556d1ae4238aeba396d512508890d65'
save('proposal.json',{
 'schema':'researchos.w07.current-revalidation-scope-proposal.v1','status':'READ_ONLY_FUTURE_SCOPE_NOT_AUTHORIZED_IMPLEMENTATION','actor':'codex:/root/sources_parent_impl','created_at':datetime.now(timezone.utc).isoformat(),
 'main_head_observed':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
 'problem':'W04 future r40 command rebinding changes an exact pinned W07 input and actual dispatcher revision; old A05 remains historical accepted but current applicability becomes NEEDS_REVALIDATION. The first-issuance helper cannot apply twice.',
 'existing_guards':{'helper_ref':ref(helper),'first':'OWNER_STATE refuses existing ACCEPTED owner before root inspection.','second':'COMPETING_ROOT refuses each existing W07 current-context/independent-review/root-observed-issuance schema.','third':'PARENT_ALREADY_REGISTERED refuses existing W07 parent registration.','additional':'Existing helper preserves all old evidence as prefix; adding new3 without replacing old3 violates unchanged formal _registered_roots exact-one rule. No state downgrade/root deletion workaround.'},
 'actual_old_chain_ref':ref(OUT/'actual-old-chain.json'),'source_catalog_ref':ref(OUT/'old-vector-catalog.json'),'guard_ref':ref(OUT/'actual-helper-guards.json'),
 'minimal_future_source_scope':[
 'execution/v2.4/receipts/W07/W07-99/integration_codex/revalidation-<exclusiveUUID>/register.py',
 'execution/v2.4/receipts/W07/W07-99/integration_codex/revalidation-<sameUUID>/test_register.py'],
 'unchanged_sources':['execution/v2.4/receipts/W07/W07-99/integration_codex/issue_reviewed_current.py','execution/v2.4/formal_case_index.py','execution/v2.4/formal_profile_w07.py','execution/command_dispatcher/dispatch.py','ops/ci/sources.py','all product source/threshold/schema/contract files'],
 'why_new_helper':'Keep the independently accepted b65 first-registration and its failure/rollback tests immutable. New bounded Root transition helper explicitly handles historical owner migration; it must not globally exempt the existing three guards or semantic supersession refusal.',
 'archive_protocol':[
 'Before r40, Root preserves exact r39 registry bytes and the complete observed canonical W07 row/full state bytes, all6 direct evidence refs, actual3 active roots, original times/actors, old completed marker, journal/desired canonical snapshots/registration, actual received message and observed binding. Archive uses a distinct historical-registration schema; never relabel old roots/review.',
 'Archive complete old proof/context/vector/GLOBAL/native receipt originals and canonical dispatch stdout/stderr, raw source reports/binary/build/go-list/H07 snapshots, independent semantic verdicts. Hash all closure references and check actual review->message->issuance->owner->completed lineage, including recorded hash prefixes. No timestamps alone or self-authored replacement message establish delivery.',
 'Old W07 source-before/after are hash inventories, not W04-style execution_source_snapshot. Root may now append source snapshots in a new archive namespace, explicitly describing Root archival now of existing public bytes. Each copied byte stream must equal its old bound SHA; preserve actual original path and acquisition provenance. Never edit old proof to add snapshot claims.',
 'The catalogue gives all five vector groups and coverage rules. Constrain archival to repository/public source and locked public tool/dependency inputs, reject symlink escapes/private DB/secrets/canary material. Where source changed, only a previously same-SHA archive or exact trusted Git blob with recorded object/commit provenance is eligible. Missing originals are a blocker, never repair old hashes. Mutable current physical inputs cannot stand in for historical bytes.',
 'Historical check validates old acceptance against its original bytes and actual old delivery evidence, not current r40 filesystem. Keep all original failures and no new historical PASS fabrication; a hash-only or unresolved old graph is insufficient to apply transition.' ],
 'old_W07_format_requirements':{'issuance_schema':'researchos.w07.root-observed-issuance.v1','actual_fields':['context_ref','review_ref','delivery_ref','observed_at','run_id','actor','executor_id','reviewer_id'],
 'delivery_schema':'researchos.root-received-independent-message.v1','actual_fields_delivery':['recorded_by','recipient','sender','event_type','review_ref','received_at','content','event_locator','recording_note'],
 'observed_event':'Root original message is also raw_event_ref; event_locator has source/task_name/sender_task/message_type/message_content_sha256, with no platform message ID. Do not import W04 message_id/channel/current_context_ref assumptions.'},
 'semantic_guard':[
 'Compare stable applicability inputs: frozen spec/baseline, actual source paths+hashes, registry/selector bindings, locks/tools/environment/policy and real request/window inputs. Run UUID, new timestamps, copying receipts or different output self-paths alone are not a changed applicability vector.',
 'Old accepted verdict remains accepted for its original applicability. Same meaningful applicability plus conflicting semantic decision, unresolved failed/missing old review, missing actors, ambiguous roots or changed frozen modes/thresholds requires separate conflict resolution and blocks this helper.',
 'No supersedes_review_refs added to v1 review. No suppression of unknown/competing direct roots; _registered_roots must still reject duplicate context/review/issuance.' ],
 'new_execution_chain':[
 'After final source/tooling/registry freeze and separate Root authorization, fresh unique MAIN 3 actual public sources + exact 13 H07 injected DB snapshots, full Go dependency inventory before/after and actual tool versions/binary/build records. Preserve each failure and legitimate BLOCKED/PARTIAL; no fixture relabel as LIVE.',
 'Actual registered G01/G02/H07/A05 native4 at new registry revision, with original argv/cwd/exits and canonical raw; G01 actual source inventory exactly matches fresh live. Preserve old86 proof/native4 untouched.',
 'New immutable full context/version-vector/tool identity/GLOBAL4, exact coverage inventories, raw A05 five assertions and gate semantics; current strict _vector/product/_dispatches/_global and Reader.finish pass.',
 'Distinct real executor, independent reviewer and Root; actual independent full review containing new context/proof SHA, then real message received by Root and new Root issuance referencing delivery_ref. No self-created independent review, future timestamps or synthetic ACCEPTED owner.' ],
 'transparent_transition':{'reference_protocol_ref':ref(amend),'stable_row':'Freeze full future W07 row with exact new3 roots replacing exact old3, preserving existing3 non-root refs in order and appending distinct historical archive ref. Preserve old actor/time fields in archive and explicitly allowed lineage fields; no other row mutation.','slots':[{'name':'self_plan_ref','location':'One final W07 evidence element','resolution':'Append exact plan path + raw SHA after plan frozen, not a fake hash/self-reference inside signed bytes.'},{'name':'actual_apply_time','location':'W07 accepted_at','resolution':'Root runtime UTC after actual new product review delivery and actual transition review delivery; preserve complete required ordering.'}],
 'independent_review':'Bind exact plan raw SHA, stable-row canonical digest, helper/test SHA, original full-state CAS/old chain, new vector/new chain, removed3/added3 and both slot rules. Root actually receives plan-bound reviewer message. Transition review/message hashes do not enter proposed row and create a cycle; later commit receipt links them.',
 'apply':'Under Root serial writer lease recheck all hashes/coverage/current inputs and exact full-state CAS. Resolve only two slots; persist PENDING exact resolved-row intent, atomic replacements with per-write CAS and append-only journal. Verify read-back full row and all unaffected owner rows, unchanged historical counters/parent records. Existing W07 parent record is preserved, not appended/count-incremented.',
 'completion':'Unchanged formal/profile/current parent ledger on actual new row, input recheck, Root commit receipt and exclusive completion marker; independent registered audit verifies final slot resolution/time/rowhash. Pending journal is not acceptance. Recovery never overwrites a foreign concurrent edit.'},
 'future_metadata_scope':'Only exact W07-99 state row transition plus Root-authorized checkpoint/path-ownership append/update through reviewed CAS protocol. Preserve other rows, prior failure counters/origins and historical accepted parent list. Registry remains unchanged during W07 replay/transition. This proposal grants no metadata write permission.',
 'future_receipt_scopes':{'Root':'integration_codex/revalidation-UUID/** plus explicit source archive namespace','executor':'source_executor_codex/new run/current-context UUID namespaces only','independent':'new W07 independent revalidation UUID; distinct actual owner'},
 'negative_controls':['Owner/root ambiguity, one old root omitted/hash changed or unknown extra root => refuse','Old review/proof/message SHA mismatch, changed original content/locator, wrong sender/recipient, time-only guessed delivery => refuse','r39 snapshot missing or source bytes not matching old SHA => refuse archive/current transition','Same stable vector conflicting review, changed baseline/mode/threshold or unresolved blocker => refuse','New reviewer equals executor/Root casefold, missing actual review delivery => refuse','Any field/evidence order changed outside frozen template and two slots, duplicate/third resolver => refuse','New registry/source/raw/helper drift or CAS mismatch => no apply; unrelated state changes require regenerated plan','A05 doubled in current count or duplicate W07 parent appended => refuse','Partial transaction, missing completed marker, foreign modification during recovery => no current acceptance','Read-back row/accepted_at differs from exact resolved intent or precedes either delivery => refuse'],
 'counts':'Future successful revalidation restores CURRENT A05 as one case with five assertions/three gate rows and four native dispatches. Old applicability archive adds zero accepted cases and zero historical parent records.',
 'limitations':['This task emits scope advice only, not a helper, archival source copies, new network capture, replay issuance or state mutation.','No claim of generic semantic supersession support; explicit reviewed transition authenticates selection of one active applicability graph.','W04 two-slot scope is a reference, not automatic W07 authorization. Independent W07 scope review and Root registration precede implementation.']})
save('inspection-result.json',{'status':'READ_ONLY_SCOPE_PROPOSAL_COMPLETE','proposal_ref':ref(OUT/'proposal.json'),'chain_ref':ref(OUT/'actual-old-chain.json'),'catalog_ref':ref(OUT/'old-vector-catalog.json'),'guards_ref':ref(OUT/'actual-helper-guards.json'),'guard_source_sha256':sha(helper),'old_direct_root_count':len(roots),'old_nonroot_count':len(nonroots),'current_product_calls':0,'source_copies':0,'source_edits':0,'canonical_edits':0,'new_acceptance_count':0})
print(json.dumps({'proposal':ref(OUT/'proposal.json'),'result':ref(OUT/'inspection-result.json'),'catalog':ref(OUT/'old-vector-catalog.json')},ensure_ascii=False))
