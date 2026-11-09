//go:build windows

package sandbox

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"
)

// These tests never call Start/Run or Windows. They drive the actual private
// production coordinator with an original fake handle identity and clock.
type fakeSandboxLife struct {
	t *testing.T
	now time.Time
	start time.Time
	signaled bool
	active uint32
	code uint32
	closed bool
	autoStop bool
	primaryErr, accountErr, terminateErr, closeErr, exitErr error
	events []string
	termCodes []uint32
	stdout, stderr chan streamResult
	onPause func(*fakeSandboxLife)
	onTerminate func(*fakeSandboxLife)
}

func fakeLife(t *testing.T) *fakeSandboxLife {
	now:=time.Unix(1700000000,0)
	return &fakeSandboxLife{t:t,now:now,start:now,active:1,autoStop:true,
		stdout:make(chan streamResult,1),stderr:make(chan streamResult,1)}
}
func (f *fakeSandboxLife) eof() {
	f.stdout<-finalStreamResult([]byte("out"),nil,true)
	f.stderr<-finalStreamResult([]byte{},nil,true)
}
func (f *fakeSandboxLife) ops() sandboxLifecycleOps {
	jobOpen:=func(){if f.closed {f.t.Fatal("operation reused closed fake original Job")}}
	return sandboxLifecycleOps{
		now:func()time.Time{return f.now},
		pause:func(d time.Duration){if d<=0 {f.t.Fatal("non-progressing pause")};f.now=f.now.Add(d);if f.onPause!=nil{f.onPause(f)}},
		primary:func()(bool,error){jobOpen();return f.signaled,f.primaryErr},
		account:func()(uint32,uint32,error){jobOpen();return 3,f.active,f.accountErr},
		terminate:func(code uint32)error{
			jobOpen();f.events=append(f.events,"terminate-original");f.termCodes=append(f.termCodes,code)
			if f.terminateErr==nil && f.autoStop {if !f.signaled{f.code=code};f.signaled=true;f.active=0}
			if f.onTerminate!=nil {f.onTerminate(f)}
			return f.terminateErr
		},
		closeJob:func()error{jobOpen();f.closed=true;f.events=append(f.events,"close-original-job");return f.closeErr},
		exitCode:func()(uint32,error){jobOpen();if !f.signaled{f.t.Fatal("exit code without original primary signal")};return f.code,f.exitErr},
		closeReaders:func()error{if !f.closed{f.t.Fatal("reader close blocked Job fail-safe")};f.events=append(f.events,"close-readers");return nil},
	}
}
func (f *fakeSandboxLife) run(ctx context.Context, timeout time.Duration, initial error) sandboxLifecycleResult {
	r:=coordinateSandboxLifecycle(ctx,f.start.Add(timeout),initial,f.ops(),f.stdout,f.stderr)
	if !f.closed {f.t.Fatal("Job fail-safe was never closed")}
	if len(f.termCodes)>1 {f.t.Fatal("termination was retried")}
	if f.now.Sub(f.start)>timeout+sandboxCleanupBudget {f.t.Fatal("cleanup budget was extended")}
	return r
}
func readyOnTerminate(f *fakeSandboxLife){f.eof()}

