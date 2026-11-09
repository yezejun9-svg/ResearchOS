from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys
sys.stdout.reconfigure(encoding='utf-8');R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/worktrees/codex-w0599-host-configuration-upgrade';O=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec';N=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex';C='c82f73cc6699b564f1357472e2859b90cafe6b0a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
B=N/'old22-build-40e94f3f6e53442fa07068089c0de64a';v=json.loads((B/'source_before.json').read_text(encoding='utf-8-sig'));bad=[]
for p,h in v.items():
 p=Path(p)
 if not p.is_file() or sha(p)!=h:bad.append({'path':str(p),'expected':h,'actual':sha(p) if p.is_file() else None})
record=json.loads((B/'git_source.json').read_text(encoding='utf-8-sig'));proc=subprocess.Popen(['git','--no-replace-objects','-C',str(W),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);bound=[]
for p,h in record['files'].items():
 proc.stdin.write((record['commit']+':'+p+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().decode().split();raw=proc.stdout.read(int(head[2]));proc.stdout.read(1);assert hashlib.sha256(raw).hexdigest()==h;bound.append(p)
proc.stdin.close();proc.wait();save('source22_git_and_current_audit.json',{'compiled_inputs':len(v),'current_drift':bad,'source_files_bound_to_git':len(bound),'commit':record['commit'],'files':bound})
rows=[]
for p in sorted((N/'closure-6e184bfb0e35426ab6f38707d3eeb5eb/actual-fixtures').rglob('*.sqlite')):
 before=sha(p);db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
 versions=[x[0] for x in db.execute('select version from schema_migrations order by version')];tables=[x[0] for x in db.execute("select name from sqlite_master where type='table' order by name")];count={}
 for t in ['host_model_configurations','host_model_config_heads','client_command_identities','client_sessions','client_command_queue','client_control_receipts','idempotency','effect_executions']:
  if t in tables:count[t]=db.execute('select count(*) from "'+t+'"').fetchone()[0]
 integrity=db.execute('pragma integrity_check').fetchone()[0];fk=list(db.execute('pragma foreign_key_check'));db.close();assert sha(p)==before
 rows.append({'path':str(p),'sha256':before,'versions':versions,'counts':count,'integrity':integrity,'foreign_key_violations':fk,'unchanged':True})
save('latest_closed_public_db_audit.json',{'files':rows,'reads':'ro immutable only; row counts/schema/integrity, no vault/private holdout'})
save('tooling_diagnostics.json',{'origins':[{'id':'configuration-independent-9673a59f-read-cwd-3f336d','tool_chunk_id':'3f336d','actual_command':'Get-Content execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec/static_source_freeze.json -TotalCount 12','actual_cwd':str(W),'observed_error':'Cannot find path in peer worktree because independent receipt resides in MAIN','shell_exit':0,'cause':'Read-only reviewer wrong cwd; PowerShell nonterminating error followed by successful directory statistics','product_failure':False,'count_once':True,'original_tool_output_locator':'functions exec tool chunk 3f336d'}]})
print(json.dumps({'old22_inputs':len(v),'drift':len(bad),'bound_git':len(bound),'closed_public_db':len(rows)}))
