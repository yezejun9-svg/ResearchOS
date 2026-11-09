package api

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

// Recorder-only fresh fixture: no listener, native pipe, model or provider.
type commandAuthHTTPFixture struct{db *sql.DB; service *domain.Service; v2 *v2Service; token,project string}

func newCommandAuthHTTPFixture(t *testing.T)*commandAuthHTTPFixture{
	t.Helper()
	db,err:=store.Open(filepath.Join(t.TempDir(),"auth-http.sqlite"));if err!=nil{t.Fatal(err)}
	t.Cleanup(func(){db.Close()})
	if err=store.Bootstrap(context.Background(),db,"../../migrations/sqlite/0001_bootstrap.sql");err!=nil{t.Fatal(err)}
	s,err:=domain.New(db,"../../spec/v2.0/contracts","../../migrations/sqlite/0002_domain.sql");if err!=nil{t.Fatal(err)}
	raw,err:=os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql");if err!=nil{t.Fatal(err)}
	if _,err=db.Exec(string(raw));err!=nil{t.Fatal(err)}
	if err=domain.EnsureClientSessionFence(context.Background(),db);err!=nil{t.Fatal(err)}
	if err=s.ProvisionPrincipal(context.Background(),domain.Principal{ID:"command-owner",Roles:[]string{"OWNER"},CanCreateProject:true});err!=nil{t.Fatal(err)}
	token,err:=s.IssueCredential(context.Background(),"command-owner",time.Minute);if err!=nil{t.Fatal(err)}
	f:=&commandAuthHTTPFixture{db:db,service:s,token:token,v2:newV2Service(db)}
	if f.v2.loadErr!=nil{t.Fatal(f.v2.loadErr)}
	f.v2.svc.Domain=s
	profile:=domain.Object{"name":"Command auth fresh fixture","intent":"Verify credential transaction boundary","facts":domain.Empty(),"accepted_scope":[]any{"auth fixture"},"constraints":domain.Empty(),"source_configs":domain.Empty(),"source_document_refs":domain.Empty(),"read_snapshot_ids":domain.Empty()}
	req:=httptest.NewRequest("POST","/v1/projects",bytes.NewReader(domain.Bytes(profile)))
	req.Header.Set("Authorization","Bearer "+token);req.Header.Set("Idempotency-Key",domain.ID())
	recorder:=httptest.NewRecorder();s.Handler().ServeHTTP(recorder,req)
	if recorder.Code!=201{t.Fatalf("fresh project fixture: %d %s",recorder.Code,recorder.Body.Bytes())}
	var project domain.Object;if err=json.Unmarshal(recorder.Body.Bytes(),&project);err!=nil{t.Fatal(err)}
	f.project=project["project_id"].(string)
	return f
}

func commandAuthEnvelope(method string,project any)domain.Object{
	payload:=domain.Object{}
	if method=="session.list"{payload=domain.Object{"cursor":nil,"limit":20}}
	return domain.Object{"protocol_version":domain.ProtocolV2,"command_id":domain.ID(),"client_id":"unproven-client-label","project_id":project,"session_id":nil,"expected_revision":nil,"writer_epoch":nil,"method":method,"payload":payload}
}

func (f *commandAuthHTTPFixture) request(t *testing.T,token string,raw []byte)(int,domain.Object,[]byte){
	t.Helper()
	req:=httptest.NewRequest("POST","/v2/command",bytes.NewReader(raw));req.Header.Set("Content-Type","application/json")
	if token!=""{req.Header.Set("Authorization","Bearer "+token)}
	// A caller-owned header is never a native attestation or an auth context.
	req.Header.Set("X-ResearchOS-Native-Verified","true")
	recorder:=httptest.NewRecorder();f.v2.serve(recorder,req)
	body:=append([]byte(nil),recorder.Body.Bytes()...)
	var out domain.Object;if err:=json.Unmarshal(body,&out);err!=nil{t.Fatalf("response JSON: %v %s",err,body)}
	return recorder.Code,out,body
}

func authHTTPCode(out domain.Object)string{if e,ok:=out["error"].(map[string]any);ok{v,_:=e["code"].(string);return v};return ""}

