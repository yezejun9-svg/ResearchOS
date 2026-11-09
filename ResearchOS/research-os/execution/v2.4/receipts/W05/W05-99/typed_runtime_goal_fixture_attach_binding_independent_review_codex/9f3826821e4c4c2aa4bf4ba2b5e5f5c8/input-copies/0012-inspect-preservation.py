import ast,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
Q3=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49")
T=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1")
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
utility=B/"typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931/construct.py"
names={"tokens","balanced","close_index","call_nodes","assertion_if_nodes"}
nodes=[n for n in ast.parse(utility.read_text(encoding="utf-8")).body if isinstance(n,ast.FunctionDef) and n.name in names]
ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(utility),"exec"),ns)
rows=[]
for name in ["runtime_permission_windows_test.go","runtime_tool_integration_windows_test.go","runtime_session_events_windows_test.go","client_protocol_goal_test.go"]:
 old=ns["tokens"]((Q3/"candidate-root/internal/domain"/name).read_text(encoding="utf-8"))
 new=ns["tokens"]((P/"candidate-root/internal/domain"/name).read_text(encoding="utf-8"))
 oldnodes=ns["assertion_if_nodes"](old);newnodes=ns["assertion_if_nodes"](new)
 def strict(node):return any(node[i:i+3]==("t",".",kind) for i in range(len(node)-2) for kind in ("Fatal","Fatalf","Error","Errorf"))
 strict_old=[n for n in oldnodes if strict(n)];strict_new=[n for n in newnodes if strict(n)]
 rows.append({"file":name,"all_lexical_nodes_byte_token_equal":oldnodes==newnodes,"strict_nodes_byte_token_equal":strict_old==strict_new,"lexical_count":len(oldnodes),"strict_count":len(strict_old),"fmt_only":len(oldnodes)-len(strict_old)})
result={"rows":rows,"lexical":sum(r["lexical_count"] for r in rows),"strict":sum(r["strict_count"] for r in rows),"fmt_only":sum(r["fmt_only"] for r in rows)}
with (P/"assertion-inspection.json").open("x",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2);f.write("\n")
paths=[T/"internal/domain/v24_sessions.go",T/"migrations/sqlite/next_v24_sessions.sql",T/"internal/domain/contracts/client.protocol.schema.json",Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md"),Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/client.protocol.schema.json")]
supplement={"inputs":[ref(p) for p in paths]}
with (P/"sourceguard.supplemental.initial.json").open("x",encoding="utf-8",newline="\n") as f:json.dump(supplement,f,ensure_ascii=True,indent=2);f.write("\n")
print(json.dumps(result,ensure_ascii=True))

