package main

import (
 "encoding/json"
 "os"
 "path/filepath"
 "strings"
 "testing"
)

func TestIndependentRejectBeforeMetadataWrite(t *testing.T) {
 for _, kind := range []string{"empty-extra-directory","existing-marker","existing-verifier","existing-temp","case-file","case-parent","root-dotdot","root-trailing-separator"} {
  t.Run(kind,func(t *testing.T){
   root:=filepath.Join(t.TempDir(),"FreshRoot"); raw,_:=fixture(t,root)
   manifest:=filepath.Join(filepath.Dir(root),"input.json"); if err:=os.WriteFile(manifest,raw,0600);err!=nil{t.Fatal(err)}
   input:=root
   var err error
   switch kind {
   case "empty-extra-directory":err=os.Mkdir(filepath.Join(root,"extra-empty"),0700)
   case "existing-marker":err=os.WriteFile(filepath.Join(root,markerPath),[]byte("sentinel"),0600)
   case "existing-verifier":err=os.WriteFile(filepath.Join(root,filepath.FromSlash(verifierPath)),[]byte("sentinel"),0600)
   case "existing-temp":err=os.WriteFile(filepath.Join(root,".installed-product.json.tmp"),[]byte("sentinel"),0600)
   case "case-file":err=os.Rename(filepath.Join(root,"payload","file-001.bin"),filepath.Join(root,"payload","FILE-001.bin"))
   case "case-parent":input=filepath.Join(filepath.Dir(root),"freshroot")
   case "root-dotdot":input=root+`\..\FreshRoot`
   case "root-trailing-separator":input=root+`\`
   }
   if err!=nil{t.Fatal(err)}
   if _,err=finalize(input,manifest,shaBytes(raw));err==nil{t.Fatal("accepted unsafe stage")}
   if kind=="existing-marker"{b,_:=os.ReadFile(filepath.Join(root,markerPath));if string(b)!="sentinel"{t.Fatal("existing marker changed")}}
   if kind!="existing-marker" {if _,err=os.Stat(filepath.Join(root,markerPath));!os.IsNotExist(err){t.Fatal("marker committed on refusal")}}
  })
 }
}
func TestIndependentManifestRoleAndSizeGuards(t *testing.T){
 for _,kind:=range []string{"missing-role","extra-role","role-digest","size-negative","metadata-source","template-executable","trailing-json","unknown-field"}{
  t.Run(kind,func(t *testing.T){
   raw,p:=fixture(t,filepath.Join(t.TempDir(),"fresh"))
   switch kind {
   case "missing-role":delete(p.Binaries,"cli")
   case "extra-role":p.Binaries["extra"]=p.Binaries["cli"]
   case "role-digest":b:=p.Binaries["cli"];b.SHA256=strings.Repeat("a",64);p.Binaries["cli"]=b
   case "size-negative":p.Files[0].Bytes=-1
   case "metadata-source":p.Metadata["source_commit"]=strings.Repeat("b",40)
   case "template-executable":p.VerifierTemplate["executable"]="C:\\foreign.exe"
   }
   raw,_=jsonLine(p)
   if kind=="trailing-json"{raw=append(raw,[]byte("{}")...)}
   if kind=="unknown-field" {var m map[string]any;json.Unmarshal(raw,&m);m["unexpected"]=true;raw,_=jsonLine(m)}
   if _,err:=parseManifest(raw,shaBytes(raw));err==nil{t.Fatal("bad trusted manifest accepted")}
  })
 }
}
func TestIndependentRenameSemanticsObservation(t *testing.T){
 d:=t.TempDir();src:=filepath.Join(d,"temp");dst:=filepath.Join(d,"marker")
 if err:=os.WriteFile(src,[]byte("new"),0600);err!=nil{t.Fatal(err)}
 if err:=os.WriteFile(dst,[]byte("concurrent-existing"),0600);err!=nil{t.Fatal(err)}
 err:=os.Rename(src,dst);b,_:=os.ReadFile(dst)
 t.Logf("Windows os.Rename existing target: error=%v content=%q; finalizer Lstat/Rename is not an atomic create-new operation",err,b)
}
