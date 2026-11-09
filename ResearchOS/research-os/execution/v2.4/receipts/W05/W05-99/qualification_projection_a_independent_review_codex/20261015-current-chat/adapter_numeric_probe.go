package main

import (
 "bytes"
 "encoding/json"
 "fmt"
 "researchos.local/research-os/internal/runtimepolicy"
)

func main() {
 config:=map[string]any{"route":"fixture","max_calls":json.Number("8"),"tools":[]any{}}
 configHash,_:=runtimepolicy.Hash(config)
 ref:=map[string]any{"id":"profile","revision":json.Number("1")}
 refHash,_:=runtimepolicy.Hash(ref)
 m:=map[string]any{"project_id":"p","task_id":"t","run_id":"r","runtime_id":"rt","dispatch_key":"d","epoch":json.Number("1"),"admission":map[string]any{"qualification_bootstrap":true,"profile_ref":ref,"profile_hash":refHash,"permission":map[string]any{"purpose":"runtime_qualification","plan_hash":"sha256:fixture"},"profile":map[string]any{"backend":"mu-sdk-broker-v1","model_config":config,"model_qualification":map[string]any{"route":"fixture","model_config_hash":configHash,"max_calls":json.Number("1")}}}}
 if err:=runtimepolicy.Prepare(m,"runtime_qualification");err!=nil {panic(err)}
 _,err:=runtimepolicy.Effective(m,"");fmt.Printf("original positive control: %v\n",err)
 if err!=nil {panic(err)}
 raw,_:=json.Marshal(m)
 var ordinary map[string]any
 if err:=json.Unmarshal(raw,&ordinary);err!=nil {panic(err)}
 _,err=runtimepolicy.Effective(ordinary,"");fmt.Printf("json.Unmarshal unmodified control: %v epoch_type=%T\n",err,ordinary["epoch"])
 if err==nil {panic("expected invalid numeric positive-control finding not reproduced")}
 var preserved map[string]any
 dec:=json.NewDecoder(bytes.NewReader(raw));dec.UseNumber()
 if err:=dec.Decode(&preserved);err!=nil {panic(err)}
 _,err=runtimepolicy.Effective(preserved,"");fmt.Printf("UseNumber unmodified control: %v epoch_type=%T\n",err,preserved["epoch"])
 if err!=nil {panic(err)}
}
