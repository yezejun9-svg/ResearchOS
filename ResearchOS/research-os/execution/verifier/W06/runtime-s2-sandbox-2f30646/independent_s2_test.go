//go:build windows

package sandbox

import (
 "bufio"
 "bytes"
 "context"
 "encoding/json"
 "errors"
 "fmt"
 "os"
 "path/filepath"
 "strings"
 "sync"
 "sync/atomic"
 "testing"
 "time"

 "golang.org/x/sys/windows"
)

func TestIndependentS2Child(t *testing.T) {
 idx:=-1; for i,a:=range os.Args {if a=="--independent-s2" {idx=i;break}}
 if idx<0{return};mode:=os.Args[idx+1]
 if os.Getenv("INDEPENDENT_S2_EVIDENCE")!="" || os.Getenv("S2_HOST_CANARY")!="" || os.Getenv("HTTP_PROXY")!="" {os.Exit(91)}
 fmt.Printf("CHILD_START %d\n",time.Now().UnixNano())
 switch mode {
 case "blocked":time.Sleep(10*time.Second)
 case "echo":
  s:=bufio.NewScanner(os.Stdin);for s.Scan(){fmt.Printf("FRAME %s\n",s.Text())};if s.Err()!=nil{os.Exit(92)}
 case "overflow":fmt.Fprint(os.Stderr,strings.Repeat("z",MaxStreamBytes+1))
 case "normal":fmt.Println("NORMAL_OK")
 }
 os.Exit(0)
}

func s2assert(t *testing.T,id string,ok bool,actual any){
 t.Helper();status:="PASS";if !ok{status="FAIL"};raw,_:=json.Marshal(map[string]any{"id":id,"status":status,"actual":actual});fmt.Println("S2_INDEPENDENT_ASSERT "+string(raw));if !ok{t.Errorf("%s: %v",id,actual)}
}
func s2save(t *testing.T,name string,v any){t.Helper();raw,e:=json.MarshalIndent(v,"","  ");if e!=nil{t.Fatal(e)};if e=os.WriteFile(filepath.Join(os.Getenv("INDEPENDENT_S2_EVIDENCE"),name+".json"),raw,0600);e!=nil{t.Fatal(e)}}
func s2command(t *testing.T,mode string)Command{c:=runtimeSandboxCommand(t,"normal");c.Args=[]string{"-test.run=^TestIndependentS2Child$","--","--independent-s2",mode};return c}
func s2wait(t *testing.T,p *Process)(Receipt,error){t.Helper();ctx,cancel:=context.WithTimeout(context.Background(),8*time.Second);defer cancel();return p.Wait(ctx)}
func s2identity(t *testing.T,id Identity) windows.Handle{
 t.Helper();h,e:=windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE,false,id.PID);if e!=nil{t.Fatal(e)}
 var created,exited,kernel,user windows.Filetime;e=windows.GetProcessTimes(h,&created,&exited,&kernel,&user)
 s2assert(t,t.Name()+"-identity",e==nil&&id.Created==created.Nanoseconds()&&id.PID>0&&strings.HasPrefix(id.SID,"S-1-15-2-")&&id.Job!="",id)
 t.Cleanup(func(){windows.CloseHandle(h)});return h
}
func s2clean(t *testing.T,id string,r Receipt){
 _,e:=os.Stat(filepath.Dir(r.Directory));s2assert(t,id+"-cleanup",r.Stopped&&r.CleanupComplete&&os.IsNotExist(e),map[string]any{"stopped":r.Stopped,"cleanup":r.CleanupComplete,"stat_error":fmt.Sprint(e),"caps":r.Capabilities});s2assert(t,id+"-no-capabilities",len(r.Capabilities)==0,r.Capabilities)
}

