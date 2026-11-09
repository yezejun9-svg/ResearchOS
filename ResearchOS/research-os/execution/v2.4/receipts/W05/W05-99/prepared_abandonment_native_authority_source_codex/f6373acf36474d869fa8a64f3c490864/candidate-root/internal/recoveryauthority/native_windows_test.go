//go:build windows

package recoveryauthority

import (
    "bytes"
    "context"
    "crypto/rand"
    "encoding/json"
    "os"
    "path/filepath"
    "testing"

    "golang.org/x/sys/windows"
)

func TestAuthorityTransportPurposeMACAndFrameLimit(t *testing.T) {
    key:=make([]byte,32); if _,err:=rand.Read(key); err!=nil { t.Fatal(err) }
    var buffer bytes.Buffer
    if err:=writeFrame(&buffer,key,Purpose,map[string]string{"hello":"world"}); err!=nil { t.Fatal(err) }
    raw:=append([]byte(nil),buffer.Bytes()...)
    var result map[string]string
    if err:=readFrame(bytes.NewReader(raw),key,Purpose,&result); err!=nil || result["hello"]!="world" { t.Fatal("valid transport failed",err) }
    if readFrame(bytes.NewReader(raw),key,MigrationPurpose,&result)==nil { t.Fatal("cross-purpose replay accepted") }
    key[0]^=1; if readFrame(bytes.NewReader(raw),key,Purpose,&result)==nil { t.Fatal("wrong inherited key accepted") }
    if readFrame(bytes.NewReader([]byte{255,255,255,255}),key,Purpose,&result)==nil { t.Fatal("unbounded frame accepted") }
}
func TestAuthorityRawPinHandleDeniesOverwrite(t *testing.T) {
    path:=filepath.Join(t.TempDir(),"evidence.json"); raw:=[]byte(`{"original":true}`)
    if err:=os.WriteFile(path,raw,0600); err!=nil { t.Fatal(err) }
    f,got,err:=pinHeld(RawPin{Path:path,SHA256:digest(raw),Bytes:int64(len(raw))}); if err!=nil { t.Fatal(err) }; defer f.file.Close()
    if !bytes.Equal(raw,got) { t.Fatal("wrong raw bytes") }
    if err=os.WriteFile(path,[]byte("changed"),0600); err==nil { t.Fatal("read guard allowed write") }
    if err=f.check(); err!=nil { t.Fatal(err) }
    if _,_,err=pinHeld(RawPin{Path:path,SHA256:digest([]byte("wrong")),Bytes:int64(len(raw))}); err==nil { t.Fatal("hash mismatch accepted") }
}
func TestAuthorityObserveNativeBirthAndRejectCallerImage(t *testing.T) {
    observed,err:=process(windows.CurrentProcess()); if err!=nil { t.Fatal(err) }
    if observed.PID!=uint32(os.Getpid()) || observed.Birth100ns=="" || observed.SID=="" { t.Fatal("native identity missing") }
    pin:=observed.Image; pin.SHA256=digest([]byte("caller hash"))
    if acceptedImage(observed,pin,observed.SID,"researchos.local/research-os/apps/control")==nil { t.Fatal("caller hash accepted") }
}
func TestAuthorityPublicModeWithoutPrivateInheritanceRejects(t *testing.T) {
    t.Setenv(bootstrapEnv,"")
    if _,_,err:=ReceiveInherited(context.Background()); err==nil { t.Fatal("public invocation minted token") }
    if _,_,err:=ReceiveMigrationInherited(context.Background()); err==nil { t.Fatal("public invocation minted migration token") }
}
func TestAuthorityProvisionReturnsOnlyDPAPIAndDistinctPurpose(t *testing.T) {
    path:=filepath.Join(t.TempDir(),"root.dpapi")
    pub,err:=ProvisionEnrollmentKey(path,"root-adoption"); if err!=nil { t.Fatal(err) }
    if len(pub)!=64 { t.Fatal("invalid public key") }
    if _,err=readPurposeKey(path,"issuer"); err==nil { t.Fatal("root signer decrypted as issuer") }
    key,err:=readPurposeKey(path,"root-adoption"); if err!=nil { t.Fatal(err) }; defer wipe(key)
    raw,err:=os.ReadFile(path); if err!=nil { t.Fatal(err) }; if bytes.Contains(raw,key) || json.Valid(raw) { t.Fatal("private key stored as plaintext") }
    if _,err=ProvisionEnrollmentKey(path,"root-adoption"); err==nil { t.Fatal("existing private resource overwritten") }
}