func TestCommandAuthHTTPOrdinaryTokenAndErrorPrecedence(t *testing.T){
	f:=newCommandAuthHTTPFixture(t)
	for _,tc:=range []struct{name,token string;raw []byte;status int;code string}{
		{"ordinary-status",f.token,domain.Bytes(commandAuthEnvelope("host.status",nil)),200,""},
		{"invalid-json","invalid",[]byte(`{`),400,"INVALID_REQUEST"},
		{"missing-protocol","invalid",[]byte(`{}`),400,"UNSUPPORTED_PROTOCOL"},
		{"wrong-protocol","invalid",[]byte(`{"protocol_version":"researchos-client/1"}`),400,"UNSUPPORTED_PROTOCOL"},
		{"decode-before-invalid-token","invalid",[]byte(`{"protocol_version":"researchos-client/2"}`),401,"UNAUTHENTICATED"},
		{"decode-after-valid-token",f.token,[]byte(`{"protocol_version":"researchos-client/2"}`),400,"INVALID_REQUEST"},
		{"unknown-method",f.token,domain.Bytes(commandAuthEnvelope("unknown.method",nil)),400,"UNSUPPORTED_METHOD"},
		{"missing-token","",domain.Bytes(commandAuthEnvelope("host.status",nil)),401,"UNAUTHENTICATED"},
	}{t.Run(tc.name,func(t *testing.T){
		status,out,body:=f.request(t,tc.token,tc.raw)
		if status!=tc.status || authHTTPCode(out)!=tc.code{t.Fatalf("status/error precedence: %d %s",status,body)}
		if tc.status==200 && out["status"]!="COMPLETED"{t.Fatalf("ordinary token no longer works: %s",body)}
		if bytes.Contains(body,[]byte(f.token)) || bytes.Contains(body,[]byte(domain.Digest([]byte(f.token)))) || bytes.Contains(body,[]byte("boot_generation")){t.Fatal("private credential facts leaked to HTTP")}
	})}
	claimed:=commandAuthEnvelope("host.status",nil);claimed["native_verified"]=true
	status,out,_:=f.request(t,f.token,domain.Bytes(claimed))
	if status!=400 || authHTTPCode(out)!="INVALID_REQUEST"{t.Fatal("request field manufactured a private authority value")}
}

func TestCommandAuthHTTPRevocationExpiryAndProjectRBAC(t *testing.T){
	for _,name:=range []string{"credential-revoked","principal-revoked","expired","project-grant-removed"}{t.Run(name,func(t *testing.T){
		f:=newCommandAuthHTTPFixture(t);query:=`UPDATE auth_credentials SET revoked=1`
		if name=="principal-revoked"{query=`UPDATE auth_principals SET revoked=1`}
		if name=="expired"{query=`UPDATE auth_credentials SET expires_at='2000-01-01T00:00:00Z'`}
		if name=="project-grant-removed"{query=`DELETE FROM auth_grants WHERE principal='command-owner'`}
		if _,err:=f.db.Exec(query);err!=nil{t.Fatal(err)}
		env:=commandAuthEnvelope("session.list",f.project)
		var before int;if err:=f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&before);err!=nil{t.Fatal(err)}
		status,out,body:=f.request(t,f.token,domain.Bytes(env));want,code:=401,"UNAUTHENTICATED";if name=="project-grant-removed"{want,code=403,"FORBIDDEN"}
		if status!=want || authHTTPCode(out)!=code{t.Fatalf("ordinary auth/RBAC changed: %d %s",status,body)}
		var after int;if err:=f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&after);err!=nil{t.Fatal(err)}
		if before!=after{t.Fatal("auth/RBAC rejection executed a command")}
	})}
}

