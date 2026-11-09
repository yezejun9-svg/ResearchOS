"""Seal Q5 Source and close public input guards; no Go/native/SQL/model actions."""
import ast,json,hashlib,re
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parent.parent
Q3=B/"typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49"
Q4=B/"typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e"
ATT3=B/"session_attach_restore_time_revision_codex/att3-1a11e02f790732395c39325fbb4668d"
REVIEW=B/"session_attach_restore_time_independent_review_codex/7b81fec959684c2a9de9b0e475479c27"
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def out(n,obj):
 with (P/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write("\n")
def verified(pin):
 actual=ref(Path(pin["path"]))
 assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"],pin["path"]
 return actual
assert ref(P/"failure-origin.845.json")["sha256"]=="ecba74f5cd81851e11963d74182b85ac3c593bbe6454ec7560bedc3238adfbbd"
inputs=json.loads((P/"sourceguard.initial.json").read_bytes())["inputs"]
inputs+=json.loads((P/"sourceguard.supplemental.initial.json").read_bytes())["inputs"]
q4=json.loads((Q4/"HDF.json").read_bytes())
q4_inputs=q4["source_input_refs"]+[q4["actual_ref"]]
for pin in q4_inputs:verified(pin)
out("sourceguard.inherited-actual-inputs.json",{"provenance":"Exact immutable Q4 HDF source_input_refs and actual_ref; Python int JSON parsing preserves 64-bit integers","inputs":q4_inputs})
inputs+=q4_inputs
unique={}
for pin in inputs:
 actual=verified(pin);unique[actual["path"]]=actual
inputs=list(unique.values())
utility=B/"typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931/construct.py"
names={"tokens","balanced","close_index","call_nodes","assertion_if_nodes"}
nodes=[n for n in ast.parse(utility.read_text(encoding="utf-8")).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert {n.name for n in nodes}==names
ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(utility),"exec"),ns)
source_refs=json.loads((P/"source-refs.json").read_bytes())["refs"]
edits=json.loads((P/"source-replacements.json").read_bytes())
for pin in source_refs:
 verified(pin)
 path=Path(pin["path"]);text=path.read_text(encoding="utf-8")
 assert ns["balanced"](ns["tokens"](text))
 inverse=text
 for change in reversed(edits[path.name]):
  at=change["position"];assert inverse[at:at+len(change["after"])]==change["after"]
  inverse=inverse[:at]+change["before"]+inverse[at+len(change["after"]):]
 assert inverse.encode()==(Q3/"candidate-root/internal/domain"/path.name).read_bytes()
