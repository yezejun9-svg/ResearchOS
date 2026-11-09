package main
import("os";"path/filepath";"strings";"testing")
func TestIndependentNoReplacePreservesBothFiles(t *testing.T){
 root:=t.TempDir();src:=filepath.Join(root,"temp");dst:=filepath.Join(root,"marker")
 if err:=writeNew(src,[]byte("new"));err!=nil{t.Fatal(err)}
 err:=publishMarkerNoReplace(src,dst,func()error{return writeNew(dst,[]byte("concurrent"))})
 if err==nil{t.Fatal("unexpected overwrite success")}
 a,_:=os.ReadFile(src);b,_:=os.ReadFile(dst)
 if string(a)!="new"||string(b)!="concurrent"{t.Fatalf("data changed %q %q",a,b)}
}
func TestIndependentLongCanonicalPublication(t *testing.T){
 root:=t.TempDir()
 for len(root)<285{root=filepath.Join(root,strings.Repeat("x",30))}
 if err:=os.MkdirAll(root,0700);err!=nil{t.Fatal(err)}
 src:=filepath.Join(root,".installed-product.json.tmp");dst:=filepath.Join(root,markerPath)
 if err:=writeNew(src,[]byte("marker"));err!=nil{t.Fatal(err)}
 err:=publishMarkerNoReplace(src,dst,nil)
 t.Logf("root chars=%d src chars=%d error=%v",len(root),len(src),err)
 if err!=nil{t.Fatalf("canonical long-path publication failed: %v",err)}
 b,e:=os.ReadFile(dst);if e!=nil||string(b)!="marker"{t.Fatalf("wrong marker: %q %v",b,e)}
}
