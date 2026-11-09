import pathlib,json,hashlib,sqlite3,re,subprocess,datetime
MAIN=pathlib.Path("D:/作品集/ResearchOS/research-os");WT=MAIN/".local/worktrees/codex-w0599-model-stream";OUT=pathlib.Path(__file__).parent
D=WT/"execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/candidate-b8938f84655849b9847611dbf3440442"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {"path":p.relative_to(MAIN).as_posix(),"sha256":h(p)}
def write(n,v):p=OUT/n;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8");return ref(p)
hand=json.loads((D/"handoff.json").read_bytes())
fixture_roots=[WT/hand["final_runs"][1]["directory"]/"actual-fixtures",OUT/"replay-fixtures"]
dbs=[]
for root in fixture_roots:
 for p in sorted(root.glob("*/fixture.sqlite")):
  before=h(p);c=sqlite3.connect(p.as_uri()+"?mode=ro&immutable=1",uri=True)
  facts={}
  queries={
  "control_kinds":"SELECT kind,count(*) FROM client_control_receipts GROUP BY kind",
  "message_phases":"SELECT json_extract(body,'$.payload.phase'),count(*) FROM outbox WHERE json_extract(body,'$.kind')='MESSAGE' AND json_extract(body,'$.payload.role')='ASSISTANT' GROUP BY json_extract(body,'$.payload.phase')",
  "effect_latest":"SELECT json_extract(x.body,'$.state'),count(*) FROM resource_effects x WHERE x.sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) GROUP BY json_extract(x.body,'$.state')",
  "fence_states":"SELECT state,restore_fenced,count(*) FROM client_queue_fences GROUP BY state,restore_fenced",
  "runs":"SELECT json_extract(body,'$.status'),json_extract(body,'$.queue_empty'),json_extract(body,'$.children_stopped') FROM domain_objects WHERE kind='Run'",
  }
  for k,q in queries.items():facts[k]=c.execute(q).fetchall()
  transcript=[]
  for sid,aid in c.execute("SELECT id,transcript_artifact_id FROM client_sessions").fetchall():
   row=c.execute("SELECT body FROM domain_objects WHERE kind='Artifact' AND id=?",(aid,)).fetchone()
   if not row:continue
   a=json.loads(row[0]);b,hash_=c.execute("SELECT bytes,content_hash FROM uploaded_content WHERE storage_key=? AND sealed=1",(a["storage_key"],)).fetchone()
   assert "sha256:"+hashlib.sha256(b).hexdigest()==hash_==a["content_hash"]
   v=json.loads(b)
   transcript.append({"session":sid,"complete":v.get("complete"),"artifact_mode":a["measurement_mode"],"evidence_kind":a["evidence_kind"],"hash":hash_,"message_completeness":[m["complete"] for m in v["messages"]]})
  raw=p.with_name("provider-original.sse")
  confirmed_raw_matches=[]
  for (body,) in c.execute("SELECT body FROM resource_effects WHERE json_extract(body,'$.receipt.model_transport')=1"):
   x=json.loads(body);response=x["receipt"]["payload"].get("body","").encode()
   if response==raw.read_bytes():confirmed_raw_matches.append(x["key"])
  c.close();assert before==h(p)
  dbs.append({"path":str(p.relative_to(MAIN)),"sha256":before,"facts":facts,"transcripts":transcript,"provider_raw_sha256":h(raw),"confirmed_original_matches":confirmed_raw_matches,"immutable_read_only":True})
dbref=write("closed_fixture_graph_audit.json",{"queries":queries,"dbs":dbs,"private_database_read":False})
counts=[]
for name in ["core-controls","actual-causal-cancel","quarantine-alias-probe","semantic-quarantine-probe"]:
 raw=(OUT/(name+".stdout")).read_text(encoding="utf8")
 inv=json.loads((OUT/(name+".invocation.json")).read_bytes())
 counts.append({"name":name,"exit":inv["exit"],"inclusive":{s:len(re.findall(r"^\s*--- "+s+r":",raw,re.M)) for s in ["PASS","FAIL","SKIP"]},"top_level":{s:len(re.findall(r"^--- "+s+r":",raw,re.M)) for s in ["PASS","FAIL","SKIP"]},"raw":ref(OUT/(name+".stdout")),"invocation":ref(OUT/(name+".invocation.json"))})
legacy=json.loads((D/"legacy_comparison.json").read_bytes())
assert len(legacy["current_failures"])==len(legacy["baseline_failures"])==29 and legacy["current_pass"]==legacy["baseline_pass"]==66
origins=json.loads((D/"failure_origins.json").read_bytes())
failureinv=[]
for p in sorted((WT/"execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex").rglob("*invocation*.json")):
 v=json.loads(p.read_bytes())
 def visit(o):
  if isinstance(o,dict):
   if isinstance(o.get("exit"),int) and o["exit"]!=0:failureinv.append({"ref":ref(p),"exit":o["exit"]})
   for z in o.values():visit(z)
  elif isinstance(o,list):
   for z in o:visit(z)
 visit(v)
