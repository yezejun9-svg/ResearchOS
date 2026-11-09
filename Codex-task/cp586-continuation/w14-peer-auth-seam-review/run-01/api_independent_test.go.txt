package api

import (
 "bytes"
 "context"
 "net/http/httptest"
 "testing"

 "researchos.local/research-os/internal/domain"
)

func reviewRecorderRequest(t *testing.T,f *commandAuthHTTPFixture,ctx context.Context,token string,raw []byte) *httptest.ResponseRecorder {
 t.Helper()
 request:=httptest.NewRequest("POST","/v2/command",bytes.NewReader(raw)).WithContext(ctx)
 request.Header.Set("Content-Type","application/json")
 request.Header.Set("X-ResearchOS-Native-Verified","true")
 if token!="" {request.Header.Set("Authorization","Bearer "+token)}
 recorder:=httptest.NewRecorder();f.v2.serve(recorder,request);return recorder
}

func TestReviewGenuineOldAuthContextCannotAuthenticateNewHTTPRequest(t *testing.T) {
 f:=newCommandAuthHTTPFixture(t)
 tx,err:=f.db.Begin();if err!=nil {t.Fatal(err)}
 old,_,err:=domain.AuthenticateCommandTx(context.Background(),tx,f.token,f.v2.svc);if err!=nil {t.Fatal(err)}
 if err=tx.Rollback();err!=nil {t.Fatal(err)}
 raw:=domain.Bytes(commandAuthEnvelope("host.status",nil))
 for _,token:=range []string{"","not-a-real-token"} {
  response:=reviewRecorderRequest(t,f,old,token,raw)
  if response.Code!=401 {t.Fatalf("genuine old private context replaced new bearer authentication: %d %s",response.Code,response.Body.Bytes())}
 }
 valid:=reviewRecorderRequest(t,f,old,f.token,raw)
 if valid.Code!=200 {t.Fatalf("fresh real credential failed positive control: %d %s",valid.Code,valid.Body.Bytes())}
 if bytes.Contains(valid.Body.Bytes(),[]byte(f.token)) || bytes.Contains(valid.Body.Bytes(),[]byte(domain.Digest([]byte(f.token)))) {t.Fatal("private token facts leaked")}
 if _,err=f.db.Exec(`UPDATE auth_credentials SET revoked=1`);err!=nil {t.Fatal(err)}
 revoked:=reviewRecorderRequest(t,f,old,f.token,domain.Bytes(commandAuthEnvelope("host.status",nil)))
 if revoked.Code!=401 {t.Fatalf("old HTTP context hid revocation: %d %s",revoked.Code,revoked.Body.Bytes())}
}

func TestReviewRecorderErrorStagesLeaveNoCommandWrites(t *testing.T) {
 f:=newCommandAuthHTTPFixture(t)
 for _,tc:=range []struct{name,token string;raw []byte;want int}{
  {"unknown-method-bad-token","invalid",domain.Bytes(commandAuthEnvelope("unknown.method",nil)),401},
  {"unknown-method-valid-token",f.token,domain.Bytes(commandAuthEnvelope("unknown.method",nil)),400},
  {"wrong-protocol-before-auth","invalid",[]byte(`{"protocol_version":"researchos-client/1"}`),400},
  {"envelope-before-valid-auth",f.token,[]byte(`{"protocol_version":"researchos-client/2","native_verified":true}`),400},
  {"auth-before-invalid-envelope","invalid",[]byte(`{"protocol_version":"researchos-client/2","native_verified":true}`),401},
 } {
  t.Run(tc.name,func(t *testing.T){
   var before,after int
   if err:=f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&before);err!=nil {t.Fatal(err)}
   result:=reviewRecorderRequest(t,f,context.Background(),tc.token,tc.raw)
   if result.Code!=tc.want {t.Fatalf("error precedence: %d %s",result.Code,result.Body.Bytes())}
   if err:=f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&after);err!=nil {t.Fatal(err)}
   if before!=after {t.Fatal("pre-execution error committed an identity")}
  })
 }
 if err:=f.db.Close();err!=nil {t.Fatal(err)}
 for _,tc:=range []struct{name string;raw []byte;want int}{
  {"closed-db-no-bearer",domain.Bytes(commandAuthEnvelope("host.status",nil)),401},
  {"closed-db-protocol-before-auth",[]byte(`{"protocol_version":"researchos-client/1"}`),400},
  {"closed-db-size-before-auth",bytes.Repeat([]byte(" "),int(maxCommandBytes)+1),413},
 } {
  t.Run(tc.name,func(t *testing.T){response:=reviewRecorderRequest(t,f,context.Background(),"",tc.raw);if response.Code!=tc.want {t.Fatalf("closed DB error precedence changed: %d %s",response.Code,response.Body.Bytes())}})
 }
}
