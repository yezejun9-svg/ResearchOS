from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=PRIOR.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assertions=read(OUT/'assertions.json');assert len(assertions)==33 and all(x['status']=='PASS' for x in assertions)
command=read(OUT/'command.json');assert command['exit_code']==0 and command['domain_decoder_unchanged']
consumer=ROOT/'execution/receipts/W06/runtime-s2/root-integration/consumer-1524356';receipt=read(consumer/'receipt.json');assert receipt['exit_code']==0 and set(receipt['passed'])=={'TestW16C20','TestW10NativePair'}
for name,wanted in receipt['files'].items():assert sha(consumer/name)==wanted
native=read(consumer/'native-execution.json');assert len(native['sandbox_receipts'])==2
for row in native['sandbox_receipts']:assert isinstance(row['process_created_ns'],str) and int(row['process_created_ns'])>2**53 and row['children_stopped'] and row['streams_drained'] and row['cleanup_complete']
acceptance=read(consumer/'native-acceptance.json');assert acceptance['verdict']=='PASS' and acceptance['measurement_mode']=='FIXTURE'
author=read(OUT/'author-evidence/receipt.json');assert author['exit_code']==0
root_refs=[]
for directory in ['consumer-349631f','consumer-diagnostic','consumer-1524356']:
 base=consumer.parent/directory
 for path in sorted(base.rglob('*')):
  if path.is_file():root_refs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
put(OUT/'root-consumer-evidence.json',{'files':root_refs,'new_consumer_head':receipt['head'],'new_consumer_exit_code':0,'new_consumer_tests':receipt['passed'],'native_creation_identities':[r['process_created_ns'] for r in native['sandbox_receipts']],'native_acceptance_verdict':acceptance['verdict'],'measurement_mode':'FIXTURE','earlier_failures_preserved':True})
report={
 'artifact_kind':'INDEPENDENT_ASYNC_IDENTITY_SERIALIZATION_REVIEW','verifier':'codex:/root/evolution_verifier',
 'verdict':'PASS_ASYNC_BOUNDARY_IDENTITY_FIX','source_revision':'a7608ad49906b174506e2198073415a4483f8408',
 'integrated_revision':receipt['head'],
 'scope':'Exact identity JSON serialization and nested domain.Decode consumer compatibility only; retains native slice scope and grants no full S2 or LIVE acceptance.',
 'findings':[],
 'resolved_root_integration_finding':{'priority':'P1','cause':'Nanosecond Windows creation identity was an int64 encoded as a JSON number outside the exact canonical-number domain. Strict domain.Decode rejected nested native execution receipts.','fix':'Only Receipt.Created and Identity.Created JSON tags add ,string; Go storage remains int64 and the strict domain decoder is unchanged.'},
 'validation':{'independent_command_exit_code':0,'independent_assertions_pass':33,'tested_exact_values':['0','9007199254740993','1790787239271034300','9223372036854775807'],'paths':['json.Marshal nested execution -> domain.Decode -> exact string','nested object -> canonical.JSON -> typed Receipt/Identity int64','decoded nested execution -> marshal -> domain.Decode','legacy lossy JSON numeric timestamp still rejected'],'root_consumer_tests_hash_verified':receipt['passed'],'root_consumer_native_receipts_verified':2,'author_identity_and_real_native_test_exit':0,'full_native_matrix_rerun':False},
 'prior_reviews_unchanged':read(OUT/'source-audit.json')['prior_indices'],
 'root_consumer_evidence_reference':'root-consumer-evidence.json',
 'limitations':['The two integration consumer reruns were performed by root and independently reconciled here; this reviewer executed the additional nested exact-value tests.','The original queue-deadline failure and both earlier native-slice reviews are unchanged. The new root integration failure, diagnostic record and fixed consumer evidence are separately hash-referenced.','No production service, database, provider, real holdout, LIVE runtime or whole S2 coordinator/bridge was activated or accepted.'],
 'whole_S2_accepted':False,'LIVE_qualified':False,'BOUNDED_AUTO_granted':False,
}
put(OUT/'review.json',report)
(OUT/'review.md').write_text('# Native identity serialization repair\n\nVerdict: **PASS_ASYNC_BOUNDARY_IDENTITY_FIX** at `a7608ad` (integrated `1524356`).\n\nBoth native creation-time fields now serialize as decimal strings while retaining Go int64 values. Independent tests passed 33 assertions through nested domain.Decode, canonical JSON and typed round trips, including 2^53+1 and MaxInt64. The original lossy numeric form still fails the unchanged strict decoder.\n\nRoot\'s W10 NativePair and W16 C20 consumer reruns passed; their raw file hashes, two string-valued native receipt identities and FIXTURE acceptance record were reconciled. Prior failure records remain preserved. This is a serialization/consumer compatibility repair, not full S2 or LIVE acceptance.\n',encoding='utf-8')
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='index.json'];put(OUT/'index.json',{'source_revision':report['source_revision'],'files':files})
for row in files:assert sha(OUT/row['path'])==row['sha256']
print(json.dumps({'verdict':report['verdict'],'review_sha256':sha(OUT/'review.json'),'index_sha256':sha(OUT/'index.json'),'files':len(files)}))
