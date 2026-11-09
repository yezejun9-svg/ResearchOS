//go:build windows

package runtime

import (
    "context"
    "fmt"
    "io"
    "os"
    "path/filepath"
    "strings"
    "testing"
    "time"
)

func TestIndependentHarnessChild(t *testing.T) {
    mode := os.Getenv("RESEARCHOS_INDEPENDENT_FAKE_CHILD")
    if mode == "" { t.Skip("owned helper entry; parent tests carry assertions") }
    _, _ = io.ReadAll(os.Stdin)
    if mode == "EMPTY_THREAD" {
        fmt.Println(`{"type":"thread.started","thread_id":""}`)
    } else if mode == "WHITESPACE_THREAD" {
        fmt.Println(`{"type":"thread.started","thread_id":"  "}`)
    } else if mode == "LONG_THREAD" {
        fmt.Printf("{\"type\":\"thread.started\",\"thread_id\":%q}\n",strings.Repeat("x",257))
    } else if mode != "NO_THREAD" {
        fmt.Println(`{"type":"thread.started","thread_id":"owned-thread-a"}`)
    }
    if mode == "CONFLICTING_THREADS" {
        fmt.Println(`{"type":"thread.started","thread_id":"owned-thread-b"}`)
    }
    if mode == "SAME_THREAD" { fmt.Println(`{"type":"thread.started","thread_id":"owned-thread-a"}`) }
    fmt.Println(`{"type":"item.completed","item":{"id":"owned-message","type":"agent_message","text":"owned fixture response"}}`)
    fmt.Println(`{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}`)
    os.Exit(0)
}

func independentHarnessResult(t *testing.T, mode string) (CodexResult, string, *codexCLI) {
    t.Helper()
    executable, err := os.Executable()
    if err != nil { t.Fatal(err) }
    raw, err := os.ReadFile(executable)
    if err != nil { t.Fatal(err) }
    driver, err := NewCodexCLI(CodexCLIOptions{Executable:executable, Descriptor:CodexDescriptor{
        Present:true, ExecutableHash:Hash(raw), AuthState:"LOGGED_IN", ConfigurationControlled:true,
    }})
    if err != nil { t.Fatal(err) }
    d := driver.(*codexCLI)
    d.fixtureArgs=[]string{"-test.run=^TestIndependentHarnessChild$"}
    d.fixtureEnv=[]string{"RESEARCHOS_INDEPENDENT_FAKE_CHILD="+mode}
    directory:=filepath.Join(t.TempDir(),"dispatch")
    launched:=false
    handle, err := d.Start(context.Background(), CodexLaunch{TaskID:"owned-task",RunID:"owned-run-"+mode,
        Epoch:"1",Workspace:t.TempDir(),Prompt:"owned bounded fixture",Directory:directory,Timeout:5*time.Second},
        CodexCallbacks{BeforeResume:func(identity CodexIdentity)error{
            if identity.PID==0 || identity.Created==0 || identity.Job=="" { return fmt.Errorf("missing real owned identity") }
            launched=true;return nil
        },Event:func(CodexEvent)error{return nil}})
    if err != nil { t.Fatal(err) }
    result, err := handle.Wait(context.Background())
    if err != nil && (mode=="CONTROL" || mode=="SAME_THREAD") { t.Fatal(err) }
    if !launched || !result.Stopped {
        t.Fatalf("owned process failed lifecycle control: %+v",result)
    }
    if (mode=="CONTROL" || mode=="SAME_THREAD") && (!result.StreamsDrained || !result.CleanupComplete) { t.Fatalf("valid protocol did not drain: %+v",result) }
    return result, filepath.Join(directory,"cwd"), d
}

func TestIndependentHarnessRecognizedProjectMarker(t *testing.T) {
    result,cwd,d:=independentHarnessResult(t,"CONTROL")
    if result.State!="COMPLETED" || result.ThreadID!="owned-thread-a" { t.Fatalf("valid control failed: %+v",result) }
    // Pinned Codex0.166 discover_project_root ignores a .git directory without HEAD.
    // Verify the actual fixed-argv marker, not mere existence of an arbitrary directory.
    markers:=[]string{}
    for _,arg:=range d.arguments(cwd,t.TempDir()) {
        if strings.HasPrefix(arg,"project_root_markers=") {
            if strings.Contains(arg,`".git"`) { markers=append(markers,".git") }
            if strings.Contains(arg,`".researchos-codex-root"`) { markers=append(markers,".researchos-codex-root") }
        }
    }
    recognized:=false
    for _,marker:=range markers {
        info,err:=os.Stat(filepath.Join(cwd,marker))
        if err!=nil { continue }
        if marker==".git" && info.IsDir() {
            if _,err=os.Stat(filepath.Join(cwd,marker,"HEAD"));err!=nil { continue }
        }
        recognized=true
    }
    if !recognized { t.Fatal("pinned Codex0.166 does not recognize actual owned cwd marker; ancestor project inheritance remains possible") }
}

func TestIndependentHarnessThreadIdentityRequired(t *testing.T) {
    for _,mode:=range []string{"NO_THREAD","CONFLICTING_THREADS","EMPTY_THREAD","WHITESPACE_THREAD","LONG_THREAD"} {
        t.Run(mode,func(t *testing.T){
            result,_,_:=independentHarnessResult(t,mode)
            if result.State!="UNKNOWN" && result.State!="FAILED" {
                t.Fatalf("invalid native thread identity accepted as COMPLETED: mode=%s thread=%q",mode,result.ThreadID)
            }
        })
    }
}

func TestIndependentHarnessRepeatedSameThreadIsIdempotent(t *testing.T) {
    result,_,_:=independentHarnessResult(t,"SAME_THREAD")
    if result.State!="COMPLETED" || result.ThreadID!="owned-thread-a" { t.Fatalf("same identity duplicate was not idempotent: %+v",result) }
}
