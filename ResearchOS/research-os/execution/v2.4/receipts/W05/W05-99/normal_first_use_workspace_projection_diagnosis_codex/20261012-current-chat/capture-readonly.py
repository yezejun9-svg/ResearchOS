import sqlite3,json,pathlib,datetime,hashlib,subprocess,sys
repo=pathlib.Path(r"D:/作品集/ResearchOS/research-os")
p=repo/".local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite"
c=sqlite3.connect(p.as_uri()+"?mode=ro",uri=True)
c.execute("PRAGMA query_only=ON")
c.execute("BEGIN")
result={"captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"database_path":str(p),"access":{"uri_mode":"ro","query_only":bool(c.execute("PRAGMA query_only").fetchone()[0]),"transaction":"read transaction"}}
queries={
 "workspace_bindings":("SELECT id,revision,json_extract(body,'$.authorized_workspace_ref'),json_extract(body,'$.display_name'),json_extract(body,'$.status'),json_extract(body,'$.project_id') FROM domain_objects WHERE project='' AND kind='WorkspaceBinding' ORDER BY id",["id","revision","authorized_workspace_ref","display_name","status","project_id"]),
 "model_configuration_revisions":("SELECT model_config_ref,config_revision FROM host_model_configurations ORDER BY model_config_ref",["model_config_ref","config_revision"]),
 "counts":("SELECT (SELECT count(*) FROM client_sessions),(SELECT count(*) FROM domain_objects WHERE kind='Task'),(SELECT count(*) FROM domain_objects WHERE kind='Run'),(SELECT count(*) FROM resource_effects),(SELECT count(*) FROM idempotency WHERE operation='v2:session.create')",["client_sessions","tasks","runs","resource_effects","session_create_commands"])}
result["queries"]={}
for name,(query,columns) in queries.items():
 result["queries"][name]={"query":query,"columns":columns,"rows":[dict(zip(columns,row)) for row in c.execute(query).fetchall()]}
query="SELECT operation,key,body,created_at FROM idempotency WHERE operation IN ('v2:workspace.register','v2:project.bootstrap','v2:host.status','v2:workspace.list','v2:session.create') ORDER BY created_at,key"
receipts=[]
for operation,key,body,created_at in c.execute(query):
 x=json.loads(body); r=x.get("result") or {}
 safe={"operation":operation,"command_id":key,"created_at":created_at,"status":x.get("status"),"body_sha256":hashlib.sha256(body.encode("utf-8")).hexdigest(),"body_hash_basis":"exact persisted UTF-8 text from idempotency.body; original body is not exported"}
 for field in ("project_id","authorized_workspace_ref"):
  if field in r: safe[field]=r[field]
 if "workspaces" in r: safe["workspaces_count"]=len(r["workspaces"])
 receipts.append(safe)
result["existing_command_receipts"]={"query":query,"safe_projection":receipts}
c.rollback();c.close()
base="84d6fc0f2018404170ec3fa4295c56cf4453a15a"
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo).decode().strip()
paths=["internal/api/v2.go","internal/api/server.go","internal/domain/client_protocol.go","internal/domain/client_protocol_sessions.go","internal/domain/client_protocol_first_use.go","internal/domain/project_workspace.go","apps/web/src/workbench.jsx"]
source=[]
for rel in paths:
 b=subprocess.check_output(["git","show",base+":"+rel],cwd=repo)
 a=subprocess.check_output(["git","show",head+":"+rel],cwd=repo)
 source.append({"path":rel,"diagnosed_commit":base,"diagnosed_blob_sha256":hashlib.sha256(b).hexdigest(),"current_commit":head,"current_blob_sha256":hashlib.sha256(a).hexdigest(),"unchanged":b==a})
result["source_comparison"]=source
assert all(s["unchanged"] for s in source if s["path"]!="apps/web/src/workbench.jsx"), "Core source changed after diagnosis"
print(json.dumps(result,ensure_ascii=False,indent=2))
