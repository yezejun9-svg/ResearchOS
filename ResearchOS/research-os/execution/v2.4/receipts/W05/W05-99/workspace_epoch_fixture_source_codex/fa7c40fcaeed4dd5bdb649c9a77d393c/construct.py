import ast,collections,difflib,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c")
T5=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
CAUSE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/remaining_full_failure_cause_review_codex/8c83a215358ce0e859da44f08b8a69d3")
UTIL=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931")
def pin(p):
 b=p.read_bytes();return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(name,value):
 p=Q/name;p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(value,bytes):
  with p.open("xb") as f:f.write(value)
 else:
  raw=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+"\n"
  with p.open("x",encoding="utf-8",newline="\n") as f:f.write(raw)
def replace_one(text,before,after):
 assert text.count(before)==1,before
 return text.replace(before,after,1)
source=T5/"internal/domain/client_workspace_test.go"
base=pin(source)
assert (base["sha256"],base["bytes"])==("d8d13327ea74eecee58911b8923acce7d3e212d32d91144a12c78663eaa4c7c8",11638)
raw=source.read_bytes();old=raw.decode("utf-8")
header="func clientWorkspaceFixtureFor(t *testing.T, f *fixture) (*fixture, *ClientService, *clientWorkspacePort, *WorkspaceBinding, string) {\n\tt.Helper()\n"
new_header=header+'''\treturn clientWorkspaceFixtureForEpoch(t, f, 1)
}

// Synthetic mapped current-state fixture, not accepted historical handoff proof.
// MapClientSession persists epoch, writer and lease on the same Session row.
func clientWorkspaceFixtureForEpoch(t *testing.T, f *fixture, writerEpoch int64) (*fixture, *ClientService, *clientWorkspacePort, *WorkspaceBinding, string) {
\tt.Helper()
\tif writerEpoch < 1 {
\t\tt.Fatal("workspace fixture requires a positive writer epoch")
\t}
'''
revised=replace_one(old,header,new_header)
revised=replace_one(revised,"Revision: 1, WriterEpoch: 1, WriterClientID: b.ClientID","Revision: 1, WriterEpoch: writerEpoch, WriterClientID: b.ClientID")
start=revised.index("func TestClientWorkspaceImportExactBytesReplayAndEpoch(")
end=revised.index("func TestClientWorkspaceTruncatedDiffSealsFullBytes(",start)
body=revised[start:end]
body=replace_one(body,"\tf, svc, port, b, sid := clientWorkspaceFixture(t)\n",'''\tconst currentEpoch int64 = 2
\tconst oldEpoch int64 = 1
\tf, svc, port, b, sid := clientWorkspaceFixtureForEpoch(t, contextFixture(t), currentEpoch)
\tvar mappedEpoch, mappedRevision int64
\tvar mappedWriter, mappedProject, mappedWorkspace, mappedLease string
\tif err := f.db.QueryRow("SELECT writer_epoch,revision,writer_client_id,project_id,workspace_ref,lease_expires_at FROM client_sessions WHERE id=?", sid).Scan(&mappedEpoch, &mappedRevision, &mappedWriter, &mappedProject, &mappedWorkspace, &mappedLease); err != nil {
\t\tt.Fatal(err)
\t}
\texpires, leaseErr := time.Parse(time.RFC3339Nano, mappedLease)
\tif leaseErr != nil || !expires.After(time.Now().UTC()) || mappedEpoch != currentEpoch || mappedRevision != 1 || mappedWriter != b.ClientID || mappedProject != f.project || mappedWorkspace != b.AuthorizedRef {
\t\tt.Fatalf("mapped current writer fixture is not coherent: epoch=%d revision=%d writer=%q project=%q workspace=%q lease_error=%v", mappedEpoch, mappedRevision, mappedWriter, mappedProject, mappedWorkspace, leaseErr)
\t}
''')
body=replace_one(body,'\tenv := workspaceTestEnvelope(f, sid, "artifact.import", body)\n','\tenv := workspaceTestEnvelope(f, sid, "artifact.import", body)\n\tenv.WriterEpoch = revPtr(currentEpoch)\n')
body=replace_one(body,'\tenv.WriterEpoch = revPtr(0)\n','\tenv.WriterEpoch = revPtr(oldEpoch)\n')
anchor='\tenv = workspaceTestEnvelope(f, sid, "artifact.import", body)\n\tres, replay := executeWorkspaceTest(t, f, svc, env)\n'
body=replace_one(body,anchor,'\tenv = workspaceTestEnvelope(f, sid, "artifact.import", body)\n\tenv.WriterEpoch = revPtr(currentEpoch)\n\tres, replay := executeWorkspaceTest(t, f, svc, env)\n')
revised=revised[:start]+body+revised[end:]
scope_old=old[old.index("func TestClientWorkspaceImportExactBytesReplayAndEpoch("):old.index("func TestClientWorkspaceTruncatedDiffSealsFullBytes(")]
utilities=ast.parse((UTIL/"construct.py").read_text(encoding="utf-8"))
wanted={"tokens","close_index","call_nodes","assertion_if_nodes","balanced"}
pure=[v for v in utilities.body if isinstance(v,ast.FunctionDef) and v.name in wanted]
assert {v.name for v in pure}==wanted
ns={};exec(compile(ast.Module(body=pure,type_ignores=[]),str(UTIL/"construct.py"),"exec"),ns)
ots,nts=ns["tokens"](old),ns["tokens"](revised)
oldcalls,newcalls=ns["call_nodes"](ots),ns["call_nodes"](nts)
oldifs,newifs=ns["assertion_if_nodes"](ots),ns["assertion_if_nodes"](nts)
assert all(collections.Counter(newcalls)[v]>=n for v,n in collections.Counter(oldcalls).items())
assert all(collections.Counter(newifs)[v]>=n for v,n in collections.Counter(oldifs).items())
names=lambda s:re.findall(r"^func (Test\w+)\(t \*testing\.T\)",s,re.M)
assert names(old)==names(revised)
assert ns["balanced"](nts)
scope_calls=ns["call_nodes"](ns["tokens"](scope_old))
scope_ifs=ns["assertion_if_nodes"](ns["tokens"](scope_old))
for name in names(old):
 if name=="TestClientWorkspaceImportExactBytesReplayAndEpoch":continue
 prefix="func "+name+"("
 old_start=old.index(prefix);new_start=revised.index(prefix)
 def body_span(text,offset):
  ts=ns["tokens"](text[offset:]);brace=next(i for i,t in enumerate(ts) if t[0]=="{");close=ns["close_index"](ts,brace,"{","}")
  return text[offset:offset+ts[close][2]]
 assert body_span(old,old_start)==body_span(revised,new_start),name