func TestIndependentS2PersistBeforeResume(t *testing.T){
 t.Setenv("S2_HOST_CANARY","synthetic-host-only")
 var returned int64;var h windows.Handle;var chunks atomic.Int64;var persisted Identity
 c:=s2command(t,"normal")
 p,e:=Start(context.Background(),c,StartOptions{BeforeResume:func(id Identity)error{
  h=s2identity(t,id);persisted=id
  f,e:=os.Create(filepath.Join(t.TempDir(),"identity.json"));if e!=nil{return e};raw,_:=json.Marshal(id);_,e=f.Write(raw);if e==nil{e=f.Sync()};ce:=f.Close();if e!=nil{return e};if ce!=nil{return ce}
  time.Sleep(120*time.Millisecond);s2assert(t,"suspended-zero-output",chunks.Load()==0,chunks.Load());state,e:=windows.WaitForSingleObject(h,0);s2assert(t,"suspended-alive",e==nil&&state==uint32(windows.WAIT_TIMEOUT),state);returned=time.Now().UnixNano();return nil
 },OnStream:func(chunk StreamChunk)error{chunks.Add(int64(len(chunk.Data)));return nil}})
 if e!=nil{t.Fatal(e)};r,e:=s2wait(t,p);s2save(t,"persist",map[string]any{"receipt":r,"error":fmt.Sprint(e),"callback_return_ns":returned,"persisted":persisted})
 var first int64;fmt.Sscanf(string(r.Stdout),"CHILD_START %d",&first)
 s2assert(t,"child-after-persist",first>=returned&&first>0,map[string]any{"child":first,"persist_return":returned})
 s2assert(t,"normal-receipt",e==nil&&r.ExitCode==0&&r.StreamsDrained&&r.OutputCopied&&r.PID==persisted.PID&&r.Created==persisted.Created,r.ExitCode);s2clean(t,"persist",r)
}

func TestIndependentS2Veto(t *testing.T){
 var h windows.Handle;var chunks atomic.Int64;c:=s2command(t,"normal")
 p,e:=Start(context.Background(),c,StartOptions{BeforeResume:func(id Identity)error{h=s2identity(t,id);time.Sleep(80*time.Millisecond);return errors.New("independent durable write veto")},OnStream:func(chunk StreamChunk)error{chunks.Add(int64(len(chunk.Data)));return nil}})
 state,we:=windows.WaitForSingleObject(h,0);entries,de:=os.ReadDir(c.OutputDirectory)
 s2assert(t,"veto-zero-execution",p==nil&&e!=nil&&chunks.Load()==0&&we==nil&&state==windows.WAIT_OBJECT_0&&de==nil&&len(entries)==0,map[string]any{"error":fmt.Sprint(e),"chunks":chunks.Load(),"wait_state":state,"output_files":len(entries)})
}

func TestIndependentS2ConcurrentLifecycle(t *testing.T){
 c:=s2command(t,"echo");p,e:=Start(context.Background(),c,StartOptions{Interactive:true});if e!=nil{t.Fatal(e)};defer p.Cancel()
 short,cancel:=context.WithTimeout(context.Background(),30*time.Millisecond);_,we:=p.Wait(short);cancel();s2assert(t,"wait-timeout-does-not-cancel",errors.Is(we,context.DeadlineExceeded),fmt.Sprint(we))
 errs:=make(chan error,8);var wg sync.WaitGroup
 for i:=0;i<8;i++{wg.Add(1);go func(n int){defer wg.Done();errs<-p.Write(context.Background(),[]byte(fmt.Sprintf("%02d-%s\n",n,strings.Repeat("q",1024))))}(i)}
 wg.Wait();close(errs);good:=true;for e:=range errs{good=good&&e==nil};s2assert(t,"concurrent-write-complete",good,good)
 e=p.CloseInput();s2assert(t,"close-input",e==nil,fmt.Sprint(e));r,e:=s2wait(t,p);s2save(t,"concurrent",map[string]any{"receipt":r,"error":fmt.Sprint(e)})
 lines:=strings.Split(strings.TrimSpace(string(r.Stdout)),"\n");seen:=map[string]bool{};valid:=true
 for _,line:=range lines[1:]{if !strings.HasPrefix(line,"FRAME ")||len(line)!=6+3+1024{valid=false};seen[strings.TrimPrefix(line,"FRAME ")[:2]]=true}
 s2assert(t,"frames-not-interleaved",valid&&len(seen)==8,map[string]any{"frames":len(seen),"lines":len(lines)})
 s2assert(t,"closed-write-rejected",p.Write(context.Background(),[]byte("no\n"))!=nil,true)
 again,ae:=s2wait(t,p);s2assert(t,"repeat-wait",e==nil&&ae==nil&&again.PID==r.PID&&bytes.Equal(again.Stdout,r.Stdout)&&r.StreamsDrained,true);s2clean(t,"concurrent",r)
}

