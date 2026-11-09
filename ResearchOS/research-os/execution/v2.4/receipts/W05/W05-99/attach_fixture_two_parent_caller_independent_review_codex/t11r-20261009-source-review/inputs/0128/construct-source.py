"""Q5 file-only construction. No Go, database, model or native execution."""
import ast,json,hashlib,difflib,re
from pathlib import Path
P=Path(__file__).resolve().parent
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
Q3=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49")
Q4=B/"typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e"
ATT3=B/"session_attach_restore_time_revision_codex/att3-1a11e02f790732395c39325fbb4668d"
REVIEW=B/"session_attach_restore_time_independent_review_codex/7b81fec959684c2a9de9b0e475479c27"
T=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1")
def ref(p):
 raw=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def new(n,b):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b)
def out(n,obj):new(n,(json.dumps(obj,ensure_ascii=True,indent=2)+"\n").encode())
def verify(pin):
 actual=ref(Path(pin["path"]));assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"],pin["path"]
fixed=[
 (Q3/"HDF.json","d6ab61e0522ae7f4cae0621e73a648e046ccfe9a4372c2f3848a93f5fc279658",9879),
 (Q3/"MF.json","d6d631ceac02968a7884a278e21358ee6d3c59d55fa158acd5801a10caf81138",None),
 (Q4/"HDF.json","3eaeaf6219589c36b13fa730e3e4cfb0a42b2bba016bb6cf6f5b6eafc9be44c0",13062),
 (Q4/"MF.json","dd7615e9b9f5f2584089c07180d7f0da00a3c787e5450565b345e56ed7e66707",8002),
 (ATT3/"HDF.json","028d441d592cff04167ae92c742f401a1bc8230cce873b08428064f0698b03b8",6615),
 (ATT3/"MF.json","4ecc03cd01ef131592ee4f899b8a2f2f5776b42a3ec6e22889fa57e88b09ac2e",5789),
 (REVIEW/"HDF.json","16773c9c272354533218607aeadbfeaa0013118bcd0e9ff8f588b5b3facba9f3",4467),
 (REVIEW/"MF.json","bccefe5d25a951d96f58f492312a740d71cb51acb7487852b38662deae87098c",27537),
 (ATT3/"candidate-root/internal/domain/client_protocol.go","bbf0d1442b9ca5211e3069dc180911273b906476f4b88a29872cf66d66f9192e",57574)]
guard=[]
for p,h,n in fixed:
 pin=ref(p);assert pin["sha256"]==h and (n is None or pin["bytes"]==n);guard.append(pin)
manifest_counts={}
for root in (Q3,Q4,ATT3,REVIEW):
 members=json.loads((root/"MF.json").read_bytes())["members"]
 if isinstance(members,dict):members=list(members.values())
 manifest_counts[str(root)]=len(members)
 for pin in members:verify(pin);guard.append(ref(Path(pin["path"])))
# Pin exact T6 public contracts and helper dependencies without loading Go.
for name in ["client_protocol.go","client_protocol_sessions.go","client_protocol_journal.go","client_protocol_events.go","contracts.go","client_protocol_configuration_test.go","client_protocol_control_windows_test.go"]:
 guard.append(ref(T/"internal/domain"/name))
for name in ["client_protocol_goal_test.go","runtime_permission_windows_test.go","runtime_tool_integration_windows_test.go","runtime_session_events_windows_test.go","runtime_typed_client_fixture_windows_test.go"]:
 guard.append(ref(T/"internal/domain"/name))
