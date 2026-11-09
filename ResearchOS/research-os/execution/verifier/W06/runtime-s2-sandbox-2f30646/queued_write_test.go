//go:build windows

package sandbox

import (
 "bytes"
 "context"
 "fmt"
 "testing"
 "time"
)

func TestIndependentS2QueuedWriteDeadline(t *testing.T) {
 p,e:=Start(context.Background(),s2command(t,"blocked"),StartOptions{Interactive:true});if e!=nil{t.Fatal(e)}
 first:=make(chan error,1);go func(){first<-p.Write(context.Background(),bytes.Repeat([]byte("a"),64*1024))}()
 // The fixture does not read stdin; confirm the first write owns the serial lock.
 deadline:=time.Now().Add(time.Second)
 for {if !p.writeMu.TryLock(){break};p.writeMu.Unlock();if time.Now().After(deadline){p.Cancel();t.Fatal("writer did not acquire lock")};time.Sleep(time.Millisecond)}
 ctx,cancel:=context.WithTimeout(context.Background(),40*time.Millisecond);defer cancel()
 second:=make(chan error,1);start:=time.Now();go func(){second<-p.Write(ctx,[]byte("should-not-send\n"))}()
 var secondError error;returned:=false
 select{case secondError=<-second:returned=true;case<-time.After(200*time.Millisecond):}
 waited:=time.Since(start).Milliseconds()
 // Always release the owned child/writer before recording the negative finding.
 p.Cancel();if !returned{select{case secondError=<-second:case<-time.After(time.Second):t.Fatal("queued writer not released by cancellation")}}
 select{case<-first:case<-time.After(time.Second):t.Fatal("first writer not released")}
 r,we:=s2wait(t,p);s2save(t,"queued-write",map[string]any{"receipt":r,"wait_error":fmt.Sprint(we),"queued_error":fmt.Sprint(secondError),"returned_before_200ms":returned,"deadline_ms":40,"observed_wait_ms":waited})
 s2clean(t,"queued-write",r)
 s2assert(t,"queued-write-honors-own-deadline",returned,map[string]any{"deadline_ms":40,"waited_ms":waited,"returned":returned,"eventual_error":fmt.Sprint(secondError)})
}