func TestCommandAuthHTTPRemoteAuthorityRemainsConstrained(t *testing.T){
	for _,name:=range []string{"active","owner-grant-removed","owner-revoked","owner-role-removed","device-revoked"}{t.Run(name,func(t *testing.T){
		f:=newCommandAuthHTTPFixture(t)
		if err:=f.service.ProvisionPrincipal(context.Background(),domain.Principal{ID:"paired-device",Roles:[]string{"OWNER"},CanCreateProject:true,Grants:[]domain.Grant{{ProjectID:f.project,Restricted:true}}});err!=nil{t.Fatal(err)}
		if _,err:=f.db.Exec(`INSERT INTO remote_devices(id,owner,body) VALUES('paired-device','command-owner','{"status":"ACTIVE","role":"READER"}')`);err!=nil{t.Fatal(err)}
		token,err:=f.service.IssueCredential(context.Background(),"paired-device",time.Minute);if err!=nil{t.Fatal(err)}
		switch name{
		case "owner-grant-removed":_,err=f.db.Exec(`DELETE FROM auth_grants WHERE principal='command-owner'`)
		case "owner-revoked":_,err=f.db.Exec(`UPDATE auth_principals SET revoked=1 WHERE id='command-owner'`)
		case "owner-role-removed":_,err=f.db.Exec(`UPDATE auth_principals SET roles='["READER"]' WHERE id='command-owner'`)
		case "device-revoked":_,err=f.db.Exec(`UPDATE remote_devices SET body='{"status":"REVOKED","role":"READER"}'`)
		};if err!=nil{t.Fatal(err)}
		status,out,body:=f.request(t,token,domain.Bytes(commandAuthEnvelope("session.list",f.project)))
		want,code:=401,"UNAUTHENTICATED";if name=="active"{want,code=200,""};if name=="owner-grant-removed"{want,code=403,"FORBIDDEN"}
		if status!=want || authHTTPCode(out)!=code{t.Fatalf("remote authority changed: %d %s",status,body)}
	})}
}

func TestCommandAuthHTTPExecutionFailureRollsBack(t *testing.T){
	f:=newCommandAuthHTTPFixture(t)
	// FAIL retains prior trigger effects until the caller rolls its transaction
	// back. This therefore checks request rollback, not only statement atomicity.
	if _,err:=f.db.Exec(`CREATE TRIGGER auth_command_fault AFTER INSERT ON client_command_identities WHEN NEW.command_id='auth-rollback' BEGIN DELETE FROM auth_grants WHERE principal='command-owner'; SELECT RAISE(FAIL,'injected command failure'); END`);err!=nil{t.Fatal(err)}
	var grantsBefore,eventsBefore int
	if err:=f.db.QueryRow(`SELECT count(*) FROM auth_grants WHERE principal='command-owner'`).Scan(&grantsBefore);err!=nil{t.Fatal(err)}
	if err:=f.db.QueryRow(`SELECT count(*) FROM outbox`).Scan(&eventsBefore);err!=nil{t.Fatal(err)}
	env:=commandAuthEnvelope("host.status",nil);env["command_id"]="auth-rollback"
	status,out,body:=f.request(t,f.token,domain.Bytes(env))
	if status!=http.StatusInternalServerError || authHTTPCode(out)!="INTERNAL_ERROR"{t.Fatalf("execution failure changed: %d %s",status,body)}
	var grantsAfter,eventsAfter,identities int
	if err:=f.db.QueryRow(`SELECT count(*) FROM auth_grants WHERE principal='command-owner'`).Scan(&grantsAfter);err!=nil{t.Fatal(err)}
	if err:=f.db.QueryRow(`SELECT count(*) FROM outbox`).Scan(&eventsAfter);err!=nil{t.Fatal(err)}
	if err:=f.db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE command_id='auth-rollback'`).Scan(&identities);err!=nil{t.Fatal(err)}
	if grantsAfter!=grantsBefore || eventsAfter!=eventsBefore || identities!=0{t.Fatal("execution failure retained command-side writes")}
}

func TestCommandAuthHTTPAuthTransactionFailureKeepsLegacyStatus(t *testing.T){
	f:=newCommandAuthHTTPFixture(t);if err:=f.db.Close();err!=nil{t.Fatal(err)}
	status,out,_:=f.request(t,f.token,domain.Bytes(commandAuthEnvelope("host.status",nil)))
	if status!=401 || authHTTPCode(out)!="UNAUTHENTICATED"{t.Fatal("auth-stage transaction failure changed status")}
	status,out,_=f.request(t,f.token,[]byte(`{"protocol_version":"wrong"}`))
	if status!=400 || !strings.Contains(authHTTPCode(out),"UNSUPPORTED_PROTOCOL"){t.Fatal("closed auth store bypassed protocol precedence")}
}
