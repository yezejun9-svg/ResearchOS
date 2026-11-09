from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
prep=json.loads((ROOT/'PREPARATION.json').read_bytes())
diagnostics=prep['diagnostics']+[
 {'raw_chunk_id':'512bc7','outer_exit_code':0,'inner_rg_exit_code':2,'classification':'CHILD_READ_ONLY_LOCATOR_GUESSED_ABSENT_PATH','message':'Child guessed contracts/domain.schema.json. Actual client.protocol.domain.schema.json was then discovered and read; no product/test effect.'}
]
report={
 'schema':'researchos.production-binding-initial-independent-review.v1',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/implementation_review',
 'decision':'REQUIRES_CHANGES',
 'reviewed_source_status':'OLD_PRE_REVISION_FREEZE_PINS_ONLY_AUTHOR_NOW_AUTHORIZED_TO_REVISE',
 'base_head':'b84b065739d64a61407ca815651880b6c06ae36a',
 'source_sha256':{
  'internal/domain/coding_delivery_binding.go':'1b99704523bd51aaa526b80da091083df2d53ce969a6e609323fb4fa2749d526',
  'internal/domain/coding_delivery_binding_store.go':'e372077b4d13ba66eed15273eae8ebea5bd1b63edc6bda1f61b86e72bf048ce3',
  'internal/domain/coding_delivery_binding_test.go':'ca295a001cefafcb101006105db1b317d72a152cf2aaceba36048dbebc7cfffb',
  'internal/domain/contracts/coding_delivery_bindings.sql':'4efd532f6e24d62afba12710db2848ed1fadd94f29c45505b31429361b0d1aad'
 },
 'source_pin_readback_chunk':'af34f9',
 'findings':[
  {
   'id':'PDB-001','severity':'P1','blocking':True,
   'title':'Canonical Task origin/candidate live in NoProgressRecord, not Task',
   'candidate_source':'coding_delivery_binding_store.go:211-212; coding_delivery_binding_test.go:57-63',
   'baseline_sources':['internal/domain/operations.go:210-235','internal/domain/contracts/client.protocol.domain.schema.json:$defs.Task','$defs.NoProgressRecord'],
   'evidence':'createTask computes inputHash=Hash(input_refs), legacyKey=Hash([origin_problem_id,candidate_id,inputHash]); stores origin/candidate/input_hash/key_hash in NoProgressRecord; explicitly removes origin/candidate from Task and stores only Task.no_progress_record_id. Public Task is closed, requires that reference and forbids the two extra fields. Frozen binding store directly reads the forbidden Task fields, while its test hand-injects them and creates no canonical NoProgressRecord.',
   'effect':'The old positive fixture is not a public-schema-valid Task. Normal canonical Tasks cannot pass this foundation relationship check; conversely fake extra Task fields substitute for the unverified canonical NoProgressRecord.',
   'required_change':'Within the four-file scope, follow Task.no_progress_record_id inside the same Tx to the same-project NoProgressRecord; validate public Goal/Task/NPR shapes and exact row/body identity, Goal problem/task roster, origin/candidate, input_hash, recomputed unchanged legacy key, binding.NoProgressRef and NoProgressInputKey. Do not add Task fields, change public schema/API/legacy NoProgress policy or introduce a migration. Complete public-schema-valid three-object fixtures are sufficient; a full API/createTask invocation is not required.'
  },
  {
   'id':'PDB-002','severity':'P1','blocking':True,
   'title':'Required checker command identity is confused with display check_id',
   'candidate_source':'coding_delivery_binding_store.go:181-199',
   'evidence':'mandatory values are executable command keys such as mu.turn-output-v1 and coding.pure-scalar-delivery-v1, but required membership is stored by check_id without checking command_key. A schema-valid self-digested contract can retain the same check_id while changing command_key to an unrelated handler. Existing valid client turn contracts use check_id=mu-turn-output and command_key=mu.turn-output-v1.',
   'effect':'The foundation can accept absence/substitution of its mandatory execution checker and reject legitimate distinct labels. The old fixtures set id and key equal, masking the distinction.',
   'required_change':'Bind mandatory presence to the explicitly intended required DETERMINISTIC command_key (or an explicitly specified id/key policy), reject duplicate/ambiguous occurrences including optional duplicates, retain unique display check_id checks and full public AcceptanceContract schema/digest validation. This does not register or execute a checker.'
  }
 ],
 'independent_regression_source':{'path':str(ROOT/'independent_relationship_test.go'),'sha256':sha(ROOT/'independent_relationship_test.go'),'status':'PREPARED_NOT_RUN_AWAITING_NEW_FINAL_FREEZE','coverage':['Three complete schema-valid Goal/Task/NPR positive objects with typed VersionRefs; Task has no origin/candidate extras.','Canonical NPR relation, fake Task extras, Goal rosters and self-consistent forged legacy key negatives.','Wrong command under the old matching label, legal independent labels under right command, optional/required duplicate command identity.','Actual existing domain.Hash, causal anchor dimensions, exact closed DTO escaped duplicate/case alias, context cancellation and rolled-back Tx.','Existing nonzero NoProgress failure/progress counters remain unchanged by binding insert/read.']},
 'author_vet':{'status':'UNKNOWN_PRESERVED','reason':'Parent confirmed attempt04 vet command/stdout/stderr exist but vet.result absent and process gone. No replay or fabricated terminal result.'},
 'independent_tests':{'status':'NOT_RUN_OLD_SOURCE_REVISION_UNFROZEN','reason':'Confirmed structural blockers handed to original author; no tests run against changing source.'},
 'independent_vet':{'status':'PENDING_NEW_FINAL_FREEZE','exit_code':None,'ref':None},
 'not_a_blocker_but_required_limits':['No trusted Host producer/current authority/approval journal/cross-DB lineage is proved.','Production schema adoption and backup/restore inventory/integrity are unsupported; no registration caller, new migration/API/503 or SDK output changes allowed.','No product or business acceptance is granted by foundational field/table checks.'],
 'diagnostics':diagnostics,
 'operations':{'four_source_mutations':0,'tests_run':0,'old_db_connections':0,'native_model_calls':0,'counter_reset':False,'formal_increment':0},
 'formal_increment':0
}
c=ROOT/'initial-blocker-review.json'
d=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding/reviews/relationship-and-command-blockers-01.json')
data=(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
for path in (c,d):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(data)
print(json.dumps({'C':str(c),'D':str(d),'sha256':sha(d),'decision':report['decision']},ensure_ascii=False))
