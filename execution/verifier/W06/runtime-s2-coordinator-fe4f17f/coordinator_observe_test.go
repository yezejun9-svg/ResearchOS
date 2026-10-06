//go:build windows
package domain
import("os";"path/filepath";"testing")
func verifierSaveCoordinator(t *testing.T,c *RuntimeCoordinator){
 target:=filepath.Join(os.Getenv("INDEPENDENT_S2_EVIDENCE"),"native",t.Name());if e:=os.MkdirAll(target,0700);e!=nil{t.Error(e);return}
 e:=filepath.Walk(c.config.DataRoot,func(path string,info os.FileInfo,err error)error{if err!=nil{return err};if info.IsDir(){return nil};if info.Name()!="bridge.json"&&info.Name()!="stdout.raw"&&info.Name()!="stderr.raw"{return nil};relative,e:=filepath.Rel(c.config.DataRoot,path);if e!=nil{return e};destination:=filepath.Join(target,relative);if e=os.MkdirAll(filepath.Dir(destination),0700);e!=nil{return e};raw,e:=os.ReadFile(path);if e!=nil{return e};return os.WriteFile(destination,raw,0600)});if e!=nil{t.Error(e)}
}
