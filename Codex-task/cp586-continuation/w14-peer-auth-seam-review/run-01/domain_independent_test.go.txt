package domain

import (
 "context"
 "errors"
 "testing"
)

func TestReviewCommandFactsCannotCrossRealTransactionsOrReplaceBearer(t *testing.T) {
 db,_,service,token:=commandAuthFixture(t)
 var credentialBefore,businessBefore int
 if err:=db.QueryRow(`SELECT count(*) FROM auth_credentials`).Scan(&credentialBefore);err!=nil {t.Fatal(err)}
 if err:=db.QueryRow(`SELECT count(*) FROM domain_objects`).Scan(&businessBefore);err!=nil {t.Fatal(err)}
 tx1,err:=db.Begin();if err!=nil {t.Fatal(err)}
 first,p,err:=AuthenticateCommandTx(context.Background(),tx1,token,service);if err!=nil {t.Fatal(err)}
 if _,ok:=commandCredentialFromContext(first,tx1,service,p.ID);!ok {t.Fatal("valid positive missing")}
 if err=tx1.Rollback();err!=nil {t.Fatal(err)}
 tx2,err:=db.Begin();if err!=nil {t.Fatal(err)};defer tx2.Rollback()
 if _,ok:=commandCredentialFromContext(first,tx2,service,p.ID);ok {t.Fatal("old context crossed real transactions")}
 for _,wrong:=range []string{"","not-a-real-token"} {
  ctx,principal,err:=AuthenticateCommandTx(first,tx2,wrong,service)
  if err==nil || ctx!=nil || principal.ID!="" {t.Fatal("old context replaced actual bearer authentication")}
 }
 fresh,again,err:=AuthenticateCommandTx(first,tx2,token,service);if err!=nil {t.Fatal(err)}
 if _,ok:=commandCredentialFromContext(fresh,tx2,service,again.ID);!ok {t.Fatal("new valid command was not rebound")}
 if _,ok:=commandCredentialFromContext(fresh,tx1,service,again.ID);ok {t.Fatal("rebound context retained old transaction proof")}
 if _,ok:=commandCredentialFromContext(fresh,tx2,&ClientService{Domain:service.Domain},again.ID);ok {t.Fatal("same DB/Domain substituted for exact ClientService")}
 var credentials,business int
 if err=tx2.QueryRow(`SELECT count(*) FROM auth_credentials`).Scan(&credentials);err!=nil {t.Fatal(err)}
 if err=tx2.QueryRow(`SELECT count(*) FROM domain_objects`).Scan(&business);err!=nil {t.Fatal(err)}
 if credentials!=credentialBefore || business!=businessBefore {t.Fatalf("authentication issued or wrote business rows: %d %d",credentials,business)}
}

func TestReviewOldFactsCannotOverruleRevokedCredentialOrClosedTransaction(t *testing.T) {
 db,_,service,token:=commandAuthFixture(t)
 tx1,err:=db.Begin();if err!=nil {t.Fatal(err)}
 old,_,err:=AuthenticateCommandTx(context.Background(),tx1,token,service);if err!=nil {t.Fatal(err)}
 if err=tx1.Rollback();err!=nil {t.Fatal(err)}
 if ctx,_,err:=AuthenticateCommandTx(old,tx1,token,service);err==nil || ctx!=nil {t.Fatal("closed transaction was replaced or authenticated")}
 if _,err=db.Exec(`UPDATE auth_credentials SET revoked=1`);err!=nil {t.Fatal(err)}
 tx2,err:=db.Begin();if err!=nil {t.Fatal(err)};defer tx2.Rollback()
 if ctx,p,err:=AuthenticateCommandTx(old,tx2,token,service);err==nil || ctx!=nil || p.ID!="" {t.Fatal("old genuine facts hid new credential revocation")}
}

func TestReviewLegacyEmptyTokenStillRejectsBeforeClosedDatabase(t *testing.T) {
 db,_,_,_:=commandAuthFixture(t)
 if err:=db.Close();err!=nil {t.Fatal(err)}
 if _,err:=AuthenticateToken(context.Background(),db,"");!errors.Is(err,ErrNoCredential) {t.Fatalf("legacy no-token precedence changed: %v",err)}
}