preservation=json.loads((P/"static-preservation.json").read_bytes())
assert preservation["original_totals"]=={"calls":181,"Test_names":20,"assertion_or_error_if":196}
inspection=json.loads((P/"assertion-inspection.json").read_bytes())
assert inspection["lexical"]==196 and inspection["strict"]==190 and inspection["fmt_only"]==6
assert all(row["all_lexical_nodes_byte_token_equal"] and row["strict_nodes_byte_token_equal"] for row in inspection["rows"])
helper=P/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go"
code=helper.read_text(encoding="utf-8")
old=(Q3/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go").read_text(encoding="utf-8")
assert old[:old.index("func attachTypedRuntimeFixture(")]==code[:code.index("type typedRuntimeFixtureWriter struct")]
assert "InsecureSkipVerify" not in code
assert 'deref(reply.Status) != "COMPLETED"' in code
assert 'ValidateResultAgainstMethod("session.attach", reply, doc)' in code
assert 'snapshot, err := typedRuntimeFixtureSnapshotBinding(doc, raw)' in code
assert 'muClientCall(t, f, service, env)' in code and 'again, replay := handlerCommand(t, f, service, env)' in code
assert 'decoder.DisallowUnknownFields()' in code
assert 'ExpectedRevision: revPtr(before.Revision)' in code
assert 'after.Writer.Epoch-before.Writer.Epoch != 1' in code
assert 'after.Revision-before.Revision != 2' in code
assert 'after.EventSequence-before.EventSequence != 1' in code
assert 'int64(9007199254740993)' in code
for name in ["runtime_permission_windows_test.go","runtime_tool_integration_windows_test.go","runtime_session_events_windows_test.go"]:
 text=(helper.parent/name).read_text(encoding="utf-8")
 assert text.count("attached := attachTypedRuntimeFixture(")==1
 assert text.count("ExpectedRevision: &attached.Revision, WriterEpoch: &attached.WriterEpoch")==1
 assert text.count("ClientID: &attached.OwnerClientID, ProjectID: &attached.ProjectID, SessionID: &attached.SessionID")==1
goal=helper.parent/"client_protocol_goal_test.go"
assert goal.read_bytes()==(Q3/"candidate-root/internal/domain/client_protocol_goal_test.go").read_bytes()
assert '(name == "expired_lease" || name == "missing_lease") && deref(reply.ErrorCode) != "LEASE_EXPIRED"' in goal.read_text(encoding="utf-8")
new_tests=re.findall(r"func (Test\w+)\(t \*testing.T\)",code)
assert new_tests==["TestTypedRuntimeFixtureAttachRejectsAlteredTerminal","TestTypedRuntimeFixtureAttachTransitionUsesExactGeneration"]
legacy=next(pin for pin in inputs if pin["path"].endswith("client_protocol_control_windows_test.go"))
assert '"ACKNOWLEDGED"' in Path(legacy["path"]).read_text(encoding="utf-8")
out("final-static-checks.json",{"mode":"PURE_PYTHON_GO_LEXICAL_AND_EXACT_TEXT_NOT_GO_AST","source_files":5,"production_source_files":0,"changed_original_runtime_files":3,"edits_each":2,"Goal_byte_equal":True,"entire_Q3_JSONL_child_TLS_configuration_profile_provider_resource_prefix_byte_equal":True,"original_calls":181,"original_Test_names":20,"original_assertion_or_error_if":196,"original_strict_t_assertion_if":190,"original_fmt_Errorf_only_if":6,"all_original_call_and_if_token_sequences_equal":True,"all_sources_inverse_byte_equal":True,"new_helper_tests":new_tests,"new_helper_tests_executed":False,"typed_int64_fields_and_above_2pow53_Source_vectors":True,"wildcard_or_ACK_promotion_added":False,"native_SQL_Go_model_executed":False})
closed=[{"expected":pin,"actual":verified(pin),"unchanged":True} for pin in inputs]
out("sourceguard.final.json",{"scope":"public frozen Source/contract/receipt inputs; Root canonical progress excluded","entry_count":len(closed),"all_unchanged":True,"entries":closed})
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
out("MF.json",{"schema":"researchos.typed-runtime-attach-binding-source-manifest.v1","authority":"NONE","formal_acceptance":False,"members":members,"exclusions":["MF.json","HDF.json"],"reason":"MF excludes its own digest and the HDF which pins MF; actual seal tool result is delivered externally"})
out("HDF.json",{"schema":"researchos.typed-runtime-attach-binding-source-handoff.v1","status":"SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_BUILD_AND_TEST","authority":"NONE","formal_acceptance":False,"production_ready":False,"self_approved":False,"actor_id":"codex:/root/command_queue_impl","namespace":str(P),"candidate_root":str(P/"candidate-root"),"source_refs":source_refs,"manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),"report_ref":ref(P/"report.md"),"base_Q3_HDF":ref(Q3/"HDF.json"),"base_Q3_MF":ref(Q3/"MF.json"),"blocked_Q4_HDF":ref(Q4/"HDF.json"),"blocked_Q4_MF":ref(Q4/"MF.json"),"required_ATT3_production":ref(ATT3/"candidate-root/internal/domain/client_protocol.go"),"ATT3_review_HDF":ref(REVIEW/"HDF.json"),"ATT3_review_MF":ref(REVIEW/"MF.json"),"ATT3_review_scope":"SOURCE_ONLY_APPROVE_WITH_FRESH_POSITIVE_BLOCKED","replacements_ref":ref(P/"source-replacements.json"),"static_checks_ref":ref(P/"final-static-checks.json"),"original_assertions_ref":ref(P/"assertion-inspection.json"),"sourceguard_initial_ref":ref(P/"sourceguard.initial.json"),"sourceguard_final_ref":ref(P/"sourceguard.final.json"),"sourceguard_inputs":len(closed),"tool_io_ref":ref(P/"original-tool-io.json"),"failure845_ref":ref(P/"failure-origin.845.json"),"mechanical_failures":[{"ordinal":845,"actualOuter":1,"actualPython":None,"native":None}],"failure_counter_reset":False,"original_inventory":{"calls":181,"Test_names":20,"assertion_or_error_if":196,"strict_t_assertion_if":190,"fmt_Errorf_only_if":6},"changes":{"helper":"original COMPLETED/AttachResult + actual binding/lease + original committed event + exact replay; prefix unchanged","runtime_files":3,"input_edits_each":2,"Goal":"byte-identical including LEASE_EXPIRED","production_members":0},"historical_T6_results":{"source":"Q4 pinned Root actual receipt, unchanged","Sources":49,"selected_parents":25,"PASS":61,"FAIL":6,"SKIP":0,"native_attach_failing_leaves":8,"new_actual_claimed":False},"legacy_scope":{"file":legacy,"test":"TestClientSameWriterRenewsExpiredLease","current_expected":"ACKNOWLEDGED","required_contract":"real COMPLETED/AttachResult; preserve epoch2, future lease, old revision VERSION_CONFLICT","modified_here":False,"root_separate_composition_required":True},"positive_restore_acceptance":"BLOCKED/PENDING_ROOT_RESOURCE","open_branches":["active asynchronous takeover","historical cached ACK terminal reconciliation","true fresh restore positive","shared TEXT dependent whole-chain acceptance"],"actions":{"Go_AST_compile_test_gofmt":False,"SQL_native_model_private":False,"Main_canonical_T6_old_Source_write":False},"root_required":["independent Q5 Source review","fresh isolated composition of approved ATT3 plus Q5 and separate legacy test correction","actual Go compile and original/new tests with strict JSONL and exit reconciliation","descendant Go Job lease closure and independent actual review"],"STOP":True})
for name,pin in members.items():assert ref(P/name)==pin
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"sources":source_refs,"sourceguard":ref(P/"sourceguard.final.json"),"guard_inputs":len(closed),"failure845":ref(P/"failure-origin.845.json"),"members":len(members),"new_mechanical_failures":[845],"source_only":True},ensure_ascii=True))

