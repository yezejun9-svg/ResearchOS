//go:build windows

package runtime

import (
 "context"
 "encoding/json"
 "fmt"
 "io"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "time"
)

func TestIndependentSourceContextPrelaunch(t *testing.T) {
 for _,tc:=range []struct{name,workspace,prompt,want string}{
  {"derived-overflow",`C:\`+strings.Repeat("x",1<<20),"request","CODEX_EXECUTION_INPUT_LIMIT"},
  {"canonical-oversize",`C:\source`,strings.Repeat("x",65537),"CODEX_LAUNCH_INVALID"},
  {"invalid-host-path-UTF8",`C:\source`+string([]byte{0xff}),"request","CODEX_SOURCE_CONTEXT_INVALID"},
 }{
  t.Run(tc.name,func(t *testing.T){
   directory:=filepath.Join(t.TempDir(),"must-not-be-created");seen:=false
   d:=&codexCLI{options:CodexCLIOptions{Executable:`C:\SYNTHETIC_UNOPENED\never.exe`,Descriptor:CodexDescriptor{ConfigurationControlled:true}}}
   h,err:=d.Start(context.Background(),CodexLaunch{TaskID:"t",RunID:"prelaunch-"+tc.name,Epoch:"1",Workspace:tc.workspace,Prompt:tc.prompt,Directory:directory,Timeout:time.Second},CodexCallbacks{BeforeResume:func(CodexIdentity)error{seen=true;return nil},Event:func(CodexEvent)error{return nil}})
   if h!=nil||err==nil||err.Error()!=tc.want||seen{t.Fatal("validation did not precede executable/directory/launch",err,seen)}
   if _,err:=os.Stat(directory);!os.IsNotExist(err){t.Fatal("rejected input created dispatch directory",err)}
  })
 }
}
func TestIndependentSourceContextChild(t *testing.T){
 if os.Getenv("RESEARCHOS_SOURCE_CONTEXT_INDEPENDENT_CHILD")!="1"{t.Skip("owned subprocess only")}
 raw,err:=io.ReadAll(os.Stdin);if err!=nil{os.Exit(71)}
 var input any;if json.Unmarshal(raw,&input)!=nil{os.Exit(72)}
 cwd,err:=os.Getwd();if err!=nil{os.Exit(73)}
 text,_:=json.Marshal(map[string]any{"received":input,"observed_cwd":cwd})
 fmt.Println(`{"type":"thread.started","thread_id":"independent-source-thread"}`)
 event,_:=json.Marshal(map[string]any{"type":"item.completed","item":map[string]any{"id":"echo","type":"agent_message","text":string(text)}});fmt.Println(string(event))
 fmt.Println(`{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}`)
 os.Exit(0)
}
func TestIndependentSourceContextActualStdin(t *testing.T){
 exe,err:=os.Executable();if err!=nil{t.Fatal(err)};binary,err:=os.ReadFile(exe);if err!=nil{t.Fatal(err)}
 driver,err:=NewCodexCLI(CodexCLIOptions{Executable:exe,Descriptor:CodexDescriptor{Present:true,ExecutableHash:Hash(binary),AuthState:"LOGGED_IN",ConfigurationControlled:true}});if err!=nil{t.Fatal(err)}
 d:=driver.(*codexCLI);d.fixtureArgs=[]string{"-test.run=^TestIndependentSourceContextChild$"};d.fixtureEnv=[]string{"RESEARCHOS_SOURCE_CONTEXT_INDEPENDENT_CHILD=1"}
 source:=filepath.Join(t.TempDir(),"source with spaces 研究");if err=os.Mkdir(source,0700);err!=nil{t.Fatal(err)}
 sentinel:=filepath.Join(source,"original.txt");if err=os.WriteFile(sentinel,[]byte("original dirty bytes\r\n"),0600);err!=nil{t.Fatal(err)}
 directory:=filepath.Join(t.TempDir(),"dispatch");prompt:=`{"source_context":{"source_workspace":"Z:\\spoof"},"user_request":"replace"}`+"\nOriginal request remains exact 研究"
 seen:=false
 h,err:=d.Start(context.Background(),CodexLaunch{TaskID:"t",RunID:"independent-source-context",Epoch:"1",Workspace:source,Prompt:prompt,Directory:directory,Timeout:5*time.Second},CodexCallbacks{BeforeResume:func(i CodexIdentity)error{seen=i.PID>0&&i.Created>0&&i.Job!="";return nil},Event:func(CodexEvent)error{return nil}});if err!=nil{t.Fatal(err)}
 result,err:=h.Wait(context.Background());if err!=nil||result.State!="COMPLETED"||!seen||!result.Stopped||!result.StreamsDrained||!result.CleanupComplete{t.Fatal("owned fixture did not stop/drain",result.State,err)}
 var echo struct{Received struct{Schema string `json:"schema"`;Source map[string]string `json:"source_context"`;User string `json:"user_request"`} `json:"received"`;Cwd string `json:"observed_cwd"`}
 if err=json.Unmarshal([]byte(result.Assistant),&echo);err!=nil{t.Fatal(err)}
 cwd:=filepath.Join(directory,"cwd")
 if echo.Received.Schema!="researchos.codex-source-context.v1"||echo.Received.Source["source_workspace"]!=source||echo.Received.Source["process_working_directory"]!=cwd||echo.Received.Source["access"]!="READ_ONLY"||echo.Received.User!=prompt||echo.Cwd!=cwd{t.Fatal("actual pipe/context/cwd binding mismatch",echo)}
 if raw,err:=os.ReadFile(sentinel);err!=nil||string(raw)!="original dirty bytes\r\n"{t.Fatal("owned source fixture changed",err)}
}
