//go:build windows

package sandbox

import (
 "bytes"
 "context"
 "errors"
 "fmt"
 "testing"
 "time"
)

func TestIndependentS2QueuedWriteDeadlineFixed(t *testing.T) {
 p,e:=Start(context.Background(),s2command(t,"blocked"),StartOptions{Interactive:true});if e!=nil{t.Fatal(e)}
 first:=make(chan error,1);go func(){first<-p.Write(context.Background(),bytes.Repeat([]byte("a"),64*1024))}()
 deadline:=time.Now().Add(time.Second)
 for len(p.writeGate)==0 {if time.Now().After(deadline){p.Cancel();t.Fatal("writer did not acquire gate")};time.Sleep(time.Millisecond)}
 ctx,cancel:=context.WithTimeout(context.Background(),40*time.Millisecond);defer cancel()
 second:=make(chan error,1);start:=time.Now();go func(){second<-p.Write(ctx,[]byte("should-not-send\n"))}()
 var secondError error;returned:=false
 select{case secondError=<-second:returned=true;case<-time.After(200*time.Millisecond):}
 waited:=time.Since(start).Milliseconds()
 active:=true;select{case<-p.stopped:active=false;default:}
 firstStillBlocked:=true;select{case<-first:firstStillBlocked=false;default:}
 p.Cancel();if !returned{select{case secondError=<-second:case<-time.After(time.Second):t.Fatal("queued writer not released by cancellation")}}
 if firstStillBlocked {select{case<-first:case<-time.After(time.Second):t.Fatal("first writer not released")}}
 r,we:=s2wait(t,p);s2save(t,"queued-write-fixed",map[string]any{"receipt":r,"wait_error":fmt.Sprint(we),"queued_error":fmt.Sprint(secondError),"returned_before_200ms":returned,"deadline_ms":40,"observed_wait_ms":waited,"active_writer_not_cancelled":active&&firstStillBlocked})
 s2clean(t,"queued-write-fixed",r)
 s2assert(t,"queued-write-honors-own-deadline-fixed",returned&&errors.Is(secondError,context.DeadlineExceeded),map[string]any{"deadline_ms":40,"waited_ms":waited,"returned":returned,"eventual_error":fmt.Sprint(secondError)})
 s2assert(t,"queued-deadline-preserves-active-writer",active&&firstStillBlocked,map[string]any{"active":active,"first_write_blocked":firstStillBlocked})
}

func TestIndependentS2AlreadyCancelledFrame(t *testing.T) {
 p,e:=Start(context.Background(),s2command(t,"echo"),StartOptions{Interactive:true});if e!=nil{t.Fatal(e)};defer p.Cancel()
 ctx,cancel:=context.WithCancel(context.Background());cancel();e=p.Write(ctx,[]byte("MUST_NOT_SEND\n"))
 s2assert(t,"cancelled-frame-rejected-before-write",errors.Is(e,context.Canceled),fmt.Sprint(e))
 good:=p.Write(context.Background(),[]byte("ONLY_ALLOWED\n"));p.CloseInput();r,we:=s2wait(t,p)
 s2save(t,"already-cancelled",map[string]any{"receipt":r,"error":fmt.Sprint(we)})
 s2assert(t,"cancelled-frame-no-side-effect",good==nil&&we==nil&&r.ExitCode==0&&!bytes.Contains(r.Stdout,[]byte("MUST_NOT_SEND"))&&bytes.Contains(r.Stdout,[]byte("FRAME ONLY_ALLOWED")),string(r.Stdout))
 s2clean(t,"already-cancelled",r)
}