write("failure_origins_independent.json",{"candidate_failure_origins":ref(D/"failure_origins.json"),"nonzero_invocation_records":failureinv,"legacy":{"baseline_pass":66,"baseline_fail":29,"current_pass":66,"current_fail":29,"added_failure_ids":legacy["added_failure_ids"],"same_pass_ids":legacy["same_pass_ids"],"ref":ref(D/"legacy_comparison.json")},"own_expected_red_probes":[x for x in counts if x["exit"]!=0],"own_audit_errors":[{"script":"audit_integrity.py","exit":1,"reason":"actual prefix repo vs assumed worktree; original retained"},{"script":"audit_integrity_v2.py","exit":1,"reason":"safe blanket DB refusal hit two explicitly published fixture DBs; v3 permits only these two exact ref paths; stderr retained"}]})
checks=[
{"id":"T01/T08","verdict":"FAIL_NEW_P1","detail":"Byte/multiline/UTF8/bounds fixtures pass, but SDK semantic reasoning reconstruction bypasses quarantine. Three actual red Go subtests and actual frozen SDK controls prove the defect. No real secrets used."},
{"id":"T02/T03","verdict":"PASS_SCOPED_FIXTURE","detail":"Original six compiled CLI cases pass; independent actual causal40/cancel/commit-failure3 tests pass. Upstream waits exact committed SDK observation+sealed SQLite prefix+CLI arrival; ordinary effect remains STARTED. Pipelines and byte hashes are original archived evidence, not independently rerun."},
{"id":"T04","verdict":"PASS_SCOPED_FIXTURE","detail":"Whole-history reconstruction uses canonical CONSUMED custom identities and SDK order; intermediate stop requires a consumed next command; old default branch retained. Archived actual final proof and7 forgery controls independently replay pass; long201-history/partialCAS passes."},
{"id":"T05","verdict":"PASS_SCOPED_FIXTURE","detail":"Independent bridge strict-init/binding/integer/digest/duplicates/window/terminal controls pass. Aux seven keys and full13key binding distinct from ordinary ACK; initial SQLite receipt and actual pipe write checked. No claim of Go transport credits alone proving model/queue completion."},
{"id":"T06","verdict":"PASS_BOUNDED_CANCEL_JOIN_OPEN_FINALIZATION","detail":"Independent both arrival orders require same complete binding, body_hash, actual idle+queueempty and cancelled idle; foreign generation/process and false queue rejected. Actual CLI cancellation yields preserved prefix/UNKNOWN/END0. Existing SQL immutable-idempotency trigger blocks ACK->final update: OPEN, not repaired."},
{"id":"T07","verdict":"PASS_SCOPED_FIXTURE","detail":"Independent actual encrypted backup/restore of copied published interrupted fixture preserves observations and UNKNOWN/END0/fence;8 tamper cases with recomputed body hashes rejected. END requires original dispatch/Run settled/result artifact/raw SSE/SDK and canonical command facts; public REPORT labels not authority. This is no full provider crash matrix."},
{"id":"T09","verdict":"PASS_RELEVANT_SELECTORS_WITH_DECLARED_BASELINE_FAILURES","detail":"265 domain+bridge/188 CLI original actual counts exactly match raw, zero skip.39,053 inputs current=both before/after. Legacy same baseline66/29, historical W17/Linux/missing-Go/6skips retained; not full broad PASS."}
]
review={
"schema":"researchos.w05.streaming-combined-independent-source-review.v1","reviewer_id":"codex:/root/w05_merge_review","issued_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"decision":"NEEDS_FIX","candidate_commit":"0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837",
"handoff_ref":ref(D/"handoff.json"),"manifest_ref":ref(D/"manifest.json"),"source_manifest_ref":ref(D/"source_manifest.json"),"integrity_audit_ref":ref(OUT/"integrity_audit.json"),"commit_blobs_ref":ref(OUT/"commit_blobs.json"),"closed_fixture_audit_ref":dbref,
"source_integrity":{"actual_commit_blobs":444,"production_and_test_sources":18,"new_receipt_blobs":426,"manifest_entries_self_excluded":425,"verified_refs":437,"hash_failures":0,"source_vector":39053,"drift":0,"candidate_clean":True,"authorized_unchanged":"runtime_effect_wire_windows.go","inherited_js_sha":"0d50cea351f325f28ca5ee377eac36833768a28be42cf48ec0e50834c0ff6517","inherited_L01_sha":"072afeb88f1a2f028df1c99b55735b3c583c729e86b2a53b9e60e889e6a2c304"},
"reused_independent_reviews":[{"scope":"JS2 only","sha256":"86bef488d74e2aaa2be5b0ec783d9e991ec4af3f5bee55a56055f23c947dd6ba"},{"scope":"L01 only","sha256":"005b880289f30e3245c5cb0af096391375b55bf50218a2167dad0ac1b83025fd"}],
"independent_actual_replays":counts,"checks":checks,
"findings":[{
"id":"W05-STREAM-SR-01","severity":"P1_BLOCKER","title":"Quarantine tracks wire field names instead of SDK semantic concatenation, allowing protected secret reassembly",
"source":"internal/domain/runtime_model_stream.go:inspectJSON(658-706),Feed(743-774),Finish(777-789)",
"mechanism":"reasoning/reasoning_content/reasoning_text are separate quarantine tails, whereas fixed SDK ensureThinkingBlock at482 retains one block and its619-625 selected alias delta is concatenated. A secret split between aliases stays hidden only until Finish releases withheld terminal bytes; Finish checks original raw substring, which cannot see decoded cross-field concatenation. Also reasoning_details consecutive reasoning.text.text and reasoning.summary.summary merge in SDK appendOpenAIReasoningDetail252-263; quarantine does not accumulate either field and may release the first prefix immediately.",
"actual_evidence":[ref(OUT/"quarantine-alias-probe.stdout"),ref(OUT/"semantic-quarantine-probe.stdout"),ref(OUT/"actual-sdk-semantic-probe.stdout"),ref(OUT/"sdk_reasoning_alias_probe.stdout")],
"actual_result":"Go exact source overlay refused none of three protected synthetic-secret vectors (red expected-safety assertion, exit1). Actual fixed0.87.1 SDK with local in-memory Response and direct network disabled reconstructs full synthetic secret in thinking or thinkingSignature for all3, stopReason stop, exit0 for counterexample confirmation. Alias 249-byte vectors match exact SHA c0b785a5a12d4c3924a34c767e9e430217e96372dfe7d00df1ecfec73dda657e; detail variants differ only JSON property order between Go and JS probes, explicitly not claimed byte-identical. No real credential read or exposure.",
"impact":"Violates T08 before-SDK secret quarantine. Escaped/delta-split host credential material can reach worker SDK memory/result, and opaque replay signatures can persist/replay. Existing private-stream non-public thinking policy does not cure the crossing into worker/evidence. Do not merge candidate as source-ready.",
"minimum_fix_scope":[{"path":"internal/domain/runtime_model_stream.go","bounds":"Align bounded secret accumulation with fixed SDK's actual selected reasoning alias and semantic detail merge rules; cover raw/decoded byte boundaries and other SDK-concatenated lanes. Preserve original bytes and frozen ceilings. Finish must not release a withheld suffix that reconstructs a secret in SDK-visible strings."},{"path":"internal/domain/runtime_model_stream_test.go","bounds":"Add exact alias-switch/alias-priority and reasoning.text/summary merge controls, JSON escapes, UTF8/read/event splits, harmless diverging-prefix progress and terminal handling."},{"path":"apps/cli/cli_model_stream_integration_windows_test.go","bounds":"Extend actual SDK fixture provider/secret negative controls to prove semantic split cannot reach worker stdout/result/canonical evidence or END; preserve existing6 tests/assertions."}],
"protected_fix_boundaries":"No fixed SDK/JS2 commit/schema/public protocol/migration changes; do not solve by labeling all thinking unsupported or buffering all benign stream until EOF. If semantic parser choice needs another source path, ask Root for exact amendment. Fix source belongs executor after Root registration, never reviewer.",
"fix_completion":"All three red safety cases must become real pre-downstream refusal and original benign causal streaming still progress; actual fixed SDK semantic positives establish fidelity; rerun affected quarantine/CLI negative + original causal/cancel/restore/verifier selectors under new full combined vector. Keep this failed candidate/raw immutable and add new handoff/proof."}],
"declared_open_product_gates":["CANCEL idempotency ACKNOWLEDGED to final SQL immutable trigger conflict remains OPEN; this slice only joins trusted abort/idle facts.","No paid provider/LIVE_MODEL qualification or W05/A04/parent acceptance.","Historical W17/current resource/Linux and legacy29 failures remain separately recorded, never greened.","Future provider binding/high-thinking work and L04 SQL23 are not part of this review."],
"failure_origins_ref":ref(OUT/"failure_origins_independent.json"),"writes":"own independent receipt namespace only; Go overlay never changes candidate files, all mutations by tests confined to test-created/copied fixtures","private_credentials_or_holdout_read":False,"paid_provider_calls":0,"canonical_registry_writes":0,"formal_acceptance_delta":0}
write("source_review.json",review)
manifest=[]
for p in sorted(OUT.rglob("*")):
 if p.is_file() and p.name!="review_manifest.json":manifest.append({"path":p.relative_to(MAIN).as_posix(),"sha256":h(p),"bytes":p.stat().st_size})
write("review_manifest.json",{"self_excluded":True,"files":manifest})
print(json.dumps({"review":ref(OUT/"source_review.json"),"manifest":ref(OUT/"review_manifest.json"),"counts":counts,"closed_fixture_count":len(dbs)},ensure_ascii=False))