func TestIndependentS2BlockedWriteCancel(t *testing.T){
 c:=s2command(t,"blocked");p,e:=Start(context.Background(),c,StartOptions{Interactive:true});if e!=nil{t.Fatal(e)}
 ctx,done:=context.WithTimeout(context.Background(),100*time.Millisecond);defer done();start:=time.Now();we:=p.Write(ctx,bytes.Repeat([]byte("x"),64*1024))
 s2assert(t,"blocked-write-deadline",errors.Is(we,context.DeadlineExceeded)&&time.Since(start)<time.Second,map[string]any{"error":fmt.Sprint(we),"elapsed_ms":time.Since(start).Milliseconds()})
 cancelled:=make(chan struct{});go func(){p.Cancel();close(cancelled)}();select{case<-cancelled:s2assert(t,"cancel-no-deadlock",true,true);case<-time.After(3*time.Second):s2assert(t,"cancel-no-deadlock",false,"timeout")}
 r,e:=s2wait(t,p);s2save(t,"blocked-write",map[string]any{"receipt":r,"error":fmt.Sprint(e)})
 s2assert(t,"blocked-writer-released",r.Stopped&&r.ExitCode==124&&r.TimedOut&&p.Write(context.Background(),[]byte("x"))!=nil,map[string]any{"receipt_exit":r.ExitCode,"wait_error":fmt.Sprint(e),"drained":r.StreamsDrained});s2clean(t,"blocked-write",r)
}

func TestIndependentS2StreamError(t *testing.T){
 for _,mode:=range []string{"callback","overflow"}{t.Run(mode,func(t *testing.T){
  cmode:="blocked";options:=StartOptions{};if mode=="overflow"{cmode="overflow"}else{options.OnStream=func(StreamChunk)error{return errors.New("independent stream sink rejected")}}
  p,e:=Start(context.Background(),s2command(t,cmode),options);if e!=nil{t.Fatal(e)};r,e:=s2wait(t,p);s2save(t,"stream-"+mode,map[string]any{"receipt":r,"error":fmt.Sprint(e)})
  s2assert(t,mode+"-not-drained",e!=nil&&!r.StreamsDrained&&len(r.Stderr)<=MaxStreamBytes,map[string]any{"error":fmt.Sprint(e),"stderr_bytes":len(r.Stderr),"drained":r.StreamsDrained});s2clean(t,mode,r)
 })}
}

func TestIndependentS2RunCompatibility(t *testing.T){
 for _,mode:=range []string{"normal","timeout"}{t.Run(mode,func(t *testing.T){cmode:="normal";if mode=="timeout"{cmode="blocked"};c:=s2command(t,cmode);if mode=="timeout"{c.Timeout=100*time.Millisecond};r,e:=Run(context.Background(),c);s2save(t,"run-"+mode,map[string]any{"receipt":r,"error":fmt.Sprint(e)});want:=0;if mode=="timeout"{want=124};s2assert(t,"run-"+mode,e==nil&&r.ExitCode==want&&r.StreamsDrained&&r.TimedOut==(mode=="timeout"),map[string]any{"error":fmt.Sprint(e),"exit":r.ExitCode,"drained":r.StreamsDrained});s2clean(t,"run-"+mode,r)})}
}
