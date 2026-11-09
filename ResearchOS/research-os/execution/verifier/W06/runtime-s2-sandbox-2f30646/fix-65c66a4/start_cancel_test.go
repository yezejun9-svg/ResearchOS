//go:build windows

package sandbox

import (
 "context"
 "errors"
 "fmt"
 "os"
 "path/filepath"
 "sync/atomic"
 "testing"
 "time"

 "golang.org/x/sys/windows"
)

func TestIndependentStartCancellationFence(t *testing.T) {
 ctx,cancel:=context.WithCancel(context.Background());defer cancel()
 entered:=make(chan struct{});release:=make(chan struct{});finished:=make(chan struct{})
 var process *Process;var startError error;var handle windows.Handle;var stage string;var callbackError error;var chunks atomic.Int64
 go func(){process,startError=Start(ctx,runtimeSandboxCommand(t,"normal"),StartOptions{BeforeResume:func(id Identity)error{
  handle,callbackError=windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE,false,id.PID)
  if callbackError==nil{buf:=make([]uint16,32768);size:=uint32(len(buf));callbackError=windows.QueryFullProcessImageName(handle,0,&buf[0],&size);if callbackError==nil{stage=filepath.Dir(filepath.Dir(windows.UTF16ToString(buf[:size])))}}
  cancel();close(entered);<-release;return callbackError
 },OnStream:func(c StreamChunk)error{chunks.Add(int64(len(c.Data)));return nil}});close(finished)}()
 select{case<-entered:case<-time.After(5*time.Second):close(release);t.Fatal("callback not reached")}
 before:=false;select{case<-finished:before=true;case<-time.After(60*time.Millisecond):}
 s2assert(t,"start-cancel-waits-for-owned-cleanup",!before,before)
 close(release);select{case<-finished:case<-time.After(3*time.Second):t.Fatal("cleanup fence did not finish")}
 if handle!=0{defer windows.CloseHandle(handle)}
 state,e:=windows.WaitForSingleObject(handle,0);_,se:=os.Stat(stage)
 s2assert(t,"start-cancel-no-process-returned",process==nil&&errors.Is(startError,context.Canceled),fmt.Sprint(startError))
 s2assert(t,"start-cancel-child-already-stopped",callbackError==nil&&e==nil&&state==windows.WAIT_OBJECT_0,map[string]any{"state":state,"error":fmt.Sprint(e),"callback_error":fmt.Sprint(callbackError)})
 s2assert(t,"start-cancel-staging-already-removed",stage!=""&&os.IsNotExist(se),map[string]any{"stage":stage,"stat_error":fmt.Sprint(se)})
 s2assert(t,"start-cancel-never-executed-child",chunks.Load()==0,chunks.Load())
 s2save(t,"start-cancel",map[string]any{"returned_before_callback_cleanup":before,"error":fmt.Sprint(startError),"process_returned":process!=nil,"child_wait_state":state,"stage":stage,"stage_removed":os.IsNotExist(se),"output_bytes":chunks.Load()})
}
