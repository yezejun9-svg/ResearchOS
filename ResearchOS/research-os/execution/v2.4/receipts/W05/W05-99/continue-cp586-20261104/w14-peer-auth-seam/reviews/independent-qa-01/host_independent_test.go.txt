package host

import (
 "bytes"
 "database/sql"
 "errors"
 "os"
 "path/filepath"
 "testing"
)

func TestReviewNativePeerCannotUseStableInstanceOrChangedHostIdentity(t *testing.T) {
 first,second:=peerSeamHost(),peerSeamHost()
 if first.InstanceID()!=second.InstanceID() {t.Fatal("control requires the same stable identifier")}
 peer,err:=first.verifyNativePeer(81);if err!=nil {t.Fatal(err)}
 if peer.validFor(second) {t.Fatal("stable identifier substituted for owning Host")}
 first.identity.VID="S-1-5-21-changed-host-subject"
 if peer.validFor(first) {t.Fatal("held facts survived a different current OS subject")}
 raw:=[]byte(`{"kind":"UNSUPPORTED_FIXTURE_KIND","client_id":"ordinary-label","payload":{}}`)
 if _,err=first.handleVerifiedNative(raw,peer,nil);!errors.Is(err,ErrFrameUntrusted) {t.Fatalf("changed identity accepted: %v",err)}
}

func TestReviewLegacyBooleanCannotPopulateForgedNativeWireFields(t *testing.T) {
 h:=peerSeamHost()
 raw:=[]byte(`{"kind":"UNSUPPORTED_FIXTURE_KIND","client_id":"ordinary-label","payload":{}}`)
 invocation,err:=h.prepareNativeInvocation(raw,nil)
 if err!=nil || invocation.peer!=nil {t.Fatalf("legacy route acquired typed facts: %v",err)}
 for _,extra:=range []string{`"native_verified":true`,`"peer":{"pid":81,"principal_ref":"synthetic-os-subject"}`,`"boot_generation":"claimed"`} {
  forged:=append(append([]byte{},raw[:len(raw)-1]...),[]byte(","+extra+"}")...)
  if _,err=h.HandleNative(forged,true,nil);!errors.Is(err,ErrFrameShape) {t.Fatalf("request field became a private capability: %v",err)}
 }
 if _,err=h.HandleNative([]byte("{"),false,nil);!errors.Is(err,ErrFrameUntrusted) {t.Fatalf("legacy trust error precedence changed: %v",err)}
}

func TestReviewHostConsumesFreshEntropyBeforeAnyMutableSetup(t *testing.T) {
 path:=filepath.Join(t.TempDir(),"not-created")
 cfg:=Config{DB:&sql.DB{},Dir:path,ContractsDir:"not-read",MigrationFile:"not-read",SchemaDir:"not-read",ReadOnlyModelCredentialRef:"incomplete-storage-config"}
 entropy:=bytes.NewReader(bytes.Repeat([]byte{7},32))
 if h,err:=newHost(cfg,entropy);h!=nil || !errors.Is(err,ErrUnknownCredential) {t.Fatalf("nonzero full entropy must reach only the next pure configuration gate: %v",err)}
 if entropy.Len()!=0 {t.Fatal("constructor did not read a complete fresh generation")}
 if h,err:=newHost(cfg,entropy);h!=nil || !errors.Is(err,ErrBadState) {t.Fatalf("second construction reused prior entropy or ignored exhaustion: %v",err)}
 if _,err:=os.Stat(path);!errors.Is(err,os.ErrNotExist) {t.Fatalf("pre-setup rejection touched the private directory: %v",err)}
}