for original_function in ("workspaceTestEnvelope","executeWorkspaceTest","clientWorkspaceFixture"):
 prefix="func "+original_function+"("
 assert body_span(old,old.index(prefix))==body_span(revised,revised.index(prefix)),original_function
default_body=old[old.index(header)+len(header):old.index("func (p *clientWorkspacePort) WorkspaceWrite(")]
current_body=revised[revised.index(new_header)+len(new_header):revised.index("func (p *clientWorkspacePort) WorkspaceWrite(")]
assert current_body.replace("WriterEpoch: writerEpoch","WriterEpoch: 1")==default_body
assert body.count("revPtr(currentEpoch)")==2 and body.count("revPtr(oldEpoch)")==1
assert "revPtr(0)" not in body
dest=Q/"candidate-root/internal/domain/client_workspace_test.go"
new(dest.relative_to(Q).as_posix(),revised)
new("client_workspace_test.patch","".join(difflib.unified_diff(old.splitlines(keepends=True),revised.splitlines(keepends=True),fromfile=source.as_posix(),tofile=dest.as_posix())))
deps=[source,T5/"internal/domain/client_protocol.go",T5/"internal/domain/v24_sessions.go",T5/"internal/domain/client_workspace.go",CAUSE/"manifest.json",CAUSE/"report.md",CAUSE/"report.json",CAUSE/"source-pins.json",UTIL/"construct.py"]
new("base-refs.json",{"authority":"NONE","refs":[pin(p) for p in deps],"root_base":"T5 immutable","current_fixture_epoch":2,"default_other_fixture_epoch":1,"negative_epoch":1,"revision":1})
new("source-refs.json",{"authority":"NONE","refs":[pin(dest)],"production_member_count":0,"changed_test_member_count":1})
checks={"authority":"NONE","formal_acceptance":False,"source_file_count":1,"scope_test":"TestClientWorkspaceImportExactBytesReplayAndEpoch","original_all_file_assertion_calls":len(oldcalls),"original_scope_assertion_calls":len(scope_calls),"original_all_file_assertion_or_error_if_nodes":len(oldifs),"original_scope_assertion_or_error_if_nodes":len(scope_ifs),"original_top_level_tests":len(names(old)),"all_original_calls_and_if_nodes_preserved":True,"all_test_names_order_preserved":True,"all_other_test_bodies_byte_equal":True,"default_shared_helper_maps_epoch1":True,"parameterized_shared_helper_body_identical_except_MapWriterEpoch":True,"workspace_envelope_and_execute_helpers_byte_equal":True,"current_DB_epoch2_revision1_same_row_valid_writer_workspace_project_lease_checked":True,"current_import_envelopes_positive_epoch2":True,"negative_old_epoch1_nonzero":True,"original_revision2_bytes_replay_noIO_ARTIFACTcount_assertions_preserved":True,"Go_lexical_delimiters_balanced":True,"Go_AST_compile_native_SQL_model_execution":0,"new_mechanical_failures":[],"failure_counter_reset":False,"evidence_kind":"SYNTHETIC_CURRENT_STATE_FIXTURE_NOT_HISTORICAL_HANDOFF"}
new("static-checks.json",checks)
print(json.dumps({"namespace":Q.as_posix(),"source":pin(dest),"static_checks":pin(Q/"static-checks.json"),"diff":pin(Q/"client_workspace_test.patch"),"assertion_counts":checks,"authority":"NONE","formal_acceptance":False},ensure_ascii=False))
