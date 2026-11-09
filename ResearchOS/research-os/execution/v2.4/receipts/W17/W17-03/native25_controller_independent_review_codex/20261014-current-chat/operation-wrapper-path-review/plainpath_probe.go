package main
import("encoding/json";"errors";"os";"path/filepath";"strings")
func plainPath(path string) error {
    a,e:=filepath.Abs(path); if e!=nil || a!=filepath.Clean(path) || strings.HasPrefix(path,`\\`) { return errors.New("AUTHORITY_ABSOLUTE_LOCAL_PATH") }
    real,e:=filepath.EvalSymlinks(path); if e!=nil || !strings.EqualFold(real,path) { return errors.New("AUTHORITY_REPARSE_PATH") }; return nil
}
func main(){
 p:=os.Args[1]
 native:=filepath.Clean(p)
 forward:=strings.ReplaceAll(native,`\`,"/")
 out:=[]map[string]any{}
 for _,v:=range []struct{name,path string}{{"backslash",native},{"forward_slash",forward},{"cleaned_forward_slash",filepath.Clean(forward)}}{
  real,evalerr:=filepath.EvalSymlinks(v.path)
  verdict:=plainPath(v.path)
  record:=map[string]any{"case":v.name,"path":v.path,"clean":filepath.Clean(v.path),"eval_symlinks":real,"accepted":verdict==nil,"file_contents_read":false}
  if evalerr!=nil {record["eval_error"]=evalerr.Error()}
  if verdict!=nil {record["error"]=verdict.Error()}
  out=append(out,record)
 }
 json.NewEncoder(os.Stdout).Encode(out)
}