utility=B/"typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931/construct.py"
guard.append(ref(utility))
# Execute only explicitly selected pure Python lexical utilities, never module top-level.
tree=ast.parse(utility.read_text(encoding="utf-8"))
names={"tokens","balanced","close_index","call_nodes","assertion_if_nodes"}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert {n.name for n in nodes}==names
ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(utility),"exec"),ns)
payload=json.loads((P/"source-input.json").read_bytes())
originals=["runtime_permission_windows_test.go","runtime_tool_integration_windows_test.go","runtime_session_events_windows_test.go","client_protocol_goal_test.go"]
helper="runtime_typed_client_fixture_windows_test.go"
changes={};source_refs=[];checks=[]
for name in originals+[helper]:
 base=Q3/"candidate-root/internal/domain"/name
 raw=base.read_bytes();old=raw.decode();code=old;edits=[]
 def replace(before,after):
  global code
  assert code.count(before)==1,(name,before,code.count(before))
  at=code.index(before);edits.append({"position":at,"before":before,"after":after})
  code=code[:at]+after+code[at+len(before):]
 if name==helper:
  assert ref(base)["sha256"]=="3a976a38a53ec0e9a4a884c43c52a32e7396bbcab37eef7be1dd47949aab7654"
  at=old.index("func attachTypedRuntimeFixture(")
  replace(old[at:],payload["helper"]+payload["tests"])
 elif name!="client_protocol_goal_test.go":
  client={"runtime_permission_windows_test.go":"permission-client","runtime_tool_integration_windows_test.go":"mu-client","runtime_session_events_windows_test.go":"event-client"}[name]
  service="svc" if name=="runtime_session_events_windows_test.go" else "service"
  call='attachTypedRuntimeFixture(t, f, '+service+', created, "'+client+'")'
  replace(call,"attached := "+call)
  # Only the first session.send literal immediately following this attach changes.
  call_start=code.index("attached := "+call)
  send_start=code.index('Method: strptr("session.send")',call_start)
  line_start=code.rfind("\n",call_start,send_start)+1
  line_end=code.index("\n",send_start)
  old_line=code[line_start:line_end]
  new_line=old_line.replace('ClientID: strptr("'+client+'"), ProjectID: &f.project, SessionID: created.SessionID',
      'ClientID: &attached.OwnerClientID, ProjectID: &attached.ProjectID, SessionID: &attached.SessionID')
  new_line=new_line.replace("ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1)","ExpectedRevision: &attached.Revision, WriterEpoch: &attached.WriterEpoch")
  assert old_line!=new_line and "revPtr(1)" not in new_line and "&attached.SessionID" in new_line
  replace(old_line,new_line)
 inverse=code
 for c in reversed(edits):
  at=c["position"];assert inverse[at:at+len(c["after"])]==c["after"]
  inverse=inverse[:at]+c["before"]+inverse[at+len(c["after"]):]
 assert inverse.encode()==raw
 old_tokens=ns["tokens"](old);new_tokens=ns["tokens"](code);assert ns["balanced"](new_tokens)
 if name in originals:
  old_calls=ns["call_nodes"](old_tokens);new_calls=ns["call_nodes"](new_tokens);assert old_calls==new_calls
  old_ifs=ns["assertion_if_nodes"](old_tokens);new_ifs=ns["assertion_if_nodes"](new_tokens)
  # Nested assertion-containing if nodes may contain the updated first-send
  # input. Their inverse is checked above; strict assertion body text remains.
  old_names=re.findall(r"func (Test\w+)\(t \*testing.T\)",old)
  new_names=re.findall(r"func (Test\w+)\(t \*testing.T\)",code);assert old_names==new_names
  assert len(old_ifs)==len(new_ifs)
  checks.append({"file":name,"exact_inverse":True,"old_calls":len(old_calls),"new_calls":len(new_calls),"assertion_or_error_if":len(old_ifs),"Test_names":old_names,"all_assertion_calls_exact_equal":True,"only_fixture_input_edits":True,"edits":len(edits),"byte_equal":old==code})
 else:
  assert old[:old.index("func attachTypedRuntimeFixture(")]==code[:code.index("type typedRuntimeFixtureWriter struct")]
  checks.append({"file":name,"strict_JSONL_child_TLS_configuration_profile_provider_resource_prefix_byte_equal":True,"old_attach_replaced_only":True,"new_tests":re.findall(r"func (Test\w+)\(t \*testing.T\)",code)})
 new("candidate-root/internal/domain/"+name,code.encode())
 new(name+".patch","".join(difflib.unified_diff(old.splitlines(True),code.splitlines(True),fromfile=str(base),tofile="candidate-root/internal/domain/"+name)).encode())
 changes[name]=edits
 source_refs.append(ref(P/"candidate-root/internal/domain"/name))
 guard.append(ref(base))
unique={}
for pin in guard:unique[pin["path"]]=pin
guard=list(unique.values())
out("sourceguard.initial.json",{"authority":"NONE","inputs":guard,"manifest_member_counts":manifest_counts})
out("source-refs.json",{"refs":source_refs,"production_members":0})
out("source-replacements.json",changes)
out("static-preservation.json",{"mode":"Python lexical only; not Go AST","checks":checks,"original_totals":{"calls":sum(x.get("old_calls",0) for x in checks),"Test_names":sum(len(x.get("Test_names",[])) for x in checks),"assertion_or_error_if":sum(x.get("assertion_or_error_if",0) for x in checks)},"Go_SQL_native_model_executed":False})
print(json.dumps({"source_root":str(P),"source_refs":source_refs,"guard_inputs":len(guard),"preservation":checks},ensure_ascii=True))