func TestSandboxLifecycleNormal(t *testing.T){
	f:=fakeLife(t);f.signaled=true;f.active=0;f.eof()
	r:=f.run(context.Background(),time.Minute,nil)
	if !r.resourcesQuiescent()||r.err!=nil||r.timedOut||len(f.termCodes)!=0||r.code!=0 {t.Fatalf("normal: %+v",r)}
	if r.stderr==nil {t.Fatal("empty natural EOF must remain []")}
}
func TestSandboxLifecycleInteractivePrimaryRemainsLive(t *testing.T){
	f:=fakeLife(t);steps:=0;f.onPause=func(f *fakeSandboxLife){steps++;if steps==4{f.signaled=true;f.active=0;f.eof()}}
	r:=f.run(context.Background(),time.Minute,nil)
	if !r.resourcesQuiescent()||r.err!=nil||len(f.termCodes)!=0||steps!=4{t.Fatalf("interactive changed: %+v",r)}
}
func TestSandboxLifecycleChildCompletesWithinGrace(t *testing.T){
	f:=fakeLife(t);f.signaled=true;f.active=2;done:=false
	f.onPause=func(f *fakeSandboxLife){if !done&&f.now.Sub(f.start)>=200*time.Millisecond{done=true;f.active=0;f.eof()}}
	r:=f.run(context.Background(),time.Minute,nil)
	if !r.resourcesQuiescent()||r.err!=nil||len(f.termCodes)!=0{t.Fatalf("grace: %+v",r)}
}
func TestSandboxLifecycleHeldChildAfterPrimaryIsForcedError(t *testing.T){
	f:=fakeLife(t);f.signaled=true;f.active=2;f.onTerminate=readyOnTerminate
	r:=f.run(context.Background(),time.Minute,nil)
	if !r.resourcesQuiescent()||r.err==nil||!strings.Contains(r.err.Error(),"descendants")||r.code!=0||r.timedOut {t.Fatalf("forced primary0 accepted: %+v",r)}
	if f.now.Sub(f.start)!=sandboxChildGrace||len(f.termCodes)!=1||f.termCodes[0]!=125{t.Fatal("grace/termination changed")}
}
func TestSandboxLifecycleCancellationEachProcessPhase(t *testing.T){
	for _,primaryDone:=range []bool{false,true}{t.Run(map[bool]string{false:"running",true:"grace"}[primaryDone],func(t *testing.T){
		f:=fakeLife(t);f.signaled=primaryDone;f.onTerminate=readyOnTerminate;ctx,cancel:=context.WithCancel(context.Background());defer cancel()
		f.onPause=func(f *fakeSandboxLife){if f.now.Sub(f.start)>=40*time.Millisecond{cancel()}}
		r:=f.run(ctx,time.Minute,nil)
		if !r.resourcesQuiescent()||!r.timedOut||r.err!=nil||len(f.termCodes)!=1||f.termCodes[0]!=124{t.Fatalf("cancel: %+v",r)}
	})}
}
func TestSandboxLifecycleCommandTimeout(t *testing.T){
	f:=fakeLife(t);f.onTerminate=readyOnTerminate
	r:=f.run(context.Background(),80*time.Millisecond,nil)
	if !r.resourcesQuiescent()||!r.timedOut||r.code!=124||r.err!=nil{t.Fatalf("timeout: %+v",r)}
}
func TestSandboxLifecycleStreamFaultEachProcessPhase(t *testing.T){
	for _,primaryDone:=range []bool{false,true}{t.Run(map[bool]string{false:"running",true:"grace"}[primaryDone],func(t *testing.T){
		f:=fakeLife(t);f.signaled=primaryDone;failure:=errors.New("stream callback or size fault")
		f.stdout<-finalStreamResult([]byte("partial"),failure,false)
		f.onTerminate=func(f *fakeSandboxLife){f.stderr<-finalStreamResult(nil,nil,true)}
		r:=f.run(context.Background(),time.Minute,nil)
		if !r.stopped||r.drained||r.resourcesQuiescent()||!errors.Is(r.err,failure)||len(f.termCodes)!=1{t.Fatalf("stream fault: %+v",r)}
	})}
}
func TestSandboxLifecyclePrimaryWaitFailure(t *testing.T){
	f:=fakeLife(t);f.primaryErr=errors.New("wait failure");f.onTerminate=readyOnTerminate
	r:=f.run(context.Background(),time.Minute,nil)
	if r.stopped||r.drained||r.resourcesQuiescent()||!errors.Is(r.err,f.primaryErr)||f.now.Sub(f.start)!=sandboxCleanupBudget{t.Fatalf("wait failure: %+v",r)}
}
func TestSandboxLifecycleJobAccountingFailure(t *testing.T){
	f:=fakeLife(t);f.accountErr=errors.New("query failure");f.onTerminate=readyOnTerminate
	r:=f.run(context.Background(),time.Minute,nil)
	if r.stopped||r.drained||r.resourcesQuiescent()||!errors.Is(r.err,f.accountErr){t.Fatalf("query failure: %+v",r)}
}
func TestSandboxLifecycleTerminateFailureRetainsUnknown(t *testing.T){
	f:=fakeLife(t);f.signaled=true;f.terminateErr=errors.New("terminate failure")
	r:=f.run(context.Background(),time.Minute,nil)
	if r.stopped||r.drained||r.resourcesQuiescent()||!errors.Is(r.err,f.terminateErr)||f.now.Sub(f.start)!=sandboxChildGrace+sandboxCleanupBudget{t.Fatalf("terminate failure: %+v",r)}
}
func TestSandboxLifecycleActiveZeroWithoutPrimarySignal(t *testing.T){
	f:=fakeLife(t);f.active=0;f.autoStop=false;f.eof()
	r:=f.run(context.Background(),40*time.Millisecond,nil)
	if r.stopped||r.resourcesQuiescent()||r.codeKnown||r.err==nil{t.Fatalf("missing primary signal accepted: %+v",r)}
}
func TestSandboxLifecycleNoStreamsBlockedCallbackAndLateEOF(t *testing.T){
	for _,mode:=range []string{"missing-both","held-stdout-callback","late-EOF"}{t.Run(mode,func(t *testing.T){
		f:=fakeLife(t);f.signaled=true;f.active=0
		if mode=="held-stdout-callback"{f.stderr<-finalStreamResult(nil,nil,true)}
		r:=f.run(context.Background(),time.Minute,nil)
		if !r.stopped||r.drained||r.resourcesQuiescent()||r.err==nil||f.now.Sub(f.start)!=sandboxCleanupBudget{t.Fatalf("missing stream: %+v",r)}
		if mode=="late-EOF"{f.eof();if r.drained||r.resourcesQuiescent(){t.Fatal("late result upgraded terminal proof")}}
	})}
}
func TestSandboxLifecycleCancelDuringDrainHasNoStaleJobOperation(t *testing.T){
	f:=fakeLife(t);f.signaled=true;f.active=0;ctx,cancel:=context.WithCancel(context.Background());defer cancel()
	f.onPause=func(f *fakeSandboxLife){if !f.closed{t.Fatal("drain before Job close")};cancel()}
	r:=f.run(ctx,time.Minute,nil)
	if r.drained||!r.stopped||!r.timedOut||len(f.termCodes)!=0{t.Fatalf("drain cancellation: %+v",r)}
}
func TestSandboxLifecyclePreResumeErrorsUseSameOwnedStop(t *testing.T){
	for _,stage:=range []string{"process-times","before-resume-veto","context-before-resume","resume-failed"}{t.Run(stage,func(t *testing.T){
		f:=fakeLife(t);f.onTerminate=readyOnTerminate;veto:=errors.New(stage)
		r:=f.run(context.Background(),time.Minute,veto)
		if !r.resourcesQuiescent()||!errors.Is(r.err,veto)||len(f.termCodes)!=1||f.termCodes[0]!=125||r.timedOut{t.Fatalf("suspended cleanup: %+v",r)}
	})}
}
func TestSandboxLifecycleHandleCloseAndExitQueryFailuresRetainResources(t *testing.T){
	for _,stage:=range []string{"job-close","exit-code"}{t.Run(stage,func(t *testing.T){
		f:=fakeLife(t);f.signaled=true;f.active=0;f.eof()
		if stage=="job-close"{f.closeErr=errors.New(stage)}else{f.exitErr=errors.New(stage)}
		r:=f.run(context.Background(),time.Minute,nil)
		if r.resourcesQuiescent()||r.err==nil{t.Fatalf("unknown handle state accepted: %+v",r)}
	})}
}
func TestSandboxLifecycleForcedReadCloseNeverEqualsNaturalEOF(t *testing.T){
	f:=fakeLife(t);f.signaled=true;f.active=0
	f.stdout<-finalStreamResult(nil,nil,false);f.stderr<-finalStreamResult(nil,nil,true)
	r:=f.run(context.Background(),time.Minute,nil)
	if r.drained||r.resourcesQuiescent()||r.err==nil{t.Fatal("non-natural result accepted")}
}
func TestSandboxLifecycleStreamSnapshotOwnsBytes(t *testing.T){
	source:=[]byte("actual stream");result:=finalStreamResult(source,nil,true);source[0]='X'
	if string(result.bytes)!="actual stream"||!result.eof{t.Fatal("late collector mutated snapshot")}
	if finalStreamResult(nil,nil,true).bytes==nil{t.Fatal("EOF null is not []")}
}
func TestSandboxLifecycleQueuedWriteCancellationDoesNotCancelProcess(t *testing.T){
	cancelled:=0;p:=&Process{writeGate:make(chan struct{},1),stopped:make(chan struct{}),done:make(chan struct{}),cancel:func(){cancelled++}}
	p.writeGate<-struct{}{};ctx,cancel:=context.WithTimeout(context.Background(),time.Millisecond);defer cancel()
	if err:=p.Write(ctx,[]byte("queued"));!errors.Is(err,context.DeadlineExceeded)||cancelled!=0||len(p.writeGate)!=1{t.Fatal("queued cancellation changed active writer")}
}
