package api
import (
 "context"
 "database/sql"
 "encoding/json"
 "net/http/httptest"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "time"
 "researchos.local/research-os/internal/domain"
 "researchos.local/research-os/internal/store"
)
func auditDB(t *testing.T) (*sql.DB,*domain.Service,string) {
 t.Helper()
 root:="D:/作品集/ResearchOS/research-os"
 db,err:=store.Open(filepath.Join(t.TempDir(),"audit.sqlite")); if err!=nil{t.Fatal(err)};t.Cleanup(func(){db.Close()})
 if err=store.Bootstrap(context.Background(),db,filepath.Join(root,"migrations/sqlite/0001_bootstrap.sql"));err!=nil{t.Fatal(err)}
 svc,err:=domain.New(db,filepath.Join(root,"spec/v2.0/contracts"),filepath.Join(root,"migrations/sqlite/0002_domain.sql"));if err!=nil{t.Fatal(err)}
 raw,err:=os.ReadFile(filepath.Join(root,"migrations/sqlite/next_v24_sessions.sql"));if err!=nil{t.Fatal(err)}
 if _,err=db.Exec(string(raw));err!=nil{t.Fatal(err)}
 if _,err=db.Exec("INSERT INTO auth_principals(id,roles) VALUES('audit-reader','[\"READER\"]')");err!=nil{t.Fatal(err)}
 token,err:=svc.IssueCredential(context.Background(),"audit-reader",time.Minute);if err!=nil{t.Fatal(err)}
 return db,svc,token
}
func auditSeed(t *testing.T,db *sql.DB,session string) {
 t.Helper()
 for _,q:=range []string{
 "INSERT OR IGNORE INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p-secret','Project','p-secret',1,'{}',0)",
 "INSERT OR IGNORE INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p-secret','Run','run-secret',1,'{\"status\":\"RUNNING\",\"children_stopped\":false,\"queue_empty\":false}',0)",
 }{if _,err:=db.Exec(q);err!=nil{t.Fatal(err)}}
 now:=time.Now().UTC();lease:=now.Add(time.Hour);ws,title,model,build:="ws-secret","PRIVATE TITLE","model-secret","core-audit";run:="run-secret"
 tx,err:=db.Begin();if err!=nil{t.Fatal(err)};defer tx.Rollback()
 if err=domain.MapClientSession(context.Background(),tx,domain.ClientSession{ID:session,ProjectID:"p-secret",Revision:1,CreatedAt:now,UpdatedAt:now,WriterEpoch:1,WriterClientID:"original-client",LeaseExpiresAt:&lease,UpstreamSession:"up-secret",WorkspaceRef:&ws,Title:&title,ModelConfigRef:&model,CoreBuildID:&build,Protocol:domain.ProtocolV2,RunID:&run});err!=nil{t.Fatal(err)}
 if err=tx.Commit();err!=nil{t.Fatal(err)}
}
func auditPost(t *testing.T,v *v2Service,token,cmd,session,method string,project any,epoch any,rev any,payload any) map[string]any{
 t.Helper()
 body,err:=json.Marshal(map[string]any{"protocol_version":domain.ProtocolV2,"command_id":cmd,"client_id":"attacker-client","project_id":project,"session_id":session,"expected_revision":rev,"writer_epoch":epoch,"method":method,"payload":payload});if err!=nil{t.Fatal(err)}
 r:=httptest.NewRequest("POST","http://localhost/v2/command",strings.NewReader(string(body)));r.Header.Set("Authorization","Bearer "+token)
 w:=httptest.NewRecorder();v.serve(w,r);var resp map[string]any
 if err=json.Unmarshal(w.Body.Bytes(),&resp);err!=nil{t.Fatal(err)}
 t.Logf("method=%s project=%v HTTP=%d response=%s",method,project,w.Code,w.Body.String());return resp
}
func TestBackendAuditNullProject(t *testing.T){
 db,_,token:=auditDB(t);auditSeed(t,db,"secret-session")
 v:=newV2Service(db)
 a:=auditPost(t,v,token,"audit-read-explicit","secret-session","session.get","p-secret",nil,nil,map[string]any{})
 b:=auditPost(t,v,token,"audit-read-null","secret-session","session.get",nil,nil,nil,map[string]any{})
 if a["status"]!="REJECTED"||b["status"]!="COMPLETED"{t.Fatalf("unexpected reproduction outcomes: %#v %#v",a,b)}
 c:=auditPost(t,v,token,"audit-ungranted-takeover","secret-session","session.attach",nil,nil,1,map[string]any{"after_sequence":0,"request_write_owner":true})
 if c["status"]!="ACKNOWLEDGED"{t.Fatalf("unexpected null-project takeover outcome: %#v",c)}
}
func TestBackendAuditRunningTakeover(t *testing.T){
 db,svc,token:=auditDB(t);auditSeed(t,db,"live-session")
 if _,err:=db.Exec("INSERT INTO auth_grants(principal,project) VALUES('audit-reader','p-secret')");err!=nil{t.Fatal(err)}
 _,err:=svc.AttachClientSession(context.Background(),domain.Principal{ID:"audit-reader",Roles:[]string{"READER"},Grants:[]domain.Grant{{ProjectID:"p-secret"}}},"p-secret",domain.SessionClaim{SessionID:"live-session",ClientID:"attacker-client",Takeover:true})
 t.Logf("W06 direct service result=%v",err)
 v:=newV2Service(db)
 b:=auditPost(t,v,token,"audit-takeover","live-session","session.attach","p-secret",nil,1,map[string]any{"after_sequence":0,"request_write_owner":true})
 var epoch int;var writer,runStatus string
 db.QueryRow("SELECT writer_epoch,writer_client_id FROM client_sessions WHERE id='live-session'").Scan(&epoch,&writer)
 db.QueryRow("SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='Run' AND id='run-secret'").Scan(&runStatus)
 t.Logf("after typed HTTP: epoch=%d writer=%s run=%s",epoch,writer,runStatus)
 if err==nil||b["status"]!="ACKNOWLEDGED"||epoch!=2||runStatus!="RUNNING"{t.Fatal("unexpected reproduction outcome")}
}




