//go:build windows

package host

import (
 "context"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "researchos.local/research-os/internal/domain"
)

func TestIndependentRevisionForeignRootDigest(t *testing.T) {
 for _, mutation:=range []string{"revocation", "remove-complete-foreign-tree", "grant-drift"} {
  t.Run(mutation,func(t *testing.T) {
   f:=newReplacementFixture(t)
   root:="local-verifier-root-"+strings.Repeat("e",24)
   child:="local-verifier-"+strings.TrimPrefix(domain.Hash([]any{root,"foreign-project"}),"sha256:")[:32]
   f.exec(t,`INSERT INTO auth_principals VALUES(?,'["VERIFIER"]',0,0),(?,'["VERIFIER"]',0,0)`,root,child)
   f.exec(t,`INSERT INTO orchestration_identity VALUES(?,?,NULL),(?,?,?)`,root,root,child,root,root)
   f.exec(t,`INSERT INTO auth_grants VALUES(?,'foreign-project','','',0)`,child)
   in:=f.preflight(t)
   path:=filepath.Join(f.Root,"host","runtime-verifier-installation.json")
   before,e:=os.ReadFile(path);if e!=nil{t.Fatal(e)}
   switch mutation {
   case "revocation": f.exec(t,`UPDATE auth_principals SET revoked=1 WHERE id IN (?,?)`,root,child)
   case "remove-complete-foreign-tree":
    f.exec(t,`DELETE FROM auth_principals WHERE id IN (?,?);DELETE FROM orchestration_identity WHERE principal IN (?,?);DELETE FROM auth_grants WHERE principal=?`,root,child,root,child,child)
   case "grant-drift":f.exec(t,`UPDATE auth_grants SET project='changed' WHERE principal=?`,child)
   }
   out,e:=RuntimeVerifierReplacement(context.Background(),in)
   if e==nil || out.Outcome!="NOT_APPLIED" {t.Fatalf("foreign reserved state drift escaped plan: %+v %v",out,e)}
   after,e:=os.ReadFile(path);if e!=nil{t.Fatal(e)};if string(before)!=string(after){t.Fatal("rejected commit changed registration")}
   if _,e=os.Stat(filepath.Join(f.Root,"host",replacementJournal));!os.IsNotExist(e){t.Fatalf("rejected stale plan created journal: %v",e)}
  })
 }
}
