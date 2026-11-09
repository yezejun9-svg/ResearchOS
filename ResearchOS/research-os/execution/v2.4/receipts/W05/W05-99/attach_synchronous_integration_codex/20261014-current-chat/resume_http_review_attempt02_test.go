package api

import (
 "bytes"
 "context"
 "encoding/base64"
 "encoding/json"
 "io"
 "net/http"
 "testing"
 "researchos.local/research-os/internal/domain"
)

func TestIndependentAttachRevokedProjectReplayHTTP(t *testing.T) {
 for _,originalStatus:= range []string{"COMPLETED","ACKNOWLEDGED"} {
  for _,change:=range []string{"grant-deleted","grant-task-only"} {
   t.Run(originalStatus+"/"+change,func(t *testing.T){
    t.Setenv("RESEARCHOS_WRITER_LEASE_TTL", "")
    f:=newSessionHTTPFixture(t);snap:=f.create(t,"ind-create");sid:=snap["session_id"].(string)
    env:=f.envelope("session.attach","ind-attach",domain.Object{"request_write_owner":true,"after_sequence":0})
    env["session_id"],env["expected_revision"]=sid,1
    originalRequest:=domain.Bytes(env)
    request:=func()(int,[]byte){
     req,e:=http.NewRequest("POST",f.server.URL+"/v2/command",bytes.NewReader(originalRequest));if e!=nil{t.Fatal(e)}
     req.Header.Set("Authorization","Bearer "+f.token);req.Header.Set("Content-Type","application/json")
     res,e:=f.server.Client().Do(req);if e!=nil{t.Fatal(e)};defer res.Body.Close();raw,e:=io.ReadAll(res.Body);if e!=nil{t.Fatal(e)};return res.StatusCode,raw
    }
    if originalStatus=="ACKNOWLEDGED" {
     decoded,e:=domain.DecodeEnvelope(originalRequest);if e!=nil{t.Fatal(e)};hash,e:=decoded.ContentHash();if e!=nil{t.Fatal(e)}
     headers:=domain.Bytes(struct {Schema string `json:"schema"`; Encoding string `json:"encoding"`; Raw string `json:"raw_envelope_base64"`}{"researchos.private-command-envelope.v1","base64",base64.StdEncoding.EncodeToString(originalRequest)})
     ack:=domain.Object{"protocol_version":domain.ProtocolV2,"command_id":"ind-attach","method":"session.attach","status":"ACKNOWLEDGED","session_id":sid,"revision":1,"result":domain.Object{"accepted_at":domain.Now(),"operation_id":"ind-op","after_sequence":0,"related_resource_ref":nil}}
     var ackResponse domain.Response; if e=json.Unmarshal(domain.Bytes(ack), &ackResponse);e!=nil{t.Fatal(e)}
     tx,e:=f.db.Begin();if e!=nil{t.Fatal(e)};defer tx.Rollback()
     _,e=tx.Exec(`INSERT INTO client_command_identities(principal,command_id,protocol,project,method,operation,request_hash,created_at) VALUES(?,?,?,?,?,?,?,?)`,"session-owner","ind-attach",domain.ProtocolV2,f.project,"session.attach","v2:session.attach",hash,domain.Now());if e!=nil{t.Fatal(e)}
     _,e=tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,?,?,?,?)`,"session-owner",f.project,"v2:session.attach","ind-attach",hash,0,string(domain.Bytes(&ackResponse)),string(headers),domain.Now());if e!=nil{t.Fatal(e)};if e=tx.Commit();e!=nil{t.Fatal(e)}
    }
    status,first:=request();var res domain.Object;if e:=json.Unmarshal(first,&res);e!=nil{t.Fatal(e)}
    if status!=200||res["status"]!=originalStatus {t.Fatalf("initial replay HTTP=%d %s",status,first)}
    status,again:=request();if status!=200||!bytes.Equal(first,again){t.Fatalf("valid authority exact replay differs: %d %s",status,again)}
    if change=="grant-deleted" {if _,e:=f.db.Exec(`DELETE FROM auth_grants WHERE principal=? AND project=?`,"session-owner",f.project);e!=nil{t.Fatal(e)}} else {if _,e:=f.db.Exec(`UPDATE auth_grants SET task='restricted-task' WHERE principal=? AND project=?`,"session-owner",f.project);e!=nil{t.Fatal(e)}}
    principal,e:=domain.AuthenticateToken(context.Background(),f.db,f.token);if e!=nil||!principal.HasRole("OWNER")||principal.Allowed(f.project,"","",false){t.Fatalf("authority fixture incorrect: %+v %v",principal,e)}
    var before,after string
    if e=f.db.QueryRow(`SELECT json_array(writer_client_id,writer_epoch,revision,event_watermark,lease_expires_at,updated_at) FROM client_sessions WHERE id=?`,sid).Scan(&before);e!=nil{t.Fatal(e)}
    status,blocked:=request();if e=json.Unmarshal(blocked,&res);e!=nil{t.Fatal(e)}
    if status!=403||res["status"]!="REJECTED"||res["error_code"]!="FORBIDDEN" {t.Fatalf("REVOKED PROJECT REPLAY LEAK: HTTP=%d %s",status,blocked)}
    var journal string;if e=f.db.QueryRow(`SELECT body FROM idempotency WHERE principal=? AND key=?`,"session-owner","ind-attach").Scan(&journal);e!=nil{t.Fatal(e)}
    if !bytes.Equal(bytes.TrimSpace(first),[]byte(journal)){t.Fatal("immutable response changed")}
    if e=f.db.QueryRow(`SELECT json_array(writer_client_id,writer_epoch,revision,event_watermark,lease_expires_at,updated_at) FROM client_sessions WHERE id=?`,sid).Scan(&after);e!=nil||before!=after{t.Fatalf("refusal mutated writer %v",e)}
    t.Logf("global OWNER and token valid; %s old %s replay: HTTP 403 FORBIDDEN; journal and writer unchanged",change,originalStatus)
   })
  }
 }
}