func auditV1(t *testing.T,svc *domain.Service,token,method,path,tag string,payload any)(int,map[string]any,string){
 t.Helper();b,_:=json.Marshal(payload);if payload==nil{b=nil};r:=httptest.NewRequest(method,"http://localhost"+path,strings.NewReader(string(b)));r.Header.Set("Authorization","Bearer "+token);r.Header.Set("Idempotency-Key",domain.ID());if tag!=""{r.Header.Set("If-Match",tag)};w:=httptest.NewRecorder();svc.Handler().ServeHTTP(w,r);var resp map[string]any;json.Unmarshal(w.Body.Bytes(),&resp);return w.Code,resp,w.Header().Get("ETag")
}
func TestBackendAuditSharedOutbox(t *testing.T){
 db,svc,token:=auditDB(t)
 if _,err:=db.Exec("UPDATE auth_principals SET roles='[\"OWNER\"]',can_create_project=1 WHERE id='audit-reader'");err!=nil{t.Fatal(err)}
 status,profile,_:=auditV1(t,svc,token,"POST","/v1/projects","",map[string]any{"name":"audit","intent":"audit","facts":[]any{},"accepted_scope":[]any{"audit"},"constraints":[]any{},"source_configs":[]any{},"source_document_refs":[]any{},"read_snapshot_ids":[]any{}})
 if status!=201{t.Fatalf("project create: %d %v",status,profile)}
 project:=profile["project_id"].(string)
 if _,err:=db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'Project',?,1,'{}',0)",project,project);err!=nil{t.Fatal(err)}
 now:=time.Now().UTC();ws,title,model,build:="ws","audit","model","core-audit"
 tx,_:=db.Begin()
 if err:=domain.MapClientSession(context.Background(),tx,domain.ClientSession{ID:"outbox-session",ProjectID:project,Revision:1,CreatedAt:now,UpdatedAt:now,WriterEpoch:1,WriterClientID:"original-client",UpstreamSession:"up-outbox",WorkspaceRef:&ws,Title:&title,ModelConfigRef:&model,CoreBuildID:&build,Protocol:domain.ProtocolV2});err!=nil{t.Fatal(err)}
 if err:=tx.Commit();err!=nil{t.Fatal(err)}
 b:=auditPost(t,newV2Service(db),token,"audit-outbox","outbox-session","session.attach",project,nil,1,map[string]any{"after_sequence":0,"request_write_owner":true});if b["status"]!="ACKNOWLEDGED"{t.Fatal(b)}
 var eventSeq,outboxSeq int
 db.QueryRow("SELECT json_extract(body,'$.event_sequence') FROM domain_objects WHERE project=? AND kind='ProjectState'",project).Scan(&eventSeq)
 db.QueryRow("SELECT max(sequence) FROM outbox WHERE project=?",project).Scan(&outboxSeq)
 _,_,etag:=auditV1(t,svc,token,"GET","/v1/projects/"+project+"/state","",nil)
 status,resp,_:=auditV1(t,svc,token,"POST","/v1/projects/"+project+"/requirements",etag,map[string]any{"requirement_key":"REQ-audit","text":"audit","basis":"USER_STATED","source_refs":[]any{},"rationale":"audit","supersedes_id":nil,"acceptance_check_ids":[]any{}})
 t.Logf("after v2 event: state.event_sequence=%d outbox.max(sequence)=%d; next v1 createRequirement HTTP=%d response=%v",eventSeq,outboxSeq,status,resp)
 if eventSeq!=1||outboxSeq!=2||status!=409{t.Fatal("unexpected outbox reproduction")}
}


